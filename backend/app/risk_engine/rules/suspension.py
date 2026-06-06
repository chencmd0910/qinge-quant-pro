"""A股风控规则 - 停牌/ST检查"""


def check_suspended(symbol: str, is_suspended: bool) -> tuple:
    """停牌检查"""
    if is_suspended:
        return False, f"{symbol} 停牌，无法交易"
    return True, ""


def check_st(symbol: str, name: str) -> tuple:
    """ST股检查

    ST/*ST 股票涨跌停幅度为5%，且风险较高。
    默认拒绝交易ST股，可在配置中开启。
    """
    if name and ("ST" in name.upper() or "*ST" in name.upper()):
        return False, f"{symbol} ({name}) 为ST股，默认拒绝交易"
    return True, ""


def check_new_stock(symbol: str, listing_days: int) -> tuple:
    """新股检查（上市不足5个交易日的新股风险较大）"""
    if listing_days < 5:
        return False, f"{symbol} 上市仅{listing_days}天，新股风险较大"
    return True, ""
