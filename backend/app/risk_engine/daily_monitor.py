"""Daily Risk Monitor - 每日风险报告

每日输出:
- 收益/回撤
- 波动率
- Beta
- 行业暴露
- 仓位集中度
- 风险评分 (0-100)
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DailyRiskReport:
    """每日风险报告"""
    date: str
    portfolio_value: float
    daily_return: float
    cumulative_return: float
    max_drawdown: float
    current_drawdown: float
    volatility_20d: float
    beta: float
    var_95: float
    sector_exposure: Dict[str, float]
    max_position_pct: float
    concentration_hhi: float
    drawdown_level: str
    risk_score: int  # 0-100, 越低越危险
    alerts: List[str] = field(default_factory=list)


class DailyRiskMonitor:
    """每日风险监控"""

    def __init__(self, initial_value: float = 1_000_000):
        self.initial_value = initial_value
        self.peak_value = initial_value
        self.history: List[dict] = []  # [{date, value, daily_return}, ...]

    def generate_report(self, date: str, current_value: float,
                        positions: Dict[str, dict] = None,
                        sector_exposure: Dict[str, float] = None) -> DailyRiskReport:
        """生成每日风险报告

        Args:
            date: 日期
            current_value: 当前净值
            positions: {symbol: {"weight": float, "value": float}}
            sector_exposure: {sector: pct}
        """
        # 更新峰值
        if current_value > self.peak_value:
            self.peak_value = current_value

        # 日收益
        prev_value = self.history[-1]["value"] if self.history else self.initial_value
        daily_return = (current_value / prev_value - 1) * 100 if prev_value > 0 else 0

        # 累计收益
        cumulative = (current_value / self.initial_value - 1) * 100

        # 回撤
        max_dd = (self.peak_value - current_value) / self.peak_value * 100 if self.peak_value > 0 else 0

        # 20日波动率
        recent_returns = [h["daily_return"] for h in self.history[-20:]]
        if len(recent_returns) > 1:
            mean = sum(recent_returns) / len(recent_returns)
            var = sum((r - mean)**2 for r in recent_returns) / (len(recent_returns) - 1)
            vol_20d = (var ** 0.5) * (252 ** 0.5)  # 年化
        else:
            vol_20d = 0

        # 仓位集中度
        weights = [p.get("weight", 0) for p in (positions or {}).values()]
        max_pos_pct = max(weights) * 100 if weights else 0
        hhi = sum(w**2 for w in weights) if weights else 0

        # 回撤级别
        if max_dd >= 20:
            dd_level = "LEVEL3_LIQUIDATE"
        elif max_dd >= 15:
            dd_level = "LEVEL2_FREEZE"
        elif max_dd >= 10:
            dd_level = "LEVEL1_REDUCE"
        else:
            dd_level = "NORMAL"

        # 风险评分 (0-100)
        risk_score = self._calculate_risk_score(
            max_dd, vol_20d, max_pos_pct, hhi
        )

        # 告警
        alerts = []
        if max_dd >= 15:
            alerts.append(f"CRITICAL: 回撤 {max_dd:.1f}% >= 15%")
        elif max_dd >= 10:
            alerts.append(f"WARNING: 回撤 {max_dd:.1f}% >= 10%")
        if max_pos_pct > 30:
            alerts.append(f"WARNING: 单标的仓位 {max_pos_pct:.1f}% > 30%")
        if hhi > 0.25:
            alerts.append(f"WARNING: 集中度过高 HHI={hhi:.3f}")
        if vol_20d > 30:
            alerts.append(f"WARNING: 波动率 {vol_20d:.1f}% > 30%")

        # 记录历史
        self.history.append({
            "date": date, "value": current_value,
            "daily_return": daily_return,
        })

        return DailyRiskReport(
            date=date,
            portfolio_value=round(current_value, 2),
            daily_return=round(daily_return, 2),
            cumulative_return=round(cumulative, 2),
            max_drawdown=round(max_dd, 2),
            current_drawdown=round(max_dd, 2),
            volatility_20d=round(vol_20d, 2),
            beta=1.0,  # 需要外部传入
            var_95=round(vol_20d * 1.645 / (252**0.5), 2),
            sector_exposure=sector_exposure or {},
            max_position_pct=round(max_pos_pct, 2),
            concentration_hhi=round(hhi, 4),
            drawdown_level=dd_level,
            risk_score=risk_score,
            alerts=alerts,
        )

    def _calculate_risk_score(self, max_dd: float, vol: float,
                               max_pos: float, hhi: float) -> int:
        """风险评分 (0-100, 越低越危险)

        回撤分 (0-40): -20%~0% -> 40~0
        波动分 (0-25): 0%~30% -> 25~0
        集中分 (0-20): 0~0.5 -> 20~0
        仓位分 (0-15): 0%~50% -> 15~0
        """
        dd_score = max(0, min(40, (20 - abs(max_dd)) / 20 * 40))
        vol_score = max(0, min(25, (30 - vol) / 30 * 25))
        conc_score = max(0, min(20, (0.5 - hhi) / 0.5 * 20))
        pos_score = max(0, min(15, (50 - max_pos) / 50 * 15))

        return int(dd_score + vol_score + conc_score + pos_score)
