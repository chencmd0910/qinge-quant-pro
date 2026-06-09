"""实盘模拟交易引擎 — 挂接策略基因库 + 真K线数据

设计:
    1. 收盘后触发（手动或cron）
    2. 从基因库读取 ACTIVE 策略
    3. 实时计算因子（从Parquet K线）
    4. 每个策略独立产生信号
    5. 组合层面汇总 → 模拟成交
    6. 记录净值 + Alpha衰减

用法:
    runner = LivePaperRunner()
    runner.run()                       # 跑所有缺失的交易日
    runner.run_daily()                 # 只跑今天
    runner.get_state()                 # 获取当前状态
"""
import os
import sys
import json
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field, asdict

import pandas as pd
import numpy as np

# 数据目录 — 支持环境变量覆盖
DATA_DIR = os.environ.get("PAPER_TRADING_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data"))
KLINE_DIR = os.path.join(DATA_DIR, "klines", "parquet")
STATE_FILE = os.path.join(DATA_DIR, "live_trading_state.json")
REGISTRY_FILE = os.path.join(DATA_DIR, "strategy_registry.json")
ALPHA_HISTORY_FILE = os.path.join(DATA_DIR, "alpha_history.json")


@dataclass
class Position:
    code: str
    name: str
    shares: int
    avg_cost: float
    current_price: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    assigned_strategy: str = ""   # 哪个策略买入的
    buy_date: str = ""


@dataclass
class Trade:
    date: str
    code: str
    name: str
    action: str  # BUY / SELL
    shares: int
    price: float
    value: float
    commission: float
    reason: str
    strategy_id: str


@dataclass
class EquityPoint:
    date: str
    total_value: float
    cash: float
    positions_value: float
    daily_return: float
    cumulative_return: float
    drawdown: float


@dataclass
class AlphaRecord:
    date: str
    strategy_id: str
    strategy_name: str
    daily_return: float
    alpha_30d: float
    status: str  # HEALTHY / DEGRADING / DEAD
    sharpe_30d: float


# ═══════════════════════════════════════════════════════════
# 因子计算引擎（复用 v25 逻辑）
# ═══════════════════════════════════════════════════════════

class FactorEngine:
    """v25 多因子评分引擎（纯OHLCV可算）"""

    # 因子权重（v25配置）
    FACTOR_WEIGHTS = {
        'mom_5d': 0.22,
        'money_flow': 0.22,
        'ma_dev_20d': 0.17,
        'mom_10d': 0.10,
        'consistency': 0.10,
        'vol_20d': -0.11,   # 负向：高波动低分
        'boll_pos': -0.08,  # 负向：高位风险
    }

    @staticmethod
    def compute_factors(df: pd.DataFrame) -> Dict[str, np.ndarray]:
        """从OHLCV计算所有因子（向量化实现，高性能）"""
        close = df['close'].values.astype(float)
        high = df['high'].values.astype(float)
        low = df['low'].values.astype(float)
        open_p = df['open'].values.astype(float)
        volume = df['volume'].values.astype(float)
        n = len(close)

        factors = {}
        nan = np.nan

        # 动量因子（向量化）
        mom5 = np.full(n, nan)
        mom10 = np.full(n, nan)
        mom5[5:] = (close[5:] - close[:-5]) / (close[:-5] + 1e-9)
        mom10[10:] = (close[10:] - close[:-10]) / (close[:-10] + 1e-9)
        factors['mom_5d'] = mom5
        factors['mom_10d'] = mom10

        # 均线偏离（向量化）
        ma_dev = np.full(n, nan)
        if n >= 20:
            ma20 = np.convolve(close, np.ones(20)/20, mode='valid')
            ma_dev[19:] = (close[19:] - ma20) / (ma20 + 1e-9)
        factors['ma_dev_20d'] = ma_dev

        # 动量一致性（向量化）
        consistency = np.full(n, nan)
        if n >= 21:
            diffs = np.diff(close)
            up_days = np.convolve((diffs > 0).astype(float), np.ones(20), mode='valid')
            consistency[20:] = up_days / 20.0
        factors['consistency'] = consistency

        # 资金流（向量化）
        mf = np.full(n, nan)
        hl_range = high - low
        mask = hl_range > 0
        mf[1:][mask[1:]] = ((close[1:] - open_p[1:])[mask[1:]] / hl_range[1:][mask[1:]]) * volume[1:][mask[1:]]
        mf[1:][~mask[1:]] = 0
        factors['money_flow'] = mf

        # 波动率（向量化）
        vol20 = np.full(n, nan)
        if n >= 21:
            returns = np.diff(close) / (close[:-1] + 1e-9)
            # 滚动std用pandas比较快
            vol_series = pd.Series(returns).rolling(20).std().values
            # vol_series[19] 对应 returns[0:19], 对应 close[0:20]
            vol20[20:] = vol_series[19:]
        factors['vol_20d'] = vol20

        # 布林带位置（向量化）
        boll = np.full(n, nan)
        if n >= 20:
            ma20_b = pd.Series(close).rolling(20).mean().values
            std20_b = pd.Series(close).rolling(20).std().values
            upper = ma20_b + 2 * std20_b
            lower = ma20_b - 2 * std20_b
            boll_range = upper - lower
            boll[19:] = np.where(boll_range[19:] > 0,
                                 (close[19:] - lower[19:]) / (boll_range[19:] + 1e-9),
                                 0.5)
        factors['boll_pos'] = boll

        return factors

    @staticmethod
    def score_stocks(df: pd.DataFrame, factor_weights: dict = None) -> np.ndarray:
        """对最近交易日计算综合因子得分（向量化版本）"""
        if factor_weights is None:
            factor_weights = FactorEngine.FACTOR_WEIGHTS

        factors = FactorEngine.compute_factors(df)
        n = len(df)

        # 百分位归一化（向量化）
        normalized = {}
        for name, values in factors.items():
            finite_mask = np.isfinite(values)
            pct = np.full(n, 0.5)  # 默认中性
            # 对每个位置，用最近60天的数据做百分位
            for i in range(20, n):
                start_idx = max(0, i - 60)
                window = values[start_idx:i]
                window_finite = window[np.isfinite(window)]
                if len(window_finite) >= 10:
                    v = values[i]
                    if np.isfinite(v):
                        pct[i] = np.clip((window_finite < v).mean(), 0.0, 1.0)
            normalized[name] = pct

        # 加权求和
        score = np.zeros(n)
        for name, weight in factor_weights.items():
            if name in normalized:
                score += weight * normalized[name]

        return score

    @staticmethod
    def rank_stocks_for_date(codes: List[str], target_date: str,
                             kline_dir: str = KLINE_DIR,
                             top_n: int = 20, max_universe: int = 300) -> List[Tuple[str, str, float]]:
        """对给定日期的所有股票按因子排名

        Args:
            codes: 股票代码列表
            target_date: 目标日期
            kline_dir: K线数据目录
            top_n: 返回前N只
            max_universe: 最大股票池大小（先按成交额筛选）

        Returns:
            [(code, name, score), ...]  按得分降序
        """
        results = []

        # 预筛选：按成交额(c close * volume)取前max_universe只
        turnover = []
        for code in codes:
            path = os.path.join(kline_dir, f"{code}.parquet")
            if not os.path.exists(path):
                continue
            df = pd.read_parquet(path, columns=['date', 'close', 'volume'])
            row = df[df['date'] == target_date]
            if row.empty:
                continue
            vol = float(row.iloc[0]['volume'])
            price = float(row.iloc[0]['close'])
            if price <= 0 or price < 3:
                continue
            turnover.append((code, vol * price))

        turnover.sort(key=lambda x: x[1], reverse=True)
        candidate_codes = [c for c, _ in turnover[:max_universe]]

        # 逐个计算因子得分
        for code in candidate_codes:
            path = os.path.join(kline_dir, f"{code}.parquet")
            df = pd.read_parquet(path)

            # 止损检查
            close_vals = df[df['date'] <= target_date]['close'].values.astype(float)
            if len(close_vals) < 60:
                continue
            if len(close_vals) >= 20 and close_vals[-1] / close_vals[-20] < 0.80:
                continue

            try:
                hist = df[df['date'] <= target_date]
                scores = FactorEngine.score_stocks(hist)
                if len(scores) > 0 and not np.isnan(scores[-1]):
                    results.append((
                        code,
                        df['name'].iloc[0] if 'name' in df.columns else code,
                        float(scores[-1]),
                    ))
            except Exception:
                continue

        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_n]


# ═══════════════════════════════════════════════════════════
# 实盘模拟运行器
# ═══════════════════════════════════════════════════════════

class LivePaperRunner:
    """实盘模拟交易运行器

    每个交易日：
    1. 读取活跃策略
    2. 每个策略独立选股
    3. 组合层面综合 → 决定买卖
    4. 执行模拟成交
    5. 更新净值 + Alpha
    """

    def __init__(self, initial_cash: float = 1_000_000,
                 commission: float = 0.0003,
                 slippage: float = 0.002):
        self.initial_cash = initial_cash
        self.commission = commission
        self.slippage = slippage

        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[EquityPoint] = []
        self.alpha_records: List[AlphaRecord] = []
        self.current_date: str = ""
        self.start_date: str = ""

        # 加载活跃策略
        self.active_strategies = self._load_active_strategies()

    def _load_active_strategies(self) -> List[dict]:
        """从基因库加载ACTIVE策略"""
        if not os.path.exists(REGISTRY_FILE):
            print("[LiveRunner] 基因库不存在，使用默认v25策略")
            return [{
                "strategy_id": "v25_default",
                "strategy_name": "多因子V25",
                "weight": 1.0,
                "backtest_params": {
                    "top_n": 20,
                    "rebalance": "monthly",
                    "stop_loss": -0.08,
                    "ranking_factor": "v25_multi",
                },
            }]

        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            registry = json.load(f)

        active = [s for s in registry if s.get('lifecycle', {}).get('status') == 'ACTIVE']
        if not active:
            print("[LiveRunner] 无ACTIVE策略，使用默认v25")
            return self._load_default_strategies()

        # 等权分配
        weight = 1.0 / len(active)
        for s in active:
            s['weight'] = weight

        print(f"[LiveRunner] 加载 {len(active)} 个ACTIVE策略: {[s['strategy_name'] for s in active]}")
        return active

    def _load_default_strategies(self) -> List[dict]:
        return [{
            "strategy_id": "v25_default",
            "strategy_name": "多因子V25",
            "weight": 1.0,
            "backtest_params": {"top_n": 20, "rebalance": "monthly", "stop_loss": -0.08},
        }]

    def load_state(self) -> bool:
        """从磁盘载入之前的状态"""
        if not os.path.exists(STATE_FILE):
            return False

        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)

        self.cash = state.get('cash', self.initial_cash)
        self.current_date = state.get('current_date', '')
        self.start_date = state.get('start_date', '')
        self.trades = []
        self.equity_curve = []

        self.positions = {}
        for p in state.get('positions', []):
            pos = Position(
                code=p['code'], name=p.get('name', p['code']),
                shares=p['shares'], avg_cost=p.get('avg_cost', 0),
                current_price=p.get('current_price', 0),
                pnl=p.get('pnl', 0), pnl_pct=p.get('pnl_pct', 0),
                assigned_strategy=p.get('assigned_strategy', ''),
                buy_date=p.get('buy_date', ''),
            )
            self.positions[p['code']] = pos

        return True

    def save_state(self):
        """保存当前状态到磁盘"""
        state = {
            'initial_cash': self.initial_cash,
            'cash': self.cash,
            'current_date': self.current_date,
            'start_date': self.start_date,
            'positions': [
                {
                    'code': p.code, 'name': p.name,
                    'shares': p.shares, 'avg_cost': p.avg_cost,
                    'current_price': p.current_price,
                    'pnl': p.pnl, 'pnl_pct': p.pnl_pct,
                    'assigned_strategy': p.assigned_strategy,
                    'buy_date': p.buy_date,
                }
                for p in self.positions.values()
            ],
            'trade_count': len(self.trades),
            'equity_count': len(self.equity_curve),
            'active_strategies': [
                {'id': s['strategy_id'], 'name': s['strategy_name'], 'weight': s['weight']}
                for s in self.active_strategies
            ],
        }
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _get_price_table(self, date_str: str, codes: List[str]) -> Dict[str, float]:
        """获取某日所有股票价格"""
        prices = {}
        for code in codes:
            path = os.path.join(KLINE_DIR, f"{code}.parquet")
            if not os.path.exists(path):
                continue
            df = pd.read_parquet(path, columns=['date', 'close', 'name'])
            row = df[df['date'] == date_str]
            if not row.empty:
                prices[code] = float(row.iloc[0]['close'])
        return prices

    def _get_market_codes(self) -> List[str]:
        """获取市场上所有可用代码"""
        if not os.path.exists(KLINE_DIR):
            return []
        return sorted([
            f.replace('.parquet', '')
            for f in os.listdir(KLINE_DIR)
            if f.endswith('.parquet')
        ])

    def _is_rebalance_day(self, date_str: str, rebalance: str = "monthly") -> bool:
        """检查是否是调仓日"""
        dt = pd.to_datetime(date_str)
        # 首日总是调仓
        if not self.positions and self.cash == self.initial_cash:
            return True
        if rebalance == "monthly":
            return dt.day <= 3 or dt.day >= 25
        elif rebalance == "biweekly":
            return dt.day in [1, 2, 15, 16]
        elif rebalance == "weekly":
            return dt.weekday() == 4  # 周五
        return True

    def _check_stop_loss(self) -> List[str]:
        """检查持仓是否需要止损
        
        策略的 stop_loss 参数可能是百分数（-8.0）或小数（-0.08），统一为小数。
        pnl_pct 来自 _mark_to_market，总是百分数（如 -5.0 表示 -5%），需转为小数。
        """
        # 取所有活跃策略中最宽松的止损线
        stop_thresholds = []
        for s in self.active_strategies:
            sl = s.get('backtest_params', {}).get('stop_loss', -0.15)
            # 如果绝对值 > 1（如 -8.0），转为小数
            if abs(sl) > 1:
                sl = sl / 100
            stop_thresholds.append(sl)
        # 取最小值（最严格）+ 硬底线
        min_stop = min(stop_thresholds) if stop_thresholds else -0.15
        hard_stop = -0.15  # 硬止损 -15%
        stop_loss = max(min_stop, hard_stop)  # 取宽松的那个（更接近0）
        
        stop_out = []
        for code, pos in self.positions.items():
            # pnl_pct 是百分数，转小数
            pnl_dec = pos.pnl_pct / 100.0
            if pnl_dec <= stop_loss:
                stop_out.append(code)
        return stop_out

    def _calc_win_rate(self) -> float:
        """计算已平仓交易的胜率（正收益 / 总平仓数）"""
        # 按代码聚合平仓交易
        closed = {}
        for t in self.trades:
            code = t.code if hasattr(t, 'code') else t.get('code', '')
            action = t.action if hasattr(t, 'action') else t.get('action', '')
            value = t.value if hasattr(t, 'value') else t.get('value', 0)
            if action in ('BUY', '买入'):
                closed[code] = closed.get(code, 0) - value
            elif action in ('SELL', '卖出', 'STOP_LOSS', 'REBALANCE_SELL'):
                closed[code] = closed.get(code, 0) + value
        profits = [v for v in closed.values() if v != 0]
        if not profits:
            return 0
        wins = sum(1 for v in profits if v > 0)
        return wins / len(profits)

    def _mark_to_market(self, date_str: str):
        """按市价估值所有持仓"""
        all_codes = [p.code for p in self.positions.values()]
        prices = self._get_price_table(date_str, all_codes)

        total_positions = 0
        for code, pos in self.positions.items():
            if code in prices:
                pos.current_price = prices[code]
                pos.pnl = (pos.current_price - pos.avg_cost) * pos.shares
                pos.pnl_pct = (pos.current_price / pos.avg_cost - 1) * 100
                total_positions += pos.current_price * pos.shares

        # 记录净值
        total_value = self.cash + total_positions
        self._record_equity(date_str, total_value, total_positions)

        return total_value, total_positions

    def _record_equity(self, date_str: str, total_value: float, positions_value: float):
        """记录权益曲线"""
        prev_value = self.initial_cash
        if self.equity_curve:
            prev_value = self.equity_curve[-1].total_value

        daily_return = (total_value / prev_value - 1) * 100 if prev_value > 0 else 0

        # 最大回撤
        peak = max(self.initial_cash, max((e.total_value for e in self.equity_curve), default=self.initial_cash))
        drawdown = (total_value / peak - 1) * 100 if peak > 0 else 0

        self.equity_curve.append(EquityPoint(
            date=date_str,
            total_value=round(total_value, 2),
            cash=round(self.cash, 2),
            positions_value=round(positions_value, 2),
            daily_return=round(daily_return, 4),
            cumulative_return=round((total_value / self.initial_cash - 1) * 100, 2),
            drawdown=round(drawdown, 2),
        ))

    def _execute_buy(self, code: str, name: str, target_value: float,
                     price: float, date_str: str, strategy_id: str):
        """模拟买入"""
        if target_value <= 0:
            return

        # 整百取整
        shares = int(target_value / price / 100) * 100
        if shares < 100 and target_value >= price * 100:
            shares = 100
        if shares < 100:
            return

        cost = shares * price * (1 + self.commission + self.slippage)
        if cost > self.cash:
            shares = int(self.cash / (price * (1 + self.commission + self.slippage)) / 100) * 100
            if shares < 100:
                return
            cost = shares * price * (1 + self.commission + self.slippage)

        self.cash -= cost

        if code in self.positions:
            # 加仓
            old = self.positions[code]
            total_shares = old.shares + shares
            old.avg_cost = (old.avg_cost * old.shares + price * shares) / total_shares
            old.shares = total_shares
        else:
            self.positions[code] = Position(
                code=code, name=name, shares=shares,
                avg_cost=price, current_price=price,
                assigned_strategy=strategy_id, buy_date=date_str,
            )

        self.trades.append(Trade(
            date=date_str, code=code, name=name, action='BUY',
            shares=shares, price=price, value=round(cost, 2),
            commission=round(cost * self.commission, 2),
            reason='STRATEGY_SIGNAL', strategy_id=strategy_id,
        ))

    def _execute_sell(self, code: str, shares: int, price: float,
                      date_str: str, reason: str, strategy_id: str):
        """模拟卖出"""
        if code not in self.positions:
            return
        pos = self.positions[code]
        sell_shares = min(shares, pos.shares)
        if sell_shares < 100:
            return

        proceeds = sell_shares * price * (1 - self.commission - self.slippage)
        self.cash += proceeds

        self.trades.append(Trade(
            date=date_str, code=code, name=pos.name, action='SELL',
            shares=sell_shares, price=price, value=round(proceeds, 2),
            commission=round(proceeds * self.commission, 2),
            reason=reason, strategy_id=strategy_id,
        ))

        pos.shares -= sell_shares
        if pos.shares < 100:
            del self.positions[code]

    def run_daily(self, target_date: str = None):
        """运行一个交易日

        Args:
            target_date: 目标日期（默认今天）
        """
        if target_date is None:
            target_date = date.today().isoformat()

        all_codes = self._get_market_codes()
        if not all_codes:
            print(f"[LiveRunner] {target_date}: 无K线数据")
            return

        print(f"\n[LiveRunner] === {target_date} ===")
        print(f"  活跃策略: {len(self.active_strategies)}个, 持仓: {len(self.positions)}只")
        print(f"  现金: ¥{self.cash:,.0f}")

        # 1. 按市价估值
        total_value, pos_value = self._mark_to_market(target_date)
        print(f"  估值: ¥{total_value:,.0f} (持仓¥{pos_value:,.0f})")

        # 2. 止损检查
        stop_out = self._check_stop_loss()
        if stop_out:
            print(f"  ⚠️ 止损: {stop_out}")
            prices = self._get_price_table(target_date, stop_out)
            for code in stop_out:
                if code in prices:
                    pos = self.positions.get(code)
                    if pos:
                        self._execute_sell(code, pos.shares, prices[code],
                                          target_date, 'STOP_LOSS', 'SYSTEM')

        # 3. 每个策略产生信号
        all_targets = {}  # {code: weight}
        code_names = {}    # {code: name} 用于名称查找
        strategy_count = len(self.active_strategies)

        for strategy in self.active_strategies:
            sid = strategy['strategy_id']
            sname = strategy['strategy_name']
            params = strategy.get('backtest_params', {})
            top_n = params.get('top_n', 20)
            rebalance = params.get('rebalance', 'monthly')
            weight = strategy.get('weight', 1.0 / strategy_count)

            # 检查是否需要调仓
            if not self._is_rebalance_day(target_date, rebalance):
                # 非调仓日：保持当前策略的持仓不变
                for code, pos in self.positions.items():
                    if pos.assigned_strategy == sid:
                        all_targets[code] = all_targets.get(code, 0) + weight
                continue

            # 调仓日：重新选股
            picks = FactorEngine.rank_stocks_for_date(
                all_codes, target_date, KLINE_DIR, top_n
            )

            # 保存名称
            for code, name, score in picks:
                code_names[code] = name

            # 分配给策略的目标权重
            per_pick_weight = weight / len(picks) if picks else 0
            for code, name, score in picks:
                all_targets[code] = all_targets.get(code, 0) + per_pick_weight

            # 记录策略本次选股
            strategy['_last_picks'] = picks

            print(f"  📊 {sname}: 选出{len(picks)}只 (Top3: {[p[0] for p in picks[:3]]})")

        # 4. 计算目标金额
        current_total = total_value
        prices = self._get_price_table(target_date, list(all_targets.keys()))

        # 5. 执行调仓：卖超配，买低配
        target_codes = set(all_targets.keys())
        current_codes = set(self.positions.keys())

        # 卖出不在目标列表的
        for code in current_codes - target_codes:
            pos = self.positions[code]
            if code in prices:
                self._execute_sell(code, pos.shares, prices[code],
                                  target_date, 'REBALANCE_SELL', 'SYSTEM')

        # 买入目标中的新股
        new_codes = target_codes - current_codes
        if new_codes:
            per_stock_cash = self.cash * 0.9 / max(len(new_codes), 1)  # 用90%现金
            for code in new_codes:
                if code in prices and prices[code] > 0:
                    # 名称查找
                    name = code_names.get(code, "")
                    if not name:
                        path = os.path.join(KLINE_DIR, f"{code}.parquet")
                        if os.path.exists(path):
                            df = pd.read_parquet(path, columns=['name'])
                            name = df['name'].iloc[0] if not df.empty else code

                    sid = "SYSTEM"
                    # 找到分配这个股票的策略
                    for s in self.active_strategies:
                        picks = s.get('_last_picks', [])
                        if picks and code in [p[0] for p in picks]:
                            sid = s['strategy_id']
                            break

                    self._execute_buy(code, name, per_stock_cash,
                                     prices[code], target_date, sid)

        # 6. 更新状态
        self.current_date = target_date
        if not self.start_date:
            self.start_date = target_date

        # 7. 记录Alpha（简化：用整体收益代表）
        if len(self.equity_curve) >= 21:
            recent_returns = [e.daily_return for e in self.equity_curve[-21:]]
            avg_ret = sum(recent_returns) / len(recent_returns)
            std_ret = np.std(recent_returns) + 1e-9
            sharpe_30d = (avg_ret / std_ret) * (252 ** 0.5) if std_ret > 0 else 0

            alpha_status = 'HEALTHY'
            if sharpe_30d < -0.5:
                alpha_status = 'DEAD'
            elif sharpe_30d < 0:
                alpha_status = 'DEGRADING'

            for s in self.active_strategies:
                self.alpha_records.append(AlphaRecord(
                    date=target_date,
                    strategy_id=s['strategy_id'],
                    strategy_name=s['strategy_name'],
                    daily_return=self.equity_curve[-1].daily_return,
                    alpha_30d=round(avg_ret, 4),
                    status=alpha_status,
                    sharpe_30d=round(sharpe_30d, 3),
                ))

        # 8. 持久化
        self.save_state()

        final_value = self.equity_curve[-1].total_value if self.equity_curve else self.initial_cash
        print(f"  收盘: ¥{final_value:,.0f}"
              f" | 收益 {self.equity_curve[-1].cumulative_return:.2f}%"
              f" | 回撤 {self.equity_curve[-1].drawdown:.2f}%"
              f" | 持仓 {len(self.positions)}只")

        return self.get_summary()

    def run(self, start_date: str = None, end_date: str = None,
            resume: bool = True):
        """运行从 start_date 到 end_date 的所有交易日

        Args:
            start_date: 开始日期（默认从2024-06-01或读上次状态）
            end_date: 结束日期（默认今天）
            resume: 是否从上次状态恢复
        """
        if resume:
            self.load_state()

        if start_date is None:
            if self.current_date:
                # 从上次日期+1天开始
                start_date = (pd.to_datetime(self.current_date) + timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                start_date = '2024-06-01'

        if end_date is None:
            end_date = date.today().isoformat()

        # 加载交易日历
        codes = self._get_market_codes()
        if not codes:
            raise RuntimeError("无K线数据，请先运行行情更新")

        # 从一只股票获取完整交易日历
        path = os.path.join(KLINE_DIR, f"{codes[0]}.parquet")
        if not os.path.exists(path):
            for c in codes:
                p = os.path.join(KLINE_DIR, f"{c}.parquet")
                if os.path.exists(p):
                    path = p
                    break

        if path and os.path.exists(path):
            df = pd.read_parquet(path, columns=['date'])
            all_dates = sorted(df['date'].unique())
            trading_dates = [
                d for d in all_dates
                if start_date <= str(d)[:10] <= end_date
            ]
        else:
            trading_dates = []

        print(f"[LiveRunner] 交易日范围: {start_date} → {end_date}")
        print(f"[LiveRunner] 待跑: {len(trading_dates)} 个交易日")

        for i, dt in enumerate(trading_dates):
            dt_str = str(dt)[:10]
            try:
                self.run_daily(dt_str)
            except Exception as e:
                print(f"  [ERR] {dt_str}: {e}")

            if (i + 1) % 50 == 0:
                print(f"  ... 进度 {i+1}/{len(trading_dates)}")

        return self.get_summary()

    def get_summary(self) -> dict:
        """获取当前状态摘要"""
        total_value = self.initial_cash
        if self.equity_curve:
            total_value = self.equity_curve[-1].total_value

        cumulative_return = 0
        max_dd = 0
        if self.equity_curve:
            cumulative_return = self.equity_curve[-1].cumulative_return
            max_dd = min(e.drawdown for e in self.equity_curve)

        # 计算夏普
        if len(self.equity_curve) >= 21:
            returns = [e.daily_return for e in self.equity_curve[-252:]]
            avg_ret = sum(returns) / len(returns)
            std_ret = np.std(returns) + 1e-9
            sharpe = (avg_ret / std_ret) * (252 ** 0.5)
        else:
            sharpe = 0

        return {
            'current_date': self.current_date,
            'start_date': self.start_date,
            'initial_cash': self.initial_cash,
            'cash': round(self.cash, 2),
            'total_value': round(total_value, 2),
            'positions_count': len(self.positions),
            'trade_count': len(self.trades),
            'cumulative_return': round(cumulative_return, 2),
            'max_drawdown': round(max_dd, 2),
            'sharpe': round(sharpe, 3),
            'active_strategies': [
                {'id': s['strategy_id'], 'name': s['strategy_name'], 'weight': s['weight']}
                for s in self.active_strategies
            ],
            'positions': [
                {
                    'code': p.code, 'name': p.name, 'shares': p.shares,
                    'avg_cost': round(p.avg_cost, 3),
                    'current_price': p.current_price,
                    'pnl': round(p.pnl, 2),
                    'pnl_pct': round(p.pnl_pct, 2),
                }
                for p in list(self.positions.values())[:20]
            ],
            'recent_trades': [
                {
                    'date': t.date, 'code': t.code, 'name': t.name,
                    'action': t.action, 'shares': t.shares,
                    'price': t.price, 'value': round(t.value, 2),
                    'reason': t.reason,
                }
                for t in self.trades[-20:]
            ],
            'alpha_status': 'HEALTHY',
            'equity_curve': [
                {'date': e.date, 'value': e.total_value, 'dd': e.drawdown}
                for e in self.equity_curve
            ],
        }
