"""均线交叉策略示例"""
from typing import List
from app.backtest_engine.strategy.strategy import Strategy
from app.backtest_engine.core.bar import Bar


class MovingAverageStrategy(Strategy):
    """双均线交叉策略"""

    def __init__(self, symbol: str = "510300", short_window: int = 5, long_window: int = 20,
                 position_pct: float = 0.9):
        super().__init__()
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.position_pct = position_pct  # 仓位比例
        self.prices: List[float] = []

    def initialize(self):
        self.prices = []

    def on_bar(self, bar: Bar, bars: List[Bar]):
        if bar.symbol != self.symbol:
            return

        self.prices.append(bar.close)
        if len(self.prices) < self.long_window:
            return

        # 计算均线
        short_ma = sum(self.prices[-self.short_window:]) / self.short_window
        long_ma = sum(self.prices[-self.long_window:]) / self.long_window

        pos = self.get_position(self.symbol)
        current_qty = pos.quantity if pos else 0
        cash = self.get_cash()
        total = self.get_total_value()

        # 金叉买入
        if short_ma > long_ma and current_qty == 0:
            buy_amount = total * self.position_pct
            qty = int(buy_amount / bar.close / 100) * 100
            if qty > 0:
                self.buy(self.symbol, qty, bar.close)

        # 死叉卖出
        elif short_ma < long_ma and current_qty > 0:
            self.sell(self.symbol, current_qty, bar.close)
