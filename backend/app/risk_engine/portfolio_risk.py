"""Portfolio Risk - 组合级风险监控

输出:
- Portfolio Volatility: 组合波动率
- Portfolio VaR: 风险价值
- Portfolio Beta: 相对基准的Beta
- Sector Exposure: 行业暴露
- Max Position Weight: 最大仓位权重
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import math


@dataclass
class PortfolioRiskReport:
    """组合风险报告"""
    portfolio_volatility: float   # 年化波动率
    portfolio_var_95: float       # 95% VaR (日)
    portfolio_var_99: float       # 99% VaR (日)
    portfolio_beta: float         # 相对基准Beta
    max_position_weight: float    # 最大单标的权重
    sector_exposure: Dict[str, float]  # 行业暴露
    concentration_index: float    # HHI集中度指数
    correlation_risk: float       # 相关性风险 (0-1)


class PortfolioRiskCalculator:
    """组合风险计算器"""

    # 行业分类 (简化版)
    SECTOR_MAP = {
        "510300.SH": "宽基", "510500.SH": "宽基", "159915.SZ": "宽基",
        "515080.SH": "宽基", "000300.SH": "宽基", "000905.SH": "宽基",
    }

    def calculate(self, positions: Dict[str, dict],
                  returns: Dict[str, List[float]] = None,
                  benchmark_returns: List[float] = None) -> PortfolioRiskReport:
        """计算组合风险

        Args:
            positions: {symbol: {"weight": float, "value": float, "sector": str}}
            returns: {symbol: [daily_returns]}
            benchmark_returns: [benchmark_daily_returns]
        """
        weights = {s: p.get("weight", 0) for s, p in positions.items()}
        total_weight = sum(weights.values())

        # 归一化权重
        if total_weight > 0:
            weights = {s: w / total_weight for s, w in weights.items()}

        # 组合波动率
        vol = self._portfolio_volatility(weights, returns or {})

        # VaR
        var_95 = vol * 1.645 / math.sqrt(252)  # 日VaR
        var_99 = vol * 2.326 / math.sqrt(252)

        # Beta
        beta = self._portfolio_beta(weights, returns or {}, benchmark_returns or [])

        # 行业暴露
        sector_exp = {}
        for s, w in weights.items():
            sector = positions[s].get("sector", self.SECTOR_MAP.get(s, "其他"))
            sector_exp[sector] = sector_exp.get(sector, 0) + w
        sector_exp = {k: round(v * 100, 2) for k, v in sector_exp.items()}

        # HHI集中度
        hhi = sum(w**2 for w in weights.values())

        # 最大仓位
        max_weight = max(weights.values()) if weights else 0

        return PortfolioRiskReport(
            portfolio_volatility=round(vol * 100, 2),
            portfolio_var_95=round(var_95 * 100, 2),
            portfolio_var_99=round(var_99 * 100, 2),
            portfolio_beta=round(beta, 3),
            max_position_weight=round(max_weight * 100, 2),
            sector_exposure=sector_exp,
            concentration_index=round(hhi, 4),
            correlation_risk=round(self._avg_correlation(returns or {}), 3),
        )

    def _portfolio_volatility(self, weights: Dict[str, float],
                               returns: Dict[str, List[float]]) -> float:
        """组合波动率 (简化: 假设相关性=0.5)"""
        if not weights or not returns:
            return 0

        variances = []
        for s, w in weights.items():
            rets = returns.get(s, [])
            if len(rets) > 1:
                mean = sum(rets) / len(rets)
                var = sum((r - mean)**2 for r in rets) / (len(rets) - 1)
            else:
                var = 0.04  # 默认20%年化
            variances.append((w, var))

        # 简化组合方差: sum(w_i^2 * var_i) + 2 * 0.5 * sum(w_i * w_j * sqrt(var_i * var_j))
        portfolio_var = sum(w**2 * v for w, v in variances)

        # 加入相关性 (假设0.5)
        for i in range(len(variances)):
            for j in range(i + 1, len(variances)):
                wi, vi = variances[i]
                wj, vj = variances[j]
                portfolio_var += 2 * 0.5 * wi * wj * math.sqrt(vi * vj)

        return math.sqrt(portfolio_var) if portfolio_var > 0 else 0

    def _portfolio_beta(self, weights: Dict[str, float],
                        returns: Dict[str, List[float]],
                        benchmark_returns: List[float]) -> float:
        """组合Beta"""
        if not benchmark_returns or not returns:
            return 1.0

        # 组合日收益
        min_len = min(len(benchmark_returns), min((len(returns.get(s, [])) for s in weights), default=0))
        if min_len < 10:
            return 1.0

        portfolio_returns = []
        for i in range(min_len):
            day_return = sum(weights.get(s, 0) * returns.get(s, [0])[i] for s in weights)
            portfolio_returns.append(day_return)

        bench = benchmark_returns[:min_len]

        # Beta = Cov(Rp, Rb) / Var(Rb)
        mean_p = sum(portfolio_returns) / len(portfolio_returns)
        mean_b = sum(bench) / len(bench)

        cov = sum((p - mean_p) * (b - mean_b) for p, b in zip(portfolio_returns, bench)) / len(bench)
        var_b = sum((b - mean_b)**2 for b in bench) / len(bench)

        return cov / var_b if var_b > 0 else 1.0

    def _avg_correlation(self, returns: Dict[str, List[float]]) -> float:
        """平均相关性"""
        symbols = list(returns.keys())
        if len(symbols) < 2:
            return 0

        correlations = []
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                r1 = returns[symbols[i]]
                r2 = returns[symbols[j]]
                if len(r1) > 10 and len(r2) > 10:
                    min_len = min(len(r1), len(r2))
                    corr = self._correlation(r1[:min_len], r2[:min_len])
                    correlations.append(corr)

        return sum(correlations) / len(correlations) if correlations else 0

    def _correlation(self, x: List[float], y: List[float]) -> float:
        """计算相关系数"""
        n = len(x)
        if n < 2:
            return 0
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        cov = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y)) / n
        std_x = math.sqrt(sum((a - mean_x)**2 for a in x) / n)
        std_y = math.sqrt(sum((b - mean_y)**2 for b in y) / n)
        if std_x > 0 and std_y > 0:
            return cov / (std_x * std_y)
        return 0
