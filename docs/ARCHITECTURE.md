# DueSignal Architecture Documentation

## System Topology

DueSignal bridges voice and conversational interfaces (such as Alexa+) to academic task management using the **Model Context Protocol (MCP)** specification over **Streamable HTTP** (protocol version `2025-11-25`).

```
+-------------------------------------------------------+
|                Client Layer                           |
|  - Alexa+ Conversational Assistant                   |
|  - DueSignal Interactive Browser Client (HTML5/Web)  |
+-------------------------------------------------------+
                           |
                           | HTTP / JSON-RPC 2.0 (Bearer Token Auth)
                           v
+-------------------------------------------------------+
|             Starlette HTTP Server (Port 8000)         |
|  - CORS & DNS Rebinding Security Middleware           |
|  - Bearer Token Authentication Middleware             |
|  - Healthcheck Route: GET /health                     |
|  - Single-Origin Web App: GET / & GET /index.html     |
|  - MCP Streamable HTTP Mount: POST /mcp & /           |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|             DueSignal FastMCP Engine                  |
|  Tools:                                               |
|  1. tool_list_deadlines(window_days)                  |
|  2. tool_add_deadline(title, course, due_at, weight)  |
|  3. tool_mark_complete(id)                            |
|  4. tool_get_priority_ranking(date)                   |
+-------------------------------------------------------+
            |                                 |
            v                                 v
+-----------------------+         +-------------------------------+
|     SQLite Database   |         |      Amazon Bedrock           |
|  - Table: deadlines   |         |  - Strands Agents SDK         |
|  - Indexed due_at     |         |  - amazon.nova-micro-v1:0     |
|  - Async aiosqlite    |         |  - Natural Language Explainer |
+-----------------------+         |  (Graceful fallback if no AWS)|
                                  +-------------------------------+
```

## Prioritization Algorithm

Deadlines are sorted deterministically according to urgency and academic stakes:

$$\text{Urgency} = \frac{1}{\max(1.0, \text{Hours Left})}$$

$$\text{Score} = \text{Urgency} \times (1.0 + \text{Grade Weight \%})$$

1. **High Urgency + High Weight:** Highest priority score.
2. **Expired / Completed:** Filtered out or placed into archival state.
3. **Bedrock Enrichment:** When AWS credentials are present, Claude/Nova synthesizes a natural-language reason tailored for voice delivery; otherwise, deterministic explanation templates are generated instantaneously.
