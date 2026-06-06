"""Binance data provider - cryptocurrency market (placeholder)

TODO: V5 implementation
"""
from .provider_base import MarketDataProvider, Market, Bar, Tick
from typing import List, Optional


class BinanceProvider(MarketDataProvider):
    @property
    def name(self) -> str: return "binance"
    @property
    def market(self) -> Market: return Market.CRYPTO
    def get_bars(self, symbol, start_date, end_date, period="daily") -> List[Bar]: return []
    def get_latest(self, symbol) -> Optional[Tick]: return None
    def get_symbols(self, **filters) -> List[str]: return []
