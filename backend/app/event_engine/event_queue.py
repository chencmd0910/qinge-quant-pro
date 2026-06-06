"""事件队列 - 线程安全的FIFO队列"""
import queue
from typing import Optional
from app.event_engine.core.event import Event, EventType


class EventQueue:
    """事件队列

    回测模式下同步处理（无锁），实盘模式下异步处理。
    """

    def __init__(self, async_mode: bool = False):
        self._async_mode = async_mode
        self._queue: queue.Queue = queue.Queue()
        self._handlers: dict = {}  # EventType -> [handler_fn]
        self._history: list = []   # 事件历史（调试用）

    def put(self, event: Event):
        """放入事件"""
        self._queue.put(event)
        self._history.append(event)

    def get(self) -> Optional[Event]:
        """取出事件（非阻塞）"""
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def register(self, event_type: EventType, handler):
        """注册事件处理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def dispatch(self, event: Event):
        """分发事件到注册的处理器"""
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            handler(event)

    def process_all(self):
        """处理队列中所有事件（回测模式用）"""
        while True:
            event = self.get()
            if event is None:
                break
            self.dispatch(event)

    def clear(self):
        """清空队列"""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    @property
    def size(self) -> int:
        return self._queue.qsize()

    @property
    def history_count(self) -> int:
        return len(self._history)
