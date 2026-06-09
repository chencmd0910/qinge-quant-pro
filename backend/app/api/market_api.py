"""
市场数据 API - Parquet K线数据查询接口
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from ..data_engine.kline_parquet import get_kline_engine

router = APIRouter(prefix="/api/market", tags=["Market Data"])

engine = get_kline_engine


@router.get("/stats")
async def get_market_stats():
    """获取数据概览"""
    return engine().get_stats()


@router.get("/stocks")
async def get_stock_list():
    """获取可用的股票列表"""
    df = engine().get_stock_list()
    return df.to_dict(orient="records")


@router.get("/stocks/search")
async def search_stocks(keyword: str = Query(..., min_length=1), limit: int = Query(20, le=50)):
    """搜索股票"""
    return engine().search_stocks(keyword, limit)


@router.get("/stocks/{code}")
async def get_stock_kline(
    code: str,
    start: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
):
    """获取单只股票K线"""
    if start or end:
        df = engine().load_stock_range(code, start or "2020-01-01", end or "2099-12-31")
    else:
        df = engine().load_stock(code)

    if df is None:
        raise HTTPException(status_code=404, detail=f"Stock {code} not found")

    return df.to_dict(orient="records")


@router.post("/basket/closes")
async def get_basket_closes(
    codes: List[str],
    start: Optional[str] = None,
    end: Optional[str] = None,
):
    """获取一组股票的收盘价透视表（回测核心接口）

    请求体: { "codes": ["000001", "600519", ...], "start": "2024-01-01", "end": "2024-12-31" }
    返回: { "dates": [...], "data": { "000001": [c1, c2, ...], ... } }
    """
    df = engine().get_closes(codes, start, end)
    if df.empty:
        return {"dates": [], "data": {}}

    result = {
        "dates": [str(d) for d in df.index.tolist()],
        "data": {code: df[code].tolist() for code in df.columns},
    }
    return result


@router.post("/basket/ohlcv")
async def get_basket_ohlcv(
    codes: List[str],
    start: Optional[str] = None,
    end: Optional[str] = None,
):
    """获取一组股票的完整OHLCV（回测核心接口2）

    请求体: { "codes": ["000001", "600519", ...], "start": "2024-01-01", "end": "2024-12-31" }
    """
    df = engine().load_basket(codes, start, end)
    if df.empty:
        return {"dates": [], "stocks": {}}

    # 将MultiIndex DataFrame转换为前端友好的格式
    stocks = {}
    dates = sorted(set(str(d) for d in df.index.get_level_values("date").unique()))

    for code in codes:
        if code not in df.index.get_level_values("code"):
            continue
        stock_df = df.xs(code, level="code").reset_index()
        stock_df["date"] = stock_df["date"].astype(str)
        stocks[code] = stock_df.to_dict(orient="records")

    return {"dates": dates, "stocks": stocks}


@router.get("/trading-dates")
async def get_trading_dates(
    start: Optional[str] = None,
    end: Optional[str] = None,
):
    """获取交易日历"""
    return engine().get_trade_dates(start, end)


@router.get("/overview")
async def get_market_overview():
    """获取市场概览（前端仪表盘用）"""
    stats = engine().get_stats()
    # 返回最近一天的数据概要
    dates = engine().get_trade_dates()
    latest = dates[-1] if dates else None
    return {
        **stats,
        "latest_trading_day": latest,
        "available": stats["stock_count"] > 0,
    }


@router.get("/sectors")
async def get_sectors():
    """获取板块概览（基于现有数据）"""
    from pathlib import Path
    import json

    # 尝试加载本地缓存的板块数据
    sector_file = Path(__file__).parent.parent.parent / "data" / "market_overview.json"
    if sector_file.exists():
        with open(sector_file) as f:
            return json.load(f)

    # 返回空数据
    return {"sectors": [], "updated": None}
