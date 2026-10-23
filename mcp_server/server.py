import os
import json
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, FileResponse
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path

WEB_CLIENT_PATH = Path(__file__).resolve().parent.parent / "web_client" / "index.html"

load_dotenv()

MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "QiLwfdv5r2zB3zXB4iiLpXJF-MNGsAEc1hcfgjRTEcY")

try:
    from mcp.server import MCPServer as _MCP
except ImportError:
    from mcp.server.fastmcp import FastMCP as _MCP

mcp = _MCP(
    "DueSignal",
    instructions=(
        "Manage academic deadlines. Always prioritize by urgency and grade weight. "
        "Never invent deadlines that are not in the database."
    ),
)

from mcp_server.db import init_db, list_deadlines, add_deadline, mark_complete
from mcp_server.models import ListDeadlinesInput, AddDeadlineInput, MarkCompleteInput
from mcp_server.priority import deterministic_rank, bedrock_reason

@mcp.tool()
async def tool_list_deadlines(window_days: int = 7) -> str:
    """Return pending deadlines within the next N days."""
    p = ListDeadlinesInput(window_days=window_days)
    rows = await list_deadlines(p.window_days)
    return json.dumps({"deadlines": rows})

@mcp.tool()
async def tool_add_deadline(title: str, course: str, due_at: str, weight_pct: float = 0) -> str:
    """Add a deadline. due_at must be ISO8601, e.g. 2026-10-25T23:59."""
    p = AddDeadlineInput(title=title, course=course, due_at=due_at, weight_pct=weight_pct)
    r = await add_deadline(p.title, p.course, p.due_at, p.weight_pct)
    return json.dumps(r)

@mcp.tool()
async def tool_mark_complete(id: int) -> str:
    """Mark a deadline as completed."""
    p = MarkCompleteInput(id=id)
    try:
        return json.dumps(await mark_complete(p.id))
    except ValueError as exc:
        return json.dumps({"error": str(exc), "code": -32000, "retryable": False})

@mcp.tool()
async def tool_get_priority_ranking(date: str = "") -> str:
    """Rank pending deadlines by urgency and grade weight, with a reason for each."""
    rows = await list_deadlines(window_days=30)
    if not rows:
        return json.dumps({"ranked": [], "message": "No pending deadlines."})
    ranked = deterministic_rank(rows)
    ranked = bedrock_reason(ranked)
    return json.dumps({"ranked": ranked})

class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method == "OPTIONS" or request.url.path in ("/health", "/docs", "/", "/index.html", "/favicon.ico"):
            return await call_next(request)
        if MCP_AUTH_TOKEN:
            auth = request.headers.get("Authorization", "")
            if auth != f"Bearer {MCP_AUTH_TOKEN}":
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)

from mcp.server.transport_security import TransportSecuritySettings

transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
mcp_streamable_app = mcp.streamable_http_app(stateless_http=True, transport_security=transport_security)

async def serve_index(request):
    if WEB_CLIENT_PATH.exists():
        return FileResponse(WEB_CLIENT_PATH, media_type="text/html")
    return JSONResponse({"name": "DueSignal MCP Server", "status": "running"})

@asynccontextmanager
async def lifespan(app):
    await init_db()
    async with mcp._lowlevel_server._session_manager.run():
        yield

app = Starlette(
    routes=[
        Route("/health", lambda r: JSONResponse({"ok": True})),
        Route("/", serve_index),
        Route("/index.html", serve_index),
    ],
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["*"], allow_headers=["*"], allow_methods=["*"]),
        Middleware(BearerAuthMiddleware),
    ],
    lifespan=lifespan,
)


app.mount("/mcp", mcp_streamable_app)
app.mount("", mcp_streamable_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        log_level="info",
    )
