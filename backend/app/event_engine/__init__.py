"""事件引擎 - 青鳄量化核心
所有模块通过事件通信，实现解耦。
回测/实盘/模拟盘共用同一套事件系统。
"""
from .core.event import Event, EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent
from .event_queue import EventQueue
from .engine import EventEngine

__all__ = [
    "Event", "EventType",
    "MarketEvent", "SignalEvent", "OrderEvent", "FillEvent",
    "EventQueue", "EventEngine",
]
