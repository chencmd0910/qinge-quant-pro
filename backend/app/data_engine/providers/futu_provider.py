"""Futu data provider - HK stock market (placeholder)

TODO: V3 implementation
"""
from .provider_base import MarketDataProvider, Market, Bar, Tick
from typing import List, Optional


class FutuProvider(MarketDataProvider):
    @property
    def name(self) -> str: return "futu"
    @property
    def market(self) -> Market: return Market.HK_STOCK
    def get_bars(self, symbol, start_date, end_date, period="daily") -> List[Bar]: return []
    def get_latest(self, symbol) -> Optional[Tick]: return None
    def get_symbols(self, **filters) -> List[str]: return []
