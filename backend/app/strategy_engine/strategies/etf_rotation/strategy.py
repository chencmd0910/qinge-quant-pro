"""ETF轮动策略 - IndicatorStrategy 示例

在多个ETF之间根据动量轮动：
- 计算每个ETF的N日收益率
- 买入收益率最高的ETF
- 每月调仓一次

标的池:
    510300 沪深300ETF
    510500 中证500ETF
    159915 创业板ETF
    515080 中证1000ETF
"""
from typing import List, Dict
from app.strategy_engine.indicator_strategy import IndicatorStrategy
from app.event_engine.core.event import MarketEvent, SignalEvent


class ETFRotationStrategy(IndicatorStrategy):
    """ETF轮动策略

    每月初比较各ETF过去20日收益率，持有最强的一只。
    """

    def __init__(self, symbols: List[str] = None, lookback: int = 20):
        self.symbols = symbols or ["510300", "510500", "159915", "515080"]
        self.lookback = lookback
        self.held_symbol = None
        self.bar_counts: Dict[str, int] = {}
        self.price_histories: Dict[str, List[float]] = {}
        super().__init__(name="etf_rotation", symbol=",".join(self.symbols))

    def setup(self):
        self.bar_counts = {s: 0 for s in self.symbols}
        self.price_histories = {s: [] for s in self.symbols}

    def indicators(self, bars):
        pass  # 不使用传统指标

    def buy_signal(self, bars) -> bool:
        return False  # 不使用传统信号

    def sell_signal(self, bars) -> bool:
        return False

    def on_market(self, event: MarketEvent) -> List[SignalEvent]:
        signals = []
        symbol = event.symbol
        close = event.close

        if symbol not in self.symbols:
            return signals

        # 记录价格
        if symbol not in self.price_histories:
            self.price_histories[symbol] = []
        self.price_histories[symbol].append(close)
        self.bar_counts[symbol] = self.bar_counts.get(symbol, 0) + 1

        # 每月初（每20个交易日）调仓
        total_bars = sum(self.bar_counts.values())
        if total_bars < self.lookback * len(self.symbols):
            return signals

        # 检查是否是调仓日（所有标的都收到足够数据）
        all_ready = all(
            len(self.price_histories.get(s, [])) >= self.lookback
            for s in self.symbols
        )
        if not all_ready:
            return signals

        # 计算动量（过去lookback日收益率）
        best_symbol = None
        best_return = -999

        for s in self.symbols:
            prices = self.price_histories.get(s, [])
            if len(prices) >= self.lookback:
                ret = (prices[-1] - prices[-self.lookback]) / prices[-self.lookback]
                if ret > best_return:
                    best_return = ret
                    best_symbol = s

        if best_symbol and best_symbol != self.held_symbol:
            # 卖出当前持仓
            if self.held_symbol:
                signals.append(self.emit_signal(
                    symbol=self.held_symbol, direction="SELL", strength=1.0,
                    price=0, reason=f"轮动卖出，切换到{best_symbol}"
                ))
            # 买入最强ETF
            signals.append(self.emit_signal(
                symbol=best_symbol, direction="BUY", strength=1.0,
                price=0, reason=f"动量最强，{self.lookback}日收益{best_return*100:.1f}%"
            ))
            self.held_symbol = best_symbol

        # 重置计数（每月调仓）
        if total_bars % (self.lookback * len(self.symbols)) == 0:
            for s in self.symbols:
                self.price_histories[s] = self.price_histories[s][-self.lookback:]

        return signals
