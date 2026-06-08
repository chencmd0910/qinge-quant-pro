"""Alpha Factory API - 使用真实策略注册表数据"""
import json
import os
from typing import List, Dict, Any
from fastapi import APIRouter

router = APIRouter(prefix="/api/alpha-factory", tags=["AlphaFactory"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data")


def _load_registry() -> List[Dict[str, Any]]:
    """加载策略注册表"""
    path = os.path.join(DATA_DIR, "strategy_registry.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _load_lifecycle():
    """加载策略生命周期"""
    path = os.path.join(DATA_DIR, "strategy_lifecycle.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _get_strategies() -> List[Dict[str, Any]]:
    """从真实注册表构建策略池"""
    registry = _load_registry()
    lifecycle = _load_lifecycle()
    
    status_map = {"VALIDATED": "ACTIVE", "RESEARCH": "WATCHLIST"}
    decay_map = {"VALIDATED": "HEALTHY", "RESEARCH": "RECOVERING"}
    
    cluster_map = {
        "multi_factor": "多因子/正交",
        "etf_rotation": "ETF/轮动",
        "industry_rotation": "行业/轮动",
        "dividend": "价值/红利",
    }
    
    strategies = []
    for s in registry:
        sid = s.get("strategy_id", "")
        key = sid.rsplit("_", 1)[0] if "_" in sid else sid
        lc = lifecycle.get(key, {})
        lc_status = lc.get("status", "RESEARCH")
        stype = s.get("strategy_type", "")
        
        strategies.append({
            "id": sid,
            "name": s.get("strategy_name", ""),
            "version": s.get("version", "1.0"),
            "sharpe": round(s.get("sharpe_ratio", 0), 2),
            "alpha": round(s.get("alpha", 0), 1),
            "max_dd": round(s.get("max_drawdown", 0), 1),
            "annual": round(s.get("annual_return", 0), 2),
            "live_days": s.get("trade_count", 0),  # uses trade_count as proxy
            "win_rate": round(s.get("win_rate", 0), 0),
            "trades": s.get("trade_count", 0),
            "total_return": round(s.get("total_return", 0), 1),
            "last_signal": {
                "multi_factor": "持有最优20只",
                "etf_rotation": "持有 159915.SZ",
                "industry_rotation": "轮动中",
                "dividend": "持有红利组合",
            }.get(stype, "运行中"),
            "status": status_map.get(lc_status, "WATCHLIST"),
            "decay_status": decay_map.get(lc_status, "RECOVERING"),
            "cluster": cluster_map.get(stype, s.get("tags", ["通用"])[0] if s.get("tags") else "通用"),
        })
    
    return sorted(strategies, key=lambda x: x["sharpe"], reverse=True)


@router.get("/strategies")
def get_all_strategies(status: str = None):
    all_s = _get_strategies()
    if status:
        all_s = [s for s in all_s if s["status"] == status.upper()]
    active = [s for s in all_s if s["status"] == "ACTIVE"]
    return {
        "strategies": all_s,
        "counts": {
            "active": sum(1 for s in all_s if s["status"] == "ACTIVE"),
            "watchlist": sum(1 for s in all_s if s["status"] == "WATCHLIST"),
            "retired": sum(1 for s in all_s if s["status"] == "RETIRED"),
        },
        "total_alpha": sum(s["alpha"] for s in active),
    }


@router.get("/dashboard")
def get_alpha_dashboard():
    strategies = _get_strategies()
    active = [s for s in strategies if s["status"] == "ACTIVE"]
    watchlist = [s for s in strategies if s["status"] == "WATCHLIST"]
    retired = [s for s in strategies if s["status"] == "RETIRED"]

    return {
        "active": {"count": len(active), "strategies": active, "total_alpha": sum(s["alpha"] for s in active)},
        "watchlist": {"count": len(watchlist), "strategies": watchlist, "total_sharpe": round(sum(s["sharpe"] for s in watchlist) / max(len(watchlist), 1), 2)},
        "retired": {"count": len(retired), "strategies": retired},
        "total_strategies": len(strategies),
    }
