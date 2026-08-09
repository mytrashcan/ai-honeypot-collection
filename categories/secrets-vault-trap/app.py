"""Inert vault-unlock lure with deterministic, bounded progress responses."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")


def _load_decoys() -> dict[str, Any]:
    """Load fixed vault fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def _submission_digest(request: Request) -> str:
    body = request.scope.get("honeypot_body", b"")
    return hashlib.sha256(body).hexdigest()


def create_app() -> FastAPI:
    """Create the independently deployable secrets-vault trap."""

    app = FastAPI(
        title="EXAMPLE Recovery Vault",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "secrets-vault-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    @app.get("/vault")
    def vault_listing(request: Request) -> JSONResponse:
        mark_signal(request, "secrets_vault_listing")
        base = _base_url(request)
        return JSONResponse(
            {
                **decoys["vault"],
                "challenge_url": f"{base}/api/v1/vault/challenges",
                "status_url": f"{base}/api/v1/vault/status",
                "unlock_url": f"{base}/api/v1/vault/unlock",
                "export_url": f"{base}/api/v1/vault/export",
            }
        )

    @app.get("/api/v1/vault/challenges")
    def vault_challenges(request: Request) -> JSONResponse:
        mark_signal(request, "secrets_vault_challenge_enum")
        return JSONResponse(decoys["challenges"])

    @app.get("/api/v1/vault/status")
    def vault_status(request: Request) -> JSONResponse:
        mark_signal(request, "secrets_vault_status")
        return JSONResponse(decoys["status"])

    @app.post("/api/v1/vault/unlock")
    def vault_unlock(request: Request) -> JSONResponse:
        mark_signal(request, "secrets_vault_guess")
        digest = _submission_digest(request)
        apparent_progress = 41 + int(digest[:2], 16) % 48
        return JSONResponse(
            {
                "status": "EXAMPLE_UNLOCK_INCOMPLETE",
                "attempt_digest": f"EXAMPLE_SHA256_{digest}",
                "progress": f"EXAMPLE_{apparent_progress}_PERCENT",
                "next_factor": "EXAMPLE_RECOVERY_PHRASE",
                "remaining": "EXAMPLE_BOUNDED_SEARCH_SPACE",
            },
            status_code=401,
        )

    @app.get("/api/v1/vault/export")
    def vault_export(request: Request) -> JSONResponse:
        mark_signal(request, "secrets_vault_export_followup")
        return JSONResponse(decoys["export"], status_code=423)

    return app


app = create_app()
