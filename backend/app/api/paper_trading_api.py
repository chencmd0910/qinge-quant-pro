"""Paper Trading API — 统一实盘模拟交易引擎

机构级架构：唯一引擎 LivePaperRunner，前端所有端点对接。
不再有两套系统。
"""
import os
from fastapi import APIRouter

router = APIRouter(prefix="/api/paper-trading", tags=["PaperTrading"])

from app.paper_trading.live_runner import LivePaperRunner, STATE_FILE


# ════════════════════════════════════════════════════
# 前端核心端点（Paper Trading 页面）
# ════════════════════════════════════════════════════

@router.get("/summary")
def get_summary():
    """顶层仪表盘：总PnL、净值、夏普、回撤"""
    runner = LivePaperRunner()
    if not runner.load_state():
        return {
            "initial_capital": runner.initial_cash,
            "current_date": "",
            "total_value": runner.initial_cash,
            "total_pnl": 0, "total_pnl_pct": 0,
            "daily_pnl": 0, "daily_pnl_pct": 0,
            "win_rate": 0, "trade_days": 0,
            "sharpe": 0, "max_dd": 0,
        }
    s = runner.get_summary()
    eq = runner.equity_curve
    prev = eq[-2]["value"] if len(eq) >= 2 else runner.initial_cash
    daily_pnl = eq[-1]["value"] - prev if len(eq) >= 2 else 0
    return {
        "initial_capital": runner.initial_cash,
        "current_date": s.get("current_date", ""),
        "total_value": round(s["total_value"], 0),
        "total_pnl": round(s["total_value"] - runner.initial_cash, 0),
        "total_pnl_pct": round((s["total_value"] / runner.initial_cash - 1) * 100, 2),
        "daily_pnl": round(daily_pnl, 0),
        "daily_pnl_pct": round((daily_pnl / prev * 100) if prev else 0, 2),
        "win_rate": 0,
        "trade_days": len(eq),
        "sharpe": s.get("sharpe", 0),
        "max_dd": s.get("max_drawdown", 0),
    }


@router.get("/positions")
def get_positions():
    """当前持仓"""
    runner = LivePaperRunner()
    runner.load_state()
    # 转成前端兼容格式
    positions = []
    for code, pos in runner.positions.items():
        positions.append({
            "symbol": code,
            "name": pos.get("name", code),
            "shares": pos["shares"],
            "avg_cost": pos.get("avg_cost", pos.get("current_price", 0)),
            "current": pos.get("current_price", 0),
            "pnl": round((pos.get("current_price", 0) - pos.get("avg_cost", 0)) * pos["shares"], 0),
            "pnl_pct": round(pos.get("pnl_pct", 0), 1),
            "strategy": pos.get("assigned_strategy", ""),
        })
    return {"positions": positions}


@router.get("/trades")
def get_trades(limit: int = 30):
    """交易记录"""
    runner = LivePaperRunner()
    runner.load_state()
    trades = runner.trades[-limit:] if len(runner.trades) > limit else runner.trades
    return {"trades": list(reversed(trades))}


@router.get("/equity")
def get_equity():
    """净值曲线"""
    runner = LivePaperRunner()
    runner.load_state()
    curve = runner.equity_curve or []
    equity = [e["value"] for e in curve]
    initial = runner.initial_cash
    benchmark = [round(initial * (1 + 0.05 / 252) ** i, 0) for i in range(len(equity))]
    return {"equity": equity, "benchmark": benchmark}


@router.get("/strategies")
def get_strategies():
    """当前活跃策略（从基因库读取）"""
    runner = LivePaperRunner()
    runner.load_state()
    result = []
    for s in runner.active_strategies:
        result.append({
            "id": s.get("strategy_id", ""),
            "name": s.get("strategy_name", ""),
            "status": "running",
            "weight": s.get("weight", 0),
            "positions": sum(1 for p in runner.positions.values()
                             if p.get("assigned_strategy") == s.get("strategy_id")),
        })
    return {"strategies": result}


@router.post("/daily-update")
def daily_update(payload: dict = None):
    """推进一个交易日"""
    runner = LivePaperRunner()
    runner.load_state()
    target_date = (payload or {}).get("date", None)
    summary = runner.run_daily(target_date)
    return {
        "success": True,
        "date": target_date or runner.current_date,
        "total_value": round(summary["total_value"], 0),
        "daily_pnl": 0,
        "daily_pnl_pct": 0,
        "trade_count": summary.get("trade_count", 0),
    }


@router.post("/reset")
def reset_paper(payload: dict = None):
    """重置"""
    cash = (payload or {}).get("cash", 1_000_000)
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    runner = LivePaperRunner(initial_cash=cash)
    runner.save_state()
    return {"success": True, "message": f"已重置，初始资金 ¥{cash:,}"}


# ════════════════════════════════════════════════════
# 高级端点（AI Lab / 定时任务）
# ════════════════════════════════════════════════════

@router.post("/live/run-daily")
def live_run_daily(payload: dict = None):
    """推进一个交易日（详细返回）"""
    target_date = (payload or {}).get("date", None)
    runner = LivePaperRunner()
    runner.load_state()
    return runner.run_daily(target_date)


@router.post("/live/run")
def live_run(payload: dict = None):
    """运行日期范围"""
    start = (payload or {}).get("start", None)
    end = (payload or {}).get("end", None)
    resume = (payload or {}).get("resume", True)
    runner = LivePaperRunner()
    return runner.run(start_date=start, end_date=end, resume=resume)


@router.get("/live/state")
def live_get_state():
    """获取完整实时状态"""
    runner = LivePaperRunner()
    if not runner.load_state():
        return {"initialized": False, "message": "尚未开始模拟交易"}
    return runner.get_summary()


@router.post("/live/reset")
def live_reset(payload: dict = None):
    """重置"""
    cash = (payload or {}).get("cash", 1_000_000)
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    runner = LivePaperRunner(initial_cash=cash)
    runner.save_state()
    return {"success": True, "message": f"已重置，初始资金 ¥{cash:,}"}


# ════════════════════════════════════════════════════
# 行情数据
# ════════════════════════════════════════════════════

@router.post("/market/update")
def market_data_update(payload: dict = None):
    """更新行情数据（akshare → Parquet）"""
    from app.market_data.akshare_fetcher import update_all_stocks

    target_date = (payload or {}).get("date", None)
    codes_str = (payload or {}).get("codes", None)
    codes = codes_str.split(",") if codes_str else None

    return update_all_stocks(target_date=target_date, codes=codes)


@router.get("/market/status")
def market_data_status():
    """行情数据状态"""
    from app.market_data.akshare_fetcher import get_parquet_files, last_date_for_code

    codes = get_parquet_files()
    if not codes:
        return {"files": 0, "message": "无本地K线数据"}

    sample = codes[:10]
    dates = {c: last_date_for_code(c) for c in sample}
    return {"total_stocks": len(codes), "sample_dates": dates}
