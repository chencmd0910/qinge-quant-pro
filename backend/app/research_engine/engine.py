"""Research Engine - 策略研究引擎

策略工厂: 创建策略 → 回测 → 基准对比 → 保存结果 → 自动排名

使用:
    engine = ResearchEngine()
    result = engine.run(strategy_func, name="ETF Rotation V1", params={...})
    leaderboard = engine.leaderboard()
"""
from typing import Callable, Dict, List, Optional
from datetime import datetime
import json, os, sys

from .registry import StrategyRegistry, StrategyRecord
from ..benchmark.benchmark import BenchmarkComparator


class ResearchEngine:
    """策略研究引擎

    统一的策略研究流程:
    1. 定义策略
    2. 运行回测
    3. 计算基准对比
    4. 注册到排行榜
    """

    def __init__(self, data_dir: str = None):
        self.registry = StrategyRegistry(data_dir)
        self.benchmark = BenchmarkComparator()
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data'
        )

    def run(self, strategy_func: Callable, name: str, strategy_type: str,
            version: str = "1.0", market: str = "A股", params: dict = None,
            symbols: list = None, period: str = "", benchmark: str = "000300.SH",
            lookback: int = 60, commission: float = 0.0003,
            slippage: float = 0.001, initial_cash: float = 1_000_000,
            tags: list = None) -> dict:
        """运行策略研究

        Args:
            strategy_func: 策略函数，接收(symbols, lookback, commission, slippage, initial_cash)
                          返回 dict with metrics
            name: 策略名称
            strategy_type: 策略类型
            version: 版本号
            market: 市场
            params: 策略参数
            symbols: 标的列表
            period: 回测区间
            benchmark: 基准标的
            lookback: 回看天数
            commission: 手续费
            slippage: 滑点
            initial_cash: 初始资金
            tags: 标签

        Returns:
            StrategyRecord
        """
        # 1. 运行回测
        print(f"[Research] Running {name} v{version}...")
        metrics = strategy_func(
            symbols=symbols, lookback=lookback,
            commission=commission, slippage=slippage,
            initial_cash=initial_cash
        )

        # 2. 基准对比
        bench_result = self.benchmark.compare(
            strategy_annual=metrics.get('annual_return', 0),
            strategy_total=metrics.get('total_return', 0),
            benchmark_code=benchmark,
            period=period or metrics.get('period', ''),
        )

        # 3. 注册
        strategy_id = f"{strategy_type}_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        record = StrategyRecord(
            strategy_id=strategy_id,
            strategy_name=name,
            strategy_type=strategy_type,
            version=version,
            market=market,
            period=period or metrics.get('period', ''),
            params=params or {},
            annual_return=metrics.get('annual_return', 0),
            total_return=metrics.get('total_return', 0),
            max_drawdown=metrics.get('max_drawdown', 0),
            sharpe_ratio=metrics.get('sharpe_ratio', 0),
            sortino_ratio=metrics.get('sortino_ratio', 0),
            win_rate=metrics.get('win_rate', 0),
            trade_count=metrics.get('trade_count', 0),
            benchmark_return=bench_result.get('benchmark_annual', 0),
            alpha=bench_result.get('alpha', 0),
            excess_return=bench_result.get('excess_return', 0),
            tags=tags or [],
        )
        self.registry.register(record)

        print(f"[Research] {name} v{version}: score={record.score}, rank=#{record.rank}")
        print(f"  Annual: {record.annual_return:+.2f}% | DD: {record.max_drawdown:.2f}% | Sharpe: {record.sharpe_ratio:.2f}")
        print(f"  Alpha: {record.alpha:+.2f}% | Excess: {record.excess_return:+.2f}%")

        return {
            "strategy_id": strategy_id,
            "name": name, "version": version,
            "score": record.score, "rank": record.rank,
            "metrics": {
                "annual_return": record.annual_return,
                "total_return": record.total_return,
                "max_drawdown": record.max_drawdown,
                "sharpe_ratio": record.sharpe_ratio,
                "win_rate": record.win_rate,
                "trade_count": record.trade_count,
            },
            "benchmark": {
                "benchmark_return": record.benchmark_return,
                "alpha": record.alpha,
                "excess_return": record.excess_return,
            },
        }

    def leaderboard(self, strategy_type: str = None,
                    market: str = None, limit: int = 20) -> List[dict]:
        """获取排行榜"""
        records = self.registry.get_leaderboard(strategy_type, market, limit)
        return [
            {
                "rank": r.rank, "id": r.strategy_id,
                "name": r.strategy_name, "type": r.strategy_type,
                "version": r.version, "market": r.market,
                "period": r.period, "score": r.score,
                "annual_return": r.annual_return,
                "max_drawdown": r.max_drawdown,
                "sharpe_ratio": r.sharpe_ratio,
                "alpha": r.alpha, "excess_return": r.excess_return,
                "created_at": r.created_at, "tags": r.tags,
            }
            for r in records
        ]

    def summary(self) -> dict:
        return self.registry.get_summary()
