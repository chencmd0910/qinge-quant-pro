"""通用风控规则 - 所有市场共用

仓位限制 / 最大回撤 / 单日亏损
"""
from dataclasses import dataclass


@dataclass
class UniversalRiskConfig:
    """通用风控配置"""
    max_position_pct: float = 0.25    # 单标的最大仓位
    max_total_pct: float = 0.80       # 总仓位上限
    max_drawdown_pct: float = 0.15    # 最大回撤
    max_daily_loss_pct: float = 0.03  # 单日最大亏损
    max_orders_per_day: int = 200     # 日内最大下单数
    stop_loss_pct: float = 0.08       # 单笔止损


class UniversalRisk:
    """通用风控 - 所有市场共用"""

    def __init__(self, config: UniversalRiskConfig = None):
        self.config = config or UniversalRiskConfig()
        self.daily_pnl = 0.0
        self.order_count_today = 0
        self.peak_value = 0.0

    def check_position_limit(self, symbol_value: float, total_value: float, buy_amount: float) -> tuple:
        if total_value <= 0:
            return False, "总资产为0"
        new_value = symbol_value + buy_amount
        if new_value / total_value > self.config.max_position_pct:
            return False, f"单标的仓位 {new_value/total_value*100:.1f}% 超限"
        return True, ""

    def check_total_position(self, invested: float, total_value: float) -> tuple:
        if total_value <= 0:
            return False, "总资产为0"
        if invested / total_value > self.config.max_total_pct:
            return False, f"总仓位 {invested/total_value*100:.1f}% 超限"
        return True, ""

    def check_drawdown(self, current_value: float) -> tuple:
        if current_value > self.peak_value:
            self.peak_value = current_value
        if self.peak_value <= 0:
            return True, ""
        dd = (self.peak_value - current_value) / self.peak_value
        if dd >= self.config.max_drawdown_pct:
            return False, f"回撤 {dd*100:.1f}% 触发限制"
        return True, ""

    def check_daily_loss(self) -> tuple:
        if self.daily_pnl < 0 and abs(self.daily_pnl) / self.peak_value > self.config.max_daily_loss_pct:
            return False, f"单日亏损超限"
        return True, ""

    def check_order_count(self) -> tuple:
        if self.order_count_today >= self.config.max_orders_per_day:
            return False, f"日内下单次数超限"
        return True, ""

    def reset_daily(self):
        self.daily_pnl = 0.0
        self.order_count_today = 0

    def update_pnl(self, pnl: float):
        self.daily_pnl += pnl
        self.order_count_today += 1
