"""
市场数据微服务 - 基于 akshare，带缓存+定时刷新
部署在阿里云服务器上，本地前端通过 HTTP 调用
"""
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional

import akshare as ak
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("market_data")

app = FastAPI(title="青鳄量化 市场数据服务", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ==================== 缓存 ====================
CACHE_TTL = 300  # 5 minutes
_cache: dict = {}
_cache_time: dict = {}
_lock = threading.Lock()


def _is_fresh(key: str) -> bool:
    return key in _cache_time and (time.time() - _cache_time[key]) < CACHE_TTL


def _get_cached(key: str):
    with _lock:
        return _cache.get(key) if _is_fresh(key) else None


def _set_cache(key: str, data, ttl: int = None):
    with _lock:
        _cache[key] = data
        _cache_time[key] = time.time()


# ==================== 数据源 ====================
INDEX_SYMBOLS = {
    "上证指数": "sh000001",
    "深证成指": "sz399001",
    "创业板指": "sz399006",
    "科创50": "sh000688",
    "沪深300": "sh000300",
    "中证500": "sh000905",
}


def _fetch_indexes():
    """获取主要指数行情"""
    try:
        result = []
        for name, symbol in INDEX_SYMBOLS.items():
            df = ak.stock_zh_index_daily_em(symbol=symbol)
            if df is None or df.empty:
                continue
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            change_pct = round(float(latest["close"]) / float(prev["close"]) * 100 - 100, 2)

            result.append({
                "name": name,
                "symbol": symbol,
                "price": round(float(latest["close"]), 2),
                "change_pct": change_pct,
                "volume": int(latest.get("volume", 0)),
                "amount": round(float(latest.get("amount", 0))),
                "date": str(latest.get("date", "")),
            })
        return result
    except Exception as e:
        log.error(f"fetch_indexes failed: {e}")
        return []


def _fetch_money_flow():
    """获取资金流向（最近 N 天）"""
    try:
        df = ak.stock_market_fund_flow()
        if df is None or df.empty:
            return []

        records = []
        for _, row in df.head(7).iterrows():
            records.append({
                "date": str(row["日期"]),
                "main_net_inflow": round(float(row.get("主力净流入-净额", 0)) / 1e8, 1),  # 亿
                "super_large_net": round(float(row.get("超大单净流入-净额", 0)) / 1e8, 1),
                "large_net": round(float(row.get("大单净流入-净额", 0)) / 1e8, 1),
                "mid_net": round(float(row.get("中单净流入-净额", 0)) / 1e8, 1),
                "small_net": round(float(row.get("小单净流入-净额", 0)) / 1e8, 1),
            })
        return records
    except Exception as e:
        log.error(f"fetch_money_flow failed: {e}")
        return []


def _fetch_breadth():
    """
    获取涨跌分布（从新浪拉取，数据量大所以低频刷新）
    注意：此接口较慢，默认 Cache TTL 设为 10 分钟
    """
    try:
        df = ak.stock_zh_a_spot()
        if df is None or df.empty:
            return None

        change = df["涨跌幅"].dropna()
        total = len(change)
        up = int((change > 0).sum())
        down = int((change < 0).sum())
        flat = int((change == 0).sum())
        limit_up = int((change >= 9.9).sum())
        limit_down = int((change <= -9.9).sum())

        # 涨幅分布桶
        bins = [
            {"label": "跌停(≤-10%)", "count": int(((change <= -9.9)).sum())},
            {"label": "-10%~-7%", "count": int(((change > -10) & (change <= -7)).sum())},
            {"label": "-7%~-5%", "count": int(((change > -7) & (change <= -5)).sum())},
            {"label": "-5%~-3%", "count": int(((change > -5) & (change <= -3)).sum())},
            {"label": "-3%~0%", "count": int(((change > -3) & (change < 0)).sum())},
            {"label": "0%~3%", "count": int(((change > 0) & (change < 3)).sum())},
            {"label": "3%~5%", "count": int(((change >= 3) & (change < 5)).sum())},
            {"label": "5%~7%", "count": int(((change >= 5) & (change < 7)).sum())},
            {"label": "7%~10%", "count": int(((change >= 7) & (change < 9.9)).sum())},
            {"label": "涨停(≥10%)", "count": int(((change >= 9.9)).sum())},
        ]

        return {
            "total": total,
            "up": up,
            "down": down,
            "flat": flat,
            "limit_up": limit_up,
            "limit_down": limit_down,
            "avg_change": round(float(change.mean()), 2),
            "distribution": bins,
            "updated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        log.error(f"fetch_breadth failed: {e}")
        return None


def _fetch_sectors():
    """
    获取板块热力数据
    尝试多个数据源：行业板块(东财) → 概念板块(东财) → 同花顺板块
    """
    try:
        # 优先东财行业板块
        df = ak.stock_board_industry_name_em()
        if df is not None and not df.empty and "涨跌幅" in df.columns:
            sectors = []
            for _, row in df.head(30).iterrows():
                sectors.append({
                    "name": row["板块名称"],
                    "change_pct": round(float(row["涨跌幅"]), 2),
                    "up_count": int(row.get("上涨家数", 0)),
                    "down_count": int(row.get("下跌家数", 0)),
                    "turnover": round(float(row.get("换手率", 0)), 2),
                })
            return sectors
    except Exception as e:
        log.warning(f"fetch_sectors (em industry) failed: {e}")

    try:
        # 尝试同花顺板块
        df = ak.stock_board_industry_summary_ths()
        if df is not None and not df.empty:
            sectors = []
            for _, row in df.head(30).iterrows():
                sectors.append({
                    "name": row.get("板块", ""),
                    "change_pct": round(float(row.get("涨跌幅", 0)), 2),
                    "up_count": 0,
                    "down_count": 0,
                    "turnover": 0,
                })
            return sectors
    except Exception as e:
        log.warning(f"fetch_sectors (ths) failed: {e}")

    log.error("All sector data sources failed")
    return []


# ==================== 后台刷新 ====================
def _refresh_loop():
    """定时刷新缓存"""
    while True:
        try:
            log.info("Refreshing cache...")
            t0 = time.time()

            indexes = _fetch_indexes()
            _set_cache("indexes", indexes)
            log.info(f"  indexes: {len(indexes)} items ({time.time()-t0:.1f}s)")

            money_flow = _fetch_money_flow()
            _set_cache("money_flow", money_flow)
            log.info(f"  money_flow: {len(money_flow)} days ({time.time()-t0:.1f}s)")

            sectors = _fetch_sectors()
            _set_cache("sectors", sectors)
            log.info(f"  sectors: {len(sectors)} items ({time.time()-t0:.1f}s)")

            # 涨跌分布单独刷新（慢，TTL 更长）
            breadth = _fetch_breadth()
            if breadth:
                _set_cache("breadth", breadth, ttl=600)
                log.info(f"  breadth: {breadth['total']} stocks ({time.time()-t0:.1f}s)")

            log.info(f"Cache refresh complete ({time.time()-t0:.1f}s)")
        except Exception as e:
            log.error(f"Refresh loop error: {e}")

        time.sleep(CACHE_TTL)


@app.on_event("startup")
def startup():
    threading.Thread(target=_refresh_loop, daemon=True).start()
    log.info("Market data service started")


# ==================== API 端点 ====================
@app.get("/")
def root():
    return {"service": "青鳄量化 市场数据服务", "status": "running"}


@app.get("/api/market/indexes")
def get_indexes():
    data = _get_cached("indexes")
    if data is None:
        data = _fetch_indexes()
        _set_cache("indexes", data)
    return {"indexes": data, "cached": _is_fresh("indexes")}


@app.get("/api/market/money-flow")
def get_money_flow(days: int = Query(7, ge=1, le=30)):
    data = _get_cached("money_flow")
    if data is None:
        data = _fetch_money_flow()
        _set_cache("money_flow", data)
    return {"money_flow": data[:days], "cached": _is_fresh("money_flow")}


@app.get("/api/market/breadth")
def get_breadth():
    data = _get_cached("breadth")
    if data is None:
        data = _fetch_breadth()
        if data:
            _set_cache("breadth", data, ttl=600)
    return {"breadth": data, "cached": _is_fresh("breadth")}


@app.get("/api/market/sectors")
def get_sectors(limit: int = Query(30, ge=5, le=100)):
    data = _get_cached("sectors")
    if data is None:
        data = _fetch_sectors()
        _set_cache("sectors", data)
    return {"sectors": data[:limit], "cached": _is_fresh("sectors")}


@app.get("/api/market/all")
def get_all():
    """聚合接口：一次性返回所有数据"""
    return {
        "indexes": get_indexes(),
        "money_flow": get_money_flow(),
        "breadth": get_breadth(),
        "sectors": get_sectors(),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8091, log_level="info")
