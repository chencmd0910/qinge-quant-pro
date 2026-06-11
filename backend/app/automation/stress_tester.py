"""
压力测试框架 — 历史情景回放 + 假设冲击 + VaR估算

核心功能:
1. 历史极端情景回放 (2008/2015/2020/2024)
2. 假设压力情景 (市场暴跌/行业崩盘/流动性冻结)
3. 组合 VaR/CVaR 估算
4. 生成压力测试报告

对标: 巴塞尔协议压力测试 / 基金公司风控报告
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger("StressTester")

KLINE_DIR = "/app/data/klines/parquet"
REPORT_DIR = "/app/data/reports"


class StressTester:
    """压力测试引擎"""

    # === A股历史极端事件 ===
    HISTORICAL_SCENARIOS = {
        "2008金融危机": {
            "period": ("2008-01-14", "2008-11-04"),
            "index_drawdown": -0.728,  # 上证跌72.8%
            "description": "全球金融危机，上证从5522跌到1664"
        },
        "2015股灾": {
            "period": ("2015-06-12", "2015-08-26"),
            "index_drawdown": -0.450,  # 上证跌45%
            "description": "杠杆牛市崩盘，千股跌停流动性枯竭"
        },
        "2016熔断": {
            "period": ("2016-01-04", "2016-01-28"),
            "index_drawdown": -0.251,
            "description": "熔断机制引发恐慌，两次熔断"
        },
        "2018贸易战": {
            "period": ("2018-01-29", "2019-01-04"),
            "index_drawdown": -0.319,
            "description": "中美贸易战，全年阴跌"
        },
        "2020疫情": {
            "period": ("2020-01-14", "2020-03-23"),
            "index_drawdown": -0.148,
            "description": "COVID-19 疫情冲击，但A股跌幅小于全球"
        },
        "2024年初暴跌": {
            "period": ("2024-01-02", "2024-02-05"),
            "index_drawdown": -0.150,
            "description": "雪球敲入+量化踩踏，小微盘流动性危机"
        },
    }

    # === 假设压力情景 ===
    HYPOTHETICAL_SCENARIOS = {
        "市场暴跌10%": {"market_shock": -0.10, "sector_shock": 0, "liquidity_discount": 0},
        "市场暴跌20%": {"market_shock": -0.20, "sector_shock": 0, "liquidity_discount": 0},
        "行业崩盘25%": {"market_shock": -0.05, "sector_shock": -0.25, "liquidity_discount": 0},
        "流动性冻结": {"market_shock": -0.15, "sector_shock": 0, "liquidity_discount": -0.10},  # 额外10%流动性折价
        "股债双杀": {"market_shock": -0.12, "sector_shock": -0.10, "liquidity_discount": -0.05},
    }

    def __init__(self, portfolio_value: float = 1_000_000, lookback_days: int = 500):
        self.portfolio_value = portfolio_value
        self.lookback_days = lookback_days

    def run_full_stress_test(self, holdings: List[dict], target_date: str) -> dict:
        """执行完整压力测试

        Args:
            holdings: [{code, weight, name, sector, ...}]
            target_date: 评估日期

        Returns:
            压力测试报告
        """
        if not holdings:
            return {"error": "无持仓数据"}

        target = pd.Timestamp(target_date)
        report = {
            "date": target_date,
            "portfolio_value": self.portfolio_value,
            "holdings_count": len(holdings),
            "historical_scenarios": self._run_historical_scenarios(holdings, target),
            "hypothetical_scenarios": self._run_hypothetical_scenarios(holdings, target),
            "var_analysis": self._compute_var_cvar(holdings, target),
            "concentration_risk": self._analyze_concentration(holdings),
            "summary": {},
        }

        # 生成摘要
        report["summary"] = self._generate_summary(report)

        # 保存报告
        self._save_report(report, target_date)

        return report

    def _run_historical_scenarios(self, holdings: List[dict], target: pd.Timestamp) -> dict:
        """历史情景回放"""
        results = {}

        for scenario_name, scenario in self.HISTORICAL_SCENARIOS.items():
            start_str, end_str = scenario["period"]
            start = pd.Timestamp(start_str)
            end = pd.Timestamp(end_str)

            total_loss = 0.0
            stock_details = []

            for h in holdings:
                code = h["code"]
                weight = h.get("weight", 1.0 / len(holdings))
                hist_ret = self._get_period_return(code, start, end)

                contribution = weight * hist_ret
                total_loss += contribution
                stock_details.append({
                    "code": code,
                    "name": h.get("name", ""),
                    "weight": round(weight, 4),
                    "period_return": round(hist_ret, 4),
                    "contribution": round(contribution, 4),
                })

            results[scenario_name] = {
                "index_drawdown": scenario["index_drawdown"],
                "portfolio_loss": round(total_loss, 4),
                "value_after": round(self.portfolio_value * (1 + total_loss), 0),
                "description": scenario["description"],
                "top_losers": sorted(stock_details, key=lambda x: x["contribution"])[:3],
            }

        return results

    def _run_hypothetical_scenarios(self, holdings: List[dict], target: pd.Timestamp) -> dict:
        """假设压力情景"""
        results = {}

        for scenario_name, params in self.HYPOTHETICAL_SCENARIOS.items():
            market_shock = params["market_shock"]
            sector_shock = params.get("sector_shock", 0)
            liquidity_discount = params.get("liquidity_discount", 0)

            total_loss = 0.0
            stock_details = []

            for h in holdings:
                code = h["code"]
                weight = h.get("weight", 1.0 / len(holdings))
                sector = h.get("sector", "")

                # 用个股Beta估算冲击
                beta = self._get_beta(code, target)
                stock_shock = market_shock * beta

                # 行业额外冲击
                if sector_shock != 0:
                    stock_shock += sector_shock * (0.5 + 0.5 * beta)

                # 流动性折价 (小盘股/高波动额外惩罚)
                if liquidity_discount != 0:
                    vol = self._get_volatility(code, target)
                    liq_penalty = liquidity_discount * max(0, (vol - 0.02) / 0.02)  # 波动越高折价越大
                    stock_shock += liq_penalty

                contribution = weight * stock_shock
                total_loss += contribution
                stock_details.append({
                    "code": code,
                    "name": h.get("name", ""),
                    "weight": round(weight, 4),
                    "beta": round(beta, 2),
                    "estimated_shock": round(stock_shock, 4),
                    "contribution": round(contribution, 4),
                })

            results[scenario_name] = {
                "portfolio_loss": round(total_loss, 4),
                "value_after": round(self.portfolio_value * (1 + total_loss), 0),
                "params": params,
                "worst_hit": sorted(stock_details, key=lambda x: x["estimated_shock"])[:3],
            }

        return results

    def _compute_var_cvar(self, holdings: List[dict], target: pd.Timestamp) -> dict:
        """历史模拟法 VaR / CVaR"""
        if not holdings:
            return {}

        # 构建组合日收益序列
        lookback_start = target - pd.Timedelta(days=self.lookback_days)
        portfolio_returns = []

        for h in holdings:
            code = h["code"]
            weight = h.get("weight", 1.0 / len(holdings))
            returns = self._get_daily_returns(code, lookback_start, target)
            if len(returns) > 0:
                padded = np.zeros(self.lookback_days)
                padded[-len(returns):] = returns[:self.lookback_days]
                portfolio_returns.append(padded * weight)

        if not portfolio_returns:
            return {"error": "无法计算"}

        portfolio_returns = np.sum(portfolio_returns, axis=0)
        sorted_rets = np.sort(portfolio_returns)

        var_95 = np.percentile(sorted_rets, 5)
        var_99 = np.percentile(sorted_rets, 1)
        cvar_95 = np.mean(sorted_rets[:int(len(sorted_rets) * 0.05)])
        cvar_99 = np.mean(sorted_rets[:int(len(sorted_rets) * 0.01)])

        return {
            "method": "历史模拟法",
            "lookback_days": self.lookback_days,
            "var_95_pct": round(float(var_95), 4),
            "var_95_amount": round(float(var_95) * self.portfolio_value, 0),
            "var_99_pct": round(float(var_99), 4),
            "var_99_amount": round(float(var_99) * self.portfolio_value, 0),
            "cvar_95_pct": round(float(cvar_95), 4),
            "cvar_95_amount": round(float(cvar_95) * self.portfolio_value, 0),
            "cvar_99_pct": round(float(cvar_99), 4),
            "cvar_99_amount": round(float(cvar_99) * self.portfolio_value, 0),
            "volatility_annual": round(float(np.std(portfolio_returns) * np.sqrt(252)), 4),
        }

    def _analyze_concentration(self, holdings: List[dict]) -> dict:
        """集中度风险分析"""
        if not holdings:
            return {}

        weights = sorted([h.get("weight", 0) for h in holdings], reverse=True)
        top3 = sum(weights[:3]) if len(weights) >= 3 else sum(weights)
        top5 = sum(weights[:5]) if len(weights) >= 5 else sum(weights)
        herfindahl = sum(w ** 2 for w in weights)  # HHI指数

        sectors = {}
        for h in holdings:
            sec = h.get("sector", "未知")
            sectors[sec] = sectors.get(sec, 0) + h.get("weight", 0)
        max_sector = max(sectors.values()) if sectors else 0

        return {
            "top3_concentration": round(top3, 4),
            "top5_concentration": round(top5, 4),
            "herfindahl_index": round(herfindahl, 4),
            "effective_n": round(1 / herfindahl, 1) if herfindahl > 0 else 0,
            "max_sector_weight": round(max_sector, 4),
            "sector_count": len(sectors),
        }

    def _generate_summary(self, report: dict) -> dict:
        """生成风险摘要"""
        hist = report.get("historical_scenarios", {})
        hypo = report.get("hypothetical_scenarios", {})
        var_analysis = report.get("var_analysis", {})
        conc = report.get("concentration_risk", {})

        # 历史最大损失
        max_hist_loss = min(
            [(k, v["portfolio_loss"]) for k, v in hist.items()],
            key=lambda x: x[1],
            default=("N/A", 0)
        )

        # 假设最大损失
        max_hypo_loss = min(
            [(k, v["portfolio_loss"]) for k, v in hypo.items()],
            key=lambda x: x[1],
            default=("N/A", 0)
        )

        # 风险等级
        var_95 = var_analysis.get("var_95_pct", 0)
        if var_95 > -0.01:
            risk_level = "低"
        elif var_95 > -0.03:
            risk_level = "中"
        elif var_95 > -0.05:
            risk_level = "中高"
        else:
            risk_level = "高"

        return {
            "risk_level": risk_level,
            "daily_var_95": f"{var_95:.2%}",
            "worst_historical": f"{max_hist_loss[0]}: {max_hist_loss[1]:.1%}",
            "worst_hypothetical": f"{max_hypo_loss[0]}: {max_hypo_loss[1]:.1%}",
            "concentration": f"Top3={conc.get('top3_concentration', 0):.1%}, "
                           f"有效持有数={conc.get('effective_n', 0)}",
        }

    # === 数据获取辅助 (从本地K线) ===

    def _get_period_return(self, code: str, start: pd.Timestamp, end: pd.Timestamp) -> float:
        try:
            path = Path(KLINE_DIR) / f"{code}.parquet"
            if not path.exists():
                return self.HISTORICAL_SCENARIOS.get("2008金融危机", {}).get("index_drawdown", -0.15)

            df = pd.read_parquet(path)
            df["date"] = pd.to_datetime(df["date"])
            period = df[(df["date"] >= start) & (df["date"] <= end)]
            if len(period) < 2:
                # 股票可能在期间未上市，用指数跌幅代替
                for s in self.HISTORICAL_SCENARIOS.values():
                    if s["period"] == (str(start.date()), str(end.date())):
                        return s["index_drawdown"] * 0.8  # 个股通常比指数波动大
                return -0.10

            start_price = float(period["close"].iloc[0])
            end_price = float(period["close"].iloc[-1])
            return (end_price - start_price) / start_price
        except:
            return -0.10

    def _get_daily_returns(self, code: str, start: pd.Timestamp, end: pd.Timestamp) -> np.ndarray:
        try:
            path = Path(KLINE_DIR) / f"{code}.parquet"
            if not path.exists():
                return np.array([])
            df = pd.read_parquet(path)
            df["date"] = pd.to_datetime(df["date"])
            df = df[(df["date"] >= start) & (df["date"] <= end)]
            if len(df) < 5:
                return np.array([])
            close = df["close"].values.astype(float)
            return np.diff(close) / close[:-1]
        except:
            return np.array([])

    def _get_beta(self, code: str, target: pd.Timestamp, window: int = 60) -> float:
        try:
            returns = self._get_daily_returns(code, target - pd.Timedelta(days=window * 2), target)
            if len(returns) < 20:
                return 1.0
            return max(0.2, min(2.5, float(np.std(returns[-window:]) / 0.015)))  # 简化: 波动率/市场波动率
        except:
            return 1.0

    def _get_volatility(self, code: str, target: pd.Timestamp, window: int = 20) -> float:
        try:
            returns = self._get_daily_returns(code, target - pd.Timedelta(days=window * 2), target)
            if len(returns) < 10:
                return 0.03
            return float(np.std(returns[-window:]))
        except:
            return 0.03

    def _save_report(self, report: dict, date_str: str):
        try:
            Path(REPORT_DIR).mkdir(parents=True, exist_ok=True)
            path = Path(REPORT_DIR) / f"stress_test_{date_str}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"压力测试报告已保存: {path}")
        except Exception as e:
            logger.warning(f"保存压力测试报告失败: {e}")
