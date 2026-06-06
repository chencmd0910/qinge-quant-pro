import math
from typing import List, Dict


def calc_returns(values):
    return [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values)) if values[i-1] > 0]

def total_return(values):
    return (values[-1] - values[0]) / values[0] if values and values[0] > 0 else 0

def annual_return(values, trading_days=252):
    if not values or len(values) < 2 or values[0] == 0: return 0
    return (values[-1] / values[0]) ** (trading_days / len(values)) - 1

def max_drawdown(values):
    if not values: return 0
    peak = values[0]
    mdd = 0
    for v in values:
        if v > peak: peak = v
        dd = (peak - v) / peak if peak > 0 else 0
        if dd > mdd: mdd = dd
    return mdd

def sharpe_ratio(values, rf=0.03, td=252):
    returns = calc_returns(values)
    if len(returns) < 2: return 0
    avg = sum(returns) / len(returns)
    std = math.sqrt(sum((r - avg)**2 for r in returns) / (len(returns) - 1))
    return (avg - rf / td) / std * math.sqrt(td) if std > 0 else 0

def sortino_ratio(values, rf=0.03, td=252):
    returns = calc_returns(values)
    if len(returns) < 2: return 0
    avg = sum(returns) / len(returns)
    drf = rf / td
    ds = math.sqrt(sum(min(0, r - drf)**2 for r in returns) / len(returns))
    return (avg - drf) / ds * math.sqrt(td) if ds > 0 else 0

def calmar_ratio(values, td=252):
    ar = annual_return(values, td)
    mdd = max_drawdown(values)
    return ar / mdd if mdd > 0 else 0

def _get_trade_side(t):
    return t.side if hasattr(t, 'side') else t.get('side', '')

def _get_trade_pnl(t):
    return t.pnl if hasattr(t, 'pnl') else t.get('pnl', 0)

def win_rate(trades):
    sells = [t for t in trades if _get_trade_side(t) == 'SELL']
    return sum(1 for t in sells if _get_trade_pnl(t) > 0) / len(sells) if sells else 0

def profit_loss_ratio(trades):
    sells = [t for t in trades if _get_trade_side(t) == 'SELL']
    profits = [_get_trade_pnl(t) for t in sells if _get_trade_pnl(t) > 0]
    losses = [abs(_get_trade_pnl(t)) for t in sells if _get_trade_pnl(t) < 0]
    if not profits or not losses: return 0
    return (sum(profits) / len(profits)) / (sum(losses) / len(losses))

def calc_all_metrics(values, trades):
    return {
        'total_return': round(total_return(values) * 100, 2),
        'annual_return': round(annual_return(values) * 100, 2),
        'max_drawdown': round(max_drawdown(values) * 100, 2),
        'sharpe_ratio': round(sharpe_ratio(values), 2),
        'sortino_ratio': round(sortino_ratio(values), 2),
        'calmar_ratio': round(calmar_ratio(values), 2),
        'win_rate': round(win_rate(trades) * 100, 2),
        'profit_loss_ratio': round(profit_loss_ratio(trades), 2),
        'total_trades': len([t for t in trades if _get_trade_side(t) == 'SELL']),
    }
