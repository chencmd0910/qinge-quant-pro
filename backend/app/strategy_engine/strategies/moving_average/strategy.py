"""双均线交叉策略 - 事件驱动版本

这是从旧版 strategy.py 升级来的事件驱动版本。
不再直接调用 buy/sell，而是发出 SignalEvent。
"""
from typing import List
from app.strategy_engine.strategy_base import StrategyBase
from app.event_engine.core.event import MarketEvent, SignalEvent


class MovingAverageStrategy(StrategyBase):
    """双均线交叉策略（事件驱动版）

    短期均线上穿长期均线 → 买入信号
    短期均线下穿长期均线 → 卖出信号
    """

    def __init__(self, short_window: int = 5, long_window: int = 20, symbol: str = ""):
        super().__init__(name="moving_average")
        self.short_window = short_window
        self.long_window = long_window
        self.symbol = symbol
        self._prices: List[float] = []

    def initialize(self):
        self._prices = []

    def on_market(self, event: MarketEvent) -> List[SignalEvent]:
        signals = []
        symbol = event.symbol
        close = event.close

        self._prices.append(close)
        if len(self._prices) < self.long_window:
            return signals

        short_ma = sum(self._prices[-self.short_window:]) / self.short_window
        long_ma = sum(self._prices[-self.long_window:]) / self.long_window

        prev_prices = self._prices[:-1]
        if len(prev_prices) >= self.long_window:
            prev_short = sum(prev_prices[-self.short_window:]) / self.short_window
            prev_long = sum(prev_prices[-self.long_window:]) / self.long_window

            if prev_short <= prev_long and short_ma > long_ma:
                signals.append(self.emit_signal(
                    symbol=symbol, direction="BUY", strength=1.0,
                    price=close, reason=f"金叉: MA{self.short_window}={short_ma:.2f} > MA{self.long_window}={long_ma:.2f}"
                ))
            elif prev_short >= prev_long and short_ma < long_ma:
                signals.append(self.emit_signal(
                    symbol=symbol, direction="SELL", strength=1.0,
                    price=close, reason=f"死叉: MA{self.short_window}={short_ma:.2f} < MA{self.long_window}={long_ma:.2f}"
                ))

        return signals
