import urllib.request, json, time

# 1. Reset and run live paper trading
print("=== 1. Reset ===")
req = urllib.request.Request(
    "http://localhost:8000/api/paper-trading/live/reset",
    data=b'{"cash":1000000}',
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
print(json.loads(resp.read()))

# 2. Run from June 2025 to today (about 1 year)
print("\n=== 2. Running live paper trading ===")
start = time.time()

req = urllib.request.Request(
    "http://localhost:8000/api/paper-trading/live/run",
    data=b'{"start":"2025-06-01","end":"2026-06-09","resume":true}',
    headers={"Content-Type": "application/json"}
)

# This might take a while, use longer timeout
resp = urllib.request.urlopen(req, timeout=600)
result = json.loads(resp.read())

elapsed = time.time() - start
print(f"\n=== Done in {elapsed:.1f}s ===")
print(f"Date: {result['current_date']}")
print(f"Initial: {result['initial_cash']}")
print(f"Final: {result['total_value']}")
print(f"Return: {result['cumulative_return']}%")
print(f"MaxDD: {result['max_drawdown']}%")
print(f"Sharpe: {result['sharpe']}")
print(f"Positions: {result['positions_count']}")
print(f"Trades: {result['trade_count']}")
print(f"Strategies: {[s['name'] for s in result['active_strategies']]}")

# Top 5 positions
print(f"\nTop positions:")
for p in result.get('positions', [])[:5]:
    print(f"  {p['code']} {p['name']}: {p['shares']}股 @{p['avg_cost']} PnL:{p['pnl']}")

# Recent trades
print(f"\nRecent trades:")
for t in result.get('recent_trades', [])[-5:]:
    print(f"  {t['date']} {t['action']} {t['code']} {t['shares']}股 @{t['price']} {t['reason']}")

# Equity curve stats
eq = result.get('equity_curve', [])
if eq:
    print(f"\nEquity curve: {len(eq)} points, {eq[0]['date']} -> {eq[-1]['date']}")
    print(f"  Start: {eq[0]['value']} -> End: {eq[-1]['value']}")
