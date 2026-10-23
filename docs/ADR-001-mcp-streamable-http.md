# ADR 001: Streamable HTTP Protocol with Stateless Mode and Embedded Web UI

## Status
Accepted

## Context
Alexa+ and modern AI assistants require low-latency, resilient tool invocation. Traditional MCP over stdio is suitable only for local CLI processes. MCP protocol `2025-11-25` introduced Streamable HTTP for network-accessible servers. In browser-based and multi-client environments, connection state drops and CORS/origin security checks can prevent reliable communication.

## Decisions

1. **Streamable HTTP over FastMCP with `stateless_http=True`**:
   - Enables JSON-RPC 2.0 requests without mandatory session negotiation or cookies.
   - Ideal for serverless or containerized scale-out.

2. **Unified Starlette Server with Co-located HTML5 Client**:
   - Serving `web_client/index.html` directly from `/` eliminates cross-origin / `null` origin barriers when opened via `file://`.
   - Maintains full CORS support for external clients like Alexa+.

3. **Deterministic Urgency Scoring with Bedrock Fallback**:
   - Critical path ranking cannot fail even if cloud AI credentials expire or network times out.
   - Core triage calculates deterministically in sub-millisecond time; Bedrock provides asynchronous enrichment.

4. **Async SQLite with WAL Mode**:
   - Zero external infrastructure dependency.
   - Thread-safe and persistent across container restarts.

## Consequences
- Fast deployment anywhere (Docker, local Windows, or Linux).
- Seamless client testing with zero setup friction.
