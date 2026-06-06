from typing import List, Dict
from app.backtest_engine.core.bar import Bar
from app.backtest_engine.core.order import OrderStatus
from app.backtest_engine.portfolio.portfolio import Portfolio
from app.backtest_engine.broker.broker import SimBroker
from app.backtest_engine.strategy.strategy import Strategy
from app.backtest_engine.metrics.metrics import calc_all_metrics


class BacktestEngine:
    def __init__(self, strategy: Strategy, data: Dict[str, List[Bar]], cash: float = 1_000_000,
                 commission_rate=None, slippage_bps=None):
        self.strategy = strategy
        self.data = data
        self.portfolio = Portfolio(initial_cash=cash)
        self.broker = SimBroker(commission_rate, slippage_bps)
        self.strategy._bind(self.portfolio, self.broker)

    def run(self) -> Dict:
        self.strategy.initialize()
        all_dates = set()
        for bars in self.data.values():
            for bar in bars:
                all_dates.add(bar.datetime.strftime('%Y-%m-%d'))

        for date_str in sorted(all_dates):
            today_bars = {}
            for symbol, bars in self.data.items():
                for bar in bars:
                    if bar.datetime.strftime('%Y-%m-%d') == date_str:
                        today_bars[symbol] = bar
                        break

            prices = {s: b.close for s, b in today_bars.items()}
            self.portfolio.update_prices(prices)

            for symbol, bar in today_bars.items():
                recent = [b for b in self.data.get(symbol, []) if b.datetime.strftime('%Y-%m-%d') <= date_str][-250:]
                self.strategy.on_bar(bar, recent)

            for order in self.strategy.pending_orders:
                if order.symbol in today_bars and order.status == OrderStatus.PENDING:
                    self.broker.execute(order, today_bars[order.symbol])
                    if order.status == OrderStatus.FILLED:
                        if order.side.value == 'BUY':
                            self.portfolio.execute_buy(order.symbol, order.filled_quantity, order.filled_price, order.commission)
                        else:
                            self.portfolio.execute_sell(order.symbol, order.filled_quantity, order.filled_price, order.commission)
            self.strategy._clear_orders()
            self.portfolio.snapshot(date_str)

        return self._report()

    def _report(self):
        values = [h['total_value'] for h in self.portfolio.history]
        metrics = calc_all_metrics(values, self.portfolio.trades)
        return {
            'metrics': metrics,
            'equity_curve': self.portfolio.history,
            'trades': self.portfolio.trades,
            'drawdown_curve': self._dd_curve(values),
            'monthly_returns': self._monthly(),
        }

    def _dd_curve(self, values):
        if not values: return []
        peak = values[0]
        curve = []
        for i, v in enumerate(values):
            if v > peak: peak = v
            dd = (peak - v) / peak * 100 if peak > 0 else 0
            date = self.portfolio.history[i]['date'] if i < len(self.portfolio.history) else ''
            curve.append({'date': date, 'drawdown': round(dd, 2)})
        return curve

    def _monthly(self):
        if not self.portfolio.history: return []
        monthly = {}
        for h in self.portfolio.history:
            m = h['date'][:7]
            if m not in monthly:
                monthly[m] = {'start': h['total_value'], 'end': h['total_value']}
            monthly[m]['end'] = h['total_value']
        result = []
        prev = None
        for m in sorted(monthly):
            v = monthly[m]
            ret = (v['end'] - prev) / prev * 100 if prev and prev > 0 else (v['end'] - v['start']) / v['start'] * 100 if v['start'] > 0 else 0
            result.append({'month': m, 'return': round(ret, 2)})
            prev = v['end']
        return result
