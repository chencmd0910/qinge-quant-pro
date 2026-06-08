"""回测组合管理"""
from typing import List, Dict


class Portfolio:
    """回测组合 - 管理资金、持仓、交易记录"""

    def __init__(self, initial_cash: float = 1_000_000):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, dict] = {}  # symbol → {qty, avg_cost, current_price}
        self.history: List[dict] = []
        self.trades: List[dict] = []
        self._total_commission = 0.0
        self._trade_count = 0

    def update_prices(self, prices: Dict[str, float]):
        """更新持仓最新价格"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol]['current_price'] = price

    def execute_buy(self, symbol: str, quantity: int, price: float, commission: float):
        """执行买入"""
        cost = price * quantity + commission
        if cost > self.cash:
            # 买不起就跳过
            return None

        self.cash -= cost
        self._total_commission += commission
        self._trade_count += 1

        if symbol in self.positions:
            pos = self.positions[symbol]
            total_qty = pos['qty'] + quantity
            pos['avg_cost'] = (pos['avg_cost'] * pos['qty'] + price * quantity) / total_qty
            pos['qty'] = total_qty
        else:
            self.positions[symbol] = {
                'qty': quantity,
                'avg_cost': price,
                'current_price': price,
            }

        trade = {
            'date': '',
            'direction': 'BUY',
            'symbol': symbol,
            'price': price,
            'qty': quantity,
            'amount': price * quantity,
            'commission': commission,
        }
        self.trades.append(trade)
        return trade

    def execute_sell(self, symbol: str, quantity: int, price: float, commission: float):
        """执行卖出"""
        if symbol not in self.positions:
            return None

        pos = self.positions[symbol]
        qty = min(quantity, pos['qty'])
        if qty <= 0:
            return None

        revenue = price * qty - commission
        self.cash += revenue
        self._total_commission += commission
        self._trade_count += 1

        pnl = (price - pos['avg_cost']) * qty

        self.trades.append({
            'date': '',
            'direction': 'SELL',
            'symbol': symbol,
            'price': price,
            'qty': qty,
            'amount': price * qty,
            'commission': commission,
            'pnl': round(pnl, 2),
        })

        pos['qty'] -= qty
        if pos['qty'] <= 0:
            del self.positions[symbol]

        return self.trades[-1]

    def snapshot(self, date_str: str):
        """记录当日快照"""
        market_value = sum(
            p['qty'] * p.get('current_price', p['avg_cost'])
            for p in self.positions.values()
        )
        total_value = self.cash + market_value
        self.history.append({
            'date': date_str,
            'cash': round(self.cash, 2),
            'market_value': round(market_value, 2),
            'total_value': round(total_value, 2),
            'positions': len(self.positions),
        })

    @property
    def total_equity(self) -> float:
        market_value = sum(
            p['qty'] * p.get('current_price', p['avg_cost'])
            for p in self.positions.values()
        )
        return self.cash + market_value
