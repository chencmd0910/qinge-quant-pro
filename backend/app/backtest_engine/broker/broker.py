from app.backtest_engine.core.order import Order, OrderSide, OrderStatus
from app.backtest_engine.core.bar import Bar


class SimBroker:
    COMMISSION_RATE = 0.0003
    COMMISSION_MIN = 5.0
    STAMP_TAX = 0.001
    TRANSFER_FEE = 0.00002
    SLIPPAGE_BPS = 2

    def __init__(self, commission_rate=None, slippage_bps=None):
        self.commission_rate = commission_rate or self.COMMISSION_RATE
        self.slippage_bps = slippage_bps or self.SLIPPAGE_BPS

    def calc_commission(self, amount, side):
        commission = max(amount * self.commission_rate, self.COMMISSION_MIN)
        transfer = amount * self.TRANSFER_FEE
        stamp = amount * self.STAMP_TAX if side == OrderSide.SELL else 0
        return commission + transfer + stamp

    def execute(self, order, bar):
        if order.side == OrderSide.BUY and bar.is_limit_up:
            order.status = OrderStatus.REJECTED
            order.reason = "涨停"
            return order
        if order.side == OrderSide.SELL and bar.is_limit_down:
            order.status = OrderStatus.REJECTED
            order.reason = "跌停"
            return order
        slippage = bar.close * self.slippage_bps / 10000
        order.filled_price = bar.close + slippage if order.side == OrderSide.BUY else bar.close - slippage
        amount = order.filled_price * order.quantity
        order.commission = self.calc_commission(amount, order.side)
        order.slippage = slippage * order.quantity
        order.filled_quantity = order.quantity
        order.status = OrderStatus.FILLED
        return order
