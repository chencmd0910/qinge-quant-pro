"""Market API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..core.database import get_db
from ..models.models import MarketData
from ..schemas.schemas import KlineResponse
from typing import List

router = APIRouter(prefix="/api/market", tags=["Market"])


@router.get("/kline/{symbol}", response_model=List[KlineResponse])
def get_kline(symbol: str, days: int = 120, db: Session = Depends(get_db)):
    rows = db.query(MarketData).filter(MarketData.symbol == symbol)\
        .order_by(MarketData.trade_date.desc()).limit(days).all()
    rows = list(reversed(rows))
    return [KlineResponse(date=r.trade_date, open=r.open, high=r.high, low=r.low,
                          close=r.close, volume=r.volume or 0, change_pct=r.change_pct or 0)
            for r in rows]


@router.get("/symbols")
def list_symbols(db: Session = Depends(get_db)):
    result = db.query(MarketData.symbol, func.max(MarketData.trade_date))\
        .group_by(MarketData.symbol).all()
    return [{"symbol": r[0], "latest_date": r[1]} for r in result]
