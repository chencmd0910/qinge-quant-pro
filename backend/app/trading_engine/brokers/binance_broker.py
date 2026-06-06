"""币安券商适配器 - 数字货币交易"""
from .broker_base import BrokerBase
from typing import Optional
from ..event_engine.core.event import OrderEvent, FillEvent


class BinanceBroker(BrokerBase):
    """币安(Binance)适配器

    TODO: 实现Binance API接口
    依赖: python-binance
    """

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self._connected = False

    def connect(self) -> bool:
        # TODO: 连接Binance API
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
