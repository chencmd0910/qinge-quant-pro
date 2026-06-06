"""投资组合管理 - 真实实现

完整跟踪：现金、持仓、市值、盈亏、交易记录
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PositionDetail:
    """持仓详情"""
    symbol: str
    name: str
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float = 0
    pnl: float = 0
    pnl_pct: float = 0
    weight: float = 0

    def update_price(self, price: float):
        self.current_price = price
        self.market_value = self.quantity * price
        self.pnl = (price - self.avg_cost) * self.quantity
        self.pnl_pct = (price / self.avg_cost - 1) * 100 if self.avg_cost > 0 else 0


@dataclass
class TradeDetail:
    """交易记录"""
    timestamp: str
    symbol: str
    side: str           # BUY / SELL
    price: float
    quantity: int
    amount: float
    commission: float
    pnl: float = 0


class Portfolio:
    """投资组合管理

    真实跟踪每一笔交易对资产的影响。
    """

    def __init__(self, initial_cash: float = 1_000_000):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, PositionDetail] = {}
        self.trades: List[TradeDetail] = []
        self.equity_history: List[dict] = []

    @property
    def invested(self) -> float:
        """持仓市值"""
        return sum(p.market_value for p in self.positions.values() if p.quantity > 0)

    @property
    def total_value(self) -> float:
        """总资产 = 现金 + 持仓市值"""
        return self.cash + self.invested

    @property
    def pnl(self) -> float:
        """总盈亏"""
        return self.total_value - self.initial_cash

    @property
    def pnl_pct(self) -> float:
        """总收益率"""
        return self.pnl / self.initial_cash * 100 if self.initial_cash else 0

    @property
    def position_count(self) -> int:
        """持仓数量"""
        return len([p for p in self.positions.values() if p.quantity > 0])

    def update_prices(self, prices: Dict[str, float]):
        """更新持仓价格"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)

    def buy(self, symbol: str, quantity: int, price: float,
            commission: float = 0, name: str = "") -> TradeDetail:
        """买入

        Returns:
            TradeDetail 成交记录
        """
        amount = price * quantity
        total_cost = amount + commission

        if total_cost > self.cash:
            # 资金不足，调整数量
            max_quantity = int((self.cash - commission) / price / 100) * 100
            if max_quantity <= 0:
                raise ValueError(f"资金不足: need {total_cost:.2f}, have {self.cash:.2f}")
            quantity = max_quantity
            amount = price * quantity
            total_cost = amount + commission

        self.cash -= total_cost

        if symbol not in self.positions:
            self.positions[symbol] = PositionDetail(
                symbol=symbol, name=name, quantity=0,
                avg_cost=0, current_price=price
            )

        pos = self.positions[symbol]
        # 更新均价
        total_cost_basis = pos.avg_cost * pos.quantity + price * quantity
        pos.quantity += quantity
        pos.avg_cost = total_cost_basis / pos.quantity if pos.quantity > 0 else 0
        pos.update_price(price)

        trade = TradeDetail(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            symbol=symbol, side="BUY", price=price,
            quantity=quantity, amount=amount, commission=commission
        )
        self.trades.append(trade)
        return trade

    def sell(self, symbol: str, quantity: int, price: float,
             commission: float = 0) -> TradeDetail:
        """卖出

        Returns:
            TradeDetail 成交记录
        """
        pos = self.positions.get(symbol)
        if not pos or pos.quantity < quantity:
            available = pos.quantity if pos else 0
            raise ValueError(f"持仓不足: need {quantity}, have {available}")

        amount = price * quantity
        pnl = (price - pos.avg_cost) * quantity - commission

        pos.quantity -= quantity
        pos.update_price(price)
        self.cash += amount - commission

        trade = TradeDetail(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            symbol=symbol, side="SELL", price=price,
            quantity=quantity, amount=amount, commission=commission, pnl=pnl
        )
        self.trades.append(trade)

        # 清理零持仓
        if pos.quantity == 0:
            del self.positions[symbol]

        return trade

    def snapshot(self, date: str):
        """记录每日快照"""
        self.equity_history.append({
            'date': date,
            'total_value': round(self.total_value, 2),
            'cash': round(self.cash, 2),
            'invested': round(self.invested, 2),
            'pnl': round(self.pnl, 2),
            'pnl_pct': round(self.pnl_pct, 4),
            'position_count': self.position_count,
        })

    def get_position(self, symbol: str) -> Optional[PositionDetail]:
        return self.positions.get(symbol)

    def get_positions_list(self) -> List[PositionDetail]:
        return [p for p in self.positions.values() if p.quantity > 0]

    def get_summary(self) -> dict:
        return {
            'initial_cash': self.initial_cash,
            'cash': round(self.cash, 2),
            'invested': round(self.invested, 2),
            'total_value': round(self.total_value, 2),
            'pnl': round(self.pnl, 2),
            'pnl_pct': round(self.pnl_pct, 4),
            'position_count': self.position_count,
            'trade_count': len(self.trades),
        }
