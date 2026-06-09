import urllib.request, json, time

print("=== Live Runner Test (2 trading days) ===")

req = urllib.request.Request(
    "http://localhost:8000/api/paper-trading/live/reset",
    data=b'{"cash":1000000}',
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
print("Reset OK")

start = time.time()
req = urllib.request.Request(
    "http://localhost:8000/api/paper-trading/live/run",
    data=b'{"start":"2026-06-01","end":"2026-06-03","resume":true}',
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req, timeout=600)
result = json.loads(resp.read())
elapsed = time.time() - start

print(f"\nDone in {elapsed:.1f}s")
print(f"Return: {result['cumulative_return']}% | MaxDD: {result['max_drawdown']}%")
print(f"Trades: {result['trade_count']} | Positions: {result['positions_count']}")

for p in result.get('positions', [])[:5]:
    print(f"  持仓: {p['code']} {p['name']} {p['shares']}sh @{p['current_price']} PnL:{p['pnl_pct']}%")
for t in result.get('recent_trades', [])[:5]:
    print(f"  {t['date']} {t['action']} {t['code']} {t['shares']}sh @{t['price']} {t['reason']}")
