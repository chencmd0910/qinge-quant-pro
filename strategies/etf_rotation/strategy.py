"""ETF轮动策略示例"""
from typing import List, Dict
from backend.backtest_engine.strategy.strategy import Strategy
from backend.backtest_engine.core.bar import Bar


class ETFRotationStrategy(Strategy):
    """ETF轮动策略 - 动量排名选最强ETF"""

    def __init__(self, symbols: List[str] = None, lookback: int = 20,
                 top_n: int = 1, rebalance_days: int = 5):
        super().__init__()
        self.symbols = symbols or ["510300", "510500", "159915", "518880"]
        self.lookback = lookback
        self.top_n = top_n
        self.rebalance_days = rebalance_days
        self.price_history: Dict[str, List[float]] = {s: [] for s in self.symbols}
        self.day_count = 0

    def initialize(self):
        self.price_history = {s: [] for s in self.symbols}
        self.day_count = 0

    def on_bar(self, bar: Bar, bars: List[Bar]):
        if bar.symbol not in self.symbols:
            return

        self.price_history[bar.symbol].append(bar.close)
        self.day_count += 1

        # 每N天调仓
        if self.day_count % self.rebalance_days != 0:
            return
        if any(len(v) < self.lookback for v in self.price_history.values()):
            return

        # 计算动量（过去N天收益率）
        momentum = {}
        for sym in self.symbols:
            prices = self.price_history[sym]
            if len(prices) >= self.lookback:
                momentum[sym] = (prices[-1] / prices[-self.lookback] - 1)

        # 选最强
        ranked = sorted(momentum.items(), key=lambda x: x[1], reverse=True)
        target_symbols = [s for s, _ in ranked[:self.top_n]]

        # 卖出不在目标中的持仓
        for sym in self.symbols:
            pos = self.get_position(sym)
            if pos and pos.quantity > 0 and sym not in target_symbols:
                self.sell(sym, pos.quantity)

        # 买入目标（等权）
        total = self.get_total_value()
        per_sym = total * 0.95 / self.top_n  # 留5%现金

        for sym in target_symbols:
            pos = self.get_position(sym)
            current_value = pos.market_value if pos else 0
            target_value = per_sym
            diff = target_value - current_value

            if diff > bar.close * 100:  # 差额大于1手
                qty = int(diff / bar.close / 100) * 100
                if qty > 0:
                    self.buy(sym, qty)
