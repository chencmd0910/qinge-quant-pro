"""券商基类 - 统一交易接口

所有券商适配器（CTP/IBKR/Binance）都实现这个接口。
回测引擎的SimBroker也实现这个接口。
"""
from abc import ABC, abstractmethod
from typing import Optional
from ..event_engine.core.event import OrderEvent, FillEvent


class BrokerBase(ABC):
    """券商基类

    回测/实盘/模拟盘都通过这个接口下单。
    """

    @abstractmethod
    def connect(self) -> bool:
        """连接券商"""
        ...

    @abstractmethod
    def disconnect(self):
        """断开连接"""
        ...

    @abstractmethod
    def send_order(self, order: OrderEvent) -> Optional[FillEvent]:
        """发送订单，返回成交事件"""
        ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        ...

    @abstractmethod
    def get_position(self, symbol: str) -> dict:
        """查询持仓"""
        ...

    @abstractmethod
    def get_account(self) -> dict:
        """查询账户"""
        ...

    @abstractmethod
    def get_market_price(self, symbol: str) -> float:
        """获取最新价格"""
        ...
