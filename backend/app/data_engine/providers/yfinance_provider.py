"""yFinance数据提供者 - 美股/全球市场

依赖: pip install yfinance
"""
from typing import List, Optional
from datetime import datetime
from .provider_base import MarketDataProvider, BarData, TickData


class YFinanceProvider(MarketDataProvider):
    """yFinance 美股数据提供者

    支持：
    - 美股日K线
    - ETF（SPY/QQQ等）
    - 实时行情
    """

    def __init__(self):
        self._yf = None
        self._load_yfinance()

    def _load_yfinance(self):
        try:
            import yfinance
            self._yf = yfinance
        except ImportError:
            pass

    @property
    def name(self) -> str:
        return "yfinance"

    def is_available(self) -> bool:
        return self._yf is not None

    def get_bars(self, symbol: str, start_date: str, end_date: str,
                 period: str = "daily") -> List[BarData]:
        if not self.is_available():
            return []
        try:
            ticker = self._yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval="1d" if period == "daily" else "1wk")
            bars = []
            for date, row in df.iterrows():
                bars.append(BarData(
                    symbol=symbol,
                    date=date.strftime('%Y-%m-%d'),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=float(row['Volume']),
                ))
            return bars
        except Exception as e:
            print(f"[yFinance] Error: {e}")
            return []

    def get_latest(self, symbol: str) -> Optional[TickData]:
        if not self.is_available():
            return None
        try:
            ticker = self._yf.Ticker(symbol)
            info = ticker.info
            return TickData(
                symbol=symbol,
                name=info.get('shortName', ''),
                price=float(info.get('currentPrice', info.get('regularMarketPrice', 0))),
                change_pct=float(info.get('regularMarketChangePercent', 0)),
                volume=float(info.get('volume', 0)),
                amount=0,
                high=float(info.get('dayHigh', 0)),
                low=float(info.get('dayLow', 0)),
                open=float(info.get('open', 0)),
                prev_close=float(info.get('previousClose', 0)),
                timestamp=datetime.now(),
            )
        except Exception as e:
            print(f"[yFinance] Latest error: {e}")
            return None

    def get_symbols(self, market: str = "US") -> List[str]:
        # yFinance没有列表API，返回常用标的
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "SPY", "QQQ", "IWM"]
