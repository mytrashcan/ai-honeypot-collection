"""Inert HTTP response-shape decoys for C2 infrastructure fingerprinting.

This service does not implement any C2 handshake, encryption, tasking,
payload staging, or request decoding. It only returns harmless static bodies.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response

from honeypot_common import install_fastapi_tracking, mark_signal

ONE_PIXEL_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
    b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


def create_app() -> FastAPI:
    """Create a safe C2-shaped HTTP decoy."""

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    install_fastapi_tracking(app, "c2-decoy")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.api_route("/", methods=["GET", "POST"])
    @app.api_route("/{resource:path}", methods=["GET", "POST"])
    def decoy(request: Request, resource: str = "") -> Response:
        lowered = resource.lower()
        mark_signal(request, "c2_like_probe")
        headers = {
            "ETag": 'W/"EXAMPLE-C2-DECOY-NOT-A-REAL-LISTENER"',
            "X-Decoy-Safety": "NO-TASKING-NO-PAYLOADS",
        }
        if lowered.endswith((".gif", ".png", ".jpg")):
            return Response(ONE_PIXEL_GIF, headers=headers, media_type="image/gif")
        if lowered.endswith((".woff", ".woff2")):
            mark_signal(request, "sliver_stager_shape_probe")
            return Response(
                b"EXAMPLE-DECOY-FONT-NO-SHELLCODE",
                headers=headers,
                media_type="font/woff",
            )
        if request.method == "POST":
            return Response(status_code=204, headers=headers)
        return HTMLResponse(
            "<html><title>Example CDN</title><body>It works.</body></html>",
            headers=headers,
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
