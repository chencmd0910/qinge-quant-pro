"""MarketEngine - 交易市场抽象

管理不同市场的：
- 交易时间
- 交易日历
- 时区
- 币种
- 资产类型

回测和实盘都能统一处理。
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, time
from enum import Enum
from ..data_engine.providers.provider_base import Market


class AssetType(Enum):
    """资产类型 - 统一扩展"""
    STOCK = "股票"
    ETF = "ETF"
    FUTURE = "期货"
    OPTION = "期权"
    CRYPTO = "加密货币"
    CONVERTIBLE = "可转债"


@dataclass
class MarketConfig:
    """单个市场的配置"""
    market: Market
    timezone: str          # IANA时区
    currency: str          # 结算币种
    asset_types: List[AssetType]  # 支持的资产类型
    trading_sessions: List[tuple]  # 交易时段 [(start, end), ...]
    t_plus: int            # T+N 交割
    lot_size: int          # 最小交易单位
    limit_pct: Optional[float]  # 涨跌停幅度（None=无限制）
    trading_days: str      # 交易日规则: "weekdays" / "everyday"


# === 预定义市场配置 ===

MARKET_CONFIGS: Dict[Market, MarketConfig] = {
    Market.A_SHARE: MarketConfig(
        market=Market.A_SHARE,
        timezone="Asia/Shanghai",
        currency="CNY",
        asset_types=[AssetType.STOCK, AssetType.ETF, AssetType.CONVERTIBLE],
        trading_sessions=[(time(9, 30), time(11, 30)), (time(13, 0), time(15, 0))],
        t_plus=1,
        lot_size=100,
        limit_pct=10.0,
        trading_days="weekdays",
    ),
    Market.HK_STOCK: MarketConfig(
        market=Market.HK_STOCK,
        timezone="Asia/Hong_Kong",
        currency="HKD",
        asset_types=[AssetType.STOCK, AssetType.ETF],
        trading_sessions=[(time(9, 30), time(12, 0)), (time(13, 0), time(16, 0))],
        t_plus=0,
        lot_size=1,  # 港股每手股数不同
        limit_pct=None,  # 无涨跌停
        trading_days="weekdays",
    ),
    Market.US_STOCK: MarketConfig(
        market=Market.US_STOCK,
        timezone="America/New_York",
        currency="USD",
        asset_types=[AssetType.STOCK, AssetType.ETF, AssetType.OPTION],
        trading_sessions=[(time(9, 30), time(16, 0))],  # 盘前盘后另算
        t_plus=0,
        lot_size=1,
        limit_pct=None,
        trading_days="weekdays",
    ),
    Market.CRYPTO: MarketConfig(
        market=Market.CRYPTO,
        timezone="UTC",
        currency="USDT",
        asset_types=[AssetType.CRYPTO],
        trading_sessions=[(time(0, 0), time(23, 59))],  # 24小时
        t_plus=0,
        lot_size=1,
        limit_pct=None,
        trading_days="everyday",
    ),
}


class MarketEngine:
    """市场引擎

    提供：
    - 交易时间判断
    - 交易日历查询
    - 资产类型查询
    - 市场配置查询
    """

    def __init__(self):
        self.configs = MARKET_CONFIGS.copy()

    def get_config(self, market: Market) -> MarketConfig:
        return self.configs[market]

    def is_trading_time(self, market: Market, dt: datetime = None) -> bool:
        """判断当前是否为交易时间"""
        config = self.configs.get(market)
        if not config:
            return False
        if dt is None:
            from datetime import timezone as tz
            import pytz
            tz_obj = pytz.timezone(config.timezone)
            dt = datetime.now(tz_obj)
        current_time = dt.time()
        return any(start <= current_time <= end for start, end in config.trading_sessions)

    def is_trading_day(self, market: Market, date: datetime = None) -> bool:
        """判断是否为交易日（简化版，不考虑节假日）"""
        config = self.configs.get(market)
        if not config:
            return False
        if date is None:
            date = datetime.now()
        if config.trading_days == "everyday":
            return True
        return date.weekday() < 5  # 周一到周五

    def get_lot_size(self, market: Market) -> int:
        """获取最小交易单位"""
        config = self.configs.get(market)
        return config.lot_size if config else 100

    def round_quantity(self, market: Market, quantity: float) -> int:
        """按最小交易单位取整"""
        lot = self.get_lot_size(market)
        return int(quantity // lot) * lot

    def get_supported_assets(self, market: Market) -> List[AssetType]:
        """获取市场支持的资产类型"""
        config = self.configs.get(market)
        return config.asset_types if config else []

    def add_market(self, config: MarketConfig):
        """注册自定义市场"""
        self.configs[config.market] = config
