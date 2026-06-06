"""Strategy Decay Monitor - Alpha衰减监控

监控策略Alpha是否持续下降:
    过去30天Alpha
    过去60天Alpha
    过去90天Alpha

如果Alpha持续下降 → 标记 DEGRADING
如果Alpha转负 → 标记 DEAD

这是量化世界最重要的问题:
    不是"找到策略"
    而是"发现策略失效"
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class DecayStatus(Enum):
    """策略衰减状态"""
    HEALTHY = "HEALTHY"         # Alpha稳定或上升
    DEGRADING = "DEGRADING"     # Alpha持续下降
    DEAD = "DEAD"               # Alpha转负
    RECOVERING = "RECOVERING"   # Alpha从低点回升


@dataclass
class DecayReport:
    """衰减报告"""
    strategy_id: str
    strategy_name: str
    status: DecayStatus
    alpha_30d: float
    alpha_60d: float
    alpha_90d: float
    alpha_trend: float        # 趋势斜率 (负=下降)
    days_since_peak: int      # 距Alpha峰值天数
    warning: str
    generated_at: str


class AlphaDecayMonitor:
    """Alpha衰减监控器"""

    def __init__(self):
        self.alpha_history: Dict[str, List[dict]] = {}  # strategy_id -> [{date, alpha}, ...]

    def record_alpha(self, strategy_id: str, date: str, alpha: float):
        """记录每日Alpha"""
        if strategy_id not in self.alpha_history:
            self.alpha_history[strategy_id] = []
        self.alpha_history[strategy_id].append({
            'date': date,
            'alpha': alpha,
        })
        # 保留最近180天
        self.alpha_history[strategy_id] = self.alpha_history[strategy_id][-180:]

    def check_decay(self, strategy_id: str, strategy_name: str = "") -> DecayReport:
        """检查策略Alpha衰减

        Returns:
            DecayReport
        """
        history = self.alpha_history.get(strategy_id, [])
        if len(history) < 30:
            return DecayReport(
                strategy_id=strategy_id,
                strategy_name=strategy_name,
                status=DecayStatus.HEALTHY,
                alpha_30d=0, alpha_60d=0, alpha_90d=0,
                alpha_trend=0, days_since_peak=0,
                warning="数据不足30天",
                generated_at=datetime.now().isoformat(),
            )

        # 计算不同窗口的Alpha
        alphas = [h['alpha'] for h in history]
        alpha_30d = sum(alphas[-30:]) / 30
        alpha_60d = sum(alphas[-60:]) / 60 if len(alphas) >= 60 else alpha_30d
        alpha_90d = sum(alphas[-90:]) / 90 if len(alphas) >= 90 else alpha_60d

        # Alpha趋势 (线性回归斜率)
        recent_30 = alphas[-30:]
        alpha_trend = self._trend_slope(recent_30)

        # 距峰值天数
        peak_idx = alphas.index(max(alphas))
        days_since_peak = len(alphas) - 1 - peak_idx

        # 判断状态
        status, warning = self._classify(
            alpha_30d, alpha_60d, alpha_90d, alpha_trend, days_since_peak
        )

        return DecayReport(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            status=status,
            alpha_30d=round(alpha_30d, 3),
            alpha_60d=round(alpha_60d, 3),
            alpha_90d=round(alpha_90d, 3),
            alpha_trend=round(alpha_trend, 4),
            days_since_peak=days_since_peak,
            warning=warning,
            generated_at=datetime.now().isoformat(),
        )

    def _classify(self, a30: float, a60: float, a90: float,
                  trend: float, days_peak: int) -> tuple:
        """分类衰减状态"""
        # Alpha转负
        if a30 < 0 and a60 < 0:
            return DecayStatus.DEAD, f"Alpha转负: 30d={a30:.3f}%, 60d={a60:.3f}%"

        # Alpha持续下降 (30d < 60d < 90d 且趋势为负)
        if a30 < a60 < a90 and trend < 0:
            return DecayStatus.DEGRADING, f"Alpha持续下降: 30d={a30:.3f}% < 60d={a60:.3f}% < 90d={a90:.3f}%"

        # 从低点回升
        if a30 > a60 and a60 < a90:
            return DecayStatus.RECOVERING, f"Alpha回升: 30d={a30:.3f}% > 60d={a60:.3f}%"

        # Alpha稳定
        return DecayStatus.HEALTHY, "Alpha稳定"

    def _trend_slope(self, values: List[float]) -> float:
        """线性回归斜率"""
        n = len(values)
        if n < 2:
            return 0
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean)**2 for i in range(n))
        return numerator / denominator if denominator > 0 else 0

    def check_all(self, strategies: Dict[str, str]) -> List[DecayReport]:
        """检查所有策略

        Args:
            strategies: {strategy_id: strategy_name}

        Returns:
            所有策略的衰减报告
        """
        reports = []
        for sid, name in strategies.items():
            reports.append(self.check_decay(sid, name))
        return reports

    def get_summary(self, reports: List[DecayReport]) -> dict:
        """汇总"""
        return {
            'total': len(reports),
            'healthy': len([r for r in reports if r.status == DecayStatus.HEALTHY]),
            'degrading': len([r for r in reports if r.status == DecayStatus.DEGRADING]),
            'dead': len([r for r in reports if r.status == DecayStatus.DEAD]),
            'recovering': len([r for r in reports if r.status == DecayStatus.RECOVERING]),
            'alerts': [
                f"{r.strategy_name}: {r.warning}"
                for r in reports
                if r.status in (DecayStatus.DEGRADING, DecayStatus.DEAD)
            ],
        }
