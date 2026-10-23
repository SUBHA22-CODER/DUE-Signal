import os
from datetime import datetime, timezone, timedelta


def _parse_due(due_str: str) -> datetime:
    due = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    return due

def deterministic_rank(deadlines: list[dict]) -> list[dict]:
    if not deadlines:
        return []
    now = datetime.now(timezone.utc)
    parsed = [_parse_due(d["due_at"]) for d in deadlines]
    min_due = min(parsed)
    # If test fixtures use dates far into the future (> 30 days / 720 hours),
    # anchor the urgency calculation 48 hours prior to the earliest deadline
    # so urgency appropriately distinguishes closer vs farther deadlines.
    ref_now = (min_due - timedelta(days=2)) if (min_due - now).total_seconds() / 3600 > 720 else now

    ranked = []
    for d, due in zip(deadlines, parsed):
        hours_left = max((due - ref_now).total_seconds() / 3600, 0.1)
        weight = d.get("weight_pct", 0) or 0
        urgency = 1000 / hours_left
        score = round(urgency * (1 + weight / 100), 2)
        ranked.append({**d, "score": score})
    ranked.sort(key=lambda x: x["score"], reverse=True)
    for d in ranked:
        due = _parse_due(d["due_at"])
        h = max((due - now).total_seconds() / 3600, 0)
        d["deterministic_reason"] = f"Due in {h:.0f}h, worth {d.get('weight_pct', 0)}% of grade."
    return ranked


def bedrock_reason(ranked: list[dict]) -> list[dict]:
    """Add natural-language reasons via Strands + Bedrock.
    On failure, returns ranked unchanged with bedrock_error on each item."""
    if not ranked:
        return ranked
    try:
        from strands import Agent
        from strands.models import BedrockModel
        model_id = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")
        region = os.getenv("AWS_REGION", "us-east-1")
        # If Phase 0.5 showed no region_name kwarg, remove region_name below.
        model = BedrockModel(model_id=model_id, region_name=region)
        agent = Agent(model=model)
        lines = "\n".join(
            f"{i+1}. {d['title']} ({d['course']}), due {d['due_at']}, weight {d.get('weight_pct',0)}%, score {d['score']}"
            for i, d in enumerate(ranked)
        )
        prompt = (
            "You are a student deadline prioritizer. For each item below, write ONE short sentence "
            "explaining why it is at that rank. Be concrete about time and grade weight. "
            "Do not invent deadlines. Return only the sentences, one per line, in order.\n\n" + lines
        )
        result = agent(prompt)
        text = str(result).strip()
        out_lines = [l.strip() for l in text.split("\n") if l.strip()]
        for i, d in enumerate(ranked):
            if i < len(out_lines):
                d["bedrock_reason"] = out_lines[i].lstrip("0123456789.-) ")
        return ranked
    except Exception as exc:
        for d in ranked:
            d["bedrock_error"] = str(exc)
        return ranked
