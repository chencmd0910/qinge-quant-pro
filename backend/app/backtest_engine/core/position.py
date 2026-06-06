from dataclasses import dataclass


@dataclass
class Position:
    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0
    current_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def cost_value(self) -> float:
        return self.quantity * self.avg_cost

    @property
    def pnl(self) -> float:
        return self.market_value - self.cost_value

    @property
    def pnl_pct(self) -> float:
        if self.cost_value == 0:
            return 0.0
        return self.pnl / self.cost_value * 100

    def update_price(self, price: float):
        self.current_price = price

    def add(self, quantity: int, price: float):
        total_cost = self.cost_value + quantity * price
        self.quantity += quantity
        if self.quantity > 0:
            self.avg_cost = total_cost / self.quantity

    def reduce(self, quantity: int, price: float) -> float:
        pnl = (price - self.avg_cost) * quantity
        self.quantity -= quantity
        if self.quantity <= 0:
            self.quantity = 0
            self.avg_cost = 0.0
        return pnl
