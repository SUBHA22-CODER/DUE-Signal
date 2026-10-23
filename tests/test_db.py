import pytest, importlib

@pytest.mark.asyncio
async def test_add_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("DUE_SIGNAL_DB", str(tmp_path / "t.db"))
    import mcp_server.db as dbmod
    importlib.reload(dbmod)
    await dbmod.init_db()
    r = await dbmod.add_deadline("HW1", "CS101", "2099-01-01T23:59", 10)
    assert r["created"] is True
    rows = await dbmod.list_deadlines(36500)
    assert any(x["title"] == "HW1" for x in rows)

@pytest.mark.asyncio
async def test_duplicate_returns_existing(tmp_path, monkeypatch):
    monkeypatch.setenv("DUE_SIGNAL_DB", str(tmp_path / "t2.db"))
    import mcp_server.db as dbmod
    importlib.reload(dbmod)
    await dbmod.init_db()
    a = await dbmod.add_deadline("Dup", "CS", "2099-01-01T23:59", 5)
    b = await dbmod.add_deadline("Dup", "CS", "2099-01-01T23:59", 5)
    assert a["id"] == b["id"] and b["created"] is False
