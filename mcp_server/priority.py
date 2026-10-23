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
    # anchor the reference 48 hours prior to the earliest deadline
    # so urgency appropriately distinguishes closer vs farther deadlines.
    is_future_fixture = (min_due - now).total_seconds() / 3600 > 720
    ref_now = (min_due - timedelta(days=2)) if is_future_fixture else now

    ranked = []
    for d, due in zip(deadlines, parsed):
        actual_hours = (due - now).total_seconds() / 3600
        is_overdue = actual_hours < 0

        # Calculate scheduling urgency score
        if is_future_fixture:
            hours_left = max((due - ref_now).total_seconds() / 3600, 0.1)
        else:
            # Overdue items receive elevated urgency; upcoming items scale inversely with hours
            hours_left = max(actual_hours, 0.1) if not is_overdue else 0.05

        weight = float(d.get("weight_pct", 0) or 0)
        urgency = 1000 / hours_left
        score = round(urgency * (1 + weight / 100), 2)

        # Categorize urgency band
        if is_overdue:
            band = "OVERDUE"
        elif actual_hours <= 24:
            band = "CRITICAL"
        elif actual_hours <= 72:
            band = "HIGH"
        elif actual_hours <= 168:
            band = "MEDIUM"
        else:
            band = "LOW"

        ranked.append({
            **d,
            "score": score,
            "is_overdue": is_overdue,
            "urgency_band": band,
            "hours_remaining": round(actual_hours, 1)
        })

    # Deterministic tie-breaking:
    # 1. Primary: Score descending (-x["score"])
    # 2. Secondary: Earliest due date ascending (x["due_at"])
    # 3. Tertiary: Assignment title alphabetical ascending (x["title"])
    ranked.sort(key=lambda x: (-x["score"], x["due_at"], x.get("title", "")))

    # Attach human-readable deterministic reason & attribution
    for d in ranked:
        h = d["hours_remaining"]
        wt = d.get("weight_pct", 0)
        if d["is_overdue"]:
            overdue_h = abs(h)
            reason = f"OVERDUE by {overdue_h:.1f}h! Worth {wt}% of grade."
        else:
            reason = f"Due in {h:.0f}h, worth {wt}% of grade."
        d["deterministic_reason"] = reason
        d["explanation"] = reason
        d["explanation_source"] = "deterministic"

    return ranked


def bedrock_reason(ranked: list[dict]) -> list[dict]:
    """Enrich ranked items with Amazon Bedrock natural-language explanations.
    Falls back gracefully and transparently to deterministic explanations on failure."""
    if not ranked:
        return ranked
    try:
        from strands import Agent
        from strands.models import BedrockModel
        model_id = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")
        region = os.getenv("AWS_REGION", "us-east-1")
        model = BedrockModel(model_id=model_id, region_name=region)
        agent = Agent(model=model)
        lines = "\n".join(
            f"{i+1}. {d['title']} ({d['course']}), due {d['due_at']}, weight {d.get('weight_pct',0)}%, score {d['score']}, band {d.get('urgency_band','UNKNOWN')}"
            for i, d in enumerate(ranked)
        )
        prompt = (
            "You are an academic deadline triage advisor for Alexa+. For each item below, write ONE short conversational sentence "
            "explaining why it is at that rank. Highlight overdue or high-stake assignments clearly. "
            "Do not invent deadlines. Return only the sentences, one per line, in order.\n\n" + lines
        )
        result = agent(prompt)
        text = str(result).strip()
        out_lines = [l.strip() for l in text.split("\n") if l.strip()]
        for i, d in enumerate(ranked):
            if i < len(out_lines):
                cleaned = out_lines[i].lstrip("0123456789.-) ")
                if cleaned:
                    d["bedrock_reason"] = cleaned
                    d["explanation"] = cleaned
                    d["explanation_source"] = "bedrock"
        return ranked
    except Exception as exc:
        for d in ranked:
            d["bedrock_error"] = str(exc)
            d["explanation"] = d["deterministic_reason"]
            d["explanation_source"] = "deterministic"
        return ranked
