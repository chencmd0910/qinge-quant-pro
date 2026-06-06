"""Position Sizer - 仓位管理

5种仓位计算方法:
1. Fixed Weight: 固定权重
2. Volatility Weight: 波动率加权
3. Risk Parity: 风险平价
4. Kelly Fraction: Kelly公式
5. ATR Position Sizing: ATR仓位

使用:
    sizer = PositionSizer(method="risk_parity")
    weights = sizer.calculate(symbols, returns_data)
"""
from typing import List, Dict, Optional
from enum import Enum
import math


class SizingMethod(Enum):
    FIXED = "fixed_weight"
    VOLATILITY = "volatility_weight"
    RISK_PARITY = "risk_parity"
    KELLY = "kelly_fraction"
    ATR = "atr_sizing"


class PositionSizer:
    """仓位管理器"""

    def __init__(self, method: str = "risk_parity", max_position: float = 0.25):
        self.method = SizingMethod(method)
        self.max_position = max_position  # 单标的最大仓位

    def calculate(self, symbols: List[str], returns: Dict[str, List[float]] = None,
                  volatilities: Dict[str, float] = None,
                  win_rates: Dict[str, float] = None,
                  atrs: Dict[str, float] = None,
                  prices: Dict[str, float] = None,
                  total_capital: float = 1_000_000) -> Dict[str, float]:
        """计算仓位权重

        Returns:
            {symbol: weight} 总和 <= 1.0
        """
        if self.method == SizingMethod.FIXED:
            return self._fixed_weight(symbols)
        elif self.method == SizingMethod.VOLATILITY:
            return self._volatility_weight(symbols, volatilities or {})
        elif self.method == SizingMethod.RISK_PARITY:
            return self._risk_parity(symbols, returns or {})
        elif self.method == SizingMethod.KELLY:
            return self._kelly_fraction(symbols, win_rates or {}, volatilities or {})
        elif self.method == SizingMethod.ATR:
            return self._atr_sizing(symbols, atrs or {}, prices or {}, total_capital)
        return self._fixed_weight(symbols)

    def _fixed_weight(self, symbols: List[str]) -> Dict[str, float]:
        """固定权重: 平均分配"""
        n = len(symbols)
        if n == 0:
            return {}
        weight = min(1.0 / n, self.max_position)
        return {s: round(weight, 4) for s in symbols}

    def _volatility_weight(self, symbols: List[str],
                           volatilities: Dict[str, float]) -> Dict[str, float]:
        """波动率加权: 低波动高权重

        weight_i = (1/vol_i) / sum(1/vol_j)
        """
        inv_vols = {}
        for s in symbols:
            vol = volatilities.get(s, 0.20)  # 默认20%
            if vol > 0:
                inv_vols[s] = 1.0 / vol

        total = sum(inv_vols.values())
        if total <= 0:
            return self._fixed_weight(symbols)

        weights = {}
        for s in symbols:
            w = inv_vols.get(s, 0) / total
            weights[s] = round(min(w, self.max_position), 4)

        # 归一化
        total_w = sum(weights.values())
        if total_w > 1.0:
            weights = {s: round(w / total_w, 4) for s, w in weights.items()}

        return weights

    def _risk_parity(self, symbols: List[str],
                     returns: Dict[str, List[float]]) -> Dict[str, float]:
        """风险平价: 每个标的贡献相同风险

        risk_contribution_i = w_i * sigma_i = 常数
        w_i = (1/sigma_i) / sum(1/sigma_j)
        """
        vols = {}
        for s in symbols:
            rets = returns.get(s, [])
            if len(rets) > 1:
                mean = sum(rets) / len(rets)
                var = sum((r - mean)**2 for r in rets) / (len(rets) - 1)
                vols[s] = math.sqrt(var) if var > 0 else 0.20
            else:
                vols[s] = 0.20

        return self._volatility_weight(symbols, vols)

    def _kelly_fraction(self, symbols: List[str],
                        win_rates: Dict[str, float],
                        volatilities: Dict[str, float]) -> Dict[str, float]:
        """Kelly公式: f* = (p*b - q) / b

        p = win_rate, q = 1-p, b = win/loss ratio (近似用vol)
        Kelly fraction 通常取半Kelly以降低风险
        """
        kelly_weights = {}
        for s in symbols:
            p = win_rates.get(s, 0.5)
            q = 1 - p
            # 用波动率近似盈亏比
            vol = volatilities.get(s, 0.20)
            b = 1.5  # 默认盈亏比

            # Kelly fraction
            kelly = (p * b - q) / b if b > 0 else 0
            # 半Kelly
            half_kelly = max(0, kelly / 2)
            kelly_weights[s] = half_kelly

        # 归一化到max_position
        total = sum(kelly_weights.values())
        if total > 1.0:
            kelly_weights = {s: round(w / total, 4) for s, w in kelly_weights.items()}

        return {s: round(min(w, self.max_position), 4) for s, w in kelly_weights.items()}

    def _atr_sizing(self, symbols: List[str],
                    atrs: Dict[str, float],
                    prices: Dict[str, float],
                    total_capital: float,
                    risk_per_trade: float = 0.01) -> Dict[str, float]:
        """ATR仓位: 每笔交易风险固定为总资金的1%

        position_size = (capital * risk_per_trade) / ATR
        """
        weights = {}
        for s in symbols:
            atr = atrs.get(s, 0)
            price = prices.get(s, 0)
            if atr > 0 and price > 0:
                # 每笔最大亏损 = 资金 * 1%
                max_loss = total_capital * risk_per_trade
                # 仓位 = 最大亏损 / ATR
                shares = max_loss / atr
                # 权重 = 仓位 * 价格 / 总资金
                weight = (shares * price) / total_capital
                weights[s] = round(min(weight, self.max_position), 4)
            else:
                weights[s] = 0

        return weights
