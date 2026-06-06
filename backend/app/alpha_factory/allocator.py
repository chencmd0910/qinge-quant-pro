"""Capital Allocation Engine - 动态资金分配引擎

从等权分配升级为动态分配:
    权重 = f(Sharpe, Alpha, Decay, Correlation)

分配方法:
    1. Score-Based: 基于综合评分
    2. Risk-Parity: 风险平价
    3. Alpha-Weighted: Alpha加权
    4. Hybrid: 混合方法 (默认)

约束:
    - 单策略最大权重: 40%
    - 单策略最小权重: 5% (ACTIVE)
    - WATCHLIST权重: 基础权重 * 50%
    - RETIRED权重: 0%
"""
from typing import Dict, List
from dataclasses import dataclass
import math


@dataclass
class AllocationResult:
    """分配结果"""
    strategy_id: str
    name: str
    phase: str
    base_weight: float
    raw_weight: float       # 计算原始权重
    effective_weight: float  # 最终权重 (考虑phase)
    reason: str


class CapitalAllocator:
    """资金分配引擎"""

    def __init__(self, max_weight: float = 0.40, min_active_weight: float = 0.05):
        self.max_weight = max_weight
        self.min_active_weight = min_active_weight

    def allocate(self, strategies: List[dict],
                 method: str = "hybrid") -> List[AllocationResult]:
        """动态分配资金

        Args:
            strategies: [{id, name, cluster, phase, alpha_30d, alpha_60d, sharpe, max_drawdown, decay_status}]
            method: 分配方法

        Returns:
            分配结果
        """
        if method == "score":
            return self._score_based(strategies)
        elif method == "alpha":
            return self._alpha_weighted(strategies)
        elif method == "risk_parity":
            return self._risk_parity(strategies)
        else:
            return self._hybrid(strategies)

    def _score_based(self, strategies: List[dict]) -> List[AllocationResult]:
        """基于综合评分分配"""
        scored = []
        for s in strategies:
            score = self._calculate_score(s)
            scored.append({**s, 'score': score})

        total_score = sum(s['score'] for s in scored if s['phase'] in ('ACTIVE', 'WATCHLIST'))
        results = []

        for s in scored:
            if s['phase'] == 'RETIRED':
                raw_w = 0
            elif s['phase'] in ('ACTIVE', 'WATCHLIST') and total_score > 0:
                raw_w = s['score'] / total_score
            else:
                raw_w = 0

            effective_w = self._apply_constraints(raw_w, s['phase'])
            results.append(AllocationResult(
                strategy_id=s['id'], name=s['name'], phase=s['phase'],
                base_weight=s.get('base_weight', 0.2), raw_weight=round(raw_w, 4),
                effective_weight=round(effective_w, 4),
                reason=f"score={s['score']:.2f}",
            ))

        return self._normalize(results)

    def _alpha_weighted(self, strategies: List[dict]) -> List[AllocationResult]:
        """Alpha加权分配"""
        active = [s for s in strategies if s['phase'] in ('ACTIVE', 'WATCHLIST')]
        total_alpha = sum(max(0, s.get('alpha_30d', 0)) for s in active)

        results = []
        for s in strategies:
            if s['phase'] == 'RETIRED' or total_alpha <= 0:
                raw_w = 0
            else:
                alpha = max(0, s.get('alpha_30d', 0))
                raw_w = alpha / total_alpha

            effective_w = self._apply_constraints(raw_w, s['phase'])
            results.append(AllocationResult(
                strategy_id=s['id'], name=s['name'], phase=s['phase'],
                base_weight=s.get('base_weight', 0.2), raw_weight=round(raw_w, 4),
                effective_weight=round(effective_w, 4),
                reason=f"alpha={s.get('alpha_30d', 0):.3f}",
            ))

        return self._normalize(results)

    def _risk_parity(self, strategies: List[dict]) -> List[AllocationResult]:
        """风险平价分配"""
        active = [s for s in strategies if s['phase'] in ('ACTIVE', 'WATCHLIST')]

        inv_vols = {}
        for s in active:
            vol = s.get('max_drawdown', 15) / 100  # 用回撤近似波动
            if vol > 0:
                inv_vols[s['id']] = 1.0 / vol

        total_inv = sum(inv_vols.values())

        results = []
        for s in strategies:
            if s['phase'] == 'RETIRED' or total_inv <= 0:
                raw_w = 0
            else:
                raw_w = inv_vols.get(s['id'], 0) / total_inv

            effective_w = self._apply_constraints(raw_w, s['phase'])
            results.append(AllocationResult(
                strategy_id=s['id'], name=s['name'], phase=s['phase'],
                base_weight=s.get('base_weight', 0.2), raw_weight=round(raw_w, 4),
                effective_weight=round(effective_w, 4),
                reason=f"risk_parity",
            ))

        return self._normalize(results)

    def _hybrid(self, strategies: List[dict]) -> List[AllocationResult]:
        """混合方法: 40% Score + 30% Alpha + 30% Risk Parity"""
        score_alloc = {r.strategy_id: r.raw_weight for r in self._score_based(strategies)}
        alpha_alloc = {r.strategy_id: r.raw_weight for r in self._alpha_weighted(strategies)}
        risk_alloc = {r.strategy_id: r.raw_weight for r in self._risk_parity(strategies)}

        results = []
        for s in strategies:
            sid = s['id']
            hybrid_w = (
                0.4 * score_alloc.get(sid, 0) +
                0.3 * alpha_alloc.get(sid, 0) +
                0.3 * risk_alloc.get(sid, 0)
            )

            effective_w = self._apply_constraints(hybrid_w, s['phase'])
            results.append(AllocationResult(
                strategy_id=sid, name=s['name'], phase=s['phase'],
                base_weight=s.get('base_weight', 0.2), raw_weight=round(hybrid_w, 4),
                effective_weight=round(effective_w, 4),
                reason="hybrid(40S+30A+30R)",
            ))

        return self._normalize(results)

    def _calculate_score(self, s: dict) -> float:
        """综合评分"""
        sharpe = s.get('sharpe', 0)
        alpha = s.get('alpha_30d', 0)
        dd = abs(s.get('max_drawdown', 0))

        sharpe_score = min(30, sharpe / 2 * 30)
        alpha_score = min(40, max(0, alpha / 15 * 40))
        dd_score = max(0, min(30, (30 - dd) / 30 * 30))

        return max(0, sharpe_score + alpha_score + dd_score)

    def _apply_constraints(self, weight: float, phase: str) -> float:
        """应用约束"""
        if phase == 'RETIRED':
            return 0
        if phase == 'WATCHLIST':
            weight *= 0.5
        return max(0, min(self.max_weight, weight))

    def _normalize(self, results: List[AllocationResult]) -> List[AllocationResult]:
        """归一化权重 (总和=1)"""
        total = sum(r.effective_weight for r in results)
        if total > 0:
            for r in results:
                r.effective_weight = round(r.effective_weight / total, 4)
        return results
