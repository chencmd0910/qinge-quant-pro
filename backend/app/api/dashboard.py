"""Dashboard API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..core.database import get_db
from ..models.models import Position, TradeRecord, Strategy, BacktestReport
from ..schemas.schemas import DashboardSummary

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    positions = db.query(Position).filter(Position.quantity > 0).all()
    total_invested = sum(p.quantity * p.current_price for p in positions)
    total_cost = sum(p.quantity * p.avg_cost for p in positions)
    total_pnl = total_invested - total_cost
    total_asset = 10_000_000 + total_pnl

    latest_bt = db.query(BacktestReport).order_by(BacktestReport.created_at.desc()).first()
    running = db.query(func.count(Strategy.id)).filter(Strategy.status == "running").scalar() or 0

    return DashboardSummary(
        total_asset=total_asset,
        daily_profit=total_pnl,
        daily_return=round(total_pnl / 10_000_000 * 100, 2) if total_pnl else 0,
        cumulative_return=round(total_pnl / 10_000_000 * 100, 2),
        annual_return=latest_bt.annual_return if latest_bt else 0,
        max_drawdown=latest_bt.max_drawdown if latest_bt else 0,
        sharpe_ratio=latest_bt.sharpe_ratio if latest_bt else 0,
        win_rate=latest_bt.win_rate if latest_bt else 0,
        profit_loss_ratio=latest_bt.profit_loss_ratio if latest_bt else 0,
        position_count=len(positions),
        running_strategies=running,
    )
