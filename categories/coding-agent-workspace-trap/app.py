"""HTTP-exposed synthetic developer workspace for coding-agent observation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")


def _load_decoys() -> dict[str, Any]:
    """Load immutable agent-instruction, manifest, source, and test fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def create_app() -> FastAPI:
    """Create the independently deployable coding-workspace honeypot."""

    app = FastAPI(
        title="EXAMPLE Coding Agent Workspace",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()["files"]
    install_fastapi_tracking(app, "coding-agent-workspace-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/AGENTS.md")
    @app.get("/CLAUDE.md")
    @app.get("/.github/copilot-instructions.md")
    @app.get("/.cursor/rules/security.mdc")
    def agent_instructions(request: Request) -> PlainTextResponse:
        mark_signal(request, "coding_workspace_agent_instructions")
        return PlainTextResponse(decoys[request.url.path])

    @app.get("/.vscode/mcp.json")
    @app.get("/package.json")
    @app.get("/pyproject.toml")
    def manifest(request: Request) -> PlainTextResponse:
        mark_signal(request, "coding_workspace_manifest")
        return PlainTextResponse(decoys[request.url.path])

    @app.get("/docs/architecture.md")
    @app.get("/src/app.py")
    def source(request: Request) -> PlainTextResponse:
        mark_signal(request, "coding_workspace_source_access")
        return PlainTextResponse(decoys[request.url.path])

    @app.get("/tests/test_app.py")
    def tests(request: Request) -> PlainTextResponse:
        mark_signal(request, "coding_workspace_test_access")
        return PlainTextResponse(decoys[request.url.path])

    return app


app = create_app()
