"""
青鳄量化 - 真实K线回测引擎
基于本地Parquet数据，向量化计算，零模拟

核心设计：
- 直接使用 KlineDataEngine 加载数据（绕过Provider层，性能最优）
- 向量化计算（无事件驱动开销）
- 支持月度/双周/周度调仓
- 返回真实权益曲线（非GBM模拟）
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import sys, os

sys.path.insert(0, str(Path(__file__).parent.parent / "data_engine"))
from kline_parquet import get_kline_engine


class RealBacktest:
    """真实K线回测引擎

    使用本地Parquet数据的向量化回测。
    无随机数，无GBM——每笔交易都是真实价格。

    使用示例:
        bt = RealBacktest(
            codes=["000001", "600519", ...],  # 股票池
            start="2024-06-01",
            end="2026-06-01",
            cash=1_000_000,
            top_n=20,         # 持仓数量
            rebalance="monthly",  # 调仓频率
            commission=0.0003,    # 手续费
        )
        result = bt.run()
        print(result["metrics"])  # 年化收益、夏普、回撤...
    """

    def __init__(
        self,
        codes: List[str],
        start: str,
        end: str,
        cash: float = 1_000_000,
        top_n: int = 20,
        rebalance: str = "monthly",
        commission: float = 0.0003,
        slippage: float = 0.0002,
        stop_loss: float = -0.08,
        ranking_factor: str = "momentum_20d",
    ):
        self.codes = codes
        self.start = start
        self.end = end
        self.cash = cash
        self.top_n = top_n
        self.rebalance = rebalance
        self.commission = commission
        self.slippage = slippage
        self.stop_loss = stop_loss
        self.ranking_factor = ranking_factor

        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = get_kline_engine()
        return self._engine

    def run(self) -> dict:
        """执行回测

        Returns:
            {
                "metrics": {annual_return, sharpe_ratio, max_drawdown, ...},
                "equity_curve": [{date, value}, ...],
                "drawdown_curve": [{date, dd}, ...],
                "trades": [{date, side, symbol, price, quantity, reason}, ...],
                "positions": [{date, symbols, ...}, ...],
                "data_source": "parquet",
                "data_source_note": "真实K线回测，数据源：本地Parquet"
            }
        """
        t0 = datetime.now()

        # 1. 加载全池收盘价
        print(f"[RealBacktest] Loading {len(self.codes)} stocks from Parquet...")
        closes = self.engine.get_closes(self.codes, self.start, self.end)
        if closes.empty:
            return {"error": "No data loaded", "metrics": {}}

        dates = closes.index.tolist()
        print(f"[RealBacktest] {len(dates)} trading days, {len(closes.columns)} stocks")

        # 2. 生成调仓信号
        rebalance_dates = self._get_rebalance_dates(dates)
        print(f"[RealBacktest] {len(rebalance_dates)} rebalance dates")

        # 3. 逐日模拟——资金管理分离
        equity_curve = []
        drawdown_curve = []
        trades = []
        positions_log = []

        cash = self.cash  # 可用现金
        peak = cash
        holdings = {}  # {code: {shares, avg_cost}}
        current_positions = []

        for i, date in enumerate(dates):
            date_str = str(date)[:10]

            # 调仓日：先卖后买
            if date_str in rebalance_dates or i == 0:
                # ── 卖出不在新持仓中的股票 ──
                new_positions = self._select_top(date, dates, closes)

                for code in list(holdings.keys()):
                    if code not in new_positions:
                        price = self._get_price(closes, code, date)
                        if price and price > 0:
                            shares = holdings[code]["shares"]
                            sell_amount = shares * price * (1 - self.slippage - self.commission)
                            cash += sell_amount
                            trades.append({
                                "date": date_str, "side": "SELL",
                                "symbol": code, "price": round(price, 2),
                                "quantity": shares, "amount": round(sell_amount, 2),
                                "reason": "调仓卖出",
                            })
                        del holdings[code]

                # ── 等权买入新持仓 ──
                if new_positions:
                    # 总投资额 = 可用现金 × 95%（留5%现金缓冲）
                    total_invest = cash * 0.95
                    per_stock = total_invest / len(new_positions)

                    for code in new_positions:
                        price = self._get_price(closes, code, date)
                        if price and price > 0:
                            shares = int(per_stock / price / 100) * 100  # 整百股
                            if shares >= 100:
                                buy_amount = shares * price * (1 + self.slippage + self.commission)
                                if buy_amount <= cash:
                                    cash -= buy_amount
                                    holdings[code] = {
                                        "shares": shares,
                                        "avg_cost": price,  # 建仓成本价
                                    }
                                    trades.append({
                                        "date": date_str, "side": "BUY",
                                        "symbol": code, "price": round(price, 2),
                                        "quantity": shares, "amount": round(buy_amount, 2),
                                        "reason": "调仓买入",
                                    })

                current_positions = list(holdings.keys())

            # ── 计算当日总权益 = 现金 + 持仓市值 ──
            positions_value = 0
            for code, h in holdings.items():
                price = self._get_price(closes, code, date)
                if price and price > 0:
                    positions_value += h["shares"] * price
            nav = cash + positions_value

            # ── 止损检查（每日）──
            for code in list(holdings.keys()):
                price = self._get_price(closes, code, date)
                if price and price > 0 and holdings[code]["avg_cost"] > 0:
                    pnl_pct = (price - holdings[code]["avg_cost"]) / holdings[code]["avg_cost"]
                    if pnl_pct <= self.stop_loss:
                        shares = holdings[code]["shares"]
                        sell_amount = shares * price * (1 - self.slippage - self.commission)
                        cash += sell_amount
                        trades.append({
                            "date": date_str, "side": "SELL",
                            "symbol": code, "price": round(price, 2),
                            "quantity": shares, "amount": round(sell_amount, 2),
                            "reason": f"止损 ({pnl_pct*100:.1f}%)",
                        })
                        del holdings[code]

            # ── 记录 ──
            peak = max(peak, nav)
            dd = (nav - peak) / peak * 100 if peak > 0 else 0
            equity_curve.append({"date": date_str, "value": round(nav, 2)})
            drawdown_curve.append({"date": date_str, "dd": round(dd, 2)})
            positions_log.append({
                "date": date_str,
                "symbols": current_positions.copy(),
                "count": len(current_positions),
            })

        # 4. 计算指标
        metrics = self._compute_metrics(equity_curve, self.cash)
        elapsed = (datetime.now() - t0).total_seconds()

        return {
            "metrics": metrics,
            "equity_curve": equity_curve,
            "drawdown_curve": drawdown_curve,
            "trades": trades,
            "positions": positions_log,
            "data_source": "parquet",
            "data_source_note": f"真实K线回测 · {len(self.codes)}只股票池 · {len(dates)}个交易日 · 耗时{elapsed:.1f}秒",
            "config": {
                "codes": len(self.codes),
                "top_n": self.top_n,
                "rebalance": self.rebalance,
                "start": self.start,
                "end": self.end,
                "stop_loss": self.stop_loss,
                "ranking_factor": self.ranking_factor,
            },
        }

    def _get_rebalance_dates(self, dates: list) -> set:
        """确定调仓日期"""
        df = pd.DataFrame({"date": dates})
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month

        if self.rebalance == "monthly":
            # 每月第一个交易日
            df["g"] = df["date"].dt.strftime("%Y-%m")
            rebalance = df.groupby("g")["date"].first().tolist()
        elif self.rebalance == "biweekly":
            # 每两周
            rebalance = [dates[i] for i in range(0, len(dates), 10)]
        elif self.rebalance == "weekly":
            rebalance = [dates[i] for i in range(0, len(dates), 5)]
        else:
            rebalance = [dates[i] for i in range(0, len(dates), 20)]

        return set(str(d)[:10] for d in rebalance)

    def _select_top(self, date, dates, closes) -> List[str]:
        """按排名因子选 top_n 股票"""
        date_str = str(date)[:10]
        codes_available = closes.columns.tolist()

        # 计算动量排名因子（默认：20日动量）
        rankings = []
        for code in codes_available:
            series = closes[code].dropna()
            if len(series) < 25:
                continue

            idx = series.index.get_loc(date) if date in series.index else -1
            if idx < 25:
                continue

            # 计算20日动量
            mom_20d = series.iloc[idx] / series.iloc[idx - 20] - 1 if idx >= 20 else 0

            # 综合因子打分（可扩展）
            score = mom_20d
            rankings.append((code, score))

        rankings.sort(key=lambda x: x[1], reverse=True)
        selected = [code for code, _ in rankings[:self.top_n]]
        return selected

    def _get_price(self, closes, code, date):
        """安全获取某日收盘价"""
        if code not in closes.columns:
            return None
        series = closes[code]
        if date in series.index:
            v = series.loc[date]
            if pd.notna(v) and v > 0:
                return float(v)
        return None

    def _compute_metrics(self, equity: list, cash: float) -> dict:
        """从权益曲线计算指标"""
        if len(equity) < 2:
            return {}

        values = [e["value"] for e in equity]
        final = values[-1]

        total_return = round((final - cash) / cash * 100, 2)
        days = len(values)

        # 年化收益
        years = days / 252
        if years > 0 and cash > 0:
            annual_return = round(((final / cash) ** (1 / years) - 1) * 100, 2)
        else:
            annual_return = 0

        # 日内收益序列
        daily_rets = [(values[i] - values[i - 1]) / values[i - 1] for i in range(1, len(values))]

        # 夏普比率
        if daily_rets:
            mean_ret = sum(daily_rets) / len(daily_rets)
            variance = sum((r - mean_ret) ** 2 for r in daily_rets) / len(daily_rets)
            std_ret = variance ** 0.5
            sharpe = round(mean_ret / max(std_ret, 1e-10) * (252 ** 0.5), 2)
        else:
            sharpe = 0

        # 最大回撤
        peak = values[0]
        max_dd = 0
        for v in values:
            peak = max(peak, v)
            dd = (v - peak) / peak * 100
            max_dd = min(max_dd, dd)

        # 胜率
        wins = sum(1 for r in daily_rets if r > 0)
        win_rate = round(wins / len(daily_rets) * 100, 1) if daily_rets else 0

        # 盈亏比
        gains = [r for r in daily_rets if r > 0]
        losses = [abs(r) for r in daily_rets if r < 0]
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0.001
        profit_factor = round(avg_gain / avg_loss, 2)

        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": round(max_dd, 2),
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_days": days,
            "annual_years": round(years, 2),
        }


def run_backtest_default(codes: List[str] = None, **kwargs) -> dict:
    """快捷入口：用默认参数跑回测

    如果不传codes，自动取沪深300成分股。
    在前端"回测中心"点"运行回测"时调用此函数。
    """
    if codes is None:
        # 默认：取前300只（近似沪深300）
        engine = get_kline_engine()
        all_codes = engine.get_available_stocks()
        codes = all_codes[:300]

    bt = RealBacktest(
        codes=codes,
        start=kwargs.get("start", "2024-06-01"),
        end=kwargs.get("end", "2026-06-09"),
        cash=kwargs.get("cash", 1_000_000),
        top_n=kwargs.get("top_n", 20),
        rebalance=kwargs.get("rebalance", "monthly"),
        commission=kwargs.get("commission", 0.0003),
        stop_loss=kwargs.get("stop_loss", -0.08),
        slippage=kwargs.get("slippage", 0.0002),
    )
    return bt.run()
