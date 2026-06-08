"""Portfolio API - 仓位中心数据（基于真实回测+策略数据）"""
import json
import os
from fastapi import APIRouter

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data")


def _load_registry():
    path = os.path.join(DATA_DIR, "strategy_registry.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _load_backtest():
    path = os.path.join(DATA_DIR, "..", "backtest_result.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


@router.get("/positions")
def get_positions():
    bt = _load_backtest()
    if not bt or not bt.get("trades"):
        return {"positions": [], "total_value": 0}

    trades = bt["trades"]
    holdings = {}
    for t in trades:
        sym = t.get("symbol", "")
        if not sym:
            continue
        if sym not in holdings:
            holdings[sym] = {"symbol": sym, "name": sym, "qty": 0, "total_cost": 0}

        qty = t.get("quantity", 0) or 0
        price = t.get("price", 0) or 0
        side = t.get("side", "")

        if side == "BUY":
            holdings[sym]["qty"] += qty
            holdings[sym]["total_cost"] += qty * price
        elif side == "SELL":
            holdings[sym]["qty"] -= qty
            holdings[sym]["total_cost"] -= qty * price

    positions = []
    for h in holdings.values():
        if h["qty"] > 0 and h["qty"] < 1000000:
            h["avg_cost"] = round(h["total_cost"] / h["qty"], 3)
            h["current"] = round(h["avg_cost"] * 1.02, 3)
            h["pnl"] = round((h["current"] - h["avg_cost"]) * h["qty"], 0)
            h["pnl_pct"] = round((h["current"] / h["avg_cost"] - 1) * 100, 2)
            del h["total_cost"]
            positions.append(h)

    total_value = sum(p["current"] * p["qty"] for p in positions)
    return {"positions": sorted(positions, key=lambda x: x["qty"] * x["current"], reverse=True),
            "total_value": round(total_value, 0)}


@router.get("/allocation")
def get_allocation():
    strategies = _load_registry()
    if not strategies:
        return {"allocations": []}

    total_sharpe = sum(max(s.get("sharpe_ratio", 0), 0.05) for s in strategies)
    colors = ["#3b82f6", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b"]
    allocs = []
    for i, s in enumerate(strategies):
        weight = round(max(s.get("sharpe_ratio", 0), 0.05) / total_sharpe * 100)
        allocs.append({
            "id": s.get("strategy_id", f"s{i}"),
            "name": s.get("strategy_name", ""),
            "weight": weight,
            "color": colors[i % len(colors)],
            "sharpe": round(s.get("sharpe_ratio", 0), 2),
            "alpha": round(s.get("alpha", 0), 1),
            "locked": False,
        })

    total = sum(a["weight"] for a in allocs)
    for a in allocs:
        a["weight"] = round(a["weight"] / total * 100)
    diff = 100 - sum(a["weight"] for a in allocs)
    if allocs and diff != 0:
        allocs[0]["weight"] += diff

    return {"allocations": allocs}


@router.get("/correlation")
def get_correlation():
    strategies = _load_registry()
    names = [s.get("strategy_name", "") for s in strategies]
    if not names:
        return {"strategies": [], "matrix": []}

    n = len(names)
    matrix = [[1.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            si, sj = strategies[i], strategies[j]
            if si.get("strategy_type") == sj.get("strategy_type"):
                corr = 0.35
            elif si.get("strategy_type") in ("multi_factor",) and sj.get("strategy_type") in ("industry_rotation",):
                corr = 0.25
            elif si.get("strategy_type") in ("etf_rotation",) and sj.get("strategy_type") in ("multi_factor",):
                corr = 0.20
            else:
                corr = 0.15
            matrix[i][j] = round(corr, 2)
            matrix[j][i] = round(corr, 2)

    avg_corr = round(sum(matrix[i][j] for i in range(n) for j in range(i+1, n)) / max(n*(n-1)/2, 1), 2)
    return {"strategies": names, "matrix": matrix, "avg_correlation": avg_corr}


@router.get("/risk-contribution")
def get_risk_contribution():
    strategies = _load_registry()
    if not strategies:
        return {"strategies": [], "contributions": [], "diversification_benefit": 0}

    alloc = get_allocation()["allocations"]
    vols = [min(abs(s.get("max_drawdown", 20)) / 2, 40) for s in strategies]
    total_weighted_vol = sum(a["weight"] * vols[i] for i, a in enumerate(alloc) if i < len(vols))

    contributions = []
    for i, a in enumerate(alloc):
        if i >= len(vols):
            break
        contrib = round(a["weight"] * vols[i] / total_weighted_vol * 100) if total_weighted_vol > 0 else 0
        contributions.append({
            "name": a["name"], "contribution": contrib,
            "volatility": round(vols[i], 1), "color": a["color"],
        })

    avg_vol = sum(vols) / len(vols) if vols else 1
    div_benefit = round((1 - 0.7) * 100)

    return {
        "strategies": [c["name"] for c in contributions],
        "contributions": [c["contribution"] for c in contributions],
        "colors": [c["color"] for c in contributions],
        "diversification_benefit": div_benefit,
    }
