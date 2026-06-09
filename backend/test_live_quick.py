import urllib.request, json, time

# Quick test: run last 5 trading days
print("=== Quick Live Runner Test (last 5 days) ===")

# Reset
req = urllib.request.Request(
    "http://localhost:8000/api/paper-trading/live/reset",
    data=b'{"cash":1000000}',
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
print("Reset:", json.loads(resp.read())['message'])

# Run small range
start = time.time()
req = urllib.request.Request(
    "http://localhost:8000/api/paper-trading/live/run",
    data=b'{"start":"2026-06-01","end":"2026-06-09","resume":true}',
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req, timeout=600)
result = json.loads(resp.read())
elapsed = time.time() - start

print(f"\n=== {elapsed:.1f}s ===")
print(f"Return: {result['cumulative_return']}% | MaxDD: {result['max_drawdown']}% | Sharpe: {result['sharpe']}")
print(f"Trades: {result['trade_count']} | Positions: {result['positions_count']}")

for t in result.get('recent_trades', [])[-8:]:
    print(f"  {t['date']} {t['action']:4s} {t['code']:12s} {t['shares']}sh @{t['price']:8.2f} {t['reason']}")
