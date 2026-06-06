"""Alpha Factory - 策略生命周期管理 2.0

新增三个状态:
    ACTIVE      活跃策略 (正在交易, 分配资金)
    WATCHLIST   观察策略 (Alpha仍在但衰减中, 减少资金)
    RETIRED     退役策略 (Alpha转负, 停止交易)

自动流转:
    每日检查Alpha Decay → 自动更新状态
    ACTIVE → WATCHLIST: Alpha 30d < 60d * 0.7
    WATCHLIST → RETIRED: Alpha 30d < 0
    WATCHLIST → ACTIVE: Alpha 30d > 60d * 0.9 (恢复)
    RETIRED → 不可回退 (需人工确认)

配合资金分配:
    ACTIVE:    100% 目标权重
    WATCHLIST: 50% 目标权重
    RETIRED:   0% (停止交易)
"""
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import json, os


class StrategyPhase(Enum):
    """策略阶段"""
    RESEARCH = "RESEARCH"           # 研究中
    VALIDATED = "VALIDATED"         # 已验证
    PAPER_TRADING = "PAPER_TRADING" # 模拟盘
    ACTIVE = "ACTIVE"               # 活跃交易
    WATCHLIST = "WATCHLIST"         # 观察中
    RETIRED = "RETIRED"             # 已退役


# 自动流转规则
AUTO_TRANSITIONS = {
    StrategyPhase.ACTIVE: [StrategyPhase.WATCHLIST],
    StrategyPhase.WATCHLIST: [StrategyPhase.ACTIVE, StrategyPhase.RETIRED],
    StrategyPhase.RETIRED: [],  # 需人工确认
}

# 资金权重乘数
WEIGHT_MULTIPLIER = {
    StrategyPhase.ACTIVE: 1.0,
    StrategyPhase.WATCHLIST: 0.5,
    StrategyPhase.RETIRED: 0.0,
    StrategyPhase.PAPER_TRADING: 0.0,
    StrategyPhase.VALIDATED: 0.0,
    StrategyPhase.RESEARCH: 0.0,
}


@dataclass
class StrategyState:
    """策略状态"""
    strategy_id: str
    name: str
    cluster: str
    phase: StrategyPhase
    base_weight: float          # 基础权重
    effective_weight: float     # 实际权重 (base * multiplier)
    alpha_30d: float
    alpha_60d: float
    alpha_90d: float
    sharpe: float
    max_drawdown: float
    decay_status: str           # HEALTHY/DEGRADING/DEAD
    days_in_phase: int
    last_transition: str
    transition_reason: str
    updated_at: str


class AlphaFactory:
    """Alpha Factory - 自动策略生命周期管理"""

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'alpha_factory'
        )
        os.makedirs(self.data_dir, exist_ok=True)

        self._state_file = os.path.join(self.data_dir, 'factory_state.json')
        self.strategies: Dict[str, StrategyState] = {}
        self.transition_history: List[dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self._state_file):
            with open(self._state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for sid, s in data.get('strategies', {}).items():
                    s['phase'] = StrategyPhase(s['phase'])
                    self.strategies[sid] = StrategyState(**s)
                self.transition_history = data.get('transitions', [])

    def _save(self):
        data = {
            'strategies': {
                sid: {
                    'strategy_id': s.strategy_id, 'name': s.name, 'cluster': s.cluster,
                    'phase': s.phase.value, 'base_weight': s.base_weight,
                    'effective_weight': s.effective_weight,
                    'alpha_30d': s.alpha_30d, 'alpha_60d': s.alpha_60d, 'alpha_90d': s.alpha_90d,
                    'sharpe': s.sharpe, 'max_drawdown': s.max_drawdown,
                    'decay_status': s.decay_status, 'days_in_phase': s.days_in_phase,
                    'last_transition': s.last_transition, 'transition_reason': s.transition_reason,
                    'updated_at': s.updated_at,
                }
                for sid, s in self.strategies.items()
            },
            'transitions': self.transition_history[-500:],
        }
        with open(self._state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def register_strategy(self, strategy_id: str, name: str, cluster: str,
                          phase: StrategyPhase, base_weight: float,
                          sharpe: float = 0, alpha: float = 0):
        """注册策略"""
        multiplier = WEIGHT_MULTIPLIER.get(phase, 0)
        self.strategies[strategy_id] = StrategyState(
            strategy_id=strategy_id, name=name, cluster=cluster,
            phase=phase, base_weight=base_weight,
            effective_weight=round(base_weight * multiplier, 4),
            alpha_30d=alpha, alpha_60d=alpha, alpha_90d=alpha,
            sharpe=sharpe, max_drawdown=0,
            decay_status="HEALTHY", days_in_phase=0,
            last_transition=datetime.now().isoformat(),
            transition_reason="registered",
            updated_at=datetime.now().isoformat(),
        )
        self._save()

    def update_alpha(self, strategy_id: str, alpha_30d: float,
                     alpha_60d: float, alpha_90d: float,
                     sharpe: float = 0, max_drawdown: float = 0):
        """更新策略Alpha数据"""
        if strategy_id not in self.strategies:
            return

        s = self.strategies[strategy_id]
        s.alpha_30d = alpha_30d
        s.alpha_60d = alpha_60d
        s.alpha_90d = alpha_90d
        s.sharpe = sharpe
        s.max_drawdown = max_drawdown
        s.updated_at = datetime.now().isoformat()

        # 判断decay状态
        if alpha_30d < 0 and alpha_60d < 0:
            s.decay_status = "DEAD"
        elif alpha_30d < alpha_60d < alpha_90d:
            s.decay_status = "DEGRADING"
        elif alpha_30d > alpha_60d:
            s.decay_status = "RECOVERING"
        else:
            s.decay_status = "HEALTHY"

        self._save()

    def auto_transition(self, strategy_id: str) -> Optional[Tuple[StrategyPhase, StrategyPhase]]:
        """自动状态转换

        Returns:
            (old_phase, new_phase) or None if no change
        """
        if strategy_id not in self.strategies:
            return None

        s = self.strategies[strategy_id]
        old_phase = s.phase

        # 只有ACTIVE/WATCHLIST参与自动流转
        if old_phase not in (StrategyPhase.ACTIVE, StrategyPhase.WATCHLIST):
            return None

        new_phase = None
        reason = ""

        if old_phase == StrategyPhase.ACTIVE:
            # ACTIVE → WATCHLIST: Alpha持续下降
            if s.decay_status == "DEGRADING" and s.alpha_30d < s.alpha_60d * 0.7:
                new_phase = StrategyPhase.WATCHLIST
                reason = f"Alpha衰减: 30d={s.alpha_30d:.3f} < 60d*0.7={s.alpha_60d*0.7:.3f}"

        elif old_phase == StrategyPhase.WATCHLIST:
            # WATCHLIST → RETIRED: Alpha转负
            if s.alpha_30d < 0 and s.alpha_60d < 0:
                new_phase = StrategyPhase.RETIRED
                reason = f"Alpha转负: 30d={s.alpha_30d:.3f}, 60d={s.alpha_60d:.3f}"
            # WATCHLIST → ACTIVE: Alpha恢复
            elif s.decay_status in ("HEALTHY", "RECOVERING") and s.alpha_30d > s.alpha_60d * 0.9:
                new_phase = StrategyPhase.ACTIVE
                reason = f"Alpha恢复: 30d={s.alpha_30d:.3f} > 60d*0.9={s.alpha_60d*0.9:.3f}"

        if new_phase and new_phase in AUTO_TRANSITIONS.get(old_phase, []):
            s.phase = new_phase
            s.days_in_phase = 0
            s.last_transition = datetime.now().isoformat()
            s.transition_reason = reason
            s.effective_weight = round(s.base_weight * WEIGHT_MULTIPLIER.get(new_phase, 0), 4)

            self.transition_history.append({
                'strategy_id': strategy_id,
                'name': s.name,
                'from': old_phase.value,
                'to': new_phase.value,
                'reason': reason,
                'at': datetime.now().isoformat(),
            })
            self._save()
            return (old_phase, new_phase)

        # 递增天数
        s.days_in_phase += 1
        self._save()
        return None

    def auto_transition_all(self) -> List[dict]:
        """批量自动流转"""
        results = []
        for sid in self.strategies:
            result = self.auto_transition(sid)
            if result:
                old, new = result
                results.append({
                    'strategy_id': sid,
                    'name': self.strategies[sid].name,
                    'from': old.value,
                    'to': new.value,
                    'reason': self.strategies[sid].transition_reason,
                })
        return results

    def get_allocation(self) -> List[dict]:
        """获取资金分配"""
        allocation = []
        for s in self.strategies.values():
            allocation.append({
                'strategy_id': s.strategy_id,
                'name': s.name,
                'cluster': s.cluster,
                'phase': s.phase.value,
                'base_weight': s.base_weight,
                'effective_weight': s.effective_weight,
                'decay_status': s.decay_status,
                'alpha_30d': s.alpha_30d,
            })
        allocation.sort(key=lambda x: -x['effective_weight'])
        return allocation

    def get_dashboard(self) -> dict:
        """Alpha Dashboard 数据"""
        strategies = list(self.strategies.values())
        active = [s for s in strategies if s.phase == StrategyPhase.ACTIVE]
        watchlist = [s for s in strategies if s.phase == StrategyPhase.WATCHLIST]
        retired = [s for s in strategies if s.phase == StrategyPhase.RETIRED]

        return {
            'timestamp': datetime.now().isoformat(),
            'total_strategies': len(strategies),
            'active': len(active),
            'watchlist': len(watchlist),
            'retired': len(retired),
            'total_effective_weight': round(sum(s.effective_weight for s in strategies), 4),
            'avg_alpha_30d': round(sum(s.alpha_30d for s in strategies) / len(strategies), 3) if strategies else 0,
            'avg_sharpe': round(sum(s.sharpe for s in strategies) / len(strategies), 3) if strategies else 0,
            'strategies': [
                {
                    'id': s.strategy_id, 'name': s.name, 'cluster': s.cluster,
                    'phase': s.phase.value, 'weight': s.effective_weight,
                    'alpha_30d': s.alpha_30d, 'sharpe': s.sharpe,
                    'decay': s.decay_status, 'days': s.days_in_phase,
                }
                for s in sorted(strategies, key=lambda x: -x.effective_weight)
            ],
            'recent_transitions': self.transition_history[-10:],
        }
