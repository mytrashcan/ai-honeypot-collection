"""Serve synthetic credential files while recording every retrieval."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response

from honeypot_common import install_fastapi_tracking, mark_signal

BASE_DIR = Path(__file__).resolve().parent


def _base_url(request: Request) -> str:
    """Return the current honeypot base URL without a trailing slash."""

    return str(request.base_url).rstrip("/")


def _request_host(request: Request) -> str:
    """Return the hostname from the current request base URL."""

    host = urlsplit(_base_url(request)).hostname
    if host is None:
        raise ValueError("request base URL has no hostname")
    return host


def _decoy_file_response(
    request: Request,
    filename: str,
    media_type: str,
) -> Response:
    """Render a host-agnostic decoy file for the current serving origin."""

    content = (BASE_DIR / filename).read_text(encoding="utf-8")
    content = content.replace("EXAMPLE_BASE_URL", _base_url(request))
    content = content.replace("EXAMPLE_REQUEST_HOST", _request_host(request))
    return Response(content, media_type=media_type)


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
    def env_file(request: Request) -> Response:
        mark_signal(request, "credential_file_probe", "environment_file_probe")
        return _decoy_file_response(request, ".env", "text/plain")

    @app.get("/.환경")
    @app.get("/설정/.환경")
    def korean_env_file(request: Request) -> Response:
        mark_signal(
            request,
            "credential_file_probe",
            "environment_file_probe",
            "korean_localized_probe",
        )
        return _decoy_file_response(request, ".환경", "text/plain")

    @app.get("/config.json")
    @app.get("/config/config.json")
    @app.get("/credentials.json")
    def config_file(request: Request) -> Response:
        mark_signal(request, "credential_file_probe", "cloud_credential_probe")
        return _decoy_file_response(request, "config.json", "application/json")

    @app.get("/설정.json")
    @app.get("/설정/설정.json")
    @app.get("/자격증명.json")
    def korean_config_file(request: Request) -> Response:
        mark_signal(
            request,
            "credential_file_probe",
            "cloud_credential_probe",
            "korean_localized_probe",
        )
        return _decoy_file_response(request, "설정.json", "application/json")

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
