"""
ParquetProvider - 基于本地Parquet数据的MarketDataProvider实现

替代AkShareProvider，零网络延迟，2核2G友好。
继承 MarketDataProvider 接口，策略引擎无需改动即可切换。
"""
from typing import List, Optional
import sys
import os

# 确保能导入 kline_parquet
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kline_parquet import get_kline_engine

from .provider_base import MarketDataProvider, Market, Bar, Tick


class ParquetProvider(MarketDataProvider):
    """本地Parquet K线数据提供者

    优势：
    - 零网络延迟（83MB数据全在磁盘上）
    - 按需加载（只读需要的股票到内存）
    - zstd 压缩（4965只 × 2年日线 = 83MB）
    - 批量API get_bars_batch() 比逐只调用快 20-50 倍
    """

    def __init__(self):
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = get_kline_engine()
        return self._engine

    @property
    def name(self) -> str:
        return "parquet"

    @property
    def market(self) -> Market:
        return Market.A_SHARE

    def is_available(self) -> bool:
        """检查Parquet数据是否可用"""
        try:
            stats = self.engine.get_stats()
            return stats.get("stock_count", 0) > 0
        except Exception:
            return False

    def get_bars(self, symbol: str, start_date: str, end_date: str,
                 period: str = "daily") -> List[Bar]:
        """从Parquet读取单只股票K线

        Args:
            symbol: 支持多种格式 → 600519 / 600519.SH / 600519.SZ
        """
        code = symbol.split('.')[0] if '.' in symbol else symbol

        try:
            df = self.engine.load_stock_range(code, start_date, end_date)
            if df is None or len(df) == 0:
                return []

            suffix = ".SH" if code.startswith('6') else ".SZ"
            bars = []
            for _, row in df.iterrows():
                bars.append(Bar(
                    symbol=f"{code}{suffix}",
                    market=Market.A_SHARE,
                    date=str(row['date'])[:10],
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=float(row['volume']),
                    amount=0,
                    change_pct=0,
                    turnover=0,
                ))
            return bars
        except Exception as e:
            print(f"[ParquetProvider] Error loading {code}: {e}")
            return []

    def get_latest(self, symbol: str) -> Optional[Tick]:
        """获取最新行情（取最后一天K线）"""
        code = symbol.split('.')[0] if '.' in symbol else symbol

        try:
            df = self.engine.load_stock(code)
            if df is None or len(df) == 0:
                return None

            row = df.iloc[-1]
            suffix = ".SH" if code.startswith('6') else ".SZ"
            return Tick(
                symbol=f"{code}{suffix}",
                market=Market.A_SHARE,
                name=row.get('name', code),
                price=float(row['close']),
                change_pct=0,
                volume=float(row['volume']),
                amount=0,
                high=float(row['high']),
                low=float(row['low']),
                open=float(row['open']),
                prev_close=0,
                timestamp=None,
            )
        except Exception as e:
            print(f"[ParquetProvider] Latest error for {code}: {e}")
            return None

    def get_symbols(self, **filters) -> List[str]:
        """获取可用标的列表"""
        try:
            codes = self.engine.get_available_stocks()
            result = []
            for code in codes:
                if code.startswith('6'):
                    result.append(f"{code}.SH")
                else:
                    result.append(f"{code}.SZ")
            return result
        except Exception:
            return []

    def get_bars_batch(self, codes: List[str], start_date: str, end_date: str) -> dict:
        """批量获取多只股票K线（性能优化版）

        使用 KlineDataEngine.load_basket_pivot()，一次读取+透视。
        比逐只调用 get_bars() 快 20-50 倍。

        Returns:
            {code: List[Bar]}
        """
        clean_codes = [c.split('.')[0] for c in codes]
        try:
            closes_df = self.engine.get_closes(clean_codes, start_date, end_date)
            if closes_df.empty:
                return {}

            result = {}
            for code in clean_codes:
                if code not in closes_df.columns:
                    continue
                series = closes_df[code].dropna()
                if len(series) == 0:
                    continue

                suffix = ".SH" if code.startswith('6') else ".SZ"
                bars = [
                    Bar(
                        symbol=f"{code}{suffix}",
                        market=Market.A_SHARE,
                        date=str(d)[:10],
                        open=0, high=0, low=0,
                        close=float(v),
                        volume=0, amount=0, change_pct=0, turnover=0,
                    )
                    for d, v in series.items()
                ]
                result[code] = bars
            return result
        except Exception as e:
            print(f"[ParquetProvider] Batch error: {e}")
            return {}
