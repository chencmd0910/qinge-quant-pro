"""数据管理器 - 统一数据接口

职责:
1. 从多个数据源获取行情（数据库/CSV/API）
2. 数据缓存（避免重复加载）
3. 数据标准化（统一Bar格式）
4. 为回测和实盘提供统一数据接口
5. 数据采集调度（AkShare/Tushare/东方财富）
"""
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from ..backtest_engine.core.bar import Bar


class DataManager:
    """统一数据管理器

    用法:
        dm = DataManager()
        dm.load_from_db("510300", "2023-01-01", "2024-12-31")
        dm.load_from_csv("510300", "data/510300.csv")

        bars = dm.get_bars("510300")
        latest = dm.get_latest("510300")
    """

    def __init__(self):
        self._data: Dict[str, List[Bar]] = {}      # symbol -> bars
        self._cache: Dict[str, Bar] = {}            # symbol -> latest bar
        self._sources: Dict[str, str] = {}          # symbol -> source name

    def load_from_db(self, symbol: str, start_date: str = "", end_date: str = "", db_session=None):
        """从数据库加载数据"""
        if db_session is None:
            return
        from ..models.models import MarketData
        query = db_session.query(MarketData).filter(MarketData.symbol == symbol)
        if start_date:
            query = query.filter(MarketData.trade_date >= start_date)
        if end_date:
            query = query.filter(MarketData.trade_date <= end_date)
        rows = query.order_by(MarketData.trade_date).all()

        bars = [
            Bar(symbol=r.symbol, datetime=datetime.strptime(r.trade_date, '%Y-%m-%d'),
                open=r.open, high=r.high, low=r.low, close=r.close,
                volume=r.volume or 0, amount=r.amount or 0, change_pct=r.change_pct or 0)
            for r in rows
        ]
        self._data[symbol] = bars
        self._sources[symbol] = "database"
        if bars:
            self._cache[symbol] = bars[-1]

    def load_from_csv(self, symbol: str, filepath: str):
        """从CSV文件加载数据"""
        import csv
        bars = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                bars.append(Bar(
                    symbol=symbol,
                    datetime=datetime.strptime(row.get('date', row.get('trade_date', '')), '%Y-%m-%d'),
                    open=float(row.get('open', 0)),
                    high=float(row.get('high', 0)),
                    low=float(row.get('low', 0)),
                    close=float(row.get('close', 0)),
                    volume=float(row.get('volume', 0)),
                    amount=float(row.get('amount', 0)),
                    change_pct=float(row.get('change_pct', 0)),
                ))
        self._data[symbol] = bars
        self._sources[symbol] = "csv"
        if bars:
            self._cache[symbol] = bars[-1]

    def load_bars(self, symbol: str, bars: List[Bar]):
        """直接加载Bar列表"""
        self._data[symbol] = bars
        self._sources[symbol] = "direct"
        if bars:
            self._cache[symbol] = bars[-1]

    def get_bars(self, symbol: str, limit: int = 0) -> List[Bar]:
        """获取历史K线"""
        bars = self._data.get(symbol, [])
        if limit > 0:
            return bars[-limit:]
        return bars

    def get_latest(self, symbol: str) -> Optional[Bar]:
        """获取最新K线"""
        return self._cache.get(symbol)

    def get_symbols(self) -> List[str]:
        """获取所有已加载的标的"""
        return list(self._data.keys())

    def get_bar_count(self, symbol: str) -> int:
        """获取K线数量"""
        return len(self._data.get(symbol, []))

    def clear(self):
        """清空所有数据"""
        self._data.clear()
        self._cache.clear()
        self._sources.clear()
