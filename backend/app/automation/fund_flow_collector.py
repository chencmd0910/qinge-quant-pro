"""
资金流因子采集器 — 东方财富大单追踪数据

数据源: akshare stock_fund_flow_big_deal
缓存: /app/data/fund_flow/fund_flow.parquet (增量)

因子:
  - fund_flow_net_5d:      5日大单净买入量 / 总大单量 (标准化-3~3)
  - fund_flow_buy_ratio_5d: 5日大单买入笔数占比 (0~1→-3~3)
  - fund_flow_avg_size_5d:  5日均笔成交额 / 20日均值 (缩量/放量)
  - fund_flow_streak:       连续买入/卖出趋势强度
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger("FundFlowCollector")

# 路径
ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = ROOT / "data" / "fund_flow"


class FundFlowCollector:
    """资金流数据采集 + 因子计算"""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Optional[pd.DataFrame] = None

    # -------- 数据采集 --------

    def collect(self, force: bool = False) -> pd.DataFrame:
        """采集今日大单数据"""
        import time
        cache_file = self.data_dir / "big_deal.parquet"
        today_str = datetime.now().strftime("%Y-%m-%d")

        if not force and cache_file.exists():
            self._cache = pd.read_parquet(cache_file)
            max_date = str(self._cache["date"].max())
            if max_date >= today_str:
                logger.info(f"资金流已采集到{max_date}，跳过")
                return self._cache

        try:
            import akshare as ak
            df = ak.stock_fund_flow_big_deal()
            if df is None or len(df) == 0:
                logger.warning("资金流API返回空")
                return self._load_cache_or_empty()

            # 字段映射
            df = df.rename(columns={
                "成交时间": "time",
                "股票代码": "code",
                "股票简称": "name",
                "成交价格": "price",
                "成交量": "volume",
                "成交额": "amount",
                "大单性质": "side",  # 买盘/卖盘/中性盘
                "涨跌幅": "change_pct",
                "涨跌额": "change_amt",
            })

            df["date"] = today_str
            df["code"] = df["code"].astype(str).str.zfill(6)
            df["price"] = pd.to_numeric(df["price"], errors="coerce")
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce") / 100  # 转为手
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
            df["is_buy"] = df["side"].str.contains("买盘", na=False).astype(int)
            df["is_sell"] = df["side"].str.contains("卖盘", na=False).astype(int)
            df["side_value"] = 0
            df.loc[df["is_buy"] == 1, "side_value"] = 1
            df.loc[df["is_sell"] == 1, "side_value"] = -1

            # 合并历史
            if cache_file.exists():
                hist = pd.read_parquet(cache_file)
                hist["date"] = hist["date"].astype(str)
                df = pd.concat([hist, df], ignore_index=True)
                # 去重
                df = df.drop_duplicates(subset=["date", "time", "code", "price", "volume"])

            df.to_parquet(cache_file, index=False)
            self._cache = df
            logger.info(f"资金流采集: {len(df[df['date']==today_str])}条今日, 总计{len(df)}条")
            return df

        except Exception as e:
            logger.error(f"资金流采集失败: {e}")
            return self._load_cache_or_empty()

    def _load_cache_or_empty(self) -> pd.DataFrame:
        cache_file = self.data_dir / "big_deal.parquet"
        if cache_file.exists():
            self._cache = pd.read_parquet(cache_file)
            return self._cache
        return pd.DataFrame()

    # -------- 因子计算 --------

    def compute_factors(self, symbols: List[str], target_date: str = None,
                        lookback: int = 5) -> Dict[str, Dict[str, float]]:
        """计算个股资金流因子

        Args:
            symbols: 股票代码列表
            target_date: 目标日期(默认最近)
            lookback: 回看天数

        Returns:
            {symbol: {factor_name: value}}
        """
        if self._cache is None:
            cache_file = self.data_dir / "big_deal.parquet"
            if cache_file.exists():
                self._cache = pd.read_parquet(cache_file)
            else:
                logger.warning("资金流缓存不存在，返回空因子")
                return {s: self._default_factors() for s in symbols}

        df = self._cache.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["code"] = df["code"].astype(str).str.zfill(6)

        if target_date:
            target_dt = pd.Timestamp(target_date)
        else:
            target_dt = df["date"].max()
            if pd.isna(target_dt):
                return {s: self._default_factors() for s in symbols}

        # 全局统计(用于z-score)
        all_codes = df["code"].unique()

        results = {}
        for symbol in symbols:
            sym = str(symbol).zfill(6)
            results[sym] = self._compute_single(df, sym, target_dt, lookback, all_codes)

        logger.info(f"资金流因子: {len(results)}只股票")
        return results

    def _compute_single(self, df: pd.DataFrame, symbol: str,
                        target_dt: pd.Timestamp, lookback: int,
                        all_codes: np.ndarray) -> Dict[str, float]:
        """单只股票资金流因子"""
        start = target_dt - pd.Timedelta(days=lookback * 3)
        stock_df = df[(df["code"] == symbol) & (df["date"] >= start) & (df["date"] <= target_dt)]

        if len(stock_df) < 10:
            return self._default_factors()

        # 逐日聚合
        daily = stock_df.groupby("date").agg(
            buy_vol=("volume", lambda x: (x * stock_df.loc[x.index, "is_buy"]).sum()),
            sell_vol=("volume", lambda x: (x * stock_df.loc[x.index, "is_sell"]).sum()),
            buy_cnt=("is_buy", "sum"),
            sell_cnt=("is_sell", "sum"),
            total_amount=("amount", "sum"),
            deal_count=("volume", "count"),
        ).reset_index()

        daily["net_vol"] = daily["buy_vol"] - daily["sell_vol"]
        daily["total_vol"] = daily["buy_vol"] + daily["sell_vol"]
        daily["net_ratio"] = np.where(daily["total_vol"] > 0,
                                       daily["net_vol"] / daily["total_vol"], 0)
        daily["buy_ratio"] = np.where((daily["buy_cnt"] + daily["sell_cnt"]) > 0,
                                       daily["buy_cnt"] / (daily["buy_cnt"] + daily["sell_cnt"]),
                                       0.5)
        daily["avg_amount"] = daily["total_amount"] / daily["deal_count"].clip(lower=1)

        # 取最近lookback天
        daily = daily.sort_values("date").tail(lookback)

        if len(daily) == 0:
            return self._default_factors()

        # 因子1: 净买入占比 (标准化) - 用所有可用天数的均值
        net_ratio = float(daily["net_ratio"].mean())
        fund_flow_net_5d = np.clip(net_ratio * 5, -3, 3)

        # 因子2: 买入笔数比
        buy_ratio = float(daily["buy_ratio"].mean())
        fund_flow_buy_ratio = np.clip((buy_ratio - 0.5) * 6, -3, 3)

        # 因子3: 均笔成交额趋势
        avg_amt = float(daily["avg_amount"].mean())
        # 与全局均值比
        global_avg = float(stock_df["amount"].mean()) if len(stock_df) > 0 else avg_amt
        fund_flow_avg_size = np.clip(np.log(avg_amt / max(global_avg, 1)), -3, 3)

        # 因子4: 买入趋势方向(单日用净方向,多日用streak)
        daily_sorted = daily.sort_values("date")
        if len(daily_sorted) >= 2:
            net_direction = np.sign(daily_sorted["net_vol"].values)
            streak = 0
            for d in reversed(net_direction):
                if d > 0:
                    streak += 1
                elif d < 0:
                    streak -= 1
                else:
                    break
        else:
            streak = np.sign(daily_sorted["net_vol"].values[-1]) if len(daily_sorted) > 0 else 0
        fund_flow_streak = np.clip(streak * 0.5, -3, 3)

        return {
            "fund_flow_net_5d": round(fund_flow_net_5d, 4),
            "fund_flow_buy_ratio": round(fund_flow_buy_ratio, 4),
            "fund_flow_avg_size_5d": round(fund_flow_avg_size, 4),
            "fund_flow_streak": round(fund_flow_streak, 4),
        }

    def _default_factors(self) -> Dict[str, float]:
        return {
            "fund_flow_net_5d": 0.0,
            "fund_flow_buy_ratio": 0.0,
            "fund_flow_avg_size_5d": 0.0,
            "fund_flow_streak": 0.0,
        }
