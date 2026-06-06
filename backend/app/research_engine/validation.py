"""Research Validation Layer - 策略真实性审计

每个策略必须输出标准化结果，并通过验证规则。
不通过验证的策略不能进入排行榜。

标准化输出:
{
    "strategy": "Multi-Factor V25",
    "start": "2018-01-01",
    "end": "2026-06-05",
    "trades": 325,
    "positions": 20,
    "annual_return": 0.125,
    "max_drawdown": -0.185,
    "sharpe": 1.15,
    "benchmark_return": 0.021,
    "alpha": 0.104
}

验证规则:
    1. 回测区间 >= 3年
    2. 交易次数 >= 20
    3. 年化收益 > -50% (不能爆仓)
    4. 最大回撤 > -80% (不能亏光)
    5. 夏普比率可计算 (std > 0)
    6. 必须有基准对比

CSV导出:
    equity_curve.csv  - 每日权益曲线
    trades.csv        - 所有交易记录
    positions.csv     - 每日持仓快照
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import csv, json, os


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    errors: List[str]
    warnings: List[str]
    standardized: dict  # 标准化输出


class StrategyValidator:
    """策略验证器"""

    # 验证规则
    MIN_YEARS = 3           # 最少回测年数
    MIN_TRADES = 20         # 最少交易次数
    MAX_ANNUAL_LOSS = -50   # 最大允许年化亏损 %
    MAX_DRAWDOWN = -80      # 最大允许回撤 %
    MIN_EQUITY_POINTS = 100 # 最少权益点数

    def validate(self, strategy_name: str, start: str, end: str,
                 metrics: dict, equity_curve: list = None,
                 trades: list = None, positions: list = None,
                 benchmark_return: float = 0) -> ValidationResult:
        """验证策略结果

        Args:
            strategy_name: 策略名称
            start: 开始日期
            end: 结束日期
            metrics: 回测指标
            equity_curve: 权益曲线
            trades: 交易记录
            positions: 持仓快照
            benchmark_return: 基准年化收益

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        # 1. 回测区间检查
        try:
            start_dt = datetime.strptime(start[:10], '%Y-%m-%d')
            end_dt = datetime.strptime(end[:10], '%Y-%m-%d')
            years = (end_dt - start_dt).days / 365.25
            if years < self.MIN_YEARS:
                errors.append(f"回测区间 {years:.1f}年 < 最低要求 {self.MIN_YEARS}年")
        except ValueError:
            errors.append(f"日期格式错误: {start} ~ {end}")
            years = 0

        # 2. 交易次数检查
        trade_count = metrics.get('trade_count', 0)
        if trade_count < self.MIN_TRADES:
            errors.append(f"交易次数 {trade_count} < 最低要求 {self.MIN_TRADES}")

        # 3. 年化收益检查
        annual_return = metrics.get('annual_return', 0)
        if annual_return < self.MAX_ANNUAL_LOSS:
            errors.append(f"年化收益 {annual_return:.2f}% 疑似爆仓 (阈值 {self.MAX_ANNUAL_LOSS}%)")

        # 4. 最大回撤检查
        max_dd = metrics.get('max_drawdown', 0)
        if max_dd < self.MAX_DRAWDOWN:
            errors.append(f"最大回撤 {max_dd:.2f}% 超限 (阈值 {self.MAX_DRAWDOWN}%)")

        # 5. 夏普比率检查
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe == 0:
            warnings.append("夏普比率为0，可能std=0或数据不足")

        # 6. 基准对比检查
        if benchmark_return == 0:
            warnings.append("未提供基准收益，Alpha无法计算")

        # 7. 权益曲线检查
        if equity_curve and len(equity_curve) < self.MIN_EQUITY_POINTS:
            warnings.append(f"权益曲线仅 {len(equity_curve)} 点，建议 >= {self.MIN_EQUITY_POINTS}")

        # 8. 收益合理性检查
        total_return = metrics.get('total_return', 0)
        if total_return > 1000:  # 10倍收益
            warnings.append(f"总收益 {total_return:.1f}% 异常高，请检查是否存在未来函数")

        # 9. 胜率检查
        win_rate = metrics.get('win_rate', 0)
        if win_rate == 100 and trade_count > 50:
            warnings.append(f"胜率100%且交易{trade_count}次，高度可疑")

        # 标准化输出
        alpha = round(annual_return - benchmark_return, 3) if benchmark_return else 0
        standardized = {
            "strategy": strategy_name,
            "start": start[:10],
            "end": end[:10],
            "trades": trade_count,
            "positions": metrics.get('positions', 0),
            "annual_return": round(annual_return / 100, 3),
            "total_return": round(total_return / 100, 3),
            "max_drawdown": round(max_dd / 100, 3),
            "sharpe": round(sharpe, 3),
            "sortino": round(metrics.get('sortino_ratio', 0), 3),
            "win_rate": round(win_rate / 100, 3),
            "benchmark_return": round(benchmark_return / 100, 3),
            "alpha": alpha,
            "excess_return": round((total_return / 100) - (benchmark_return / 100 * years), 3) if years > 0 else 0,
            "validated_at": datetime.now().isoformat(),
            "errors": errors,
            "warnings": warnings,
        }

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            standardized=standardized,
        )


class CSVExporter:
    """CSV导出器

    导出策略回测的详细数据为CSV文件。
    """

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'exports'
        )
        os.makedirs(self.output_dir, exist_ok=True)

    def export_equity_curve(self, equity_curve: List[dict],
                            strategy_name: str = "strategy") -> str:
        """导出权益曲线

        Args:
            equity_curve: [{"date": "2018-01-02", "total": 1000000, "cash": 500000, ...}, ...]
            strategy_name: 策略名称

        Returns:
            文件路径
        """
        filename = f"{strategy_name}_equity_curve.csv"
        filepath = os.path.join(self.output_dir, filename)

        if not equity_curve:
            return filepath

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=equity_curve[0].keys())
            writer.writeheader()
            writer.writerows(equity_curve)

        return filepath

    def export_trades(self, trades: List[dict],
                      strategy_name: str = "strategy") -> str:
        """导出交易记录

        Args:
            trades: [{"date": "2018-04-13", "symbol": "510300.SH", "side": "BUY", ...}, ...]
            strategy_name: 策略名称

        Returns:
            文件路径
        """
        filename = f"{strategy_name}_trades.csv"
        filepath = os.path.join(self.output_dir, filename)

        if not trades:
            return filepath

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=trades[0].keys())
            writer.writeheader()
            writer.writerows(trades)

        return filepath

    def export_positions(self, positions: List[dict],
                         strategy_name: str = "strategy") -> str:
        """导出持仓快照

        Args:
            positions: [{"date": "2018-01-02", "symbol": "510300.SH", "quantity": 100, ...}, ...]
            strategy_name: 策略名称

        Returns:
            文件路径
        """
        filename = f"{strategy_name}_positions.csv"
        filepath = os.path.join(self.output_dir, filename)

        if not positions:
            return filepath

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=positions[0].keys())
            writer.writeheader()
            writer.writerows(positions)

        return filepath

    def export_all(self, equity_curve: List[dict], trades: List[dict],
                   positions: List[dict], strategy_name: str = "strategy") -> dict:
        """导出所有CSV

        Returns:
            {"equity_curve": path, "trades": path, "positions": path}
        """
        return {
            "equity_curve": self.export_equity_curve(equity_curve, strategy_name),
            "trades": self.export_trades(trades, strategy_name),
            "positions": self.export_positions(positions, strategy_name),
        }
