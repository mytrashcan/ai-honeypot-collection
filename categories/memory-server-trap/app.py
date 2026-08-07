"""Inert Mem0/Zep-style agent memory-sync API decoys.

The service mimics a long-term memory server that AI agents use to store
and retrieve conversational memory. Agents that probe or post to a
discovered memory endpoint reveal their identity. Payloads are bounded
(64 KiB) and only metadata + digests are recorded — never raw content.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")

EXAMPLE_SESSION_ID = "EXAMPLE_SESSION_0001"
EXAMPLE_USER_ID = "EXAMPLE_USER_0001"


def _load_decoys() -> dict[str, Any]:
    """Load the immutable memory fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _body_digest(body: bytes) -> str:
    """Return a bounded SHA-256 digest of a request body, never the body."""

    return hashlib.sha256(body).hexdigest() if body else ""


def create_app() -> FastAPI:
    """Create the independently deployable memory-server honeypot."""

    app = FastAPI(
        title="EXAMPLE Memory Server",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "memory-server-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/memories")
    def memories_list(request: Request) -> JSONResponse:
        mark_signal(request, "memory_server_list")
        return JSONResponse({"memories": decoys["memories"], "has_more": False})

    @app.post("/v1/memories")
    def memories_add(request: Request) -> JSONResponse:
        # The tracking middleware publishes the bounded body (<= 64 KiB) on
        # the shared scope; raw content is never stored or echoed.
        body = request.scope.get("honeypot_body", b"")
        mark_signal(request, "memory_server_add")
        return JSONResponse(
            {
                "id": "EXAMPLE_MEMORY_0001",
                "status": "stored",
                "body_sha256": _body_digest(body),
            }
        )

    @app.post("/v1/memories/search")
    def memories_search(request: Request) -> JSONResponse:
        body = request.scope.get("honeypot_body", b"")
        mark_signal(request, "memory_server_search")
        return JSONResponse(
            {
                "memories": decoys["memories"],
                "query_digest": _body_digest(body),
            }
        )

    @app.get("/v1/sessions")
    def sessions_list(request: Request) -> JSONResponse:
        mark_signal(request, "memory_server_sessions")
        return JSONResponse(
            {"sessions": [{"id": EXAMPLE_SESSION_ID, "user_id": EXAMPLE_USER_ID}]}
        )

    @app.get("/v1/sessions/{session_id}/messages")
    def session_messages(session_id: str, request: Request) -> JSONResponse:
        if session_id != EXAMPLE_SESSION_ID:
            return JSONResponse({"error": "Not found"}, status_code=404)
        mark_signal(request, "memory_server_session_messages")
        return JSONResponse({"messages": decoys["messages"]})

    @app.post("/v1/sessions/{session_id}/messages")
    def session_messages_add(session_id: str, request: Request) -> JSONResponse:
        if session_id != EXAMPLE_SESSION_ID:
            return JSONResponse({"error": "Not found"}, status_code=404)
        # Same cross-module contract as /v1/memories: scope-published body.
        body = request.scope.get("honeypot_body", b"")
        mark_signal(request, "memory_server_session_message_add")
        return JSONResponse(
            {"id": "EXAMPLE_MESSAGE_0001", "body_sha256": _body_digest(body)}
        )

    @app.get("/api/memory")
    def api_memory(request: Request) -> JSONResponse:
        mark_signal(request, "memory_server_api_memory")
        return JSONResponse({"status": "ok", "backend": "EXAMPLE", "users": 1})

    @app.get("/memories")
    def memories_legacy(request: Request) -> JSONResponse:
        mark_signal(request, "memory_server_legacy")
        return JSONResponse({"memories": decoys["memories"]})

    return app


app = create_app()
