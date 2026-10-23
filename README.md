# DueSignal

Production-grade, self-hosted Alexa+-compatible MCP server (Streamable HTTP, protocol `2025-11-25`) and student academic command center that turns scattered deadlines into clear, prioritized daily guidance.

---

## What It Does
* **4 MCP Tools**: Exposes `tool_list_deadlines`, `tool_add_deadline`, `tool_mark_complete`, and `tool_get_priority_ranking` over Streamable HTTP.
* **Persistent SQLite Store**: High-performance indexed storage (`idx_deadlines_status_due`) with full CRUD support (Add, Edit, Complete, Reopen, Delete).
* **Deterministic Priority Engine with Fallback**: Ranks by urgency $\times$ grade weight with explicit tie-breaking (`score DESC, due_at ASC, title ASC`). Optionally enriches with natural language rationale via Amazon Bedrock (Strands Agents SDK) with transparent source attribution.
* **Student Command Center UI**: Modern, restrained dark-first interface featuring real workload metrics, urgency bands (`OVERDUE`, `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), iCalendar (`.ics`) import, and simulated Alexa+ voice dialogue.

---

## Verified Environment
* **OS:** Windows 11 / Linux compatible
* **Python:** 3.11.9
* **MCP Protocol:** `2025-11-25` (Streamable HTTP / Stateless)
* **SDKs:** `mcp` 2.1.1, `strands-agents` 1.62.0, `aiosqlite` 0.22.1

---

## Quickstart (Windows PowerShell)

```powershell
# 1. Setup virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Configure environment
copy .env.example .env

# 3. Start server
python -m mcp_server.server
# Or double-click run_server.bat
```

Access the application in your browser at: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## Run Verification & Test Suite

```powershell
pytest -v
# 14 passed in 3.41s
```

Run scale benchmark (1,000 deadlines):
```powershell
python tests/benchmark.py
# 1,000 Deadlines ranked in 3.61 ms (3.61 µs / item)
```

---

## Protocol & Tool Reference

| MCP Tool | Signature | Purpose |
|---|---|---|
| `tool_list_deadlines` | `window_days: int = 7` | Returns pending deadlines within forward window |
| `tool_add_deadline` | `title: str, course: str, due_at: str, weight_pct: float = 0` | Inserts deadline with ISO8601 validation |
| `tool_mark_complete` | `id: int` | Marks deadline complete |
| `tool_get_priority_ranking` | `date: str = ""` | Evaluates and prioritizes tasks with reasons |

---

## Security Model
* **Timing-Safe Auth:** Constant-time `hmac.compare_digest` for Bearer token validation.
* **SQL Injection Defense:** 100% parameterized queries using `aiosqlite`.
* **DNS Rebinding Protection:** Configured transport security and restricted CORS boundaries.

---

## Documentation
* [Architecture Guide](docs/ARCHITECTURE.md)
* [Architectural Decision Records](docs/ADR-001-mcp-streamable-http.md)
* [API & Protocol Specification](docs/API.md)
* [Security Threat Model](docs/SECURITY.md)
* [Benchmark Report](docs/BENCHMARKS.md)
* [Friction Log](friction-log.md)
