"""基准对比系统

所有策略必须与基准对比:
- 沪深300 (000300.SH)
- 中证500 (000905.SH)
- 中证1000 (000852.SH)

计算:
- Alpha: 策略超额收益
- Excess Return: 策略收益 - 基准收益
- Benchmark Return: 基准年化收益
"""
from typing import Dict, Optional
import json, os


# 基准历史收益 (预计算, 简化版)
# 生产环境应从数据源实时获取
BENCHMARK_RETURNS = {
    "000300.SH": {  # 沪深300
        "2018": -25.31, "2019": 36.07, "2020": 27.21,
        "2021": -5.20, "2022": -21.63, "2023": -11.38,
        "2024": 14.68, "2025": -2.50, "2026": 0.50,
    },
    "000905.SH": {  # 中证500
        "2018": -33.32, "2019": 26.38, "2020": 20.87,
        "2021": 15.58, "2022": -20.31, "2023": -7.42,
        "2024": 8.32, "2025": 3.20, "2026": 1.80,
    },
    "000852.SH": {  # 中证1000
        "2018": -36.87, "2019": 25.67, "2020": 18.55,
        "2021": 20.52, "2022": -21.58, "2023": -6.28,
        "2024": 5.10, "2025": 5.80, "2026": 2.10,
    },
}


class BenchmarkComparator:
    """基准对比器"""

    def __init__(self):
        self.benchmarks = BENCHMARK_RETURNS

    def get_benchmark_annual(self, code: str, start_year: int = None,
                              end_year: int = None) -> float:
        """获取基准年化收益"""
        data = self.benchmarks.get(code, {})
        if not data:
            return 0

        years = sorted(data.keys())
        if start_year:
            years = [y for y in years if int(y) >= start_year]
        if end_year:
            years = [y for y in years if int(y) <= end_year]

        if not years:
            return 0

        # 计算年化收益
        cumulative = 1.0
        for y in years:
            cumulative *= (1 + data[y] / 100)

        n = len(years)
        annual = (cumulative ** (1 / n) - 1) * 100 if n > 0 else 0
        return round(annual, 2)

    def get_benchmark_total(self, code: str, start_year: int = None,
                             end_year: int = None) -> float:
        """获取基准总收益"""
        data = self.benchmarks.get(code, {})
        if not data:
            return 0

        years = sorted(data.keys())
        if start_year:
            years = [y for y in years if int(y) >= start_year]
        if end_year:
            years = [y for y in years if int(y) <= end_year]

        cumulative = 1.0
        for y in years:
            cumulative *= (1 + data[y] / 100)

        return round((cumulative - 1) * 100, 2)

    def compare(self, strategy_annual: float, strategy_total: float,
                benchmark_code: str = "000300.SH", period: str = "") -> dict:
        """策略与基准对比

        Returns:
            {
                "benchmark_code": "000300.SH",
                "benchmark_annual": float,
                "benchmark_total": float,
                "alpha": float,  # 策略年化 - 基准年化
                "excess_return": float,  # 策略总收益 - 基准总收益
            }
        """
        # 从period提取年份范围
        start_year = None
        end_year = None
        if period and '~' in period:
            parts = period.split('~')
            try:
                start_year = int(parts[0].strip()[:4])
                end_year = int(parts[1].strip()[:4])
            except:
                pass
        elif period and '-' in period:
            parts = period.split('-')
            try:
                start_year = int(parts[0].strip()[:4])
                end_year = int(parts[-1].strip()[:4])
            except:
                pass

        bench_annual = self.get_benchmark_annual(benchmark_code, start_year, end_year)
        bench_total = self.get_benchmark_total(benchmark_code, start_year, end_year)

        alpha = round(strategy_annual - bench_annual, 2)
        excess = round(strategy_total - bench_total, 2)

        return {
            "benchmark_code": benchmark_code,
            "benchmark_annual": bench_annual,
            "benchmark_total": bench_total,
            "alpha": alpha,
            "excess_return": excess,
        }

    def compare_all(self, strategy_annual: float, strategy_total: float,
                    period: str = "") -> Dict[str, dict]:
        """与所有基准对比"""
        results = {}
        for code in self.benchmarks:
            results[code] = self.compare(strategy_annual, strategy_total, code, period)
        return results
