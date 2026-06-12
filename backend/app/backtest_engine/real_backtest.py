"""
青鳄量化 - 真实K线回测引擎
基于本地Parquet数据，向量化计算，零模拟

核心设计：
- 直接使用 KlineDataEngine 加载数据（绕过Provider层，性能最优）
- 向量化计算（无事件驱动开销）
- 支持月度/双周/周度调仓
- 返回真实权益曲线（非GBM模拟）
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import sys, os

sys.path.insert(0, str(Path(__file__).parent.parent / "data_engine"))
from kline_parquet import get_kline_engine


class RealBacktest:
    """真实K线回测引擎

    使用本地Parquet数据的向量化回测。
    无随机数，无GBM——每笔交易都是真实价格。

    使用示例:
        bt = RealBacktest(
            codes=["000001", "600519", ...],  # 股票池
            start="2024-06-01",
            end="2026-06-01",
            cash=1_000_000,
            top_n=20,         # 持仓数量
            rebalance="monthly",  # 调仓频率
            commission=0.0003,    # 手续费
        )
        result = bt.run()
        print(result["metrics"])  # 年化收益、夏普、回撤...
    """

    def __init__(
        self,
        codes: List[str],
        start: str,
        end: str,
        cash: float = 1_000_000,
        top_n: int = 20,
        rebalance: str = "monthly",
        commission: float = 0.0003,
        slippage: float = 0.0002,
        stop_loss: float = -0.08,
        ranking_factor: str = "v25_multi",  # v25 多因子评分
    ):
        self.codes = codes
        self.start = start
        self.end = end
        self.cash = cash
        self.top_n = top_n
        self.rebalance = rebalance
        self.commission = commission
        self.slippage = slippage
        self.stop_loss = stop_loss
        self.ranking_factor = ranking_factor

        self._engine = None
        self.funda_data = None  # PE/PB fundamentals, loaded in run()
        self.northbound_data = None  # 北向资金
        self.margin_data = None  # 融资融券
        self.big_deal_data = None  # 大单交易

    @property
    def engine(self):
        if self._engine is None:
            self._engine = get_kline_engine()
        return self._engine

    def run(self) -> dict:
        """执行回测

        Returns:
            {
                "metrics": {annual_return, sharpe_ratio, max_drawdown, ...},
                "equity_curve": [{date, value}, ...],
                "drawdown_curve": [{date, dd}, ...],
                "trades": [{date, side, symbol, price, quantity, reason}, ...],
                "positions": [{date, symbols, ...}, ...],
                "data_source": "parquet",
                "data_source_note": "真实K线回测，数据源：本地Parquet"
            }
        """
        t0 = datetime.now()

        # 1. 加载全池收盘价（含回溯窗口用于因子计算）
        #    需要往前多拉 60 个交易日保证动量/均线等因子有足够历史
        lookback_start = str(pd.to_datetime(self.start) - pd.Timedelta(days=90))
        print(f"[RealBacktest] Loading {len(self.codes)} stocks from Parquet...")
        closes_full = self.engine.get_closes(self.codes, lookback_start, self.end)
        if closes_full.empty:
            return {"error": "No data loaded", "metrics": {}}

        # 加载基本面数据 (PE/PB)
        self.funda_data = self._load_fundamentals()
        print(f"[RealBacktest] Fundamentals: {len(self.funda_data) if self.funda_data is not None else 0} rows")

        # 加载北向资金/融资融券/大单数据 (2026-06-12 新增)
        self.northbound_data = self._load_northbound()
        self.margin_data = self._load_margin()
        self.big_deal_data = self._load_big_deal()
        if self.northbound_data is not None:
            print(f"[RealBacktest] Northbound data loaded: {len(self.northbound_data)} rows")
        if self.margin_data is not None:
            print(f"[RealBacktest] Margin data loaded: {len(self.margin_data)} rows")
        if self.big_deal_data is not None:
            print(f"[RealBacktest] Big deal data loaded: {len(self.big_deal_data)} rows")

        # 只在回测区间内交易
        closes = closes_full[closes_full.index >= self.start]

        dates = closes.index.tolist()
        print(f"[RealBacktest] {len(dates)} trading days, {len(closes.columns)} stocks")

        # 2. 生成调仓信号
        rebalance_dates = self._get_rebalance_dates(dates)
        print(f"[RealBacktest] {len(rebalance_dates)} rebalance dates")

        # 3. 逐日模拟——资金管理分离
        equity_curve = []
        drawdown_curve = []
        trades = []
        positions_log = []

        cash = self.cash  # 可用现金
        peak = cash
        holdings = {}  # {code: {shares, avg_cost}}
        current_positions = []

        for i, date in enumerate(dates):
            date_str = str(date)[:10]

            # 调仓日：等权重再平衡
            if date_str in rebalance_dates or i == 0:
                new_positions = self._select_top(date, dates, closes_full)

                if new_positions:
                    # ── 先算当前总权益，确定目标仓位金额 ──
                    pos_val = 0.0
                    for code, h in holdings.items():
                        price = self._get_price(closes, code, date)
                        if price and price > 0:
                            pos_val += h["shares"] * price
                    nav_before = cash + pos_val
                    target_per_stock = nav_before * 0.95 / len(new_positions)

                    # ── 1. 卖出不在新持仓中的股票 ──
                    for code in list(holdings.keys()):
                        if code not in new_positions:
                            price = self._get_price(closes, code, date)
                            if price and price > 0:
                                shares = holdings[code]["shares"]
                                sell_amount = shares * price * (1 - self.slippage - self.commission)
                                cash += sell_amount
                                trades.append({
                                    "date": date_str, "side": "SELL",
                                    "symbol": code, "price": round(price, 2),
                                    "quantity": shares, "amount": round(sell_amount, 2),
                                    "reason": "调仓卖出",
                                })
                            del holdings[code]

                    # ── 2. 调整目标仓位到等权重 ──
                    for code in new_positions:
                        price = self._get_price(closes, code, date)
                        if not price or price <= 0:
                            continue

                        current_val = 0.0
                        if code in holdings:
                            current_val = holdings[code]["shares"] * price

                        diff = target_per_stock - current_val

                        # 需要减仓（超配超过15%）
                        if diff < -target_per_stock * 0.15:
                            sell_shares = int(abs(diff) / price / 100) * 100
                            if sell_shares >= 100 and sell_shares <= holdings[code]["shares"]:
                                sell_amount = sell_shares * price * (1 - self.slippage - self.commission)
                                cash += sell_amount
                                holdings[code]["shares"] -= sell_shares
                                trades.append({
                                    "date": date_str, "side": "SELL",
                                    "symbol": code, "price": round(price, 2),
                                    "quantity": sell_shares, "amount": round(sell_amount, 2),
                                    "reason": "调仓减仓",
                                })

                        # 需要加仓（低配超过15%）
                        elif diff > target_per_stock * 0.15:
                            buy_shares = int(diff / price / 100) * 100
                            if buy_shares < 100 and diff >= price * 100:
                                buy_shares = 100
                            if buy_shares >= 100:
                                buy_amount = buy_shares * price * (1 + self.slippage + self.commission)
                                if buy_amount <= cash:
                                    cash -= buy_amount
                                    if code in holdings:
                                        old_s = holdings[code]["shares"]
                                        old_c = holdings[code]["avg_cost"]
                                        new_s = old_s + buy_shares
                                        holdings[code]["avg_cost"] = (old_c * old_s + price * buy_shares) / new_s
                                        holdings[code]["shares"] = new_s
                                    else:
                                        holdings[code] = {"shares": buy_shares, "avg_cost": price}
                                    trades.append({
                                        "date": date_str, "side": "BUY",
                                        "symbol": code, "price": round(price, 2),
                                        "quantity": buy_shares, "amount": round(buy_amount, 2),
                                        "reason": "调仓加仓",
                                    })

                current_positions = list(holdings.keys())

            # ── 计算当日总权益 = 现金 + 持仓市值 ──
            positions_value = 0
            for code, h in holdings.items():
                price = self._get_price(closes, code, date)
                if price and price > 0:
                    positions_value += h["shares"] * price
            nav = cash + positions_value

            # ── 止损检查（每日）──
            for code in list(holdings.keys()):
                price = self._get_price(closes, code, date)
                if price and price > 0 and holdings[code]["avg_cost"] > 0:
                    pnl_pct = (price - holdings[code]["avg_cost"]) / holdings[code]["avg_cost"]
                    if pnl_pct <= self.stop_loss:
                        shares = holdings[code]["shares"]
                        sell_amount = shares * price * (1 - self.slippage - self.commission)
                        cash += sell_amount
                        trades.append({
                            "date": date_str, "side": "SELL",
                            "symbol": code, "price": round(price, 2),
                            "quantity": shares, "amount": round(sell_amount, 2),
                            "reason": f"止损 ({pnl_pct*100:.1f}%)",
                        })
                        del holdings[code]

            # ── 记录 ──
            peak = max(peak, nav)
            dd = (nav - peak) / peak * 100 if peak > 0 else 0
            equity_curve.append({"date": date_str, "value": round(nav, 2)})
            drawdown_curve.append({"date": date_str, "dd": round(dd, 2)})
            positions_log.append({
                "date": date_str,
                "symbols": current_positions.copy(),
                "count": len(current_positions),
            })

        # 4. 计算指标
        metrics = self._compute_metrics(equity_curve, self.cash)
        elapsed = (datetime.now() - t0).total_seconds()

        return {
            "metrics": metrics,
            "equity_curve": equity_curve,
            "drawdown_curve": drawdown_curve,
            "trades": trades,
            "positions": positions_log,
            "data_source": "parquet",
            "data_source_note": f"真实K线回测 · {len(self.codes)}只股票池 · {len(dates)}个交易日 · 耗时{elapsed:.1f}秒",
            "config": {
                "codes": len(self.codes),
                "top_n": self.top_n,
                "rebalance": self.rebalance,
                "start": self.start,
                "end": self.end,
                "stop_loss": self.stop_loss,
                "ranking_factor": self.ranking_factor,
            },
        }

    def _get_rebalance_dates(self, dates: list) -> set:
        """确定调仓日期"""
        df = pd.DataFrame({"date": dates})
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month

        if self.rebalance == "monthly":
            # 每月第一个交易日
            df["g"] = df["date"].dt.strftime("%Y-%m")
            rebalance = df.groupby("g")["date"].first().tolist()
        elif self.rebalance == "biweekly":
            # 每两周
            rebalance = [dates[i] for i in range(0, len(dates), 10)]
        elif self.rebalance == "weekly":
            rebalance = [dates[i] for i in range(0, len(dates), 5)]
        else:
            rebalance = [dates[i] for i in range(0, len(dates), 20)]

        return set(str(d)[:10] for d in rebalance)

    # ── v25 多因子权重（基于网格搜索最优，去掉 mom_20d/volume/money_flow 后重归一化）──
    FACTOR_WEIGHTS = {
        # 动量因子 (4个, 合计32%)
        'mom_5d':      0.12,   # 5日动量
        'mom_10d':     0.10,   # 10日动量
        'mom_3d':      0.05,   # 3日动量
        'mom_20d':     0.05,   # 20日动量
        # 趋势因子 (3个, 合计18%)
        'ma_dev_20d':  0.06,   # 均线偏离
        'boll_pos':    0.06,   # 布林带位置
        'price_accel': 0.06,   # 价格加速度
        # 质量因子 (3个, 合计15%)
        'consistency': 0.05,   # 动量一致性
        'daily_sharpe':0.05,   # 日频夏普
        'vol_20d':     0.05,   # 低波动偏好
        # 资金/情绪因子 (3个, 合计9%)
        'money_flow':  0.04,   # 简化MFI
        'rsi_14':      0.02,   # RSI
        'macd_hist':   0.03,   # MACD柱
        # 基本面因子 (2个, 合计10%) — 2026-06-11 新增
        'pe_ttm':      0.05,   # PE_TTM (低估值偏好)
        'pb_ttm':      0.05,   # PB (低市净率偏好)
        # 北向资金/融资/大单因子 (合计10%, 2026-06-12 新增)
        'northbound_flow':0.03,   # 北向资金近5日净买入
        'margin_change': 0.03,   # 融资余额变化率
        'big_deal_net':  0.04,   # 大单净买入强度
        # 预留位 (暂无数据源, 合计6%)
        'turnover_mom':0.02,   # 换手率变化
        'volume_ratio':0.02,   # 量比
        'atr_14':      0.02,   # 平均真实波幅
    }

    # 选股过滤器
    MIN_PRICE = 3.0
    MAX_PRICE = 100.0
    MAX_CHG_5D = 0.15          # 5日最大涨幅（防追高）
    MAX_CHG_10D_DROP = -0.20   # 10日最大跌幅（防接飞刀）

    def _load_fundamentals(self):
        """加载PE/PB基本面数据。返回DataFrame或None"""
        funda_file = Path(__file__).parent.parent.parent / "data" / "fundamentals" / "fundamentals.parquet"
        if not funda_file.exists():
            return None
        try:
            df = pd.read_parquet(funda_file)
            df['date'] = pd.to_datetime(df['date'])
            # 过滤极端值：PE在 1~500 之间，PB在 0.1~50 之间
            bad_pe = (df['pe_ttm'] <= 0) | (df['pe_ttm'] > 500) | (~np.isfinite(df['pe_ttm']))
            bad_pb = (df['pb'] <= 0) | (df['pb'] > 50) | (~np.isfinite(df['pb']))
            df.loc[bad_pe, 'pe_ttm'] = np.nan
            df.loc[bad_pb, 'pb'] = np.nan
            return df
        except Exception as e:
            print(f"[RealBacktest] WARN: Failed to load fundamentals: {e}")
            return None

    def _load_northbound(self):
        """加载北向资金数据，计算近5日净买入强度"""
        nb_file = Path(__file__).parent.parent.parent / "data" / "alternative" / "northbound.parquet"
        if not nb_file.exists():
            return None
        try:
            df = pd.read_parquet(nb_file)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            # 近5日净买入强度: net_buy_amt / buy_amt 的5日滚动均值
            buy_5d = df['buy_amt'].rolling(5, min_periods=1).mean()
            net_5d = df['net_buy_amt'].rolling(5, min_periods=1).mean()
            df['northbound_flow'] = net_5d / (buy_5d + 1e-10)
            # 累积净买入（缩放到合理范围）
            df['northbound_cumulative'] = df['cumulative_net'] / 1e8
            df = df.set_index('date')
            return df[['northbound_flow', 'northbound_cumulative']]
        except Exception as e:
            print(f"[RealBacktest] WARN: Failed to load northbound: {e}")
            return None

    def _load_margin(self):
        """加载融资融券数据，计算融资余额5日变化率"""
        mg_file = Path(__file__).parent.parent.parent / "data" / "alternative" / "margin.parquet"
        if not mg_file.exists():
            return None
        try:
            df = pd.read_parquet(mg_file)
            df['date'] = pd.to_datetime(df['date'])
            # 检测融资余额列名
            bal_col = None
            for col in ['margin_balance', '融资余额']:
                if col in df.columns:
                    bal_col = col
                    break
            if bal_col is None:
                # 找含"余额"的列
                for col in df.columns:
                    if '余额' in col:
                        bal_col = col
                        break
            if bal_col is None:
                print("[RealBacktest] WARN: margin data has no balance column")
                return None
            df = df.sort_values(['symbol', 'date'])
            df['margin_change'] = df.groupby('symbol')[bal_col].transform(
                lambda x: x.pct_change(5)
            )
            df = df.dropna(subset=['margin_change'])
            # 过滤极端值
            df.loc[np.abs(df['margin_change']) > 2, 'margin_change'] = np.nan
            df = df.dropna(subset=['margin_change'])
            df = df.set_index(['symbol', 'date'])
            return df[['margin_change']]
        except Exception as e:
            print(f"[RealBacktest] WARN: Failed to load margin: {e}")
            return None

    def _load_big_deal(self):
        """加载大单交易数据，计算近5日大单净买入强度"""
        bd_file = Path(__file__).parent.parent.parent / "data" / "fund_flow" / "big_deal.parquet"
        if not bd_file.exists():
            return None
        try:
            df = pd.read_parquet(bd_file)
            df['date'] = pd.to_datetime(df['date'])
            # 计算每笔的净买入金额 (side_value: 1=买, -1=卖)
            df['net_amount'] = df['side_value'] * df['amount']
            # 按股票和日期聚合
            daily = df.groupby(['code', 'date']).agg(
                net_buy_amt=('net_amount', 'sum'),
                total_amt=('amount', 'sum')
            ).reset_index()
            daily = daily.sort_values(['code', 'date'])
            # 近5日滚动聚合
            daily['net_buy_5d'] = daily.groupby('code')['net_buy_amt'].transform(
                lambda x: x.rolling(5, min_periods=1).sum()
            )
            daily['total_5d'] = daily.groupby('code')['total_amt'].transform(
                lambda x: x.rolling(5, min_periods=1).sum()
            )
            daily['big_deal_net'] = daily['net_buy_5d'] / (daily['total_5d'] + 1e-10)
            daily = daily.dropna(subset=['big_deal_net'])
            daily = daily.set_index(['code', 'date'])
            return daily[['big_deal_net']]
        except Exception as e:
            print(f"[RealBacktest] WARN: Failed to load big deal: {e}")
            return None

    def _select_top(self, date, dates, closes) -> List[str]:
        """v25 多因子评分选股 + 质量过滤
        
        两步法：
        1. 逐个计算原始因子值 + 基础过滤
        2. 跨股票百分位归一化 + 加权打分
        """
        weights = self.FACTOR_WEIGHTS

        # ── Step 1: 逐个计算原始因子 ──
        raw_results = []  # [(code, {factor: val}), ...]
        for code in closes.columns:
            series = closes[code].dropna()
            if len(series) < 25:
                continue
            if date not in series.index:
                continue
            idx = series.index.get_loc(date)
            if idx < 25:
                continue

            values = series.values[:idx + 1]

            # 基础过滤
            price = values[-1]
            if price < self.MIN_PRICE or price > self.MAX_PRICE:
                continue

            # 5日涨幅过滤
            if len(values) >= 6:
                chg_5d = values[-1] / values[-6] - 1
                if chg_5d > self.MAX_CHG_5D:
                    continue

            # 10日跌幅过滤
            if len(values) >= 11:
                chg_10d = values[-1] / values[-11] - 1
                if chg_10d < self.MAX_CHG_10D_DROP:
                    continue

            # 计算因子（从收盘价序列 + 基本面数据）
            factors = {}

            # ── 基本面因子 (从fundamentals.parquet加载) ──
            if self.funda_data is not None:
                funda_row = self.funda_data[
                    (self.funda_data['code'] == code) &
                    (self.funda_data['date'] <= str(date)[:10])
                ]
                if len(funda_row) > 0:
                    latest = funda_row.iloc[-1]
                    pe_val = latest.get('pe_ttm')
                    pb_val = latest.get('pb')
                    if pd.notna(pe_val) and pe_val > 0:
                        factors['pe_ttm'] = 1.0 / (1.0 + pe_val)  # 低PE=高得分
                    if pd.notna(pb_val) and pb_val > 0:
                        factors['pb_ttm'] = 1.0 / (1.0 + pb_val)  # 低PB=高得分

            if len(values) >= 6:
                factors['mom_5d'] = values[-1] / values[-6] - 1
            if len(values) >= 11:
                factors['mom_10d'] = values[-1] / values[-11] - 1
            if len(values) >= 21:
                ma20 = np.mean(values[-20:])
                std20 = np.std(values[-20:])
                factors['ma_dev_20d'] = values[-1] / ma20 - 1
                factors['boll_pos'] = (values[-1] - ma20) / (2.0 * max(std20, 1e-10))
            if len(values) >= 20:
                rets = np.diff(values[-20:]) / (values[-20:-1] + 1e-10)
                factors['vol_20d'] = 1.0 / (1.0 + np.std(rets))  # 低波偏好
                up_days = np.sum(rets > 0)
                factors['consistency'] = up_days / max(len(rets), 1)
                up_sum = np.sum(np.maximum(rets, 0))
                dn_sum = np.sum(np.abs(np.minimum(rets, 0)))
                factors['money_flow'] = up_sum / max(dn_sum, 1e-10) - 1.0


            # ── 新增因子 (2026-06-11 真校准) ──
            # 3日动量
            if len(values) >= 4:
                factors['mom_3d'] = values[-1] / values[-4] - 1
            # 20日动量
            if len(values) >= 21:
                factors['mom_20d'] = values[-1] / values[-21] - 1
            # RSI_14
            if len(values) >= 15:
                deltas = np.diff(values[-15:])
                gains = np.sum(np.maximum(deltas, 0))
                losses = np.sum(np.abs(np.minimum(deltas, 0)))
                factors['rsi_14'] = 100.0 * gains / (gains + losses) if losses > 1e-10 else (100.0 if gains > 0 else 50.0)
            # Price acceleration
            if len(values) >= 41:
                mom_now = values[-1] / values[-21] - 1
                mom_prev = values[-21] / values[-41] - 1
                factors['price_accel'] = mom_now - mom_prev
            elif len(values) >= 31:
                mom_now = values[-1] / values[-21] - 1
                mom_prev = values[-11] / values[-31] - 1
                factors['price_accel'] = mom_now - mom_prev
            # Daily Sharpe
            if len(values) >= 21:
                rets = np.diff(values[-21:]) / (values[-21:-1] + 1e-10)
                avg_ret = np.mean(rets)
                std_ret = np.std(rets)
                factors['daily_sharpe'] = avg_ret / max(std_ret, 1e-10)
            # MACD hist (简化版: close变化率替代EMA)
            if len(values) >= 26:
                fast = np.mean(values[-12:])
                slow = np.mean(values[-26:])
                macd_line = fast / max(slow, 1e-10) - 1
                macd_vals = []
                for i in range(9, len(values)):
                    f12 = np.mean(values[i-11:i+1]) if i >= 11 else np.mean(values[:i+1])
                    f26 = np.mean(values[i-25:i+1]) if i >= 25 else np.mean(values[:i+1])
                    macd_vals.append(f12 / max(f26, 1e-10) - 1)
                if len(macd_vals) >= 9:
                    signal = np.mean(macd_vals[-9:])
                    factors['macd_hist'] = macd_vals[-1] - signal
                elif macd_vals:
                    factors['macd_hist'] = macd_vals[-1]

            # ── 北向资金/融资/大单因子 (2026-06-12 新增) ──
            dt_str = str(date)[:10]
            target_dt = pd.to_datetime(dt_str)
            # 北向资金 (市场级，所有股票同值——用于市场择时参考)
            if self.northbound_data is not None:
                try:
                    nb_slice = self.northbound_data[self.northbound_data.index <= target_dt]
                    if len(nb_slice) > 0:
                        factors['northbound_flow'] = float(nb_slice.iloc[-1]['northbound_flow'])
                except:
                    pass
            # 融资余额变化率 (个股级)
            if self.margin_data is not None:
                try:
                    dates_idx = self.margin_data.index.get_level_values('date')
                    symbols_idx = self.margin_data.index.get_level_values('symbol')
                    mask = (symbols_idx == code) & (dates_idx <= target_dt)
                    matching = self.margin_data[mask]
                    if len(matching) > 0:
                        factors['margin_change'] = float(matching.iloc[-1]['margin_change'])
                except:
                    pass
            # 大单净买入 (个股级)
            if self.big_deal_data is not None:
                try:
                    dates_idx = self.big_deal_data.index.get_level_values('date')
                    codes_idx = self.big_deal_data.index.get_level_values('code')
                    mask = (codes_idx == code) & (dates_idx <= target_dt)
                    matching = self.big_deal_data[mask]
                    if len(matching) > 0:
                        factors['big_deal_net'] = float(matching.iloc[-1]['big_deal_net'])
                except:
                    pass

            if factors:
                raw_results.append((code, factors))

        if not raw_results:
            return []

        # ── Step 2: 百分位归一化 + 加权打分 ──
        factor_names = list(weights.keys())
        # 收集每个因子的所有值
        factor_vals = {f: [] for f in factor_names}
        for _, factors in raw_results:
            for f in factor_names:
                v = factors.get(f)
                if v is not None:
                    factor_vals[f].append(v)

        # 计算每个因子的5%-95%分位数
        factor_range = {}
        for f in factor_names:
            vals = factor_vals[f]
            if len(vals) >= 10:
                p5 = np.percentile(vals, 5)
                p95 = np.percentile(vals, 95)
                if p95 > p5:
                    factor_range[f] = (p5, p95)
                else:
                    factor_range[f] = None
            else:
                factor_range[f] = None

        # 加权打分
        rankings = []
        for code, factors in raw_results:
            score = 0.0
            for f in factor_names:
                v = factors.get(f)
                if v is None:
                    continue
                rng = factor_range[f]
                if rng:
                    # 归一化到 0-1
                    v_norm = np.clip((v - rng[0]) / (rng[1] - rng[0]), 0.0, 1.0)
                else:
                    v_norm = 0.5
                score += weights[f] * v_norm
            rankings.append((code, score))

        rankings.sort(key=lambda x: x[1], reverse=True)
        return [code for code, _ in rankings[:self.top_n]]

    def _get_price(self, closes, code, date):
        """安全获取某日收盘价"""
        if code not in closes.columns:
            return None
        series = closes[code]
        if date in series.index:
            v = series.loc[date]
            if pd.notna(v) and v > 0:
                return float(v)
        return None

    def _compute_metrics(self, equity: list, cash: float) -> dict:
        """从权益曲线计算指标"""
        if len(equity) < 2:
            return {}

        values = [e["value"] for e in equity]
        final = values[-1]

        total_return = round((final - cash) / cash * 100, 2)
        days = len(values)

        # 年化收益
        years = days / 252
        if years > 0 and cash > 0:
            annual_return = round(((final / cash) ** (1 / years) - 1) * 100, 2)
        else:
            annual_return = 0

        # 日内收益序列
        daily_rets = [(values[i] - values[i - 1]) / values[i - 1] for i in range(1, len(values))]

        # 夏普比率
        if daily_rets:
            mean_ret = sum(daily_rets) / len(daily_rets)
            variance = sum((r - mean_ret) ** 2 for r in daily_rets) / len(daily_rets)
            std_ret = variance ** 0.5
            sharpe = round(mean_ret / max(std_ret, 1e-10) * (252 ** 0.5), 2)
        else:
            sharpe = 0

        # 最大回撤
        peak = values[0]
        max_dd = 0
        for v in values:
            peak = max(peak, v)
            dd = (v - peak) / peak * 100
            max_dd = min(max_dd, dd)

        # 胜率
        wins = sum(1 for r in daily_rets if r > 0)
        win_rate = round(wins / len(daily_rets) * 100, 1) if daily_rets else 0

        # 盈亏比
        gains = [r for r in daily_rets if r > 0]
        losses = [abs(r) for r in daily_rets if r < 0]
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0.001
        profit_factor = round(avg_gain / avg_loss, 2)

        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": round(max_dd, 2),
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_days": days,
            "annual_years": round(years, 2),
        }


def run_backtest_default(codes: List[str] = None, **kwargs) -> dict:
    """快捷入口：用默认参数跑回测

    如果不传codes，自动取沪深300成分股。
    在前端"回测中心"点"运行回测"时调用此函数。
    """
    if codes is None:
        # 默认：取前300只（近似沪深300）
        engine = get_kline_engine()
        all_codes = engine.get_available_stocks()
        codes = all_codes[:300]

    bt = RealBacktest(
        codes=codes,
        start=kwargs.get("start", "2024-06-01"),
        end=kwargs.get("end", "2026-06-09"),
        cash=kwargs.get("cash", 1_000_000),
        top_n=kwargs.get("top_n", 20),
        rebalance=kwargs.get("rebalance", "monthly"),
        commission=kwargs.get("commission", 0.0003),
        stop_loss=kwargs.get("stop_loss", -0.08),
        slippage=kwargs.get("slippage", 0.0002),
    )
    return bt.run()
