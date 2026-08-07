"""Inert RSS/Atom feed and webhook-receiver decoys.

The service mimics a content publisher that AI agents subscribe to:
RSS/Atom feeds with canary links, webhook receivers, and an /llms.txt
canary surface. Fetching a feed or following a canary link proves agent
follow-through. Webhook payloads are bounded and only digested, never
stored raw.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from honeypot_common import install_fastapi_tracking, mark_signal

FEED_TITLE = "EXAMPLE Product Updates"
FEED_URL = "https://example.invalid/feed.xml"
CANARY_PATH = "/canary/EXAMPLE-CANARY-0001"


def _feed_xml() -> str:
    """Return a fixed RSS 2.0 document with one canary item."""

    now = datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S +0000")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>'
        f"<title>{FEED_TITLE}</title>"
        f"<link>{FEED_URL}</link>"
        "<description>EXAMPLE update feed</description>"
        "<item>"
        f"<title>EXAMPLE release notes</title>"
        f"<link>https://example.invalid{CANARY_PATH}</link>"
        "<description>EXAMPLE description with release details</description>"
        f"<pubDate>{now}</pubDate>"
        "</item>"
        "</channel></rss>"
    )


def _atom_xml() -> str:
    """Return a fixed Atom document with one canary entry."""

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">'
        f"<title>{FEED_TITLE}</title>"
        f'<link href="{FEED_URL}"/>'
        "<entry>"
        f"<title>EXAMPLE release notes</title>"
        f'<link href="https://example.invalid{CANARY_PATH}"/>'
        f"<updated>{now}</updated>"
        "<summary>EXAMPLE summary</summary>"
        "</entry>"
        "</feed>"
    )


def _body_digest(body: bytes) -> str:
    """Return a bounded SHA-256 digest of a request body, never the body."""

    return hashlib.sha256(body).hexdigest() if body else ""


def create_app() -> FastAPI:
    """Create the independently deployable feed/webhook honeypot."""

    app = FastAPI(
        title="EXAMPLE Content Publisher",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    install_fastapi_tracking(app, "feed-webhook-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/feed.xml")
    def feed_rss(request: Request) -> Response:
        mark_signal(request, "feed_rss_fetch")
        return PlainTextResponse(_feed_xml(), media_type="application/rss+xml")

    @app.get("/rss")
    def feed_rss_short(request: Request) -> Response:
        mark_signal(request, "feed_rss_fetch")
        return PlainTextResponse(_feed_xml(), media_type="application/rss+xml")

    @app.get("/atom.xml")
    def feed_atom(request: Request) -> Response:
        mark_signal(request, "feed_atom_fetch")
        return PlainTextResponse(_atom_xml(), media_type="application/atom+xml")

    @app.get("/llms.txt")
    def llms_txt(request: Request) -> Response:
        mark_signal(request, "feed_llms_txt")
        return PlainTextResponse(
            "# EXAMPLE\n\n"
            f"- [Canary link](https://example.invalid{CANARY_PATH})\n"
            "- https://example.invalid/feed.xml\n"
        )

    @app.get(CANARY_PATH)
    def canary_link(request: Request) -> JSONResponse:
        mark_signal(request, "feed_canary_follow")
        return JSONResponse({"status": "ok", "content": "EXAMPLE canary page"})

    @app.post("/webhooks/events")
    def webhook_events(request: Request) -> JSONResponse:
        mark_signal(request, "feed_webhook_events")
        return JSONResponse(
            {"received": True, "body_sha256": _body_digest(getattr(request, "_body", b""))}
        )

    @app.post("/webhooks/{token}")
    def webhook_token(token: str, request: Request) -> JSONResponse:
        mark_signal(request, "feed_webhook_token")
        return JSONResponse(
            {
                "received": True,
                "token": f"EXAMPLE_{token}" if not token.startswith("EXAMPLE_") else token,
                "body_sha256": _body_digest(getattr(request, "_body", b"")),
            }
        )

    return app


app = create_app()
