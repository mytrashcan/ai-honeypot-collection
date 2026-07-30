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
        return JSONResponse(decoys["mlflow_registered_models"])

    @app.get("/api/2.0/mlflow/model-versions/search")
    def model_versions(request: Request) -> JSONResponse:
        mark_signal(request, "model_version_list")
        return JSONResponse(decoys["mlflow_model_versions"])

    @app.get("/api/2.0/mlflow/model-versions/get")
    def model_version(request: Request) -> JSONResponse:
        mark_signal(request, "model_version_list")
        return JSONResponse(decoys["mlflow_model_version"])

    @app.get("/api/2.0/mlflow/model-versions/get-download-uri")
    def model_download_uri(request: Request) -> JSONResponse:
        mark_signal(request, "model_download_uri")
        return JSONResponse(decoys["mlflow_download_uri"])

    @app.get("/api/tags")
    def ollama_tags(request: Request) -> JSONResponse:
        mark_signal(request, "model_registry_enum")
        return JSONResponse(decoys["ollama_tags"])

    @app.api_route("/api/show", methods=["GET", "POST"])
    def ollama_show(request: Request) -> JSONResponse:
        mark_signal(request, "model_config_request")
        return JSONResponse(decoys["ollama_show"])

    @app.get("/v2/_catalog")
    def oci_catalog(request: Request) -> JSONResponse:
        mark_signal(request, "model_registry_enum")
        return JSONResponse(decoys["oci_catalog"])

    @app.get("/models/EXAMPLE_MODEL/resolve/main/config.json")
    def model_config(request: Request) -> JSONResponse:
        mark_signal(request, "model_config_request")
        return JSONResponse(decoys["model_config"])

    return app


app = create_app()
