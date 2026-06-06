"""Correlation Matrix - 相关性分析

计算:
- 策略相关性: 策略间收益相关
- 因子相关性: 因子间暴露相关
- 持仓相关性: 持仓标的相关

避免: 多个策略实际押注同一风险因子
"""
from typing import Dict, List
from dataclasses import dataclass
import math


@dataclass
class CorrelationMatrix:
    """相关性矩阵"""
    labels: List[str]
    matrix: List[List[float]]  # NxN 矩阵
    high_corr_pairs: List[dict]  # 高相关对


class CorrelationAnalyzer:
    """相关性分析器"""

    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold  # 高相关阈值

    def calculate_matrix(self, data: Dict[str, List[float]]) -> CorrelationMatrix:
        """计算相关性矩阵

        Args:
            data: {name: [values]}

        Returns:
            CorrelationMatrix
        """
        labels = sorted(data.keys())
        n = len(labels)

        # 计算相关系数矩阵
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                elif j > i:
                    corr = self._pearson(data[labels[i]], data[labels[j]])
                    matrix[i][j] = round(corr, 4)
                    matrix[j][i] = round(corr, 4)

        # 找高相关对
        high_corr = []
        for i in range(n):
            for j in range(i + 1, n):
                if abs(matrix[i][j]) >= self.threshold:
                    high_corr.append({
                        "pair": f"{labels[i]} vs {labels[j]}",
                        "correlation": matrix[i][j],
                        "risk": "HIGH" if abs(matrix[i][j]) >= 0.85 else "MEDIUM",
                    })

        high_corr.sort(key=lambda x: -abs(x["correlation"]))

        return CorrelationMatrix(
            labels=labels,
            matrix=matrix,
            high_corr_pairs=high_corr,
        )

    def check_diversification(self, strategies: List[dict]) -> dict:
        """检查策略多样化

        Args:
            strategies: 策略列表，需有 factor_categories

        Returns:
            多样化分析结果
        """
        # 按因子类别统计
        category_count = {}
        for s in strategies:
            for cat in s.get("factor_categories", []):
                category_count[cat] = category_count.get(cat, 0) + 1

        total = len(strategies)
        concentration = sum((c / total)**2 for c in category_count.values())  # HHI

        # 最大类别占比
        max_cat = max(category_count.values()) if category_count else 0
        max_pct = max_cat / total * 100 if total > 0 else 0

        # 警告
        warnings = []
        if max_pct > 50:
            warnings.append(f"最大类别占比 {max_pct:.0f}% > 50%, 集中度过高")
        if concentration > 0.3:
            warnings.append(f"HHI {concentration:.3f} > 0.3, 多样化不足")

        return {
            "total_strategies": total,
            "category_distribution": category_count,
            "hhi": round(concentration, 4),
            "max_category_pct": round(max_pct, 1),
            "diversification_score": round((1 - concentration) * 100, 1),
            "warnings": warnings,
        }

    def _pearson(self, x: List[float], y: List[float]) -> float:
        """Pearson相关系数"""
        n = min(len(x), len(y))
        if n < 2:
            return 0
        x, y = x[:n], y[:n]
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        cov = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y)) / n
        std_x = math.sqrt(sum((a - mean_x)**2 for a in x) / n)
        std_y = math.sqrt(sum((b - mean_y)**2 for b in y) / n)
        if std_x > 0 and std_y > 0:
            return cov / (std_x * std_y)
        return 0
