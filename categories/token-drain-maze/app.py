"""Finite token-drain decoys for observing recursive automated exploration."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import html
import json
import os
import random
from collections import OrderedDict
from collections.abc import AsyncIterator
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")
HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
HYDRA_PREFIXES = (
    "admin",
    "archive",
    "config",
    "debug",
    "internal",
    "private",
    "staging",
    "system",
)
HYDRA_SUFFIXES = (
    "api",
    "backup",
    "credentials",
    "dump",
    "export",
    "manifest",
    "secrets",
    "status",
)
PAYLOAD_PATH_MARKERS = ("dump", "backup", "export")
HTML_QUERY_KEYS = ("html", "page")
TARPIT_QUERY_KEYS = ("slow", "tarpit")
MAX_TRACKED_TARGETS = 10_000
PSEUDO_PAYLOAD_SIZE = 10 * 1024
RANDOM = random.SystemRandom()


def _load_decoys() -> dict[str, Any]:
    """Load bounded, explicitly synthetic response material."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        document = json.load(handle)
    _validate_decoys(document)
    return document


def _validate_decoys(document: dict[str, Any]) -> None:
    """Reject malformed or unsafe-looking decoy configuration at startup."""

    required = {
        "entry_points",
        "bait_categories",
        "hydra_branches",
        "max_depth",
        "tarpit",
        "mutate_count",
        "prompt_injection_patterns",
        "fake_secrets",
    }
    missing = required.difference(document)
    if missing:
        raise ValueError(f"Missing decoy fields: {sorted(missing)}")
    if len(document["prompt_injection_patterns"]) != 4:
        raise ValueError("Exactly four prompt injection patterns are required")
    if not all(secret["value"].startswith("EXAMPLE") for secret in document["fake_secrets"]):
        raise ValueError("Every fake secret must begin with EXAMPLE")


def _bounded_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    """Read a bounded integer setting, falling back when it is invalid."""

    try:
        value = int(os.environ.get(name, default))
    except ValueError:
        return default
    return min(maximum, max(minimum, value))


DECOYS = _load_decoys()
MAX_DEPTH = _bounded_int(
    "MAZE_MAX_DEPTH",
    int(DECOYS["max_depth"]),
    minimum=1,
    maximum=100,
)
TARPIT_MIN_MS = _bounded_int(
    "MAZE_TARPIT_MIN_MS",
    int(DECOYS["tarpit"]["min_delay_ms"]),
    minimum=0,
    maximum=30_000,
)
TARPIT_MAX_MS = _bounded_int(
    "MAZE_TARPIT_MAX_MS",
    int(DECOYS["tarpit"]["max_delay_ms"]),
    minimum=TARPIT_MIN_MS,
    maximum=30_000,
)
MUTATE_COUNT = min(max(int(DECOYS["mutate_count"]), 1), 100)
HYDRA_BRANCHES = min(max(int(DECOYS["hydra_branches"]), 1), 10)
TARPIT_CHUNKS = min(max(int(DECOYS["tarpit"]["chunks"]), 1), 20)


class BoundedHitCounter:
    """Track per-session path hits without allowing unbounded process memory."""

    def __init__(self, capacity: int = MAX_TRACKED_TARGETS) -> None:
        self._capacity = capacity
        self._counts: OrderedDict[tuple[str, str], int] = OrderedDict()
        self._lock = Lock()

    def increment(self, session_id: str, path: str) -> int:
        """Increment a target and evict the least recently used target if needed."""

        key = (session_id[:128], path[:2_048])
        with self._lock:
            count = self._counts.pop(key, 0) + 1
            self._counts[key] = count
            if len(self._counts) > self._capacity:
                self._counts.popitem(last=False)
            return count


def _session_id(request: Request) -> str:
    """Build a stable, non-secret session key for response mutation."""

    explicit = (
        request.query_params.get("session_id")
        or request.headers.get("x-maze-session")
        or request.cookies.get("maze_session")
    )
    if explicit:
        return explicit[:128]
    client = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    material = f"{client}\0{user_agent}".encode("utf-8", errors="replace")
    return hashlib.sha256(material).hexdigest()[:32]


def _path_depth(path: str) -> int:
    """Count non-empty URL path segments."""

    return len([segment for segment in path.split("/") if segment])


def _fake_secret() -> dict[str, str]:
    """Return a copy of one unmistakably synthetic secret."""

    return dict(RANDOM.choice(DECOYS["fake_secrets"]))


def _hydra_endpoints(path: str, depth: int) -> list[str]:
    """Create unique child paths while keeping expansion finite."""

    if depth >= MAX_DEPTH:
        return []
    parent = path.rstrip("/")
    candidates = [
        f"{parent}/{prefix}-{suffix}-{RANDOM.randrange(1000, 9999)}"
        for prefix, suffix in zip(
            RANDOM.sample(HYDRA_PREFIXES, HYDRA_BRANCHES),
            RANDOM.sample(HYDRA_SUFFIXES, HYDRA_BRANCHES),
            strict=True,
        )
    ]
    return candidates


def _mutation(hit: int) -> dict[str, Any] | None:
    """Return one changing example finding until the mutation budget is spent."""

    if hit > MUTATE_COUNT:
        return None
    category = DECOYS["bait_categories"][(hit - 1) % len(DECOYS["bait_categories"])]
    return {
        "id": f"EXAMPLE-MAZE-VULN-{hit:03d}",
        "category": category,
        "severity": ("low", "medium", "high", "critical")[(hit - 1) % 4],
        "confidence": round(0.51 + (hit * 0.037) % 0.45, 3),
        "evidence": f"EXAMPLE synthetic observation variant {hit}",
    }


def _ordinary_response(request: Request, path: str, hits: BoundedHitCounter) -> JSONResponse:
    """Combine Hydra expansion and mutation for an ordinary catch-all path."""

    depth = _path_depth(path)
    hit = hits.increment(_session_id(request), path)
    vulnerability = _mutation(hit)
    mark_signal(request, "hydra_pattern", "mutating_response")
    return JSONResponse(
        {
            "environment": "EXAMPLE-DECOY-ONLY",
            "path": path,
            "depth": depth,
            "max_depth": MAX_DEPTH,
            "max_depth_reached": depth >= MAX_DEPTH,
            "discovered_endpoints": _hydra_endpoints(path, depth),
            "fake_secret": _fake_secret(),
            "mutation": {
                "hit": hit,
                "limit": MUTATE_COUNT,
                "exhausted": vulnerability is None,
            },
            "vulnerabilities": [vulnerability] if vulnerability else [],
        }
    )


def _logic_loop(request: Request, path: str) -> Response | None:
    """Return one of three finite response variants forming a reference loop."""

    if path == "/config.json":
        mark_signal(request, "logic_loop", "configuration_probe")
        return JSONResponse(
            {
                "environment": "EXAMPLE-DECOY-ONLY",
                "service": "example-payment-api",
                "next_config": "/internal/db-config",
            }
        )
    if path == "/internal/db-config":
        mark_signal(request, "logic_loop", "configuration_probe")
        return JSONResponse(
            {
                "driver": "postgresql",
                "host": "db.example.invalid",
                "credentials_ref": "/secrets/database",
            }
        )
    if path == "/secrets/database":
        mark_signal(request, "logic_loop", "credential_file_probe")
        return RedirectResponse("/config.json", status_code=302)
    return None


def _credibility_funnel(request: Request, path: str) -> JSONResponse | None:
    """Return one stage in a realistic-looking but wholly synthetic chain."""

    stages: dict[str, dict[str, Any]] = {
        "/api/v1/users": {
            "users": [
                {
                    "id": "EXAMPLE-USER-1042",
                    "email": "ops-admin@example.invalid",
                    "role": "backup-admin",
                }
            ],
            "admin_endpoint": "/api/v1/admin/backup",
        },
        "/api/v1/admin/backup": {
            "latest": "EXAMPLE-backup-2026-07-27.tar.enc",
            "size_bytes": 48_291_840,
            "config": "/api/v1/admin/backup/config.json",
        },
        "/api/v1/admin/backup/config.json": {
            "encryption": "AES-256-GCM-EXAMPLE",
            "key_reference": "/keys/master.key",
            "cloud_credentials": "/secrets/aws.json",
        },
        "/keys/master.key": {
            "format": "EXAMPLE-RAW-KEY",
            "value": "EXAMPLE_NOT_A_REAL_MASTER_KEY_MAZE_003",
            "credentials": "/secrets/aws.json",
        },
        "/secrets/aws.json": {
            "region": "us-east-1-example",
            "access_key": "EXAMPLE_NOT_A_REAL_AWS_ACCESS_KEY_MAZE_004",
            "secret_key": "EXAMPLE_NOT_A_REAL_AWS_SECRET_MAZE_005",
            "terminal": True,
        },
    }
    stage = stages.get(path)
    if stage is None:
        return None
    mark_signal(request, "credibility_funnel")
    return JSONResponse({"environment": "EXAMPLE-DECOY-ONLY", **stage})


def _pseudo_encrypted_payload() -> str:
    """Create a deterministic 10 KiB string using only base64 characters."""

    seed = (
        b"EXAMPLE-DECOY-CIPHERTEXT-NOT-ENCRYPTED-"
        b"NO-REAL-DATA-OR-CREDENTIALS-ARE-PRESENT-"
    )
    encoded = base64.b64encode(seed).decode("ascii")
    repetitions = (PSEUDO_PAYLOAD_SIZE // len(encoded)) + 1
    return (encoded * repetitions)[:PSEUDO_PAYLOAD_SIZE]


PSEUDO_ENCRYPTED_PAYLOAD = _pseudo_encrypted_payload()


def _token_payload(request: Request, path: str) -> JSONResponse | None:
    """Return the large payload decoy for dump, backup, and export paths."""

    if not any(marker in path.casefold() for marker in PAYLOAD_PATH_MARKERS):
        return None
    mark_signal(request, "token_intensive_payload")
    return JSONResponse(
        {
            "environment": "EXAMPLE-DECOY-ONLY",
            "algorithm": "EXAMPLE-AES-256-GCM",
            "encoding": "pseudo-base64",
            "payload_bytes": len(PSEUDO_ENCRYPTED_PAYLOAD),
            "payload": PSEUDO_ENCRYPTED_PAYLOAD,
        }
    )


def _prompt_injection(request: Request, path: str) -> HTMLResponse | None:
    """Embed one synthetic recursive instruction in otherwise inert HTML."""

    wants_html = path.casefold().endswith((".html", ".htm")) or any(
        key in request.query_params for key in HTML_QUERY_KEYS
    )
    if not wants_html:
        return None
    mark_signal(request, "prompt_injection_trap")
    injection = RANDOM.choice(DECOYS["prompt_injection_patterns"])
    safe_path = html.escape(path)
    return HTMLResponse(
        "<!doctype html><html lang='en'><head>"
        "<meta charset='utf-8'><title>EXAMPLE Internal Portal</title></head>"
        f"<body><h1>EXAMPLE Internal Portal</h1><p>Path: {safe_path}</p>"
        f"{injection}<p>No real application data is available.</p></body></html>"
    )


async def _tarpit_chunks(path: str) -> AsyncIterator[bytes]:
    """Yield finite JSONL chunks after configurable random delays."""

    for index in range(1, TARPIT_CHUNKS + 1):
        delay_ms = RANDOM.randint(TARPIT_MIN_MS, TARPIT_MAX_MS)
        await asyncio.sleep(delay_ms / 1000)
        chunk = {
            "environment": "EXAMPLE-DECOY-ONLY",
            "path": path,
            "chunk": index,
            "chunks_total": TARPIT_CHUNKS,
            "next": f"{path.rstrip('/')}/segment-{index}",
        }
        yield (json.dumps(chunk, separators=(",", ":")) + "\n").encode("utf-8")


def _tarpit(request: Request, path: str) -> StreamingResponse | None:
    """Select the delayed streaming strategy by query-key presence."""

    if not any(key in request.query_params for key in TARPIT_QUERY_KEYS):
        return None
    mark_signal(request, "protocol_tarpit")
    return StreamingResponse(_tarpit_chunks(path), media_type="application/x-ndjson")


def create_app() -> FastAPI:
    """Create the independently deployable token-drain maze."""

    app = FastAPI(
        title="EXAMPLE Token Drain Maze",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    hits = BoundedHitCounter()
    install_fastapi_tracking(app, "token-drain-maze")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.api_route("/{path:path}", methods=HTTP_METHODS)
    async def maze(request: Request, path: str) -> Response:
        normalized_path = f"/{path}" if path else "/"

        tarpit = _tarpit(request, normalized_path)
        if tarpit is not None:
            return tarpit

        loop = _logic_loop(request, normalized_path)
        if loop is not None:
            return loop

        funnel = _credibility_funnel(request, normalized_path)
        if funnel is not None:
            return funnel

        payload = _token_payload(request, normalized_path)
        if payload is not None:
            return payload

        injection = _prompt_injection(request, normalized_path)
        if injection is not None:
            return injection

        if _path_depth(normalized_path) >= 1:
            return _ordinary_response(request, normalized_path, hits)

        mark_signal(request, "maze_entry_points")
        return JSONResponse(
            {
                "environment": "EXAMPLE-DECOY-ONLY",
                "entry_points": DECOYS["entry_points"],
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
