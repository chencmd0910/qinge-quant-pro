"""多因子策略 V25 - 全新因子分支

新增因子:
    1. 北向资金因子 (Northbound Flow)
       - 北向资金净买入额
       - 北向资金持股比例变化

    2. 融资余额因子 (Margin Balance)
       - 融资余额变化率
       - 融资买入占比

    3. 行业景气度因子 (Industry Prosperity)
       - 行业PMI
       - 行业营收增速
       - 行业利润增速

原有因子保留:
    - 动量因子 (mom_5d/10d/20d)
    - 量价因子 (volume_ratio/money_flow)
    - 波动率因子 (volatility)
    - 基本面因子 (pe_ttm/pb_ttm)

合成方式:
    composite = 0.20 * northbound_flow
              + 0.15 * margin_balance
              + 0.20 * industry_prosperity
              + 0.15 * momentum
              + 0.15 * volume_price
              + 0.10 * volatility
              + 0.05 * fundamental
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class FactorCategory(Enum):
    """因子分类"""
    NORTHBOUND = "北向资金"
    MARGIN = "融资余额"
    INDUSTRY = "行业景气度"
    MOMENTUM = "动量"
    VOLUME_PRICE = "量价"
    VOLATILITY = "波动率"
    FUNDAMENTAL = "基本面"


@dataclass
class Factor:
    """因子定义"""
    name: str
    category: FactorCategory
    weight: float
    description: str
    grade: str = ""  # A/B/C/D


# V25因子池
V25_FACTORS = [
    # === 北向资金因子 ===
    Factor("northbound_net_buy", FactorCategory.NORTHBOUND, 0.10,
           "北向资金5日净买入额/总成交额", "A"),
    Factor("northbound_holding_chg", FactorCategory.NORTHBOUND, 0.10,
           "北向资金持股比例5日变化", "A"),

    # === 融资余额因子 ===
    Factor("margin_balance_chg", FactorCategory.MARGIN, 0.08,
           "融资余额5日变化率", "B"),
    Factor("margin_buy_ratio", FactorCategory.MARGIN, 0.07,
           "融资买入额/总成交额", "B"),

    # === 行业景气度因子 ===
    Factor("industry_revenue_growth", FactorCategory.INDUSTRY, 0.08,
           "行业营收同比增速(季度)", "A"),
    Factor("industry_profit_growth", FactorCategory.INDUSTRY, 0.07,
           "行业利润同比增速(季度)", "A"),
    Factor("industry_pmi", FactorCategory.INDUSTRY, 0.05,
           "行业PMI指数", "B"),

    # === 动量因子 (原有) ===
    Factor("mom_5d", FactorCategory.MOMENTUM, 0.06,
           "5日收益率", "A"),
    Factor("mom_10d", FactorCategory.MOMENTUM, 0.05,
           "10日收益率", "A"),
    Factor("consistency", FactorCategory.MOMENTUM, 0.04,
           "收益一致性(上涨天数占比)", "B"),

    # === 量价因子 (原有) ===
    Factor("volume_ratio", FactorCategory.VOLUME_PRICE, 0.08,
           "5日量比", "A"),
    Factor("money_flow", FactorCategory.VOLUME_PRICE, 0.07,
           "主力资金净流入/成交额", "A"),

    # === 波动率因子 (原有) ===
    Factor("volatility_20d", FactorCategory.VOLATILITY, 0.05,
           "20日波动率", "B"),
    Factor("daily_sharpe", FactorCategory.VOLATILITY, 0.05,
           "20日日度夏普", "B"),

    # === 基本面因子 (原有) ===
    Factor("pe_ttm", FactorCategory.FUNDAMENTAL, 0.03,
           "PE-TTM倒数(EP)", "C"),
    Factor("pb_ttm", FactorCategory.FUNDAMENTAL, 0.02,
           "PB-TTM倒数(BP)", "C"),
]


class MultiFactorV25:
    """多因子策略 V25

    包含北向资金、融资余额、行业景气度三大新因子。
    """

    def __init__(self, custom_weights: dict = None):
        self.factors = V25_FACTORS
        self.factor_dict = {f.name: f for f in self.factors}

        # 允许自定义权重
        if custom_weights:
            for name, weight in custom_weights.items():
                if name in self.factor_dict:
                    self.factor_dict[name].weight = weight

    def get_factor_list(self) -> List[dict]:
        """获取因子列表"""
        return [
            {
                "name": f.name,
                "category": f.category.value,
                "weight": f.weight,
                "description": f.description,
                "grade": f.grade,
            }
            for f in self.factors
        ]

    def get_category_weights(self) -> Dict[str, float]:
        """按类别汇总权重"""
        weights = {}
        for f in self.factors:
            cat = f.category.value
            weights[cat] = weights.get(cat, 0) + f.weight
        return {k: round(v, 2) for k, v in weights.items()}

    def calculate_composite(self, factor_values: Dict[str, float]) -> float:
        """计算合成因子值

        Args:
            factor_values: {factor_name: normalized_value}

        Returns:
            合成因子值 (加权平均)
        """
        total_weight = 0
        weighted_sum = 0

        for f in self.factors:
            if f.name in factor_values:
                weighted_sum += f.weight * factor_values[f.name]
                total_weight += f.weight

        if total_weight > 0:
            return weighted_sum / total_weight
        return 0

    def rank_stocks(self, stocks: List[dict], top_n: int = 20) -> List[dict]:
        """根据合成因子排名选股

        Args:
            stocks: [{symbol, factor_values: {name: value}}, ...]
            top_n: 选取前N只

        Returns:
            排序后的前N只股票
        """
        scored = []
        for stock in stocks:
            composite = self.calculate_composite(stock.get('factor_values', {}))
            scored.append({**stock, 'composite_score': composite})

        scored.sort(key=lambda x: x['composite_score'], reverse=True)
        return scored[:top_n]

    def get_factor_summary(self) -> str:
        """因子摘要"""
        cats = self.get_category_weights()
        lines = ["Multi-Factor V25 Summary:"]
        for cat, weight in cats.items():
            factors = [f for f in self.factors if f.category.value == cat]
            lines.append(f"  {cat}: {weight*100:.0f}%")
            for f in factors:
                lines.append(f"    - {f.name} ({f.weight*100:.0f}%): {f.description}")
        return "\n".join(lines)
