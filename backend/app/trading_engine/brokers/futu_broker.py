"""Futu券商 - 港股实盘（占位）

TODO: V3实现
"""
from ..broker_base import BrokerBase, Order, OrderSide, OrderType, OrderStatus, Position, Account
from ...data_engine.providers.provider_base import Market
from typing import Optional, List


class FutuBroker(BrokerBase):
    @property
    def name(self) -> str: return "futu"
    @property
    def market(self) -> Market: return Market.HK_STOCK
    @property
    def currency(self) -> str: return "HKD"
    def connect(self) -> bool: return False
    def disconnect(self): pass
    def send_order(self, order: Order) -> Optional[Order]: return None
    def cancel_order(self, order_id: str) -> bool: return False
    def get_positions(self) -> List[Position]: return []
    def get_account(self) -> Account: return Account(account_id="HK001", market=Market.HK_STOCK, broker="futu", currency="HKD")
    def get_market_price(self, symbol: str) -> float: return 0.0
