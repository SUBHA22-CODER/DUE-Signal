import pytest, httpx

BASE = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/health")
        assert r.status_code == 200 and r.json() == {"ok": True}

@pytest.mark.asyncio
async def test_unauthorized_without_token():
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        assert r.status_code == 401
