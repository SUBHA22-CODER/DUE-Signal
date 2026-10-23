from datetime import datetime, timezone, timedelta
from mcp_server.priority import deterministic_rank

def test_priority_overdue_handling():
    now = datetime.now(timezone.utc)
    overdue_due = (now - timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M")
    future_due = (now + timedelta(hours=20)).strftime("%Y-%m-%dT%H:%M")
    
    deadlines = [
        {"id": 1, "title": "Overdue Lab", "course": "CS101", "due_at": overdue_due, "weight_pct": 15, "status": "pending"},
        {"id": 2, "title": "Future Exam", "course": "MATH201", "due_at": future_due, "weight_pct": 20, "status": "pending"},
    ]
    
    ranked = deterministic_rank(deadlines)
    assert len(ranked) == 2
    
    overdue_item = next(d for d in ranked if d["id"] == 1)
    assert overdue_item["is_overdue"] is True
    assert overdue_item["urgency_band"] == "OVERDUE"
    assert "OVERDUE" in overdue_item["deterministic_reason"]
    
    future_item = next(d for d in ranked if d["id"] == 2)
    assert future_item["is_overdue"] is False
    assert future_item["urgency_band"] == "CRITICAL"

def test_priority_urgency_bands():
    now = datetime.now(timezone.utc)
    deadlines = [
        {"id": 1, "title": "In 10h", "course": "A", "due_at": (now + timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M"), "weight_pct": 10},
        {"id": 2, "title": "In 48h", "course": "B", "due_at": (now + timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M"), "weight_pct": 10},
        {"id": 3, "title": "In 120h", "course": "C", "due_at": (now + timedelta(hours=120)).strftime("%Y-%m-%dT%H:%M"), "weight_pct": 10},
        {"id": 4, "title": "In 300h", "course": "D", "due_at": (now + timedelta(hours=300)).strftime("%Y-%m-%dT%H:%M"), "weight_pct": 10},
    ]
    ranked = deterministic_rank(deadlines)
    band_map = {d["id"]: d["urgency_band"] for d in ranked}
    assert band_map[1] == "CRITICAL"
    assert band_map[2] == "HIGH"
    assert band_map[3] == "MEDIUM"
    assert band_map[4] == "LOW"
