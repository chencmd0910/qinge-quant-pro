"""A股风控规则 - 仓位/回撤/流动性"""
from dataclasses import dataclass


@dataclass
class PositionRule:
    """单标的仓位限制"""
    max_position_pct: float = 0.25   # 单标的最大仓位占比
    max_total_pct: float = 0.80      # 总仓位上限

    def check(self, symbol_value: float, total_value: float, buy_amount: float) -> tuple:
        """检查买入后仓位是否超限"""
        if total_value <= 0:
            return False, "总资产为0"
        new_value = symbol_value + buy_amount
        if new_value / total_value > self.max_position_pct:
            return False, f"单标的仓位 {new_value/total_value*100:.1f}% 超限 {self.max_position_pct*100:.0f}%"
        return True, ""


@dataclass
class DrawdownRule:
    """最大回撤限制"""
    max_drawdown_pct: float = 0.15   # 最大回撤15%

    def check(self, current_value: float, peak_value: float) -> tuple:
        """检查是否触发最大回撤"""
        if peak_value <= 0:
            return True, ""
        drawdown = (peak_value - current_value) / peak_value
        if drawdown >= self.max_drawdown_pct:
            return False, f"回撤 {drawdown*100:.1f}% 触发限制 {self.max_drawdown_pct*100:.0f}%，停止交易"
        return True, ""


@dataclass
class LiquidityRule:
    """流动性检查"""
    min_daily_volume: int = 100_000  # 最低日成交量

    def check(self, volume: float) -> tuple:
        """检查成交量是否足够"""
        if volume < self.min_daily_volume:
            return False, f"成交量 {volume:.0f} 低于阈值 {self.min_daily_volume:.0f}"
        return True, ""
