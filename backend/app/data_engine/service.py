"""DataEngine服务 - 统一数据管理层

职责:
1. 管理多个数据提供者（AkShare/Tushare/yFinance）
2. 自动选择最佳数据源
3. 数据缓存（避免重复请求）
4. 数据标准化
5. 历史数据持久化到数据库
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from .providers.provider_base import MarketDataProvider, BarData, TickData


class DataEngine:
    """数据引擎 - 统一数据管理

    用法:
        engine = DataEngine()
        engine.add_provider(AkShareProvider())
        engine.add_provider(YFinanceProvider())

        bars = engine.get_bars("510300", "2024-01-01", "2024-12-31")
        latest = engine.get_latest("510300")
        symbols = engine.get_symbols("A股")
    """

    def __init__(self):
        self._providers: Dict[str, MarketDataProvider] = {}
        self._cache: Dict[str, List[BarData]] = {}  # 缓存键: "symbol_start_end"
        self._latest_cache: Dict[str, TickData] = {}
        self._cache_ttl: Dict[str, datetime] = {}
        self._cache_duration = timedelta(minutes=5)

    def add_provider(self, provider: MarketDataProvider):
        """添加数据提供者"""
        self._providers[provider.name] = provider

    def get_bars(self, symbol: str, start_date: str, end_date: str,
                 period: str = "daily", provider: str = "") -> List[BarData]:
        """获取历史K线

        优先使用指定的provider，否则按顺序尝试所有可用provider。
        结果会缓存5分钟。
        """
        cache_key = f"{symbol}_{start_date}_{end_date}_{period}"

        # 检查缓存
        if cache_key in self._cache:
            if datetime.now() - self._cache_ttl.get(cache_key, datetime.min) < self._cache_duration:
                return self._cache[cache_key]

        # 获取数据
        bars = self._fetch_bars(symbol, start_date, end_date, period, provider)

        # 缓存结果
        if bars:
            self._cache[cache_key] = bars
            self._cache_ttl[cache_key] = datetime.now()

        return bars

    def get_latest(self, symbol: str, provider: str = "") -> Optional[TickData]:
        """获取最新行情"""
        # 实时数据缓存更短
        if symbol in self._latest_cache:
            if datetime.now() - self._cache_ttl.get(f"latest_{symbol}", datetime.min) < timedelta(seconds=10):
                return self._latest_cache[symbol]

        tick = self._fetch_latest(symbol, provider)
        if tick:
            self._latest_cache[symbol] = tick
            self._cache_ttl[f"latest_{symbol}"] = datetime.now()
        return tick

    def get_symbols(self, market: str = "A股", provider: str = "") -> List[str]:
        """获取标的列表"""
        p = self._get_provider(provider)
        if p:
            return p.get_symbols(market)
        return []

    def list_providers(self) -> List[str]:
        """列出所有已注册的数据源"""
        return list(self._providers.keys())

    def list_available_providers(self) -> List[str]:
        """列出所有可用的数据源"""
        return [name for name, p in self._providers.items() if p.is_available()]

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        self._latest_cache.clear()
        self._cache_ttl.clear()

    def _fetch_bars(self, symbol: str, start_date: str, end_date: str,
                    period: str, provider_name: str) -> List[BarData]:
        """从数据源获取K线"""
        if provider_name:
            p = self._providers.get(provider_name)
            if p and p.is_available():
                return p.get_bars(symbol, start_date, end_date, period)
            return []

        # 按优先级尝试
        for name, p in self._providers.items():
            if p.is_available():
                bars = p.get_bars(symbol, start_date, end_date, period)
                if bars:
                    return bars
        return []

    def _fetch_latest(self, symbol: str, provider_name: str) -> Optional[TickData]:
        """从数据源获取最新行情"""
        if provider_name:
            p = self._providers.get(provider_name)
            if p and p.is_available():
                return p.get_latest(symbol)
            return None

        for name, p in self._providers.items():
            if p.is_available():
                tick = p.get_latest(symbol)
                if tick:
                    return tick
        return None

    def _get_provider(self, name: str) -> Optional[MarketDataProvider]:
        if name:
            return self._providers.get(name)
        # 返回第一个可用的
        for p in self._providers.values():
            if p.is_available():
                return p
        return None
