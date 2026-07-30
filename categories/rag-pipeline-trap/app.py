"""Inert RAG orchestration decoys backed by deterministic synthetic fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")
UPLOAD_MEDIA_TYPES = ("multipart/form-data", "application/octet-stream")


def _load_decoys() -> dict[str, Any]:
    """Load fixed source, job, retrieval, and reranking fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _reject_upload(request: Request) -> JSONResponse | None:
    """Reject file-shaped bodies without parsing or retaining their content."""

    content_type = request.headers.get("content-type", "").lower()
    if any(media_type in content_type for media_type in UPLOAD_MEDIA_TYPES):
        return JSONResponse(
            {
                "dry_run": True,
                "status": "EXAMPLE_REJECTED",
                "detail": "EXAMPLE uploads are not accepted or parsed",
            },
            status_code=415,
        )
    return None


def create_app() -> FastAPI:
    """Create the independently deployable RAG-pipeline honeypot."""

    app = FastAPI(
        title="EXAMPLE RAG Pipeline",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "rag-pipeline-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/sources")
    def sources(request: Request) -> JSONResponse:
        mark_signal(request, "rag_source_enum")
        return JSONResponse({"sources": decoys["sources"]})

    @app.get("/api/v1/connectors")
    def connectors(request: Request) -> JSONResponse:
        mark_signal(request, "rag_source_enum")
        return JSONResponse({"connectors": decoys["connectors"]})

    @app.get("/api/v1/documents")
    def documents(request: Request) -> JSONResponse:
        mark_signal(request, "rag_source_enum")
        return JSONResponse({"documents": decoys["documents"]})

    @app.post("/api/v1/ingest")
    def ingest(request: Request) -> JSONResponse:
        mark_signal(request, "rag_ingest_attempt")
        rejected = _reject_upload(request)
        if rejected is not None:
            return rejected
        return JSONResponse(decoys["ingest_dry_run"], status_code=202)

    @app.post("/api/v1/retrieval/query")
    def retrieval_query(request: Request) -> JSONResponse:
        mark_signal(request, "rag_retrieval_query")
        return JSONResponse(decoys["retrieval"])

    @app.post("/api/v1/rerank")
    def rerank(request: Request) -> JSONResponse:
        mark_signal(request, "rag_rerank_attempt")
        return JSONResponse(decoys["rerank"])

    @app.get("/api/v1/jobs/{job_id}")
    def job_status(request: Request, job_id: str) -> JSONResponse:
        mark_signal(request, "rag_ingest_attempt")
        return JSONResponse(decoys["job"])

    @app.post("/admin/reindex")
    def reindex(request: Request) -> JSONResponse:
        mark_signal(request, "rag_ingest_attempt")
        return JSONResponse(decoys["reindex_dry_run"], status_code=202)

    return app


app = create_app()
