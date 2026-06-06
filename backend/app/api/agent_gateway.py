"""Agent Gateway API - AI调用接口

提供 /api/agent/v1 端点，让 AI (Cursor/Claude/Codex/MCP) 可以：
- 创建策略
- 运行回测
- 查看持仓
- 生成报告
- 获取市场数据

所有接口返回JSON，AI可直接解析。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..core.database import get_db
from ..models.models import Strategy, BacktestReport, Position
from ..schemas.schemas import BacktestRequest, BacktestResponse

router = APIRouter(prefix="/api/agent/v1", tags=["Agent Gateway"])


@router.get("/status")
def agent_status():
    """系统状态 - AI检查系统是否可用"""
    return {
        "status": "running",
        "version": "1.0",
        "capabilities": [
            "strategy_create",
            "backtest_run",
            "backtest_report",
            "portfolio_query",
            "market_data",
        ]
    }


@router.post("/strategy/create")
def agent_create_strategy(
    name: str,
    code: str,
    strategy_type: str = "script",
    description: str = "",
    db: Session = Depends(get_db)
):
    """创建策略 - AI提交策略代码"""
    strategy = Strategy(
        name=name,
        description=description,
        strategy_type=strategy_type,
        path=f"strategies/{name.lower().replace(' ', '_')}",
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return {
        "strategy_id": strategy.id,
        "name": strategy.name,
        "status": "created",
        "message": f"Strategy '{name}' created. Use /api/agent/v1/backtest/run to test it."
    }


@router.post("/backtest/run")
def agent_run_backtest(
    symbol: str = "510300",
    strategy: str = "moving_average",
    days: int = 250,
    cash: float = 1_000_000,
    short_window: int = 5,
    long_window: int = 20,
    db: Session = Depends(get_db)
):
    """运行回测 - AI提交回测参数，返回完整结果"""
    from ..api.backtest import run_backtest
    from ..schemas.schemas import BacktestRequest

    req = BacktestRequest(
        strategy=strategy,
        symbol=symbol,
        days=days,
        cash=cash,
        params={"short_window": short_window, "long_window": long_window}
    )
    result = run_backtest(req, db)

    # 简化返回给AI的格式
    m = result.metrics
    return {
        "summary": {
            "total_return": f"{m.total_return:.2f}%",
            "annual_return": f"{m.annual_return:.2f}%",
            "max_drawdown": f"{m.max_drawdown:.2f}%",
            "sharpe_ratio": round(m.sharpe_ratio, 2),
            "win_rate": f"{m.win_rate:.1f}%",
            "profit_loss_ratio": round(m.profit_loss_ratio, 2),
            "total_trades": m.total_trades,
        },
        "equity_curve_points": len(result.equity_curve),
        "monthly_returns": result.monthly_returns,
        "trade_count": len(result.trades),
        "recommendation": _generate_recommendation(m),
    }


@router.get("/portfolio")
def agent_portfolio(db: Session = Depends(get_db)):
    """查看持仓 - AI获取当前持仓"""
    positions = db.query(Position).filter(Position.quantity > 0).all()
    total_value = sum(p.quantity * p.current_price for p in positions)
    return {
        "total_value": round(total_value, 2),
        "position_count": len(positions),
        "positions": [
            {
                "symbol": p.symbol,
                "name": p.name,
                "quantity": p.quantity,
                "avg_cost": round(p.avg_cost, 2),
                "current_price": round(p.current_price, 2),
                "pnl": round((p.current_price - p.avg_cost) * p.quantity, 2),
                "pnl_pct": round((p.current_price / p.avg_cost - 1) * 100, 2) if p.avg_cost > 0 else 0,
            }
            for p in positions
        ]
    }


@router.get("/market/{symbol}")
def agent_market(symbol: str, days: int = 30, db: Session = Depends(get_db)):
    """获取市场数据 - AI获取K线"""
    from ..models.models import MarketData
    rows = db.query(MarketData).filter(MarketData.symbol == symbol)\
        .order_by(MarketData.trade_date.desc()).limit(days).all()
    rows = list(reversed(rows))
    if not rows:
        return {"symbol": symbol, "data_points": 0, "message": "No data. Use synthetic data for testing."}
    return {
        "symbol": symbol,
        "data_points": len(rows),
        "latest_date": rows[-1].trade_date if rows else "",
        "latest_close": rows[-1].close if rows else 0,
        "bars": [
            {"date": r.trade_date, "open": r.open, "high": r.high,
             "low": r.low, "close": r.close, "volume": r.volume}
            for r in rows[-10:]  # 最近10根
        ]
    }


@router.get("/reports")
def agent_reports(limit: int = 5, db: Session = Depends(get_db)):
    """查看回测报告 - AI获取历史回测结果"""
    reports = db.query(BacktestReport).order_by(BacktestReport.created_at.desc()).limit(limit).all()
    return {
        "count": len(reports),
        "reports": [
            {
                "id": r.id,
                "annual_return": f"{r.annual_return:.2f}%",
                "sharpe_ratio": round(r.sharpe_ratio, 2),
                "max_drawdown": f"{r.max_drawdown:.2f}%",
                "total_trades": r.total_trades,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in reports
        ]
    }


def _generate_recommendation(metrics) -> str:
    """AI友好的策略评价"""
    recs = []
    if metrics.sharpe_ratio > 1.5:
        recs.append("Excellent risk-adjusted returns (Sharpe > 1.5)")
    elif metrics.sharpe_ratio > 0.5:
        recs.append("Acceptable risk-adjusted returns")
    else:
        recs.append("Low risk-adjusted returns, consider optimization")

    if metrics.max_drawdown > 30:
        recs.append("WARNING: High drawdown (>30%), add stop-loss")
    elif metrics.max_drawdown > 15:
        recs.append("Moderate drawdown, acceptable for most strategies")

    if metrics.win_rate > 50:
        recs.append("Good win rate")
    elif metrics.win_rate < 30:
        recs.append("Low win rate, ensure P/L ratio compensates")

    if metrics.total_trades < 5:
        recs.append("Too few trades, results may not be statistically significant")

    return "; ".join(recs)
