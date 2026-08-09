"""HTTP decoys for high-value paths commonly enumerated by scanners."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")


def _load_decoys() -> dict[str, Any]:
    """Load immutable, unmistakably synthetic response material."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _base_url(request: Request) -> str:
    """Return the current honeypot base URL without a trailing slash."""

    return str(request.base_url).rstrip("/")


def create_app() -> FastAPI:
    """Create the independently deployable scanner-trap application."""

    app = FastAPI(
        title="EXAMPLE Inventory API",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "web-scanner-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    def index() -> HTMLResponse:
        return HTMLResponse(
            "<html><title>Example Inventory API</title>"
            "<body><h1>Inventory service</h1><p>API version 1</p></body></html>"
        )

    @app.api_route("/api/v1/", methods=["GET", "POST"])
    @app.api_route("/api/v1/users", methods=["GET", "POST"])
    def api_v1(request: Request) -> JSONResponse:
        mark_signal(request, "api_version_probe")
        return JSONResponse(decoys["api"])

    @app.api_route("/api/v1/사용자", methods=["GET", "POST"])
    def korean_api_users(request: Request) -> JSONResponse:
        mark_signal(request, "api_version_probe", "korean_localized_probe")
        return JSONResponse(decoys["korean_api"])

    @app.get("/actuator")
    def actuator_index(request: Request) -> JSONResponse:
        mark_signal(request, "spring_actuator_probe")
        base = _base_url(request)
        return JSONResponse(
            {
                "_links": {
                    "self": {"href": f"{base}/actuator"},
                    "health": {"href": f"{base}/actuator/health"},
                    "env": {"href": f"{base}/actuator/env"},
                }
            }
        )

    @app.get("/actuator/health")
    def actuator_health(request: Request) -> JSONResponse:
        mark_signal(request, "spring_actuator_probe")
        return JSONResponse({"status": "UP", "components": {"decoy": {"status": "UP"}}})

    @app.get("/actuator/env")
    def actuator_env(request: Request) -> JSONResponse:
        mark_signal(request, "spring_actuator_probe", "credential_file_probe")
        return JSONResponse(decoys["actuator_env"])

    @app.api_route("/graphql", methods=["GET", "POST"])
    async def graphql_hint(request: Request) -> JSONResponse:
        body = (await request.body()).decode("utf-8", errors="replace")
        query = request.query_params.get("query", "")
        if "__schema" in body or "__type" in body or "__schema" in query:
            mark_signal(request, "graphql_introspection")
        return JSONResponse(
            {
                "data": {
                    "__typename": "Query",
                    "service": "EXAMPLE-DECOY-GRAPHQL",
                }
            }
        )

    @app.get("/.env")
    def env_file(request: Request) -> PlainTextResponse:
        mark_signal(request, "credential_file_probe")
        body = "\n".join(
            [
                "APP_ENV=EXAMPLE_DECOY_ONLY",
                f"DATABASE_URL={_base_url(request)}"
                f"{decoys['credentials']['database_url']}",
                f"API_TOKEN={decoys['credentials']['api_token']}",
                "",
            ]
        )
        return PlainTextResponse(body)

    @app.get("/.git/config")
    def git_config(request: Request) -> PlainTextResponse:
        mark_signal(request, "source_control_probe")
        return PlainTextResponse(
            '[core]\n\trepositoryformatversion = 0\n'
            f'[remote "origin"]\n\turl = {_base_url(request)}/EXAMPLE/decoy.git\n'
        )

    @app.api_route("/wp-admin", methods=["GET", "POST"])
    @app.api_route("/wp-login.php", methods=["GET", "POST"])
    def wordpress_login(request: Request) -> HTMLResponse:
        mark_signal(request, "wordpress_admin_probe")
        return HTMLResponse(
            "<html><title>EXAMPLE WordPress</title><body>"
            '<form method="post"><input name="log"><input name="pwd" type="password">'
            '<button type="submit">Log In</button></form></body></html>'
        )

    @app.get("/openapi.json")
    @app.get("/swagger.json")
    def openapi_document(request: Request) -> JSONResponse:
        mark_signal(request, "api_schema_probe")
        return JSONResponse(decoys["openapi"])

    @app.get("/swagger-ui")
    @app.get("/swagger-ui/")
    @app.get("/docs")
    def api_docs(request: Request) -> HTMLResponse:
        mark_signal(request, "api_schema_probe")
        return HTMLResponse(
            "<html><title>EXAMPLE API documentation</title>"
            "<body>Specification: /openapi.json</body></html>"
        )

    @app.get("/admin")
    def admin(request: Request) -> HTMLResponse:
        mark_signal(request, "admin_panel_probe")
        return HTMLResponse(
            "<html><title>EXAMPLE Admin</title><body>Sign in</body></html>"
        )

    @app.get("/상태")
    def korean_status(request: Request) -> JSONResponse:
        mark_signal(request, "korean_localized_probe")
        return JSONResponse(decoys["korean_status"])

    @app.api_route("/관리자", methods=["GET", "POST"])
    @app.api_route("/관리/로그인", methods=["GET", "POST"])
    def korean_admin(request: Request) -> HTMLResponse:
        mark_signal(request, "admin_panel_probe", "korean_localized_probe")
        return HTMLResponse(
            "<html lang='ko'><title>EXAMPLE 관리자</title><body>"
            "<h1>관리자 로그인</h1><p>합성 디코이 페이지입니다.</p>"
            '<form method="post"><input name="사용자">'
            '<input name="비밀번호" type="password">'
            '<button type="submit">로그인</button></form></body></html>'
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
