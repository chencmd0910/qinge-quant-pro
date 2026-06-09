"""Paper Trading API - 动态模拟交易"""
import json
import os
import random
from datetime import datetime, timedelta
from fastapi import APIRouter

router = APIRouter(prefix="/api/paper-trading", tags=["PaperTrading"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
STATE_FILE = os.path.join(DATA_DIR, "paper_trading_state.json")
RESULTS_DIR = os.path.join(DATA_DIR, "backtest_results")

ETF_NAMES = {
    "159915.SZ": "创业板ETF", "510300.SH": "沪深300ETF", "510500.SH": "中证500ETF",
    "515080.SH": "中证红利ETF", "159919.SZ": "沪深300ETF", "159949.SZ": "创业板50",
    "512880.SH": "证券ETF", "512100.SH": "1000ETF", "510050.SH": "上证50ETF",
    "159845.SZ": "中证1000ETF", "159922.SZ": "中证500ETF",
}

SYMBOLS = list(ETF_NAMES.keys())

random.seed(42)


def _load_json(path: str, default=None):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def _save_json(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _sym_name(sym):
    return ETF_NAMES.get(sym, sym)


def _init_state():
    """初始化模拟交易状态"""
    if os.path.exists(STATE_FILE):
        return _load_json(STATE_FILE)

    # First run: create from scratch
    initial_capital = 1_000_000
    today = datetime.now().strftime("%Y-%m-%d")

    # Generate initial positions
    positions = []
    pos_symbols = random.sample(SYMBOLS, 6)
    total_alloc = initial_capital * 0.85
    per_pos = total_alloc / len(pos_symbols)

    for sym in pos_symbols:
        price = round(random.uniform(1.2, 4.5), 3)
        qty = int(per_pos / price / 100) * 100
        cost = qty * price
        positions.append({
            "symbol": sym,
            "name": _sym_name(sym),
            "qty": qty,
            "avg_cost": price,
            "current": round(price * random.uniform(0.92, 1.08), 3),
            "pnl": round((price * random.uniform(0.92, 1.08) - price) * qty, 0),
            "pnl_pct": round((random.uniform(0.92, 1.08) - 1) * 100, 1),
        })

    state = {
        "initial_capital": initial_capital,
        "cash": round(initial_capital - sum(p["qty"] * p["avg_cost"] for p in positions), 0),
        "positions": positions,
        "current_date": today,
        "start_date": "2024-01-01",
        "trade_count": 0,
        "trades": [],
        "equity_curve": [{"date": "2024-01-01", "value": initial_capital, "dd": 0}],
        "daily_pnl": 0,
        "daily_pnl_pct": 0,
        "active_strategies": [
            {"id": "multi_factor_v25_20260606", "name": "多因子V25", "weight": 0.4},
            {"id": "industry_rotation_v1_20260606", "name": "行业轮动V1", "weight": 0.35},
            {"id": "etf_rotation_v1_20260606", "name": "ETF轮动V1", "weight": 0.25},
        ],
    }

    _save_json(STATE_FILE, state)
    return state


@router.get("/summary")
def get_paper_summary():
    state = _init_state()
    pos_value = sum(p["qty"] * p["current"] for p in state["positions"])
    total = pos_value + state["cash"]
    pnl = total - state["initial_capital"]
    pnl_pct = round(pnl / state["initial_capital"] * 100, 2)

    # 计算胜率
    all_trades = state.get("trades", []) + state.get("pending_trades", [])
    win_count = sum(1 for t in all_trades if t.get("pnl", 0) > 0)

    return {
        "initial_capital": state["initial_capital"],
        "current_value": round(total, 0),
        "total_pnl": round(pnl, 0),
        "total_pnl_pct": pnl_pct,
        "daily_pnl": state.get("daily_pnl", 0),
        "daily_pnl_pct": state.get("daily_pnl_pct", 0),
        "win_rate": round(win_count / max(len(all_trades), 1) * 100, 0),
        "trade_days": state.get("trade_count", 0),
        "sharpe": round(random.uniform(0.5, 1.5), 2),
        "max_dd": round(min((e.get("dd", 0) for e in state.get("equity_curve", [{"dd": 0}])), default=0), 1),
        "current_date": state.get("current_date", ""),
    }


@router.get("/strategies")
def get_paper_strategies():
    state = _init_state()
    strategies = state.get("active_strategies", [])
    result = []
    for s in strategies:
        result.append({
            "id": s["id"],
            "name": s["name"],
            "status": "running",
            "pnl_pct": round(random.uniform(2, 25), 1),
            "positions": random.randint(5, 15),
        })
    return {"strategies": result}


@router.get("/positions")
def get_paper_positions():
    state = _init_state()
    return {"positions": state.get("positions", [])}


@router.get("/trades")
def get_paper_trades(limit: int = 30):
    state = _init_state()
    trades = state.get("trades", [])
    recent = trades[-limit:] if len(trades) > limit else trades
    return {"trades": list(reversed(recent))}


@router.get("/equity")
def get_paper_equity():
    state = _init_state()
    curve = state.get("equity_curve", [])
    initial = state["initial_capital"]

    equity = [e.get("value", initial) for e in curve]
    # Benchmark: 5% annual return
    benchmark = [round(initial * (1 + 0.05 / 252) ** i) for i in range(len(equity))]

    return {"equity": equity, "benchmark": benchmark}


@router.post("/toggle-strategy")
def toggle_strategy(strategy_id: str, action: str = "pause"):
    state = _init_state()
    for s in state.get("active_strategies", []):
        if s["id"] == strategy_id:
            s["status"] = "paused" if action == "pause" else "running"
    _save_json(STATE_FILE, state)
    return {"success": True, "strategy_id": strategy_id, "new_status": "paused" if action == "pause" else "running"}


@router.post("/daily-update")
def daily_update():
    """模拟一个交易日的市场变化，产生交易信号"""
    state = _init_state()
    today = state.get("current_date", datetime.now().strftime("%Y-%m-%d"))
    next_date = (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. 更新持仓现价 (±4%)
    for pos in state["positions"]:
        ret = random.gauss(0.0005, 0.015)
        pos["current"] = round(pos["current"] * (1 + ret), 3)
        pos["pnl"] = round((pos["current"] - pos["avg_cost"]) * pos["qty"], 0)
        pos["pnl_pct"] = round((pos["current"] / pos["avg_cost"] - 1) * 100, 1)

    # 2. 检查调仓信号（每5天调一次）
    trade_count = state.get("trade_count", 0)
    if trade_count > 0 and trade_count % 5 == 0:
        # 卖出最差持仓
        if len(state["positions"]) >= 5:
            worst = min(state["positions"], key=lambda p: p["pnl_pct"])
            trade = {
                "time": next_date,
                "action": "卖出",
                "symbol": worst["symbol"],
                "name": worst["name"],
                "qty": worst["qty"],
                "price": worst["current"],
                "amount": round(worst["current"] * worst["qty"], 0),
                "pnl": round((worst["current"] - worst["avg_cost"]) * worst["qty"], 0),
            }
            state["trades"].append(trade)
            state["cash"] += trade["amount"]
            state["positions"].remove(worst)

            # 买入新标的
            available = [s for s in SYMBOLS if s not in [p["symbol"] for p in state["positions"]]]
            if available:
                new_sym = random.choice(available)
                new_price = round(random.uniform(1.2, 4.5), 3)
                alloc = state["cash"] * 0.2
                new_qty = int(alloc / new_price / 100) * 100
                new_pos = {
                    "symbol": new_sym, "name": _sym_name(new_sym),
                    "qty": new_qty, "avg_cost": new_price,
                    "current": new_price, "pnl": 0, "pnl_pct": 0,
                }
                state["positions"].append(new_pos)
                state["cash"] -= new_qty * new_price
                state["trades"].append({
                    "time": next_date, "action": "买入",
                    "symbol": new_sym, "name": _sym_name(new_sym),
                    "qty": new_qty, "price": new_price,
                    "amount": round(new_qty * new_price, 0), "pnl": 0,
                })

    # 3. 更新净值
    pos_value = sum(p["qty"] * p["current"] for p in state["positions"])
    total = pos_value + state["cash"]
    peak = max(e.get("value", 0) for e in state["equity_curve"])
    dd = round((total - peak) / peak * 100, 1) if peak > 0 else 0

    prev_total = state["equity_curve"][-1]["value"] if state["equity_curve"] else state["initial_capital"]
    state["daily_pnl"] = round(total - prev_total, 0)
    state["daily_pnl_pct"] = round((total / prev_total - 1) * 100, 2)

    state["equity_curve"].append({"date": next_date, "value": round(total, 0), "dd": dd})
    state["trade_count"] = trade_count + 1
    state["current_date"] = next_date

    _save_json(STATE_FILE, state)

    return {
        "success": True,
        "date": next_date,
        "total_value": round(total, 0),
        "daily_pnl": state["daily_pnl"],
        "daily_pnl_pct": state["daily_pnl_pct"],
        "trade_count": state["trade_count"],
    }


@router.post("/reset")
def reset_paper_trading():
    """重置模拟交易"""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    state = _init_state()
    return {"success": True, "message": "模拟交易已重置", "date": state["current_date"]}


# ════════════════════════════════════════════════════
# 新版：实盘模拟交易（接基因库+真K线）
# ════════════════════════════════════════════════════

@router.post("/live/run-daily")
def live_run_daily(payload: dict = None):
    """推进一个交易日（实盘模式，用真K线+基因库策略）

    POST /api/paper-trading/live/run-daily
    {"date": "2026-06-09"}   // 可选，默认今天
    """
    from app.paper_trading.live_runner import LivePaperRunner

    target_date = (payload or {}).get("date", None)
    runner = LivePaperRunner()
    runner.load_state()  # 从上次状态恢复
    summary = runner.run_daily(target_date)
    return summary


@router.post("/live/run")
def live_run(payload: dict = None):
    """运行从上次停止日期到今天的所有交易日

    POST /api/paper-trading/live/run
    {"start": "2025-01-01", "end": "2026-06-09"}  // 可选
    """
    from app.paper_trading.live_runner import LivePaperRunner

    start = (payload or {}).get("start", None)
    end = (payload or {}).get("end", None)
    resume = (payload or {}).get("resume", True)

    runner = LivePaperRunner()
    return runner.run(start_date=start, end_date=end, resume=resume)


@router.get("/live/state")
def live_get_state():
    """获取当前实盘模拟状态"""
    from app.paper_trading.live_runner import LivePaperRunner

    runner = LivePaperRunner()
    has_state = runner.load_state()
    if not has_state:
        return {
            "initialized": False,
            "message": "尚未开始模拟交易，请先调用 POST /live/run",
        }
    return runner.get_summary()


@router.post("/live/reset")
def live_reset(payload: dict = None):
    """重置实盘模拟（可选参数：初始资金）"""
    import os
    from app.paper_trading.live_runner import STATE_FILE as LIVE_STATE_FILE, LivePaperRunner

    cash = (payload or {}).get("cash", 1_000_000)
    if os.path.exists(LIVE_STATE_FILE):
        os.remove(LIVE_STATE_FILE)

    runner = LivePaperRunner(initial_cash=cash)
    runner.save_state()
    return {"success": True, "message": f"实盘模拟已重置，初始资金 ¥{cash:,}"}


# ════════════════════════════════════════════════════
# 行情数据更新
# ════════════════════════════════════════════════════

@router.post("/market/update")
def market_data_update(payload: dict = None):
    """更新行情数据（akshare拉取最新K线）

    POST /api/paper-trading/market/update
    {"date": "2026-06-09", "codes": "000001,600519"}  // codes可选
    """
    from app.market_data.akshare_fetcher import update_all_stocks

    target_date = (payload or {}).get("date", None)
    codes_str = (payload or {}).get("codes", None)
    codes = codes_str.split(",") if codes_str else None

    result = update_all_stocks(target_date=target_date, codes=codes)
    return result


@router.get("/market/status")
def market_data_status():
    """查看行情数据状态"""
    from app.market_data.akshare_fetcher import get_parquet_files, last_date_for_code
    import os

    codes = get_parquet_files()
    if not codes:
        return {"files": 0, "message": "无本地K线数据"}

    # 抽样检查最新日期
    sample = codes[:10]
    dates = {}
    for c in sample:
        dates[c] = last_date_for_code(c)

    return {
        "total_stocks": len(codes),
        "sample_dates": dates,
        "data_dir": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "data", "klines", "parquet"),
    }
