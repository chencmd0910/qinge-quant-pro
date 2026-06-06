"""Walk Forward Test - 滚动窗口验证

这是量化策略验证的核心方法。
避免过拟合，验证策略在未见过的数据上是否有效。

方法:
    窗口1: 训练 2018-2020 → 测试 2021-2023
    窗口2: 训练 2019-2021 → 测试 2022-2024
    窗口3: 训练 2020-2022 → 测试 2023-2025
    窗口4: 训练 2021-2023 → 测试 2024-2026

评判标准:
    - 每个测试窗口都赚钱 → 策略有效
    - 3/4赚钱 → 策略可能有效
    - <= 2/4 赚钱 → 策略无效或过拟合

输出:
    每个窗口的独立回测结果
    汇总统计: 平均年化、最差窗口、一致性评分
"""
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json


@dataclass
class WalkForwardWindow:
    """Walk Forward 单个窗口"""
    window_id: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    # 测试结果
    test_annual_return: float = 0
    test_total_return: float = 0
    test_max_drawdown: float = 0
    test_sharpe: float = 0
    test_trades: int = 0
    is_profitable: bool = False


@dataclass
class WalkForwardResult:
    """Walk Forward 汇总结果"""
    strategy_name: str
    windows: List[WalkForwardWindow]
    # 汇总
    total_windows: int = 0
    profitable_windows: int = 0
    consistency_score: float = 0  # 一致性评分 0-100
    avg_annual_return: float = 0
    worst_annual_return: float = 0
    best_annual_return: float = 0
    avg_max_drawdown: float = 0
    is_valid: bool = False  # 策略是否有效


class WalkForwardTest:
    """Walk Forward 测试框架

    使用:
        wft = WalkForwardTest()
        result = wft.run(
            strategy_func=my_strategy,
            full_start="2018-01-01",
            full_end="2026-06-05",
            train_years=3,
            test_years=3,
            step_years=1,
        )
    """

    def __init__(self):
        pass

    def generate_windows(self, full_start: str, full_end: str,
                         train_years: int = 3, test_years: int = 3,
                         step_years: int = 1) -> List[dict]:
        """生成Walk Forward窗口

        Args:
            full_start: 完整数据起始日期
            full_end: 完整数据结束日期
            train_years: 训练窗口年数
            test_years: 测试窗口年数
            step_years: 滑动步长年数

        Returns:
            [{"train_start", "train_end", "test_start", "test_end"}, ...]
        """
        start_dt = datetime.strptime(full_start[:10], '%Y-%m-%d')
        end_dt = datetime.strptime(full_end[:10], '%Y-%m-%d')

        windows = []
        current = start_dt
        window_id = 0

        while True:
            train_start = current
            train_end = train_start + timedelta(days=train_years * 365)
            test_start = train_end + timedelta(days=1)
            test_end = test_start + timedelta(days=test_years * 365)

            # 检查是否超出数据范围
            if test_end > end_dt:
                break

            windows.append({
                "window_id": window_id,
                "train_start": train_start.strftime('%Y-%m-%d'),
                "train_end": train_end.strftime('%Y-%m-%d'),
                "test_start": test_start.strftime('%Y-%m-%d'),
                "test_end": test_end.strftime('%Y-%m-%d'),
            })

            current += timedelta(days=step_years * 365)
            window_id += 1

        return windows

    def run(self, strategy_func: Callable, full_start: str, full_end: str,
            train_years: int = 3, test_years: int = 3, step_years: int = 1,
            strategy_name: str = "Unknown", **kwargs) -> WalkForwardResult:
        """运行Walk Forward测试

        Args:
            strategy_func: 策略函数，接收(start_date, end_date, **kwargs)返回metrics dict
            full_start: 完整数据起始
            full_end: 完整数据结束
            train_years: 训练年数
            test_years: 测试年数
            step_years: 步长
            strategy_name: 策略名称
            **kwargs: 传递给策略函数的额外参数

        Returns:
            WalkForwardResult
        """
        windows_spec = self.generate_windows(full_start, full_end,
                                              train_years, test_years, step_years)

        if not windows_spec:
            print(f"[WalkForward] No valid windows for {train_years}+{test_years} years")
            return WalkForwardResult(strategy_name=strategy_name, windows=[])

        print(f"[WalkForward] {strategy_name}: {len(windows_spec)} windows")
        print(f"  Train: {train_years}y | Test: {test_years}y | Step: {step_years}y")

        windows = []
        for spec in windows_spec:
            wid = spec["window_id"]
            print(f"\n  Window {wid}: Train {spec['train_start']}~{spec['train_end']} "
                  f"-> Test {spec['test_start']}~{spec['test_end']}")

            # 运行测试窗口回测
            try:
                metrics = strategy_func(
                    start_date=spec["test_start"],
                    end_date=spec["test_end"],
                    **kwargs
                )

                window = WalkForwardWindow(
                    window_id=wid,
                    train_start=spec["train_start"],
                    train_end=spec["train_end"],
                    test_start=spec["test_start"],
                    test_end=spec["test_end"],
                    test_annual_return=metrics.get('annual_return', 0),
                    test_total_return=metrics.get('total_return', 0),
                    test_max_drawdown=metrics.get('max_drawdown', 0),
                    test_sharpe=metrics.get('sharpe_ratio', 0),
                    test_trades=metrics.get('trade_count', 0),
                    is_profitable=metrics.get('annual_return', 0) > 0,
                )
                windows.append(window)

                status = "PROFIT" if window.is_profitable else "LOSS"
                print(f"    -> {status}: annual={window.test_annual_return:+.2f}% "
                      f"dd={window.test_max_drawdown:.2f}% sharpe={window.test_sharpe:.2f}")

            except Exception as e:
                print(f"    -> ERROR: {e}")
                windows.append(WalkForwardWindow(
                    window_id=wid,
                    train_start=spec["train_start"],
                    train_end=spec["train_end"],
                    test_start=spec["test_start"],
                    test_end=spec["test_end"],
                ))

        # 汇总
        profitable = [w for w in windows if w.is_profitable]
        total = len(windows)
        profitable_count = len(profitable)

        returns = [w.test_annual_return for w in windows if w.test_annual_return != 0]
        drawdowns = [w.test_max_drawdown for w in windows if w.test_max_drawdown != 0]

        # 一致性评分: 盈利窗口占比 * 100
        consistency = (profitable_count / total * 100) if total > 0 else 0

        # 策略有效: >= 75% 窗口盈利 (3/4 或更多)
        is_valid = consistency >= 75

        result = WalkForwardResult(
            strategy_name=strategy_name,
            windows=windows,
            total_windows=total,
            profitable_windows=profitable_count,
            consistency_score=round(consistency, 1),
            avg_annual_return=round(sum(returns) / len(returns), 2) if returns else 0,
            worst_annual_return=round(min(returns), 2) if returns else 0,
            best_annual_return=round(max(returns), 2) if returns else 0,
            avg_max_drawdown=round(sum(drawdowns) / len(drawdowns), 2) if drawdowns else 0,
            is_valid=is_valid,
        )

        # 打印汇总
        print(f"\n  === Walk Forward Summary ===")
        print(f"  Strategy: {strategy_name}")
        print(f"  Windows: {profitable_count}/{total} profitable")
        print(f"  Consistency: {consistency:.1f}%")
        print(f"  Avg Annual: {result.avg_annual_return:+.2f}%")
        print(f"  Worst: {result.worst_annual_return:+.2f}% | Best: {result.best_annual_return:+.2f}%")
        print(f"  Valid: {'YES' if is_valid else 'NO'}")

        return result

    def format_report(self, result: WalkForwardResult) -> dict:
        """格式化为JSON报告"""
        return {
            "strategy": result.strategy_name,
            "total_windows": result.total_windows,
            "profitable_windows": result.profitable_windows,
            "consistency_score": result.consistency_score,
            "avg_annual_return": result.avg_annual_return,
            "worst_annual_return": result.worst_annual_return,
            "best_annual_return": result.best_annual_return,
            "avg_max_drawdown": result.avg_max_drawdown,
            "is_valid": result.is_valid,
            "windows": [
                {
                    "id": w.window_id,
                    "train": f"{w.train_start} ~ {w.train_end}",
                    "test": f"{w.test_start} ~ {w.test_end}",
                    "annual_return": w.test_annual_return,
                    "max_drawdown": w.test_max_drawdown,
                    "sharpe": w.test_sharpe,
                    "trades": w.test_trades,
                    "profitable": w.is_profitable,
                }
                for w in result.windows
            ],
        }
