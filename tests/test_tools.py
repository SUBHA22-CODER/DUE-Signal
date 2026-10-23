from mcp_server.priority import deterministic_rank

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
