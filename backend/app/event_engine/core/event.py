"""事件定义 - 量化系统的核心数据流

流程：
  行情(MarketEvent) → 策略 → 信号(SignalEvent) → 风控 → 订单(OrderEvent) → 券商 → 成交(FillEvent) → 持仓更新
"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


class EventType(Enum):
    """事件类型"""
    MARKET = "MARKET"       # 行情事件：新的K线/Tick到达
    SIGNAL = "SIGNAL"       # 信号事件：策略产生买卖信号
    ORDER = "ORDER"         # 订单事件：风控通过，发送到券商
    FILL = "FILL"           # 成交事件：券商回报成交
    RISK = "RISK"           # 风控事件：风控拒绝/警告
    TIMER = "TIMER"         # 定时事件：心跳/定时任务
    LOG = "LOG"             # 日志事件


@dataclass
class Event:
    """基础事件"""
    type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return f"Event({self.type.value}, {self.timestamp.strftime('%H:%M:%S')})"


@dataclass
class MarketEvent(Event):
    """行情事件 - 新K线到达时触发

    data字段:
        symbol: 标的代码
        open/high/low/close/volume/amount: OHLCV数据
        datetime: 时间戳
        change_pct: 涨跌幅
    """
    type: EventType = EventType.MARKET

    @property
    def symbol(self) -> str:
        return self.data.get("symbol", "")

    @property
    def close(self) -> float:
        return self.data.get("close", 0.0)

    @property
    def bar_datetime(self) -> Optional[datetime]:
        return self.data.get("datetime")


@dataclass
class SignalEvent(Event):
    """信号事件 - 策略产出

    data字段:
        symbol: 标的代码
        direction: BUY/SELL/HOLD
        strength: 信号强度 0~1
        strategy: 来源策略名
        reason: 信号原因
        target_weight: 目标仓位权重(可选)
    """
    type: EventType = EventType.SIGNAL

    @property
    def symbol(self) -> str:
        return self.data.get("symbol", "")

    @property
    def direction(self) -> str:
        return self.data.get("direction", "HOLD")

    @property
    def strength(self) -> float:
        return self.data.get("strength", 0.0)


@dataclass
class OrderEvent(Event):
    """订单事件 - 风控通过后发送给券商

    data字段:
        symbol: 标的代码
        side: BUY/SELL
        quantity: 数量
        price: 限价(0=市价)
        order_type: MARKET/LIMIT
        strategy: 来源策略
    """
    type: EventType = EventType.ORDER

    @property
    def symbol(self) -> str:
        return self.data.get("symbol", "")

    @property
    def side(self) -> str:
        return self.data.get("side", "")

    @property
    def quantity(self) -> int:
        return self.data.get("quantity", 0)

    @property
    def price(self) -> float:
        return self.data.get("price", 0.0)


@dataclass
class FillEvent(Event):
    """成交事件 - 券商回报

    data字段:
        symbol: 标的代码
        side: BUY/SELL
        quantity: 成交数量
        price: 成交价格
        commission: 手续费
        slippage: 滑点
        order_id: 订单号
    """
    type: EventType = EventType.FILL

    @property
    def symbol(self) -> str:
        return self.data.get("symbol", "")

    @property
    def side(self) -> str:
        return self.data.get("side", "")

    @property
    def quantity(self) -> int:
        return self.data.get("quantity", 0)

    @property
    def fill_price(self) -> float:
        return self.data.get("price", 0.0)

    @property
    def commission(self) -> float:
        return self.data.get("commission", 0.0)
