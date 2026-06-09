import sys, os, time
sys.path.insert(0, "/app")

from app.paper_trading.live_runner import LivePaperRunner, FactorEngine, KLINE_DIR
import numpy as np, pandas as pd

# Quick test: factor on 1 stock
print("=== Single stock factor test ===")
path = os.path.join(KLINE_DIR, "000001.parquet")
df = pd.read_parquet(path)
print(f"000001: {len(df)} rows, dates {df['date'].iloc[0]} -> {df['date'].iloc[-1]}")

# Time factor computation for 1 stock
start = time.time()
scores = FactorEngine.score_stocks(df)
elapsed = time.time() - start
print(f"Factor on 1 stock: {elapsed*1000:.0f}ms, last score={scores[-1]:.4f}")

# Time for 50 stocks
print("\n=== 50 stock ranking test ===")
all_codes = sorted([f.replace('.parquet', '') for f in os.listdir(KLINE_DIR) if f.endswith('.parquet')])[:50]
start = time.time()
picks = FactorEngine.rank_stocks_for_date(all_codes, "2026-06-09", KLINE_DIR, top_n=10, max_universe=50)
elapsed = time.time() - start
print(f"50 stocks: {elapsed:.1f}s, {len(picks)} picks")
for i, (code, name, score) in enumerate(picks[:5]):
    print(f"  {i+1}. {code} {name}: {score:.4f}")

# Time full runner with 50 stocks and 1 strategy, 1 day
print("\n=== Mini Runner test (50 stocks, 1 strategy, 1 day) ===")
from app.paper_trading.live_runner import LivePaperRunner as LPR

runner = LPR()
# Override to use only the default strategy
runner.active_strategies = [{
    "strategy_id": "test",
    "strategy_name": "Test",
    "weight": 1.0,
    "backtest_params": {"top_n": 10, "rebalance": "monthly", "stop_loss": -0.08},
}]
# Override market codes
original_get_codes = runner._get_market_codes
runner._get_market_codes = lambda: all_codes  # only 50 stocks

start = time.time()
summary = runner.run_daily("2026-06-01")
elapsed = time.time() - start
print(f"Mini runner: {elapsed:.1f}s")
print(f"Return: {summary['cumulative_return']}% | Trades: {summary['trade_count']} | Positions: {summary['positions_count']}")
for t in summary.get('recent_trades', [])[:5]:
    print(f"  {t['date']} {t['action']} {t['code']} {t['shares']}sh @{t['price']}")
