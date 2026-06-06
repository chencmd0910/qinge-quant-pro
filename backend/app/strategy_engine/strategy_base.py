"""策略基类 - 事件驱动版本

所有策略继承此类，实现 initialize() 和 on_event() 方法。
策略不直接下单，而是发出 SignalEvent，由风控引擎审核后转为 OrderEvent。
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from ..event_engine.core.event import Event, EventType, MarketEvent, SignalEvent
from ..backtest_engine.core.bar import Bar


class StrategyBase(ABC):
    """策略基类（事件驱动版本）

    子类实现:
        initialize() - 初始化参数
        on_market(event: MarketEvent) - 处理行情事件，返回SignalEvent列表
    """

    def __init__(self, name: str = "unnamed"):
        self.name = name
        self._signals: List[SignalEvent] = []

    @abstractmethod
    def initialize(self):
        """初始化策略参数"""
        ...

    @abstractmethod
    def on_market(self, event: MarketEvent) -> List[SignalEvent]:
        """处理行情事件

        Args:
            event: 包含最新K线数据的行情事件

        Returns:
            信号事件列表（可以为空）
        """
        ...

    def on_event(self, event: Event) -> List[SignalEvent]:
        """事件分发入口"""
        if event.type == EventType.MARKET:
            return self.on_market(event)
        return []

    def emit_signal(self, symbol: str, direction: str, strength: float = 1.0,
                    price: float = 0, quantity: int = 0, reason: str = "") -> SignalEvent:
        """发出交易信号"""
        signal = SignalEvent(data={
            "symbol": symbol,
            "direction": direction,
            "strength": strength,
            "strategy": self.name,
            "price": price,
            "quantity": quantity,
            "reason": reason,
        })
        self._signals.append(signal)
        return signal

    def clear_signals(self):
        """清空信号"""
        self._signals.clear()

    @property
    def pending_signals(self) -> List[SignalEvent]:
        return self._signals.copy()
