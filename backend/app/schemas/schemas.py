"""Pydantic schemas"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# === Dashboard ===
class DashboardSummary(BaseModel):
    total_asset: float
    daily_profit: float
    daily_return: float
    cumulative_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_loss_ratio: float
    position_count: int
    running_strategies: int


# === Portfolio ===
class PositionResponse(BaseModel):
    symbol: str
    name: str
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float
    pnl: float
    pnl_pct: float
    weight: float

    class Config:
        from_attributes = True


class TradeResponse(BaseModel):
    id: int
    symbol: str
    side: str
    price: float
    quantity: int
    amount: float
    commission: float
    pnl: float
    created_at: datetime

    class Config:
        from_attributes = True


# === Strategy ===
class StrategyCreate(BaseModel):
    name: str
    description: str = ""
    strategy_type: str = "custom"
    code: str = ""
    config: Dict[str, Any] = {}


class StrategyResponse(BaseModel):
    id: int
    name: str
    description: str
    strategy_type: str
    status: str
    config: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StrategyRunRequest(BaseModel):
    strategy_id: int
    symbol: str = "510300"
    params: Dict[str, Any] = {}


# === Backtest ===
class BacktestRequest(BaseModel):
    strategy: str  # strategy name or id
    symbol: str = "510300"
    days: int = 250
    cash: float = 1_000_000
    params: Dict[str, Any] = {}


class BacktestMetrics(BaseModel):
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    win_rate: float
    profit_loss_ratio: float
    total_trades: int


class BacktestResponse(BaseModel):
    metrics: BacktestMetrics
    equity_curve: List[Dict[str, Any]]
    drawdown_curve: List[Dict[str, Any]]
    monthly_returns: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]


# === Market ===
class KlineResponse(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    change_pct: float


class SymbolInfo(BaseModel):
    code: str
    name: str
    market: str
    last_price: float
    change_pct: float
    volume: float
    amount: float
