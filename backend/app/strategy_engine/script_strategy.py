"""脚本策略基类 - ScriptStrategy

用于实盘和复杂逻辑。
提供上下文对象 ctx，支持 on_init / on_bar / on_order 生命周期。

用法:
    class MyTrendStrategy(ScriptStrategy):
        def on_init(self):
            self.period = 20
            self.position_held = False

        def on_bar(self, ctx):
            bars = ctx.get_bars(self.symbol, self.period)
            if len(bars) < self.period:
                return
            ma = sum(b.close for b in bars[-self.period:]) / self.period
            if not self.position_held and ctx.close > ma:
                ctx.buy(self.symbol, quantity=100)
                self.position_held = True
            elif self.position_held and ctx.close < ma:
                ctx.sell(self.symbol, quantity=100)
                self.position_held = False

        def on_order(self, ctx, order):
            print(f"Order filled: {order}")
"""
from abc import abstractmethod
from typing import List, Optional, Dict, Any
from ..event_engine.core.event import MarketEvent, SignalEvent, FillEvent
from .strategy_base import StrategyBase
from ..backtest_engine.core.bar import Bar


class StrategyContext:
    """策略上下文 - 提供给脚本策略的运行环境"""

    def __init__(self):
        self.symbol: str = ""
        self.close: float = 0
        self.open: float = 0
        self.high: float = 0
        self.low: float = 0
        self.volume: float = 0
        self.datetime = None
        self._bar_cache: Dict[str, List[Bar]] = {}
        self._signals: List[SignalEvent] = []
        self._portfolio = None

    def get_bars(self, symbol: str, count: int = 100) -> List[Bar]:
        """获取历史K线"""
        bars = self._bar_cache.get(symbol, [])
        return bars[-count:] if count > 0 else bars

    def buy(self, symbol: str, quantity: int = 0, price: float = 0, reason: str = ""):
        """发出买入信号"""
        signal = SignalEvent(data={
            "symbol": symbol, "direction": "BUY", "strength": 1.0,
            "price": price or self.close, "quantity": quantity, "reason": reason or "script_buy",
        })
        self._signals.append(signal)

    def sell(self, symbol: str, quantity: int = 0, price: float = 0, reason: str = ""):
        """发出卖出信号"""
        signal = SignalEvent(data={
            "symbol": symbol, "direction": "SELL", "strength": 1.0,
            "price": price or self.close, "quantity": quantity, "reason": reason or "script_sell",
        })
        self._signals.append(signal)

    def get_position(self, symbol: str) -> int:
        """获取持仓数量"""
        if self._portfolio:
            pos = self._portfolio.get_position(symbol)
            return pos.quantity if pos else 0
        return 0

    def get_cash(self) -> float:
        """获取可用现金"""
        if self._portfolio:
            return self._portfolio.cash
        return 0

    def get_total_value(self) -> float:
        """获取总资产"""
        if self._portfolio:
            return self._portfolio.total_value
        return 0


class ScriptStrategy(StrategyBase):
    """脚本驱动策略基类

    子类实现:
        on_init() - 初始化
        on_bar(ctx) - 每根K线触发
        on_order(ctx, order) - 订单成交触发（可选）
    """

    def __init__(self, name: str = "script_strategy"):
        super().__init__(name=name)
        self.ctx = StrategyContext()
        self._bar_history: Dict[str, List[Bar]] = {}

    def initialize(self):
        self.ctx = StrategyContext()
        self._bar_history = {}
        self.on_init()

    @abstractmethod
    def on_init(self):
        """初始化策略参数"""
        ...

    @abstractmethod
    def on_bar(self, ctx: StrategyContext):
        """每根K线触发"""
        ...

    def on_order(self, ctx: StrategyContext, order: FillEvent):
        """订单成交触发（可选重写）"""
        pass

    def on_market(self, event: MarketEvent) -> List[SignalEvent]:
        symbol = event.symbol
        bar = Bar(
            symbol=symbol,
            datetime=event.bar_datetime,
            open=event.data.get("open", 0),
            high=event.data.get("high", 0),
            low=event.data.get("low", 0),
            close=event.close,
            volume=event.data.get("volume", 0),
        )

        if symbol not in self._bar_history:
            self._bar_history[symbol] = []
        self._bar_history[symbol].append(bar)

        self.ctx.symbol = symbol
        self.ctx.close = bar.close
        self.ctx.open = bar.open
        self.ctx.high = bar.high
        self.ctx.low = bar.low
        self.ctx.volume = bar.volume
        self.ctx.datetime = bar.datetime
        self.ctx._bar_cache = self._bar_history
        self.ctx._signals = []

        self.on_bar(self.ctx)

        return self.ctx._signals
