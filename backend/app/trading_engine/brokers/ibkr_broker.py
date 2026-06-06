"""IBKR券商 - 美股实盘（占位）

TODO: V4实现
"""
from ..broker_base import BrokerBase, Order, OrderSide, OrderType, OrderStatus, Position, Account
from ...data_engine.providers.provider_base import Market
from typing import Optional, List


class IBKRBroker(BrokerBase):
    @property
    def name(self) -> str: return "ibkr"
    @property
    def market(self) -> Market: return Market.US_STOCK
    @property
    def currency(self) -> str: return "USD"
    def connect(self) -> bool: return False
    def disconnect(self): pass
    def send_order(self, order: Order) -> Optional[Order]: return None
    def cancel_order(self, order_id: str) -> bool: return False
    def get_positions(self) -> List[Position]: return []
    def get_account(self) -> Account: return Account(account_id="US001", market=Market.US_STOCK, broker="ibkr", currency="USD")
    def get_market_price(self, symbol: str) -> float: return 0.0
