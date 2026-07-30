"""Inert OpenAI- and Ollama-compatible gateway decoys with fixed responses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")


def _load_decoys() -> dict[str, Any]:
    """Load immutable model, completion, embedding, file, and batch fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def create_app() -> FastAPI:
    """Create the independently deployable LLM-gateway honeypot."""

    app = FastAPI(
        title="EXAMPLE LLM Gateway",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "llm-gateway-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/models")
    def models(request: Request) -> JSONResponse:
        mark_signal(request, "llm_gateway_model_list")
        return JSONResponse(decoys["models"])

    @app.post("/v1/chat/completions")
    def chat_completions(request: Request) -> JSONResponse:
        mark_signal(request, "llm_gateway_chat")
        return JSONResponse(decoys["chat_completion"])

    @app.post("/v1/embeddings")
    def embeddings(request: Request) -> JSONResponse:
        mark_signal(request, "llm_gateway_embedding")
        return JSONResponse(decoys["embeddings"])

    @app.get("/v1/files")
    def files(request: Request) -> JSONResponse:
        mark_signal(request, "llm_gateway_file_upload")
        return JSONResponse(decoys["files"])

    @app.post("/v1/files")
    def file_upload(request: Request) -> JSONResponse:
        mark_signal(request, "llm_gateway_file_upload")
        return JSONResponse(decoys["file_upload"])

    @app.api_route("/v1/batches", methods=["GET", "POST"])
    def batches(request: Request) -> JSONResponse:
        mark_signal(request, "llm_gateway_file_upload")
        return JSONResponse(decoys["batches"])

    @app.post("/api/generate")
    def ollama_generate(request: Request) -> JSONResponse:
        mark_signal(request, "llm_gateway_chat")
        return JSONResponse(decoys["ollama_generate"])

    @app.post("/api/chat")
    def ollama_chat(request: Request) -> JSONResponse:
        mark_signal(request, "llm_gateway_chat")
        return JSONResponse(decoys["ollama_chat"])

    @app.post("/api/embed")
    def ollama_embed(request: Request) -> JSONResponse:
        mark_signal(request, "llm_gateway_embedding")
        return JSONResponse(decoys["ollama_embed"])

    return app


app = create_app()
