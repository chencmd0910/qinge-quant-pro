import sys, os, time
sys.path.insert(0, "/app")

from app.paper_trading.live_runner import LivePaperRunner, FactorEngine, KLINE_DIR

# Test: just compute factors for one day, 300 stocks
import pandas as pd
codes = sorted([f.replace('.parquet', '') for f in os.listdir(KLINE_DIR) if f.endswith('.parquet')])

start = time.time()
picks = FactorEngine.rank_stocks_for_date(codes, "2026-06-09", KLINE_DIR, top_n=20, max_universe=300)
elapsed = time.time() - start
print(f"Factor ranking for 2026-06-09: {elapsed:.1f}s, found {len(picks)} stocks")
for i, (code, name, score) in enumerate(picks[:5]):
    print(f"  {i+1}. {code} {name}: score={score:.4f}")
    
# Test full runner on 1 day
print("\n--- Full runner test (1 day) ---")
runner = LivePaperRunner()
runner.load_state()
start = time.time()
summary = runner.run_daily("2026-06-01")
elapsed = time.time() - start
print(f"Daily run: {elapsed:.1f}s")
print(f"Return: {summary['cumulative_return']}%")
print(f"Trades: {summary['trade_count']}")
print(f"Positions: {summary['positions_count']}")
for t in summary.get('recent_trades', [])[:5]:
    print(f"  {t['date']} {t['action']} {t['code']} {t['shares']}sh @{t['price']}")
