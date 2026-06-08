"""Strategy API - file-based strategy CRUD (no DB dependency)"""
import json
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/strategy", tags=["Strategy"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data")
REGISTRY_FILE = os.path.join(DATA_DIR, "strategy_registry.json")
STRATEGY_CODE_DIR = os.path.join(DATA_DIR, "strategy_codes")


def _load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_registry(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _load_code(strategy_id: str) -> str:
    path = os.path.join(STRATEGY_CODE_DIR, f"{strategy_id}.py")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def _save_code(strategy_id: str, code: str):
    os.makedirs(STRATEGY_CODE_DIR, exist_ok=True)
    with open(os.path.join(STRATEGY_CODE_DIR, f"{strategy_id}.py"), "w", encoding="utf-8") as f:
        f.write(code)


@router.get("/list")
def list_strategies():
    """列出所有注册策略"""
    return _load_registry()


@router.get("/{strategy_id}")
def get_strategy(strategy_id: str):
    """获取单个策略详情（含代码）"""
    registry = _load_registry()
    for s in registry:
        if s.get("strategy_id") == strategy_id:
            s["code"] = _load_code(strategy_id)
            return s
    raise HTTPException(404, "策略不存在")


@router.post("/create")
def create_strategy(payload: dict):
    """创建新策略"""
    registry = _load_registry()
    strategy_id = payload.get("strategy_id") or f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    strategy = {
        "strategy_id": strategy_id,
        "strategy_name": payload.get("strategy_name", "未命名策略"),
        "strategy_type": payload.get("strategy_type", "multi_factor"),
        "version": payload.get("version", "1.0"),
        "status": "RESEARCH",
        "lifecycle": {
            "status": "RESEARCH",
            "live_days": 0,
            "decay_status": "NONE",
        },
        "metrics": {
            "annual_return": 0,
            "total_return": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "win_rate": 0,
            "alpha": 0,
        },
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    registry.append(strategy)
    _save_registry(registry)
    
    if payload.get("code"):
        _save_code(strategy_id, payload["code"])
    
    return strategy


@router.post("/{strategy_id}/start")
def start_strategy(strategy_id: str):
    """激活策略（RESEARCH → ACTIVE）"""
    registry = _load_registry()
    for s in registry:
        if s.get("strategy_id") == strategy_id:
            if "lifecycle" not in s:
                s["lifecycle"] = {}
            s["lifecycle"]["status"] = "ACTIVE"
            s["lifecycle"]["live_days"] = s["lifecycle"].get("live_days", 0) + 1
            s["updated_at"] = datetime.now().isoformat()
            _save_registry(registry)
            return {"status": "ACTIVE", "strategy_id": strategy_id}
    raise HTTPException(404, "策略不存在")


@router.post("/{strategy_id}/stop")
def stop_strategy(strategy_id: str):
    """停用策略"""
    registry = _load_registry()
    for s in registry:
        if s.get("strategy_id") == strategy_id:
            if "lifecycle" not in s:
                s["lifecycle"] = {}
            s["lifecycle"]["status"] = "IDLE"
            s["updated_at"] = datetime.now().isoformat()
            _save_registry(registry)
            return {"status": "IDLE", "strategy_id": strategy_id}
    raise HTTPException(404, "策略不存在")


@router.post("/{strategy_id}/save-code")
def save_strategy_code(strategy_id: str, payload: dict):
    """保存策略代码"""
    code = payload.get("code", "")
    _save_code(strategy_id, code)
    return {"saved": True, "strategy_id": strategy_id}


@router.delete("/{strategy_id}")
def delete_strategy(strategy_id: str):
    """删除策略"""
    registry = _load_registry()
    registry = [s for s in registry if s.get("strategy_id") != strategy_id]
    _save_registry(registry)
    return {"deleted": True}
