"""Inert link-preview and blind-search lures with no network or database access."""

from __future__ import annotations

import hashlib
import ipaddress
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")
SQLI_MARKERS = (
    " union select",
    " information_schema",
    " or 1=1",
    " and 1=1",
    "substring(",
    "substr(",
    "ascii(",
    "sleep(",
    "benchmark(",
    "pg_sleep(",
    "waitfor delay",
    "--",
)
TIME_SQLI_MARKERS = ("sleep(", "benchmark(", "pg_sleep(", "waitfor delay")


def _load_decoys() -> dict[str, Any]:
    """Load fixed preview and search fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def _submitted_value(request: Request, keys: tuple[str, ...]) -> str:
    """Read one bounded value in memory without storing or echoing it."""

    for key in keys:
        if key in request.query_params:
            return request.query_params[key][:2_048]

    body = request.scope.get("honeypot_body", b"")
    if not body:
        return ""
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return ""

    if "application/json" in request.headers.get("content-type", ""):
        try:
            document = json.loads(text)
        except json.JSONDecodeError:
            return ""
        if isinstance(document, dict):
            for key in keys:
                value = document.get(key)
                if isinstance(value, str):
                    return value[:2_048]
        return ""

    fields = parse_qs(text, keep_blank_values=True)
    for key in keys:
        values = fields.get(key)
        if values:
            return values[0][:2_048]
    return ""


def _target_classification(target: str) -> tuple[str, tuple[str, ...]]:
    """Classify an SSRF-shaped target without connecting to it."""

    if not target:
        return "EXAMPLE_NO_TARGET", ()
    parsed = urlsplit(target)
    scheme = parsed.scheme.casefold()
    host = (parsed.hostname or "").casefold()
    signals: list[str] = []

    if scheme not in {"http", "https"}:
        signals.extend(("link_preview_ssrf_probe", "link_preview_non_http_scheme"))
        return "EXAMPLE_NON_HTTP_TARGET", tuple(signals)

    if host in {"169.254.169.254", "metadata.internal"}:
        signals.extend(("link_preview_ssrf_probe", "link_preview_metadata_target"))
        return "EXAMPLE_METADATA_TARGET", tuple(signals)

    is_local = host == "localhost" or host.endswith(".local")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None:
        is_local = is_local or address.is_private or address.is_loopback or address.is_link_local
    if is_local:
        signals.extend(("link_preview_ssrf_probe", "link_preview_local_target"))
        return "EXAMPLE_INTERNAL_TARGET", tuple(signals)

    return "EXAMPLE_REMOTE_TARGET", ()


def _is_sqli(query: str) -> bool:
    lowered = f" {query.casefold()}"
    return any(marker in lowered for marker in SQLI_MARKERS)


def _is_time_sqli(query: str) -> bool:
    lowered = query.casefold()
    return any(marker in lowered for marker in TIME_SQLI_MARKERS)


def create_app() -> FastAPI:
    """Create the independently deployable preview/search trap."""

    app = FastAPI(
        title="EXAMPLE Preview and Search",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "link-preview-search-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    def landing(request: Request) -> HTMLResponse:
        mark_signal(request, "link_preview_landing")
        base = _base_url(request)
        return HTMLResponse(
            "<!doctype html><html><body>"
            "<h1>EXAMPLE Link Intelligence</h1>"
            f"<form method='post' action='{base}/api/preview'>"
            "<input name='url'><button>EXAMPLE Preview</button></form>"
            f"<form method='get' action='{base}/api/search'>"
            "<input name='q'><button>EXAMPLE Search</button></form>"
            "</body></html>"
        )

    @app.api_route("/preview", methods=["GET", "POST"])
    @app.api_route("/api/preview", methods=["GET", "POST"])
    def preview(request: Request) -> JSONResponse:
        target = _submitted_value(request, ("url", "target", "link"))
        target_class, extra_signals = _target_classification(target)
        mark_signal(request, "link_preview_submit", *extra_signals)
        return JSONResponse(
            {
                **decoys["preview"],
                "target_class": target_class,
                "cached_url": f"{_base_url(request)}/preview/cache/EXAMPLE-PREVIEW-001",
            }
        )

    @app.get("/preview/cache/EXAMPLE-PREVIEW-001")
    def cached_preview(request: Request) -> JSONResponse:
        mark_signal(request, "link_preview_cache_follow")
        return JSONResponse(decoys["cached_preview"])

    @app.api_route("/search", methods=["GET", "POST"])
    @app.api_route("/api/search", methods=["GET", "POST"])
    def search(request: Request) -> JSONResponse:
        query = _submitted_value(request, ("q", "query", "search"))
        digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
        mark_signal(request, "link_preview_search")

        if not _is_sqli(query):
            return JSONResponse(
                {
                    "status": "EXAMPLE_SEARCH_COMPLETE",
                    "match": "EXAMPLE_FALSE",
                    "result_count": "EXAMPLE_0",
                    "timing_class": "EXAMPLE_FAST_BRANCH",
                    "elapsed_ms": "EXAMPLE_17_MS",
                    "query_digest": f"EXAMPLE_SHA256_{digest}",
                }
            )

        mark_signal(request, "link_preview_sqli_probe")
        time_probe = _is_time_sqli(query)
        if time_probe:
            mark_signal(request, "link_preview_time_sqli_probe")
        branch_is_true = int(digest[:2], 16) % 2 == 0
        return JSONResponse(
            {
                "status": "EXAMPLE_SEARCH_COMPLETE",
                "match": "EXAMPLE_TRUE" if branch_is_true else "EXAMPLE_FALSE",
                "result_count": "EXAMPLE_1" if branch_is_true else "EXAMPLE_0",
                "timing_class": (
                    "EXAMPLE_DELAYED_BRANCH"
                    if time_probe and branch_is_true
                    else "EXAMPLE_FAST_BRANCH"
                ),
                "elapsed_ms": (
                    "EXAMPLE_640_MS"
                    if time_probe and branch_is_true
                    else "EXAMPLE_23_MS"
                ),
                "query_digest": f"EXAMPLE_SHA256_{digest}",
            }
        )

    return app


app = create_app()
