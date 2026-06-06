"""事件驱动引擎 - 青鳄量化核心调度器

回测模式: 同步处理，一个事件处理完再处理下一个
实盘模式: 异步处理，事件到达立即分发
"""
from typing import Callable, List
from app.event_engine.core.event import Event, EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent
from app.event_engine.event_queue import EventQueue


class EventEngine:
    """事件驱动引擎

    用法:
        engine = EventEngine()
        engine.register(EventType.MARKET, my_market_handler)
        engine.register(EventType.SIGNAL, my_signal_handler)

        # 回测模式：手动灌入事件
        engine.put(MarketEvent(data={...}))
        engine.run_once()  # 处理一个事件
        # 或
        engine.run_all()   # 处理所有待处理事件
    """

    def __init__(self, async_mode: bool = False):
        self.queue = EventQueue(async_mode=async_mode)
        self._running = False
        self._async_mode = async_mode

    def register(self, event_type: EventType, handler: Callable):
        """注册事件处理器"""
        self.queue.register(event_type, handler)

    def put(self, event: Event):
        """放入事件"""
        self.queue.put(event)

    def run_once(self):
        """处理一个事件"""
        event = self.queue.get()
        if event:
            self.queue.dispatch(event)
            return True
        return False

    def run_all(self):
        """处理所有待处理事件"""
        self.queue.process_all()

    def start(self):
        """启动引擎（实盘模式）"""
        self._running = True

    def stop(self):
        """停止引擎"""
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def pending_events(self) -> int:
        return self.queue.size
