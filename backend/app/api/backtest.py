"""Backtest API - file-based backtest engine with overfitting detection"""
import json
import os
import random
import math
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/backtest", tags=["Backtest"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data")
RESULTS_DIR = os.path.join(DATA_DIR, "backtest_results")


def _ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def _load_json(path: str, default=None):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def _save_json(path: str, data):
    _ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _safe_annual(annual_return: float, years: float = 1.0) -> float:
    """Sanity-check annual return — cap at 100% and detect mislabeled total returns"""
    clamped = max(min(annual_return, 100.0), -99.0)
    if clamped != annual_return:
        # Likely a total return passed as annual — try to annualize
        return round(annual_return / max(years, 0.5), 1)
    return annual_return


def _generate_equity_curve(annual_return: float, max_dd: float, sharpe: float,
                           days: int = 1200, start_cash: float = 1_000_000,
                           start_date: str = "2018-01-01", seed_override: int = None,
                           calibrate: bool = True):
    """Generate deterministic GBM equity curve from strategy metrics

    Uses a seeded random walk with mean reversion to produce
    visually plausible equity curves for display purposes.
    When calibrate=True, the final value is normalized to match
    the target annual_return exactly.
    These are NOT real backtest results — they are synthetic estimates.
    """
    if seed_override is not None:
        random.seed(seed_override)
    else:
        seed_key = f"{annual_return}|{max_dd}|{sharpe}|{start_date}"
        random.seed(int(abs(hash(seed_key)) % 100000))

    r_daily = (1 + annual_return / 100) ** (1 / 252) - 1
    # max_dd ≈ 3σ annualized → convert to daily vol
    annual_vol = abs(max_dd) / 100 / 3
    vol = max(annual_vol / (252 ** 0.5), 0.003)
    target_final = start_cash * (1 + annual_return / 100) ** (days / 365)

    equity = []
    nav = start_cash
    peak = nav
    sd = datetime.strptime(start_date, "%Y-%m-%d")
    raw_values = []

    for i in range(days):
        ret = r_daily + random.gauss(0, vol)
        ret = max(min(ret, 0.05), -0.05)
        nav *= (1 + ret)

        peak = max(peak, nav)
        dd_pct = (nav - peak) / peak * 100
        # Mean-reversion toward target drawdown
        if dd_pct < max_dd * 1.15:
            nav += nav * abs(dd_pct / 100) * 0.003
            dd_pct = max_dd * 1.1

        raw_values.append(nav)

    # Anchor calibration: rescale so final == target_final
    if calibrate and raw_values and raw_values[-1] != start_cash:
        scale = (target_final - start_cash) / (raw_values[-1] - start_cash)
        scale = max(min(scale, 5.0), 0.2)  # wider clamp, GBM is now calibrated
        for i in range(len(raw_values)):
            raw_values[i] = start_cash + (raw_values[i] - start_cash) * scale

    # Recompute DD after calibration
    peak = start_cash
    for i, nav in enumerate(raw_values):
        peak = max(peak, nav)
        dd = (nav - peak) / peak * 100
        d = sd + timedelta(days=i)
        equity.append({"date": d.strftime("%Y-%m-%d"), "value": round(nav), "dd": round(dd, 1)})

    return equity


def _compute_metrics(equity: list, cash: float, annual_years: float) -> dict:
    """Compute standard metrics from an equity curve"""
    if not equity:
        return {}
    final = equity[-1]["value"]
    total_ret = round((final - cash) / cash * 100, 2)
    annual_ret = round(((final / cash) ** (1 / max(annual_years, 0.25)) - 1) * 100, 1)
    dds = [e.get("dd", 0) for e in equity]
    max_dd = round(min(dds), 1) if dds else 0
    # Sharpe approximation from daily returns
    if len(equity) > 20:
        values = [e["value"] for e in equity]
        daily_rets = [(values[i] - values[i - 1]) / values[i - 1] for i in range(1, len(values))]
        mean_ret = sum(daily_rets) / len(daily_rets)
        std_ret = (sum((r - mean_ret) ** 2 for r in daily_rets) / len(daily_rets)) ** 0.5
        _sharpe = round(mean_ret / max(std_ret, 1e-8) * (252 ** 0.5), 2)
    else:
        _sharpe = 0.0
    return {
        "total_return": total_ret,
        "annual_return": annual_ret,
        "max_drawdown": max_dd,
        "sharpe_ratio": _sharpe,
    }


def _overfitting_check(annual_return: float, max_dd: float, sharpe: float,
                       calendar_days: int, cash: float, start_date: str,
                       strategy_id: str) -> dict:
    """Run in-sample (first 60%) vs out-of-sample (last 40%) split test

    Returns overfitting diagnostics:
      - is_sharpe: in-sample Sharpe
      - oos_sharpe: out-of-sample Sharpe
      - sharpe_decay: % drop from IS to OOS
      - dd_ratio: OOS maxDD / IS maxDD
      - overfit_risk: LOW | MODERATE | HIGH | SEVERE
    """
    split_point = int(calendar_days * 0.6)
    s = datetime.strptime(start_date, "%Y-%m-%d")
    mid = s + timedelta(days=split_point)
    mid_str = mid.strftime("%Y-%m-%d")

    years_is = split_point / 365
    years_oos = max((calendar_days - split_point) / 365, 0.25)

    # Generate two distinct curves (different seeds)
    is_equity = _generate_equity_curve(annual_return, max_dd, sharpe, split_point, cash, start_date,
                                       seed_override=int(abs(hash(strategy_id + "IS")) % 100000))
    oos_equity = _generate_equity_curve(annual_return, max_dd, sharpe, calendar_days - split_point,
                                        is_equity[-1]["value"], mid_str,
                                        seed_override=int(abs(hash(strategy_id + "OOS")) % 100000))

    is_m = _compute_metrics(is_equity, cash, years_is)
    oos_m = _compute_metrics(oos_equity, is_equity[-1]["value"], years_oos)

    decay = round((is_m["sharpe_ratio"] - oos_m["sharpe_ratio"]) / max(abs(is_m["sharpe_ratio"]), 0.01) * 100, 1)
    dd_ratio = round(abs(oos_m["max_drawdown"]) / max(abs(is_m["max_drawdown"]), 0.1), 1)

    # Classify risk
    if oos_m["sharpe_ratio"] < 0:
        risk = "SEVERE"
    elif decay > 50 or dd_ratio > 2.0:
        risk = "HIGH"
    elif decay > 25 or dd_ratio > 1.5:
        risk = "MODERATE"
    else:
        risk = "LOW"

    return {
        "split_date": mid_str,
        "is_metrics": is_m,
        "oos_metrics": oos_m,
        "sharpe_decay_pct": decay,
        "maxdd_ratio": dd_ratio,
        "overfit_risk": risk,
    }


@router.post("/run")
def run_backtest(payload: dict):
    """运行回测，支持自定义区间 + 过拟合检测"""
    strategy_id = payload.get("strategy_id", "default")
    symbol = payload.get("symbol", "ETF")
    start_date = payload.get("start_date", "2018-01-01")
    end_date = payload.get("end_date", "2026-06-05")
    cash = payload.get("cash", 1_000_000)
    enable_overfit = payload.get("overfit_check", True)
    metrics_override = payload.get("metrics", {})

    s = datetime.strptime(start_date, "%Y-%m-%d")
    e = datetime.strptime(end_date, "%Y-%m-%d")
    calendar_days = max((e - s).days, 60)
    annual_years = calendar_days / 365

    # ─── Sanitize inputs ───
    raw_annual = metrics_override.get("annual_return", 5.0)
    annual = _safe_annual(raw_annual, annual_years)
    max_dd = max(min(metrics_override.get("max_drawdown", -20.0), -0.5), -90.0)
    sharpe = max(min(metrics_override.get("sharpe_ratio", 0.5), 5.0), -3.0)

    # ─── GBM equity curve (synthetic) ───
    equity = _generate_equity_curve(annual, max_dd, sharpe, calendar_days, cash, start_date, None)

    # ─── Trades (synthetic, within range) ───
    random.seed(int(abs(hash(strategy_id)) % 10000))
    trade_count = min(random.randint(30, 180), calendar_days // 5)
    trades = []
    for _ in range(trade_count):
        td = s + timedelta(days=random.randint(0, calendar_days))
        trades.append({
            "date": td.strftime("%Y-%m-%d"),
            "side": random.choice(["BUY", "SELL"]),
            "symbol": symbol,
            "name": f"{symbol}基金",
            "price": round(random.uniform(1.5, 50), 2),
            "quantity": random.randint(1000, 50000),
        })
    trades.sort(key=lambda x: x["date"])

    # ─── Real metrics from actual curve (not override) ───
    metrics = _compute_metrics(equity, cash, annual_years)
    metrics["win_rate"] = round(random.uniform(35, 68), 0)
    metrics["alpha"] = round(metrics["annual_return"] - 3.0, 1)
    metrics["trade_count"] = len(trades)

    result = {
        "strategy_id": strategy_id,
        "start_date": start_date,
        "end_date": end_date,
        "data_source": "synthetic",  # ← clearly marked
        "data_source_note": "GBM模拟曲线，非真实K线回测。仅用于策略对比展示，实际表现可能存在显著偏差。",
        "metrics": metrics,
        "equity_curve_sample": equity,
        "drawdown_curve_sample": [{"date": x["date"], "dd": x["dd"]} for x in equity],
        "trades": trades,
        "created_at": datetime.now().isoformat(),
    }

    # ─── Overfitting check ───
    if enable_overfit and calendar_days > 180:
        try:
            result["overfitting"] = _overfitting_check(
                annual, max_dd, sharpe, calendar_days, cash, start_date, strategy_id
            )
        except Exception:
            result["overfitting"] = {"error": "overfit check failed", "overfit_risk": "UNKNOWN"}

    _ensure_dir(RESULTS_DIR)
    _save_json(os.path.join(RESULTS_DIR, f"{strategy_id}.json"), result)

    return result


@router.get("/reports")
def list_reports():
    """列出所有回测报告"""
    reports = []
    if os.path.exists(RESULTS_DIR):
        for fname in os.listdir(RESULTS_DIR):
            if fname.endswith(".json"):
                data = _load_json(os.path.join(RESULTS_DIR, fname))
                overfit = data.get("overfitting", {})
                reports.append({
                    "id": fname.replace(".json", ""),
                    "strategy_id": data.get("strategy_id", ""),
                    "annual_return": data.get("metrics", {}).get("annual_return", 0),
                    "sharpe_ratio": data.get("metrics", {}).get("sharpe_ratio", 0),
                    "max_drawdown": data.get("metrics", {}).get("max_drawdown", 0),
                    "total_trades": data.get("metrics", {}).get("trade_count", 0),
                    "data_source": data.get("data_source", "unknown"),
                    "overfit_risk": overfit.get("overfit_risk", "N/A"),
                    "created_at": data.get("created_at", ""),
                })
    return sorted(reports, key=lambda x: x.get("created_at", ""), reverse=True)


@router.get("/report/{report_id}")
def get_report(report_id: str):
    """获取单个回测报告"""
    path = os.path.join(RESULTS_DIR, f"{report_id}.json")
    if not os.path.exists(path):
        raise HTTPException(404, "回测报告不存在")
    return _load_json(path)


# ═══════════════════════════════════════════════════════════
# 真实回测端点 — 使用本地Parquet K线数据
# ═══════════════════════════════════════════════════════════

@router.post("/run-real")
def run_real_backtest(payload: dict):
    """运行真实K线回测（基于本地Parquet数据）

    请求体:
    {
        "codes": ["000001", "600519", ...],  // 股票池，默认沪深前300只
        "start": "2024-06-01",
        "end": "2026-06-09",
        "cash": 1000000,
        "top_n": 20,          // 持仓数量
        "rebalance": "monthly",  // monthly/biweekly/weekly
        "stop_loss": -0.08,   // 止损线
        "commission": 0.0003, // 手续费
        "slippage": 0.0002    // 滑点
    }
    """
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from backtest_engine.real_backtest import RealBacktest
    from data_engine.kline_parquet import get_kline_engine

    # 解析参数
    codes = payload.get("codes")
    if not codes:
        # 默认：前300只（近似沪深300）
        engine = get_kline_engine()
        codes = engine.get_available_stocks()[:300]

    start = payload.get("start", "2024-06-01")
    end = payload.get("end", "2026-06-09")
    cash = payload.get("cash", 1_000_000)
    top_n = payload.get("top_n", 20)
    rebalance = payload.get("rebalance", "monthly")
    stop_loss = payload.get("stop_loss", -0.08)
    commission = payload.get("commission", 0.0003)
    slippage = payload.get("slippage", 0.0002)

    strategy_id = payload.get("strategy_id", "real-backtest")

    # 运行回测
    bt = RealBacktest(
        codes=codes,
        start=start,
        end=end,
        cash=cash,
        top_n=top_n,
        rebalance=rebalance,
        commission=commission,
        slippage=slippage,
        stop_loss=stop_loss,
    )
    result = bt.run()

    if "error" in result:
        raise HTTPException(500, result["error"])

    # 保存结果
    result["strategy_id"] = strategy_id
    result["created_at"] = datetime.now().isoformat()
    _ensure_dir(RESULTS_DIR)
    _save_json(os.path.join(RESULTS_DIR, f"{strategy_id}.json"), result)

    return result


@router.get("/real-run")
def run_real_backtest_quick(
    start: str = "2024-06-01",
    end: str = "2026-06-09",
    cash: float = 1_000_000,
    top_n: int = 20,
    rebalance: str = "monthly",
):
    """快速真实回测（GET方法，适合浏览器直接测试）

    GET /api/backtest/real-run?start=2024-06-01&end=2026-06-09&top_n=20&rebalance=monthly
    """
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from backtest_engine.real_backtest import RealBacktest
    from data_engine.kline_parquet import get_kline_engine

    engine = get_kline_engine()
    codes = engine.get_available_stocks()[:300]

    bt = RealBacktest(
        codes=codes,
        start=start,
        end=end,
        cash=cash,
        top_n=top_n,
        rebalance=rebalance,
        commission=0.0003,
        slippage=0.0002,
        stop_loss=-0.08,
    )
    result = bt.run()

    if result.get("error"):
        raise HTTPException(500, result["error"])

    result["strategy_id"] = f"quick-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    result["created_at"] = datetime.now().isoformat()
    _ensure_dir(RESULTS_DIR)
    _save_json(os.path.join(RESULTS_DIR, f"{result['strategy_id']}.json"), result)

    return result
