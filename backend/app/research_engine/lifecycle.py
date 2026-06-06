"""Strategy Lifecycle - 策略生命周期状态机

状态流转:
    RESEARCH      研究中 (刚创建, 回测阶段)
        ↓
    VALIDATED     已验证 (通过Walk Forward + Alpha验证)
        ↓
    PAPER_TRADING 模拟盘 (PaperBroker运行中)
        ↓
    LIVE          实盘 (QMT实盘交易)

回退:
    PAPER_TRADING → RESEARCH (模拟盘表现不佳)
    LIVE → PAPER_TRADING (实盘异常)

自动晋级规则 (Promotion Rules):
    RESEARCH → VALIDATED:
        - Walk Forward >= 70% consistency
        - Alpha > 5%
        - Sharpe > 0.8
    VALIDATED → PAPER_TRADING:
        - 人工确认
    PAPER_TRADING → LIVE:
        - 模拟盘连续运行 >= 30天
        - 总收益 > 0
        - 最大回撤 < 20%
"""
from typing import Dict, Optional, List
from enum import Enum
from datetime import datetime
import json, os


class StrategyStatus(Enum):
    """策略状态"""
    RESEARCH = "RESEARCH"           # 研究中
    VALIDATED = "VALIDATED"         # 已验证
    PAPER_TRADING = "PAPER_TRADING" # 模拟盘
    LIVE = "LIVE"                   # 实盘


# 合法状态转换
VALID_TRANSITIONS = {
    StrategyStatus.RESEARCH: [StrategyStatus.VALIDATED],
    StrategyStatus.VALIDATED: [StrategyStatus.PAPER_TRADING, StrategyStatus.RESEARCH],
    StrategyStatus.PAPER_TRADING: [StrategyStatus.LIVE, StrategyStatus.RESEARCH],
    StrategyStatus.LIVE: [StrategyStatus.PAPER_TRADING],
}


class StrategyLifecycle:
    """策略生命周期管理"""

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data'
        )
        self._registry_file = os.path.join(self.data_dir, 'strategy_lifecycle.json')
        self.strategies: Dict[str, dict] = {}
        self._load()

    def _load(self):
        if os.path.exists(self._registry_file):
            with open(self._registry_file, 'r', encoding='utf-8') as f:
                self.strategies = json.load(f)

    def _save(self):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self._registry_file, 'w', encoding='utf-8') as f:
            json.dump(self.strategies, f, ensure_ascii=False, indent=2)

    def register(self, strategy_id: str, name: str, strategy_type: str,
                 status: StrategyStatus = StrategyStatus.RESEARCH):
        """注册策略"""
        self.strategies[strategy_id] = {
            "strategy_id": strategy_id,
            "name": name,
            "type": strategy_type,
            "status": status.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "history": [{"status": status.value, "at": datetime.now().isoformat(), "reason": "created"}],
        }
        self._save()

    def transition(self, strategy_id: str, new_status: StrategyStatus,
                   reason: str = "") -> bool:
        """状态转换"""
        if strategy_id not in self.strategies:
            return False

        current = StrategyStatus(self.strategies[strategy_id]["status"])
        if new_status not in VALID_TRANSITIONS.get(current, []):
            print(f"[Lifecycle] Invalid transition: {current.value} -> {new_status.value}")
            return False

        self.strategies[strategy_id]["status"] = new_status.value
        self.strategies[strategy_id]["updated_at"] = datetime.now().isoformat()
        self.strategies[strategy_id]["history"].append({
            "status": new_status.value,
            "at": datetime.now().isoformat(),
            "reason": reason,
        })
        self._save()
        return True

    def get_status(self, strategy_id: str) -> Optional[str]:
        if strategy_id in self.strategies:
            return self.strategies[strategy_id]["status"]
        return None

    def get_strategies_by_status(self, status: StrategyStatus) -> List[dict]:
        return [s for s in self.strategies.values() if s["status"] == status.value]

    def get_all(self) -> List[dict]:
        return list(self.strategies.values())

    def get_summary(self) -> dict:
        """策略状态汇总"""
        all_strategies = list(self.strategies.values())
        return {
            "total": len(all_strategies),
            "RESEARCH": len([s for s in all_strategies if s["status"] == "RESEARCH"]),
            "VALIDATED": len([s for s in all_strategies if s["status"] == "VALIDATED"]),
            "PAPER_TRADING": len([s for s in all_strategies if s["status"] == "PAPER_TRADING"]),
            "LIVE": len([s for s in all_strategies if s["status"] == "LIVE"]),
        }


class PromotionRules:
    """策略晋级规则

    RESEARCH → VALIDATED:
        - Walk Forward consistency >= 70%
        - Alpha > 5%
        - Sharpe > 0.8

    VALIDATED → PAPER_TRADING:
        - 人工确认 (auto_promote=False)

    PAPER_TRADING → LIVE:
        - 模拟盘运行 >= 30天
        - 总收益 > 0
        - 最大回撤 < 20%
    """

    # RESEARCH → VALIDATED 阈值
    MIN_WF_CONSISTENCY = 70.0   # Walk Forward一致性 %
    MIN_ALPHA = 5.0             # 最低Alpha %
    MIN_SHARPE = 0.8            # 最低Sharpe

    # PAPER_TRADING → LIVE 阈值
    MIN_PAPER_DAYS = 30         # 最低模拟盘天数
    MIN_PAPER_RETURN = 0.0      # 最低模拟盘收益 %
    MAX_PAPER_DRAWDOWN = 20.0   # 最大模拟盘回撤 %

    @classmethod
    def check_research_to_validated(cls, walk_forward_consistency: float,
                                     alpha: float, sharpe: float) -> tuple:
        """检查 RESEARCH → VALIDATED

        Returns:
            (can_promote: bool, reasons: list)
        """
        reasons = []
        can_promote = True

        if walk_forward_consistency < cls.MIN_WF_CONSISTENCY:
            can_promote = False
            reasons.append(f"Walk Forward {walk_forward_consistency:.1f}% < {cls.MIN_WF_CONSISTENCY}%")

        if alpha < cls.MIN_ALPHA:
            can_promote = False
            reasons.append(f"Alpha {alpha:.2f}% < {cls.MIN_ALPHA}%")

        if sharpe < cls.MIN_SHARPE:
            can_promote = False
            reasons.append(f"Sharpe {sharpe:.2f} < {cls.MIN_SHARPE}")

        if can_promote:
            reasons.append("All promotion criteria met")

        return can_promote, reasons

    @classmethod
    def check_paper_to_live(cls, paper_days: int, paper_return: float,
                             paper_drawdown: float) -> tuple:
        """检查 PAPER_TRADING → LIVE

        Returns:
            (can_promote: bool, reasons: list)
        """
        reasons = []
        can_promote = True

        if paper_days < cls.MIN_PAPER_DAYS:
            can_promote = False
            reasons.append(f"模拟盘运行 {paper_days}天 < {cls.MIN_PAPER_DAYS}天")

        if paper_return <= cls.MIN_PAPER_RETURN:
            can_promote = False
            reasons.append(f"模拟盘收益 {paper_return:.2f}% <= {cls.MIN_PAPER_RETURN}%")

        if abs(paper_drawdown) > cls.MAX_PAPER_DRAWDOWN:
            can_promote = False
            reasons.append(f"模拟盘回撤 {paper_drawdown:.2f}% > {cls.MAX_PAPER_DRAWDOWN}%")

        if can_promote:
            reasons.append("All promotion criteria met")

        return can_promote, reasons
