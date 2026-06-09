import httpx, asyncio, json, sys
sys.stdout.reconfigure(encoding='utf-8')

async def test(msg):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post("http://localhost:8000/api/ai/chat", json={"message": msg, "history": []})
        d = json.loads(r.text)
        tool = d.get("tool", "?")
        print(f"[{tool}] {msg[:40]}")

async def main():
    for msg in ["看看持仓", "茅台最近行情", "风险警报", "帮我看看有什么策略", "今天天气"]:
        await test(msg)

asyncio.run(main())
