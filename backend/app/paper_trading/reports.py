"""Paper Campaign Reports - 日报/周报/30天验证

Task-3: Daily Report (paper_reports/YYYY-MM-DD.json)
Task-4: Weekly Review
Task-5: 30-Day Validation
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json, os


class DailyReportGenerator:
    """每日风险报告"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.reports_dir = os.path.join(data_dir, 'paper_reports')
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate(self, date_str: str, portfolio_snapshot: dict,
                 risk_score: int = 80, alerts: List[str] = None) -> dict:
        """生成每日报告

        Args:
            date_str: 日期
            portfolio_snapshot: PaperPortfolio.snapshot() 返回值
            risk_score: 风险评分 (0-100)
            alerts: 告警列表

        Returns:
            日报dict
        """
        report = {
            'report_type': 'daily',
            'date': date_str,
            'generated_at': datetime.now().isoformat(),
            'equity': portfolio_snapshot.get('total', 0),
            'cash': portfolio_snapshot.get('cash', 0),
            'invested': portfolio_snapshot.get('invested', 0),
            'daily_return': portfolio_snapshot.get('daily_return', 0),
            'cumulative_return': portfolio_snapshot.get('pnl_pct', 0),
            'drawdown': portfolio_snapshot.get('drawdown', 0),
            'risk_score': risk_score,
            'position_count': portfolio_snapshot.get('position_count', 0),
            'positions': portfolio_snapshot.get('positions', {}),
            'alerts': alerts or [],
        }

        # 保存到文件
        filepath = os.path.join(self.reports_dir, f'{date_str}.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report


class WeeklyReviewGenerator:
    """每周回顾"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.reports_dir = os.path.join(data_dir, 'paper_reports')
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate(self, week_ending: str, daily_reports: List[dict],
                 benchmark_annual: float = 2.5) -> dict:
        """生成周报

        Args:
            week_ending: 周结束日期
            daily_reports: 本周每日报告列表
            benchmark_annual: 基准年化收益
        """
        if not daily_reports:
            return {}

        first = daily_reports[0]
        last = daily_reports[-1]

        # 周收益
        week_return = (last['equity'] / first['equity'] - 1) * 100 if first['equity'] > 0 else 0

        # 周波动率
        returns = [r['daily_return'] for r in daily_reports]
        mean_ret = sum(returns) / len(returns)
        std_ret = (sum((r - mean_ret)**2 for r in returns) / len(returns)) ** 0.5 if len(returns) > 1 else 0

        # 周最大回撤
        max_dd = max(r['drawdown'] for r in daily_reports)

        # 年化Sharpe (周数据)
        sharpe = (mean_ret / std_ret * (252**0.5)) if std_ret > 0 else 0

        # 行业暴露 (从最新日报取)
        sector_exposure = {}
        for r in daily_reports:
            for sym, pos in r.get('positions', {}).items():
                sector = '宽基'  # 简化
                sector_exposure[sector] = sector_exposure.get(sector, 0) + pos.get('market_value', 0)

        total_invested = sum(sector_exposure.values())
        if total_invested > 0:
            sector_exposure = {k: round(v / total_invested * 100, 2) for k, v in sector_exposure.items()}

        # Alpha (周化)
        week_benchmark = benchmark_annual / 52  # 周化基准
        alpha = week_return - week_benchmark

        review = {
            'report_type': 'weekly',
            'week_ending': week_ending,
            'generated_at': datetime.now().isoformat(),
            'trading_days': len(daily_reports),
            'start_equity': first['equity'],
            'end_equity': last['equity'],
            'week_return': round(week_return, 2),
            'alpha': round(alpha, 2),
            'sharpe': round(sharpe, 3),
            'max_drawdown': round(max_dd, 2),
            'daily_volatility': round(std_ret, 4),
            'sector_exposure': sector_exposure,
            'risk_score': last.get('risk_score', 0),
            'alerts': [a for r in daily_reports for a in r.get('alerts', [])],
        }

        # 保存
        filepath = os.path.join(self.reports_dir, f'weekly_{week_ending}.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(review, f, ensure_ascii=False, indent=2)

        return review


class Validation30Day:
    """30天验证"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.reports_dir = os.path.join(data_dir, 'paper_reports')
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate(self, daily_reports: List[dict],
                 target_days: int = 30) -> dict:
        """生成30天验证报告

        Args:
            daily_reports: 所有每日报告
            target_days: 目标天数

        Returns:
            验证报告
        """
        if len(daily_reports) < target_days:
            return {
                'report_type': 'validation_30d',
                'status': 'INCOMPLETE',
                'days_run': len(daily_reports),
                'days_required': target_days,
                'message': f'需要{target_days}天数据，当前{len(daily_reports)}天',
            }

        # 取最近30天
        reports = daily_reports[-target_days:]
        first = reports[0]
        last = reports[-1]

        # 总收益
        total_return = (last['equity'] / first['equity'] - 1) * 100

        # 年化收益
        years = target_days / 252
        annual_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100 if years > 0 else 0

        # 夏普
        returns = [r['daily_return'] for r in reports]
        mean_ret = sum(returns) / len(returns)
        std_ret = (sum((r - mean_ret)**2 for r in returns) / len(returns)) ** 0.5 if len(returns) > 1 else 1
        sharpe = (mean_ret / std_ret * (252**0.5)) if std_ret > 0 else 0

        # 最大回撤
        max_dd = max(r['drawdown'] for r in reports)

        # Alpha (vs 沪深300 年化约2.5%)
        benchmark_30d = 2.5 * target_days / 252
        alpha = annual_return - 2.5

        # 晋级判断
        is_live_candidate = (
            total_return > 0 and
            sharpe > 0.5 and
            max_dd < 20 and
            alpha > 0
        )

        validation = {
            'report_type': 'validation_30d',
            'status': 'COMPLETE',
            'generated_at': datetime.now().isoformat(),
            'period': f'{first["date"]} ~ {last["date"]}',
            'trading_days': target_days,
            'initial_equity': first['equity'],
            'final_equity': last['equity'],
            'total_return': round(total_return, 2),
            'annual_return': round(annual_return, 2),
            'sharpe': round(sharpe, 3),
            'max_drawdown': round(max_dd, 2),
            'alpha': round(alpha, 2),
            'avg_risk_score': round(sum(r.get('risk_score', 0) for r in reports) / len(reports), 1),
            'criteria': {
                'total_return_positive': total_return > 0,
                'sharpe_above_0_5': sharpe > 0.5,
                'drawdown_below_20': max_dd < 20,
                'alpha_positive': alpha > 0,
            },
            'is_live_candidate': is_live_candidate,
            'recommendation': 'LIVE_CANDIDATE' if is_live_candidate else 'CONTINUE_PAPER',
        }

        # 保存
        filepath = os.path.join(self.reports_dir, 'validation_30d.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(validation, f, ensure_ascii=False, indent=2)

        return validation
