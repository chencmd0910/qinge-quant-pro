"""AkShare数据提供者 - A股市场

支持: A股/ETF/可转债
数据源: 东方财富（通过AkShare）
"""
from typing import List, Optional
from datetime import datetime, timedelta
from .provider_base import MarketDataProvider, Market, Bar, Tick


class AkShareProvider(MarketDataProvider):
    """AkShare A股数据提供者"""

    def __init__(self):
        self._ak = None
        try:
            import akshare
            self._ak = akshare
        except ImportError:
            pass

    @property
    def name(self) -> str:
        return "akshare"

    @property
    def market(self) -> Market:
        return Market.A_SHARE

    def is_available(self) -> bool:
        return self._ak is not None

    def get_bars(self, symbol: str, start_date: str, end_date: str,
                 period: str = "daily") -> List[Bar]:
        if not self.is_available():
            return []
        try:
            # 统一代码格式: 600519.SH -> 600519
            code = symbol.split('.')[0] if '.' in symbol else symbol
            df = self._ak.stock_zh_a_hist(
                symbol=code, period=period,
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq"
            )
            bars = []
            for _, row in df.iterrows():
                bars.append(Bar(
                    symbol=symbol,
                    market=Market.A_SHARE,
                    date=str(row['日期']),
                    open=float(row['开盘']),
                    high=float(row['最高']),
                    low=float(row['最低']),
                    close=float(row['收盘']),
                    volume=float(row['成交量']),
                    amount=float(row.get('成交额', 0)),
                    change_pct=float(row.get('涨跌幅', 0)),
                    turnover=float(row.get('换手率', 0)),
                ))
            return bars
        except Exception as e:
            print(f"[AkShare] Error: {e}")
            return []

    def get_latest(self, symbol: str) -> Optional[Tick]:
        if not self.is_available():
            return None
        try:
            code = symbol.split('.')[0] if '.' in symbol else symbol
            df = self._ak.stock_zh_a_spot_em()
            row = df[df['代码'] == code]
            if row.empty:
                return None
            r = row.iloc[0]
            return Tick(
                symbol=symbol, market=Market.A_SHARE,
                name=str(r.get('名称', '')),
                price=float(r.get('最新价', 0)),
                change_pct=float(r.get('涨跌幅', 0)),
                volume=float(r.get('成交量', 0)),
                amount=float(r.get('成交额', 0)),
                high=float(r.get('最高', 0)),
                low=float(r.get('最低', 0)),
                open=float(r.get('今开', 0)),
                prev_close=float(r.get('昨收', 0)),
                timestamp=datetime.now(),
            )
        except Exception as e:
            print(f"[AkShare] Latest error: {e}")
            return None

    def get_symbols(self, **filters) -> List[str]:
        if not self.is_available():
            return []
        try:
            df = self._ak.stock_zh_a_spot_em()
            codes = df['代码'].tolist()
            # 标准化为 600519.SH 格式
            result = []
            for code in codes:
                if code.startswith('6'):
                    result.append(f"{code}.SH")
                else:
                    result.append(f"{code}.SZ")
            return result
        except:
            return []
