"""Serve synthetic credential files while recording every retrieval."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse

from honeypot_common import install_fastapi_tracking, mark_signal

BASE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    """Create the credential-file decoy service."""

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    install_fastapi_tracking(app, "credential-honey")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    def index() -> PlainTextResponse:
        return PlainTextResponse("EXAMPLE configuration service\n")

    @app.get("/.env")
    @app.get("/.env.production")
    @app.get("/config/.env")
    def env_file(request: Request) -> FileResponse:
        mark_signal(request, "credential_file_probe", "environment_file_probe")
        return FileResponse(BASE_DIR / ".env", media_type="text/plain")

    @app.get("/config.json")
    @app.get("/config/config.json")
    @app.get("/credentials.json")
    def config_file(request: Request) -> FileResponse:
        mark_signal(request, "credential_file_probe", "cloud_credential_probe")
        return FileResponse(BASE_DIR / "config.json", media_type="application/json")

    @app.get("/.aws/credentials")
    def aws_credentials(request: Request) -> PlainTextResponse:
        mark_signal(request, "credential_file_probe", "cloud_credential_probe")
        return PlainTextResponse(
            "[example]\n"
            "aws_access_key_id = EXAMPLE-NOT-A-VALID-AWS-ACCESS-KEY\n"
            "aws_secret_access_key = EXAMPLE-NOT-A-VALID-AWS-SECRET\n"
        )

    @app.get("/.ssh/id_rsa")
    @app.get("/id_rsa")
    def ssh_private_key(request: Request) -> PlainTextResponse:
        mark_signal(request, "credential_file_probe", "ssh_key_probe")
        return PlainTextResponse(
            "-----BEGIN EXAMPLE INVALID PRIVATE KEY-----\n"
            "EXAMPLE-NOT-CRYPTOGRAPHIC-KEY-MATERIAL\n"
            "-----END EXAMPLE INVALID PRIVATE KEY-----\n"
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
