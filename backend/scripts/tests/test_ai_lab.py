import json
import urllib.request

data = {
    "strategy_name": "AI多因子V1",
    "strategy_type": "multi_factor",
    "description": "v25多因子+月度调仓",
    "start": "2025-06-01",
    "end": "2026-06-09",
    "top_n": 20,
    "rebalance": "monthly"
}

req = urllib.request.Request(
    "http://localhost:8000/api/ai/create-and-backtest",
    data=json.dumps(data).encode(),
    headers={"Content-Type": "application/json"}
)

resp = urllib.request.urlopen(req, timeout=120)
result = json.loads(resp.read())
print(json.dumps(result, indent=2, ensure_ascii=False)[:3000])
