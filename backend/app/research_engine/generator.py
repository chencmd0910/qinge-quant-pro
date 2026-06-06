"""Strategy Generator - 自动策略生成器

随机组合因子，自动生成策略变体。

因子池:
    动量类: mom_5d, mom_10d, mom_20d, consistency
    资金类: northbound_net_buy, northbound_holding_chg, margin_balance_chg, money_flow
    行业类: industry_revenue_growth, industry_profit_growth, industry_pmi
    量价类: volume_ratio, turnover_mom
    波动类: volatility_20d, daily_sharpe
    基本面: pe_ttm, pb_ttm

生成逻辑:
    1. 随机选取N个因子 (3-8个)
    2. 随机分配权重 (总和=1.0)
    3. 随机选择持仓数量 (10-30只)
    4. 随机选择调仓频率 (周/双周/月)
    5. 生成唯一策略ID

使用:
    generator = StrategyGenerator(seed=42)
    strategies = generator.generate(count=100)
"""
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
import random
import hashlib
from datetime import datetime


# 因子定义: (名称, 类别, 默认权重范围)
FACTOR_POOL = [
    # 动量类
    ("mom_5d", "动量", (0.05, 0.25)),
    ("mom_10d", "动量", (0.05, 0.20)),
    ("mom_20d", "动量", (0.05, 0.15)),
    ("consistency", "动量", (0.03, 0.12)),

    # 资金类
    ("northbound_net_buy", "北向资金", (0.08, 0.25)),
    ("northbound_holding_chg", "北向资金", (0.05, 0.20)),
    ("margin_balance_chg", "融资余额", (0.05, 0.18)),
    ("margin_buy_ratio", "融资余额", (0.04, 0.15)),
    ("money_flow", "资金流", (0.06, 0.20)),

    # 行业类
    ("industry_revenue_growth", "行业景气", (0.05, 0.18)),
    ("industry_profit_growth", "行业景气", (0.05, 0.15)),
    ("industry_pmi", "行业景气", (0.03, 0.10)),

    # 量价类
    ("volume_ratio", "量价", (0.05, 0.20)),
    ("turnover_mom", "量价", (0.03, 0.12)),

    # 波动类
    ("volatility_20d", "波动率", (0.03, 0.12)),
    ("daily_sharpe", "波动率", (0.04, 0.15)),

    # 基本面
    ("pe_ttm", "基本面", (0.02, 0.10)),
    ("pb_ttm", "基本面", (0.02, 0.08)),
]

# 调仓频率
REBALANCE_FREQ = ["weekly", "biweekly", "monthly"]
REBALANCE_MAP = {"weekly": 5, "biweekly": 10, "monthly": 20}


@dataclass
class GeneratedStrategy:
    """生成的策略"""
    strategy_id: str
    name: str
    factors: List[Tuple[str, float]]  # [(factor_name, weight), ...]
    top_n: int                        # 持仓数量
    rebalance_freq: str               # 调仓频率
    rebalance_days: int               # 调仓天数
    factor_categories: List[str]      # 涉及的因子类别
    generation: int                   # 第几代


class StrategyGenerator:
    """策略生成器"""

    def __init__(self, seed: int = None):
        self.rng = random.Random(seed)
        self.factor_pool = FACTOR_POOL
        self._counter = 0

    def _generate_id(self, factors: list, top_n: int, freq: str) -> str:
        """生成唯一策略ID"""
        self._counter += 1
        content = f"{factors}{top_n}{freq}{self._counter}{datetime.now().isoformat()}"
        hash_val = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"AUTO_{self._counter:04d}_{hash_val}"

    def _select_factors(self, min_factors: int = 3, max_factors: int = 8) -> List[Tuple[str, str, Tuple[float, float]]]:
        """随机选取因子"""
        count = self.rng.randint(min_factors, max_factors)
        # 确保至少覆盖3个类别
        categories = list(set(f[1] for f in self.factor_pool))
        self.rng.shuffle(categories)

        selected = []
        # 先从每个类别选一个
        for cat in categories[:min(count, len(categories))]:
            cat_factors = [f for f in self.factor_pool if f[1] == cat]
            if cat_factors:
                selected.append(self.rng.choice(cat_factors))

        # 再随机补充
        remaining = [f for f in self.factor_pool if f not in selected]
        while len(selected) < count and remaining:
            f = self.rng.choice(remaining)
            selected.append(f)
            remaining.remove(f)

        return selected

    def _assign_weights(self, factors: list) -> List[float]:
        """随机分配权重 (总和=1.0)"""
        raw_weights = []
        for f in factors:
            name, cat, (w_min, w_max) = f
            raw_weights.append(self.rng.uniform(w_min, w_max))

        total = sum(raw_weights)
        if total > 0:
            weights = [w / total for w in raw_weights]
        else:
            weights = [1.0 / len(factors)] * len(factors)

        return [round(w, 4) for w in weights]

    def generate_one(self, generation: int = 0) -> GeneratedStrategy:
        """生成一个策略"""
        # 1. 选因子
        factors = self._select_factors()

        # 2. 分配权重
        weights = self._assign_weights(factors)

        # 3. 选持仓数
        top_n = self.rng.choice([10, 15, 20, 25, 30])

        # 4. 选调仓频率
        freq = self.rng.choice(REBALANCE_FREQ)

        # 5. 生成ID
        factor_names = [(f[0], w) for f, w in zip(factors, weights)]
        strategy_id = self._generate_id(factor_names, top_n, freq)

        # 6. 因子类别
        categories = list(set(f[1] for f in factors))

        name = f"Gen{generation}_{categories[0]}_{len(factors)}F_{freq}"

        return GeneratedStrategy(
            strategy_id=strategy_id,
            name=name,
            factors=factor_names,
            top_n=top_n,
            rebalance_freq=freq,
            rebalance_days=REBALANCE_MAP[freq],
            factor_categories=categories,
            generation=generation,
        )

    def generate(self, count: int = 100, generation: int = 0) -> List[GeneratedStrategy]:
        """批量生成策略"""
        strategies = []
        for _ in range(count):
            strategies.append(self.generate_one(generation))
        return strategies

    def generate_diverse(self, count: int = 100) -> List[GeneratedStrategy]:
        """生成多样化策略 (确保覆盖所有因子类别)"""
        strategies = []
        categories = list(set(f[1] for f in self.factor_pool))

        # 每个类别至少生成一个纯策略
        for cat in categories:
            cat_factors = [f for f in self.factor_pool if f[1] == cat]
            if len(cat_factors) >= 2:
                selected = self.rng.sample(cat_factors, min(3, len(cat_factors)))
                weights = self._assign_weights(selected)
                factor_names = [(f[0], w) for f, w in zip(selected, weights)]
                top_n = self.rng.choice([10, 20])
                freq = self.rng.choice(REBALANCE_FREQ)
                sid = self._generate_id(factor_names, top_n, freq)
                strategies.append(GeneratedStrategy(
                    strategy_id=sid, name=f"Pure_{cat}_Gen0",
                    factors=factor_names, top_n=top_n,
                    rebalance_freq=freq, rebalance_days=REBALANCE_MAP[freq],
                    factor_categories=[cat], generation=0,
                ))

        # 剩余随机生成
        remaining = count - len(strategies)
        strategies.extend(self.generate(remaining, generation=0))

        return strategies[:count]
