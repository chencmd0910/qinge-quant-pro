"""QMT券商 - A股实盘（占位）

QMT (Quick Market Trading) 迅投量化客户端。
依赖: xtquant
"""
from typing import Optional, List
from ..broker_base import BrokerBase, Order, OrderSide, OrderType, OrderStatus, Position, Account
from ...data_engine.providers.provider_base import Market


class QMTBroker(BrokerBase):
    """QMT实盘券商 - A股

    TODO: 实现QMT接口
    """

    def __init__(self, path: str = "", account: str = ""):
        self._path = path
        self._account = account
        self._connected = False

    @property
    def name(self) -> str:
        return "qmt"

    @property
    def market(self) -> Market:
        return Market.A_SHARE

    @property
    def currency(self) -> str:
        return "CNY"

    def connect(self) -> bool:
        # TODO: 连接QMT
        return False

    def disconnect(self):
        self._connected = False

    def send_order(self, order: Order) -> Optional[Order]:
        # TODO: QMT下单
        order.status = OrderStatus.REJECTED
        order.reason = "QMT未实现"
        return order

    def cancel_order(self, order_id: str) -> bool:
        return False

    def get_positions(self) -> List[Position]:
        return []

    def get_account(self) -> Account:
        return Account(account_id="QMT_A", market=Market.A_SHARE, broker="qmt", currency="CNY")

    def get_market_price(self, symbol: str) -> float:
        return 0.0
