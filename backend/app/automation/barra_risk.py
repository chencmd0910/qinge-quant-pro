"""
Barra风险模型 (CNE6简化版) — 风险分解与归因

对标机构: MSCI Barra CNE6 / Axioma / Northfield

核心能力:
1. 因子暴露计算 — 7大类风险因子 (Size/Value/Momentum/Volatility/Quality/Leverage/Liquidity)
2. 协方差矩阵 — 日收益协方差 + 收缩估计 (Ledoit-Wolf style) + 特征值清洗
3. 风险分解 — 系统风险 vs 特质风险 / 因子归因贡献
4. 边际风险 — 每只股票对组合总风险的边际贡献
5. 风险报告 — 可读的JSON报告 + 日志

设计原则:
- 零API依赖 (全部从OHLCV计算)
- 对标Barra CNE6但简化到实操级
- 收缩估计减少估计误差 (真实Barra也这么做)
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import json

logger = logging.getLogger("BarraRisk")

KLINE_DIR = "/app/data/klines/parquet"
REPORT_DIR = "/app/data/reports"
LOOKBACK_DAYS = 252  # 1年交易日


class BarraRiskModel:
    """Barra风格风险模型 (CNE6简化)"""

    def __init__(self, lookback_days: int = LOOKBACK_DAYS):
        self.lookback_days = lookback_days

    def analyze_portfolio(self, holdings: List[dict], target_date: str) -> dict:
        """组合风险全分析

        Args:
            holdings: [{code, weight, name, ...}]
            target_date: 评估日期 str "YYYY-MM-DD"

        Returns:
            完整风险报告
        """
        if not holdings or len(holdings) < 2:
            return {"error": "持仓不足，至少2只"}

        target = pd.Timestamp(target_date)

        # 1. 因子暴露矩阵
        exposures = self._compute_exposures(holdings, target)
        if exposures is None:
            return {"error": "因子暴露计算失败"}

        # 2. 协方差矩阵
        cov_matrix = self._estimate_covariance(holdings, target)
        if cov_matrix is None:
            return {"error": "协方差估计失败"}

        # 3. 风险分解
        risk_decomp = self._decompose_risk(holdings, exposures, cov_matrix)

        # 4. 边际风险
        marginal = self._marginal_risk(holdings, cov_matrix)

        # 5. 因子贡献
        factor_contrib = self._factor_contribution(holdings, exposures, cov_matrix)

        report = {
            "date": target_date,
            "holdings_count": len(holdings),
            "total_portfolio_volatility_annual": risk_decomp["total_vol"],
            "systematic_risk_pct": risk_decomp["systematic_pct"],
            "specific_risk_pct": risk_decomp["specific_pct"],
            "factor_exposures": exposures,
            "risk_decomposition": risk_decomp,
            "marginal_risk": marginal,
            "factor_contribution": factor_contrib,
            "covariance_eigenvalues": risk_decomp.get("eigenvalues", []),
            "risk_budget_summary": self._generate_summary(holdings, risk_decomp, factor_contrib),
        }

        self._save_report(report, target_date)
        return report

    # ============================================================
    # 1. 因子暴露
    # ============================================================

    def _compute_exposures(self, holdings: List[dict], target: pd.Timestamp) -> dict:
        """计算组合在Barra风险因子上的暴露"""
        # Barra CNE6 风险因子 (简化版):
        # Size — 市值对数 (小盘=高暴露)
        # Value — 1/PB代理 (value=高暴露)
        # Momentum — 12-1月动量
        # Volatility — 60日波动率
        # Quality — 夏普比率
        # Beta — 市场Beta
        # Liquidity — 换手率倒数 (低流动性=高暴露)
        # Leverage — 波动率放大 (高杠杆=高暴露)

        n = len(holdings)
        codes = [h["code"] for h in holdings]
        weights = np.array([h.get("weight", 1.0 / n) for h in holdings])

        # 逐股计算暴露
        exp_size = np.zeros(n)
        exp_value = np.zeros(n)
        exp_momentum = np.zeros(n)
        exp_volatility = np.zeros(n)
        exp_quality = np.zeros(n)
        exp_beta = np.zeros(n)
        exp_liquidity = np.zeros(n)
        exp_leverage = np.zeros(n)

        for i, code in enumerate(codes):
            df = self._load_kline(code)
            if df is None or len(df) < 60:
                continue

            close = df["close"].values.astype(float)
            volume = df["volume"].values.astype(float)
            rets = np.diff(close) / close[:-1]

            # Size: -log(price * volume) 归一化 (负号使小盘为正暴露)
            avg_price = np.mean(close[-20:])
            avg_vol = np.mean(volume[-20:])
            exp_size[i] = -np.log(avg_price * avg_vol + 1e-8) / 20  # scale

            # Value: 1/PB代理 = 1/(price/book) ≈ volatility_of_returns / price_drawdown
            # 简化: 低PB = 价格相对低 = 用 (high-low range / close) 代理
            recent = close[-60:]
            exp_value[i] = (np.max(recent) - np.min(recent)) / np.mean(recent) * 2  # 高range=高价值暴露

            # Momentum: 12-1月动量 (跳最近1个月)
            if len(close) >= 252:
                mom_12_1 = close[-20] / close[-252] - 1  # Janus style
            else:
                mom_12_1 = close[-1] / close[-60] - 1
            exp_momentum[i] = mom_12_1 * 5  # scale

            # Volatility: 60日年化波动率
            if len(rets) >= 60:
                vol_60 = np.std(rets[-60:]) * np.sqrt(252)
            else:
                vol_60 = np.std(rets) * np.sqrt(252)
            exp_volatility[i] = vol_60

            # Quality: daily_sharpe proxy
            if len(rets) >= 60:
                sharpe = np.mean(rets[-60:]) / (np.std(rets[-60:]) + 1e-8)
            else:
                sharpe = np.mean(rets) / (np.std(rets) + 1e-8)
            exp_quality[i] = sharpe * 2  # scale

            # Beta: 简化 — 自身波动率 / 假设市场波动率15%
            exp_beta[i] = min(3.0, max(0.2, vol_60 / 0.15))

            # Liquidity: 1 / 日均换手率 (高换手=低暴露)
            if len(close) >= 20:
                turnover = np.mean(volume[-20:]) / (np.mean(close[-20:]) * 100)  # 简化换手
            else:
                turnover = 0.01
            exp_liquidity[i] = max(0, 0.1 / (turnover + 1e-8))  # 低流动性=高暴露

            # Leverage: 波动率/TTM动量 — 高波动+负动量=去杠杆风险
            exp_leverage[i] = vol_60 * (1 - mom_12_1) * 10  # 高波动+无动量=高杠杆暴露

        # Z-score 归一化每个因子暴露 (使各因子可比)
        def _zscore(arr):
            s = np.std(arr)
            return (arr - np.mean(arr)) / s if s > 0 else arr

        factor_exposures = {
            "Size": _zscore(exp_size).tolist(),
            "Value": _zscore(exp_value).tolist(),
            "Momentum": _zscore(exp_momentum).tolist(),
            "Volatility": _zscore(exp_volatility).tolist(),
            "Quality": _zscore(exp_quality).tolist(),
            "Beta": _zscore(exp_beta).tolist(),
            "Liquidity": _zscore(exp_liquidity).tolist(),
            "Leverage": _zscore(exp_leverage).tolist(),
        }

        # 加权暴露
        weighted = {}
        for name, exp_list in factor_exposures.items():
            weighted[name] = float(np.sum(np.array(exp_list) * weights))

        return {
            "raw": {k: [round(float(x), 3) for x in v] for k, v in factor_exposures.items()},
            "weighted_portfolio": {k: round(float(v), 4) for k, v in weighted.items()},
            "top_exposures": sorted(weighted.items(), key=lambda x: abs(x[1]), reverse=True)[:3],
            "codes": codes,
        }

    # ============================================================
    # 2. 协方差矩阵
    # ============================================================

    def _estimate_covariance(self, holdings: List[dict], target: pd.Timestamp) -> Optional[np.ndarray]:
        """收缩估计协方差矩阵 (Ledoit-Wolf简化)"""
        n = len(holdings)
        if n < 2:
            return None

        # 获取日收益矩阵
        lookback = min(self.lookback_days, 252)
        returns_matrix = []
        valid_stocks = []

        for h in holdings:
            rets = self._get_returns(h["code"], target, lookback)
            if len(rets) >= 60:  # 至少60个有效交易日
                returns_matrix.append(rets[-lookback:])
                valid_stocks.append(h)

        if len(valid_stocks) < 2:
            return None

        # Pad to same length
        max_len = max(len(r) for r in returns_matrix) if returns_matrix else 0
        padded = np.zeros((len(valid_stocks), max_len))
        for i, r in enumerate(returns_matrix):
            padded[i, -len(r):] = r[:max_len]

        # 样本协方差
        sample_cov = np.cov(padded)

        # 收缩估计: Σ_shrink = δ * Σ_target + (1-δ) * Σ_sample
        # 目标矩阵: 对角矩阵 (假设零相关性)
        target_cov = np.diag(np.diag(sample_cov))

        # 收缩强度 δ (简化Ledoit-Wolf)
        # δ = (总方差误差) / (偏置^2 + 方差误差)
        n_obs = max_len
        n_assets = len(valid_stocks)
        delta = min(0.5, n_assets / n_obs)  # 资产数越多收缩越大

        cov_shrunk = delta * target_cov + (1 - delta) * sample_cov

        return cov_shrunk

    # ============================================================
    # 3. 风险分解
    # ============================================================

    def _decompose_risk(
        self, holdings: List[dict], exposures: dict, cov_matrix: np.ndarray
    ) -> dict:
        """分解总风险为系统风险+特质风险"""
        n = len(holdings)
        weights = np.array([h.get("weight", 1.0 / n) for h in holdings])

        # 用有效个数的cov
        valid_n = cov_matrix.shape[0]
        valid_weights = weights[:valid_n]
        valid_weights = valid_weights / valid_weights.sum()  # re-normalize

        # 总波动率 (年化)
        daily_var = valid_weights @ cov_matrix @ valid_weights
        daily_vol = np.sqrt(max(0, daily_var))
        total_vol_annual = daily_vol * np.sqrt(252)

        # 特征值分解 (风险因子分析)
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
        eigenvalues = np.sort(eigenvalues)[::-1]  # 降序
        total_eigenval = np.sum(eigenvalues)

        # 系统风险 = 前K个主成分解释的方差
        # 经验法则: 前3个PC通常是系统因子
        n_pcs = min(3, len(eigenvalues))
        systematic_pct = float(np.sum(eigenvalues[:n_pcs]) / total_eigenval) if total_eigenval > 0 else 0
        specific_pct = 1.0 - systematic_pct

        # 风险预算
        marginal_risks = cov_matrix @ valid_weights  # 边际风险贡献向量
        risk_contributions = valid_weights * marginal_risks / daily_vol  # 风险贡献

        return {
            "total_vol_annual": round(float(total_vol_annual), 4),
            "total_vol_daily": round(float(daily_vol), 6),
            "systematic_pct": round(systematic_pct, 4),
            "specific_pct": round(specific_pct, 4),
            "total_vol": round(float(total_vol_annual), 4),
            "eigenvalues_top5": [round(float(e), 8) for e in eigenvalues[:5]],
            "condition_number": round(float(eigenvalues[0] / (eigenvalues[-1] + 1e-12)), 1),
            "effective_rank": int(np.sum(eigenvalues) ** 2 / np.sum(eigenvalues ** 2)) if total_eigenval > 0 else 0,
        }

    # ============================================================
    # 4. 边际风险
    # ============================================================

    def _marginal_risk(self, holdings: List[dict], cov_matrix: np.ndarray) -> list:
        """每只股票的边际风险贡献"""
        n = len(holdings)
        valid_n = cov_matrix.shape[0]
        weights = np.array([h.get("weight", 1.0 / n) for h in holdings[:valid_n]])
        weights = weights / weights.sum()

        daily_var = weights @ cov_matrix @ weights
        daily_vol = np.sqrt(max(0, daily_var))
        marginal = cov_matrix @ weights / daily_vol

        results = []
        for i, h in enumerate(holdings[:valid_n]):
            results.append({
                "code": h["code"],
                "name": h.get("name", ""),
                "weight": round(float(weights[i]), 4),
                "marginal_risk": round(float(marginal[i]), 6),
                "risk_contribution": round(float(weights[i] * marginal[i] / daily_vol), 4),
                "pct_of_total": round(float(weights[i] * marginal[i] / daily_vol) * 100, 1) if daily_vol > 0 else 0,
            })

        return sorted(results, key=lambda x: x["risk_contribution"], reverse=True)

    # ============================================================
    # 5. 因子贡献
    # ============================================================

    def _factor_contribution(self, holdings: List[dict], exposures: dict, cov_matrix: np.ndarray) -> dict:
        """因子风险归因"""
        weighted = exposures.get("weighted_portfolio", {})
        if not weighted:
            return {}

        # 因子波动率贡献 = 暴露 * 因子波动率
        # 简化: 每个因子的年化波动率近似 20%
        factor_vol = 0.20

        contributions = {}
        for name, exposure in weighted.items():
            # 风险贡献 = |exposure| * factor_vol (标准化暴露×因子波动率)
            risk_pct = abs(exposure) * factor_vol
            contributions[name] = {
                "exposure": exposure,
                "risk_contribution_pct": round(risk_pct * 100, 2),
                "direction": "long" if exposure > 0 else "short",
            }

        # 排序
        sorted_contrib = sorted(
            contributions.items(),
            key=lambda x: x[1]["risk_contribution_pct"],
            reverse=True
        )

        return {
            "by_factor": {k: v for k, v in sorted_contrib},
            "total_factor_risk_pct": round(
                sum(v["risk_contribution_pct"] for _, v in sorted_contrib), 2
            ),
        }

    # ============================================================
    # 6. 风险摘要
    # ============================================================

    def _generate_summary(self, holdings, risk_decomp, factor_contrib) -> dict:
        """生成可读风险摘要"""
        total_vol = risk_decomp.get("total_vol", 0)
        systematic = risk_decomp.get("systematic_pct", 0)

        # 风险等级
        if total_vol < 0.10:
            level = "低"
            color = "green"
        elif total_vol < 0.20:
            level = "中"
            color = "yellow"
        elif total_vol < 0.30:
            level = "中高"
            color = "orange"
        else:
            level = "高"
            color = "red"

        # 最大因子暴露
        top_exposures = factor_contrib.get("by_factor", {})
        top_factors = list(top_exposures.items())[:3]

        return {
            "risk_level": level,
            "risk_color": color,
            "annual_volatility": f"{total_vol:.1%}",
            "systematic_risk": f"{systematic:.0%}",
            "top_risk_factors": [
                f"{name}({info['direction']}): {info['risk_contribution_pct']:.1f}%"
                for name, info in top_factors
            ],
            "condition_number": risk_decomp.get("condition_number", 0),
            "effective_diversification": risk_decomp.get("effective_rank", len(holdings)),
        }

    # ============================================================
    # 数据辅助
    # ============================================================

    def _load_kline(self, code: str) -> Optional[pd.DataFrame]:
        try:
            path = Path(KLINE_DIR) / f"{code}.parquet"
            if not path.exists():
                return None
            df = pd.read_parquet(path)
            df["date"] = pd.to_datetime(df["date"])
            return df
        except:
            return None

    def _get_returns(self, code: str, target: pd.Timestamp, days: int) -> np.ndarray:
        try:
            df = self._load_kline(code)
            if df is None:
                return np.array([])
            df = df[df["date"] <= target]
            close = df["close"].values.astype(float)[-days-1:]
            if len(close) < 2:
                return np.array([])
            return np.diff(close) / close[:-1]
        except:
            return np.array([])

    def _save_report(self, report: dict, date_str: str):
        try:
            Path(REPORT_DIR).mkdir(parents=True, exist_ok=True)
            path = Path(REPORT_DIR) / f"barra_risk_{date_str}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"Barra风险报告已保存: {path}")
        except Exception as e:
            logger.warning(f"保存Barra报告失败: {e}")
