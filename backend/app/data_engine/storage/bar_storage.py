"""PostgreSQL/SQLite K线存储

将获取的历史K线持久化到数据库，避免重复下载。
"""
from typing import List, Optional
from datetime import datetime
from ..providers.provider_base import BarData


class BarStorage:
    """K线数据存储

    默认使用SQLite（开发），生产环境用PostgreSQL。
    """

    def __init__(self, db_session=None):
        self._db = db_session

    def save_bars(self, bars: List[BarData]) -> int:
        """保存K线到数据库

        Returns:
            新增条数
        """
        if not self._db or not bars:
            return 0
        from ...models.models import MarketData
        saved = 0
        for bar in bars:
            exists = self._db.query(MarketData).filter(
                MarketData.symbol == bar.symbol,
                MarketData.trade_date == bar.date
            ).first()
            if not exists:
                self._db.add(MarketData(
                    symbol=bar.symbol, trade_date=bar.date,
                    open=bar.open, high=bar.high, low=bar.low, close=bar.close,
                    volume=bar.volume, amount=bar.amount, change_pct=bar.change_pct,
                ))
                saved += 1
        if saved:
            self._db.commit()
        return saved

    def load_bars(self, symbol: str, start_date: str, end_date: str) -> List[BarData]:
        """从数据库加载K线"""
        if not self._db:
            return []
        from ...models.models import MarketData
        rows = self._db.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.trade_date >= start_date,
            MarketData.trade_date <= end_date,
        ).order_by(MarketData.trade_date).all()
        return [
            BarData(
                symbol=r.symbol, date=r.trade_date,
                open=r.open, high=r.high, low=r.low, close=r.close,
                volume=r.volume or 0, amount=r.amount or 0, change_pct=r.change_pct or 0,
            )
            for r in rows
        ]

    def exists(self, symbol: str, date: str) -> bool:
        """检查某天数据是否已存在"""
        if not self._db:
            return False
        from ...models.models import MarketData
        return self._db.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.trade_date == date,
        ).first() is not None

    def get_latest_date(self, symbol: str) -> Optional[str]:
        """获取某标的最新数据日期"""
        if not self._db:
            return None
        from ...models.models import MarketData
        row = self._db.query(MarketData).filter(
            MarketData.symbol == symbol
        ).order_by(MarketData.trade_date.desc()).first()
        return row.trade_date if row else None

    def get_symbol_count(self) -> int:
        """获取存储的标的数量"""
        if not self._db:
            return 0
        from ...models.models import MarketData
        return self._db.query(MarketData.symbol).distinct().count()
