import urllib.request, json, time

# Test: just 2 days with optimized engine
print("=== Live Runner Test (2 days) ===")

# Reset
req = urllib.request.Request(
    "http://localhost:8000/api/paper-trading/live/reset",
    data=b'{"cash":1000000}',
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
print("Reset OK")

# Run 2 days
start = time.time()
req = urllib.request.Request(
    "http://localhost:8000/api/paper-trading/live/run",
    data=b'{"start":"2026-06-05","end":"2026-06-09","resume":true}',
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req, timeout=600)
result = json.loads(resp.read())
elapsed = time.time() - start

print(f"\nDone in {elapsed:.1f}s")
print(f"Return: {result['cumulative_return']}% | MaxDD: {result['max_drawdown']}%")
print(f"Trades: {result['trade_count']} | Positions: {result['positions_count']}")

for t in result.get('recent_trades', [])[-5:]:
    print(f"  {t['date']} {t['action']:4s} {t['code']:12s} {t['shares']}sh @{t['price']:8.2f} {t['reason']}")
