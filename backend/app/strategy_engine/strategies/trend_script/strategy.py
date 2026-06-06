"""趋势跟踪脚本策略 - ScriptStrategy 示例

用法:
    strategy = TrendScriptStrategy(symbol="510300")
"""
from app.strategy_engine.script_strategy import ScriptStrategy, StrategyContext


class TrendScriptStrategy(ScriptStrategy):
    """趋势跟踪（脚本模式）

    价格突破20日高点 → 买入
    价格跌破10日低点 → 卖出
    """

    def __init__(self, symbol: str = "", lookback: int = 20):
        self.symbol = symbol
        self.lookback = lookback
        self.position_held = False
        super().__init__(name="trend_script")

    def on_init(self):
        self.position_held = False

    def on_bar(self, ctx: StrategyContext):
        bars = ctx.get_bars(self.symbol, self.lookback + 1)
        if len(bars) < self.lookback + 1:
            return

        recent = bars[-(self.lookback + 1):-1]  # 不含当前bar
        current_close = bars[-1].close

        high_20 = max(b.high for b in recent)
        low_10 = min(b.low for b in recent[-10:])

        if not self.position_held and current_close > high_20:
            ctx.buy(self.symbol, quantity=0, reason=f"breakout_above_{high_20:.2f}")
            self.position_held = True
        elif self.position_held and current_close < low_10:
            ctx.sell(self.symbol, quantity=0, reason=f"breakdown_below_{low_10:.2f}")
            self.position_held = False
