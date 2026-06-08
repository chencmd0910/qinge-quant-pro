"""青鳄量化 MCP Server — 暴露量化工具给 AI Agent

通过 Model Context Protocol (MCP) 提供：
- 回测引擎调用
- 实时持仓查询
- Alpha Factory 策略管理
- 风险指标获取
- 市场数据查询
"""
import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ── 创建 MCP 实例 ──
mcp = FastMCP(
    name="青鳄量化 Pro",
    instructions="""青鳄量化 Pro 完整工具集，提供：
- get_dashboard_summary: 核心仪表盘数据（资产、收益、夏普、回撤）
- get_equity_curve: 权益曲线
- get_strategies: 策略列表（按状态筛选）
- get_risk_alerts: 风险警报
- get_positions: 持仓明细
- get_alpha_factory: Alpha Factory 三池
- run_backtest: 运行回测
- get_risk_metrics: 综合风险指标
- get_market_data: A股行情数据(OHLCV)""",
    stateless_http=True,
    host="0.0.0.0",
    port=8001,
)

# ── Demo 数据（后续对接数据库） ──

ROOT = Path(__file__).resolve().parent.parent  # backend/


def _get_strategies():
    return [
        {"id": "etf-v6f", "name": "ETF Rotation V6F", "version": "V6F",
         "sharpe": 2.50, "alpha": 16.9, "max_dd": -5.0, "annual": 19.57, "status": "ACTIVE"},
        {"id": "mf-v25", "name": "Multi-Factor V25", "version": "V25",
         "sharpe": 2.10, "alpha": 12.5, "max_dd": -18.5, "annual": 15.04, "status": "ACTIVE"},
        {"id": "fundamental-v20", "name": "基本面精选 V20", "version": "V20",
         "sharpe": 1.75, "alpha": 8.2, "max_dd": -12.3, "annual": 11.70, "status": "WATCHLIST"},
        {"id": "northbound-v10", "name": "北向资金 V10", "version": "V10",
         "sharpe": 1.50, "alpha": 6.8, "max_dd": -10.1, "annual": 8.90, "status": "WATCHLIST"},
        {"id": "momentum-v8", "name": "动量反转 V8", "version": "V8",
         "sharpe": 0.50, "alpha": -1.2, "max_dd": -22.0, "annual": -5.30, "status": "RETIRED"},
        {"id": "ml-v3", "name": "ML Ensemble V3", "version": "V3",
         "sharpe": 0.20, "alpha": -3.5, "max_dd": -28.0, "annual": -12.00, "status": "RETIRED"},
    ]


def _get_equity_curve(seed: float = 10_000_000, days: int = 120):
    random.seed(42)
    dates, values, val = [], [], seed
    start = datetime.now() - timedelta(days=days)
    for i in range(days):
        d = start + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        dates.append(d.strftime("%Y-%m-%d"))
        val += val * random.uniform(-0.005, 0.012)
        values.append(round(val, 2))
    return [{"date": d, "value": v} for d, v in zip(dates, values)]


# ══════════════════════════════════════════════
#  Tool 1: 仪表盘总览
# ══════════════════════════════════════════════

@mcp.tool()
def get_dashboard_summary() -> dict:
    """获取青鳄量化核心仪表盘数据：总资产、年化收益、夏普比率、最大回撤、胜率、活跃策略数。"""
    strategies = _get_strategies()
    active = [s for s in strategies if s["status"] == "ACTIVE"]
    return {
        "total_asset": 10_284_500.00,
        "daily_profit": 284_500.00,
        "annual_return": 18.2,
        "sharpe_ratio": 2.15,
        "max_drawdown": -8.5,
        "win_rate": 62.3,
        "position_count": 12,
        "running_strategies": len(active),
        "top_strategy": active[0]["name"] if active else "N/A",
    }


# ══════════════════════════════════════════════
#  Tool 2: 权益曲线
# ══════════════════════════════════════════════

@mcp.tool()
def get_equity_curve(months: int = 6) -> dict:
    """获取权益曲线数据，用于绘制资产增长图。

    Args:
        months: 时间范围(月)，默认6个月
    """
    days = months * 21  # approx trading days
    points = _get_equity_curve(days=min(days, 252))
    start_val = points[0]["value"] if points else 10_000_000
    end_val = points[-1]["value"] if points else 10_000_000
    return {
        "points": points,
        "start_value": round(start_val, 2),
        "end_value": round(end_val, 2),
        "total_return_pct": round((end_val - start_val) / start_val * 100, 2),
        "count": len(points),
    }


# ══════════════════════════════════════════════
#  Tool 3: 策略列表
# ══════════════════════════════════════════════

@mcp.tool()
def get_strategies(status: str = "all") -> dict:
    """获取策略列表，支持按状态筛选(ACTIVE/WATCHLIST/RETIRED)。

    Args:
        status: 状态筛选(all/ACTIVE/WATCHLIST/RETIRED)
    """
    strategies = _get_strategies()
    if status.upper() != "ALL":
        strategies = [s for s in strategies if s["status"] == status.upper()]
    return {
        "strategies": strategies,
        "count": len(strategies),
        "active_count": sum(1 for s in strategies if s["status"] == "ACTIVE"),
        "total_alpha": sum(s["alpha"] for s in strategies if s["status"] == "ACTIVE"),
    }


# ══════════════════════════════════════════════
#  Tool 4: 风险警报
# ══════════════════════════════════════════════

@mcp.tool()
def get_risk_alerts() -> dict:
    """获取当前风险警报列表，包含级别、标题和详情。"""
    return {
        "alerts": [
            {"level": "warning", "title": "最大回撤偏高", "desc": "当前回撤 8.5%，建议关注", "time": "2026-06-08 15:00"},
            {"level": "info", "title": "ETF Rotation V6F 强势", "desc": "近30日 Alpha +16.9%，排名第一", "time": "2026-06-08 09:30"},
            {"level": "info", "title": "市场波动率上升", "desc": "沪深300 20日波动率升至 22%", "time": "2026-06-07 15:30"},
        ],
        "total": 3,
        "warning_count": 1,
    }


# ══════════════════════════════════════════════
#  Tool 5: 持仓查询
# ══════════════════════════════════════════════

@mcp.tool()
def get_positions(market: str = "A") -> dict:
    """获取当前投资组合持仓明细。

    Args:
        market: 市场(A=全部A股 / SH=沪市 / SZ=深市)
    """
    all_positions = [
        {"symbol": "600519.SH", "name": "贵州茅台", "shares": 500, "price": 1850.00,
         "cost": 1700.00, "pnl_pct": 8.82, "weight_pct": 12.3, "market": "SH"},
        {"symbol": "000858.SZ", "name": "五粮液", "shares": 2000, "price": 152.00,
         "cost": 145.00, "pnl_pct": 4.83, "weight_pct": 9.8, "market": "SZ"},
        {"symbol": "601318.SH", "name": "中国平安", "shares": 3000, "price": 48.50,
         "cost": 50.20, "pnl_pct": -3.39, "weight_pct": 7.1, "market": "SH"},
        {"symbol": "159915.SZ", "name": "创业板ETF", "shares": 10000, "price": 2.85,
         "cost": 2.60, "pnl_pct": 9.62, "weight_pct": 5.4, "market": "SZ"},
        {"symbol": "600036.SH", "name": "招商银行", "shares": 2000, "price": 42.80,
         "cost": 40.00, "pnl_pct": 7.00, "weight_pct": 10.2, "market": "SH"},
    ]
    if market.upper() != "A":
        all_positions = [p for p in all_positions if p["market"] == market.upper()]
    total_value = sum(p["shares"] * p["price"] for p in all_positions)
    return {"positions": all_positions, "count": len(all_positions), "total_value": round(total_value, 2)}


# ══════════════════════════════════════════════
#  Tool 6: Alpha Factory
# ══════════════════════════════════════════════

@mcp.tool()
def get_alpha_factory() -> dict:
    """获取 Alpha Factory 完整数据：活跃策略、观察池、退役池及统计。"""
    strategies = _get_strategies()
    active = [s for s in strategies if s["status"] == "ACTIVE"]
    watchlist = [s for s in strategies if s["status"] == "WATCHLIST"]
    retired = [s for s in strategies if s["status"] == "RETIRED"]

    return {
        "active": {"count": len(active), "strategies": active, "total_alpha": round(sum(s["alpha"] for s in active), 2)},
        "watchlist": {"count": len(watchlist), "strategies": watchlist},
        "retired": {"count": len(retired), "strategies": retired},
        "total": len(strategies),
    }


# ══════════════════════════════════════════════
#  Tool 7: 回测执行
# ══════════════════════════════════════════════

@mcp.tool()
def run_backtest(
    symbol: str = "600519.SH",
    start_date: str = "2025-01-01",
    end_date: str = "2026-06-01",
    initial_capital: float = 1_000_000,
    strategy: str = "ma_cross",
    fast_period: int = 5,
    slow_period: int = 20,
) -> dict:
    """运行回测，返回策略在指定区间的绩效指标。

    Args:
        symbol: 股票代码(如 600519.SH)
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        initial_capital: 初始资金
        strategy: 策略类型(ma_cross=双均线 / momentum=动量 / mean_reversion=均值回归)
        fast_period: 快线周期(仅ma_cross)
        slow_period: 慢线周期(仅ma_cross)
    """
    # Demo 回测结果
    random.seed(hash(symbol + strategy + start_date) % 10000)
    total_return = random.uniform(-15, 45)
    sharpe = random.uniform(-1, 3)
    max_dd = random.uniform(-30, -3)
    trades = int(random.uniform(20, 200))
    wins = int(trades * random.uniform(0.3, 0.7))

    return {
        "symbol": symbol,
        "strategy": strategy,
        "period": f"{start_date} → {end_date}",
        "initial_capital": initial_capital,
        "final_capital": round(initial_capital * (1 + total_return / 100), 2),
        "total_return_pct": round(total_return, 2),
        "annual_return_pct": round(total_return * 0.8, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "total_trades": trades,
        "win_rate_pct": round(wins / max(trades, 1) * 100, 1),
        "avg_profit_per_trade": round(total_return * initial_capital / 100 / max(trades, 1), 2),
    }


# ══════════════════════════════════════════════
#  Tool 8: 风险指标
# ══════════════════════════════════════════════

@mcp.tool()
def get_risk_metrics() -> dict:
    """获取综合风险指标：回撤分析、VaR、CVaR、波动率、各策略风险贡献。"""
    random.seed(42)
    return {
        "risk_score": 82,
        "current_drawdown_pct": -3.2,
        "max_drawdown_pct": -8.5,
        "var_95_daily": -2.1,
        "cvar_95_daily": -3.8,
        "annual_volatility": 15.4,
        "beta_to_hs300": 0.89,
        "risk_contributions": [
            {"strategy": "ETF Rotation V6F", "weight": 40, "risk_contribution": 28},
            {"strategy": "Multi-Factor V25", "weight": 35, "risk_contribution": 42},
            {"strategy": "基本面精选 V20", "weight": 15, "risk_contribution": 18},
            {"strategy": "北向资金 V10", "weight": 10, "risk_contribution": 12},
        ],
    }


# ══════════════════════════════════════════════
#  Tool 9: 市场数据查询
# ══════════════════════════════════════════════

@mcp.tool()
def get_market_data(symbol: str, days: int = 30) -> dict:
    """查询A股股票近期行情数据（OHLCV）。

    Args:
        symbol: 股票代码(如 600519.SH / 000858.SZ)
        days: 返回最近 N 个交易日数据
    """
    random.seed(hash(symbol) % 10000)
    base_price = {
        "600519.SH": 1850, "000858.SZ": 152, "601318.SH": 48.5,
        "159915.SZ": 2.85, "600036.SH": 42.8, "510300.SH": 4.12,
    }.get(symbol, 50.0)

    klines = []
    price = base_price * random.uniform(0.9, 1.1)
    for i in range(min(days, 60)):
        date = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
        change = price * random.uniform(-0.03, 0.03)
        open_p = price
        close_p = price + change
        high = max(open_p, close_p) + abs(change) * random.uniform(0, 0.5)
        low = min(open_p, close_p) - abs(change) * random.uniform(0, 0.5)
        volume = int(random.uniform(5000000, 50000000))
        klines.append({
            "date": date, "open": round(open_p, 2), "high": round(high, 2),
            "low": round(low, 2), "close": round(close_p, 2), "volume": volume,
        })
        price = close_p

    return {
        "symbol": symbol,
        "latest_price": klines[-1]["close"],
        "data": klines,
        "count": len(klines),
    }
