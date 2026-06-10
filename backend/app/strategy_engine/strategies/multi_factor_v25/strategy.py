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
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger("MultiFactorV25")


class FactorCategory(Enum):
    """因子分类"""
    NORTHBOUND = "北向资金"
    MARGIN = "融资余额"
    FUND_FLOW = "资金流向"
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
    Factor("margin_buy_ratio", FactorCategory.MARGIN, 0.06,
           "融资买入额/总成交额", "B"),

    # === 行业景气度因子 ===
    Factor("industry_revenue_growth", FactorCategory.INDUSTRY, 0.06,
           "行业营收同比增速(季度)", "A"),
    Factor("industry_profit_growth", FactorCategory.INDUSTRY, 0.07,
           "行业利润同比增速(季度)", "A"),
    Factor("industry_pmi", FactorCategory.INDUSTRY, 0.04,
           "行业PMI指数", "B"),

    # === 动量因子 ===
    Factor("mom_10d", FactorCategory.MOMENTUM, 0.05,
           "10日收益率", "A"),
    Factor("mom_20d", FactorCategory.MOMENTUM, 0.04,
           "20日中期动量", "B"),
    Factor("consistency", FactorCategory.MOMENTUM, 0.03,
           "收益一致性(上涨天数占比)", "B"),

    # === 量价因子 ===
    Factor("volume_ratio", FactorCategory.VOLUME_PRICE, 0.01,
           "5日量比(火种保留)", "D"),
    Factor("money_flow", FactorCategory.VOLUME_PRICE, 0.06,
           "主力资金净流入/成交额", "A"),

    # === 波动率+技术因子 ===
    Factor("volatility_20d", FactorCategory.VOLATILITY, 0.04,
           "20日波动率", "B"),
    Factor("daily_sharpe", FactorCategory.VOLATILITY, 0.03,
           "20日日度夏普", "B"),
    Factor("boll_pos", FactorCategory.VOLATILITY, 0.02,
           "布林带位置(均值回归)", "B"),
    Factor("rsi_14", FactorCategory.VOLATILITY, 0.03,
           "RSI-14超买超卖", "B"),

    # === 基本面因子 (原有) ===
    Factor("pe_ttm", FactorCategory.FUNDAMENTAL, 0.02,
           "PE-TTM倒数估值(EP)", "C"),
    Factor("pb_ttm", FactorCategory.FUNDAMENTAL, 0.02,
           "PB-TTM倒数估值(BP)", "C"),
    Factor("long_term_mom_60d", FactorCategory.MOMENTUM, 0.02,
           "60日长期反转(均值回归)", "B"),
    Factor("size_factor", FactorCategory.FUNDAMENTAL, 0.02,
           "市值对数(大盘/小盘偏好)", "B"),

    # === 资金流因子 (新增) ===
    Factor("fund_flow_net_5d", FactorCategory.FUND_FLOW, 0.04,
           "5日大单净买入强度", "A"),
    Factor("fund_flow_buy_ratio", FactorCategory.FUND_FLOW, 0.03,
           "5日大单买入笔数占比", "B"),
    Factor("fund_flow_streak", FactorCategory.FUND_FLOW, 0.02,
           "大单连续买入趋势强度", "B"),
    Factor("fund_flow_avg_size_5d", FactorCategory.FUND_FLOW, 0.01,
           "均笔大单成交额(大资金偏好)", "C"),
]


class MultiFactorV25:
    """多因子策略 V25 — 含北向资金/融资融券/行业景气度

    Usage:
        st = MultiFactorV25()
        st.initialize()
        signals = st.generate_signals("2026-06-10")
    """

    # 数据路径
    KLINE_DIR = "/app/data/klines/parquet"

    def __init__(self, custom_weights: dict = None, top_n: int = 20):
        self.factors = V25_FACTORS
        self.factor_dict = {f.name: f for f in self.factors}
        self.top_n = top_n
        self._initialized = False
        self._symbols: List[str] = []
        self._kline_data: Dict[str, pd.DataFrame] = {}

        # 允许自定义权重
        if custom_weights:
            for name, weight in custom_weights.items():
                if name in self.factor_dict:
                    self.factor_dict[name].weight = weight

    def initialize(self):
        """初始化：加载股票列表和K线缓存"""
        import os
        kline_dir = Path(self.KLINE_DIR)
        if not kline_dir.exists():
            logger.warning(f"K线目录不存在: {kline_dir}")
            self._initialized = True
            return

        # 加载所有symbol
        parquet_files = sorted(kline_dir.glob("*.parquet"))
        self._symbols = [f.stem for f in parquet_files]
        logger.info(f"MultiFactorV25 初始化: {len(self._symbols)} 只股票")

        # 预加载另类数据（一次性，不重复采集）
        self._alt_cache: Dict[str, Dict[str, float]] = {}
        try:
            from app.automation.alternative_data import AlternativeDataCollector
            alt = AlternativeDataCollector()
            alt.collect_northbound()
            alt.collect_margin()
            self._alt_collector = alt
            logger.info("另类数据预加载完成")
        except Exception as e:
            logger.debug(f"另类数据预加载跳过: {e}")
            self._alt_collector = None

        # 预加载资金流数据
        self._fund_flow_cache: Dict[str, Dict[str, float]] = {}
        try:
            from app.automation.fund_flow_collector import FundFlowCollector
            ff = FundFlowCollector()
            ff.collect()
            self._fund_flow = ff
            logger.info("资金流数据预加载完成")
        except Exception as e:
            logger.debug(f"资金流预加载跳过: {e}")
            self._fund_flow = None

        self._initialized = True

    def generate_signals(self, target_date: str) -> List[dict]:
        """生成交易信号

        Args:
            target_date: 目标日期 "YYYY-MM-DD"

        Returns:
            [{"code", "symbol", "name", "side": "BUY"/"SELL",
              "confidence": 0-1, "composite_score": float, "weight": 1.0}, ...]
        """
        if not self._initialized:
            self.initialize()

        signals = []
        target = pd.Timestamp(target_date)

        try:
            # 1. 批量加载近期K线数据（最近60天，足够算所有因子）
            stock_data = self._load_recent_klines(target, lookback=60)
            if not stock_data:
                logger.warning(f"{target_date} 无K线数据")
                return signals

            logger.info(f"加载 {len(stock_data)} 只股票K线→计算因子")

            # 2a. 预计算另类因子（一次批量，避免逐股票重复采集）
            alt_factors_batch = {}
            if self._alt_collector:
                try:
                    all_symbols = list(stock_data.keys())
                    alt_factors_batch = self._alt_collector.compute_factors(all_symbols, target_date)
                    logger.info(f"另类因子批量计算: {len(alt_factors_batch)}/{len(all_symbols)} 只")
                except Exception as e:
                    logger.warning(f"另类因子批量计算失败: {e}")

            # 2c. 预计算资金流因子
            fund_flow_batch = {}
            if self._fund_flow:
                try:
                    all_symbols = list(stock_data.keys())
                    fund_flow_batch = self._fund_flow.compute_factors(all_symbols, target_date)
                    logger.info(f"资金流因子批量计算: {len(fund_flow_batch)}/{len(all_symbols)} 只")
                except Exception as e:
                    logger.warning(f"资金流因子计算失败: {e}")

            # 2b. 计算所有股票的技术因子
            scored = []
            for symbol, df in stock_data.items():
                factors = self._compute_technical_factors(df, target, symbol)
                if factors is None:
                    continue
                # 注入预计算的另类因子
                if symbol in alt_factors_batch:
                    factors.update(alt_factors_batch[symbol])
                # 注入资金流因子
                if symbol in fund_flow_batch:
                    factors.update(fund_flow_batch[symbol])
                factors["symbol"] = symbol
                composite = self.calculate_composite(factors)
                if composite != 0:
                    # 附加行业信息(用于后续中性化)
                    sector = self._alt_collector._symbol_to_sector(symbol) if self._alt_collector else "其他"
                    scored.append({
                        "code": symbol,
                        "symbol": symbol,
                        "name": str(df["name"].iloc[-1]) if "name" in df.columns else symbol,
                        "composite_score": composite,
                        "sector": sector,
                        "factor_values": factors,
                    })

            # 3. 行业中性化(每行业最多3只，行业内部标准化)
            scored = self._industry_neutralize(scored)

            # 4. 按中性化score排序
            scored.sort(key=lambda x: x["composite_score"], reverse=True)
            logger.info(f"有效评分股票: {len(scored)}/{len(stock_data)}, "
                       f"TOP3: {[(s['symbol'], round(s['composite_score'],3)) for s in scored[:3]]}")

            # 4. 生成BUY信号(TOP-N)
            for s in scored[:self.top_n]:
                score = s["composite_score"]
                signals.append({
                    "code": s["code"],
                    "symbol": s["symbol"],
                    "name": s["name"],
                    "side": "BUY",
                    "confidence": round(min(score / 3.0, 1.0), 4),
                    "composite_score": round(score, 4),
                    "weight": 1.0,
                    "reason": f"V25多因子排名 #{scored.index(s)+1}/{len(scored)}, score={round(score,3)}",
                })

            logger.info(f"信号生成: {len(signals)} 条 ({len([s for s in signals if s['side']=='BUY'])}买)")

        except Exception as e:
            logger.error(f"信号生成异常: {e}", exc_info=True)

        return signals

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

    def _load_recent_klines(self, target: pd.Timestamp, lookback: int = 60) -> Dict[str, pd.DataFrame]:
        """批量加载近期K线"""
        import os
        start = target - pd.Timedelta(days=lookback * 2)  # 留余量
        stock_data = {}
        kline_dir = Path(self.KLINE_DIR)

        loaded = 0
        skipped = 0
        for sym in self._symbols:
            try:
                path = kline_dir / f"{sym}.parquet"
                if not path.exists():
                    skipped += 1
                    continue
                df = pd.read_parquet(path)
                if "date" not in df.columns:
                    skipped += 1
                    continue
                df["date"] = pd.to_datetime(df["date"])
                df = df[(df["date"] >= start) & (df["date"] <= target)]
                if len(df) < 20:
                    skipped += 1
                    continue
                stock_data[sym] = df.sort_values("date")
                loaded += 1
            except Exception:
                skipped += 1

        logger.info(f"K线加载: {loaded} OK, {skipped} skip")
        return stock_data

    def _compute_technical_factors(self, df: pd.DataFrame, target: pd.Timestamp, symbol: str = "") -> Optional[Dict[str, float]]:
        """计算所有可计算的技术因子值（标准化后）

        Returns:
            {factor_name: zscore_normalized_value} or None
        """
        try:
            close = df["close"].values.astype(float)
            high = df["high"].values.astype(float)
            low = df["low"].values.astype(float)
            volume = df["volume"].values.astype(float)

            if len(close) < 30:
                return None

            factors = {}
            latest_close = close[-1]

            # --- 动量因子 ---
            factors["mom_5d"] = (latest_close / close[-6] - 1) if len(close) >= 6 else 0
            factors["mom_10d"] = (latest_close / close[-11] - 1) if len(close) >= 11 else 0

            # consistency: 20日内上涨天数占比
            if len(close) >= 21:
                up_days = sum(1 for i in range(-20, 0) if close[i] > close[i-1])
                factors["consistency"] = up_days / 20.0
            else:
                factors["consistency"] = 0.5

            # --- 量价因子 ---
            if len(volume) >= 6:
                avg_vol_5 = np.mean(volume[-6:-1])
                avg_vol_20 = np.mean(volume[-21:-1]) if len(volume) >= 21 else avg_vol_5
                factors["volume_ratio"] = avg_vol_5 / avg_vol_20 if avg_vol_20 > 0 else 1.0

            # money_flow: simplified (close - open) * volume / total_volume
            if len(close) >= 6:
                recent_vol = volume[-5:]
                recent_close = close[-5:]
                recent_open = df["open"].values[-5:].astype(float)
                mf = sum((recent_close[i] - recent_open[i]) * recent_vol[i] for i in range(5))
                total_vol = sum(recent_vol)
                factors["money_flow"] = mf / total_vol if total_vol > 0 else 0
            else:
                factors["money_flow"] = 0

            # --- 波动率因子 ---
            if len(close) >= 21:
                returns = np.diff(close[-21:]) / close[-21:-1]
                factors["volatility_20d"] = np.std(returns)
                factors["daily_sharpe"] = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
            else:
                factors["volatility_20d"] = 0.03
                factors["daily_sharpe"] = 0

            # boll_pos (implied: 20日布林带位置)
            if len(close) >= 20:
                ma20 = np.mean(close[-20:])
                std20 = np.std(close[-20:])
                if std20 > 0:
                    factors["boll_pos"] = (latest_close - ma20) / (2 * std20)
                else:
                    factors["boll_pos"] = 0
            else:
                factors["boll_pos"] = 0

            # rsi_14
            if len(close) >= 15:
                deltas = np.diff(close[-15:])
                gains = np.sum(deltas[deltas > 0])
                losses = -np.sum(deltas[deltas < 0])
                rs = gains / losses if losses > 0 else 100
                factors["rsi_14"] = 100 - (100 / (1 + rs))
            else:
                factors["rsi_14"] = 50

            # turnover_mom: 换手率动量（用成交量近似）
            if len(volume) >= 11:
                factors["turnover_mom"] = np.mean(volume[-5:]) / np.mean(volume[-11:-6]) - 1 if np.mean(volume[-11:-6]) > 0 else 0
            else:
                factors["turnover_mom"] = 0

            # mom_20d
            factors["mom_20d"] = (latest_close / close[-21] - 1) if len(close) >= 21 else 0

            # long_term_mom_60d: 60日收益率(均值反转信号)
            factors["long_term_mom_60d"] = (latest_close / close[-61] - 1) if len(close) >= 61 else 0

            # size_factor: log(price * volume) - 大/小盘风格
            avg_price = np.mean(close[-20:])
            avg_vol_20d_val = np.mean(volume[-20:]) if len(volume) >= 20 else volume[-1]
            factors["size_factor"] = np.log(avg_price * avg_vol_20d_val + 1)

            # --- 另类数据因子（由调用方批量注入，此处跳过）---
            # 保留为占位，实际值在 generate_signals 中注入

            # --- 基本面因子（从parquet中的静态字段或默认值）---
            # pe_ttm/pb_ttm: 用倒数(EP/BP)估值因子
            factors.setdefault("pe_ttm", 0)
            factors.setdefault("pb_ttm", 0)

            # 标准化：Z-score（排除另类因子，它们已经标准化）
            tech_names = ["mom_10d", "mom_20d", "consistency",
                         "volume_ratio", "money_flow", "volatility_20d",
                         "daily_sharpe", "boll_pos", "rsi_14",
                         "turnover_mom", "long_term_mom_60d", "size_factor"]

            # 截尾/缩放，防极端值
            factors["mom_10d"] = np.clip(factors["mom_10d"] * 3, -3, 3)
            factors["mom_20d"] = np.clip(factors["mom_20d"] * 2, -3, 3)
            factors["consistency"] = (factors["consistency"] - 0.5) * 6  # -3~3
            factors["volume_ratio"] = np.clip((factors["volume_ratio"] - 1) * 2, -3, 3)
            factors["money_flow"] = np.clip(factors["money_flow"] * 100, -3, 3)
            factors["volatility_20d"] = np.clip((0.03 - factors["volatility_20d"]) * 100, -3, 3)  # 低波动利好
            factors["daily_sharpe"] = np.clip(factors["daily_sharpe"] * 2, -3, 3)
            factors["boll_pos"] = np.clip(factors["boll_pos"], -3, 3)
            factors["rsi_14"] = (factors["rsi_14"] - 50) / 15  # -3.3~3.3
            factors["turnover_mom"] = np.clip(factors["turnover_mom"] * 3, -3, 3)
            factors["long_term_mom_60d"] = np.clip(factors["long_term_mom_60d"] * 2, -3, 3)  # 反转因子: 涨太多=负
            factors["size_factor"] = np.clip((15 - factors["size_factor"]) / 3, -3, 3)  # 小盘偏好

            return factors

        except Exception as e:
            logger.debug(f"因子计算异常 symbol={df.iloc[-1].get('code','?')}: {e}")
            return None

    def _industry_neutralize(self, scored: List[dict], max_per_sector: int = 3) -> List[dict]:
        """行业中性化：行业内Z-score标准化 + 每行业上限

        1. 同行业内 composite_score → z-score（行业内部对比）
        2. 跨行业排名时用原score+0.5*zscore，保留跨行业差异
        3. 每行业最多max_per_sector只
        """
        if not scored:
            return scored

        # 按行业分组
        sectors = {}
        for s in scored:
            sec = s.get("sector", "其他")
            sectors.setdefault(sec, []).append(s)

        # 行业内z-score标准化，跨行业混合排名
        for sec, stocks in sectors.items():
            if len(stocks) < 2:
                continue
            scores = np.array([s["composite_score"] for s in stocks])
            mu, sigma = np.mean(scores), np.std(scores)
            if sigma == 0:
                continue
            for i, s in enumerate(stocks):
                z = (scores[i] - mu) / sigma
                # 混合: 70%原分+30%行业内z分 → 保留跨行业差异
                s["composite_score"] = s["composite_score"] * 0.7 + z * 0.3

        # 按新分排序
        scored.sort(key=lambda x: x["composite_score"], reverse=True)

        # 每行业上限筛选
        selected = []
        sector_counts = {}
        for s in scored:
            sec = s.get("sector", "其他")
            cnt = sector_counts.get(sec, 0)
            if cnt < max_per_sector or max_per_sector == 0:
                selected.append(s)
                sector_counts[sec] = cnt + 1
            # 不限制总数，由调用方截取top_n

        logger.info(f"行业中性化: {len(sectors)}行业, {len(scored)}→{len(selected)}只"
                   f" (每行业≤{max_per_sector})")
        return selected

    def _get_alternative_factors(self, symbol: str) -> Dict[str, float]:
        """从缓存获取另类因子（快速路径，不重新采集）"""
        try:
            if self._alt_collector:
                results = self._alt_collector.compute_factors([symbol], target_date=None)
                if symbol in results:
                    return results[symbol]
        except Exception:
            pass
        return {
            "northbound_net_buy": 0,
            "northbound_holding_chg": 0,
            "margin_balance_chg": 0,
            "margin_buy_ratio": 0,
            "industry_revenue_growth": 0,
            "industry_profit_growth": 0,
            "industry_pmi": 0,
        }

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
