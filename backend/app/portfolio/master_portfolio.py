"""MasterPortfolio - 多账户聚合

将不同市场、不同券商的账户聚合为统一视图：
- A001 (A股/QMT/CNY)
- HK001 (港股/Futu/HKD)
- US001 (美股/IBKR/USD)
- C001 (加密/Binance/USDT)

Dashboard显示：
- 总资产
- 今日收益
- 风险暴露
- 市场分布
"""
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class AccountSummary:
    """单个账户摘要"""
    account_id: str
    market: str         # "A股" / "港股" / "美股" / "加密"
    broker: str         # "qmt" / "futu" / "ibkr" / "binance"
    currency: str       # "CNY" / "HKD" / "USD" / "USDT"
    cash: float = 0
    invested: float = 0
    total: float = 0
    pnl_today: float = 0
    pnl_pct_today: float = 0
    position_count: int = 0
    # 汇率（用于聚合）
    fx_rate: float = 1.0  # 相对于基准币种


class MasterPortfolio:
    """多账户聚合组合

    聚合所有市场的账户为统一视图。
    基准币种默认CNY，可切换USD。
    """

    # 简化汇率表（生产环境应实时获取）
    FX_RATES = {
        "CNY": 1.0,
        "USD": 7.25,
        "HKD": 0.93,
        "USDT": 7.25,
    }

    def __init__(self, base_currency: str = "CNY"):
        self.base_currency = base_currency
        self.accounts: Dict[str, AccountSummary] = {}

    def add_account(self, account: AccountSummary):
        """注册账户"""
        self.accounts[account.account_id] = account

    def update_account(self, account_id: str, cash: float, invested: float,
                       pnl_today: float = 0, position_count: int = 0):
        """更新账户数据"""
        if account_id in self.accounts:
            acc = self.accounts[account_id]
            acc.cash = cash
            acc.invested = invested
            acc.total = cash + invested
            acc.pnl_today = pnl_today
            acc.pnl_pct_today = (pnl_today / acc.total * 100) if acc.total > 0 else 0
            acc.position_count = position_count

    def _to_base(self, amount: float, currency: str) -> float:
        """转换为基准币种"""
        if currency == self.base_currency:
            return amount
        rate = self.FX_RATES.get(currency, 1.0)
        base_rate = self.FX_RATES.get(self.base_currency, 1.0)
        return amount * rate / base_rate

    def get_total_value(self) -> float:
        """总资产（基准币种）"""
        return sum(
            self._to_base(acc.total, acc.currency)
            for acc in self.accounts.values()
        )

    def get_total_cash(self) -> float:
        return sum(
            self._to_base(acc.cash, acc.currency)
            for acc in self.accounts.values()
        )

    def get_total_invested(self) -> float:
        return sum(
            self._to_base(acc.invested, acc.currency)
            for acc in self.accounts.values()
        )

    def get_total_pnl_today(self) -> float:
        return sum(
            self._to_base(acc.pnl_today, acc.currency)
            for acc in self.accounts.values()
        )

    def get_market_distribution(self) -> Dict[str, float]:
        """市场分布（百分比）"""
        total = self.get_total_value()
        if total <= 0:
            return {}
        dist = {}
        for acc in self.accounts.values():
            mkt = acc.market
            value = self._to_base(acc.total, acc.currency)
            dist[mkt] = dist.get(mkt, 0) + value / total * 100
        return {k: round(v, 2) for k, v in dist.items()}

    def get_dashboard(self) -> dict:
        """Dashboard数据"""
        total = self.get_total_value()
        return {
            "base_currency": self.base_currency,
            "total_value": round(total, 2),
            "total_cash": round(self.get_total_cash(), 2),
            "total_invested": round(self.get_total_invested(), 2),
            "pnl_today": round(self.get_total_pnl_today(), 2),
            "pnl_pct_today": round(self.get_total_pnl_today() / total * 100, 2) if total > 0 else 0,
            "account_count": len(self.accounts),
            "market_distribution": self.get_market_distribution(),
            "accounts": [
                {
                    "id": acc.account_id,
                    "market": acc.market,
                    "broker": acc.broker,
                    "currency": acc.currency,
                    "total": round(acc.total, 2),
                    "pnl_today": round(acc.pnl_today, 2),
                    "positions": acc.position_count,
                }
                for acc in self.accounts.values()
            ],
        }
