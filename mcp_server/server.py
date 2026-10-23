import os
import json
import time
import uuid
import hmac
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, FileResponse
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException
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

from mcp_server.db import (
    init_db,
    list_deadlines,
    list_deadlines_filtered,
    get_deadline,
    add_deadline,
    update_deadline,
    mark_complete,
    reopen_deadline,
    delete_deadline,
    clear_all_deadlines,
    count_deadlines,
    seed_scenario,
)
from mcp_server.models import ListDeadlinesInput, AddDeadlineInput, MarkCompleteInput
from mcp_server.priority import deterministic_rank, bedrock_reason

# Telemetry store
telemetry = {
    "start_time": time.time(),
    "total_requests": 0,
    "tool_calls": {
        "tool_list_deadlines": 0,
        "tool_add_deadline": 0,
        "tool_mark_complete": 0,
        "tool_get_priority_ranking": 0,
    },
    "total_latency_ms": 0.0,
}

# The 4 Required MCP Tools
@mcp.tool()
async def tool_list_deadlines(window_days: int = 7) -> str:
    """Return pending deadlines within the next N days."""
    telemetry["tool_calls"]["tool_list_deadlines"] += 1
    p = ListDeadlinesInput(window_days=window_days)
    rows = await list_deadlines(p.window_days)
    return json.dumps({"deadlines": rows})

@mcp.tool()
async def tool_add_deadline(title: str, course: str, due_at: str, weight_pct: float = 0) -> str:
    """Add a deadline. due_at must be ISO8601, e.g. 2026-10-25T23:59."""
    telemetry["tool_calls"]["tool_add_deadline"] += 1
    p = AddDeadlineInput(title=title, course=course, due_at=due_at, weight_pct=weight_pct)
    r = await add_deadline(p.title, p.course, p.due_at, p.weight_pct)
    return json.dumps(r)

@mcp.tool()
async def tool_mark_complete(id: int) -> str:
    """Mark a deadline as completed."""
    telemetry["tool_calls"]["tool_mark_complete"] += 1
    p = MarkCompleteInput(id=id)
    r = await mark_complete(p.id)
    return json.dumps(r)

@mcp.tool()
async def tool_get_priority_ranking(date: str = "") -> str:
    """Rank pending deadlines by urgency and grade weight, with a reason for each."""
    telemetry["tool_calls"]["tool_get_priority_ranking"] += 1
    rows = await list_deadlines(window_days=90)
    ranked = deterministic_rank(rows)
    enriched = bedrock_reason(ranked)
    return json.dumps({"ranked": enriched})


class SecurityAndObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        req_id = str(uuid.uuid4())
        telemetry["total_requests"] += 1

        # Public endpoints (static assets, health, metrics, client REST API)
        public_routes = (
            "/health", "/metrics", "/docs", "/", "/index.html", "/favicon.ico",
            "/api/deadlines", "/api/summary", "/api/demo/seed"
        )
        is_public = (
            request.method == "OPTIONS" or 
            any(request.url.path == p or request.url.path.startswith("/api/deadlines") for p in public_routes)
        )

        if not is_public and MCP_AUTH_TOKEN:
            auth = request.headers.get("Authorization", "")
            expected = f"Bearer {MCP_AUTH_TOKEN}"
            # Constant-time comparison to prevent timing side-channel attacks
            if not hmac.compare_digest(auth.encode("utf-8"), expected.encode("utf-8")):
                return JSONResponse(
                    {"error": "Unauthorized", "message": "Invalid or missing Bearer token."},
                    status_code=401,
                    headers={"X-Request-ID": req_id}
                )

        response = await call_next(request)
        elapsed_ms = round((time.time() - start) * 1000, 2)
        telemetry["total_latency_ms"] += elapsed_ms

        response.headers["X-Request-ID"] = req_id
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
        return response


from mcp.server.transport_security import TransportSecuritySettings

transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
mcp_streamable_app = mcp.streamable_http_app(stateless_http=True, transport_security=transport_security)

async def serve_index(request):
    if WEB_CLIENT_PATH.exists():
        return FileResponse(WEB_CLIENT_PATH, media_type="text/html")
    return JSONResponse({"name": "DueSignal MCP Server", "status": "running"})

async def get_metrics(request):
    counts = await count_deadlines()
    uptime_sec = round(time.time() - telemetry["start_time"], 1)
    reqs = max(telemetry["total_requests"], 1)
    avg_latency = round(telemetry["total_latency_ms"] / reqs, 2)
    return JSONResponse({
        "status": "healthy",
        "uptime_seconds": uptime_sec,
        "total_requests": telemetry["total_requests"],
        "average_latency_ms": avg_latency,
        "mcp_tool_invocations": telemetry["tool_calls"],
        "database": counts,
        "mcp_protocol_version": "2025-11-25",
        "server_engine": "DueSignal FastMCP + Starlette",
    })

async def get_summary_api(request):
    counts = await count_deadlines()
    all_pending = await list_deadlines(window_days=90)
    ranked = deterministic_rank(all_pending)
    overdue_count = sum(1 for d in ranked if d.get("is_overdue"))
    critical_count = sum(1 for d in ranked if d.get("urgency_band") == "CRITICAL")
    top_task = ranked[0] if ranked else None

    # Determine Bedrock availability status honestly
    bedrock_configured = bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")) or bool(os.getenv("AWS_PROFILE"))
    
    return JSONResponse({
        **counts,
        "overdue_count": overdue_count,
        "critical_count": critical_count,
        "top_task": top_task,
        "bedrock_configured": bedrock_configured,
        "ranking_engine": "Urgency x Grade Weight (Deterministic)",
    })

async def get_deadlines_api(request):
    status = request.query_params.get("status", "all")
    course = request.query_params.get("course", None)
    search = request.query_params.get("search", None)
    sort_by = request.query_params.get("sort_by", "priority")
    window_days = int(request.query_params.get("window_days", 90))

    rows = await list_deadlines_filtered(status=status, window_days=window_days, course=course, search=search)
    ranked = deterministic_rank(rows)

    if sort_by == "due":
        ranked.sort(key=lambda x: (x["due_at"], -x.get("weight_pct", 0)))
    elif sort_by == "weight":
        ranked.sort(key=lambda x: (-x.get("weight_pct", 0), x["due_at"]))

    return JSONResponse({"deadlines": ranked, "count": len(ranked)})

async def post_deadline_api(request):
    try:
        data = await request.json()
        title = data["title"].strip()
        course = data.get("course", "Course").strip()
        due_at = data["due_at"].strip()
        weight_pct = float(data.get("weight_pct", 0))
    except Exception as exc:
        return JSONResponse({"error": f"Invalid payload: {str(exc)}"}, status_code=400)

    res = await add_deadline(title, course, due_at, weight_pct)
    return JSONResponse(res, status_code=201 if res.get("created") else 200)

async def deadline_item_router(request):
    deadline_id = int(request.path_params["id"])
    action = request.path_params.get("action", "")

    try:
        if request.method == "GET":
            item = await get_deadline(deadline_id)
            if not item:
                return JSONResponse({"error": "Not found"}, status_code=404)
            return JSONResponse(item)

        elif request.method == "PUT":
            data = await request.json()
            res = await update_deadline(
                deadline_id,
                data["title"].strip(),
                data.get("course", "Course").strip(),
                data["due_at"].strip(),
                float(data.get("weight_pct", 0))
            )
            return JSONResponse(res)

        elif request.method == "DELETE":
            res = await delete_deadline(deadline_id)
            return JSONResponse(res)

        elif request.method == "POST":
            if action == "complete":
                res = await mark_complete(deadline_id)
                return JSONResponse(res)
            elif action == "reopen":
                res = await reopen_deadline(deadline_id)
                return JSONResponse(res)

    except ValueError as val_err:
        return JSONResponse({"error": str(val_err)}, status_code=404)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)

    return JSONResponse({"error": "Method not allowed"}, status_code=405)

async def seed_demo_endpoint(request):
    try:
        data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    except Exception:
        data = {}
    scenario = data.get("scenario", "finals_crisis")
    if scenario == "clear":
        res = await clear_all_deadlines()
    else:
        res = await seed_scenario(scenario)
    return JSONResponse(res)

@asynccontextmanager
async def lifespan(app):
    await init_db()
    async with mcp._lowlevel_server._session_manager.run():
        yield

app = Starlette(
    routes=[
        Route("/health", lambda r: JSONResponse({"ok": True})),
        Route("/metrics", get_metrics),
        Route("/api/summary", get_summary_api),
        Route("/api/deadlines", get_deadlines_api, methods=["GET"]),
        Route("/api/deadlines", post_deadline_api, methods=["POST"]),
        Route("/api/deadlines/{id:int}", deadline_item_router, methods=["GET", "PUT", "DELETE"]),
        Route("/api/deadlines/{id:int}/{action:str}", deadline_item_router, methods=["POST"]),
        Route("/api/demo/seed", seed_demo_endpoint, methods=["POST", "GET"]),
        Route("/", serve_index),
        Route("/index.html", serve_index),
    ],
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"], allow_headers=["*"], allow_methods=["*"]),
        Middleware(SecurityAndObservabilityMiddleware),
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
