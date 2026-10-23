from datetime import datetime, timezone, timedelta
from mcp_server.priority import deterministic_rank

def test_deterministic_tie_breaking():
    now = datetime.now(timezone.utc)
    # Same hours and same weight -> exactly identical score
    due_same = (now + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M")

    deadlines = [
        {"id": 1, "title": "Zulu Assignment", "course": "CS1", "due_at": due_same, "weight_pct": 20},
        {"id": 2, "title": "Alpha Assignment", "course": "CS2", "due_at": due_same, "weight_pct": 20},
        {"id": 3, "title": "Beta Assignment", "course": "CS3", "due_at": due_same, "weight_pct": 20},
    ]

    ranked = deterministic_rank(deadlines)
    # Identical score should tie-break alphabetically by title: Alpha -> Beta -> Zulu
    assert [d["title"] for d in ranked] == [
        "Alpha Assignment",
        "Beta Assignment",
        "Zulu Assignment"
    ]

def test_explanation_source_attribution():
    now = datetime.now(timezone.utc)
    due = (now + timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M")
    deadlines = [{"id": 1, "title": "Project", "course": "CS101", "due_at": due, "weight_pct": 10}]
    
    ranked = deterministic_rank(deadlines)
    assert ranked[0]["explanation_source"] == "deterministic"
    assert "explanation" in ranked[0]
