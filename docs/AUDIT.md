# DueSignal Prioritized Engineering Audit

**Audit Date:** October 23, 2026  
**Auditor:** Principal Software & Security Engineering Review  
**Repository:** DueSignal (Alexa+ MCP Deadline Triage)

---

## 1. Executive Summary & Baseline State

* **Git Status:** Branch `main`, clean working tree.
* **Test Suite:** 10/10 tests passing (`pytest -v`).
* **Protocol Target:** Streamable HTTP protocol `2025-11-25` over FastMCP / Starlette.
* **Core Status:** The 4 baseline MCP tools (`tool_list_deadlines`, `tool_add_deadline`, `tool_mark_complete`, `tool_get_priority_ranking`) are operational and discoverable. SQLite backend with indexed lookups is active.

---

## 2. Prioritized Findings

### P0 — Critical Correctness, Security & Data Integrity
1. **Bearer Token Verification Timing:** Standard string equality (`auth == f"Bearer {TOKEN}"`) in `BearerAuthMiddleware` is vulnerable to timing analysis. Must use `hmac.compare_digest`.
2. **Missing Reopen & Edit Operations in Storage:** Completed deadlines cannot currently be reopened without raw DB manipulation; deadlines cannot be edited after initial creation.
3. **Deterministic Tie-Breaking:** If two assignments share the same score, Python's TimSort preserves insertion order. Needs explicit secondary sort key: `(score DESC, due_at ASC, title ASC)`.
4. **CORS Configuration:** `allow_origins=["*"]` allows any web origin to hit local endpoints if token is known. Needs bounded local origin controls.

### P1 — Core Product Functionality & User Experience
1. **Interactive Deadline Lifecycle:** The product needs deadline editing, status reopening (`completed` -> `pending`), deletion with confirmation, and comprehensive detail inspection.
2. **Real Workload Metrics:** Main screen should communicate real workload: pending count, completed count, completion percentage, workload risk rating.
3. **Filtering & Sorting Matrix:** Multi-dimensional sorting (by Priority, Due Date, Grade Weight) and filtering (Status, Course, Window).
4. **Transparent AI Explanation Attribution:** Every explanation must clearly and honestly badge whether it was synthesized by Amazon Bedrock or computed via the deterministic fallback engine.

### P2 — Reliability, Observability & Resilience
1. **SQLite Concurrency & Timeout:** Add `timeout=15.0` to SQLite connection pools to prevent database locks under rapid requests.
2. **Strict ISO8601 Validation:** Parse and validate ISO datetime formats with descriptive client-facing error feedback rather than generic server 500s.
3. **Connection Health Indicator:** Real-time polling/SSE ping reflecting true MCP server availability.

### P3 — Developer Experience & Documentation
1. **Honest System Description:** Accurately describe client as "Alexa+-inspired MCP Demonstration" rather than claiming native proprietary Amazon hardware integration.
2. **API Documentation:** Complete contract specification for all endpoints and tool signatures.
