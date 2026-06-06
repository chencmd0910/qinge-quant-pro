"""风控管理器 - 两层风控

通用层: UniversalRisk (仓位/回撤/单日亏损 -> 所有市场)
市场层: MarketRule (涨跌停/T+1 -> 仅A股, 盘前盘后 -> 美股, etc.)
"""
from typing import Optional, Tuple, List, Dict
from .universal_risk import UniversalRisk, UniversalRiskConfig
from .market_rules.a_share_rule import AShareRule
from ..event_engine.core.event import SignalEvent, OrderEvent
from ..data_engine.providers.provider_base import Market


class RiskManager:
    """风控管理器

    两层风控:
        Layer 1: UniversalRisk → 所有市场通用
        Layer 2: MarketRule → 市场特有规则

    使用:
        rm = RiskManager(initial_capital=1_000_000, market=Market.A_SHARE)
        order = rm.check_signal(signal)  # → OrderEvent or None
    """

    def __init__(self, initial_capital: float = 1_000_000,
                 market: Market = Market.A_SHARE,
                 config: UniversalRiskConfig = None):
        self.initial_capital = initial_capital
        self.market = market
        self.universal = UniversalRisk(config)
        self.universal.peak_value = initial_capital

        # 市场规则映射
        self._market_rules = self._load_market_rules()

        # 持仓跟踪
        self.positions: Dict[str, Dict] = {}
        self.last_buy_dates: Dict[str, str] = {}  # symbol → last buy date

    def _load_market_rules(self) -> dict:
        """加载市场特有规则"""
        if self.market == Market.A_SHARE:
            return {"t_plus": True, "limit": AShareRule()}
        elif self.market == Market.HK_STOCK:
            return {"t_plus": False, "limit": None}
        elif self.market == Market.US_STOCK:
            return {"t_plus": False, "limit": None}
        elif self.market == Market.CRYPTO:
            return {"t_plus": False, "limit": None}
        return {"t_plus": False, "limit": None}

    def check_signal(self, signal: SignalEvent,
                     current_price: float = 0,
                     current_volume: float = 0,
                     date_str: str = "") -> Optional[OrderEvent]:
        """风控检查信号，通过则生成订单

        Returns:
            OrderEvent if approved, None if rejected
        """
        symbol = signal.symbol
        direction = signal.direction
        quantity = int(signal.strength * 100)  # 信号强度→手

        # === Layer 1: 通用风控 ===
        ok, reason = self.universal.check_order_count()
        if not ok:
            print(f"[Risk] {symbol} {direction}: {reason}")
            return None

        ok, reason = self.universal.check_drawdown(
            sum(p.get("value", 0) for p in self.positions.values()) + self.universal.peak_value
        )
        if not ok:
            print(f"[Risk] {reason}")
            return None

        # === Layer 2: 市场规则 ===
        limit_rule = self._market_rules.get("limit")
        if limit_rule and hasattr(limit_rule, 'can_buy'):
            if direction == "BUY":
                ok, reason = limit_rule.can_buy(0)  # change_pct would come from market data
                if not ok:
                    print(f"[Risk] {symbol}: {reason}")
                    return None
            else:
                ok, reason = limit_rule.can_sell(0)
                if not ok:
                    print(f"[Risk] {symbol}: {reason}")
                    return None

        # T+1 检查（A股特有）
        if self._market_rules.get("t_plus") and direction == "SELL":
            last_buy = self.last_buy_dates.get(symbol, "")
            if AShareRule.is_t1_restricted(last_buy, date_str):
                print(f"[Risk] {symbol}: T+1限制，当日买入不可卖出")
                return None

        # === 生成订单 ===
        order = OrderEvent(data={
            "symbol": symbol, "side": direction, "quantity": quantity,
            "price": current_price, "signal": signal,
        })
        return order

    def update_position(self, symbol: str, quantity: float, price: float, side: str, date_str: str = ""):
        """更新持仓记录"""
        if side == "BUY":
            self.positions[symbol] = {
                "quantity": quantity, "avg_cost": price,
                "value": quantity * price,
            }
            self.last_buy_dates[symbol] = date_str
        elif side == "SELL":
            if symbol in self.positions:
                old = self.positions[symbol]
                pnl = (price - old["avg_cost"]) * quantity
                self.universal.update_pnl(pnl)
                old["quantity"] = max(0, old["quantity"] - quantity)
                if old["quantity"] <= 0:
                    del self.positions[symbol]

    def reset_daily(self):
        self.universal.reset_daily()
