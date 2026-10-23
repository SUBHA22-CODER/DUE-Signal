import json
from datetime import datetime, timezone, timedelta
import pytest
from pydantic import ValidationError
from mcp_server.priority import deterministic_rank
from mcp_server.server import (
    tool_list_deadlines,
    tool_add_deadline,
    tool_mark_complete,
    tool_get_priority_ranking,
)
import mcp_server.db as dbmod

def test_ranking_orders_near_before_far():
    rows = [
        {"id": 1, "title": "Far", "course": "A", "due_at": "2099-01-10T00:00", "weight_pct": 50, "status": "pending"},
        {"id": 2, "title": "Near", "course": "B", "due_at": "2099-01-01T00:00", "weight_pct": 5, "status": "pending"},
    ]
    ranked = deterministic_rank(rows)
    assert ranked[0]["title"] == "Near"
    assert "deterministic_reason" in ranked[0]

def test_empty_ranking_returns_empty():
    assert deterministic_rank([]) == []

@pytest.mark.asyncio
async def test_tool_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setenv("DUE_SIGNAL_DB", str(tmp_path / "lifecycle.db"))
    await dbmod.init_db()

    # Target date within 30 days
    near_due = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M")

    # 1. Add deadline via tool
    res_add = json.loads(await tool_add_deadline(
        title="Final Exam",
        course="MATH201",
        due_at=near_due,
        weight_pct=40.0
    ))
    assert res_add["created"] is True
    item_id = res_add["id"]

    # 2. List deadlines via tool
    res_list = json.loads(await tool_list_deadlines(window_days=14))
    assert any(d["id"] == item_id and d["title"] == "Final Exam" for d in res_list["deadlines"])

    # 3. Get priority ranking via tool
    res_rank = json.loads(await tool_get_priority_ranking())
    assert "ranked" in res_rank
    assert any(d["id"] == item_id for d in res_rank["ranked"])

    # 4. Mark complete via tool
    res_comp = json.loads(await tool_mark_complete(id=item_id))
    assert res_comp["status"] == "completed"

    # 5. Verify no longer pending in active list
    res_list2 = json.loads(await tool_list_deadlines(window_days=14))
    assert not any(d["id"] == item_id for d in res_list2["deadlines"])

def test_validation_constraints():
    from mcp_server.models import ListDeadlinesInput
    with pytest.raises(ValidationError):
        ListDeadlinesInput(window_days=100)  # max is 90
