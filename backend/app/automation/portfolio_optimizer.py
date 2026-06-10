"""
组合优化器 — 波动率倒数加权 (Risk Parity 简化版)

替代等权TOP-20，根据个股波动率动态分配仓位。
高波动股票少配，低波动股票多配，控制组合整体风险。

学术对标: Risk Parity / Inverse Volatility Weighting
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger("PortfolioOptimizer")

KLINE_DIR = "/app/data/klines/parquet"


class PortfolioOptimizer:
    """组合优化器 — 波动率倒数 + 行业上限 + 单票上限"""

    def __init__(self, max_single_weight: float = 0.08,
                 max_sector_weight: float = 0.25,
                 lookback: int = 60):
        self.max_single_weight = max_single_weight  # 单票上限8%
        self.max_sector_weight = max_sector_weight  # 行业上限25%
        self.lookback = lookback

    def optimize(self, signals: List[dict], target_date: str) -> List[dict]:
        """优化组合权重

        Args:
            signals: V25信号列表 [{code, name, composite_score, sector, ...}]
            target_date: 目标日期

        Returns:
            带仓位的信号列表 [{code, name, weight, ...}]
        """
        if not signals:
            return signals

        # 1. 计算个股波动率
        volatilities = {}
        for s in signals:
            vol = self._get_volatility(s["code"], target_date)
            volatilities[s["code"]] = vol

        # 处理所有波动率为0的情况
        min_vol = min(v for v in volatilities.values() if v > 0) if any(v > 0 for v in volatilities.values()) else 0.01
        for code in volatilities:
            if volatilities[code] <= 0:
                volatilities[code] = min_vol

        # 2. 波动率倒数权重（风险平价简化）
        inv_vol = {code: 1.0 / v for code, v in volatilities.items()}
        total_inv = sum(inv_vol.values())
        raw_weights = {code: iv / total_inv for code, iv in inv_vol.items()}

        # 3. 应用约束
        # 3a. 单票上限 8%
        for code in list(raw_weights.keys()):
            if raw_weights[code] > self.max_single_weight:
                excess = raw_weights[code] - self.max_single_weight
                raw_weights[code] = self.max_single_weight
                # 重新分配超额
                others = [c for c in raw_weights if c != code]
                if others:
                    each_extra = excess / len(others)
                    for c in others:
                        raw_weights[c] += each_extra

        # 3b. 行业上限 25%
        sector_weights = {}
        for s in signals:
            sec = s.get("sector", "其他")
            code = s["code"]
            sector_weights[sec] = sector_weights.get(sec, 0) + raw_weights.get(code, 0)

        for sec, total in sector_weights.items():
            if total > self.max_sector_weight:
                ratio = self.max_sector_weight / total
                for s in signals:
                    if s.get("sector") == sec:
                        raw_weights[s["code"]] = raw_weights.get(s["code"], 0) * ratio

        # 3c. 归一化到1.0
        final_total = sum(raw_weights.values())
        if final_total > 0:
            for code in raw_weights:
                raw_weights[code] /= final_total

        # 4. 生成最终信号（带仓位）
        result = []
        for s in signals:
            weight = round(raw_weights.get(s["code"], 1.0 / len(signals)), 4)
            result.append({
                **s,
                "weight": weight,
                "volatility": round(volatilities.get(s["code"], 0), 4),
            })

        logger.info(f"组合优化: {len(result)}只, 最大仓位{max(w['weight'] for w in result):.1%}, "
                   f"最小仓位{min(w['weight'] for w in result):.1%}")

        return result

    def _get_volatility(self, symbol: str, target_date: str) -> float:
        """计算个股年化波动率"""
        try:
            path = Path(KLINE_DIR) / f"{symbol}.parquet"
            if not path.exists():
                return 0.03  # 默认3%

            df = pd.read_parquet(path)
            if "date" not in df.columns or "close" not in df.columns:
                return 0.03

            df["date"] = pd.to_datetime(df["date"])
            target = pd.Timestamp(target_date)
            df = df[df["date"] <= target].tail(self.lookback + 1)

            if len(df) < 20:
                return 0.03

            close = df["close"].values.astype(float)
            returns = np.diff(close) / close[:-1]
            daily_vol = np.std(returns)
            annual_vol = daily_vol * np.sqrt(252)
            return float(annual_vol)

        except Exception:
            return 0.03
