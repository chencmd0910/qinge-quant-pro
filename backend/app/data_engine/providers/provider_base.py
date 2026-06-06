"""统一数据提供者接口 - 全球多市场设计

所有市场（A股/港股/美股/加密）实现此接口。
策略层永远不知道底层是哪个市场。

市场代码规范:
    A股:    600519.SH, 000001.SZ, 510300.SH
    港股:   00700.HK, 09988.HK
    美股:   AAPL.US, TSLA.US, SPY.US
    加密:   BTCUSDT, ETHUSDT
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class Market(Enum):
    """市场类型"""
    A_SHARE = "A股"
    HK_STOCK = "港股"
    US_STOCK = "美股"
    CRYPTO = "加密货币"
    FUTURES = "期货"


@dataclass
class Bar:
    """统一K线数据 - 所有市场通用"""
    symbol: str         # 标准代码: 600519.SH / AAPL.US / BTCUSDT
    market: Market      # 市场类型
    date: str           # YYYY-MM-DD
    open: float
    high: float
    low: float
    close: float
    volume: float       # 成交量
    amount: float = 0   # 成交额
    change_pct: float = 0  # 涨跌幅
    turnover: float = 0    # 换手率


@dataclass
class Tick:
    """统一实时行情 - 所有市场通用"""
    symbol: str
    market: Market
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
    # 加密货币额外字段
    bid: float = 0          # 买一价
    ask: float = 0          # 卖一价
    open_interest: float = 0  # 持仓量（期货/合约）


class MarketDataProvider(ABC):
    """统一数据提供者接口

    实现此接口即可接入任何市场。
    策略层只依赖此接口，不关心具体市场。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """提供者名称: 'akshare', 'futu', 'alpaca', 'binance'"""
        ...

    @property
    @abstractmethod
    def market(self) -> Market:
        """此提供者对应的市场"""
        ...

    @abstractmethod
    def get_bars(self, symbol: str, start_date: str, end_date: str,
                 period: str = "daily") -> List[Bar]:
        """获取历史K线

        Args:
            symbol: 标的代码 (600519.SH / AAPL.US / BTCUSDT)
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            period: 周期 daily/weekly/monthly/1min/5min

        Returns:
            按日期升序排列的K线列表
        """
        ...

    @abstractmethod
    def get_latest(self, symbol: str) -> Optional[Tick]:
        """获取最新行情"""
        ...

    @abstractmethod
    def get_symbols(self, **filters) -> List[str]:
        """获取可用标的列表

        Args:
            **filters: 过滤条件
                market: 市场
                sector: 行业
                keyword: 关键词

        Returns:
            标准代码列表
        """
        ...

    def is_available(self) -> bool:
        """数据源是否可用"""
        return True

    def get_trading_calendar(self, start_date: str, end_date: str) -> List[str]:
        """获取交易日历（可选实现）"""
        return []
