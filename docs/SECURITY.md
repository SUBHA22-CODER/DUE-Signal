# DueSignal Security Architecture & Threat Model

## 1. Threat Model & Mitigation Matrix

| Threat / Attack Vector | Severity | Mitigation Strategy | Implementation |
|---|---|---|---|
| **DNS Rebinding Attacks** | High | TransportSecuritySettings and CORS origins | Server explicitly isolates local HTTP access and validates origins. |
| **SQL Injection** | Critical | Parameterized queries with aiosqlite | Zero string concatenation in SQL statements; all parameters bound via `?`. |
| **Unauthorized MCP Invocation** | High | Bearer Token Authentication | Strict `BearerAuthMiddleware` validating against cryptographically secure random token. |
| **Session Hijacking / DoS** | Medium | Stateless HTTP Mode (`stateless_http=True`) | Eliminates stateful session exhaustion and memory leaks. |
| **Input Schema Tampering** | Medium | Strict Pydantic v2 data models | Validates input bounds (`window_days <= 90`, ISO8601 formatting). |

---

## 2. Authentication Flow

Clients accessing `POST /mcp` must present an HTTP Authorization header:

```http
Authorization: Bearer <MCP_AUTH_TOKEN>
MCP-Protocol-Version: 2025-11-25
```

Requests lacking or presenting invalid tokens immediately receive an HTTP 401 Unauthorized response with zero side-effects on SQLite.
