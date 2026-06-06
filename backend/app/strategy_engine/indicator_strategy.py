"""指标策略基类 - IndicatorStrategy

用于快速研究和回测。
通过定义 buy/sell 信号条件自动生成 SignalEvent。

用法:
    class MyMAStrategy(IndicatorStrategy):
        def setup(self):
            self.short = 5
            self.long = 20

        def indicators(self, bars):
            self.short_ma = self.sma(bars, self.short)
            self.long_ma = self.sma(bars, self.long)

        def buy_signal(self, bars):
            return self.short_ma > self.long_ma and self.short_ma_prev <= self.long_ma_prev

        def sell_signal(self, bars):
            return self.short_ma < self.long_ma and self.short_ma_prev >= self.long_ma_prev
"""
from abc import abstractmethod
from typing import List, Optional
from ..event_engine.core.event import MarketEvent, SignalEvent
from .strategy_base import StrategyBase


class IndicatorStrategy(StrategyBase):
    """指标驱动策略基类

    子类实现:
        setup() - 设置参数
        indicators(bars) - 计算指标
        buy_signal(bars) - 买入条件
        sell_signal(bars) - 卖出条件
    """

    def __init__(self, name: str = "indicator_strategy", symbol: str = ""):
        super().__init__(name=name)
        self.symbol = symbol
        self._bar_history: List[dict] = []

    def initialize(self):
        self._bar_history = []
        self.setup()

    @abstractmethod
    def setup(self):
        """设置策略参数"""
        ...

    @abstractmethod
    def indicators(self, bars: List[dict]):
        """计算技术指标"""
        ...

    @abstractmethod
    def buy_signal(self, bars: List[dict]) -> bool:
        """买入信号条件"""
        ...

    @abstractmethod
    def sell_signal(self, bars: List[dict]) -> bool:
        """卖出信号条件"""
        ...

    def on_market(self, event: MarketEvent) -> List[SignalEvent]:
        signals = []
        bar = {
            "datetime": event.bar_datetime,
            "open": event.data.get("open", 0),
            "high": event.data.get("high", 0),
            "low": event.data.get("low", 0),
            "close": event.close,
            "volume": event.data.get("volume", 0),
        }
        self._bar_history.append(bar)

        if len(self._bar_history) < 2:
            return signals

        self.indicators(self._bar_history)

        if self.buy_signal(self._bar_history):
            signals.append(self.emit_signal(
                symbol=event.symbol, direction="BUY", strength=1.0,
                price=event.close, reason="indicator_buy"
            ))
        elif self.sell_signal(self._bar_history):
            signals.append(self.emit_signal(
                symbol=event.symbol, direction="SELL", strength=1.0,
                price=event.close, reason="indicator_sell"
            ))

        return signals

    # === 辅助指标函数 ===

    def sma(self, bars: List[dict], period: int) -> float:
        """简单移动平均"""
        if len(bars) < period:
            return 0
        return sum(b["close"] for b in bars[-period:]) / period

    def ema(self, bars: List[dict], period: int) -> float:
        """指数移动平均"""
        if len(bars) < period:
            return 0
        closes = [b["close"] for b in bars]
        multiplier = 2 / (period + 1)
        ema_val = sum(closes[:period]) / period
        for price in closes[period:]:
            ema_val = (price - ema_val) * multiplier + ema_val
        return ema_val

    def rsi(self, bars: List[dict], period: int = 14) -> float:
        """RSI"""
        if len(bars) < period + 1:
            return 50
        closes = [b["close"] for b in bars[-(period + 1):]]
        gains, losses = [], []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def atr(self, bars: List[dict], period: int = 14) -> float:
        """ATR"""
        if len(bars) < period + 1:
            return 0
        trs = []
        for i in range(1, len(bars[-(period + 1):])):
            b = bars[-(period + 1) + i]
            prev = bars[-(period + 1) + i - 1]
            tr = max(b["high"] - b["low"],
                     abs(b["high"] - prev["close"]),
                     abs(b["low"] - prev["close"]))
            trs.append(tr)
        return sum(trs[-period:]) / period

    def bollinger(self, bars: List[dict], period: int = 20, std_dev: float = 2.0):
        """布林带 -> (upper, middle, lower)"""
        if len(bars) < period:
            return (0, 0, 0)
        closes = [b["close"] for b in bars[-period:]]
        middle = sum(closes) / period
        variance = sum((c - middle) ** 2 for c in closes) / period
        std = variance ** 0.5
        return (middle + std_dev * std, middle, middle - std_dev * std)
