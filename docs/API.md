# DueSignal MCP Protocol & API Specification

Protocol Version: `2025-11-25`  
Base URL: `http://127.0.0.1:8000`  
Endpoint: `POST /mcp`  
Authentication: `Authorization: Bearer <MCP_AUTH_TOKEN>`

## 1. HTTP Endpoints

| Method | Path | Description | Auth Required |
|---|---|---|---|
| `GET` | `/health` | Healthcheck (returns `{"ok": true}`) | No |
| `GET` | `/` | Web Client HTML interface | No |
| `POST` | `/mcp` | MCP JSON-RPC 2.0 Streamable HTTP endpoint | Yes |

## 2. JSON-RPC 2.0 Tools

### `tool_list_deadlines`
Retrieve pending deadlines within a forward-looking window.
- **Parameters:**
  - `window_days` (integer, default: 7): Lookahead timeframe in days.
- **Response:**
  ```json
  {"deadlines": [{"id": 1, "title": "Homework 1", "course": "CS101", "due_at": "2026-10-25T23:59", "weight_pct": 10.0, "status": "pending"}]}
  ```

### `tool_add_deadline`
Create a new academic deadline.
- **Parameters:**
  - `title` (string, required): Title of assignment or exam.
  - `course` (string, required): Course identifier (e.g. `CS301`).
  - `due_at` (string, required): ISO8601 formatted datetime string (`YYYY-MM-DDTHH:MM`).
  - `weight_pct` (number, optional, default: 0): Percentage weight of overall course grade.
- **Response:**
  ```json
  {"id": 1, "created": true}
  ```

### `tool_mark_complete`
Mark a deadline as done.
- **Parameters:**
  - `id` (integer, required): Deadline database identifier.
- **Response:**
  ```json
  {"id": 1, "status": "completed"}
  ```

### `tool_get_priority_ranking`
Sort and prioritize all pending deadlines with urgency $\times$ grade weight calculation and natural language rationale.
- **Parameters:**
  - `date` (string, optional): Base reference date (defaults to current UTC time).
- **Response:**
  ```json
  {
    "ranked": [
      {
        "id": 1,
        "title": "OS Project",
        "course": "CS301",
        "due_at": "2026-10-25T23:59",
        "weight_pct": 25.0,
        "status": "pending",
        "score": 18.98,
        "deterministic_reason": "Due in 66h, worth 25.0% of grade."
      }
    ]
  }
  ```
