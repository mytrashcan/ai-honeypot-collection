"""Read-only GraphQL decoy with safe, finite introspection responses."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from honeypot_common import install_fastapi_tracking, mark_signal

QUERY_FIELDS = [
    {"name": "serviceStatus", "type": {"kind": "SCALAR", "name": "String"}},
    {"name": "users", "type": {"kind": "LIST", "name": None}},
]
TYPES = [
    {"kind": "OBJECT", "name": "Query", "fields": QUERY_FIELDS},
    {
        "kind": "OBJECT",
        "name": "User",
        "fields": [
            {"name": "id", "type": {"kind": "SCALAR", "name": "ID"}},
            {"name": "email", "type": {"kind": "SCALAR", "name": "String"}},
            {"name": "apiKey", "type": {"kind": "SCALAR", "name": "String"}},
        ],
    },
]


async def _extract_query(request: Request) -> str:
    """Read a GraphQL query from GET parameters or a small JSON body."""

    if request.method == "GET":
        return request.query_params.get("query", "")
    try:
        document: dict[str, Any] = await request.json()
    except ValueError:
        document = {}
    return str(document.get("query", ""))


def _base_url(request: Request) -> str:
    """Return the current honeypot base URL without a trailing slash."""

    return str(request.base_url).rstrip("/")


def _request_host(request: Request) -> str:
    """Return the hostname from the current request base URL."""

    host = urlsplit(_base_url(request)).hostname
    if host is None:
        raise ValueError("request base URL has no hostname")
    return host


def create_app() -> FastAPI:
    """Create the finite, mutation-free GraphQL trap."""

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    install_fastapi_tracking(app, "graphql-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    def index() -> HTMLResponse:
        return HTMLResponse(
            "<html><title>EXAMPLE GraphQL Console</title>"
            "<body>POST queries to /graphql</body></html>"
        )

    @app.api_route("/graphql", methods=["GET", "POST"])
    async def graphql(request: Request) -> JSONResponse:
        query = await _extract_query(request)
        if not query:
            return JSONResponse(
                {"errors": [{"message": "A GraphQL query is required."}]},
                status_code=400,
            )
        if "mutation" in query.lower():
            mark_signal(request, "graphql_mutation_attempt")
            return JSONResponse(
                {"errors": [{"message": "Mutations are disabled on this example."}]},
                status_code=400,
            )
        if "__schema" in query:
            mark_signal(request, "graphql_introspection")
            return JSONResponse(
                {
                    "data": {
                        "__schema": {
                            "queryType": {"name": "Query"},
                            "mutationType": None,
                            "types": TYPES,
                            "directives": [],
                        }
                    }
                }
            )
        if "__type" in query:
            mark_signal(request, "graphql_introspection")
            selected = next((item for item in TYPES if item["name"] in query), TYPES[0])
            return JSONResponse({"data": {"__type": selected}})
        if "users" in query:
            mark_signal(request, "graphql_data_probe")
            return JSONResponse(
                {
                    "data": {
                        "users": [
                            {
                                "apiKey": "EXAMPLE-NOT-A-VALID-GRAPHQL-KEY",
                                "email": f"EXAMPLE-admin@{_request_host(request)}",
                                "id": "EXAMPLE-USER-001",
                            }
                        ]
                    },
                    "extensions": {"tracking": "EXAMPLE-GRAPHQL-TRACK-001"},
                }
            )
        return JSONResponse({"data": {"serviceStatus": "EXAMPLE_DECOY_OK"}})

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
