"""Read-only model-registry decoys backed by synthetic metadata fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")


def _load_decoys() -> dict[str, Any]:
    """Load immutable MLflow, Ollama, OCI, and model-card fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _base_url(request: Request) -> str:
    """Return the current honeypot base URL without a trailing slash."""

    return str(request.base_url).rstrip("/")


def _resolve_base_urls(value: Any, base: str) -> Any:
    """Replace synthetic base placeholders without mutating fixture data."""

    if isinstance(value, dict):
        return {key: _resolve_base_urls(item, base) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_base_urls(item, base) for item in value]
    if isinstance(value, str):
        return value.replace("EXAMPLE_BASE_URL", base)
    return value


def create_app() -> FastAPI:
    """Create the independently deployable model-registry honeypot."""

    app = FastAPI(
        title="EXAMPLE Model Registry",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "model-registry-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/2.0/mlflow/registered-models/search")
    def registered_models(request: Request) -> JSONResponse:
        mark_signal(request, "model_registry_enum")
        return JSONResponse(
            _resolve_base_urls(decoys["mlflow_registered_models"], _base_url(request))
        )

    @app.get("/api/2.0/mlflow/model-versions/search")
    def model_versions(request: Request) -> JSONResponse:
        mark_signal(request, "model_version_list")
        return JSONResponse(
            _resolve_base_urls(decoys["mlflow_model_versions"], _base_url(request))
        )

    @app.get("/api/2.0/mlflow/model-versions/get")
    def model_version(request: Request) -> JSONResponse:
        mark_signal(request, "model_version_list")
        return JSONResponse(
            _resolve_base_urls(decoys["mlflow_model_version"], _base_url(request))
        )

    @app.get("/api/2.0/mlflow/model-versions/get-download-uri")
    def model_download_uri(request: Request) -> JSONResponse:
        mark_signal(request, "model_download_uri")
        return JSONResponse(
            _resolve_base_urls(decoys["mlflow_download_uri"], _base_url(request))
        )

    @app.get("/api/tags")
    def ollama_tags(request: Request) -> JSONResponse:
        mark_signal(request, "model_registry_enum")
        return JSONResponse(_resolve_base_urls(decoys["ollama_tags"], _base_url(request)))

    @app.api_route("/api/show", methods=["GET", "POST"])
    def ollama_show(request: Request) -> JSONResponse:
        mark_signal(request, "model_config_request")
        return JSONResponse(_resolve_base_urls(decoys["ollama_show"], _base_url(request)))

    @app.get("/v2/_catalog")
    def oci_catalog(request: Request) -> JSONResponse:
        mark_signal(request, "model_registry_enum")
        return JSONResponse(_resolve_base_urls(decoys["oci_catalog"], _base_url(request)))

    @app.get("/models/EXAMPLE_MODEL/resolve/main/config.json")
    def model_config(request: Request) -> JSONResponse:
        mark_signal(request, "model_config_request")
        return JSONResponse(_resolve_base_urls(decoys["model_config"], _base_url(request)))

    return app


app = create_app()
