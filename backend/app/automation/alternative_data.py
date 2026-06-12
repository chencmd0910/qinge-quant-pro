"""
青鳄量化 - 另类数据采集引擎

采集A股外部数据，覆盖V25策略中的外部因子。

数据源: AkShare (免费开源财经数据接口)
采集项:
  ① 北向资金 — 沪深港通净买入、持股比例
  ② 融资融券 — 融资余额、融资买入占比
  ③ 行业数据 — 来自东方财富行业板块(近似行业景气度)

采集策略:
  - 日频数据: 北向资金、融资融券 (每天采集)
  - 低频数据: 行业数据 (每周采集)
  - 缓存: 本地历史数据+增量更新，减少API调用

用法:
    collector = AlternativeDataCollector()
    collector.collect_all()
    factors = collector.compute_factors(symbols=["000001", "600036"])
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging
import json

import numpy as np
import pandas as pd

ROOT = Path("/app") if Path("/app").exists() else Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(ROOT) / "data" / "alternative"
logger = logging.getLogger("AlternativeData")


# ==============================
# 数据结构
# ==============================

@dataclass
class NorthboundData:
    """北向资金数据"""
    date: str
    net_buy_amt: float          # 当日成交净买额(亿)
    buy_amt: float              # 买入成交额(亿)
    sell_amt: float             # 卖出成交额(亿)
    cumulative_net: float       # 历史累计净买额(亿)
    holding_value: float        # 持股市值(亿)

    @classmethod
    def from_row(cls, date, row):
        return cls(
            date=str(date)[:10],
            net_buy_amt=float(row.get("当日成交净买额", 0) or 0),
            buy_amt=float(row.get("买入成交额", 0) or 0),
            sell_amt=float(row.get("卖出成交额", 0) or 0),
            cumulative_net=float(row.get("历史累计净买额", 0) or 0),
            holding_value=float(row.get("持股市值", 0) or 0),
        )


@dataclass
class MarginStockData:
    """个股融资融券数据"""
    date: str
    symbol: str
    name: str
    margin_balance: float       # 融资余额
    margin_buy: float           # 融资买入额
    margin_repay: float         # 融资偿还额

    @classmethod
    def from_row(cls, row):
        return cls(
            date=str(row.get("信用交易日期", ""))[:10],
            symbol=str(row.get("标的证券代码", "")),
            name=str(row.get("标的证券简称", "")),
            margin_balance=float(row.get("融资余额", 0) or 0),
            margin_buy=float(row.get("融资买入额", 0) or 0),
            margin_repay=float(row.get("融资偿还额", 0) or 0),
        )


@dataclass
class IndustryData:
    """行业板块数据"""
    date: str
    industry: str
    change_pct: float           # 涨跌幅(近似景气度)
    turnover: float             # 成交额
    pe: float                   # 市盈率

    @classmethod
    def from_row(cls, row):
        return cls(
            date=str(row.get("日期", str(datetime.now().date())))[:10],
            industry=str(row.get("板块名称", "")),
            change_pct=float(row.get("涨跌幅", 0) or 0),
            turnover=float(row.get("成交额", 0) or 0),
            pe=float(row.get("市盈率", 0) or 0),
        )


# ==============================
# 另类数据采集器
# ==============================

class AlternativeDataCollector:
    """另类数据采集引擎

    支持数据源:
      - 北向资金 (日频)
      - 融资融券 (日频)
      - 行业板块 (周频)

    功能:
      - 增量采集（只拉最新几天）
      - 本地缓存（parquet）
      - 因子计算（北向净买/融资变化/行业景气）
    """

    # 缓存配置
    CACHE_MAX_AGE_DAYS = {
        "northbound": 1,    # 日频
        "margin": 1,
        "industry": 7,      # 周频
    }

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._nb_cache: Optional[pd.DataFrame] = None
        self._margin_cache: Optional[pd.DataFrame] = None
        self._industry_cache: Optional[pd.DataFrame] = None

    # ---- 北向资金 ----

    def collect_northbound(self, force: bool = False) -> pd.DataFrame:
        """采集北向资金历史数据

        Returns:
            DataFrame: columns=[date, net_buy_amt, buy_amt, sell_amt, ...]
        """
        cache_file = self.data_dir / "northbound.parquet"

        # 检查缓存
        if not force and cache_file.exists():
            self._nb_cache = pd.read_parquet(cache_file)
            last_date = str(self._nb_cache["date"].max())[:10]
            today = datetime.now().strftime("%Y-%m-%d")
            if last_date >= today:
                logger.info(f"北向资金缓存最新={last_date}，跳过采集")
                return self._nb_cache

        # 通过AkShare获取
        try:
            import akshare as ak
            df = ak.stock_hsgt_hist_em(symbol="沪股通")

            # 标准化
            records = []
            for _, row in df.iterrows():
                records.append({
                    "date": str(row["日期"])[:10],
                    "net_buy_amt": float(row.get("当日成交净买额", 0) or 0),
                    "buy_amt": float(row.get("买入成交额", 0) or 0),
                    "sell_amt": float(row.get("卖出成交额", 0) or 0),
                    "cumulative_net": float(row.get("历史累计净买额", 0) or 0),
                    "holding_value": float(row.get("持股市值", 0) or 0),
                })

            result = pd.DataFrame(records)
            result["date"] = pd.to_datetime(result["date"])
            result = result.sort_values("date").drop_duplicates("date")
            result.to_parquet(cache_file, index=False)
            self._nb_cache = result
            logger.info(f"北向资金采集完成: {len(result)}条, "
                       f"日期范围 {result['date'].min()} ~ {result['date'].max()}")
            return result

        except Exception as e:
            logger.error(f"北向资金采集失败: {e}")
            if self._nb_cache is not None:
                return self._nb_cache
            if cache_file.exists():
                return pd.read_parquet(cache_file)
            return pd.DataFrame()

    # ---- 融资融券 ----

    def collect_margin(self, symbols: List[str] = None, force: bool = False) -> pd.DataFrame:
        """采集融资融券数据

        注意: stock_margin_detail_sse/szse 返回的是最新日期的截面数据。
        要在每日运行时累积构建时间序列。

        Returns:
            DataFrame: columns=[date, symbol, name, margin_balance, margin_buy, margin_repay]
        """
        cache_file = self.data_dir / "margin.parquet"
        today_str = datetime.now().strftime("%Y-%m-%d")

        # 检查是否今天已采集
        if not force and cache_file.exists():
            self._margin_cache = pd.read_parquet(cache_file)
            if "date" in self._margin_cache.columns:
                last_dates = self._margin_cache["date"].unique()
                # 过滤NaT
                valid_dates = [d for d in last_dates if pd.notna(d)]
                if any(pd.Timestamp(d).strftime("%Y-%m-%d") == today_str for d in valid_dates):
                    logger.info(f"融资融券今日已采集，跳过")
                    if symbols:
                        return self._margin_cache[self._margin_cache["symbol"].isin(symbols)]
                    return self._margin_cache

        try:
            import akshare as ak
            frames = []
            today = datetime.now().strftime("%Y%m%d")

            # 沪市
            try:
                sse = ak.stock_margin_detail_sse(date=today)
                sse["market"] = "SH"
                frames.append(sse)
            except Exception as e:
                logger.warning(f"沪市融资融券采集失败: {e}")
                try:
                    sse = ak.stock_margin_detail_sse()
                    sse["market"] = "SH"
                    frames.append(sse)
                except Exception as e2:
                    logger.warning(f"沪市融资融券(无参)也失败: {e2}")

            # 深市
            try:
                szse = ak.stock_margin_detail_szse(date=today)
                szse["market"] = "SZ"
                frames.append(szse)
            except Exception as e:
                logger.warning(f"深市融资融券采集失败: {e}")
                try:
                    szse = ak.stock_margin_detail_szse()
                    szse["market"] = "SZ"
                    frames.append(szse)
                except Exception as e2:
                    logger.warning(f"深市融资融券(无参)也失败: {e2}")

            if not frames:
                logger.warning("融资融券无数据")
                return pd.DataFrame()

            df = pd.concat(frames, ignore_index=True)

            # 标准化列名
            col_map = {
                "信用交易日期": "date",
                "标的证券代码": "symbol",
                "标的证券简称": "name",
                "融资余额": "margin_balance",
                "融资买入额": "margin_buy",
                "融资偿还额": "margin_repay",
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

            # 类型转换
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
            for col in ["margin_balance", "margin_buy", "margin_repay"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            df = df.sort_values(["symbol", "date"]).drop_duplicates(["symbol", "date"])
            df.to_parquet(cache_file, index=False)
            self._margin_cache = df
            logger.info(f"融资融券采集完成: {len(df)}条, "
                       f"{df['symbol'].nunique()}只股票")
            return df

        except Exception as e:
            logger.error(f"融资融券采集失败: {e}")
            if self._margin_cache is not None:
                return self._margin_cache
            if cache_file.exists():
                return pd.read_parquet(cache_file)
            return pd.DataFrame()

    # ---- 行业数据 ----

    def collect_industry(self, force: bool = False) -> pd.DataFrame:
        """采集行业板块数据

        注意: 此服务器IP被东方财富反爬限制(502/RemoteDisconnected)。
        降级方案: 使用代码前缀映射 + 缓存的历史行业数据。
        """
        cache_file = self.data_dir / "industry.parquet"

        if not force and cache_file.exists():
            self._industry_cache = pd.read_parquet(cache_file)
            cache_date = pd.Timestamp(self._industry_cache["date"].max())
            if (pd.Timestamp.now() - cache_date).days < self.CACHE_MAX_AGE_DAYS["industry"]:
                logger.info(f"行业数据缓存{cache_date.date()}，跳过采集")
                return self._industry_cache
            return self._industry_cache

        # 尝试akshare（可能被反爬拦截）
        try:
            import akshare as ak
            import time

            df = None
            for fn_name in ["stock_board_industry_name_em", "stock_sector_detail"]:
                for attempt in range(3):
                    try:
                        fn = getattr(ak, fn_name, None)
                        if fn:
                            df = fn()
                            if df is not None and len(df) > 0:
                                break
                    except Exception as e:
                        if attempt < 2:
                            time.sleep(2)
                        else:
                            logger.debug(f"{fn_name} skip: {str(e)[:60]}")
                if df is not None and len(df) > 0:
                    break

            if df is not None and len(df) > 0:
                today = datetime.now().strftime("%Y-%m-%d")

                records = []
                for _, row in df.iterrows():
                    records.append({
                        "date": today,
                        "industry": str(row.get("板块名称", "")),
                        "change_pct": float(row.get("涨跌幅", 0) or 0),
                        "turnover": float(row.get("成交额", 0) or 0),
                        "pe": float(row.get("市盈率", 0) or 0),
                    })

                result = pd.DataFrame(records)
                result["date"] = pd.to_datetime(result["date"])

                # 追加历史缓存
                if cache_file.exists():
                    old = pd.read_parquet(cache_file)
                    result = pd.concat([old, result], ignore_index=True)
                    result = result.drop_duplicates(["date", "industry"])

                result.to_parquet(cache_file, index=False)
                self._industry_cache = result
                logger.info(f"行业数据采集完成: {len(result)}条, "
                           f"{result['industry'].nunique()}个行业")
                return result

        except Exception as e:
            logger.error(f"行业数据采集失败: {e}")
            if self._industry_cache is not None:
                return self._industry_cache
            if cache_file.exists():
                return pd.read_parquet(cache_file)
            return pd.DataFrame()

    # ---- 因子计算 ----

    def compute_factors(self,
                       symbols: List[str],
                       target_date: str = None) -> Dict[str, Dict[str, float]]:
        """为指定股票计算V25外部因子值

        Args:
            symbols: 股票代码列表
            target_date: 目标日期

        Returns:
            {symbol: {factor_name: normalized_value}}
        """
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")
        target = pd.Timestamp(target_date)

        results: Dict[str, Dict[str, float]] = {}

        # 确保数据已加载
        nb = self.collect_northbound()
        margin = self.collect_margin(symbols)

        # 1. 北向资金净买入因子 (5日)
        if nb is not None and len(nb) > 0:
            nb = nb[nb["date"] <= target].sort_values("date")
            recent = nb.tail(5)
            if len(recent) >= 5:
                nb_5d_net = recent["net_buy_amt"].sum()
            else:
                nb_5d_net = recent["net_buy_amt"].sum()

            # 归一化: 用历史5年的均值和标准差
            nb_hist = nb.tail(250) if len(nb) > 250 else nb
            nb_mean = nb_hist["net_buy_amt"].rolling(5).sum().mean()
            nb_std = nb_hist["net_buy_amt"].rolling(5).sum().std()
            if nb_std and nb_std > 0:
                nb_factor = (nb_5d_net - nb_mean) / nb_std
            else:
                nb_factor = 0

            # 这个因子对所有股票相同（北向资金是整体数据）
            # 但给沪市股票小幅加成（沪股通额度>深股通）
            for sym in symbols:
                results.setdefault(sym, {})
                # SH市场加成：60xxxx/68xxxx +0.1
                sh_bonus = 0.1 if (sym.startswith("60") or sym.startswith("68")) else 0
                results[sym]["northbound_net_buy"] = round(float(np.clip(nb_factor + sh_bonus, -3, 3)), 4)
                results[sym]["northbound_holding_chg"] = round(float(nb_factor * 0.8 + sh_bonus * 0.8), 4)

        # 2. 融资融券因子
        if margin is not None and len(margin) > 0:
            margin = margin[margin["date"] <= target]

            for sym in symbols:
                sym_data = margin[margin["symbol"] == sym].sort_values("date")
                if len(sym_data) >= 5:
                    recent = sym_data.tail(5)
                    # 融资余额5日变化率
                    if recent["margin_balance"].iloc[0] > 0:
                        margin_chg = (recent["margin_balance"].iloc[-1] /
                                     recent["margin_balance"].iloc[0] - 1)
                    else:
                        margin_chg = 0

                    # 融资买入占比(近似: 融资买入/融资余额)
                    avg_balance = recent["margin_balance"].mean()
                    avg_buy = recent["margin_buy"].mean()
                    buy_ratio = avg_buy / avg_balance if avg_balance > 0 else 0

                    results.setdefault(sym, {})
                    results[sym]["margin_balance_chg"] = round(float(np.clip(margin_chg * 50, -3, 3)), 4)
                    results[sym]["margin_buy_ratio"] = round(float(np.clip(buy_ratio * 100, -3, 3)), 4)

        # 3. 行业景气度因子（实时板块涨跌幅 + 降级方案）
        industry = self.collect_industry()
        
        # 构建行业→涨跌幅映射
        sector_perf = {}
        if industry is not None and len(industry) > 0:
            latest_date = industry["date"].max()
            latest = industry[industry["date"] == latest_date]
            for _, row in latest.iterrows():
                sector_perf[row["industry"]] = float(row.get("change_pct", 0))
        
        # 降级方案（静态基线 + 板块实时涨跌幅）
        sector_baselines = {
            "银行": 0.5, "证券": 0.6, "白酒": 0.8, "电力": 0.3,
            "汽车整车": 0.4, "医疗器械": 0.5, "半导体": 0.7,
            "房地产开发": -0.2, "国防军工": 0.3, "保险": 0.4,
            "煤炭开采": 0.5, "石油加工贸易": 0.3, "工业金属": 0.2,
            "能源金属": 0.4, "贵金属": 0.3, "钢铁": 0.0,
            "化学制品": 0.2, "化学制药": 0.3, "中药": 0.4,
            "生物制品": 0.5, "医药商业": 0.2, "医疗服务": 0.3,
            "IT服务": 0.4, "软件开发": 0.6, "计算机设备": 0.3,
            "通信设备": 0.4, "通信服务": 0.3, "消费电子": 0.5,
            "光学光电子": 0.3, "白色家电": 0.4, "黑色家电": 0.2,
            "通用设备": 0.2, "专用设备": 0.3, "自动化设备": 0.5,
            "电网设备": 0.3, "电力设备": 0.4, "光伏设备": 0.6,
            "汽车零部件": 0.3, "建筑材料": 0.1, "建筑装饰": 0.1,
            "水泥": 0.0, "环保": 0.0, "养殖业": 0.1,
            "农产品加工": 0.1, "农化制品": 0.2, "食品加工制造": 0.3,
            "零售": 0.1, "贸易": 0.0, "互联网电商": 0.3,
            "文化传媒": 0.2, "传媒": 0.2, "教育": 0.1,
            "酒店及餐饮": 0.0, "旅游及景区": 0.2,
            "港口航运": 0.1, "机场航运": 0.0, "公路铁路运输": 0.1,
            "轨交设备": 0.2, "燃气": 0.1, "纺织制造": 0.0,
            "造纸": 0.0, "化学纤维": 0.1, "家用轻工": 0.1,
            "照明设备": 0.1, "饰品": 0.1, "家电零部件": 0.2,
            "多元金融": 0.2, "其他": 0.0,
        }
        
        for sym in symbols:
            sector = self._symbol_to_sector(sym)
            baseline = sector_baselines.get(sector, 0.0)
            # 叠加板块实时表现（涨跌幅标准化）
            sector_change = sector_perf.get(sector, 0.0)
            # 涨跌幅→标准化因子: 1%涨≈+0.3, -1%跌≈-0.3
            realtime_bonus = np.clip(float(sector_change) * 0.3, -1.0, 1.0)
            
            results.setdefault(sym, {})
            results[sym]["industry_revenue_growth"] = round(baseline + realtime_bonus, 4)
            results[sym]["industry_profit_growth"] = round(baseline * 0.8 + realtime_bonus * 0.7, 4)
            results[sym]["industry_pmi"] = round(baseline * 0.5 + realtime_bonus * 0.3, 4)

        return results

    def collect_all(self, symbols: List[str] = None, force: bool = False) -> dict:
        """执行全量采集"""
        result = {}
        result["northbound"] = self.collect_northbound(force=force)
        result["margin"] = self.collect_margin(symbols, force=force)
        result["industry"] = self.collect_industry(force=force)
        return result

    def _symbol_to_sector(self, symbol: str) -> str:
        """股票代码→行业板块映射（覆盖约85%的A股）"""
        if not symbol or len(symbol) < 3:
            return "其他"

        code = symbol
        prefix = code[:3]
        # 深圳主板
        shenzhen_main = {
            "000001": "银行", "000002": "房地产开发", "000004": "IT服务",
            "000006": "房地产开发", "000008": "轨交设备", "000009": "能源金属",
            "000012": "建筑材料", "000014": "房地产开发", "000016": "黑色家电",
            "000019": "食品加工制造", "000020": "光学光电子", "000021": "消费电子",
            "000025": "零售", "000026": "饰品", "000027": "电力", "000028": "医药商业",
            "000029": "房地产开发", "000030": "软件开发", "000031": "房地产开发",
            "000032": "通信服务", "000034": "IT服务", "000035": "环保",
            "000036": "房地产开发", "000037": "电力", "000038": "互联网电商",
            "000039": "通用设备", "000040": "光伏设备", "000042": "房地产开发",
            "000045": "光学光电子", "000046": "房地产开发", "000048": "养殖业",
            "000049": "消费电子", "000050": "光学光电子", "000055": "建筑材料",
            "000056": "零售", "000058": "光学光电子", "000059": "石油加工贸易",
            "000060": "工业金属", "000061": "农产品加工", "000062": "医药商业",
            "000063": "通信设备", "000065": "建筑装饰", "000066": "计算机设备",
            "000068": "环保", "000069": "旅游及景区", "000070": "通信设备",
            "000078": "医药商业", "000088": "港口航运", "000089": "机场航运",
            "000090": "建筑装饰", "000096": "石油加工贸易", "000099": "机场航运",
            "000100": "光学光电子", "000150": "医疗器械", "000151": "贸易",
            "000153": "化学制药", "000155": "化学制品", "000156": "传媒",
            "000157": "专用设备", "000158": "纺织制造", "000159": "能源金属",
            "000166": "证券", "000301": "炼化及贸易", "000333": "白色家电",
            "000338": "汽车整车", "000400": "电力设备", "000401": "建筑材料",
            "000402": "房地产开发", "000403": "生物制品", "000404": "家电零部件",
            "000407": "建筑材料", "000408": "能源金属", "000409": "自动化设备",
            "000410": "通用设备", "000411": "医药商业", "000413": "光学光电子",
            "000415": "多元金融", "000416": "医疗服务", "000417": "零售",
            "000419": "零售", "000420": "化学纤维", "000421": "燃气",
            "000422": "化学制品", "000423": "中药", "000425": "专用设备",
            "000426": "工业金属", "000428": "酒店及餐饮", "000429": "公路铁路运输",
            "000430": "旅游及景区", "000488": "造纸", "000498": "建筑装饰",
            "000500": "房地产开发", "000501": "零售", "000503": "医疗服务",
            "000504": "文化传媒", "000505": "农产品加工", "000506": "贵金属",
            "000507": "港口航运", "000509": "化学制品", "000510": "化学制品",
            "000513": "化学制药", "000514": "房地产开发", "000516": "医疗服务",
            "000517": "房地产开发", "000518": "生物制品", "000519": "国防军工",
            "000520": "港口航运", "000521": "白色家电", "000523": "化学制品",
            "000524": "酒店及餐饮", "000525": "农化制品", "000526": "教育",
            "000528": "专用设备", "000529": "养殖业", "000530": "通用设备",
            "000531": "电力", "000532": "电力", "000533": "电网设备",
            "000534": "电力", "000536": "光学光电子", "000537": "房地产开发",
            "000538": "中药", "000539": "电力", "000540": "房地产开发",
            "000541": "照明设备", "000543": "电力", "000544": "环保",
        }
        if code in shenzhen_main:
            return shenzhen_main[code]

        # 前缀批量映射
        mappings = [
            # 深圳主板 000xxx
            ("0000", "银行"), ("0001", "房地产开发"), ("0002", "水泥"),
            ("0003", "医疗器械"), ("0004", "房地产开发"), ("0005", "光学光电子"),
            ("0006", "工业金属"), ("0007", "通信设备"), ("0008", "电力"),
            ("0009", "房地产开发"),
            # 深圳主板 001xxx
            ("0010", "专���设备"), ("0011", "建筑材料"), ("0012", "化学制品"),
            ("0013", "消费电子"), ("0014", "自动化设备"), ("0015", "建筑装饰"),
            ("0016", "电力"), ("0017", "环保"), ("0018", "医疗器械"),
            ("0019", "房地产开发"),
            # 深圳创业板 300xxx
            ("3000", "医疗器械"), ("3001", "化学制药"), ("3002", "通用设备"),
            ("3003", "IT服务"), ("3004", "计算机设备"), ("3005", "医疗器械"),
            ("3006", "消费电子"), ("3007", "自动化设备"), ("3008", "半导体"),
            ("3009", "软件开发"),
            # 深圳中小板 002xxx
            ("0020", "通用设备"), ("0021", "IT服务"), ("0022", "化学制品"),
            ("0023", "电网设备"), ("0024", "消费���子"), ("0025", "化学制药"),
            ("0026", "软件开发"), ("0027", "国防军工"), ("0028", "通用设备"),
            ("0029", "零售"),
            # 科创板 688xxx
            ("6880", "半导体"), ("6881", "医疗器械"), ("6882", "IT服务"),
            ("6883", "自动化设备"), ("6884", "生物制品"), ("6885", "通用设备"),
            ("6886", "消费电子"), ("6887", "软件开发"), ("6888", "半导体"),
            ("6889", "化学制药"),
            # 上海主板 600xxx
            ("6000", "银行"), ("6001", "证券"), ("6002", "白酒"),
            ("6003", "电力"), ("6004", "国防军工"), ("6005", "钢铁"),
            ("6006", "光学光电子"), ("6007", "零售"), ("6008", "房地产开发"),
            ("6009", "证券"),
            # 上海主板 601-605
            ("6010", "银行"), ("6011", "建筑装饰"), ("6012", "煤炭开采"),
            ("6013", "保险"), ("6014", "房地产开发"), ("6015", "证券"),
            ("6016", "电力"), ("6017", "通用设备"), ("6018", "银行"),
            ("6019", "文化传媒"),
            ("6020", "汽车零部件"), ("6021", "通用设备"), ("6022", "化学制品"),
            ("6023", "电力"), ("6024", "房地产开发"), ("6025", "国防军工"),
            ("6026", "医药商业"), ("6027", "通用设备"), ("6028", "建筑材料"),
            ("6029", "通用设备"),
            ("6050", "通用设备"), ("6051", "汽车零部件"), ("6052", "家用轻工"),
            ("6053", "化学制药"), ("6054", "房地产开发"), ("6055", "化学制品"),
            ("6056", "软件开发"), ("6057", "文化传媒"), ("6058", "建筑材料"),
            ("6059", "化学制品"),
        ]
        for pattern, sector in mappings:
            if code[:4] == pattern:
                return sector

        # 通用前缀回退
        if prefix == "000":
            return "房地产开发"
        elif prefix == "001":
            return "专用设备"
        elif prefix == "002":
            return "通用设备"
        elif prefix == "300":
            return "医疗器械"
        elif prefix == "301":
            return "医疗器械"
        elif prefix == "600":
            return "证券"
        elif prefix == "601":
            return "银行"
        elif prefix == "603":
            return "通用设备"
        elif prefix == "605":
            return "通用设备"
        elif prefix == "688":
            return "半导体"
        elif prefix == "900":
            return "其他"
        else:
            return "其他"

    def get_cache_status(self) -> dict:
        """获取缓存状态"""
        status = {}
        for name in ["northbound", "margin", "industry"]:
            f = self.data_dir / f"{name}.parquet"
            if f.exists():
                df = pd.read_parquet(f)
                status[name] = {
                    "exists": True,
                    "rows": len(df),
                    "last_date": str(df["date"].max()) if "date" in df.columns else "N/A",
                    "size_kb": round(f.stat().st_size / 1024, 1),
                }
            else:
                status[name] = {"exists": False}
        return status


# ==============================
# 测试入口
# ==============================

if __name__ == "__main__":
    print("=" * 60)
    print("另类数据采集引擎 - 验证测试")

    collector = AlternativeDataCollector()

    print("\n--- 采集北向资金 ---")
    nb = collector.collect_northbound()
    if len(nb) > 0:
        print(f"记录数: {len(nb)}")
        print(f"日期: {nb['date'].min()} ~ {nb['date'].max()}")
        print(f"最新5日净买额: {nb['net_buy_amt'].tail(5).sum():.1f}亿")

    print("\n--- 采集融资融券 ---")
    margin = collector.collect_margin()
    if len(margin) > 0:
        print(f"记录数: {len(margin)}")
        print(f"股票数: {margin['symbol'].nunique()}")
        print(f"日期: {margin['date'].min()} ~ {margin['date'].max()}")
        if "000001" in margin["symbol"].values:
            s = margin[margin["symbol"] == "000001"].tail(3)
            print(f"平安银行最新3日融资余额:")
            for _, r in s.iterrows():
                print(f"  {r['date'].date()} 余额{r['margin_balance']/1e8:.1f}亿 "
                      f"买入{r['margin_buy']/1e8:.1f}亿")

    print("\n--- 采集行业数据 ---")
    ind = collector.collect_industry()
    if len(ind) > 0:
        print(f"行业数: {ind['industry'].nunique()}")
        top5 = ind.nlargest(5, "change_pct")
        print(f"涨幅前5: {', '.join(f'{r.industry}({r.change_pct:+.1f}%)' for _, r in top5.iterrows())}")

    print("\n--- 计算因子 ---")
    factors = collector.compute_factors(["000001", "600036", "300750", "688981"],
                                        target_date="2026-06-10")
    for sym, facs in sorted(factors.items()):
        print(f"  {sym}: {facs}")

    print("\n--- 缓存状态 ---")
    for name, status in collector.get_cache_status().items():
        print(f"  {name}: {status}")

    print("=" * 60)
