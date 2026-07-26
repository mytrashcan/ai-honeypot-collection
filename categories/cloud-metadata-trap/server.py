"""Safe imitations of AWS, GCP, and Azure instance metadata endpoints."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from honeypot_common import install_fastapi_tracking, mark_signal


def create_app() -> FastAPI:
    """Create the multi-cloud metadata protocol trap."""

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    install_fastapi_tracking(app, "cloud-metadata-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    def index() -> PlainTextResponse:
        return PlainTextResponse("EXAMPLE local metadata service\n")

    @app.put("/latest/api/token")
    def aws_token(request: Request) -> PlainTextResponse:
        mark_signal(request, "aws_metadata")
        return PlainTextResponse(
            "EXAMPLE-IMDSV2-TOKEN-NOT-VALID",
            headers={"X-Example-Tracking": "EXAMPLE-AWS-METADATA-TRACK-001"},
        )

    @app.get("/latest/meta-data/")
    def aws_index(request: Request) -> PlainTextResponse:
        mark_signal(request, "aws_metadata")
        return PlainTextResponse("instance-id\niam/security-credentials/\n")

    @app.get("/latest/meta-data/instance-id")
    def aws_instance_id(request: Request) -> PlainTextResponse:
        mark_signal(request, "aws_metadata")
        return PlainTextResponse("i-EXAMPLE-NOT-VALID")

    @app.get("/latest/meta-data/iam/security-credentials/")
    def aws_role_list(request: Request) -> PlainTextResponse:
        mark_signal(request, "aws_metadata", "cloud_credential_probe")
        return PlainTextResponse("EXAMPLE-DECOY-ROLE")

    @app.get("/latest/meta-data/iam/security-credentials/<role>")
    def aws_role(role: str, request: Request) -> JSONResponse:
        mark_signal(request, "aws_metadata", "cloud_credential_probe")
        return JSONResponse(
            {
                "AccessKeyId": "EXAMPLE-NOT-A-VALID-AWS-ACCESS-KEY",
                "Code": "Success",
                "Expiration": "2099-01-01T00:00:00Z",
                "LastUpdated": "2026-01-01T00:00:00Z",
                "SecretAccessKey": "EXAMPLE-NOT-A-VALID-AWS-SECRET",
                "Token": f"EXAMPLE-NOT-A-VALID-AWS-SESSION-FOR-{role[:40]}",
                "Type": "EXAMPLE-DECOY",
            }
        )

    @app.get("/computeMetadata/v1/")
    @app.get("/computeMetadata/v1/{resource:path}")
    def gcp_metadata(request: Request, resource: str = "") -> Response:
        mark_signal(request, "gcp_metadata")
        if request.headers.get("metadata-flavor", "").lower() != "google":
            return PlainTextResponse("Metadata-Flavor header required", status_code=403)
        if resource.endswith("/token"):
            mark_signal(request, "cloud_credential_probe")
            return JSONResponse(
                {
                    "access_token": "EXAMPLE-NOT-A-VALID-GCP-TOKEN",
                    "expires_in": 3599,
                    "token_type": "Bearer",
                }
            )
        return PlainTextResponse(
            "EXAMPLE-GCP-METADATA-NO-REAL-PROJECT",
            headers={
                "Metadata-Flavor": "Google",
                "X-Example-Tracking": "EXAMPLE-GCP-METADATA-TRACK-001",
            },
        )

    @app.get("/metadata/instance")
    @app.get("/metadata/instance/{resource:path}")
    def azure_metadata(request: Request, resource: str = "") -> Response:
        mark_signal(request, "azure_metadata")
        if request.headers.get("metadata", "").lower() != "true":
            return PlainTextResponse("Required metadata header not specified", status_code=400)
        return JSONResponse(
            {
                "_warning": "EXAMPLE DECOY DATA ONLY",
                "compute": {
                    "location": "example-region",
                    "name": "EXAMPLE-DECOY-VM",
                    "resourceId": "/EXAMPLE/NOT/A/REAL/RESOURCE",
                    "vmId": "EXAMPLE-NOT-A-UUID",
                },
                "tracking": f"EXAMPLE-AZURE-METADATA-TRACK-{resource or 'ROOT'}",
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
