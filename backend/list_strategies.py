import urllib.request, json

d = json.loads(urllib.request.urlopen("http://localhost:8000/api/ai/strategies").read())
for s in d:
    print(f"{s['strategy_name']:20s} | {s['total_return']}% | Sharpe:{s['sharpe_ratio']} | {s['status']}")
