"""ETF轮动策略 - Sprint-3 精确实现

规则:
    每周五收盘 → 计算60日收益率 → 选最强ETF
    下周一开盘 → 调仓
    始终持有一个ETF

标的池:
    510300.SH  沪深300ETF
    510500.SH  中证500ETF
    159915.SZ  创业板ETF
    515080.SH  中证1000ETF

成本:
    手续费: 万3 (单边)
    滑点: 可配置
"""
from typing import List, Dict, Optional
from datetime import datetime


class ETFRotationStrategy:
    """ETF轮动策略

    非事件驱动模式，直接操作Bar数据回测。
    """

    def __init__(self, symbols: List[str], lookback: int = 60,
                 commission_rate: float = 0.0003, slippage_pct: float = 0.001):
        self.symbols = symbols
        self.lookback = lookback
        self.commission_rate = commission_rate
        self.slippage_pct = slippage_pct

        # 状态
        self.held_symbol: Optional[str] = None
        self.held_quantity: int = 0
        self.cash: float = 0
        self.initial_cash: float = 0

        # 历史价格 {symbol: [(date_str, close), ...]}
        self.price_history: Dict[str, List[tuple]] = {s: [] for s in symbols}

        # 交易记录
        self.trades: List[dict] = []
        self.equity_curve: List[dict] = []

        # 日历状态
        self.bars_received: Dict[str, int] = {s: 0 for s in symbols}
        self.current_date: Optional[str] = None
        self.current_prices: Dict[str, float] = {}

    def initialize(self, initial_cash: float = 1_000_000):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.held_symbol = None
        self.held_quantity = 0
        self.trades = []
        self.equity_curve = []

    def on_bar(self, symbol: str, date_str: str, close: float) -> Optional[dict]:
        """处理一根K线

        Args:
            symbol: 标的代码
            date_str: 日期 YYYY-MM-DD
            close: 收盘价

        Returns:
            交易信号 dict 或 None
        """
        if symbol not in self.symbols:
            return None

        self.price_history[symbol].append((date_str, close))
        self.current_prices[symbol] = close
        self.bars_received[symbol] += 1
        self.current_date = date_str

        dt = datetime.strptime(date_str, '%Y-%m-%d')
        weekday = dt.weekday()  # 0=Mon, 4=Fri

        # 每周五收盘 → 计算信号
        if weekday == 4:
            return self._check_rebalance(date_str)

        return None

    def _check_rebalance(self, date_str: str) -> Optional[dict]:
        """周五检查是否需要调仓"""
        # 需要至少 lookback 天数据
        for s in self.symbols:
            if len(self.price_history[s]) < self.lookback:
                return None

        # 计算每个ETF的lookback日收益率
        best_symbol = None
        best_return = -999

        for s in self.symbols:
            prices = self.price_history[s]
            old_price = prices[-self.lookback][1]
            new_price = prices[-1][1]
            if old_price > 0:
                ret = (new_price - old_price) / old_price
                if ret > best_return:
                    best_return = ret
                    best_symbol = s

        if best_symbol is None:
            return None

        # 如果最强ETF和当前持仓不同，需要调仓
        if best_symbol != self.held_symbol:
            return {
                "action": "rebalance",
                "date": date_str,
                "from": self.held_symbol,
                "to": best_symbol,
                "return_60d": best_return,
                "reason": f"60日收益 {best_return*100:.2f}%",
            }

        return None

    def execute_trade(self, signal: dict, next_date: str, next_prices: Dict[str, float]):
        """执行调仓（下周一开盘）

        Args:
            signal: on_bar返回的信号
            next_date: 调仓执行日期（下周一）
            next_prices: 执行时的价格 {symbol: price}
        """
        target_symbol = signal["to"]
        target_price = next_prices.get(target_symbol, 0)

        if target_price <= 0:
            return

        # 1. 卖出当前持仓
        if self.held_symbol and self.held_quantity > 0:
            sell_price = next_prices.get(self.held_symbol, 0)
            if sell_price > 0:
                # 加滑点
                sell_price *= (1 - self.slippage_pct)
                proceeds = sell_price * self.held_quantity
                commission = proceeds * self.commission_rate
                self.cash += proceeds - commission

                self.trades.append({
                    "date": next_date,
                    "symbol": self.held_symbol,
                    "side": "SELL",
                    "quantity": self.held_quantity,
                    "price": round(sell_price, 4),
                    "commission": round(commission, 2),
                    "proceeds": round(proceeds - commission, 2),
                })

        # 2. 买入目标ETF
        buy_price = target_price * (1 + self.slippage_pct)
        max_quantity = int(self.cash / buy_price)
        if max_quantity > 0:
            cost = buy_price * max_quantity
            commission = cost * self.commission_rate
            self.cash -= cost + commission

            self.held_symbol = target_symbol
            self.held_quantity = max_quantity

            self.trades.append({
                "date": next_date,
                "symbol": target_symbol,
                "side": "BUY",
                "quantity": max_quantity,
                "price": round(buy_price, 4),
                "commission": round(commission, 2),
                "cost": round(cost + commission, 2),
            })

    def snapshot(self, date_str: str):
        """记录每日权益"""
        invested = 0
        if self.held_symbol and self.held_quantity > 0:
            price = self.current_prices.get(self.held_symbol, 0)
            invested = price * self.held_quantity

        total = self.cash + invested
        self.equity_curve.append({
            "date": date_str,
            "cash": round(self.cash, 2),
            "invested": round(invested, 2),
            "total": round(total, 2),
            "held": self.held_symbol,
            "positions": self.held_quantity,
        })

    def get_metrics(self) -> dict:
        """计算回测指标"""
        if not self.equity_curve:
            return {}

        values = [e["total"] for e in self.equity_curve]
        initial = self.initial_cash
        final = values[-1]

        # 总收益
        total_return = (final - initial) / initial

        # 年化收益
        days = len(values)
        years = days / 252
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # 最大回撤
        peak = values[0]
        max_dd = 0
        dd_curve = []
        for v in values:
            if v > peak:
                peak = v
            dd = (peak - v) / peak
            dd_curve.append(dd)
            if dd > max_dd:
                max_dd = dd

        # 夏普比率（年化）
        returns = []
        for i in range(1, len(values)):
            if values[i-1] > 0:
                returns.append(values[i] / values[i-1] - 1)
        if returns:
            import math
            mean_ret = sum(returns) / len(returns)
            std_ret = math.sqrt(sum((r - mean_ret)**2 for r in returns) / len(returns))
            sharpe = (mean_ret / std_ret * math.sqrt(252)) if std_ret > 0 else 0
        else:
            sharpe = 0

        # 胜率（调仓后盈利）
        rebuy_trades = [t for t in self.trades if t["side"] == "SELL"]
        win_count = sum(1 for t in rebuy_trades if t.get("proceeds", 0) > 0)
        win_rate = win_count / len(rebuy_trades) * 100 if rebuy_trades else 0

        # 调仓次数
        trade_count = len([t for t in self.trades if t["side"] == "BUY"])

        return {
            "initial_cash": initial,
            "final_value": round(final, 2),
            "total_return": round(total_return * 100, 2),
            "annual_return": round(annual_return * 100, 2),
            "max_drawdown": round(max_dd * 100, 2),
            "sharpe_ratio": round(sharpe, 2),
            "win_rate": round(win_rate, 1),
            "trade_count": trade_count,
            "trading_days": days,
            "years": round(years, 1),
            "equity_curve": self.equity_curve,
            "drawdown_curve": [{"date": e["date"], "dd": round(d*100, 2)}
                               for e, d in zip(self.equity_curve, dd_curve)],
            "trades": self.trades,
        }
