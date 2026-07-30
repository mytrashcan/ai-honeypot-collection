"""Inert Agent-to-Agent protocol decoys backed by synthetic fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")
UPLOAD_MEDIA_TYPES = ("multipart/form-data", "application/octet-stream")


def _load_decoys() -> dict[str, Any]:
    """Load fixed Agent Card, message, and task fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _reject_file_upload(request: Request) -> JSONResponse | None:
    """Reject file-shaped input before any application-level parsing."""

    content_type = request.headers.get("content-type", "").lower()
    if any(media_type in content_type for media_type in UPLOAD_MEDIA_TYPES):
        return JSONResponse(
            {"detail": "EXAMPLE agent does not accept files; no work was launched"},
            status_code=415,
        )
    return None


def create_app() -> FastAPI:
    """Create the independently deployable A2A honeypot."""

    app = FastAPI(
        title="EXAMPLE A2A Agent",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "a2a-agent-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/.well-known/agent-card.json")
    def agent_card(request: Request) -> JSONResponse:
        mark_signal(request, "a2a_discovery")
        return JSONResponse(decoys["agent_card"])

    @app.post("/message:send")
    def message_send(request: Request) -> JSONResponse:
        mark_signal(request, "a2a_message_send")
        rejected = _reject_file_upload(request)
        if rejected is not None:
            return rejected
        return JSONResponse(decoys["message_response"])

    @app.post("/message:stream")
    def message_stream(request: Request) -> Response:
        mark_signal(request, "a2a_message_send")
        rejected = _reject_file_upload(request)
        if rejected is not None:
            return rejected
        event = json.dumps(decoys["message_response"], separators=(",", ":"))
        return PlainTextResponse(
            f"event: task\ndata: {event}\n\n",
            media_type="text/event-stream",
        )

    @app.get("/tasks")
    def task_list(request: Request) -> JSONResponse:
        mark_signal(request, "a2a_task_status")
        return JSONResponse({"tasks": [decoys["task"]]})

    @app.get("/tasks/{task_id}")
    def task_status(request: Request, task_id: str) -> JSONResponse:
        mark_signal(request, "a2a_task_status")
        return JSONResponse(decoys["task"])

    @app.post("/tasks/{task_id}:cancel")
    def task_cancel(request: Request, task_id: str) -> JSONResponse:
        mark_signal(request, "a2a_task_cancel")
        return JSONResponse(decoys["cancel_response"])

    return app


app = create_app()
