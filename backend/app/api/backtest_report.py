"""回测报告API - Sprint-3 Task-2

/api/backtest/result/{id}
"""
import json, os
from typing import Optional


def get_backtest_result(result_id: str = "latest") -> Optional[dict]:
    """获取回测结果

    Args:
        result_id: 结果ID，目前只支持 "latest"

    Returns:
        回测结果dict
    """
    result_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'backtest_result.json'
    )

    if not os.path.exists(result_file):
        return None

    with open(result_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_report(result: dict) -> dict:
    """格式化回测报告为API响应格式"""
    metrics = result.get("metrics", {})
    return {
        "strategy": result.get("strategy", ""),
        "symbols": result.get("symbols", []),
        "period": result.get("period", ""),
        "commission": result.get("commission", 0),
        "slippage": result.get("slippage", 0),
        "lookback": result.get("lookback", 0),
        "annual_return": f"{metrics.get('annual_return', 0):.2f}%",
        "total_return": f"{metrics.get('total_return', 0):.2f}%",
        "max_drawdown": f"{metrics.get('max_drawdown', 0):.2f}%",
        "sharpe_ratio": metrics.get("sharpe_ratio", 0),
        "win_rate": f"{metrics.get('win_rate', 0):.1f}%",
        "trade_count": metrics.get("trade_count", 0),
        "trading_days": metrics.get("trading_days", 0),
        "years": metrics.get("years", 0),
        "initial_cash": metrics.get("initial_cash", 0),
        "final_value": metrics.get("final_value", 0),
        "equity_curve": result.get("equity_curve_sample", []),
        "drawdown_curve": result.get("drawdown_curve_sample", []),
        "trades": result.get("trades", []),
        "annual_returns": result.get("annual_returns", {}),
        "generated_at": result.get("generated_at", ""),
    }
