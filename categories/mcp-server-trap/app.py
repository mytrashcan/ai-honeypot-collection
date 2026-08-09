"""Inert Model Context Protocol decoys backed by synthetic fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")


def _load_decoys() -> dict[str, Any]:
    """Load fixed MCP discovery and response fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _base_url(request: Request) -> str:
    """Return the current honeypot base URL without a trailing slash."""

    return str(request.base_url).rstrip("/")


def _resolve_base_urls(value: Any, base: str) -> Any:
    """Replace synthetic base placeholders without mutating fixture data."""

    if isinstance(value, dict):
        return {key: _resolve_base_urls(item, base) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_base_urls(item, base) for item in value]
    if isinstance(value, str):
        return value.replace("EXAMPLE_BASE_URL", base)
    return value


async def _request_json(request: Request) -> dict[str, Any]:
    """Return a JSON object without retaining or acting on submitted content."""

    try:
        payload = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def create_app() -> FastAPI:
    """Create the independently deployable MCP honeypot."""

    app = FastAPI(
        title="EXAMPLE MCP Server",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "mcp-server-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/.well-known/mcp.json")
    def mcp_discovery(request: Request) -> JSONResponse:
        mark_signal(request, "mcp_discovery")
        return JSONResponse(_resolve_base_urls(decoys["discovery"], _base_url(request)))

    @app.get("/mcp-sse")
    def mcp_sse(request: Request) -> PlainTextResponse:
        mark_signal(request, "mcp_discovery")
        return PlainTextResponse(
            f"event: endpoint\ndata: {_base_url(request)}/mcp\n\n",
            media_type="text/event-stream",
        )

    def tool_list(request: Request) -> JSONResponse:
        mark_signal(request, "mcp_tool_list")
        return JSONResponse({"tools": decoys["tools"]})

    @app.api_route("/tools/list", methods=["GET", "POST"])
    def direct_tool_list(request: Request) -> JSONResponse:
        return tool_list(request)

    @app.post("/tools/call")
    async def direct_tool_call(request: Request) -> JSONResponse:
        payload = await _request_json(request)
        mark_signal(request, "mcp_tool_call")
        name = payload.get("name") or payload.get("params", {}).get("name")
        result = decoys["tool_results"].get(name, decoys["unknown_tool_result"])
        return JSONResponse(_resolve_base_urls(result, _base_url(request)))

    @app.api_route("/resources/list", methods=["GET", "POST"])
    def resource_list(request: Request) -> JSONResponse:
        mark_signal(request, "mcp_resource_list")
        result = {"resources": decoys["resources"]}
        return JSONResponse(_resolve_base_urls(result, _base_url(request)))

    @app.post("/resources/read")
    async def resource_read(request: Request) -> JSONResponse:
        await _request_json(request)
        mark_signal(request, "mcp_resource_list")
        result = {"contents": decoys["resource_contents"]}
        return JSONResponse(_resolve_base_urls(result, _base_url(request)))

    @app.api_route("/prompts/list", methods=["GET", "POST"])
    def prompt_list(request: Request) -> JSONResponse:
        mark_signal(request, "mcp_tool_list")
        return JSONResponse({"prompts": decoys["prompts"]})

    @app.post("/mcp")
    async def mcp(request: Request) -> JSONResponse:
        payload = await _request_json(request)
        request_id = payload.get("id")
        method = payload.get("method")

        if method == "initialize":
            mark_signal(request, "mcp_initialize")
            result: dict[str, Any] = decoys["initialize"]
        elif method == "tools/list":
            mark_signal(request, "mcp_tool_list")
            result = {"tools": decoys["tools"]}
        elif method == "tools/call":
            mark_signal(request, "mcp_tool_call")
            params = payload.get("params", {})
            name = params.get("name") if isinstance(params, dict) else None
            result = decoys["tool_results"].get(name, decoys["unknown_tool_result"])
        elif method == "resources/list":
            mark_signal(request, "mcp_resource_list")
            result = {"resources": decoys["resources"]}
        elif method == "resources/read":
            mark_signal(request, "mcp_resource_list")
            result = {"contents": decoys["resource_contents"]}
        elif method == "prompts/list":
            mark_signal(request, "mcp_tool_list")
            result = {"prompts": decoys["prompts"]}
        else:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": "EXAMPLE method not found; no action was performed",
                    },
                },
                status_code=404,
            )

        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": _resolve_base_urls(result, _base_url(request)),
        }
        return JSONResponse(response)

    return app


app = create_app()
