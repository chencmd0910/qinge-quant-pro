"""
青鳄量化 - Parquet K线数据引擎
基于本地Parquet分片 + SQLite索引，支持按需加载、子集查询、缓存

内存优化：
- 单文件加载 → ~20KB (一只股票)
- 沪深300加载 → ~6MB
- 全市场加载 → ~80MB (仅回测时)
"""
import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from functools import lru_cache

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "klines"
PARQUET_DIR = DATA_DIR / "parquet"
INDEX_DB = DATA_DIR / "kline_index.db"


class KlineDataEngine:
    """Parquet分片K线数据引擎"""

    def __init__(self):
        self.parquet_dir = PARQUET_DIR
        self.index_db = INDEX_DB
        self._cache = {}  # Simple LRU-like cache
        self._max_cache = 50  # Max stocks in memory

    # ===== 元数据 =====
    def get_index_db(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.index_db))

    def get_stock_list(self) -> pd.DataFrame:
        """获取所有可用的股票列表"""
        db = self.get_index_db()
        df = pd.read_sql_query(
            "SELECT code, name, start_date, end_date, row_count FROM kline_index ORDER BY code",
            db
        )
        db.close()
        return df

    def get_available_stocks(self) -> List[str]:
        """获取所有可用的股票代码列表"""
        db = self.get_index_db()
        codes = [r[0] for r in db.execute("SELECT code FROM kline_index ORDER BY code").fetchall()]
        db.close()
        return codes

    def get_trade_dates(self, start: str = None, end: str = None) -> List[str]:
        """获取交易日历"""
        db = self.get_index_db()
        query = "SELECT trade_date FROM trade_calendar"
        params = []
        if start:
            query += " WHERE trade_date >= ?"
            params.append(start)
        if end:
            query += (" AND " if start else " WHERE ") + "trade_date <= ?"
            params.append(end)
        query += " ORDER BY trade_date"
        dates = [r[0] for r in db.execute(query, params).fetchall()]
        db.close()
        return dates

    def get_stats(self) -> dict:
        """获取数据统计"""
        db = self.get_index_db()
        stock_cnt = db.execute("SELECT COUNT(*) FROM kline_index").fetchone()[0]
        total_rows = db.execute("SELECT SUM(row_count) FROM kline_index").fetchone()[0]
        min_date = db.execute("SELECT MIN(start_date) FROM kline_index").fetchone()[0]
        max_date = db.execute("SELECT MAX(end_date) FROM kline_index").fetchone()[0]
        trade_days = db.execute("SELECT COUNT(*) FROM trade_calendar").fetchone()[0]
        db.close()

        total_size = sum(f.stat().st_size for f in self.parquet_dir.glob("*.parquet"))
        return {
            "stock_count": stock_cnt,
            "total_rows": total_rows,
            "total_size_mb": round(total_size / 1024 / 1024, 1),
            "date_range": f"{min_date} ~ {max_date}",
            "trading_days": trade_days,
        }

    # ===== 单股加载 =====
    def load_stock(self, code: str) -> Optional[pd.DataFrame]:
        """加载单只股票的完整K线"""
        if code in self._cache:
            return self._cache[code].copy()

        filepath = self.parquet_dir / f"{code}.parquet"
        if not filepath.exists():
            return None

        df = pd.read_parquet(filepath)
        df["date"] = pd.to_datetime(df["date"])

        # 简单的LRU缓存淘汰
        if len(self._cache) >= self._max_cache:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[code] = df.copy()
        return df

    def load_stock_range(self, code: str, start: str, end: str) -> Optional[pd.DataFrame]:
        """加载单只股票指定时间范围的K线"""
        df = self.load_stock(code)
        if df is None:
            return None
        return df[(df["date"] >= start) & (df["date"] <= end)].copy()

    # ===== 批量加载 =====
    def load_basket(self, codes: List[str],
                    start: str = None, end: str = None,
                    columns: List[str] = None) -> pd.DataFrame:
        """批量加载一组股票的K线数据

        Args:
            codes: 股票代码列表
            start: 开始日期 (YYYY-MM-DD)，默认全部
            end: 结束日期 (YYYY-MM-DD)，默认全部
            columns: 需要的列，默认全部
        Returns:
            多股票合并的DataFrame，索引为 date+code
        """
        frames = []
        for code in codes:
            df = self.load_stock(code)
            if df is None:
                continue
            if start:
                df = df[df["date"] >= start]
            if end:
                df = df[df["date"] <= end]
            if len(df) == 0:
                continue
            if columns:
                df = df[columns + ["date"]]
            frames.append(df)

        if not frames:
            return pd.DataFrame()

        result = pd.concat(frames, ignore_index=True)
        return result.set_index(["date", "code"])

    def load_basket_pivot(self, codes: List[str], field: str = "close",
                           start: str = None, end: str = None) -> pd.DataFrame:
        """加载一组股票的K线并转换为日期×代码的透视表

        Args:
            codes: 股票代码列表
            field: 要透视的字段 (close/open/high/low/volume)
            start/end: 时间范围
        Returns:
            DataFrame: index=date, columns=code, values=field
        """
        df = self.load_basket(codes, start, end, columns=["code", field])
        if df.empty:
            return pd.DataFrame()
        return df.reset_index().pivot(index="date", columns="code", values=field)

    def get_closes(self, codes: List[str], start: str = None, end: str = None) -> pd.DataFrame:
        """快捷方法：获取一组股票的收盘价透视表"""
        return self.load_basket_pivot(codes, "close", start, end)

    def get_volumes(self, codes: List[str], start: str = None, end: str = None) -> pd.DataFrame:
        """快捷方法：获取一组股票的成交量透视表"""
        return self.load_basket_pivot(codes, "volume", start, end)

    # ===== 搜索 =====
    def search_stocks(self, keyword: str, limit: int = 20) -> List[dict]:
        """搜索股票（支持代码或名称）"""
        db = self.get_index_db()
        rows = db.execute(
            "SELECT code, name FROM kline_index WHERE code LIKE ? OR name LIKE ? LIMIT ?",
            (f"%{keyword}%", f"%{keyword}%", limit)
        ).fetchall()
        db.close()
        return [{"code": r[0], "name": r[1]} for r in rows]

    # ===== 管理 =====
    def clear_cache(self):
        """清空内存缓存"""
        self._cache.clear()

    def refresh(self):
        """刷新所有数据（重新下载需要外部脚本）"""
        self.clear_cache()
        return {"status": "ok", "message": "Cache cleared. Re-run download_klines.py to refresh data."}


# 全局单例
_data_engine: Optional[KlineDataEngine] = None


def get_kline_engine() -> KlineDataEngine:
    global _data_engine
    if _data_engine is None:
        _data_engine = KlineDataEngine()
    return _data_engine
