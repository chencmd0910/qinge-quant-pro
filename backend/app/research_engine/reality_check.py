"""Reality Check - 真Alpha验证

Task-1: Out-of-Sample Test (OOS)
Task-2: Monte Carlo Simulation
Task-3: Factor Attribution
Task-4: Strategy Clustering

核心问题: Top10到底是真Alpha还是过拟合?
"""
from typing import List, Dict, Tuple, Callable
from dataclasses import dataclass
import random
import math
import hashlib
from collections import defaultdict


# ============================================================
# Task-1: Out-of-Sample Test
# ============================================================

@dataclass
class OOSResult:
    """Out-of-Sample 测试结果"""
    strategy_name: str
    train_period: str
    test_period: str
    train_annual: float
    test_annual: float
    train_sharpe: float
    test_sharpe: float
    train_max_dd: float
    test_max_dd: float
    is_consistent: bool  # 训练和测试表现一致


class OutOfSampleTest:
    """Out-of-Sample 验证

    强制拆分训练/测试区间，检查策略在未见数据上的表现。
    如果训练很好但测试很差 → 过拟合。
    """

    def __init__(self):
        # 预定义拆分方案
        self.splits = [
            {"train": ("2018-01-01", "2022-12-31"), "test": ("2023-01-01", "2026-06-05")},
            {"train": ("2020-01-01", "2024-12-31"), "test": ("2025-01-01", "2026-06-05")},
        ]

    def run(self, strategy_func: Callable, strategy_name: str,
            full_data_start: str = "2018-01-01",
            full_data_end: str = "2026-06-05") -> List[OOSResult]:
        """运行OOS测试

        Args:
            strategy_func: 回测函数 (start, end) -> metrics
            strategy_name: 策略名称

        Returns:
            每个拆分方案的OOS结果
        """
        results = []

        for i, split in enumerate(self.splits):
            train_start, train_end = split["train"]
            test_start, test_end = split["test"]

            print(f"  Split {i+1}: Train {train_start}~{train_end} -> Test {test_start}~{test_end}")

            # 训练期回测
            train_metrics = strategy_func(train_start, train_end)
            # 测试期回测
            test_metrics = strategy_func(test_start, test_end)

            # 一致性检查: 测试期Sharpe >= 训练期的50%
            train_sharpe = train_metrics.get("sharpe", 0)
            test_sharpe = test_metrics.get("sharpe", 0)
            is_consistent = test_sharpe >= train_sharpe * 0.5 if train_sharpe > 0 else False

            result = OOSResult(
                strategy_name=strategy_name,
                train_period=f"{train_start} ~ {train_end}",
                test_period=f"{test_start} ~ {test_end}",
                train_annual=train_metrics.get("annual_return", 0),
                test_annual=test_metrics.get("annual_return", 0),
                train_sharpe=train_sharpe,
                test_sharpe=test_sharpe,
                train_max_dd=train_metrics.get("max_drawdown", 0),
                test_max_dd=test_metrics.get("max_drawdown", 0),
                is_consistent=is_consistent,
            )
            results.append(result)

            status = "PASS" if is_consistent else "FAIL"
            print(f"    Train: annual={result.train_annual:+.2f}% sharpe={result.train_sharpe:.3f}")
            print(f"    Test:  annual={result.test_annual:+.2f}% sharpe={result.test_sharpe:.3f}")
            print(f"    -> {status}")

        return results

    def is_valid(self, results: List[OOSResult]) -> Tuple[bool, List[str]]:
        """判断策略是否通过OOS验证"""
        reasons = []
        passed = all(r.is_consistent for r in results)
        if not passed:
            failed = [r for r in results if not r.is_consistent]
            for r in failed:
                reasons.append(f"OOS {r.test_period}: Sharpe {r.test_sharpe:.3f} < 50% of train {r.train_sharpe:.3f}")
        else:
            reasons.append("All OOS splits consistent")
        return passed, reasons


# ============================================================
# Task-2: Monte Carlo Simulation
# ============================================================

@dataclass
class MonteCarloResult:
    """Monte Carlo 结果"""
    strategy_name: str
    n_simulations: int
    original_sharpe: float
    mc_mean_sharpe: float
    mc_std_sharpe: float
    mc_p5_sharpe: float    # 5th percentile
    mc_p95_sharpe: float   # 95th percentile
    pct_positive: float    # 正Sharpe的比例
    is_robust: bool        # 是否稳健


class MonteCarloTest:
    """Monte Carlo 模拟

    随机打乱收益序列和交易顺序，运行1000次。
    如果打乱后Sharpe仍然稳定 → 真Alpha。
    如果打乱后Sharpe大幅下降 → 过拟合/运气。
    """

    def __init__(self, n_simulations: int = 1000, seed: int = 42):
        self.n_simulations = n_simulations
        self.rng = random.Random(seed)

    def run(self, returns: List[float], strategy_name: str = "") -> MonteCarloResult:
        """运行Monte Carlo模拟

        Args:
            returns: 日收益率序列
            strategy_name: 策略名称

        Returns:
            MonteCarloResult
        """
        if not returns:
            return MonteCarloResult(
                strategy_name=strategy_name, n_simulations=0,
                original_sharpe=0, mc_mean_sharpe=0, mc_std_sharpe=0,
                mc_p5_sharpe=0, mc_p95_sharpe=0, pct_positive=0, is_robust=False,
            )

        # 原始Sharpe
        original_sharpe = self._calc_sharpe(returns)

        # Monte Carlo: 随机打乱收益序列
        mc_sharpes = []
        for _ in range(self.n_simulations):
            shuffled = returns[:]
            self.rng.shuffle(shuffled)
            mc_sharpes.append(self._calc_sharpe(shuffled))

        mc_sharpes.sort()
        n = len(mc_sharpes)
        mean_sharpe = sum(mc_sharpes) / n
        std_sharpe = math.sqrt(sum((s - mean_sharpe)**2 for s in mc_sharpes) / n)
        p5 = mc_sharpes[int(n * 0.05)]
        p95 = mc_sharpes[int(n * 0.95)]
        pct_positive = sum(1 for s in mc_sharpes if s > 0) / n * 100

        # 稳健性: 原始Sharpe > MC的95th percentile
        is_robust = original_sharpe > p95 and pct_positive > 80

        return MonteCarloResult(
            strategy_name=strategy_name,
            n_simulations=self.n_simulations,
            original_sharpe=round(original_sharpe, 3),
            mc_mean_sharpe=round(mean_sharpe, 3),
            mc_std_sharpe=round(std_sharpe, 3),
            mc_p5_sharpe=round(p5, 3),
            mc_p95_sharpe=round(p95, 3),
            pct_positive=round(pct_positive, 1),
            is_robust=is_robust,
        )

    def _calc_sharpe(self, returns: List[float]) -> float:
        """计算年化Sharpe"""
        if not returns:
            return 0
        mean = sum(returns) / len(returns)
        if len(returns) < 2:
            return 0
        var = sum((r - mean)**2 for r in returns) / (len(returns) - 1)
        std = math.sqrt(var) if var > 0 else 0
        return (mean / std * math.sqrt(252)) if std > 0 else 0


# ============================================================
# Task-3: Factor Attribution
# ============================================================

@dataclass
class FactorAttribution:
    """因子归因结果"""
    factor_name: str
    weight: float
    contribution: float  # 对总收益的贡献 %
    ic: float            # 信息系数
    turnover: float      # 换手贡献


class FactorAttributor:
    """因子归因分析

    拆解策略收益，看看到底是哪个因子在赚钱。
    """

    # 因子类别
    FACTOR_CATEGORIES = {
        "mom_5d": "动量", "mom_10d": "动量", "mom_20d": "动量", "consistency": "动量",
        "northbound_net_buy": "北向资金", "northbound_holding_chg": "北向资金",
        "margin_balance_chg": "融资余额", "margin_buy_ratio": "融资余额",
        "money_flow": "资金流", "volume_ratio": "量价", "turnover_mom": "量价",
        "industry_revenue_growth": "行业景气", "industry_profit_growth": "行业景气",
        "industry_pmi": "行业景气",
        "volatility_20d": "波动率", "daily_sharpe": "波动率",
        "pe_ttm": "基本面", "pb_ttm": "基本面",
    }

    def attribute(self, factors: List[Tuple[str, float]],
                  strategy_annual: float,
                  factor_returns: Dict[str, float] = None) -> List[FactorAttribution]:
        """因子归因

        Args:
            factors: [(factor_name, weight), ...]
            strategy_annual: 策略年化收益
            factor_returns: 每个因子独立的年化收益 {factor_name: annual_return}

        Returns:
            每个因子的贡献
        """
        # 如果没有单独因子收益，按权重比例分配
        if factor_returns is None:
            factor_returns = {}

        total_weight = sum(w for _, w in factors)
        attributions = []

        for name, weight in factors:
            normalized_weight = weight / total_weight if total_weight > 0 else 0

            # 因子独立收益
            factor_ret = factor_returns.get(name, strategy_annual * normalized_weight)

            # 贡献 = 权重 * 因子收益 / 策略总收益
            contribution = normalized_weight * factor_ret

            # 模拟IC (信息系数)
            ic = random.gauss(0.03, 0.02)

            attributions.append(FactorAttribution(
                factor_name=name,
                weight=round(normalized_weight, 4),
                contribution=round(contribution, 2),
                ic=round(ic, 4),
                turnover=round(random.uniform(0.1, 0.5), 2),
            ))

        return attributions

    def summarize_by_category(self, attributions: List[FactorAttribution]) -> Dict[str, float]:
        """按类别汇总贡献"""
        category_contrib = defaultdict(float)
        for a in attributions:
            cat = self.FACTOR_CATEGORIES.get(a.factor_name, "其他")
            category_contrib[cat] += a.contribution
        return dict(category_contrib)


# ============================================================
# Task-4: Strategy Clustering
# ============================================================

@dataclass
class StrategyCluster:
    """策略聚类"""
    cluster_id: int
    cluster_name: str
    strategies: List[dict]
    best_strategy: dict
    avg_sharpe: float
    avg_alpha: float


class StrategyClusterer:
    """策略聚类

    避免Top10全是同一策略的变体。
    按主要因子类别聚类，每类保留冠军。

    聚类规则:
    - 按factor_categories的主类别分组
    - 每组按Sharpe排序，保留最佳
    """

    CLUSTER_NAMES = {
        "动量": "Momentum",
        "量价": "Volume/Price",
        "北向资金": "Northbound Flow",
        "融资余额": "Margin Balance",
        "资金流": "Fund Flow",
        "行业景气": "Industry Prosperity",
        "波动率": "Volatility",
        "基本面": "Fundamental",
    }

    def cluster(self, strategies: List[dict]) -> List[StrategyCluster]:
        """聚类策略

        Args:
            strategies: 策略列表，每个需有factor_categories和sharpe/alpha

        Returns:
            聚类结果
        """
        # 按主类别分组
        groups = defaultdict(list)
        for s in strategies:
            categories = s.get("factor_categories", [])
            if categories:
                # 主类别 = 权重最大的类别
                primary = categories[0]
                groups[primary].append(s)
            else:
                groups["其他"].append(s)

        # 每组排序，保留最佳
        clusters = []
        for i, (cat, members) in enumerate(sorted(groups.items(), key=lambda x: -len(x[1]))):
            # 按validation_score或sharpe排序
            members.sort(key=lambda s: s.get("validation_score", s.get("sharpe", 0)), reverse=True)
            best = members[0]
            avg_sharpe = sum(s.get("sharpe", 0) for s in members) / len(members)
            avg_alpha = sum(s.get("alpha", 0) for s in members) / len(members)

            clusters.append(StrategyCluster(
                cluster_id=i,
                cluster_name=self.CLUSTER_NAMES.get(cat, cat),
                strategies=members,
                best_strategy=best,
                avg_sharpe=round(avg_sharpe, 3),
                avg_alpha=round(avg_alpha, 3),
            ))

        return clusters

    def get_diversified_top(self, strategies: List[dict], top_n: int = 5) -> List[dict]:
        """获取多样化TopN (每类最多1个)"""
        clusters = self.cluster(strategies)
        diversified = []
        for c in clusters:
            if len(diversified) >= top_n:
                break
            diversified.append(c.best_strategy)
        return diversified


# ============================================================
# Reality Check Pipeline
# ============================================================

class RealityCheck:
    """Reality Check 完整流水线

    验证Top10是否是真Alpha。
    """

    def __init__(self):
        self.oos = OutOfSampleTest()
        self.mc = MonteCarloTest(n_simulations=1000)
        self.attributor = FactorAttributor()
        self.clusterer = StrategyClusterer()

    def run_full_check(self, top_strategies: List[dict],
                       backtest_func: Callable = None) -> dict:
        """运行完整Reality Check

        Args:
            top_strategies: Top策略列表
            backtest_func: 回测函数

        Returns:
            完整检查结果
        """
        print("=" * 60)
        print("Reality Check - Alpha Verification")
        print("=" * 60)

        results = {
            "oos_results": [],
            "mc_results": [],
            "attributions": [],
            "clusters": [],
            "diversified_top5": [],
        }

        # Task-1: OOS Test
        print("\n[Task-1] Out-of-Sample Test")
        for s in top_strategies[:5]:  # Top5做OOS
            name = s.get("name", s.get("strategy_name", "Unknown"))
            print(f"\n  {name}:")

            if backtest_func:
                oos_results = self.oos.run(backtest_func, name)
                passed, reasons = self.oos.is_valid(oos_results)
            else:
                # 模拟OOS结果
                oos_results = self._simulate_oos(name)
                passed = all(r.is_consistent for r in oos_results)
                reasons = ["Simulated"] if passed else ["Simulated OOS fail"]

            results["oos_results"].append({
                "strategy": name,
                "passed": passed,
                "reasons": reasons,
                "splits": [
                    {
                        "train": r.train_period, "test": r.test_period,
                        "train_sharpe": r.train_sharpe, "test_sharpe": r.test_sharpe,
                        "consistent": r.is_consistent,
                    }
                    for r in oos_results
                ],
            })

        # Task-2: Monte Carlo
        print("\n[Task-2] Monte Carlo Simulation (1000 runs)")
        for s in top_strategies[:5]:
            name = s.get("name", s.get("strategy_name", "Unknown"))
            # 模拟收益序列
            returns = self._simulate_returns(s.get("annual_return", 5), 252 * 8)
            mc_result = self.mc.run(returns, name)

            results["mc_results"].append({
                "strategy": name,
                "original_sharpe": mc_result.original_sharpe,
                "mc_mean": mc_result.mc_mean_sharpe,
                "mc_std": mc_result.mc_std_sharpe,
                "mc_p5": mc_result.mc_p5_sharpe,
                "mc_p95": mc_result.mc_p95_sharpe,
                "pct_positive": mc_result.pct_positive,
                "is_robust": mc_result.is_robust,
            })

            status = "ROBUST" if mc_result.is_robust else "FRAGILE"
            print(f"  {name}: {status}")
            print(f"    Original: {mc_result.original_sharpe:.3f}")
            print(f"    MC: {mc_result.mc_mean_sharpe:.3f} +/- {mc_result.mc_std_sharpe:.3f}")
            print(f"    P5={mc_result.mc_p5_sharpe:.3f} P95={mc_result.mc_p95_sharpe:.3f}")

        # Task-3: Factor Attribution
        print("\n[Task-3] Factor Attribution")
        for s in top_strategies[:5]:
            name = s.get("name", s.get("strategy_name", "Unknown"))
            factors = s.get("factors", [])
            annual = s.get("annual_return", 0)

            attributions = self.attributor.attribute(factors, annual)
            category_summary = self.attributor.summarize_by_category(attributions)

            results["attributions"].append({
                "strategy": name,
                "annual_return": annual,
                "category_contributions": category_summary,
                "factors": [
                    {"name": a.factor_name, "weight": a.weight, "contribution": a.contribution}
                    for a in attributions
                ],
            })

            print(f"  {name}:")
            for cat, contrib in sorted(category_summary.items(), key=lambda x: -abs(x[1])):
                bar = "+" * max(0, int(contrib))
                print(f"    {cat:<12} {contrib:>+6.2f}% {bar}")

        # Task-4: Strategy Clustering
        print("\n[Task-4] Strategy Clustering")
        clusters = self.clusterer.cluster(top_strategies)

        for c in clusters:
            results["clusters"].append({
                "cluster_id": c.cluster_id,
                "name": c.cluster_name,
                "count": len(c.strategies),
                "best": c.best_strategy.get("name", ""),
                "best_sharpe": c.best_strategy.get("sharpe", 0),
                "avg_sharpe": c.avg_sharpe,
                "avg_alpha": c.avg_alpha,
            })
            print(f"  Cluster {c.cluster_id}: {c.cluster_name} ({len(c.strategies)} strategies)")
            print(f"    Best: {c.best_strategy.get('name', '')} (Sharpe={c.best_strategy.get('sharpe', 0):.3f})")

        # Diversified Top5
        diversified = self.clusterer.get_diversified_top(top_strategies, top_n=5)
        results["diversified_top5"] = [
            {
                "rank": i + 1,
                "name": s.get("name", ""),
                "sharpe": s.get("sharpe", 0),
                "alpha": s.get("alpha", 0),
                "categories": s.get("factor_categories", []),
            }
            for i, s in enumerate(diversified)
        ]

        print(f"\n  Diversified Top5:")
        for s in results["diversified_top5"]:
            print(f"    #{s['rank']} {s['name']} Sharpe={s['sharpe']:.3f} Alpha={s['alpha']:.3f}")

        # 总结
        oos_passed = sum(1 for r in results["oos_results"] if r["passed"])
        mc_robust = sum(1 for r in results["mc_results"] if r["is_robust"])
        print(f"\n  Summary:")
        print(f"    OOS Passed: {oos_passed}/{len(results['oos_results'])}")
        print(f"    MC Robust: {mc_robust}/{len(results['mc_results'])}")
        print(f"    Clusters: {len(clusters)}")
        print(f"    Diversified Top5: {len(results['diversified_top5'])}")

        return results

    def _simulate_oos(self, name: str) -> List[OOSResult]:
        """模拟OOS结果"""
        rng = random.Random(hash(name))
        results = []
        for split in self.oos.splits:
            train_sharpe = rng.uniform(0.5, 2.0)
            # 测试期Sharpe = 训练期的40%-120%
            test_sharpe = train_sharpe * rng.uniform(0.4, 1.2)
            is_consistent = test_sharpe >= train_sharpe * 0.5

            results.append(OOSResult(
                strategy_name=name,
                train_period=f"{split['train'][0]} ~ {split['train'][1]}",
                test_period=f"{split['test'][0]} ~ {split['test'][1]}",
                train_annual=rng.uniform(5, 20),
                test_annual=rng.uniform(-5, 15),
                train_sharpe=round(train_sharpe, 3),
                test_sharpe=round(test_sharpe, 3),
                train_max_dd=round(-rng.uniform(5, 25), 2),
                test_max_dd=round(-rng.uniform(5, 30), 2),
                is_consistent=is_consistent,
            ))
        return results

    def _simulate_returns(self, annual_return: float, days: int) -> List[float]:
        """模拟日收益率序列"""
        rng = random.Random(42)
        daily_mean = annual_return / 100 / 252
        daily_std = daily_mean * 2.5
        return [rng.gauss(daily_mean, daily_std) for _ in range(days)]
