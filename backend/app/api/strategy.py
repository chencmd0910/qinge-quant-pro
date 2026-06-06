"""Strategy API"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.models import Strategy, StrategyVersion
from ..schemas.schemas import StrategyCreate, StrategyResponse
from typing import List

router = APIRouter(prefix="/api/strategy", tags=["Strategy"])


@router.get("/list", response_model=List[StrategyResponse])
def list_strategies(db: Session = Depends(get_db)):
    return db.query(Strategy).order_by(Strategy.updated_at.desc()).all()


@router.post("/create", response_model=StrategyResponse)
def create_strategy(req: StrategyCreate, db: Session = Depends(get_db)):
    strategy = Strategy(
        name=req.name, description=req.description,
        strategy_type=req.strategy_type,
        path=f"strategies/{req.name.lower().replace(' ', '_')}",
        config=json.dumps(req.config, ensure_ascii=False),
    )
    db.add(strategy)
    db.flush()
    if req.code:
        db.add(StrategyVersion(strategy_id=strategy.id, version="1.0.0",
                               code=req.code, commit_message="Initial"))
    db.commit()
    db.refresh(strategy)
    return strategy


@router.post("/{strategy_id}/run")
def run_strategy(strategy_id: int, db: Session = Depends(get_db)):
    s = db.query(Strategy).get(strategy_id)
    if not s:
        raise HTTPException(404, "策略不存在")
    s.status = "running"
    db.commit()
    return {"status": "running", "strategy_id": strategy_id}


@router.post("/{strategy_id}/stop")
def stop_strategy(strategy_id: int, db: Session = Depends(get_db)):
    s = db.query(Strategy).get(strategy_id)
    if not s:
        raise HTTPException(404, "策略不存在")
    s.status = "idle"
    db.commit()
    return {"status": "stopped"}
