import pytest
import aiosqlite
import mcp_server.db as dbmod
from datetime import datetime, timezone, timedelta

@pytest.mark.asyncio
async def test_sql_injection_defense(tmp_path, monkeypatch):
    monkeypatch.setenv("DUE_SIGNAL_DB", str(tmp_path / "sec.db"))
    await dbmod.init_db()

    now = datetime.now(timezone.utc)
    due = (now + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M")

    # Attempt classic SQL injection payload in title and course
    malicious_title = "Final Project'); DROP TABLE deadlines;--"
    malicious_course = "CS301' OR '1'='1"

    res = await dbmod.add_deadline(malicious_title, malicious_course, due, 25.0)
    assert res["created"] is True

    # Verify table was NOT dropped and query executed cleanly as literal text
    item = await dbmod.get_deadline(res["id"])
    assert item is not None
    assert item["title"] == malicious_title
    assert item["course"] == malicious_course

    # Test filtering with SQL injection in search term
    injected_results = await dbmod.list_deadlines_filtered(search="' OR '1'='1")
    # Should not return all rows unconditionally; searches literal string
    assert all("' OR '1'='1" in (d["title"] + d["course"]) for d in injected_results)
