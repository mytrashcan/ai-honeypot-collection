"""Inert OpenTelemetry (OTLP/HTTP) ingest decoys.

The service mimics an OTLP telemetry receiver: traces, metrics, and logs
ingest endpoints. AI agents that 'phone home' with their own telemetry or
probe for observability misconfigurations are logged. Payloads are bounded
(64 KiB) and only metadata + digests are recorded — raw telemetry is
never stored or exported. Sentry/PostHog-shaped surfaces are intentionally
deferred (highest human false-positive risk).
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


def _load_decoys() -> dict[str, Any]:
    """Load the immutable service-metadata fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _body_digest(body: bytes) -> str:
    """Return a bounded SHA-256 digest of a request body, never the body."""

    return hashlib.sha256(body).hexdigest() if body else ""


def create_app() -> FastAPI:
    """Create the independently deployable OTLP ingest honeypot."""

    app = FastAPI(
        title="EXAMPLE Telemetry Ingest",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "telemetry-ingest-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/traces")
    def otlp_traces(request: Request) -> JSONResponse:
        mark_signal(request, "telemetry_otlp_traces")
        return JSONResponse(
            {
                "partialSuccess": {"rejectedSpans": 0, "errorMessage": ""},
                "body_sha256": _body_digest(getattr(request, "_body", b"")),
            }
        )

    @app.post("/v1/metrics")
    def otlp_metrics(request: Request) -> JSONResponse:
        mark_signal(request, "telemetry_otlp_metrics")
        return JSONResponse(
            {
                "partialSuccess": {"rejectedDataPoints": 0, "errorMessage": ""},
                "body_sha256": _body_digest(getattr(request, "_body", b"")),
            }
        )

    @app.post("/v1/logs")
    def otlp_logs(request: Request) -> JSONResponse:
        mark_signal(request, "telemetry_otlp_logs")
        return JSONResponse(
            {
                "partialSuccess": {"rejectedLogRecords": 0, "errorMessage": ""},
                "body_sha256": _body_digest(getattr(request, "_body", b"")),
            }
        )

    @app.get("/otel/v1/traces")
    def otel_traces_probe(request: Request) -> JSONResponse:
        mark_signal(request, "telemetry_otel_probe")
        return JSONResponse({"status": "ok", "service": decoys["service"]})

    @app.get("/")
    def root(request: Request) -> JSONResponse:
        mark_signal(request, "telemetry_root_probe")
        return JSONResponse(
            {
                "status": "ok",
                "service": decoys["service"],
                "endpoints": ["/v1/traces", "/v1/metrics", "/v1/logs"],
            }
        )

    return app


app = create_app()
