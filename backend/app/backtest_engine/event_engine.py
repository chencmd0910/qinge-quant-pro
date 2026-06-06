"""回测引擎 - 事件驱动版本

流程：
  数据(DataManager) → MarketEvent → 策略(StrategyBase) → SignalEvent → 风控(RiskManager) → OrderEvent → 券商(SimBroker) → FillEvent → 持仓更新

回测/实盘/模拟盘共用同一套事件流，只是数据源和券商不同。
"""
from typing import Dict, List, Optional
from datetime import datetime
from ..event_engine.engine import EventEngine
from ..event_engine.core.event import EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent
from ..data_engine.manager import DataManager
from ..risk_engine.risk_manager import RiskManager
from ..strategy_engine.strategy_base import StrategyBase
from ..backtest_engine.core.bar import Bar
from ..backtest_engine.core.order import Order, OrderSide, OrderStatus
from ..backtest_engine.portfolio.portfolio import Portfolio
from ..backtest_engine.broker.broker import SimBroker
from ..backtest_engine.metrics.metrics import calc_all_metrics


class EventDrivenBacktestEngine:
    """事件驱动回测引擎

    用法:
        engine = EventDrivenBacktestEngine()
        engine.set_data(dm)                      # 设置数据源
        engine.set_strategy(my_strategy)          # 设置策略
        engine.set_cash(1_000_000)               # 设置初始资金
        result = engine.run()                     # 运行回测
    """

    def __init__(self):
        self.event_engine = EventEngine(async_mode=False)
        self.data_manager = DataManager()
        self.risk_manager = RiskManager()
        self.portfolio = Portfolio(initial_cash=1_000_000)
        self.broker = SimBroker()
        self.strategy: Optional[StrategyBase] = None
        self._symbols: List[str] = []
        self._current_bars: Dict[str, Bar] = {}  # 当前正在处理的K线

        # 注册事件处理器
        self.event_engine.register(EventType.MARKET, self._on_market)
        self.event_engine.register(EventType.SIGNAL, self._on_signal)
        self.event_engine.register(EventType.ORDER, self._on_order)
        self.event_engine.register(EventType.FILL, self._on_fill)

    def set_data(self, data_manager: DataManager):
        """设置数据源"""
        self.data_manager = data_manager
        self._symbols = data_manager.get_symbols()

    def set_strategy(self, strategy: StrategyBase):
        """设置策略"""
        self.strategy = strategy
        strategy.initialize()

    def set_cash(self, cash: float):
        """设置初始资金"""
        self.portfolio = Portfolio(initial_cash=cash)
        self.risk_manager = RiskManager(initial_capital=cash)

    def run(self) -> Dict:
        """运行回测"""
        # 获取所有交易日期
        all_dates = set()
        date_bars: Dict[str, Dict[str, Bar]] = {}

        for symbol in self._symbols:
            bars = self.data_manager.get_bars(symbol)
            for bar in bars:
                date_str = bar.datetime.strftime('%Y-%m-%d')
                all_dates.add(date_str)
                if date_str not in date_bars:
                    date_bars[date_str] = {}
                date_bars[date_str][symbol] = bar

        # 按日期顺序推送MarketEvent
        for date_str in sorted(all_dates):
            today_bars = date_bars.get(date_str, {})
            self._current_bars = today_bars  # 记录当天K线

            for symbol, bar in today_bars.items():
                self.portfolio.update_prices({symbol: bar.close})
                market_event = MarketEvent(data={
                    "symbol": symbol,
                    "datetime": bar.datetime,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "amount": bar.amount,
                    "change_pct": bar.change_pct,
                })
                self.event_engine.put(market_event)

            self.event_engine.run_all()
            self.portfolio.snapshot(date_str)

        return self._report()

    def _on_market(self, event: MarketEvent):
        """处理行情事件：分发给策略"""
        if self.strategy:
            signals = self.strategy.on_market(event)
            for signal in signals:
                self.event_engine.put(signal)

    def _on_signal(self, event: SignalEvent):
        """处理信号事件：经过风控检查，生成订单"""
        order = self.risk_manager.check_signal(event)
        if order:
            self.event_engine.put(order)

    def _on_order(self, event: OrderEvent):
        """处理订单事件：发送给模拟券商执行"""
        side = OrderSide.BUY if event.side == "BUY" else OrderSide.SELL
        order = Order(
            symbol=event.symbol,
            side=side,
            quantity=event.quantity,
            price=event.price,
        )

        # 使用当天的K线执行，而非缓存的最新K线
        bar = self._current_bars.get(event.symbol)
        if bar:
            self.broker.execute(order, bar)
            if order.status == OrderStatus.FILLED:
                fill_event = FillEvent(data={
                    "symbol": order.symbol,
                    "side": event.side,
                    "quantity": order.filled_quantity,
                    "price": order.filled_price,
                    "commission": order.commission,
                    "slippage": order.slippage,
                })
                self.event_engine.put(fill_event)

    def _on_fill(self, event: FillEvent):
        """处理成交事件：更新持仓和风控"""
        if event.side == "BUY":
            self.portfolio.execute_buy(
                event.symbol, event.quantity, event.fill_price, event.commission
            )
        else:
            self.portfolio.execute_sell(
                event.symbol, event.quantity, event.fill_price, event.commission
            )
        self.risk_manager.update_position(
            event.symbol, event.quantity, event.fill_price, event.side
        )

    def _report(self) -> Dict:
        """生成回测报告"""
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
            ret = (v['end'] - prev) / prev * 100 if prev and prev > 0 else \
                  (v['end'] - v['start']) / v['start'] * 100 if v['start'] > 0 else 0
            result.append({'month': m, 'return': round(ret, 2)})
            prev = v['end']
        return result
