"""策略基类"""
from typing import List, Dict, Optional
from ..core.order import Order, OrderSide


class Strategy:
    """回测策略基类"""

    def __init__(self, name: str = "BaseStrategy"):
        self.name = name
        self._portfolio = None
        self._broker = None
        self.pending_orders: List[Order] = []

    def _bind(self, portfolio, broker):
        """绑定组合和券商"""
        self._portfolio = portfolio
        self._broker = broker

    def initialize(self):
        """初始化 - 子类可重写"""
        pass

    def on_bar(self, bar, recent_bars: List):
        """每根K线触发 - 子类必须重写

        Args:
            bar: 当前Bar
            recent_bars: 最近N根K线（含当前）
        """
        pass

    def buy(self, symbol: str, quantity: int, price: float = 0.0):
        """创建买入订单"""
        order = Order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            price=price,
        )
        self.pending_orders.append(order)
        return order

    def sell(self, symbol: str, quantity: int, price: float = 0.0):
        """创建卖出订单"""
        order = Order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            price=price,
        )
        self.pending_orders.append(order)
        return order

    def _clear_orders(self):
        """清空待处理订单"""
        self.pending_orders = []

    @property
    def portfolio(self):
        return self._portfolio

    @property
    def broker(self):
        return self._broker
