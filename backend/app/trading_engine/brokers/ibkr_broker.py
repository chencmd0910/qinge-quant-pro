"""IBKR券商适配器 - 美股/全球市场"""
from .broker_base import BrokerBase
from typing import Optional
from ..event_engine.core.event import OrderEvent, FillEvent


class IBKRBroker(BrokerBase):
    """盈透证券(IBKR)适配器

    TODO: 实现IBKR TWS/Gateway接口
    依赖: ib_insync
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self._connected = False

    def connect(self) -> bool:
        # TODO: 连接TWS/Gateway
        return False

    def disconnect(self):
        self._connected = False

    def send_order(self, order: OrderEvent) -> Optional[FillEvent]:
        return None

    def cancel_order(self, order_id: str) -> bool:
        return False

    def get_position(self, symbol: str) -> dict:
        return {}

    def get_account(self) -> dict:
        return {}

    def get_market_price(self, symbol: str) -> float:
        return 0.0
