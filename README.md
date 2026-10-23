# DueSignal

Self-hosted Alexa+ MCP server that turns scattered academic deadlines into one prioritized daily answer.

## What it does
- Exposes four MCP tools over Streamable HTTP (protocol 2025-11-25).
- Stores deadlines in SQLite.
- Ranks by urgency × grade weight; uses Amazon Bedrock (via Strands) for a natural-language reason, with deterministic fallback.

## Verified environment
- OS: Windows 11
- Python: Python 3.11.9
- mcp: 2.1.1
- strands-agents: 1.62.0
- boto3: 1.43.118

## Setup (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env: set MCP_AUTH_TOKEN to a random string, and AWS credentials if using Bedrock
python -m mcp_server.server
```

## Smoke test (executed output)
```powershell
$TOKEN = "[REDACTED]"

# 1. Health check
curl.exe -s http://127.0.0.1:8000/health
# {"ok":true}

# 2. Initialize
curl.exe -s -X POST http://127.0.0.1:8000/mcp -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "Authorization: Bearer $TOKEN" -H "MCP-Protocol-Version: 2025-11-25" -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-11-25\",\"capabilities\":{},\"clientInfo\":{\"name\":\"smoke\",\"version\":\"1.0\"}}}'
# event: message
# data: {"jsonrpc":"2.0","id":1,"result":{"capabilities":{"experimental":{},"prompts":{"listChanged":false},"resources":{"listChanged":false,"subscribe":false},"tools":{"listChanged":false}},"instructions":"Manage academic deadlines. Always prioritize by urgency and grade weight. Never invent deadlines that are not in the database.","protocolVersion":"2025-11-25","serverInfo":{"name":"DueSignal","version":""}}}

# 3. Tools list
curl.exe -s -X POST http://127.0.0.1:8000/mcp -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "Authorization: Bearer $TOKEN" -H "MCP-Protocol-Version: 2025-11-25" -d '{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\",\"params\":{}}'
# event: message
# data: {"jsonrpc":"2.0","id":2,"result":{"tools":[{"description":"Return pending deadlines within the next N days.","inputSchema":{"properties":{"window_days":{"default":7,"title":"Window Days","type":"integer"}},"type":"object","title":"tool_list_deadlinesArguments"},"name":"tool_list_deadlines","outputSchema":{"properties":{"result":{"title":"Result","type":"string"}},"required":["result"],"type":"object","title":"tool_list_deadlinesOutput"}},{"description":"Add a deadline. due_at must be ISO8601, e.g. 2026-10-25T23:59.","inputSchema":{"properties":{"title":{"title":"Title","type":"string"},"course":{"title":"Course","type":"string"},"due_at":{"title":"Due At","type":"string"},"weight_pct":{"default":0,"title":"Weight Pct","type":"number"}},"required":["title","course","due_at"],"type":"object","title":"tool_add_deadlineArguments"},"name":"tool_add_deadline","outputSchema":{"properties":{"result":{"title":"Result","type":"string"}},"required":["result"],"type":"object","title":"tool_add_deadlineOutput"}},{"description":"Mark a deadline as completed.","inputSchema":{"properties":{"id":{"title":"Id","type":"integer"}},"required":["id"],"type":"object","title":"tool_mark_completeArguments"},"name":"tool_mark_complete","outputSchema":{"properties":{"result":{"title":"Result","type":"string"}},"required":["result"],"type":"object","title":"tool_mark_completeOutput"}},{"description":"Rank pending deadlines by urgency and grade weight, with a reason for each.","inputSchema":{"properties":{"date":{"default":"","title":"Date","type":"string"}},"type":"object","title":"tool_get_priority_rankingArguments"},"name":"tool_get_priority_ranking","outputSchema":{"properties":{"result":{"title":"Result","type":"string"}},"required":["result"],"type":"object","title":"tool_get_priority_rankingOutput"}}]}}

# 4. Add deadline
curl.exe -s -X POST http://127.0.0.1:8000/mcp -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "Authorization: Bearer $TOKEN" -H "MCP-Protocol-Version: 2025-11-25" -d "{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"tool_add_deadline\",\"arguments\":{\"title\":\"OS Project\",\"course\":\"CS301\",\"due_at\":\"2026-10-25T23:59\",\"weight_pct\":25}}}"
# event: message
# data: {"jsonrpc":"2.0","id":3,"result":{"content":[{"text":"{\"id\": 1, \"created\": true}","type":"text"}],"isError":false,"structuredContent":{"result":"{\"id\": 1, \"created\": true}"}}}

# 5. Priority ranking
curl.exe -s -X POST http://127.0.0.1:8000/mcp -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "Authorization: Bearer $TOKEN" -H "MCP-Protocol-Version: 2025-11-25" -d "{\"jsonrpc\":\"2.0\",\"id\":4,\"method\":\"tools/call\",\"params\":{\"name\":\"tool_get_priority_ranking\",\"arguments\":{}}}"
# event: message
# data: {"jsonrpc":"2.0","id":4,"result":{"content":[{"text":"{\"ranked\": [{\"id\": 1, \"title\": \"OS Project\", \"course\": \"CS301\", \"due_at\": \"2026-10-25T23:59\", \"weight_pct\": 25.0, \"status\": \"pending\", \"score\": 18.98, \"deterministic_reason\": \"Due in 66h, worth 25.0% of grade.\", \"bedrock_error\": \"Unable to locate credentials\"}]}","type":"text"}],"isError":false,"structuredContent":{"result":"{\"ranked\": [{\"id\": 1, \"title\": \"OS Project\", \"course\": \"CS301\", \"due_at\": \"2026-10-25T23:59\", \"weight_pct\": 25.0, \"status\": \"pending\", \"score\": 18.98, \"deterministic_reason\": \"Due in 66h, worth 25.0% of grade.\", \"bedrock_error\": \"Unable to locate credentials\"}]}"}}}
```

## Run tests
```powershell
pytest -q
# 6 passed in 1.27s
```

## MCP tools
| Tool | Purpose |
|---|---|
| tool_list_deadlines | Pending deadlines in next N days |
| tool_add_deadline | Insert a deadline (ISO8601 due_at) |
| tool_mark_complete | Mark a deadline done |
| tool_get_priority_ranking | Ranked deadlines with reason |

## Architecture
Client → POST /mcp (Bearer auth, MCP-Protocol-Version: 2025-11-25) → MCP tools → SQLite → optional Bedrock via Strands → JSON-RPC response.
