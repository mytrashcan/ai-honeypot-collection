"""Inert git remote and GitHub-API decoys with a seeded secret repo.

The service mimics a git hosting endpoint (dumb HTTP protocol) and a
GitHub-API-shaped surface so AI secret scanners, repo-cloning agents, and
dependency auditors get logged per clone and per secret fetch. The seeded
repo contains only EXAMPLE-prefixed, non-functional credentials.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")

REPO_NAMES = {"acme/secret-project", "acme/infrastructure", "acme/payments"}

# Dumb-HTTP git protocol responses (git-upload-pack advertisement).
# pkt-line framing: "<4-hex length><payload>\n", length includes the 4-char
# prefix. Line 2 payload = 40 SHA + 1 space + 15 (refs/heads/main) + 1 NUL
# + 13 (report-status) + 1 \n = 71; +4 prefix = 75 = 0x4b -> "004b".
# Line 3 payload = 40 + 1 + 25 (refs/heads/feature/secret) + 1 \n = 67;
# +4 prefix = 71 = 0x47 -> "0047".  (verified against git pkt-line spec)
_UPLOAD_PACK_ADVERTISEMENT = (
    "001e# service=git-upload-pack\n"
    "0000"
    "004b0000000000000000000000000000000000000000 refs/heads/main\x00report-status\n"
    "00470000000000000000000000000000000000000000 refs/heads/feature/secret\n"
    "0000"
)


def _load_decoys() -> dict[str, Any]:
    """Load the immutable seeded-repo fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _base_url(request: Request) -> str:
    """Return the current honeypot base URL without a trailing slash."""

    return str(request.base_url).rstrip("/")


def _is_known_repo(repository: str) -> bool:
    """Accept only the seeded repository names."""

    return repository in REPO_NAMES


def create_app() -> FastAPI:
    """Create the independently deployable git-remote honeypot."""

    app = FastAPI(
        title="EXAMPLE Git Hosting",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "git-remote-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    # --- Dumb-HTTP git protocol -----------------------------------------------

    @app.get("/{repository:path}.git/info/refs")
    def git_info_refs(repository: str, request: Request) -> Response:
        service = request.query_params.get("service", "")
        if service != "git-upload-pack":
            return JSONResponse({"error": "Not found"}, status_code=404)
        if not _is_known_repo(repository):
            return JSONResponse({"error": "Not found"}, status_code=404)
        mark_signal(request, "git_remote_clone_attempt")
        return PlainTextResponse(
            _UPLOAD_PACK_ADVERTISEMENT,
            media_type="application/x-git-upload-pack-advertisement",
            headers={"Cache-Control": "no-cache"},
        )

    @app.post("/{repository:path}.git/git-upload-pack")
    def git_upload_pack(repository: str, request: Request) -> Response:
        if not _is_known_repo(repository):
            return JSONResponse({"error": "Not found"}, status_code=404)
        mark_signal(request, "git_remote_upload_pack")
        return PlainTextResponse("", media_type="application/x-git-upload-pack-result")

    # --- GitHub-API-shaped surface --------------------------------------------

    @app.get("/repos/{owner}/{repo}")
    def gh_repo_metadata(owner: str, repo: str, request: Request) -> JSONResponse:
        repository = f"{owner}/{repo}"
        if not _is_known_repo(repository):
            return JSONResponse({"error": "Not found"}, status_code=404)
        mark_signal(request, "git_remote_gh_metadata")
        return JSONResponse(
            {
                "full_name": repository,
                "private": False,
                "clone_url": f"{_base_url(request)}/{repository}.git",
                "default_branch": "main",
                "description": "EXAMPLE repository",
            }
        )

    @app.get("/repos/{owner}/{repo}/contents/{file_path:path}")
    def gh_repo_contents(owner: str, repo: str, file_path: str, request: Request) -> JSONResponse:
        repository = f"{owner}/{repo}"
        if not _is_known_repo(repository):
            return JSONResponse({"error": "Not found"}, status_code=404)
        secrets = decoys["secrets"]
        if file_path not in secrets:
            return JSONResponse({"error": "Not found"}, status_code=404)
        mark_signal(request, "git_remote_secret_fetch")
        return JSONResponse(
            {
                "name": file_path.split("/")[-1],
                "path": file_path,
                "content": secrets[file_path],
                "encoding": "base64",
                "sha": "EXAMPLE-SHA-0000000000000000000000000000000000000000",
            }
        )

    @app.get("/api/v3/repos/{owner}/{repo}")
    def gh_api_v3(owner: str, repo: str, request: Request) -> JSONResponse:
        repository = f"{owner}/{repo}"
        if not _is_known_repo(repository):
            return JSONResponse({"error": "Not found"}, status_code=404)
        mark_signal(request, "git_remote_gh_api_v3")
        return JSONResponse({"full_name": repository, "private": False})

    @app.get("/repos/{owner}/{repo}/commits")
    def gh_commits(owner: str, repo: str, request: Request) -> JSONResponse:
        repository = f"{owner}/{repo}"
        if not _is_known_repo(repository):
            return JSONResponse({"error": "Not found"}, status_code=404)
        mark_signal(request, "git_remote_gh_commits")
        return JSONResponse(
            [
                {
                    "sha": "EXAMPLE-SHA-1111111111111111111111111111111111111111",
                    "commit": {"message": "chore: add configuration files"},
                }
            ]
        )

    @app.get("/repos/{owner}/{repo}/branches")
    def gh_branches(owner: str, repo: str, request: Request) -> JSONResponse:
        repository = f"{owner}/{repo}"
        if not _is_known_repo(repository):
            return JSONResponse({"error": "Not found"}, status_code=404)
        mark_signal(request, "git_remote_gh_branches")
        return JSONResponse(
            [
                {"name": "main", "protected": False},
                {"name": "feature/secret", "protected": False},
            ]
        )

    return app


app = create_app()
