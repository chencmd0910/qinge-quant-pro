import sys, os, time
sys.path.insert(0, "/app")

from app.paper_trading.live_runner import LivePaperRunner

print("=== Direct Live Runner: June 1-3 (3 days) ===")

runner = LivePaperRunner()
runner.load_state()
# Reset
runner.cash = runner.initial_cash
runner.positions = {}
runner.trades = []
runner.equity_curve = []
runner.current_date = ""
runner.start_date = ""

start = time.time()
summary = runner.run(start_date="2026-06-01", end_date="2026-06-03", resume=True)
elapsed = time.time() - start

print(f"\n{'='*50}")
print(f"Total time: {elapsed:.1f}s")
print(f"Return: {summary['cumulative_return']}%")
print(f"MaxDD: {summary['max_drawdown']}%")
print(f"Sharpe: {summary['sharpe']}")
print(f"Trades: {summary['trade_count']}")
print(f"Positions: {summary['positions_count']}")
print(f"Final value: {summary['total_value']:,.0f}")

print(f"\nPortfolio:")
for p in summary.get('positions', [])[:10]:
    print(f"  {p['code']} {p['name']}: {p['shares']}sh @{p['current_price']} PnL:{p['pnl_pct']}%")

print(f"\nRecent trades (last 10):")
for t in summary.get('recent_trades', [])[-10:]:
    print(f"  {t['date']} {t['action']} {t['code']} {t['shares']}sh @{t['price']} {t['reason']}")

eq = summary.get('equity_curve', [])
if eq:
    print(f"\nEquity: {len(eq)} days, {eq[0]['date']} {eq[0]['value']} -> {eq[-1]['date']} {eq[-1]['value']}")
