"""Inert script-download and execution-shaped lures with no execution path."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")


def _load_decoys() -> dict[str, Any]:
    """Load fixed, side-effect-free script fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def _submission_digest(request: Request) -> str:
    body = request.scope.get("honeypot_body", b"")
    return hashlib.sha256(body).hexdigest()


def create_app() -> FastAPI:
    """Create the independently deployable script-drop trap."""

    app = FastAPI(
        title="EXAMPLE Script Exchange",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "script-drop-trap")

    def script_response(request: Request, script_key: str) -> Response:
        script = decoys["scripts"][script_key]
        mark_signal(
            request,
            "script_drop_download",
            f"script_drop_{script_key}_download",
        )
        return Response(
            content=script["body"],
            media_type=script["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{script["filename"]}"',
            },
        )

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    @app.get("/scripts")
    def script_catalog(request: Request) -> JSONResponse:
        mark_signal(request, "script_drop_catalog")
        base = _base_url(request)
        entries = []
        for script in decoys["scripts"].values():
            entries.append(
                {
                    "id": script["id"],
                    "language": script["language"],
                    "status": "EXAMPLE_AVAILABLE",
                    "download_url": f"{base}/downloads/{script['filename']}",
                }
            )
        return JSONResponse(
            {
                "status": "EXAMPLE_CATALOG_READY",
                "scripts": entries,
                "paste_url": f"{base}/api/v1/paste/EXAMPLE-PASTE-001",
                "execute_url": f"{base}/api/v1/execute",
                "analysis_url": f"{base}/analysis/EXAMPLE-SCRIPT-001",
            }
        )

    @app.get("/downloads/EXAMPLE-audit.ps1")
    def powershell_download(request: Request) -> Response:
        return script_response(request, "powershell")

    @app.get("/downloads/EXAMPLE-bootstrap.sh")
    def shell_download(request: Request) -> Response:
        return script_response(request, "shell")

    @app.get("/downloads/EXAMPLE-loader.js")
    def javascript_download(request: Request) -> Response:
        return script_response(request, "javascript")

    @app.get("/api/v1/paste/EXAMPLE-PASTE-001")
    def paste_document(request: Request) -> Response:
        mark_signal(request, "script_drop_paste_followup")
        return Response(
            content=decoys["scripts"]["powershell"]["body"],
            media_type="text/plain",
        )

    @app.post("/api/v1/execute")
    def execute_lure(request: Request) -> JSONResponse:
        mark_signal(request, "script_drop_execute_attempt")
        digest = _submission_digest(request)
        return JSONResponse(
            {
                "status": "EXAMPLE_EXECUTION_DISABLED",
                "result": "EXAMPLE_NO_PROCESS_STARTED",
                "submission_digest": f"EXAMPLE_SHA256_{digest}",
            }
        )

    @app.get("/analysis/EXAMPLE-SCRIPT-001")
    def analysis_report(request: Request) -> JSONResponse:
        mark_signal(request, "script_drop_analysis_followup")
        return JSONResponse(decoys["analysis"])

    return app


app = create_app()
