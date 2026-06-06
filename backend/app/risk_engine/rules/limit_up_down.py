"""A股风控规则 - 涨跌停检查"""
from ..risk_manager import RiskConfig


def check_limit_up(symbol: str, current_price: float, prev_close: float) -> bool:
    """检查是否涨停（涨幅>=9.8%视为涨停）"""
    if prev_close <= 0:
        return False
    change_pct = (current_price - prev_close) / prev_close * 100
    return change_pct >= 9.8


def check_limit_down(symbol: str, current_price: float, prev_close: float) -> bool:
    """检查是否跌停（跌幅<=-9.8%视为跌停）"""
    if prev_close <= 0:
        return False
    change_pct = (current_price - prev_close) / prev_close * 100
    return change_pct <= -9.8


def can_buy(symbol: str, current_price: float, prev_close: float) -> tuple:
    """买入前检查：涨停不能买

    Returns:
        (can_trade: bool, reason: str)
    """
    if check_limit_up(symbol, current_price, prev_close):
        return False, f"{symbol} 涨停，无法买入"
    return True, ""


def can_sell(symbol: str, current_price: float, prev_close: float) -> tuple:
    """卖出前检查：跌停不能卖

    Returns:
        (can_trade: bool, reason: str)
    """
    if check_limit_down(symbol, current_price, prev_close):
        return False, f"{symbol} 跌停，无法卖出"
    return True, ""
