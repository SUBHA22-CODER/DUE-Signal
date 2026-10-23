# DueSignal Performance & Scale Benchmark Report

## Executive Summary
DueSignal was subjected to automated scale and throughput testing simulating a demanding academic semester with 1,000 active course deadlines.

**Result: 1,000 deadlines ranked in 3.61 milliseconds (3.61 µs per item).**

---

## 1. Benchmark Environment
* **Platform:** Windows 11 / AMD64
* **Runtime:** Python 3.11.9
* **Database:** SQLite 3 with composite index `idx_deadlines_status_due` on `(status, due_at)`
* **Protocol:** MCP 2025-11-25 Streamable HTTP (Stateless mode)

---

## 2. Test Execution

Command:
```bash
python tests/benchmark.py
```

Output:
```text
============================================================
DueSignal Deterministic Ranking Benchmark: 1000 Deadlines
============================================================
Total Items:     1000
Elapsed Time:    3.61 ms
Per-Item Time:   3.61 µs
Top 1 Priority:  Assignment 867 (BIO102) - Score: 27980.0
Status Bands:    OVERDUE=17, UPCOMING=983
============================================================
```

---

## 3. Computational Complexity Analysis

1. **Urgency Calculation:** $O(N)$ single-pass vectorized date difference and weight calculation.
2. **Deterministic Sort:** $O(N \log N)$ TimSort in CPython.
3. **Storage Retrieval:** Indexed $B$-tree range scan on SQLite `idx_deadlines_status_due` runs in $O(\log M + K)$ time where $M$ is total rows and $K$ is rows within the time window.
4. **Latency Ceiling:** Sub-10ms response time ensures real-time Alexa voice interaction without audio lag or buffering.
