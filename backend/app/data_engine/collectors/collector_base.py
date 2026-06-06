"""数据采集器基类 - Collector

支持多种数据源：AkShare / Tushare / 东方财富 / Yahoo Finance
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from ..backtest_engine.core.bar import Bar


class CollectorBase(ABC):
    """数据采集器基类"""

    @abstractmethod
    def fetch_bars(self, symbol: str, start_date: str, end_date: str) -> List[Bar]:
        """获取历史K线数据"""
        ...

    @abstractmethod
    def fetch_latest(self, symbol: str) -> Optional[Bar]:
        """获取最新K线"""
        ...

    @abstractmethod
    def get_symbols(self) -> List[str]:
        """获取可用标的列表"""
        ...


class AkShareCollector(CollectorBase):
    """AkShare数据采集器（A股数据）

    依赖: pip install akshare
    """

    def __init__(self):
        self._available = False
        try:
            import akshare
            self._ak = akshare
            self._available = True
        except ImportError:
            pass

    @property
    def is_available(self) -> bool:
        return self._available

    def fetch_bars(self, symbol: str, start_date: str, end_date: str) -> List[Bar]:
        if not self._available:
            return []
        try:
            # AkShare获取A股日K线
            df = self._ak.stock_zh_a_hist(
                symbol=symbol, period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq"
            )
            bars = []
            for _, row in df.iterrows():
                bars.append(Bar(
                    symbol=symbol,
                    datetime=datetime.strptime(str(row['日期']), '%Y-%m-%d'),
                    open=float(row['开盘']),
                    high=float(row['最高']),
                    low=float(row['最低']),
                    close=float(row['收盘']),
                    volume=float(row['成交量']),
                    amount=float(row.get('成交额', 0)),
                    change_pct=float(row.get('涨跌幅', 0)),
                ))
            return bars
        except Exception as e:
            print(f"[AkShare] Error fetching {symbol}: {e}")
            return []

    def fetch_latest(self, symbol: str) -> Optional[Bar]:
        bars = self.fetch_bars(symbol,
                               (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
                               datetime.now().strftime('%Y-%m-%d'))
        return bars[-1] if bars else None

    def get_symbols(self) -> List[str]:
        return []
