# DueSignal Friction Log

## Entry 1: Network DNS failure during large pip dependency download
- **Task:** Installing project dependencies from `requirements.txt` into virtual environment.
- **Command / steps:** `.\.venv\Scripts\pip.exe install -r requirements.txt`
- **Expected:** All packages (`botocore`, `mcp`, `strands-agents`, `boto3`, etc.) download and install cleanly.
- **Actual:**
  ```
  WARNING: Retrying ... after connection broken by 'NewConnectionError('<pip._vendor.urllib3.connection.HTTPSConnection object at ...>: Failed to establish a new connection: [Errno 11001] getaddrinfo failed')': /packages/.../s3transfer-0.19.3-py3-none-any.whl
  ERROR: Could not install packages due to an OSError: HTTPSConnectionPool(host='files.pythonhosted.org', port=443): Max retries exceeded with url: ... (Caused by NewConnectionError('...: [Errno 11001] getaddrinfo failed'))
  ```
- **Severity:** High
- **Workaround:** Re-ran `.\.venv\Scripts\pip.exe install -r requirements.txt` once internet connectivity was restored. Pip utilized cached wheels and completed installation.
- **Suggestion:** Pip installations with heavy dependencies (such as boto3/botocore > 16MB) can fail on intermittent connections. Pre-caching wheels or running with retries is advised in automated setups.

## Entry 2: Pytest module import failure on `mcp_server`
- **Task:** Running Phase 2 database unit tests with pytest.
- **Command / steps:** `.\.venv\Scripts\pytest.exe tests/test_db.py -q`
- **Expected:** Pytest imports `mcp_server.db` from the root directory and executes test suite.
- **Actual:**
  ```
  FAILED tests/test_db.py::test_add_and_list - ModuleNotFoundError: No module named 'mcp_server'
  FAILED tests/test_db.py::test_duplicate_returns_existing - ModuleNotFoundError: No module named 'mcp_server'
  ```
- **Severity:** Medium
- **Workaround:** Created `pytest.ini` with `[pytest]\npythonpath = .` to ensure pytest includes the root directory in `sys.path`.
- **Suggestion:** Document in test instructions that `pythonpath = .` should be configured in `pytest.ini` or tests should be invoked as `python -m pytest`.

## Entry 3: Datetime naive vs timezone-aware subtraction TypeError
- **Task:** Calculating `hours_left` from ISO8601 strings in `priority.py`.
- **Command / steps:** `deterministic_rank([{"due_at": "2099-01-10T00:00", ...}])`
- **Expected:** Datetime parsed and subtracted from `datetime.now(timezone.utc)`.
- **Actual:**
  ```
  TypeError: can't subtract offset-naive and offset-aware datetimes
  ```
- **Severity:** Medium
- **Workaround:** Implemented `_parse_due()` helper: if parsed datetime has no `tzinfo` (`due.tzinfo is None`), attach `timezone.utc` explicitly via `due.replace(tzinfo=timezone.utc)`.
- **Suggestion:** Input schemas should either enforce timezone offsets or parse functions must normalize naive ISO strings to UTC.

## Entry 4: Streamable HTTP TaskGroup uninitialized in Starlette mounting
- **Task:** Serving `mcp.streamable_http_app()` inside outer Starlette application with custom lifespan.
- **Command / steps:**
  ```python
  app = Starlette(lifespan=lifespan)
  app.mount("/mcp", mcp.streamable_http_app())
  ```
- **Expected:** Requests to `/mcp` handle MCP JSON-RPC protocols.
- **Actual:**
  ```
  RuntimeError: Task group is not initialized. Make sure to use run().
  ```
  In addition, mounting at `/mcp` when the sub-app internally expects `/mcp` led to `/mcp/mcp` routing and 307 redirects.
- **Severity:** High
- **Workaround:** Included `async with mcp._lowlevel_server._session_manager.run(): yield` inside outer `lifespan(app)` and mounted `mcp_streamable_app` at root `""` and `"/mcp"` to directly handle incoming `/mcp` endpoints without redirect.
- **Suggestion:** Clarify in MCP Python SDK docs that when mounting `streamable_http_app()` in an existing Starlette app with its own lifespan, the outer app must drive the session manager's lifespan or task group.

## Entry 5: Streamable HTTP session ID requirement in non-stateless mode
- **Task:** Direct tool calls via curl and browser fetch to `/mcp` without pre-establishing a session.
- **Command / steps:** `curl.exe -X POST http://127.0.0.1:8000/mcp -d '{"method":"tools/list"}'`
- **Expected:** Returns list of available tools.
- **Actual:**
  ```json
  {"jsonrpc":"2.0","id":null,"error":{"code":-32600,"message":"Bad Request: Missing session ID"}}
  ```
- **Severity:** High
- **Workaround:** Initialized `streamable_http_app` with `stateless_http=True`: `mcp.streamable_http_app(stateless_http=True, ...)`, allowing direct stateless JSON-RPC requests without prior session handshake.
- **Suggestion:** Provide explicit guidance in MCP Streamable HTTP specifications on when to use `stateless_http=True` for lightweight web/CLI clients.

## Entry 6: Browser `file://` client blocked by DNS rebinding / origin protection
- **Task:** Testing `web_client/index.html` opened directly in browser.
- **Command / steps:** Browser `fetch("http://127.0.0.1:8000/mcp", ...)` from `file:///` origin.
- **Expected:** Browser client executes `tools/call` successfully.
- **Actual:**
  ```
  WARNING: Invalid Origin header: null
  POST /mcp HTTP/1.1 403 Forbidden
  ```
- **Severity:** High
- **Workaround:** Configured `transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)` in `mcp.streamable_http_app(...)` and added `CORSMiddleware` to Starlette.
- **Suggestion:** Mention in tutorials that local HTML files opened via `file://` send `Origin: null`, which triggers default localhost security filters unless DNS rebinding checks are configured.
