"""AI Research Lab v1 - 自动策略研究流水线

完整流程:
    1. Generator: 生成100个策略变体
    2. Batch Backtest: 自动回测
    3. Auto Validation: 自动过滤
    4. Tournament: Top10排行榜
    5. Promotion: 自动晋级

使用:
    lab = AIResearchLab()
    result = lab.run_full_pipeline(count=100)
"""
from typing import List, Dict, Callable, Optional
from datetime import datetime
import json, os, sys, random, math

from .generator import StrategyGenerator, GeneratedStrategy
from .database import ResearchDatabase
from .validation import StrategyValidator
from .walk_forward import WalkForwardTest
from .lifecycle import StrategyLifecycle, StrategyStatus, PromotionRules
from .registry import StrategyRegistry, StrategyRecord
from ..benchmark.benchmark import BenchmarkComparator


class AIResearchLab:
    """AI研究实验室

    自动化策略研究全流程。
    """

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'research'
        )
        os.makedirs(self.data_dir, exist_ok=True)

        self.generator = StrategyGenerator(seed=42)
        self.db = ResearchDatabase(self.data_dir)
        self.validator = StrategyValidator()
        self.benchmark = BenchmarkComparator()
        self.registry = StrategyRegistry(self.data_dir)
        self.lifecycle = StrategyLifecycle(self.data_dir)

    def run_full_pipeline(self, count: int = 100,
                          backtest_func: Callable = None) -> dict:
        """运行完整研究流水线

        Args:
            count: 生成策略数量
            backtest_func: 回测函数 (strategy) -> metrics dict

        Returns:
            {
                "generated": int,
                "backtested": int,
                "validated": int,
                "filtered": int,
                "top10": list,
                "summary": dict,
            }
        """
        print("=" * 60)
        print("AI Research Lab v1 - Full Pipeline")
        print("=" * 60)

        # 1. 生成策略
        print(f"\n[1/5] Generating {count} strategies...")
        strategies = self.generator.generate_diverse(count)
        print(f"  Generated: {len(strategies)}")
        categories = set()
        for s in strategies:
            categories.update(s.factor_categories)
        print(f"  Categories covered: {sorted(categories)}")

        # 2. 批量回测
        print(f"\n[2/5] Batch backtesting...")
        if backtest_func is None:
            backtest_func = self._simulate_backtest

        results = []
        for i, strategy in enumerate(strategies):
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i+1}/{len(strategies)}")
            try:
                metrics = backtest_func(strategy)
                results.append({
                    "strategy_id": strategy.strategy_id,
                    "strategy_name": strategy.name,
                    "strategy_type": "auto_generated",
                    "factors": strategy.factors,
                    "top_n": strategy.top_n,
                    "rebalance_freq": strategy.rebalance_freq,
                    "factor_categories": strategy.factor_categories,
                    "generation": strategy.generation,
                    "status": "BACKTESTED",
                    **metrics,
                })
            except Exception as e:
                results.append({
                    "strategy_id": strategy.strategy_id,
                    "strategy_name": strategy.name,
                    "status": "FAILED",
                    "error": str(e),
                })

        backtested = len([r for r in results if r["status"] == "BACKTESTED"])
        failed = len([r for r in results if r["status"] == "FAILED"])
        print(f"  Backtested: {backtested}, Failed: {failed}")

        # 3. 自动验证
        print(f"\n[3/5] Auto validation...")
        validated = []
        filtered = []

        for r in results:
            if r["status"] != "BACKTESTED":
                filtered.append(r)
                continue

            # 验证规则
            is_valid, reasons = self._validate_strategy(r)
            if is_valid:
                r["status"] = "VALIDATED"
                r["validation_score"] = self._calculate_validation_score(r)
                validated.append(r)
            else:
                r["status"] = "FILTERED"
                r["filter_reasons"] = reasons
                filtered.append(r)

        print(f"  Validated: {len(validated)}")
        print(f"  Filtered: {len(filtered)}")

        # 4. Tournament (Top 10)
        print(f"\n[4/5] Strategy Tournament...")
        validated.sort(key=lambda r: r.get("validation_score", 0), reverse=True)
        top10 = validated[:10]

        print(f"\n  {'Rank':<5} {'Name':<30} {'Annual':>8} {'DD':>8} {'Sharpe':>8} {'Alpha':>8} {'Score':>7}")
        print(f"  {'-'*80}")
        for i, r in enumerate(top10):
            print(f"  {i+1:<5} {r['strategy_name']:<30} "
                  f"{r.get('annual_return', 0):>+7.2f}% "
                  f"{r.get('max_drawdown', 0):>7.2f}% "
                  f"{r.get('sharpe', 0):>8.3f} "
                  f"{r.get('alpha', 0):>+7.3f} "
                  f"{r.get('validation_score', 0):>7.1f}")

        # 5. 存入数据库
        print(f"\n[5/5] Saving to Research Database...")
        self.db.insert_batch(results)
        print(f"  Total records: {self.db.count()}")

        # 汇总
        summary = self.db.get_summary()
        print(f"\n  Research DB Summary: {summary}")

        output = {
            "generated": len(strategies),
            "backtested": backtested,
            "validated": len(validated),
            "filtered": len(filtered),
            "failed": failed,
            "top10": [
                {
                    "rank": i + 1,
                    "strategy_id": r["strategy_id"],
                    "name": r["strategy_name"],
                    "annual_return": r.get("annual_return", 0),
                    "max_drawdown": r.get("max_drawdown", 0),
                    "sharpe": r.get("sharpe", 0),
                    "alpha": r.get("alpha", 0),
                    "validation_score": r.get("validation_score", 0),
                    "factors": [f[0] for f in r.get("factors", [])],
                    "top_n": r.get("top_n", 0),
                    "rebalance_freq": r.get("rebalance_freq", ""),
                }
                for i, r in enumerate(top10)
            ],
            "db_summary": summary,
            "run_at": datetime.now().isoformat(),
        }

        # 保存结果
        output_file = os.path.join(self.data_dir, 'latest_research_run.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        return output

    def _validate_strategy(self, r: dict) -> tuple:
        """验证单个策略"""
        reasons = []

        # 年化收益 > -20%
        annual = r.get("annual_return", 0)
        if annual < -20:
            reasons.append(f"年化收益 {annual:.2f}% < -20%")

        # 最大回撤 > -60%
        dd = r.get("max_drawdown", 0)
        if dd < -60:
            reasons.append(f"最大回撤 {dd:.2f}% < -60%")

        # 夏普 > 0.3
        sharpe = r.get("sharpe", 0)
        if sharpe < 0.3:
            reasons.append(f"夏普 {sharpe:.3f} < 0.3")

        # Alpha > -5%
        alpha = r.get("alpha", 0)
        if alpha < -5:
            reasons.append(f"Alpha {alpha:.3f}% < -5%")

        return len(reasons) == 0, reasons

    def _calculate_validation_score(self, r: dict) -> float:
        """计算验证评分 (0-100)"""
        annual = r.get("annual_return", 0)
        dd = r.get("max_drawdown", 0)
        sharpe = r.get("sharpe", 0)
        alpha = r.get("alpha", 0)

        # 年化收益分 (0-25): -10%~+30% -> 0~25
        ar_score = max(0, min(25, (annual + 10) / 40 * 25))

        # 回撤分 (0-25): -50%~0% -> 25~0
        dd_score = max(0, min(25, (50 - abs(dd)) / 50 * 25))

        # 夏普分 (0-30): 0~2.0 -> 0~30
        sharpe_score = max(0, min(30, sharpe / 2.0 * 30))

        # Alpha分 (0-20): -5%~+15% -> 0~20
        alpha_score = max(0, min(20, (alpha + 5) / 20 * 20))

        return round(ar_score + dd_score + sharpe_score + alpha_score, 1)

    def _simulate_backtest(self, strategy: GeneratedStrategy) -> dict:
        """模拟回测 (用于测试，不依赖真实数据)

        基于因子组合生成合理的模拟结果。
        """
        rng = random.Random(hash(strategy.strategy_id))

        # 基础收益 (与因子数量和类别正相关)
        factor_count = len(strategy.factors)
        category_bonus = len(strategy.factor_categories) * 0.5

        # 模拟年化收益: 3%~15% 正态分布
        base_annual = rng.gauss(7, 4) + category_bonus
        base_annual = max(-10, min(25, base_annual))

        # 模拟回撤: -10%~-35%
        max_dd = -abs(rng.gauss(18, 8))
        max_dd = max(-50, min(-5, max_dd))

        # 模拟夏普: 与收益/回撤比相关
        sharpe = abs(base_annual / abs(max_dd)) * rng.uniform(0.8, 1.5) if max_dd != 0 else 0
        sharpe = max(0, min(2.5, sharpe))

        # 模拟Alpha
        alpha = base_annual - rng.gauss(2, 1)  # 基准约2%
        alpha = max(-5, min(20, alpha))

        # 模拟胜率
        win_rate = rng.uniform(40, 70)

        # 模拟交易次数
        trade_count = int(252 / strategy.rebalance_days * strategy.top_n * 0.3)

        total_return = (1 + base_annual / 100) ** 8 - 1  # 8年

        return {
            "annual_return": round(base_annual, 2),
            "total_return": round(total_return * 100, 2),
            "max_drawdown": round(max_dd, 2),
            "sharpe": round(sharpe, 3),
            "sortino": round(sharpe * 1.3, 3),
            "win_rate": round(win_rate, 1),
            "trade_count": trade_count,
            "positions": strategy.top_n,
            "benchmark_return": 2.5,
            "alpha": round(alpha, 3),
            "period": "2018-01-01 ~ 2026-06-05",
        }
