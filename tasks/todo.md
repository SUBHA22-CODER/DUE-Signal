# DueSignal Implementation Roadmap & Verification Checklist

## Phase 1: Robust Priority Ranking & Overdue Categorization
- [ ] Refactor `mcp_server/priority.py` to add `is_overdue`, status bands (`OVERDUE`, `CRITICAL`, `UPCOMING`), and normalized urgency curve.
- [ ] Add unit tests in `tests/test_priority_edge_cases.py` for negative hours, zero hours, and leap years.

## Phase 2: Observability & Metrics
- [ ] Add `RequestTracingMiddleware` with UUID4 `X-Request-ID` and latency calculation.
- [ ] Add `GET /metrics` returning JSON metrics (total requests, tool call count, average latency, DB operations).
- [ ] Add automated contract test for `/metrics` and `X-Request-ID`.

## Phase 3: Instant Demo Seeder & Quick Curriculum Load
- [ ] Implement `mcp_server/seed.py` with realistic CS & STEM assignments.
- [ ] Add "⚡ Load Sample Deadlines" button in `web_client/index.html`.

## Phase 4: Conversational Intent Dispatcher & Audio Earcons
- [ ] Add Web Audio API synthesizer for Alexa chime sound effects on start/end listening.
- [ ] Add conversational query router: "What should I do?", "What's due tomorrow?", "I finished <x>".

## Phase 5: Production Performance Benchmark
- [ ] Build `tests/benchmark.py` testing 1,000 deadlines in SQLite.
- [ ] Assert execution latency $< 20\text{ms}$ and record results in docs.
