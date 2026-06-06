from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    symbol: str
    side: OrderSide
    quantity: int
    price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    filled_price: float = 0.0
    filled_quantity: int = 0
    commission: float = 0.0
    slippage: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    filled_at: datetime = None
    reason: str = ""

    @property
    def amount(self) -> float:
        return self.filled_price * self.filled_quantity

    @property
    def total_cost(self) -> float:
        if self.side == OrderSide.BUY:
            return self.amount + self.commission
        return self.amount - self.commission
