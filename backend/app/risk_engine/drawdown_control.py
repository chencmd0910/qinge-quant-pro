"""Dynamic Drawdown Control - 动态回撤控制

三级控制:
    Level 1: 回撤 >= 10% → 减仓50%
    Level 2: 回撤 >= 15% → 冻结开仓
    Level 3: 回撤 >= 20% → 风险模式 (全部平仓)

动作:
    REDUCE: 减仓
    FREEZE: 冻结开仓
    LIQUIDATE: 全部平仓
    NORMAL: 正常交易
"""
from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class DrawdownLevel(Enum):
    NORMAL = "NORMAL"
    REDUCE = "REDUCE"
    FREEZE = "FREEZE"
    LIQUIDATE = "LIQUIDATE"


@dataclass
class DrawdownState:
    """回撤状态"""
    level: DrawdownLevel
    current_drawdown: float  # 当前回撤 %
    peak_value: float        # 最高净值
    current_value: float     # 当前净值
    action: str              # 建议动作
    reduce_pct: float = 0    # 减仓比例


class DynamicDrawdownControl:
    """动态回撤控制"""

    def __init__(self, level1: float = 10, level2: float = 15, level3: float = 20):
        self.level1_threshold = level1   # 减仓阈值 %
        self.level2_threshold = level2   # 冻结阈值 %
        self.level3_threshold = level3   # 平仓阈值 %
        self.peak_value = 0
        self.current_level = DrawdownLevel.NORMAL
        self.is_frozen = False

    def update(self, current_value: float) -> DrawdownState:
        """更新净值，返回回撤状态"""
        if current_value > self.peak_value:
            self.peak_value = current_value

        if self.peak_value <= 0:
            return DrawdownState(
                level=DrawdownLevel.NORMAL,
                current_drawdown=0, peak_value=0,
                current_value=current_value, action="NORMAL",
            )

        drawdown = (self.peak_value - current_value) / self.peak_value * 100

        # 判断级别
        if drawdown >= self.level3_threshold:
            level = DrawdownLevel.LIQUIDATE
            action = "LIQUIDATE: 全部平仓"
            reduce_pct = 100
        elif drawdown >= self.level2_threshold:
            level = DrawdownLevel.FREEZE
            action = "FREEZE: 冻结开仓"
            reduce_pct = 0
        elif drawdown >= self.level1_threshold:
            level = DrawdownLevel.REDUCE
            action = "REDUCE: 减仓50%"
            reduce_pct = 50
        else:
            level = DrawdownLevel.NORMAL
            action = "NORMAL: 正常交易"
            reduce_pct = 0

        self.current_level = level
        self.is_frozen = level in (DrawdownLevel.FREEZE, DrawdownLevel.LIQUIDATE)

        return DrawdownState(
            level=level,
            current_drawdown=round(drawdown, 2),
            peak_value=round(self.peak_value, 2),
            current_value=round(current_value, 2),
            action=action,
            reduce_pct=reduce_pct,
        )

    def can_open_position(self) -> Tuple[bool, str]:
        """是否允许开仓"""
        if self.current_level == DrawdownLevel.LIQUIDATE:
            return False, "风险模式: 全部平仓中"
        if self.current_level == DrawdownLevel.FREEZE:
            return False, "冻结模式: 禁止开仓"
        return True, "允许开仓"

    def get_position_multiplier(self) -> float:
        """仓位乘数 (减仓用)"""
        if self.current_level == DrawdownLevel.LIQUIDATE:
            return 0
        if self.current_level == DrawdownLevel.REDUCE:
            return 0.5
        return 1.0

    def reset(self):
        """重置状态"""
        self.peak_value = 0
        self.current_level = DrawdownLevel.NORMAL
        self.is_frozen = False
