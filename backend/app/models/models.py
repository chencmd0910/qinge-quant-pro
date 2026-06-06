"""数据库模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, default="admin")
    password_hash = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.now)
    strategies = relationship("Strategy", back_populates="user")


class Strategy(Base):
    __tablename__ = "strategies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    path = Column(Text, nullable=False)
    strategy_type = Column(String(50), default="custom")
    status = Column(String(20), default="idle")
    config = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    user = relationship("User", back_populates="strategies")
    versions = relationship("StrategyVersion", back_populates="strategy")
    backtests = relationship("BacktestReport", back_populates="strategy")


class StrategyVersion(Base):
    __tablename__ = "strategy_versions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    version = Column(String(20), nullable=False)
    code = Column(Text, nullable=False)
    commit_message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    strategy = relationship("Strategy", back_populates="versions")


class BacktestReport(Base):
    __tablename__ = "backtest_reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    config = Column(Text, default="{}")
    total_return = Column(Float, default=0)
    annual_return = Column(Float, default=0)
    max_drawdown = Column(Float, default=0)
    sharpe_ratio = Column(Float, default=0)
    sortino_ratio = Column(Float, default=0)
    calmar_ratio = Column(Float, default=0)
    win_rate = Column(Float, default=0)
    profit_loss_ratio = Column(Float, default=0)
    total_trades = Column(Integer, default=0)
    equity_curve = Column(Text, default="[]")
    drawdown_curve = Column(Text, default="[]")
    monthly_returns = Column(Text, default="[]")
    trades = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.now)
    strategy = relationship("Strategy", back_populates="backtests")


class Position(Base):
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    symbol = Column(String(20), nullable=False)
    name = Column(String(50), default="")
    quantity = Column(Integer, default=0)
    avg_cost = Column(Float, default=0)
    current_price = Column(Float, default=0)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class TradeRecord(Base):
    __tablename__ = "trade_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    strategy_id = Column(Integer, nullable=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    amount = Column(Float, default=0)
    commission = Column(Float, default=0)
    pnl = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)


class MarketData(Base):
    __tablename__ = "market_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    trade_date = Column(String(10), nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    change_pct = Column(Float)
