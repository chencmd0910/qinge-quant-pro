"""Market API - file-based market data (no DB dependency)"""
import json
import os
from fastapi import APIRouter
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/api/market", tags=["Market"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data")

MARKET_DATA_FILE = os.path.join(DATA_DIR, "market_overview.json")
SECTORS_FILE = os.path.join(DATA_DIR, "sectors.json")
KLINE_DIR = os.path.join(DATA_DIR, "klines")


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _load_json(path: str, default=None):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}


def _save_json(path: str, data):
    _ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─── Default market data (seed data) ───

DEFAULT_MARKET = {
    "indices": [
        {"name": "上证指数", "price": "3157.28", "change": 0.42, "status": "up"},
        {"name": "深证成指", "price": "10623.47", "change": -0.15, "status": "down"},
        {"name": "沪深300", "price": "3865.12", "change": 0.38, "status": "up"},
        {"name": "中证500", "price": "5876.34", "change": -0.21, "status": "down"},
        {"name": "中证1000", "price": "6123.89", "change": -0.45, "status": "down"},
        {"name": "创业板指", "price": "2156.78", "change": 0.55, "status": "up"},
    ],
    "money_flow": [
        {"label": "主力净流入", "value": 78.5, "status": "up"},
        {"label": "散户净流入", "value": -23.2, "status": "down"},
        {"label": "北向资金", "value": 42.1, "status": "up"},
        {"label": "两融余额", "value": 15680, "status": "flat"},
    ],
}

DEFAULT_SECTORS = [
    {"name": "贵金属", "change": 3.25, "flow": 12.8},
    {"name": "煤炭", "change": 2.18, "flow": 8.5},
    {"name": "银行", "change": 1.52, "flow": 15.3},
    {"name": "电力", "change": 1.38, "flow": 6.7},
    {"name": "半导体", "change": -1.87, "flow": -9.2},
    {"name": "消费电子", "change": -2.34, "flow": -11.5},
    {"name": "房地产", "change": -0.92, "flow": -4.8},
    {"name": "传媒", "change": -1.15, "flow": -5.6},
    {"name": "医药生物", "change": 0.78, "flow": 3.2},
    {"name": "食品饮料", "change": -0.56, "flow": -2.1},
    {"name": "汽车", "change": 1.02, "flow": 5.6},
    {"name": "国防军工", "change": -0.34, "flow": -1.8},
]


@router.get("/overview")
def market_overview():
    """返回市场概览（指数行情+资金流向）"""
    data = _load_json(MARKET_DATA_FILE)
    if not data:
        data = DEFAULT_MARKET
        _save_json(MARKET_DATA_FILE, data)
    return data


@router.get("/sectors")
def sectors():
    """返回板块涨跌数据"""
    data = _load_json(SECTORS_FILE)
    if not data:
        data = DEFAULT_SECTORS
        _save_json(SECTORS_FILE, data)
    return {"sectors": data}


@router.get("/kline/{symbol}")
def get_kline(symbol: str, days: int = 120):
    """返回K线数据（文件缓存版）"""
    random.seed(symbol + str(datetime.now().date()))  # 每天固定

    kline_path = os.path.join(KLINE_DIR, f"{symbol}.json")
    _ensure_dir(KLINE_DIR)

    data = _load_json(kline_path, default=[])

    # 如果数据不足，生成模拟K线
    if len(data) < days:
        base_price = 50.0 if "300" in symbol else 25.0 if "000" in symbol else 15.0
        if symbol.startswith("60"):
            base_price = 30.0
        elif symbol.startswith("688"):
            base_price = 80.0

        last_date = datetime.now().date()
        if data:
            base_price = data[-1]["close"]
            last_date = datetime.strptime(data[-1]["date"], "%Y-%m-%d").date()

        new_bars = []
        price = base_price
        gen_days = days - len(data) if len(data) < days else 1

        for i in range(gen_days):
            dt = last_date - timedelta(days=gen_days - i)
            daily_ret = random.gauss(0.0003, 0.02)
            open_price = price
            close_price = price * (1 + daily_ret)
            high = max(open_price, close_price) * (1 + abs(random.gauss(0, 0.005)))
            low = min(open_price, close_price) * (1 - abs(random.gauss(0, 0.005)))
            volume = random.randint(5000000, 50000000)
            change_pct = round(daily_ret * 100, 2)
            new_bars.append({
                "date": dt.strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close_price, 2),
                "volume": volume,
                "change_pct": change_pct,
            })
            price = close_price

        data = data + new_bars
        _save_json(kline_path, data)

    return data[-days:]


@router.get("/symbols")
def list_symbols():
    """返回所有缓存的标的列表"""
    result = []
    if os.path.exists(KLINE_DIR):
        for fname in os.listdir(KLINE_DIR):
            if fname.endswith(".json"):
                data = _load_json(os.path.join(KLINE_DIR, fname))
                latest = data[-1]["date"] if data else None
                result.append({"symbol": fname.replace(".json", ""), "latest_date": latest})
    if not result:
        # 默认标的
        default_symbols = [
            "000001", "000002", "000858", "600519", "600036", "601318",
            "688981", "300750", "600900", "000725"
        ]
        result = [{"symbol": s, "latest_date": datetime.now().strftime("%Y-%m-%d")} for s in default_symbols]
    return result
