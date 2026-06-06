"""Backtest API"""
import json, random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.models import BacktestReport, MarketData
from ..schemas.schemas import BacktestRequest, BacktestResponse, BacktestMetrics
from ..backtest_engine.core.bar import Bar
from ..backtest_engine.engine import BacktestEngine

router = APIRouter(prefix="/api/backtest", tags=["Backtest"])


def _generate_synthetic_bars(symbol: str, days: int) -> list:
    """生成合成数据（无真实数据时使用）"""
    random.seed(hash(symbol) % 10000)
    bars = []
    price = 100.0
    start = datetime(2024, 1, 1)
    for i in range(days):
        dt = start + timedelta(days=i)
        change = random.gauss(0.0003, 0.015)
        price *= (1 + change)
        o = price * (1 + random.uniform(-0.005, 0.005))
        h = max(price, o) * (1 + random.uniform(0, 0.015))
        l = min(price, o) * (1 - random.uniform(0, 0.015))
        bars.append(Bar(symbol=symbol, datetime=dt, open=round(o, 2), high=round(h, 2),
                        low=round(l, 2), close=round(price, 2), volume=random.randint(1000000, 5000000)))
    return bars


@router.post("/run", response_model=BacktestResponse)
def run_backtest(req: BacktestRequest, db: Session = Depends(get_db)):
    # 尝试从数据库加载真实数据
    rows = db.query(MarketData).filter(MarketData.symbol == req.symbol)\
        .order_by(MarketData.trade_date).limit(req.days).all()

    if rows:
        bars = [Bar(symbol=r.symbol, datetime=datetime.strptime(r.trade_date, '%Y-%m-%d'),
                    open=r.open, high=r.high, low=r.low, close=r.close,
                    volume=r.volume or 0, amount=r.amount or 0, change_pct=r.change_pct or 0)
                for r in rows]
        data_source = "database"
    else:
        bars = _generate_synthetic_bars(req.symbol, req.days)
        data_source = "synthetic"

    # 加载策略
    strategy_name = req.strategy
    if strategy_name == "moving_average":
        from strategies.moving_average.strategy import MovingAverageStrategy
        strategy = MovingAverageStrategy(
            symbol=req.symbol,
            short_window=req.params.get("short_window", 5),
            long_window=req.params.get("long_window", 20),
        )
    elif strategy_name == "etf_rotation":
        from strategies.etf_rotation.strategy import ETFRotationStrategy
        strategy = ETFRotationStrategy(symbols=[req.symbol])
    else:
        raise HTTPException(400, f"未知策略: {strategy_name}")

    # 运行回测
    engine = BacktestEngine(strategy=strategy, data={req.symbol: bars}, cash=req.cash)
    result = engine.run()

    # 保存报告
    report = BacktestReport(
        strategy_id=1,
        config=json.dumps({"strategy": strategy_name, "symbol": req.symbol, "data_source": data_source}),
        **result['metrics'],
        equity_curve=json.dumps(result['equity_curve'][-100:], ensure_ascii=False),
        drawdown_curve=json.dumps(result['drawdown_curve'][-100:], ensure_ascii=False),
        monthly_returns=json.dumps(result['monthly_returns'], ensure_ascii=False),
        trades=json.dumps(result['trades'][-50:], ensure_ascii=False),
    )
    db.add(report)
    db.commit()

    return BacktestResponse(
        metrics=BacktestMetrics(**result['metrics']),
        equity_curve=result['equity_curve'],
        drawdown_curve=result['drawdown_curve'],
        monthly_returns=result['monthly_returns'],
        trades=result['trades'],
    )


@router.get("/reports")
def list_reports(limit: int = 20, db: Session = Depends(get_db)):
    reports = db.query(BacktestReport).order_by(BacktestReport.created_at.desc()).limit(limit).all()
    return [
        {"id": r.id, "strategy_id": r.strategy_id, "annual_return": r.annual_return,
         "sharpe_ratio": r.sharpe_ratio, "max_drawdown": r.max_drawdown,
         "total_trades": r.total_trades, "created_at": r.created_at.isoformat() if r.created_at else ""}
        for r in reports
    ]
