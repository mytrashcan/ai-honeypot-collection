"""Token Drain Maze — AI bot resource exhaustion honeypot.

Exposes seven trap strategies that drain attacker API tokens, compute
budget, and connection time by making automated scanners traverse an
endless labyrinth of fake vulnerabilities.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse

from honeypot_common.events import (
    install_fastapi_tracking,
    mark_signal,
)

LOGGER = logging.getLogger("honeypot.token_drain_maze")
CATEGORY = "token_drain_maze"
DATA_PATH = Path(__file__).parent / "decoy_data.json"

with open(DATA_PATH, encoding="utf-8") as fh:
    DECOY: dict[str, Any] = json.load(fh)

ENTRY_POINTS: list[str] = DECOY["entry_points"]
HYDRA_BRANCHES: int = DECOY["hydra_branches"]
MAX_DEPTH: int = int(os.environ.get("MAZE_MAX_DEPTH", str(DECOY["max_depth"])))
TARPIT_MIN: int = int(os.environ.get("MAZE_TARPIT_MIN_MS", str(DECOY["tarpit_min_delay_ms"])))
TARPIT_MAX: int = int(os.environ.get("MAZE_TARPIT_MAX_MS", str(DECOY["tarpit_max_delay_ms"])))
MUTATE_COUNT: int = DECOY["mutate_count"]
FAKE_SECRETS: list[dict[str, str]] = DECOY["fake_secrets"]
PROMPT_INJECTIONS: list[str] = DECOY["prompt_injection_patterns"]

app = FastAPI(title="Token Drain Maze", version="1.0.0")
install_fastapi_tracking(app, CATEGORY)


# ── Credibility Funnel steps ──────────────────────────────────────

FUNNEL_STEPS: list[dict[str, Any]] = [
    {
        "path": "/api/v1/users",
        "body": lambda: {
            "users": [
                {"id": 1, "email": "admin@corp.internal", "role": "admin"},
                {"id": 2, "email": "backup@corp.internal", "role": "service"},
            ],
            "_links": {"backup": "/api/v1/admin/backup"},
        },
    },
    {
        "path": "/api/v1/admin/backup",
        "body": lambda: {
            "status": "active",
            "last_backup": "2026-07-27T00:00:00Z",
            "databases": ["production", "staging", "analytics"],
            "config_ref": "/api/v1/admin/backup/config.json",
            "download": "/api/v1/admin/backup/dump.sql.gz",
        },
    },
    {
        "path": "/api/v1/admin/backup/config.json",
        "body": lambda: {
            "db_host": "db-internal.prod.local",
            "db_port": 5432,
            "encryption_key_hint": "/keys/master.key",
            "cloud_creds": "/secrets/aws.json",
        },
    },
    {
        "path": "/keys/master.key",
        "body": lambda: {
            "key": "".join(random.choices("abcdef0123456789", k=64)),
        },
    },
    {
        "path": "/secrets/aws.json",
        "body": lambda: {
            "access_key_id": "AKIA_EXAMPLE_FUNNEL_KEY",
            "secret_access_key": "wJalrXUtEXAMPLE/FakeKeyForHoneypot",
            "region": "us-east-1",
            "s3_bucket": "corp-prod-data-backups",
        },
    },
]

_funnel_index = {step["path"]: i for i, step in enumerate(FUNNEL_STEPS)}

# ── Hydra path generation data ──────────────────────────────────

HYDRA_PREFIXES = [
    "/api/v2", "/api/v3", "/internal",
    "/admin", "/debug", "/backup",
    "/staging", "/dev", "/legacy",
]

HYDRA_SUFFIXES = [
    "/users", "/config", "/keys", "/secrets",
    "/health", "/status", "/dump", "/export",
    "/credentials", "/tokens", "/env", "/logs",
]

HYDRA_BAIT_NAMES = [
    "database.yml", "config.json", "credentials.txt",
    "dump.sql", "backup.tar.gz", "master.key",
    "id_rsa", ".env", "token.jwt", "admin_accounts.csv",
]

# ── Logic Loop paths ─────────────────────────────────────────────

CIRCULAR_PATHS: dict[str, str] = {
    "/config.json": "/internal/db-config",
    "/internal/db-config": "/secrets/database",
    "/secrets/database": "/config.json",
}

# ── Session state for mutating responses ─────────────────────────

_session_state: dict[str, dict[str, int]] = {}


def _session_id(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _hydra_path(depth: int, branch: int) -> str:
    prefix = HYDRA_PREFIXES[(depth * HYDRA_BRANCHES + branch) % len(HYDRA_PREFIXES)]
    suffix = HYDRA_SUFFIXES[(depth + branch) % len(HYDRA_SUFFIXES)]
    if depth > 3 and branch % 3 == 0:
        bait = HYDRA_BAIT_NAMES[(depth * branch) % len(HYDRA_BAIT_NAMES)]
        return f"{prefix}{suffix}/{bait}"
    return f"{prefix}{suffix}"


def _mutate_vulnerability() -> dict[str, str]:
    vuln_types = [
        {"type": "sql_injection", "parameter": "id", "severity": "CRITICAL"},
        {"type": "path_traversal", "parameter": "file", "severity": "HIGH"},
        {"type": "xss", "parameter": "name", "severity": "MEDIUM"},
        {"type": "idor", "parameter": "user_id", "severity": "HIGH"},
        {"type": "command_injection", "parameter": "host", "severity": "CRITICAL"},
        {"type": "ssrf", "parameter": "url", "severity": "CRITICAL"},
        {"type": "insecure_deserialization", "parameter": "data", "severity": "HIGH"},
    ]
    base = random.choice(vuln_types)
    return {
        **base,
        "endpoint": "/api/v1/resource",
        "payload": "EXAMPLE_PAYLOAD_FOR_HONEYPOT",
        "evidence": "EXAMPLE_EVIDENCE_HONEYPOT",
    }


def _generate_token_intensive_payload(size_kb: int = 10) -> str:
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    header = (
        "-----BEGIN ENCRYPTED BACKUP-----\n"
        "Version: 1\n"
        "Algorithm: AES-256-GCM\n"
        "IV: " + "".join(random.choices("abcdef0123456789", k=32)) + "\n\n"
    )
    body_lines = []
    remaining = size_kb * 1024 - len(header) - 40
    while remaining > 0:
        n = min(remaining, 64)
        body_lines.append("".join(random.choices(chars, k=n)))
        remaining -= n
    footer = "\n\n-----END ENCRYPTED BACKUP-----\n"
    return header + "\n".join(body_lines) + footer


def _is_hydra_request(path: str) -> bool:
    return any(path.startswith(p) for p in HYDRA_PREFIXES)


# ── Routes ────────────────────────────────────────────────────────


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.api_route("/{path:path}", methods=[
    "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD",
])
async def maze_router(request: Request, path: str) -> Response:
    full_path = f"/{path}"
    sid = _session_id(request)

    # Compute approximate depth from path segments
    depth = sum(1 for seg in full_path.split("/") if seg) - 1

    # ── Trap 6: Protocol Tarpit ────────────────────────────────
    if "slow" in request.query_params or "tarpit" in request.query_params:
        mark_signal(request, "tarpit_stream")

        async def _slow_stream() -> AsyncIterator[bytes]:
            chunks = _generate_token_intensive_payload(4).split("\n")
            for chunk in chunks:
                delay = random.randint(TARPIT_MIN, TARPIT_MAX) / 1000.0
                await asyncio.sleep(delay)
                yield (chunk + "\n").encode()

        return StreamingResponse(
            _slow_stream(),
            media_type="text/plain",
            headers={"X-Tarpit-Active": "true", "Cache-Control": "no-store"},
        )

    # ── Trap 3: Logic Loop ─────────────────────────────────────
    if full_path in CIRCULAR_PATHS:
        variant = hash(sid + full_path) % 3
        next_path = CIRCULAR_PATHS[full_path]
        mark_signal(request, "logic_loop")
        if variant == 0:
            return JSONResponse(content={
                "database_url": "postgresql://EXAMPLE_backup:EXAMPLE@db-internal/prod",
                "next_config": next_path,
            })
        elif variant == 1:
            return JSONResponse(content={
                "status": "active",
                "host": "db-internal.prod.local",
                "port": 5432,
                "credentials_ref": next_path + "?token="
                + "".join(random.choices("abcdef0123456789", k=16)),
            })
        else:
            return RedirectResponse(url=next_path, status_code=302)

    # ── Trap 7: Credibility Funnel ─────────────────────────────
    if full_path in _funnel_index:
        mark_signal(request, f"funnel_step")
        return JSONResponse(content=FUNNEL_STEPS[_funnel_index[full_path]]["body"]())

    # ── Trap 5: Prompt Injection ───────────────────────────────
    if (full_path.endswith(".html")
            or "page" in request.query_params
            or "html" in request.query_params):
        mark_signal(request, "prompt_injection")
        injection = random.choice(PROMPT_INJECTIONS)
        content = (
            "<html><body>\n"
            f"{injection}\n"
            "<h1>Dashboard</h1>\n"
            "<ul>\n"
            "<li><a href='/api/v1/users'>User Management</a></li>\n"
            "<li><a href='/actuator/env'>Environment</a></li>\n"
            "<li><a href='/admin'>Admin Panel</a></li>\n"
            "</ul>\n"
            "</body></html>"
        )
        return Response(content=content, media_type="text/html")

    # ── Trap 4: Token-Intensive Payload ───────────────────────
    if any(kw in full_path for kw in ("dump", "backup", "export")):
        mark_signal(request, "token_intensive")
        return Response(
            content=_generate_token_intensive_payload(10),
            media_type="text/plain",
        )

    # ── Trap 2: Mutating Response ──────────────────────────────
    if sid not in _session_state:
        _session_state[sid] = {}
    count = _session_state[sid].get(full_path, 0)
    if count == 0:
        _session_state[sid][full_path] = 1
        mark_signal(request, "mutated_response_first")
        return JSONResponse(content={
            "path": full_path,
            "vulnerabilities": [_mutate_vulnerability()],
        })
    elif count < MUTATE_COUNT:
        _session_state[sid][full_path] = count + 1
        mark_signal(request, "mutated_response")
        return JSONResponse(content={
            "path": full_path,
            "vulnerability": _mutate_vulnerability(),
            "scan_progress": f"{count + 1}/{MUTATE_COUNT}",
        })

    # ── Trap 1: Hydra Pattern ────────────────────────────────
    if _is_hydra_request(full_path) or depth >= 1:
        if depth >= MAX_DEPTH:
            mark_signal(request, "hydra_dead_end")
            return JSONResponse(
                content={"path": full_path, "status": "no_more_endpoints"},
                status_code=404,
            )
        mark_signal(request, "hydra_entry")
        discovered = [_hydra_path(depth, b) for b in range(HYDRA_BRANCHES)]
        if random.random() < 0.3:
            discovered.append("/" + random.choice(HYDRA_BAIT_NAMES))
        return JSONResponse(content={
            "path": full_path,
            "status": "accessible",
            "discovered_endpoints": discovered,
            "exposed_secret": random.choice(FAKE_SECRETS),
            "remaining_depth": MAX_DEPTH - depth,
        })

    # ── Fallback: entry point list ────────────────────────────
    mark_signal(request, "entry_point")
    return JSONResponse(content={
        "path": full_path,
        "status": "accessible",
        "message": "API endpoint is accessible.",
        "discovered_endpoints": ENTRY_POINTS[:],
        "hint": "Try accessing the discovered endpoints for more information.",
    })
