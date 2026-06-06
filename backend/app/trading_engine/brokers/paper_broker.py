"""PaperBroker - 模拟券商（A股）

完全复用BrokerBase接口，支持A股规则。
手续费: 可配置 (默认万3)
滑点: 可配置 (默认0.1%)

与Backtest Engine共用订单模型。
"""
from typing import Optional, List
from datetime import datetime
from ..broker_base import BrokerBase, Order, OrderSide, OrderType, OrderStatus, Position, Account
from ...data_engine.providers.provider_base import Market


class PaperBroker(BrokerBase):
    """模拟券商 - A股"""

    def __init__(self, initial_cash: float = 1_000_000,
                 commission_rate: float = 0.0003,
                 slippage_pct: float = 0.001):
        self._cash = initial_cash
        self._initial_cash = initial_cash
        self._positions: dict = {}  # symbol -> {quantity, avg_cost, current_price}
        self._orders: List[Order] = []
        self._connected = False
        self._commission_rate = commission_rate
        self._slippage_pct = slippage_pct
        self._trade_count = 0
        self._total_commission = 0.0

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
        """发送订单 - 支持手续费和滑点"""
        if not self._connected:
            order.status = OrderStatus.REJECTED
            order.reason = "未连接"
            return order

        symbol = order.symbol
        price = order.price
        quantity = int(order.quantity)

        if quantity <= 0:
            order.status = OrderStatus.REJECTED
            order.reason = "数量无效"
            return order

        # A股最小交易单位: 100股
        if quantity % 100 != 0:
            quantity = (quantity // 100) * 100
            if quantity == 0:
                order.status = OrderStatus.REJECTED
                order.reason = "数量不足1手(100股)"
                return order

        if order.side == OrderSide.BUY:
            # 买入: 加滑点
            exec_price = price * (1 + self._slippage_pct)
            cost = exec_price * quantity
            commission = cost * self._commission_rate
            total_cost = cost + commission

            if total_cost > self._cash:
                order.status = OrderStatus.REJECTED
                order.reason = f"资金不足: need {total_cost:.2f}, have {self._cash:.2f}"
                return order

            self._cash -= total_cost
            if symbol not in self._positions:
                self._positions[symbol] = {"quantity": 0, "avg_cost": 0, "current_price": exec_price}
            pos = self._positions[symbol]
            total = pos["avg_cost"] * pos["quantity"] + exec_price * quantity
            pos["quantity"] += quantity
            pos["avg_cost"] = total / pos["quantity"]
            pos["current_price"] = exec_price

            order.filled_price = exec_price
            order.commission = commission

        elif order.side == OrderSide.SELL:
            pos = self._positions.get(symbol)
            if not pos or pos["quantity"] < quantity:
                order.status = OrderStatus.REJECTED
                order.reason = f"持仓不足: have {pos['quantity'] if pos else 0}, need {quantity}"
                return order

            # 卖出: 减滑点
            exec_price = price * (1 - self._slippage_pct)
            proceeds = exec_price * quantity
            commission = proceeds * self._commission_rate

            pos["quantity"] -= quantity
            self._cash += proceeds - commission

            if pos["quantity"] == 0:
                del self._positions[symbol]

            order.filled_price = exec_price
            order.commission = commission

        order.status = OrderStatus.FILLED
        order.filled_quantity = quantity
        order.timestamp = datetime.now().isoformat()
        self._orders.append(order)
        self._trade_count += 1
        self._total_commission += order.commission
        return order

    def cancel_order(self, order_id: str) -> bool:
        return False  # 立即成交，无法撤销

    def get_positions(self) -> List[Position]:
        return [
            Position(
                symbol=sym, market=Market.A_SHARE,
                quantity=d["quantity"], avg_cost=d["avg_cost"],
                current_price=d.get("current_price", d["avg_cost"]),
                market_value=d["quantity"] * d.get("current_price", d["avg_cost"]),
                pnl=round((d.get("current_price", d["avg_cost"]) - d["avg_cost"]) * d["quantity"], 2),
                pnl_pct=round(((d.get("current_price", d["avg_cost"]) / d["avg_cost"]) - 1) * 100, 2) if d["avg_cost"] > 0 else 0,
            )
            for sym, d in self._positions.items()
            if d["quantity"] > 0
        ]

    def get_account(self) -> Account:
        invested = sum(d["quantity"] * d.get("current_price", d["avg_cost"]) for d in self._positions.values())
        return Account(
            account_id="PAPER_A", market=Market.A_SHARE,
            broker="paper", currency="CNY",
            cash=round(self._cash, 2), invested=round(invested, 2),
            total=round(self._cash + invested, 2),
        )

    def get_market_price(self, symbol: str) -> float:
        pos = self._positions.get(symbol)
        return pos.get("current_price", 0) if pos else 0.0

    def update_prices(self, prices: dict):
        """更新持仓价格 (由Daily Runner调用)"""
        for symbol, price in prices.items():
            if symbol in self._positions:
                self._positions[symbol]["current_price"] = price

    def get_snapshot(self) -> dict:
        """获取账户快照"""
        account = self.get_account()
        positions = self.get_positions()
        return {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "cash": account.cash,
            "market_value": account.invested,
            "total_equity": account.total,
            "pnl": round(account.total - self._initial_cash, 2),
            "pnl_pct": round((account.total / self._initial_cash - 1) * 100, 2),
            "trade_count": self._trade_count,
            "total_commission": round(self._total_commission, 2),
            "positions": [
                {
                    "symbol": p.symbol,
                    "quantity": p.quantity,
                    "avg_cost": round(p.avg_cost, 4),
                    "current_price": round(p.current_price, 4),
                    "market_value": round(p.market_value, 2),
                    "pnl": p.pnl,
                    "pnl_pct": p.pnl_pct,
                }
                for p in positions
            ],
        }
