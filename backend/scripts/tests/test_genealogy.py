import urllib.request, json

# Test genealogy endpoint
resp = urllib.request.urlopen("http://localhost:8000/api/ai/genealogy/summary")
summary = json.loads(resp.read())
print("=== GENEALOGY SUMMARY ===")
print(f"Total strategies: {summary['total']}")
print(f"Active: {summary['active_count']}")
if summary['all_time_best']:
    best = summary['all_time_best']
    print(f"All-time best: {best['name']} | Sharpe:{best['sharpe']} | Return:{best['total_return']}%")

# Test evolve endpoint (small scale)
print("\n=== EVOLUTION TEST ===")
data = json.dumps({
    "count": 5,
    "promote_top": 2,
    "base": {"start": "2025-03-01", "end": "2026-06-09", "rebalance": "monthly"},
    "explore_params": {
        "top_n": [10, 20, 30],
        "stop_loss": [-5, -8, -12],
    },
    "inherit_from_best": True
}).encode()

req = urllib.request.Request(
    "http://localhost:8000/api/ai/evolve",
    data=data,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req, timeout=300)
result = json.loads(resp.read())
print(f"Generation: {result.get('generation_id')}")
print(f"Evolved from: {result.get('evolved_from_generations')} generations")
print(f"Best inherited: {result.get('best_ever_inherited')}")
print(f"Succeeded: {result['succeeded']}/{result['total']}")
print(f"Gene pool size: {result.get('gene_pool_size')}")
if result.get('ranked'):
    for r in result['ranked'][:3]:
        print(f"  TOP: {r['name']:25s} Sharpe:{r['sharpe_ratio']:.2f} Return:{r['total_return']}% DD:{r['max_drawdown']}%")

# Final genealogy
resp2 = urllib.request.urlopen("http://localhost:8000/api/ai/genealogy/summary")
summary2 = json.loads(resp2.read())
print(f"\nFinal gene pool: {summary2['total']} strategies, {len(summary2['generations'])} generations")
print(f"Active: {summary2['active_count']}")
for gen in summary2['generations']:
    print(f"  {gen['generation_id']}: {gen['count']} strategies, avg_sharpe={gen['avg_sharpe']}")
