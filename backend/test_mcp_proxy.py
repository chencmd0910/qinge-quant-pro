import httpx
import json
import asyncio

async def test():
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post("http://localhost:8000/api/mcp/call", json={
            "jsonrpc": "2.0", "method": "tools/call",
            "params": {"name": "get_positions", "arguments": {"market": "SH"}},
            "id": 2
        })
        print("Status:", r.status_code)
        data = json.loads(r.text)
        result = json.loads(data["result"]["content"][0]["text"])
        print("Positions:", result["count"], "Total:", result["total_value"])

asyncio.run(test())
