"""统一券商接口 - 全球多市场设计

所有券商（QMT/Futu/IBKR/Binance）实现此接口。
策略层永远不知道底层是哪个券商。

账户模型:
    A001  → A股/QMT/CNY
    HK001 → 港股/Futu/HKD
    US001 → 美股/IBKR/USD
    C001  → 加密/Binance/USDT
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum
from ..data_engine.providers.provider_base import Market


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"   # 市价单
    LIMIT = "LIMIT"     # 限价单


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    """统一订单模型 - 所有市场通用"""
    symbol: str         # 标准代码: 600519.SH / AAPL.US / BTCUSDT
    market: Market      # 市场类型
    side: OrderSide     # 买/卖
    quantity: float     # 数量
    price: float        # 价格（市价单为0）
    asset_type: str = "STOCK"  # STOCK/ETF/FUTURE/OPTION/CRYPTO
    order_type: OrderType = OrderType.MARKET
    order_id: str = ""
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0
    filled_price: float = 0
    commission: float = 0
    slippage: float = 0
    reason: str = ""    # 拒绝原因
    timestamp: str = ""


@dataclass
class Position:
    """统一持仓模型"""
    symbol: str
    market: Market
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float = 0
    pnl: float = 0
    pnl_pct: float = 0


@dataclass
class Account:
    """统一账户模型"""
    account_id: str     # 账户ID: A001 / HK001 / US001
    market: Market      # 市场
    broker: str         # 券商: qmt / futu / ibkr / binance
    currency: str       # 币种: CNY / HKD / USD / USDT
    cash: float = 0
    invested: float = 0
    total: float = 0


class BrokerBase(ABC):
    """统一券商接口

    实现此接口即可接入任何券商。
    策略层只依赖此接口，不关心具体券商。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """券商名称: 'paper', 'qmt', 'futu', 'ibkr', 'binance'"""
        ...

    @property
    @abstractmethod
    def market(self) -> Market:
        """此券商对应的市场"""
        ...

    @property
    @abstractmethod
    def currency(self) -> str:
        """结算币种: 'CNY', 'USD', 'HKD', 'USDT'"""
        ...

    @abstractmethod
    def connect(self) -> bool:
        """连接券商"""
        ...

    @abstractmethod
    def disconnect(self):
        """断开连接"""
        ...

    @abstractmethod
    def send_order(self, order: Order) -> Optional[Order]:
        """发送订单，返回更新后的订单（含成交信息）"""
        ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        ...

    @abstractmethod
    def get_positions(self) -> List[Position]:
        """查询所有持仓"""
        ...

    @abstractmethod
    def get_account(self) -> Account:
        """查询账户信息"""
        ...

    @abstractmethod
    def get_market_price(self, symbol: str) -> float:
        """获取最新价格"""
        ...

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return False
