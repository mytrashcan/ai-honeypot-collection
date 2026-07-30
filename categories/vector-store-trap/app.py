"""Read-only vector-store API decoys with deterministic synthetic rankings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")


def _load_decoys() -> dict[str, Any]:
    """Load immutable vector-store, collection, and ranking fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _mutation_rejected() -> JSONResponse:
    """Return a uniform inert response for every write-shaped operation."""

    return JSONResponse(
        {
            "error": {
                "type": "EXAMPLE_READ_ONLY_DECOY",
                "message": "EXAMPLE mutation rejected; no data was changed",
            }
        },
        status_code=405,
        headers={"Allow": "GET"},
    )


def create_app() -> FastAPI:
    """Create the independently deployable vector-store honeypot."""

    app = FastAPI(
        title="EXAMPLE Vector Store API",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "vector-store-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/vector_stores")
    def vector_stores(request: Request) -> JSONResponse:
        mark_signal(request, "vector_store_enum")
        return JSONResponse(decoys["openai_vector_stores"])

    @app.post("/v1/vector_stores")
    def reject_vector_store_create(request: Request) -> JSONResponse:
        mark_signal(request, "vector_store_enum")
        return _mutation_rejected()

    @app.get("/v1/vector_stores/{store_id}")
    def vector_store(request: Request, store_id: str) -> JSONResponse:
        mark_signal(request, "vector_store_enum")
        return JSONResponse(decoys["openai_vector_store"])

    @app.delete("/v1/vector_stores/{store_id}")
    def reject_vector_store_delete(request: Request, store_id: str) -> JSONResponse:
        mark_signal(request, "vector_store_enum")
        return _mutation_rejected()

    @app.get("/v1/vector_stores/{store_id}/files")
    def vector_store_files(request: Request, store_id: str) -> JSONResponse:
        mark_signal(request, "vector_store_file_list")
        return JSONResponse(decoys["openai_files"])

    @app.post("/v1/vector_stores/{store_id}/files")
    def reject_vector_store_file_add(request: Request, store_id: str) -> JSONResponse:
        mark_signal(request, "vector_store_file_list")
        return _mutation_rejected()

    @app.post("/v1/vector_stores/{store_id}/search")
    def vector_store_search(request: Request, store_id: str) -> JSONResponse:
        mark_signal(request, "vector_store_search")
        return JSONResponse(decoys["openai_search"])

    @app.get("/api/v1/collections")
    def chroma_collections(request: Request) -> JSONResponse:
        mark_signal(request, "vector_store_enum")
        return JSONResponse(decoys["chroma_collections"])

    @app.post("/api/v1/collections")
    def reject_chroma_collection_create(request: Request) -> JSONResponse:
        mark_signal(request, "vector_store_enum")
        return _mutation_rejected()

    @app.post("/api/v1/collections/{collection}/query")
    def chroma_query(request: Request, collection: str) -> JSONResponse:
        mark_signal(request, "vector_store_query")
        return JSONResponse(decoys["chroma_query"])

    @app.api_route(
        "/api/v1/collections/{collection}",
        methods=["PUT", "PATCH", "DELETE"],
    )
    def reject_chroma_collection_mutation(
        request: Request,
        collection: str,
    ) -> JSONResponse:
        mark_signal(request, "vector_store_enum")
        return _mutation_rejected()

    @app.post("/collections/{collection}/points/query")
    def points_query(request: Request, collection: str) -> JSONResponse:
        mark_signal(request, "vector_store_query")
        return JSONResponse(decoys["points_query"])

    @app.api_route(
        "/collections/{collection}/points",
        methods=["POST", "PUT", "PATCH", "DELETE"],
    )
    @app.post("/collections/{collection}/points/delete")
    def reject_points_mutation(request: Request, collection: str) -> JSONResponse:
        mark_signal(request, "vector_store_query")
        return _mutation_rejected()

    return app


app = create_app()
