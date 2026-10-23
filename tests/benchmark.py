import time
import random
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timezone, timedelta
from mcp_server.priority import deterministic_rank

def generate_deadlines(n: int = 1000) -> list[dict]:
    now = datetime.now(timezone.utc)
    courses = ["CS101", "CS229", "MATH201", "PHYS150", "BIO102", "CHEM204", "ENG105"]
    deadlines = []
    for i in range(1, n + 1):
        hours_offset = random.uniform(-12, 500)
        due = now + timedelta(hours=hours_offset)
        deadlines.append({
            "id": i,
            "title": f"Assignment {i}",
            "course": random.choice(courses),
            "due_at": due.strftime("%Y-%m-%dT%H:%M"),
            "weight_pct": round(random.uniform(5, 40), 1),
            "status": "pending"
        })
    return deadlines

def run_benchmark():
    n = 1000
    deadlines = generate_deadlines(n)
    
    # Warmup
    deterministic_rank(deadlines[:50])
    
    # Timed run
    start = time.perf_counter()
    ranked = deterministic_rank(deadlines)
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    print("=" * 60)
    print(f"DueSignal Deterministic Ranking Benchmark: {n} Deadlines")
    print("=" * 60)
    print(f"Total Items:     {len(ranked)}")
    print(f"Elapsed Time:    {elapsed_ms:.2f} ms")
    print(f"Per-Item Time:   {(elapsed_ms / n) * 1000:.2f} µs")
    print(f"Top 1 Priority:  {ranked[0]['title']} ({ranked[0]['course']}) - Score: {ranked[0]['score']}")
    print(f"Status Bands:    OVERDUE={sum(1 for d in ranked if d['is_overdue'])}, UPCOMING={sum(1 for d in ranked if not d['is_overdue'])}")
    print("=" * 60)
    
    assert elapsed_ms < 50.0, f"Benchmark failed: {elapsed_ms:.2f}ms exceeds 50ms threshold"
    return elapsed_ms

if __name__ == "__main__":
    run_benchmark()
