"""CTP券商适配器 - 期货交易"""
from .broker_base import BrokerBase
from typing import Optional
from ..event_engine.core.event import OrderEvent, FillEvent


class CTPBroker(BrokerBase):
    """CTP期货券商

    TODO: 实现CTP接口
    依赖: openctp / vnpy_ctp
    """

    def __init__(self, broker_id: str = "", user_id: str = "", password: str = ""):
        self.broker_id = broker_id
        self.user_id = user_id
        self.password = password
        self._connected = False

    def connect(self) -> bool:
        # TODO: 连接CTP前置
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    def send_order(self, order: OrderEvent) -> Optional[FillEvent]:
        # TODO: CTP下单
        return None

    def cancel_order(self, order_id: str) -> bool:
        return False

    def get_position(self, symbol: str) -> dict:
        return {}

    def get_account(self) -> dict:
        return {}

    def get_market_price(self, symbol: str) -> float:
        return 0.0
