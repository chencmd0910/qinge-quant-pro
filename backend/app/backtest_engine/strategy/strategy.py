from abc import ABC, abstractmethod
from typing import List
from app.backtest_engine.core.bar import Bar
from app.backtest_engine.core.order import Order, OrderSide


class Strategy(ABC):
    def __init__(self):
        self._orders: List[Order] = []
        self._portfolio = None
        self._broker = None

    def _bind(self, portfolio, broker):
        self._portfolio = portfolio
        self._broker = broker

    @abstractmethod
    def initialize(self): pass

    @abstractmethod
    def on_bar(self, bar: Bar, bars: List[Bar]): pass

    def buy(self, symbol, quantity, price=0):
        if price == 0:
            price = self._get_current_price(symbol)
        if price > 0:
            self._orders.append(Order(symbol=symbol, side=OrderSide.BUY, quantity=quantity, price=price))

    def sell(self, symbol, quantity, price=0):
        if price == 0:
            price = self._get_current_price(symbol)
        if price > 0:
            self._orders.append(Order(symbol=symbol, side=OrderSide.SELL, quantity=quantity, price=price))

    def get_position(self, symbol):
        return self._portfolio.get_position(symbol) if self._portfolio else None

    def get_cash(self):
        return self._portfolio.cash if self._portfolio else 0

    def get_total_value(self):
        return self._portfolio.total_value if self._portfolio else 0

    def _get_current_price(self, symbol):
        if self._portfolio:
            pos = self._portfolio.get_position(symbol)
            if pos and pos.current_price > 0:
                return pos.current_price
        return 0.0

    def _clear_orders(self):
        self._orders.clear()

    @property
    def pending_orders(self):
        return self._orders.copy()
