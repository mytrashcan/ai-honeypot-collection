"""CBC-shaped session-cookie lures that never grant real authorization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")
COOKIE_NAME = "session"


def _load_decoys() -> dict[str, Any]:
    """Load fixed cookie, decoder, and export fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def _is_tampered(request: Request, issued_cookie: str) -> bool:
    submitted = request.cookies.get(COOKIE_NAME)
    return submitted is not None and submitted != issued_cookie


def create_app() -> FastAPI:
    """Create the independently deployable session-cookie trap."""

    app = FastAPI(
        title="EXAMPLE Session Service",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    issued_cookie = str(decoys["issued_cookie"])
    install_fastapi_tracking(app, "session-cookie-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    @app.get("/session/issue")
    def issue_session(request: Request) -> HTMLResponse:
        mark_signal(request, "session_cookie_issue")
        admin_url = f"{_base_url(request)}/admin"
        response = HTMLResponse(
            "<!doctype html><html><body>"
            "<h1>EXAMPLE Account Portal</h1>"
            "<p>EXAMPLE role=guest; cipher=EXAMPLE_AES-CBC; "
            "block-size=EXAMPLE_16_BYTES</p>"
            f"<a href='{admin_url}'>EXAMPLE Admin</a>"
            "</body></html>"
        )
        response.set_cookie(
            COOKIE_NAME,
            issued_cookie,
            httponly=True,
            samesite="lax",
        )
        return response

    @app.get("/admin")
    def admin_panel(request: Request) -> HTMLResponse:
        mark_signal(request, "session_cookie_admin_probe")
        if _is_tampered(request, issued_cookie):
            mark_signal(request, "session_cookie_tamper")
            export_url = f"{_base_url(request)}/admin/export"
            return HTMLResponse(
                "<!doctype html><html><body>"
                "<h1>EXAMPLE Admin Console</h1>"
                "<p>EXAMPLE role=admin</p>"
                f"<a href='{export_url}'>EXAMPLE Export</a>"
                "</body></html>"
            )
        return HTMLResponse(
            "<!doctype html><html><body>"
            "<h1>EXAMPLE Access Denied</h1>"
            "<p>EXAMPLE role=guest</p>"
            "</body></html>",
            status_code=403,
        )

    @app.get("/admin/export")
    def admin_export(request: Request) -> JSONResponse:
        mark_signal(request, "session_cookie_admin_followup")
        if _is_tampered(request, issued_cookie):
            mark_signal(request, "session_cookie_tamper")
        return JSONResponse(decoys["admin_export"])

    @app.post("/api/v1/session/decode")
    def decode_session(request: Request) -> JSONResponse:
        body = request.scope.get("honeypot_body", b"")
        digest = hashlib.sha256(body).hexdigest()
        mark_signal(request, "session_cookie_decode", "session_cookie_tamper")
        return JSONResponse(
            {
                **decoys["decoder"],
                "submission_digest": f"EXAMPLE_SHA256_{digest}",
            }
        )

    return app


app = create_app()
