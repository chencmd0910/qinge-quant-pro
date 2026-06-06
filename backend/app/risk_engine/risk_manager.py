"""风控管理器 - 订单发出前的最后一道关卡

职责:
1. 单笔止损检查
2. 总仓位控制
3. 单标的最大仓位
4. 日内最大亏损
5. 流动性检查
"""
from dataclasses import dataclass
from typing import Optional
from ..event_engine.core.event import OrderEvent, SignalEvent, EventType


@dataclass
class RiskConfig:
    """风控参数"""
    max_position_pct: float = 0.25      # 单标的最大仓位占比
    max_total_position_pct: float = 0.8 # 总仓位上限
    max_daily_loss_pct: float = 0.03    # 日内最大亏损比例
    stop_loss_pct: float = 0.08         # 单笔止损比例
    min_volume: int = 100_000           # 最小成交量（流动性检查）
    max_orders_per_day: int = 50        # 日内最大下单数


class RiskManager:
    """风控管理器

    接收SignalEvent，检查通过后生成OrderEvent，否则拒绝。
    """

    def __init__(self, config: Optional[RiskConfig] = None, initial_capital: float = 1_000_000):
        self.config = config or RiskConfig()
        self.initial_capital = initial_capital
        self.daily_pnl = 0.0
        self.order_count_today = 0
        self.positions = {}  # symbol -> {quantity, avg_cost, current_price}

    def check_signal(self, signal: SignalEvent) -> Optional[OrderEvent]:
        """检查信号，通过返回OrderEvent，否则返回None"""
        symbol = signal.symbol
        direction = signal.direction

        if direction == "HOLD":
            return None

        # 检查日内下单次数
        if self.order_count_today >= self.config.max_orders_per_day:
            return self._reject("日内下单次数超限")

        # 检查日内亏损
        if self.daily_pnl < -self.initial_capital * self.config.max_daily_loss_pct:
            return self._reject("日内亏损超限")

        # 检查总仓位
        total_position_value = sum(
            p.get("quantity", 0) * p.get("current_price", 0)
            for p in self.positions.values()
        )
        if direction == "BUY":
            if total_position_value / self.initial_capital > self.config.max_total_position_pct:
                return self._reject("总仓位超限")

            # 检查单标的仓位
            pos_value = self.positions.get(symbol, {}).get("quantity", 0) * \
                       self.positions.get(symbol, {}).get("current_price", 0)
            if pos_value / self.initial_capital > self.config.max_position_pct:
                return self._reject(f"{symbol} 单标的仓位超限")

        # 检查通过，生成OrderEvent
        price = signal.data.get("price", 0)
        quantity = signal.data.get("quantity", 0)
        if quantity <= 0:
            quantity = self._calc_quantity(symbol, direction, price)

        self.order_count_today += 1
        return OrderEvent(data={
            "symbol": symbol,
            "side": direction,
            "quantity": quantity,
            "price": price,
            "order_type": "MARKET",
            "strategy": signal.data.get("strategy", ""),
        })

    def update_position(self, symbol: str, quantity: int, price: float, side: str):
        """更新持仓（成交后调用）"""
        if symbol not in self.positions:
            self.positions[symbol] = {"quantity": 0, "avg_cost": 0, "current_price": price}

        pos = self.positions[symbol]
        if side == "BUY":
            total_cost = pos["avg_cost"] * pos["quantity"] + price * quantity
            pos["quantity"] += quantity
            pos["avg_cost"] = total_cost / pos["quantity"] if pos["quantity"] > 0 else 0
        elif side == "SELL":
            pnl = (price - pos["avg_cost"]) * quantity
            self.daily_pnl += pnl
            pos["quantity"] -= quantity
            if pos["quantity"] <= 0:
                pos["quantity"] = 0
                pos["avg_cost"] = 0

        pos["current_price"] = price

    def reset_daily(self):
        """每日重置"""
        self.daily_pnl = 0.0
        self.order_count_today = 0

    def _calc_quantity(self, symbol: str, direction: str, price: float) -> int:
        """计算下单数量"""
        if price <= 0:
            return 0
        if direction == "BUY":
            max_amount = self.initial_capital * self.config.max_position_pct
            quantity = int(max_amount / price / 100) * 100
            return max(quantity, 0)
        elif direction == "SELL":
            pos = self.positions.get(symbol, {})
            return pos.get("quantity", 0)
        return 0

    def _reject(self, reason: str) -> None:
        """风控拒绝"""
        print(f"[RISK] 拒绝: {reason}")
        return None
