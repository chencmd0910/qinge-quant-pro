"""策略管理器 - 策略的加载/注册/执行"""
from typing import Dict, List, Optional
from .strategy_base import StrategyBase
from ..event_engine.core.event import MarketEvent, SignalEvent


class StrategyManager:
    """策略管理器

    负责:
    1. 注册/注销策略
    2. 将MarketEvent分发给所有活跃策略
    3. 收集所有策略产生的SignalEvent
    """

    def __init__(self):
        self._strategies: Dict[str, StrategyBase] = {}
        self._active: Dict[str, bool] = {}

    def register(self, strategy: StrategyBase):
        """注册策略"""
        self._strategies[strategy.name] = strategy
        self._active[strategy.name] = True
        strategy.initialize()

    def unregister(self, name: str):
        """注销策略"""
        self._strategies.pop(name, None)
        self._active.pop(name, None)

    def activate(self, name: str):
        """激活策略"""
        if name in self._active:
            self._active[name] = True

    def deactivate(self, name: str):
        """停用策略"""
        if name in self._active:
            self._active[name] = False

    def on_market(self, event: MarketEvent) -> List[SignalEvent]:
        """将行情事件分发给所有活跃策略，收集信号"""
        all_signals = []
        for name, strategy in self._strategies.items():
            if self._active.get(name, False):
                signals = strategy.on_market(event)
                all_signals.extend(signals)
        return all_signals

    def get_strategy(self, name: str) -> Optional[StrategyBase]:
        """获取策略"""
        return self._strategies.get(name)

    def list_strategies(self) -> List[str]:
        """列出所有策略"""
        return list(self._strategies.keys())

    @property
    def active_count(self) -> int:
        return sum(1 for v in self._active.values() if v)
