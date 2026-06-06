"""A股市场规则 - 涨跌停/T+1/停牌/ST

A股特有规则，其他市场不需要。
"""
from enum import Enum


class AShareRule:
    """A股市场规则"""

    # 涨跌停幅度
    LIMIT_PCT_NORMAL = 10.0    # 主板 10%
    LIMIT_PCT_STAR = 20.0      # 科创板/创业板 20%
    LIMIT_PCT_ST = 5.0         # ST股 5%

    @staticmethod
    def is_limit_up(change_pct: float, is_st: bool = False, is_star: bool = False) -> bool:
        """是否涨停"""
        limit = AShareRule.LIMIT_PCT_ST if is_st else (ASHareRule.LIMIT_PCT_STAR if is_star else AShareRule.LIMIT_PCT_NORMAL)
        return change_pct >= limit - 0.2  # 允许0.2%误差

    @staticmethod
    def is_limit_down(change_pct: float, is_st: bool = False, is_star: bool = False) -> bool:
        """是否跌停"""
        limit = AShareRule.LIMIT_PCT_ST if is_st else (ASHareRule.LIMIT_PCT_STAR if is_star else AShareRule.LIMIT_PCT_NORMAL)
        return change_pct <= -(limit - 0.2)

    @staticmethod
    def can_buy(change_pct: float, is_st: bool = False, is_star: bool = False) -> tuple:
        """买入检查: 涨停不能买"""
        if AShareRule.is_limit_up(change_pct, is_st, is_star):
            return False, "涨停，无法买入"
        return True, ""

    @staticmethod
    def can_sell(change_pct: float, is_st: bool = False, is_star: bool = False) -> tuple:
        """卖出检查: 跌停不能卖"""
        if AShareRule.is_limit_down(change_pct, is_st, is_star):
            return False, "跌停，无法卖出"
        return True, ""

    @staticmethod
    def check_st(name: str) -> tuple:
        """ST检查"""
        if name and ("ST" in name.upper()):
            return False, "ST股，默认拒绝交易"
        return True, ""

    @staticmethod
    def check_suspended(is_suspended: bool) -> tuple:
        """停牌检查"""
        if is_suspended:
            return False, "停牌，无法交易"
        return True, ""

    @staticmethod
    def is_t1_restricted(buy_date: str, sell_date: str) -> bool:
        """T+1检查: 当天买的不能当天卖"""
        return buy_date == sell_date

    @staticmethod
    def get_board_type(symbol: str) -> str:
        """判断板块类型"""
        code = symbol.split('.')[0] if '.' in symbol else symbol
        if code.startswith('68'):
            return "科创板"  # 20%涨跌停
        elif code.startswith('30'):
            return "创业板"  # 20%涨跌停
        elif code.startswith('8') or code.startswith('4'):
            return "北交所"  # 30%涨跌停
        else:
            return "主板"    # 10%涨跌停
