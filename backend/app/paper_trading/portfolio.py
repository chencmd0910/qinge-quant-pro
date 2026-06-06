"""Paper Portfolio - Top5 Diversified Portfolio

组合配置:
    Top1 量价策略    20%
    Top2 基本面策略  20%
    Top3 资金流策略  20%
    Top4 动量策略    20%
    Top5 北向策略    20%

等权配置，每日调仓检查。
"""
from typing import Dict, List, Optional
from datetime import datetime
import json, os


# Top5 Diversified 策略定义
TOP5_STRATEGIES = [
    {
        "id": "top1_volume_price",
        "name": "量价_6F_biweekly",
        "cluster": "Volume/Price",
        "weight": 0.20,
        "annual_return": 19.57,
        "sharpe": 2.500,
        "alpha": 16.924,
        "factors": ["volume_ratio", "money_flow", "mom_5d", "mom_10d", "volatility_20d", "daily_sharpe"],
    },
    {
        "id": "top2_fundamental",
        "name": "基本面_5F_biweekly",
        "cluster": "Fundamental",
        "weight": 0.20,
        "annual_return": 15.04,
        "sharpe": 1.594,
        "alpha": 12.595,
        "factors": ["pe_ttm", "pb_ttm", "industry_revenue_growth", "industry_profit_growth", "industry_pmi"],
    },
    {
        "id": "top3_fund_flow",
        "name": "资金流_4F_biweekly",
        "cluster": "Fund Flow",
        "weight": 0.20,
        "annual_return": 11.73,
        "sharpe": 1.704,
        "alpha": 10.986,
        "factors": ["money_flow", "northbound_net_buy", "margin_balance_chg", "volume_ratio"],
    },
    {
        "id": "top4_momentum",
        "name": "动量_5F_weekly",
        "cluster": "Momentum",
        "weight": 0.20,
        "annual_return": 11.06,
        "sharpe": 1.612,
        "alpha": 10.123,
        "factors": ["mom_5d", "mom_10d", "consistency", "mom_20d", "volume_ratio"],
    },
    {
        "id": "top5_northbound",
        "name": "北向_4F_biweekly",
        "cluster": "Northbound Flow",
        "weight": 0.20,
        "annual_return": 10.50,
        "sharpe": 1.500,
        "alpha": 8.200,
        "factors": ["northbound_net_buy", "northbound_holding_chg", "margin_balance_chg", "volume_ratio"],
    },
]


class PaperPortfolio:
    """Paper Trading Portfolio

    管理Top5等权组合的模拟盘。
    """

    def __init__(self, initial_cash: float = 1_000_000,
                 data_dir: str = None):
        self.initial_cash = initial_cash
        self.strategies = TOP5_STRATEGIES
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'paper_campaign'
        )
        os.makedirs(self.data_dir, exist_ok=True)

        # 状态
        self.cash = initial_cash
        self.positions: Dict[str, dict] = {}  # symbol -> {quantity, avg_cost, current_price}
        self.equity_history: List[dict] = []
        self.trade_history: List[dict] = []
        self.daily_reports: List[dict] = []

        # 加载历史状态
        self._state_file = os.path.join(self.data_dir, 'portfolio_state.json')
        self._load_state()

    def _load_state(self):
        if os.path.exists(self._state_file):
            with open(self._state_file, 'r') as f:
                state = json.load(f)
                self.cash = state.get('cash', self.initial_cash)
                self.positions = state.get('positions', {})
                self.equity_history = state.get('equity_history', [])
                self.trade_history = state.get('trade_history', [])

    def _save_state(self):
        state = {
            'cash': self.cash,
            'positions': self.positions,
            'equity_history': self.equity_history[-500:],  # 保留最近500天
            'trade_history': self.trade_history[-1000:],
        }
        with open(self._state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def get_total_value(self) -> float:
        """当前总净值"""
        invested = sum(
            p.get('current_price', p.get('avg_cost', 0)) * p.get('quantity', 0)
            for p in self.positions.values()
        )
        return self.cash + invested

    def update_prices(self, prices: Dict[str, float]):
        """更新持仓价格"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol]['current_price'] = price

    def snapshot(self, date_str: str) -> dict:
        """每日快照"""
        total = self.get_total_value()
        invested = total - self.cash
        pnl = total - self.initial_cash
        pnl_pct = (total / self.initial_cash - 1) * 100

        # 日收益
        prev = self.equity_history[-1]['total'] if self.equity_history else self.initial_cash
        daily_return = (total / prev - 1) * 100 if prev > 0 else 0

        # 回撤
        peak = max((h['total'] for h in self.equity_history), default=self.initial_cash)
        peak = max(peak, total)
        drawdown = (peak - total) / peak * 100 if peak > 0 else 0

        snapshot = {
            'date': date_str,
            'cash': round(self.cash, 2),
            'invested': round(invested, 2),
            'total': round(total, 2),
            'pnl': round(pnl, 2),
            'pnl_pct': round(pnl_pct, 2),
            'daily_return': round(daily_return, 2),
            'drawdown': round(drawdown, 2),
            'position_count': len([p for p in self.positions.values() if p.get('quantity', 0) > 0]),
            'positions': {
                s: {
                    'quantity': p.get('quantity', 0),
                    'avg_cost': round(p.get('avg_cost', 0), 4),
                    'current_price': round(p.get('current_price', p.get('avg_cost', 0)), 4),
                    'market_value': round(p.get('current_price', p.get('avg_cost', 0)) * p.get('quantity', 0), 2),
                    'pnl_pct': round(
                        ((p.get('current_price', p.get('avg_cost', 0)) / p.get('avg_cost', 1)) - 1) * 100, 2
                    ) if p.get('avg_cost', 0) > 0 else 0,
                }
                for s, p in self.positions.items()
                if p.get('quantity', 0) > 0
            },
        }

        self.equity_history.append(snapshot)
        self._save_state()
        return snapshot

    def get_strategy_allocation(self) -> List[dict]:
        """获取策略配置"""
        return [
            {
                'id': s['id'],
                'name': s['name'],
                'cluster': s['cluster'],
                'weight': s['weight'],
                'target_value': round(self.get_total_value() * s['weight'], 2),
                'annual_return': s['annual_return'],
                'sharpe': s['sharpe'],
                'alpha': s['alpha'],
            }
            for s in self.strategies
        ]

    def get_performance_summary(self, days: int = None) -> dict:
        """绩效摘要"""
        history = self.equity_history[-days:] if days else self.equity_history
        if not history:
            return {}

        first = history[0]
        last = history[-1]
        values = [h['total'] for h in history]

        # 年化收益
        total_return = (last['total'] / first['total'] - 1) * 100
        years = len(values) / 252
        annual_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100 if years > 0 else 0

        # 夏普
        returns = [h['daily_return'] for h in history]
        mean_ret = sum(returns) / len(returns) if returns else 0
        std_ret = (sum((r - mean_ret)**2 for r in returns) / len(returns)) ** 0.5 if len(returns) > 1 else 1
        sharpe = (mean_ret / std_ret * (252**0.5)) if std_ret > 0 else 0

        # 最大回撤
        max_dd = max(h['drawdown'] for h in history) if history else 0

        return {
            'start_date': first['date'],
            'end_date': last['date'],
            'trading_days': len(history),
            'initial_value': first['total'],
            'final_value': round(last['total'], 2),
            'total_return': round(total_return, 2),
            'annual_return': round(annual_return, 2),
            'sharpe': round(sharpe, 3),
            'max_drawdown': round(max_dd, 2),
            'avg_daily_return': round(mean_ret, 4),
            'daily_volatility': round(std_ret, 4),
        }
