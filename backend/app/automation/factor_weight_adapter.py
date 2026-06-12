"""
青鳄量化 - 因子权重自动适配器

根据FactorICMonitor的实时IC数据，自动调整策略中因子的权重。
对标机构实践：IC衰减 → 降权，IC恢复 → 升权，平滑调权避免冲击。

核心逻辑:
  HEALTHY → 保留100%权重
  WATCH   → 保留80%权重
  WARNING → 保留50%权重
  DEAD    → 保留20%权重（保留火种等待复苏）

释放的权重按IC_IR成比例重新分配给HEALTHY/WATCH因子。

用法:
    adapter = FactorWeightAdapter()
    new_weights = adapter.adapt(ic_report, strategy_factors)
    strategy = MultiFactorV25(custom_weights=new_weights)
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging
import json
from datetime import datetime

ROOT = Path("/app") if Path("/app").exists() else Path(__file__).resolve().parent.parent.parent
logger = logging.getLogger("FactorWeightAdapter")


# ==============================
# 数据结构
# ==============================

@dataclass
class WeightChange:
    """权重变更记录"""
    factor_name: str
    old_weight: float
    new_weight: float
    ic_ir: float
    health: str
    reason: str


@dataclass
class WeightAdaptation:
    """权重适配结果"""
    timestamp: str
    ic_date_range: str
    new_weights: Dict[str, float]     # {factor_name: new_weight}
    changes: List[WeightChange]
    total_weight_before: float
    total_weight_after: float
    freed_weight: float               # 释放的权重
    summary: str = ""

    def to_json(self) -> str:
        return json.dumps({
            "timestamp": self.timestamp,
            "ic_date_range": self.ic_date_range,
            "new_weights": {k: round(v, 4) for k, v in self.new_weights.items()},
            "changes": [
                {"factor": c.factor_name, "old": round(c.old_weight, 4),
                 "new": round(c.new_weight, 4), "ic_ir": round(c.ic_ir, 4),
                 "health": c.health, "reason": c.reason}
                for c in self.changes
            ],
            "freed_weight": round(self.freed_weight, 4),
        }, ensure_ascii=False, indent=2)


# ==============================
# 因子权重适配器
# ==============================

class FactorWeightAdapter:
    """根据IC监控结果自动调整因子权重

    对标专业机构:
      - 不一次性砍光权重（avoid whipsaw）
      - 平滑阶梯降权（stepped haircut）
      - 根据IC_IR重新分配（risk-budget redistribution）
      - 冷因子保留火种（keep embers for recovery）

    配置:
      HEALTHY_SCALE: HEALTHY因子权重倍率 (1.0 = 不动)
      WATCH_SCALE:   WATCH因子权重倍率
      WARNING_SCALE: WARNING因子权重倍率
      DEAD_SCALE:    DEAD因子权重倍率 (>0 = 保留火种)
      MAX_SINGLE_CHANGE: 单因子最大变动率（防止突变）
      SMOOTHING:     平滑系数(0-1), 新旧权重混合
    """

    # 权重倍率
    HEALTHY_SCALE = 1.0    # 健康因子全权重
    WATCH_SCALE = 0.80     # 观察因子打8折
    WARNING_SCALE = 0.50   # 警告因子打5折
    DEAD_SCALE = 0.20      # 失效因子打2折（保留火种）

    # 稳定约束
    MAX_SINGLE_CHANGE = 0.50  # 单因子权重最多砍50%
    SMOOTHING = 0.7            # 新旧权重各占比例 (0=全信IC, 1=不动)
    MIN_WEIGHT = 0.005         # 最低权重0.5%（低于此归零）

    def __init__(self, smoothing: float = None, dead_scale: float = None):
        if smoothing is not None:
            self.SMOOTHING = max(0, min(1, smoothing))
        if dead_scale is not None:
            self.DEAD_SCALE = max(0, min(1, dead_scale))

    def adapt(self,
             ic_factors: List[dict],      # [{factor_name, health, ic_ir, ...}]
             current_weights: Dict[str, float],  # {factor_name: weight}
             weight_history: Dict[str, float] = None  # 上期权重(平滑用)
             ) -> WeightAdaptation:
        """根据IC数据调整因子权重

        Args:
            ic_factors: IC监控结果列表
            current_weights: 当前策略因子权重
            weight_history: 上期已调权重（用于平滑，避免跳变）

        Returns:
            WeightAdaptation 包含新权重和变更记录
        """
        # 1. 构建IC健康映射
        ic_map: Dict[str, dict] = {}
        for f in ic_factors:
            ic_map[f.get("factor_name", f.get("name", ""))] = f

        # 2. 计算缩放倍率
        scales = {}
        health_map = {}
        for name, weight in current_weights.items():
            if name not in ic_map:
                # 不在IC监控范围内的因子，保持原权重
                scales[name] = 1.0
                health_map[name] = "UNMONITORED"
                continue

            health = ic_map[name].get("health", "WATCH")
            ic_ir = ic_map[name].get("ic_ir", 0)
            health_map[name] = health

            if health == "HEALTHY":
                scales[name] = self.HEALTHY_SCALE
            elif health == "WATCH":
                scales[name] = self.WATCH_SCALE
            elif health == "WARNING":
                scales[name] = self.WARNING_SCALE
            elif health == "DEAD":
                scales[name] = self.DEAD_SCALE
            else:
                scales[name] = self.WATCH_SCALE

        # 3. 计算新权重（按健康度缩放）
        raw_new = {}
        for name, weight in current_weights.items():
            scale = scales.get(name, 1.0)
            adjusted = weight * scale

            # 限制单次最大变动
            if weight_history and name in weight_history:
                old_adjusted = weight_history[name]
                max_delta = weight * self.MAX_SINGLE_CHANGE
                if abs(adjusted - old_adjusted) > max_delta:
                    direction = 1 if adjusted > old_adjusted else -1
                    adjusted = old_adjusted + direction * max_delta

            raw_new[name] = adjusted

        # 4. 计算释放的权重
        total_old = sum(current_weights.values())
        total_scaled = sum(raw_new.values())
        freed_weight = total_old - total_scaled

        # 5. 红利用于给非DEAD因子加权
        if freed_weight > 0.0001:
            # 按IC_IR成比例分配给HEALTHY+WATCH因子
            bonus_pool = freed_weight
            bonus_candidates = {}

            for name in current_weights:
                if ic_map.get(name, {}).get("health") in ("HEALTHY", "WATCH"):
                    ic_ir = ic_map[name].get("ic_ir", 0.01)
                    bonus_candidates[name] = max(ic_ir, 0.01)  # 兜底

            if bonus_candidates:
                total_ir = sum(bonus_candidates.values())
                for name, ir in bonus_candidates.items():
                    bonus = bonus_pool * (ir / total_ir)
                    raw_new[name] += bonus

        # 6. 归一化
        total_new = sum(raw_new.values())
        if total_new > 0:
            new_weights = {k: v / total_new * total_old for k, v in raw_new.items()}
        else:
            new_weights = current_weights.copy()

        # 7. 剔除低于最低阈值的
        new_weights = {k: v for k, v in new_weights.items() if v >= self.MIN_WEIGHT}
        total_after = sum(new_weights.values())
        if total_after > 0:
            new_weights = {k: v / total_after * total_old for k, v in new_weights.items()}

        # 8. 平滑（与历史混合）
        if weight_history:
            smoothed = {}
            for name in new_weights:
                prev = weight_history.get(name, new_weights[name])
                smoothed[name] = self.SMOOTHING * prev + (1 - self.SMOOTHING) * new_weights[name]
            new_weights = smoothed
            # 再归一化
            total_s = sum(new_weights.values())
            if total_s > 0:
                new_weights = {k: v / total_s * total_old for k, v in new_weights.items()}

        # 9. 生成变更记录
        changes = []
        for name, new_w in new_weights.items():
            old_w = current_weights.get(name, 0)
            if abs(new_w - old_w) > 0.0001:
                ic = ic_map.get(name, {})
                changes.append(WeightChange(
                    factor_name=name,
                    old_weight=old_w,
                    new_weight=new_w,
                    ic_ir=ic.get("ic_ir", 0),
                    health=health_map.get(name, "UNKNOWN"),
                    reason=self._describe_change(name, old_w, new_w, health_map.get(name, "UNKNOWN")),
                ))

        # 10. 构建报告
        adaptation = WeightAdaptation(
            timestamp=datetime.now().isoformat(),
            ic_date_range="",
            new_weights=new_weights,
            changes=changes,
            total_weight_before=total_old,
            total_weight_after=sum(new_weights.values()),
            freed_weight=freed_weight,
        )

        # 生成摘要
        deactivated = [c for c in changes if c.health == "DEAD" and c.new_weight < c.old_weight * 0.5]
        warnings = [c for c in changes if c.health == "WARNING" and c.new_weight < c.old_weight]
        upgraded = [c for c in changes if c.new_weight > c.old_weight * 1.05]

        lines = [f"权重适配: {len(changes)}项变更 | 释放{freed_weight:.3f}"]
        if deactivated:
            lines.append(f"  大幅降权: {', '.join(c.factor_name for c in deactivated)}")
        if warnings:
            lines.append(f"  警告降权: {', '.join(c.factor_name for c in warnings)}")
        if upgraded:
            lines.append(f"  红利加权: {', '.join(c.factor_name for c in upgraded)}")
        adaptation.summary = "\n".join(lines)

        logger.info(adaptation.summary)
        return adaptation

    def _describe_change(self, name: str, old: float, new: float, health: str) -> str:
        """生成变更说明"""
        direction = "↑" if new > old else "↓"
        pct = abs(new - old) / old * 100 if old > 0 else 100

        if health == "DEAD" and pct > 30:
            return f"IC失效，大幅降权{old:.3f}→{new:.3f} ({pct:.0f}%)"
        elif health == "WARNING":
            return f"IC走弱，降权{old:.3f}→{new:.3f} ({pct:.0f}%)"
        elif direction == "↑":
            return f"IC稳定，红利加权{old:.3f}→{new:.3f} (+{pct:.0f}%)"
        else:
            return f"调整{old:.3f}→{new:.3f} ({pct:.0f}%)"


# ==============================
# 与策略的桥接
# ==============================

def apply_to_strategy(adaptation: WeightAdaptation,
                     strategy_config_path: str = None) -> Dict[str, float]:
    """将适配后的权重应用到策略

    可以直接作为 MultiFactorV25(custom_weights=result) 的参数。

    Args:
        adaptation: 权重适配结果
        strategy_config_path: 可选，保存权重到JSON文件

    Returns:
        可直接传给策略构造函数的custom_weights字典
    """
    return {k: round(v, 4) for k, v in adaptation.new_weights.items()}


# ==============================
# 测试入口
# ==============================

if __name__ == "__main__":
    print("=" * 60)
    print("因子权重适配器 - 验证测试")
    print()

    # 模拟当前策略权重
    current_weights = {
        "mom_5d": 0.06,
        "mom_10d": 0.05,
        "consistency": 0.04,
        "volume_ratio": 0.08,
        "money_flow": 0.07,
        "volatility_20d": 0.05,
        "daily_sharpe": 0.05,
        # 非IC监控因子
        "northbound_net_buy": 0.10,
        "northbound_holding_chg": 0.10,
        "margin_balance_chg": 0.08,
        "margin_buy_ratio": 0.07,
        "industry_revenue_growth": 0.08,
        "industry_profit_growth": 0.07,
        "industry_pmi": 0.05,
        "pe_ttm": 0.03,
        "pb_ttm": 0.02,
    }

    # 模拟IC监控结果（来自之前测试的真实数据）
    ic_factors = [
        {"factor_name": "consistency", "health": "HEALTHY", "ic_ir": 0.507},
        {"factor_name": "turnover_mom", "health": "HEALTHY", "ic_ir": 0.169},
        {"factor_name": "mom_20d", "health": "WATCH", "ic_ir": 0.343},
        {"factor_name": "daily_sharpe", "health": "WATCH", "ic_ir": 0.337},
        {"factor_name": "rsi_14", "health": "WATCH", "ic_ir": 0.289},
        {"factor_name": "volatility_20d", "health": "WATCH", "ic_ir": 0.282},
        {"factor_name": "mom_10d", "health": "WATCH", "ic_ir": 0.247},
        {"factor_name": "boll_pos", "health": "WATCH", "ic_ir": 0.239},
        {"factor_name": "money_flow", "health": "WATCH", "ic_ir": 0.127},
        {"factor_name": "mom_5d", "health": "DEAD", "ic_ir": 0.010},
        {"factor_name": "volume_ratio", "health": "DEAD", "ic_ir": -0.071},
        {"factor_name": "price_accel", "health": "DEAD", "ic_ir": -0.472},
    ]

    # 构建适配器
    adapter = FactorWeightAdapter()

    # 执行适配
    adaptation = adapter.adapt(ic_factors, current_weights)

    print(adaptation.summary)
    print()
    print(f"总权重: {adaptation.total_weight_before:.1%} → {adaptation.total_weight_after:.1%}")
    print(f"释放权重: {adaptation.freed_weight:.3f}")
    print()

    print("变更明细:")
    for c in sorted(adaptation.changes, key=lambda x: x.new_weight, reverse=True):
        direction = "↑" if c.new_weight > c.old_weight else "↓"
        print(f"  {c.factor_name:25s} {c.health:10s} "
              f"{c.old_weight:.3f}→{c.new_weight:.3f} {direction} "
              f"[IC_IR={c.ic_ir:+.3f}] {c.reason}")

    print()
    print("新权重(可直接传入MultiFactorV25):")
    print(json.dumps({k: round(v, 4) for k, v in sorted(
        adaptation.new_weights.items(), key=lambda x: x[1], reverse=True
    )}, indent=2))

    print()
    print("=" * 60)
