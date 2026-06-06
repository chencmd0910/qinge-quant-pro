from typing import Dict, List, Optional
from datetime import datetime
from app.backtest_engine.core.position import Position
from app.backtest_engine.core.order import Order, OrderSide, OrderStatus


class Portfolio:
    def __init__(self, initial_cash: float = 1_000_000):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.history: List[dict] = []
        self.trades: List[dict] = []

    @property
    def invested(self):
        return sum(p.market_value for p in self.positions.values())

    @property
    def total_value(self):
        return self.cash + self.invested

    @property
    def pnl(self):
        return self.total_value - self.initial_cash

    @property
    def pnl_pct(self):
        return self.pnl / self.initial_cash * 100 if self.initial_cash else 0

    def update_prices(self, prices):
        for symbol, pos in self.positions.items():
            if symbol in prices:
                pos.update_price(prices[symbol])

    def execute_buy(self, symbol, quantity, price, commission=0, slippage=0):
        actual_price = price * (1 + slippage)
        amount = actual_price * quantity
        total_cost = amount + commission
        if total_cost > self.cash:
            max_qty = int(self.cash / (actual_price * (1 + slippage / max(price, 1))))
            max_qty = (max_qty // 100) * 100
            if max_qty <= 0:
                return Order(symbol=symbol, side=OrderSide.BUY, quantity=quantity, status=OrderStatus.REJECTED, reason="资金不足")
            quantity = max_qty
            amount = actual_price * quantity
            total_cost = amount + commission
        self.cash -= total_cost
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        self.positions[symbol].add(quantity, actual_price)
        self.trades.append({'date': datetime.now().strftime('%Y-%m-%d'), 'side': 'BUY', 'symbol': symbol, 'price': actual_price, 'quantity': quantity, 'amount': amount, 'commission': commission})
        return Order(symbol=symbol, side=OrderSide.BUY, quantity=quantity, price=price, status=OrderStatus.FILLED, filled_price=actual_price, filled_quantity=quantity, commission=commission)

    def execute_sell(self, symbol, quantity, price, commission=0, slippage=0):
        if symbol not in self.positions or self.positions[symbol].quantity <= 0:
            return Order(symbol=symbol, side=OrderSide.SELL, quantity=quantity, status=OrderStatus.REJECTED, reason="无持仓")
        pos = self.positions[symbol]
        quantity = min(quantity, pos.quantity)
        actual_price = price * (1 - slippage)
        amount = actual_price * quantity
        pnl = pos.reduce(quantity, actual_price)
        self.cash += amount - commission
        self.trades.append({'date': datetime.now().strftime('%Y-%m-%d'), 'side': 'SELL', 'symbol': symbol, 'price': actual_price, 'quantity': quantity, 'amount': amount, 'commission': commission, 'pnl': pnl})
        return Order(symbol=symbol, side=OrderSide.SELL, quantity=quantity, price=price, status=OrderStatus.FILLED, filled_price=actual_price, filled_quantity=quantity, commission=commission)

    def snapshot(self, date):
        self.history.append({'date': date, 'total_value': self.total_value, 'cash': self.cash, 'invested': self.invested, 'pnl': self.pnl, 'pnl_pct': self.pnl_pct, 'position_count': len([p for p in self.positions.values() if p.quantity > 0])})

    def get_position(self, symbol):
        return self.positions.get(symbol)
