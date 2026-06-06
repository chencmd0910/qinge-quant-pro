"""双均线指标策略 - IndicatorStrategy 示例

用法:
    strategy = MAIndicatorStrategy(symbol="510300", short_window=5, long_window=20)
"""
from app.strategy_engine.indicator_strategy import IndicatorStrategy


class MAIndicatorStrategy(IndicatorStrategy):
    """双均线交叉（指标模式）

    短期均线上穿长期均线 → 买入
    短期均线下穿长期均线 → 卖出
    """

    def __init__(self, symbol: str = "", short_window: int = 5, long_window: int = 20):
        self.short_window = short_window
        self.long_window = long_window
        super().__init__(name="ma_indicator", symbol=symbol)

    def setup(self):
        pass

    def indicators(self, bars):
        self.short_ma = self.sma(bars, self.short_window)
        self.long_ma = self.sma(bars, self.long_window)
        if len(bars) > self.long_window:
            prev = bars[:-1]
            self.short_ma_prev = self.sma(prev, self.short_window)
            self.long_ma_prev = self.sma(prev, self.long_window)
        else:
            self.short_ma_prev = 0
            self.long_ma_prev = 0

    def buy_signal(self, bars) -> bool:
        return (self.short_ma > self.long_ma and
                self.short_ma_prev <= self.long_ma_prev and
                self.short_ma > 0)

    def sell_signal(self, bars) -> bool:
        return (self.short_ma < self.long_ma and
                self.short_ma_prev >= self.long_ma_prev and
                self.short_ma > 0)
