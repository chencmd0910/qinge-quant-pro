import urllib.request, json

# Check active strategies
resp = urllib.request.urlopen("http://localhost:8000/api/ai/strategies")
d = json.loads(resp.read())
for s in d:
    if s['status'] == 'ACTIVE':
        print(f"ID: {s['strategy_id']}")
        print(f"Name: {s['strategy_name']}")
        print(f"Type: {s['strategy_type']}")
        print(f"Metric return: {s.get('total_return')}%")
        
# Also check raw registry
print("\n--- Raw registry ---")
resp2 = urllib.request.urlopen("http://localhost:8000/api/ai/genealogy/summary")
g = json.loads(resp2.read())
for gen in g.get('generations', []):
    for s in gen.get('top3', []):
        print(f"  {s['name']}: params={s.get('params', {})}")
