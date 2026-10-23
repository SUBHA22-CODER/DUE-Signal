# DueSignal Production Elevation Plan

## 1. Executive Summary & Quality Bar
DueSignal is a functional, tested Alexa+ MCP server and client. To transition from a working MVP to an award-winning submission, this plan addresses 5 key axes identified via `doubt-driven-development`, `observability-and-instrumentation`, `frontend-ui-engineering`, and `performance-optimization`.

---

## 2. Identified Improvement Axes

```
                                DueSignal Ecosystem
                                        │
    ┌───────────────────┬───────────────┼───────────────┬──────────────────┐
    ▼                   ▼               ▼               ▼                  ▼
[Axis 1: Core]   [Axis 2: Obs]    [Axis 3: Data]   [Axis 4: Voice]   [Axis 5: Perf]
Overdue edge-    Structured JSON  One-click Demo   Alexa earcon      1,000-deadline
case handling &  logging, trace   Dataset Seeder   audio chimes &    benchmark &
grace periods    IDs & /metrics   & .ics support   intent matcher    load harness
```

---

## 3. High-Value Task Specifications

### Task 1: Overdue Edge-Case Handling & Grade Risk Categorization (`mcp_server/priority.py`)
- **Problem:** When an item is past its `due_at`, `hours_left` becomes negative or zero.
- **Solution:** Add explicit `is_overdue: bool` flag, graceful overdue penalty scoring, and distinct status tag (`"OVERDUE"`, `"CRITICAL"`, `"UPCOMING"`, `"FAR"`).
- **Verification:** Unit test with past, present, and future timestamps.

### Task 2: Observability & Tracing Middleware (`mcp_server/server.py`)
- **Problem:** No visibility into tool invocation latency, Bedrock vs. fallback execution time, or per-request trace IDs.
- **Solution:** Add a structured logger and middleware injecting `X-Request-ID`, recording elapsed milliseconds and tool execution metrics (`GET /metrics`).
- **Verification:** Test verifying `X-Request-ID` header and `/metrics` response.

### Task 3: Conversational Natural Language Intent Dispatcher (`web_client/index.html`)
- **Problem:** Alexa users speak conversational phrases ("What should I work on first?", "I finished CS301", "Add Biology lab due tomorrow").
- **Solution:** Implement a client-side conversational parser that translates raw voice input into the corresponding MCP tool call (`tool_get_priority_ranking`, `tool_mark_complete`, `tool_add_deadline`).
- **Verification:** Tested in browser client with voice and simulated text inputs.

### Task 4: Interactive Demo Seeder & Syllabus Quick-Import
- **Problem:** Evaluators starting a clean instance have an empty database and must type items manually.
- **Solution:** Add a "Load Stanford CS Demo Curriculum" button in the Web Client and a CLI seed command (`python -m mcp_server.seed`) populating 5 realistic deadlines across diverse urgencies and grade weights.
- **Verification:** One-click instant population on the UI and CLI seed verification.

### Task 5: Performance Benchmark Suite (`tests/benchmark.py`)
- **Problem:** No empirical proof of latency under heavy deadline volume.
- **Solution:** Create an automated benchmark script demonstrating that sorting and ranking 1,000 deadlines executes in under 15ms.
- **Verification:** `python tests/benchmark.py` asserts latency $< 20\text{ms}$.
