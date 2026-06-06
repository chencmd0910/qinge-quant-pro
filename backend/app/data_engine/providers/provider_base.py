"""市场数据提供者统一接口

所有数据源（AkShare/Tushare/yFinance）实现此接口。
上层代码只依赖接口，不关心数据来源。
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from dataclasses import dataclass


@dataclass
class BarData:
    """标准化K线数据"""
    symbol: str
    date: str           # YYYY-MM-DD
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float = 0   # 成交额
    change_pct: float = 0  # 涨跌幅
    turnover: float = 0  # 换手率


@dataclass
class TickData:
    """实时行情数据"""
    symbol: str
    name: str
    price: float
    change_pct: float
    volume: float
    amount: float
    high: float
    low: float
    open: float
    prev_close: float
    timestamp: datetime


class MarketDataProvider(ABC):
    """数据提供者基类

    所有数据源必须实现这些方法。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称"""
        ...

    @abstractmethod
    def get_bars(self, symbol: str, start_date: str, end_date: str,
                 period: str = "daily") -> List[BarData]:
        """获取历史K线

        Args:
            symbol: 标的代码（如 "510300", "AAPL"）
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"
            period: 周期 "daily"/"weekly"/"monthly"

        Returns:
            按日期升序排列的K线列表
        """
        ...

    @abstractmethod
    def get_latest(self, symbol: str) -> Optional[TickData]:
        """获取最新行情"""
        ...

    @abstractmethod
    def get_symbols(self, market: str = "") -> List[str]:
        """获取可用标的列表

        Args:
            market: 市场（如 "A股", "ETF", "US"）

        Returns:
            标的代码列表
        """
        ...

    def is_available(self) -> bool:
        """数据源是否可用"""
        return True
