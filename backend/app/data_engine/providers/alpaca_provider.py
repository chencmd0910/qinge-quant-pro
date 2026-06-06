"""Alpaca data provider - US stock market (placeholder)

TODO: V4 implementation
"""
from .provider_base import MarketDataProvider, Market, Bar, Tick
from typing import List, Optional


class AlpacaProvider(MarketDataProvider):
    @property
    def name(self) -> str: return "alpaca"
    @property
    def market(self) -> Market: return Market.US_STOCK
    def get_bars(self, symbol, start_date, end_date, period="daily") -> List[Bar]: return []
    def get_latest(self, symbol) -> Optional[Tick]: return None
    def get_symbols(self, **filters) -> List[str]: return []
