"""PaperBroker - 模拟券商（A股）

最基础的模拟交易，无延迟无滑点。
用于策略验证和模拟盘。
"""
from typing import Optional, List
from datetime import datetime
from ..broker_base import BrokerBase, Order, OrderSide, OrderType, OrderStatus, Position, Account
from ...data_engine.providers.provider_base import Market


class PaperBroker(BrokerBase):
    """模拟券商 - A股"""

    def __init__(self, initial_cash: float = 1_000_000):
        self._cash = initial_cash
        self._positions: dict = {}  # symbol -> {quantity, avg_cost}
        self._orders: List[Order] = []
        self._connected = False

    @property
    def name(self) -> str:
        return "paper"

    @property
    def market(self) -> Market:
        return Market.A_SHARE

    @property
    def currency(self) -> str:
        return "CNY"

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    def send_order(self, order: Order) -> Optional[Order]:
        if not self._connected:
            order.status = OrderStatus.REJECTED
            order.reason = "未连接"
            return order

        symbol = order.symbol
        price = order.price
        quantity = order.quantity

        if order.side == OrderSide.BUY:
            cost = price * quantity
            if cost > self._cash:
                order.status = OrderStatus.REJECTED
                order.reason = f"资金不足: need {cost:.2f}, have {self._cash:.2f}"
                return order
            self._cash -= cost
            if symbol not in self._positions:
                self._positions[symbol] = {"quantity": 0, "avg_cost": 0}
            pos = self._positions[symbol]
            total = pos["avg_cost"] * pos["quantity"] + price * quantity
            pos["quantity"] += quantity
            pos["avg_cost"] = total / pos["quantity"]

        elif order.side == OrderSide.SELL:
            pos = self._positions.get(symbol)
            if not pos or pos["quantity"] < quantity:
                order.status = OrderStatus.REJECTED
                order.reason = "持仓不足"
                return order
            pos["quantity"] -= quantity
            self._cash += price * quantity
            if pos["quantity"] == 0:
                del self._positions[symbol]

        order.status = OrderStatus.FILLED
        order.filled_quantity = quantity
        order.filled_price = price
        order.timestamp = datetime.now().isoformat()
        self._orders.append(order)
        return order

    def cancel_order(self, order_id: str) -> bool:
        return False  # 立即成交，无法撤销

    def get_positions(self) -> List[Position]:
        return [
            Position(
                symbol=sym, market=Market.A_SHARE,
                quantity=d["quantity"], avg_cost=d["avg_cost"],
                current_price=d["avg_cost"],  # Paper没有实时价格
                market_value=d["quantity"] * d["avg_cost"],
            )
            for sym, d in self._positions.items()
            if d["quantity"] > 0
        ]

    def get_account(self) -> Account:
        invested = sum(d["quantity"] * d["avg_cost"] for d in self._positions.values())
        return Account(
            account_id="PAPER_A", market=Market.A_SHARE,
            broker="paper", currency="CNY",
            cash=self._cash, invested=invested, total=self._cash + invested,
        )

    def get_market_price(self, symbol: str) -> float:
        return 0.0  # Paper不提供行情
