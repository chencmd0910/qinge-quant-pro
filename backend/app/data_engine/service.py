"""数据引擎 - 统一数据服务

支持多数据源回退：先查DB缓存，再调API获取。
"""
from typing import List, Optional, Dict
from datetime import datetime
from .providers.provider_base import MarketDataProvider, Market, Bar, Tick
from .providers.akshare_provider import AkShareProvider
from .providers.parquet_provider import ParquetProvider
from .storage.bar_storage import BarStorage


class DataEngine:
    """统一数据引擎

    策略层只调用此引擎获取数据，不直接调用Provider。
    引擎负责：缓存检查 → API获取 → 写入缓存
    """

    def __init__(self, db_session=None):
        self._providers: Dict[str, MarketDataProvider] = {}
        self._storage = BarStorage(db_session)

        # 自动注册可用Provider
        self._auto_register()

    def _auto_register(self):
        """自动注册可用的数据源，Parquet优先"""
        # 本地Parquet数据优先（零延迟）
        parquet = ParquetProvider()
        if parquet.is_available():
            self._providers["parquet"] = parquet
            self._providers["akshare"] = AkShareProvider()  # 备用
        else:
            akshare = AkShareProvider()
            if akshare.is_available():
                self._providers["akshare"] = akshare

    def add_provider(self, provider: MarketDataProvider):
        """手动注册数据源"""
        self._providers[provider.name] = provider

    def get_provider(self, name: str) -> Optional[MarketDataProvider]:
        return self._providers.get(name)

    def get_provider_by_market(self, market: Market) -> Optional[MarketDataProvider]:
        for p in self._providers.values():
            if p.market == market:
                return p
        return None

    def list_providers(self) -> List[str]:
        return list(self._providers.keys())

    def get_bars(self, symbol: str, start_date: str, end_date: str,
                 period: str = "daily", auto_cache: bool = True) -> List[Bar]:
        """获取K线数据（优先缓存）"""
        # 1. 查缓存
        if auto_cache and self._storage._db:
            cached = self._storage.load_bars(symbol, start_date, end_date)
            if cached:
                return cached

        # 2. 查Provider
        for provider in self._providers.values():
            bars = provider.get_bars(symbol, start_date, end_date, period)
            if bars:
                # 3. 写缓存
                if auto_cache:
                    self._storage.save_bars(bars)
                return bars

        return []

    def get_latest(self, symbol: str) -> Optional[Tick]:
        """获取最新行情"""
        for provider in self._providers.values():
            tick = provider.get_latest(symbol)
            if tick:
                return tick
        return None

    def get_symbols(self, market: Market = None, **filters) -> List[str]:
        """获取可用标的"""
        all_symbols = []
        for name, provider in self._providers.items():
            if market is None or provider.market == market:
                all_symbols.extend(provider.get_symbols(**filters))
        return all_symbols

    def get_cache(self, symbol: str, start_date: str, end_date: str) -> List[Bar]:
        """仅从缓存读取"""
        return self._storage.load_bars(symbol, start_date, end_date)
