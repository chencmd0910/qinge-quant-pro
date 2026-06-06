"""Binance券商 - 加密货币（占位）

TODO: V5实现
"""
from ..broker_base import BrokerBase, Order, OrderSide, OrderType, OrderStatus, Position, Account
from ...data_engine.providers.provider_base import Market
from typing import Optional, List


class BinanceBroker(BrokerBase):
    @property
    def name(self) -> str: return "binance"
    @property
    def market(self) -> Market: return Market.CRYPTO
    @property
    def currency(self) -> str: return "USDT"
    def connect(self) -> bool: return False
    def disconnect(self): pass
    def send_order(self, order: Order) -> Optional[Order]: return None
    def cancel_order(self, order_id: str) -> bool: return False
    def get_positions(self) -> List[Position]: return []
    def get_account(self) -> Account: return Account(account_id="C001", market=Market.CRYPTO, broker="binance", currency="USDT")
    def get_market_price(self, symbol: str) -> float: return 0.0
