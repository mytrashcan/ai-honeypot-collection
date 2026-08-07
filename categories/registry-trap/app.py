"""Inert npm, PyPI, and OCI package-registry decoys with fixed responses.

The service mimics package-registry surfaces that AI coding agents probe
while resolving or installing dependencies. Every response is static and
inert: tarballs and wheels are gzip/zip placeholders with EXAMPLE-only
content, OCI manifests reference zeroed digests, and no endpoint
executes or validates anything.
"""

from __future__ import annotations

import gzip
import html
import io
import json
import zipfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")


def _load_decoys() -> dict[str, Any]:
    """Load the immutable package-metadata fixtures."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _placeholder_tarball(name: str) -> bytes:
    """Return a deterministic gzip placeholder for a fake package tarball."""

    payload = (
        f"package {name} (EXAMPLE inert fixture)\n"
        f"name: EXAMPLE-{name}\n"
        "version: 1.0.0\n"
        "description: EXAMPLE distribution\n"
    ).encode()
    return gzip.compress(payload, mtime=0)


def _placeholder_wheel(name: str) -> bytes:
    """Return a deterministic zip placeholder for a fake Python wheel."""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            f"{name}/METADATA",
            f"Metadata-Version: 2.1\nName: {name}\nVersion: 1.0.0\n"
            "Summary: EXAMPLE distribution\n",
        )
        archive.writestr(
            f"{name}/WHEEL",
            "Wheel-Version: 1.0\nGenerator: EXAMPLE\nRoot-Is-Purelib: true\n",
        )
    return buffer.getvalue()


def _placeholder_blob() -> bytes:
    """Return a deterministic placeholder for an OCI config blob."""

    return json.dumps(
        {
            "architecture": "amd64",
            "os": "linux",
            "config": {"Env": ["EXAMPLE=1"]},
        }
    ).encode("utf-8")


def create_app() -> FastAPI:
    """Create the independently deployable package-registry honeypot."""

    app = FastAPI(
        title="EXAMPLE Package Registry",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()

    npm_packages = {item["name"]: item for item in decoys["npm"]["packages"]}
    pypi_packages = set(decoys["pypi"]["packages"])
    oci_manifests = decoys["oci"]["manifests"]

    install_fastapi_tracking(app, "registry-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    # --- npm registry surface -------------------------------------------------

    @app.get("/-/v1/search")
    def npm_search(request: Request) -> JSONResponse:
        mark_signal(request, "registry_npm_search")
        query = request.query_params.get("text", "").lower()
        objects = [
            {"package": package}
            for name, package in npm_packages.items()
            if not query or query in name
        ]
        return JSONResponse({"objects": objects, "total": len(objects)})

    @app.get("/{package}")
    def npm_package(package: str, request: Request) -> JSONResponse:
        mark_signal(request, "registry_npm_metadata")
        metadata = npm_packages.get(package)
        if metadata is None:
            return JSONResponse(
                {"error": "Not found", "reason": "unknown package"},
                status_code=404,
            )
        # Rewrite the tarball reference to point at this honeypot so an
        # npm client actually fetches the artifact and fires the signal.
        tarball = metadata["dist"]["tarball"]
        metadata["dist"]["tarball"] = f"{str(request.base_url).rstrip('/')}{tarball}"
        return JSONResponse(metadata)

    @app.get("/{package}/-/{filename}")
    def npm_tarball(package: str, filename: str, request: Request) -> Response:
        mark_signal(request, "registry_npm_tarball")
        expected = f"{package}-1.0.0.tgz"
        if package not in npm_packages or filename != expected:
            return JSONResponse(
                {"error": "Not found", "reason": "unknown file"},
                status_code=404,
            )
        return Response(
            content=_placeholder_tarball(package),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # --- PyPI surface ---------------------------------------------------------

    @app.get("/simple/{package}/")
    def pypi_simple(package: str, request: Request) -> Response:
        mark_signal(request, "registry_pypi_simple")
        if package not in pypi_packages:
            return JSONResponse({"error": "Not found"}, status_code=404)
        safe_package = html.escape(package)
        wheel_href = f"{safe_package}-1.0.0-py3-none-any.whl"
        body = (
            f"<!DOCTYPE html><html><head><title>Links for {safe_package}</title></head>"
            f"<body><h1>Links for {safe_package}</h1>"
            f'<a href="{wheel_href}">{wheel_href}</a>'
            f"</body></html>"
        )
        return Response(content=body, media_type="text/html; charset=utf-8")

    @app.get("/simple/{package}/{filename}")
    def pypi_wheel(package: str, filename: str, request: Request) -> Response:
        mark_signal(request, "registry_pypi_wheel")
        expected = f"{package}-1.0.0-py3-none-any.whl"
        if package not in pypi_packages or filename != expected:
            return JSONResponse({"error": "Not found"}, status_code=404)
        return Response(
            content=_placeholder_wheel(package),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.get("/pypi/{package}/json")
    def pypi_json(package: str, request: Request) -> JSONResponse:
        mark_signal(request, "registry_pypi_json")
        if package not in pypi_packages:
            return JSONResponse({"error": "Not found"}, status_code=404)
        return JSONResponse(
            {
                "info": {
                    "name": package,
                    "version": "1.0.0",
                    "summary": f"EXAMPLE distribution for {package}",
                    "author": "EXAMPLE Author",
                    "home_page": f"https://example.invalid/{package}",
                    "requires_python": ">=3.9",
                },
                "releases": {"1.0.0": []},
            }
        )

    # --- OCI registry surface -------------------------------------------------

    @app.get("/v2/")
    def oci_version(request: Request) -> Response:
        mark_signal(request, "registry_oci_version")
        return Response(content="{}", media_type="application/json")

    @app.get("/v2/{repository:path}/manifests/latest")
    def oci_manifest(repository: str, request: Request) -> JSONResponse:
        mark_signal(request, "registry_oci_manifest")
        if repository not in oci_manifests:
            return JSONResponse(
                {"errors": [{"code": "MANIFEST_UNKNOWN", "message": "manifest unknown"}]},
                status_code=404,
            )
        digest = oci_manifests[repository]["digest"]
        return JSONResponse(
            {
                "schemaVersion": 2,
                "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                "config": {
                    "mediaType": "application/vnd.docker.container.image.v1+json",
                    "size": len(_placeholder_blob()),
                    "digest": digest,
                },
                "layers": [],
            }
        )

    @app.get("/v2/{repository:path}/manifests/{reference}")
    def oci_manifest_reference(repository: str, reference: str, request: Request) -> JSONResponse:
        return oci_manifest(repository, request)

    @app.get("/v2/{repository:path}/blobs/{digest}")
    def oci_blob(repository: str, digest: str, request: Request) -> Response:
        mark_signal(request, "registry_oci_blob")
        if repository not in oci_manifests:
            return JSONResponse(
                {"errors": [{"code": "NAME_UNKNOWN", "message": "repository name not known"}]},
                status_code=404,
            )
        if digest != oci_manifests[repository]["digest"]:
            return JSONResponse(
                {"errors": [{"code": "BLOB_UNKNOWN", "message": "blob unknown"}]},
                status_code=404,
            )
        return Response(
            content=_placeholder_blob(),
            media_type="application/vnd.docker.container.image.v1+json",
        )

    @app.get("/v2/{repository:path}/tags/list")
    def oci_tags(repository: str, request: Request) -> JSONResponse:
        mark_signal(request, "registry_oci_tags")
        if repository not in oci_manifests:
            return JSONResponse(
                {"errors": [{"code": "NAME_UNKNOWN", "message": "repository name not known"}]},
                status_code=404,
            )
        return JSONResponse({"name": repository, "tags": ["latest", "1.0.0"]})

    return app


app = create_app()
