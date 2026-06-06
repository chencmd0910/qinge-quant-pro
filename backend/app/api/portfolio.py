"""Portfolio API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.models import Position, TradeRecord
from ..schemas.schemas import PositionResponse, TradeResponse
from typing import List

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


@router.get("/positions", response_model=List[PositionResponse])
def get_positions(db: Session = Depends(get_db)):
    positions = db.query(Position).filter(Position.quantity > 0).all()
    total_value = sum(p.quantity * p.current_price for p in positions) or 1
    return [
        PositionResponse(
            symbol=p.symbol, name=p.name, quantity=p.quantity,
            avg_cost=p.avg_cost, current_price=p.current_price,
            market_value=p.quantity * p.current_price,
            pnl=(p.current_price - p.avg_cost) * p.quantity,
            pnl_pct=round((p.current_price / p.avg_cost - 1) * 100, 2) if p.avg_cost > 0 else 0,
            weight=round(p.quantity * p.current_price / total_value * 100, 2),
        )
        for p in positions
    ]


@router.get("/trades", response_model=List[TradeResponse])
def get_trades(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(TradeRecord).order_by(TradeRecord.created_at.desc()).limit(limit).all()
