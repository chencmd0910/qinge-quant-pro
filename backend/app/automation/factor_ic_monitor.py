"""
青鳄量化 - 因子IC衰减监控引擎

对标专业机构的因子评估体系。实时追踪因子IC（信息系数）的衰减趋势，
自动检测失效因子，防止策略越跑越歪。

核心功能:
  1. 滚动IC计算: 最近60天Rank IC + IC_IR
  2. 衰减检测: IC斜率 < 0 且持续N天 → 衰减中
  3. 失效标记: IC_IR < 阈值 → 自动降级/禁用
  4. 因子健康报告: 每日生成，供策略校准参考

专业对标:
  - Barra/WorldQuant 因子库的月度IC审查
  - 量化私募每周的因子健康检查
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

import numpy as np
import pandas as pd

def _linregress_slope(x, y):
    """简易线性回归斜率（替代scipy.stats.linregress）"""
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    num = np.sum((x - x_mean) * (y - y_mean))
    den = np.sum((x - x_mean) ** 2)
    if abs(den) < 1e-12:
        return 0.0
    return num / den

ROOT = Path("/app") if Path("/app").exists() else Path(__file__).resolve().parent.parent.parent
logger = logging.getLogger("FactorICMonitor")


# ==============================
# 因子定义与计算
# ==============================

# 可从OHLCV数据直接计算的技术因子
TECHNICAL_FACTORS = {
    "mom_5d": {
        "name": "5日动量",
        "category": "动量",
        "formula": "close / close_5d_ago - 1",
        "forward_days": 5,   # 预测5日未来收益
    },
    "mom_10d": {
        "name": "10日动量",
        "category": "动量",
        "formula": "close / close_10d_ago - 1",
        "forward_days": 5,
    },
    "mom_20d": {
        "name": "20日动量",
        "category": "动量",
        "formula": "close / close_20d_ago - 1",
        "forward_days": 10,
    },
    "consistency": {
        "name": "收益一致性",
        "category": "动量",
        "formula": "sum(close > prev_close) / window_size",
        "forward_days": 5,
    },
    "volume_ratio": {
        "name": "量比",
        "category": "量价",
        "formula": "avg(vol_5d) / avg(vol_20d)",
        "forward_days": 5,
    },
    "money_flow": {
        "name": "资金流向",
        "category": "量价",
        "formula": "((close-low)-(high-close))/(high-low) * volume",
        "forward_days": 5,
    },
    "volatility_20d": {
        "name": "20日波动率",
        "category": "波动率",
        "formula": "std(ret_20d)",
        "forward_days": 10,
    },
    "daily_sharpe": {
        "name": "日度夏普",
        "category": "波动率",
        "formula": "mean(ret_20d) / std(ret_20d)",
        "forward_days": 10,
    },
    "boll_pos": {
        "name": "布林位置",
        "category": "技术",
        "formula": "(close - ma20) / (2 * std20)",
        "forward_days": 5,
    },
    "rsi_14": {
        "name": "RSI_14",
        "category": "技术",
        "formula": "100 - 100/(1+avg_gain/avg_loss)",
        "forward_days": 5,
    },
    "price_accel": {
        "name": "价格加速度",
        "category": "动量",
        "formula": "mom_5d - mom_20d",
        "forward_days": 5,
    },
    "turnover_mom": {
        "name": "换手率动量",
        "category": "量价",
        "formula": "vol_5d / vol_60d - 1",
        "forward_days": 5,
    },
}


# ==============================
# 数据结构
# ==============================

@dataclass
class FactorICResult:
    """单个因子IC评估结果"""
    factor_name: str
    factor_label: str
    category: str

    # IC统计
    ic_mean: float = 0.0          # 平均Rank IC
    ic_std: float = 0.0           # IC标准差
    ic_ir: float = 0.0            # IC信息比率 ( = ic_mean / ic_std)
    ic_latest: float = 0.0        # 最新一期IC

    # IC趋势
    ic_slope: float = 0.0         # 最近24期IC趋势斜率
    trend: str = "stable"         # improving / stable / declining / dead

    # 统计
    ic_positive_ratio: float = 0.0  # IC为正的比例
    data_points: int = 0

    # 健康状态
    health: str = "UNKNOWN"       # HEALTHY / WATCH / WARNING / DEAD
    recommendation: str = ""

    @property
    def is_healthy(self) -> bool:
        return self.health in ("HEALTHY", "WATCH")

    @property
    def is_dead(self) -> bool:
        return self.health == "DEAD"


@dataclass
class ICFactorReport:
    """因子IC监控综合报告"""
    check_time: str = ""
    stocks_used: int = 0
    total_factors: int = 0
    data_date_range: str = ""

    # 健康统计
    healthy_factors: int = 0
    watch_factors: int = 0
    warning_factors: int = 0
    dead_factors: int = 0

    # IC排名
    top_factors: List[str] = field(default_factory=list)
    worst_factors: List[str] = field(default_factory=list)

    # 详细结果
    results: List[FactorICResult] = field(default_factory=list)

    # 操作建议
    recommendations: List[str] = field(default_factory=list)

    @property
    def needs_rebalance(self) -> bool:
        """是否需要调整因子权重"""
        return self.warning_factors + self.dead_factors > 0

    @property
    def summary_score(self) -> int:
        """0-100 健康分"""
        if self.total_factors == 0:
            return 0
        decaying = self.warning_factors + self.dead_factors * 2
        return max(0, 100 - decaying * 10)


# ==============================
# IC监控引擎
# ==============================

class FactorICMonitor:
    """因子IC衰减监控引擎

    用法:
        monitor = FactorICMonitor(data_dir="/app/data")
        report = monitor.run()
        if report.needs_rebalance:
            print("需要调整因子权重:", report.recommendations)
    """

    # 配置
    IC_WINDOW = 60          # 滚动IC窗口（交易日）
    TREND_WINDOW = 24       # 趋势检测窗口（最近N期）
    MIN_STOCKS = 100        # 最少股票数
    IC_IR_THRESHOLD = {     # IC_IR阈值
        "healthy": 0.10,    # > 0.10 = HEALTHY
        "watch": 0.05,      # > 0.05 = WATCH
        "warning": 0.02,    # > 0.02 = WARNING
        # <= 0.02 = DEAD
    }
    SLOPE_THRESHOLD = {     # IC斜率阈值(per period)
        "improving": 0.005,
        "stable": -0.003,
        "declining": -0.010,
    }

    def __init__(self, data_dir: str = None, max_stocks: int = 300):
        self.data_dir = Path(data_dir) if data_dir else ROOT / "data"
        self.kline_dir = self.data_dir / "klines" / "parquet"
        self.max_stocks = max_stocks

    def run(self) -> ICFactorReport:
        """执行因子IC监控"""
        t0 = datetime.now()
        report = ICFactorReport(check_time=datetime.now().isoformat())

        # 1. 加载股票数据 → 面板数据
        parquet_files = sorted(self.kline_dir.glob("*.parquet"))
        if not parquet_files:
            logger.warning("无k线数据")
            return report

        # 采样股票
        sample_files = self._sample(parquet_files, self.max_stocks)
        report.stocks_used = len(sample_files)

        # 2. 构建因子面板
        factor_panel = self._build_factor_panel(sample_files)
        if factor_panel is None or len(factor_panel) < 30:
            logger.warning(f"因子面板数据不足: {len(factor_panel) if factor_panel is not None else 0}天")
            return report

        report.data_date_range = f"{str(factor_panel['date'].min())[:10]} ~ {str(factor_panel['date'].max())[:10]}"
        report.total_factors = len(TECHNICAL_FACTORS)

        # 3. 对每个因子计算IC
        for fname, fdef in TECHNICAL_FACTORS.items():
            try:
                result = self._compute_factor_ic(factor_panel, fname, fdef)
                report.results.append(result)
            except Exception as e:
                logger.warning(f"计算 {fname} IC失败: {e}")
                report.results.append(FactorICResult(
                    fname, fdef["name"], fdef["category"], health="UNKNOWN"
                ))

        # 4. 汇总统计
        for r in report.results:
            if r.health == "HEALTHY":
                report.healthy_factors += 1
            elif r.health == "WATCH":
                report.watch_factors += 1
            elif r.health == "WARNING":
                report.warning_factors += 1
            elif r.health == "DEAD":
                report.dead_factors += 1

        # 排序
        sorted_results = sorted(report.results, key=lambda x: x.ic_ir, reverse=True)
        report.top_factors = [f"{r.factor_name}(IR={r.ic_ir:.3f})" for r in sorted_results[:5]]
        report.worst_factors = [f"{r.factor_name}(IR={r.ic_ir:.3f})" for r in sorted_results[-3:]]

        # 5. 生成建议
        report.recommendations = self._generate_recommendations(report)

        elapsed = (datetime.now() - t0).total_seconds()
        logger.info(f"因子IC监控完成: {report.total_factors}因子, "
                   f"健康{report.healthy_factors} 观察{report.watch_factors} "
                   f"警告{report.warning_factors} 失效{report.dead_factors}, "
                   f"耗时{elapsed:.1f}s")

        return report

    def _build_factor_panel(self, files: List[Path]) -> Optional[pd.DataFrame]:
        """构建多因子面板数据

        为每只股票计算所有因子值和未来收益，堆叠成面板。

        Returns:
            DataFrame with columns: date, symbol, factor values..., forward_return
        """
        panels = []
        total = len(files)

        for i, pf in enumerate(files):
            try:
                df = pd.read_parquet(pf)
                if len(df) < 100:
                    continue

                df = df.sort_values("date").copy()
                symbol = pf.stem

                # 基础数据
                close = df["close"].astype(float)
                high = df["high"].astype(float)
                low = df["low"].astype(float)
                volume = df["volume"].astype(float)

                factors = {"date": df["date"], "symbol": symbol}

                # 计算每个因子
                # 动量类
                factors["mom_5d"] = close.pct_change(5)
                factors["mom_10d"] = close.pct_change(10)
                factors["mom_20d"] = close.pct_change(20)

                # 一致性: 上涨天数占比(20日窗口)
                up_days = (close > close.shift(1)).rolling(20).sum()
                factors["consistency"] = up_days / 20

                # 量价: 量比
                vol_5d_avg = volume.rolling(5).mean()
                vol_20d_avg = volume.rolling(20).mean()
                factors["volume_ratio"] = vol_5d_avg / (vol_20d_avg + 1)

                # 资金流向(简化CMF)
                mf_mult = ((close - low) - (high - close)) / (high - low + 1e-9)
                mf_volume = mf_mult * volume
                factors["money_flow"] = mf_volume.rolling(10).mean() / (volume.rolling(10).mean() + 1)

                # 波动率
                ret = close.pct_change()
                factors["volatility_20d"] = ret.rolling(20).std()
                factors["daily_sharpe"] = ret.rolling(20).mean() / (ret.rolling(20).std() + 1e-9)

                # 布林位置
                ma20 = close.rolling(20).mean()
                std20 = close.rolling(20).std()
                factors["boll_pos"] = (close - ma20) / (std20 * 2 + 1e-9)

                # RSI_14
                delta = close.diff()
                gain = delta.clip(lower=0).rolling(14).mean()
                loss = (-delta.clip(upper=0)).rolling(14).mean()
                rs = gain / (loss + 1e-9)
                factors["rsi_14"] = 100 - 100 / (1 + rs)

                # 价格加速度
                factors["price_accel"] = factors["mom_5d"] - factors["mom_20d"]

                # 换手率动量
                factors["turnover_mom"] = volume / (volume.rolling(60).mean() + 1) - 1

                # 未来收益（前向）
                factors["forward_return"] = close.shift(-5) / close - 1  # 5日未来收益

                row = pd.DataFrame(factors)
                panels.append(row)

                if (i + 1) % 50 == 0:
                    logger.debug(f"构建因子面板: {i+1}/{total}")

            except Exception as e:
                logger.debug(f"处理 {pf.stem} 失败: {e}")
                continue

        if not panels:
            return None

        panel = pd.concat(panels, ignore_index=True)
        # 删除NaN
        panel = panel.dropna()
        return panel

    def _compute_factor_ic(self, panel: pd.DataFrame, factor_name: str,
                           fdef: dict) -> FactorICResult:
        """计算单个因子的Rank IC序列和统计"""
        result = FactorICResult(
            factor_name=factor_name,
            factor_label=fdef["name"],
            category=fdef["category"],
        )

        # 确保必要字段存在
        if factor_name not in panel.columns or "forward_return" not in panel.columns:
            result.health = "UNKNOWN"
            result.recommendation = "数据不足"
            return result

        # 对每个日期计算横截面Rank IC
        ic_series = []
        dates = sorted(panel["date"].unique())

        for d in dates:
            daily = panel[panel["date"] == d]
            if len(daily) < 20:  # 至少20只股票
                continue

            try:
                # Pearson on ranks = Spearman rank correlation (no scipy needed)
                ic = daily[factor_name].rank().corr(daily["forward_return"].rank())
                ic_series.append({"date": d, "ic": ic})
            except:
                continue

        if not ic_series:
            result.health = "UNKNOWN"
            result.recommendation = "IC系列为空"
            return result

        ic_df = pd.DataFrame(ic_series).set_index("date")["ic"]
        result.data_points = len(ic_df)

        # 滚动IC统计
        if len(ic_df) >= self.IC_WINDOW:
            rolling_ic = ic_df.iloc[-self.IC_WINDOW:]
        else:
            rolling_ic = ic_df

        result.ic_mean = float(rolling_ic.mean())
        result.ic_std = float(rolling_ic.std() + 1e-9)
        result.ic_ir = result.ic_mean / result.ic_std
        result.ic_latest = float(ic_df.iloc[-1])
        result.ic_positive_ratio = float((rolling_ic > 0).mean())

        # IC趋势（最近TREND_WINDOW期）
        if len(ic_df) >= self.TREND_WINDOW:
            recent = ic_df.iloc[-self.TREND_WINDOW:]
            x = np.arange(len(recent))
            slope = _linregress_slope(x, recent.values)
            result.ic_slope = float(slope)
        else:
            result.ic_slope = 0.0

        # 判断趋势
        if result.ic_slope > self.SLOPE_THRESHOLD["improving"]:
            result.trend = "improving"
        elif result.ic_slope > self.SLOPE_THRESHOLD["stable"]:
            result.trend = "stable"
        elif result.ic_slope > self.SLOPE_THRESHOLD["declining"]:
            result.trend = "declining"
        else:
            result.trend = "dead"

        # 判断健康状态
        if result.ic_ir > self.IC_IR_THRESHOLD["healthy"] and result.trend != "dead":
            result.health = "HEALTHY"
        elif result.ic_ir > self.IC_IR_THRESHOLD["watch"]:
            result.health = "WATCH"
        elif result.ic_ir > self.IC_IR_THRESHOLD["warning"]:
            result.health = "WARNING"
        else:
            result.health = "DEAD"

        # 建议
        if result.health == "DEAD":
            result.recommendation = f"因子已失效(IC_IR={result.ic_ir:.3f})，建议停用或降低权重"
        elif result.health == "WARNING":
            if result.trend == "declining":
                result.recommendation = f"IC持续衰减(斜率{result.ic_slope:.4f})，建议监控"
            else:
                result.recommendation = f"IC偏低(IR={result.ic_ir:.3f})，建议降低权重"
        elif result.health == "WATCH":
            result.recommendation = "IC波动较大，暂不调整权重"
        else:
            result.recommendation = "因子健康，保持当前权重"

        return result

    def _sample(self, files: List[Path], n: int) -> List[Path]:
        if len(files) <= n:
            return files
        step = len(files) // n
        return [files[i] for i in range(0, len(files), max(1, step))][:n]

    def _generate_recommendations(self, report: ICFactorReport) -> List[str]:
        """生成操作建议"""
        recs = []

        dead = [r for r in report.results if r.health == "DEAD"]
        if dead:
            names = ", ".join(r.factor_name for r in dead)
            recs.append(f"停用失效因子: {names}")

        warning = [r for r in report.results if r.health == "WARNING"]
        if warning:
            names = ", ".join(r.factor_name for r in warning)
            recs.append(f"降低警告因子权重: {names}")

        declining = [r for r in report.results if r.trend == "declining"]
        if declining and not dead:
            recs.append(f"监控衰减因子: {', '.join(r.factor_name for r in declining)}")

        if not recs:
            recs.append("所有因子运行正常，无需调整")

        return recs

    def generate_summary(self, report: ICFactorReport = None) -> str:
        """生成可读摘要"""
        if report is None:
            return "(无报告)"

        lines = [
            f"因子IC监控报告 — {report.check_time[:19]}",
            f"",
            f"股票样本: {report.stocks_used}只",
            f"日期范围: {report.data_date_range}",
            f"",
            f"📊 健康状态: {report.healthy_factors}健康 {report.watch_factors}观察 "
            f"{report.warning_factors}警告 {report.dead_factors}失效",
            f"",
            f"🏆 TOP5 因子:",
        ]
        for f in report.top_factors:
            lines.append(f"  ✅ {f}")
        lines.append(f"")
        lines.append(f"⚠️ 最弱因子:")
        for f in report.worst_factors:
            lines.append(f"  ❌ {f}")

        lines.append(f"")
        lines.append(f"因子明细:")
        for r in sorted(report.results, key=lambda x: x.ic_ir, reverse=True):
            icon = {"HEALTHY": "✅", "WATCH": "👀", "WARNING": "⚠️", "DEAD": "💀", "UNKNOWN": "❓"}[r.health]
            lines.append(f"  {icon} {r.factor_name:20s} IR={r.ic_ir:+.3f} "
                        f"mean={r.ic_mean:+.3f} std={r.ic_std:.3f} "
                        f"trend={r.trend:10s} [{r.health}]")

        if report.recommendations:
            lines.append(f"")
            lines.append(f"💡 操作建议:")
            for rec in report.recommendations:
                lines.append(f"  → {rec}")

        return "\n".join(lines)


# ==============================
# 入口
# ==============================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="因子IC衰减监控")
    parser.add_argument("--data-dir", type=str, default=None)
    parser.add_argument("--stocks", type=int, default=300)
    args = parser.parse_args()

    print("🔬 青鳄量化 - 因子IC衰减监控")
    print(f"   计算中（{args.stocks}只股票 × 12个因子）...")
    monitor = FactorICMonitor(data_dir=args.data_dir, max_stocks=args.stocks)
    report = monitor.run()
    print(monitor.generate_summary(report))
