"""PaperBroker - 模拟券商

最基础的模拟交易实现。
无延迟、无滑点模拟，用于策略验证。
"""
from typing import Optional
from datetime import datetime
from ..broker_base import BrokerBase
from ...event_engine.core.event import OrderEvent, FillEvent


class PaperBroker(BrokerBase):
    """模拟券商

    用于策略验证和模拟盘。
    所有订单立即以指定价格成交。
    """

    def __init__(self, initial_cash: float = 1_000_000):
        self.cash = initial_cash
        self.positions = {}   # symbol -> {quantity, avg_cost}
        self.orders = []      # 历史订单
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        return True

    def disconnect(self):
        self.connected = False

    def send_order(self, order: OrderEvent) -> Optional[FillEvent]:
        """发送订单 - 立即成交"""
        if not self.connected:
            return None

        symbol = order.data.get("symbol", "")
        side = order.data.get("side", "")
        quantity = order.data.get("quantity", 0)
        price = order.data.get("price", 0)

        if side == "BUY":
            cost = price * quantity
            if cost > self.cash:
                return None  # 资金不足
            self.cash -= cost
            if symbol not in self.positions:
                self.positions[symbol] = {"quantity": 0, "avg_cost": 0}
            pos = self.positions[symbol]
            total = pos["avg_cost"] * pos["quantity"] + price * quantity
            pos["quantity"] += quantity
            pos["avg_cost"] = total / pos["quantity"]

        elif side == "SELL":
            pos = self.positions.get(symbol)
            if not pos or pos["quantity"] < quantity:
                return None  # 持仓不足
            pnl = (price - pos["avg_cost"]) * quantity
            pos["quantity"] -= quantity
            self.cash += price * quantity
            if pos["quantity"] == 0:
                del self.positions[symbol]

        fill = FillEvent(data={
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "commission": 0,
            "slippage": 0,
        })
        self.orders.append({
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol, "side": side,
            "quantity": quantity, "price": price,
        })
        return fill

    def cancel_order(self, order_id: str) -> bool:
        return False  # PaperBroker 立即成交，无法撤销

    def get_position(self, symbol: str) -> dict:
        return self.positions.get(symbol, {"quantity": 0, "avg_cost": 0})

    def get_account(self) -> dict:
        invested = sum(p["quantity"] * p["avg_cost"] for p in self.positions.values())
        return {
            "cash": round(self.cash, 2),
            "invested": round(invested, 2),
            "total": round(self.cash + invested, 2),
        }

    def get_market_price(self, symbol: str) -> float:
        return 0.0  # PaperBroker 不提供行情

    def get_summary(self) -> dict:
        account = self.get_account()
        return {
            **account,
            "position_count": len(self.positions),
            "order_count": len(self.orders),
        }
