"""Privacy-conscious JSONL request tracking for the honeypot services.

The recorder intentionally stores request metadata and a body digest rather
than request bodies. This preserves useful sequencing evidence without turning
the honeypot into a repository of attacker-submitted secrets or payloads.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self
from uuid import uuid4

LOGGER = logging.getLogger("honeypot.events")
DEFAULT_LOG_PATH = "/data/events.jsonl"
MAX_TEXT_FIELD = 512
MAX_BODY_BYTES = 65_536
SIGNALS_KEY = "ai_honeypot.signals"


def _clean(value: object, limit: int = MAX_TEXT_FIELD) -> str:
    """Return a bounded string; JSON encoding handles any control characters."""

    return str(value or "")[:limit]


def _header_names(headers: Any) -> list[str]:
    """Record header names, never authorization, cookie, or token values."""

    return sorted({_clean(name, 100).lower() for name in headers})[:100]


@dataclass(slots=True, frozen=True)
class RequestEvent:
    """A normalized request observation suitable for JSONL storage."""

    event_id: str
    timestamp: str
    category: str
    source_ip: str
    forwarded_for_present: bool
    method: str
    path: str
    query_keys: list[str]
    endpoint: str
    status: int
    user_agent: str
    content_type: str
    accept: str
    body_size: int
    body_sha256: str
    header_names: list[str]
    signals: list[str] = field(default_factory=list)

    @classmethod
    def from_asgi(
        cls,
        request: Any,
        response: Any,
        category: str,
        body: bytes,
    ) -> Self:
        """Build an event from Starlette-compatible request/response objects."""

        signals = request.scope.get(SIGNALS_KEY, [])
        route = request.scope.get("route")
        try:
            declared_size = int(request.headers.get("content-length", "0"))
        except ValueError:
            declared_size = 0
        return cls(
            event_id=str(uuid4()),
            timestamp=datetime.now(UTC).isoformat(),
            category=_clean(category, 100),
            source_ip=_clean(request.client.host if request.client else "unknown", 128),
            forwarded_for_present="x-forwarded-for" in request.headers,
            method=_clean(request.method, 16),
            path=_clean(request.url.path, 2_048),
            query_keys=sorted({_clean(key, 200) for key in request.query_params})[:100],
            endpoint=_clean(getattr(route, "name", "unmatched"), 200),
            status=int(getattr(response, "status_code", 500)),
            user_agent=_clean(request.headers.get("user-agent"), 512),
            content_type=_clean(request.headers.get("content-type"), 200),
            accept=_clean(request.headers.get("accept"), 200),
            body_size=min(max(len(body), declared_size), MAX_BODY_BYTES),
            body_sha256=hashlib.sha256(body).hexdigest() if body else "",
            header_names=_header_names(request.headers),
            signals=sorted({_clean(signal, 100) for signal in signals})[:20],
        )


class EventRecorder:
    """Append request events atomically to JSONL and mirror them to stdout."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path or os.environ.get("HONEYPOT_LOG_PATH", DEFAULT_LOG_PATH))

    def record(self, event: RequestEvent) -> None:
        """Persist one bounded event without interrupting request handling."""

        line = json.dumps(asdict(event), sort_keys=True, separators=(",", ":")) + "\n"
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(
                self.path,
                os.O_APPEND | os.O_CREAT | os.O_WRONLY,
                0o600,
            )
            try:
                os.write(descriptor, line.encode("utf-8"))
            finally:
                os.close(descriptor)
        except OSError:
            LOGGER.exception("Unable to append honeypot event")
        print(line, end="", file=sys.stdout, flush=True)


def mark_signal(request: Any, *signals: str) -> None:
    """Attach safe, route-derived signals to the current request event."""

    existing = request.scope.setdefault(SIGNALS_KEY, [])
    existing.extend(_clean(signal, 100) for signal in signals)


def install_fastapi_tracking(
    app: Any,
    category: str,
    *,
    recorder: EventRecorder | None = None,
) -> None:
    """Install bounded request logging and defensive response headers."""

    active_recorder = recorder or EventRecorder()

    @app.middleware("http")
    async def track_request(
        request: Any,
        call_next: Callable[[Any], Awaitable[Any]],
    ) -> Any:
        from starlette.responses import JSONResponse

        try:
            declared_size = int(request.headers.get("content-length", "0"))
        except ValueError:
            declared_size = 0

        body = b""
        too_large = declared_size > MAX_BODY_BYTES
        if not too_large:
            chunks = bytearray()
            async for chunk in request.stream():
                chunks.extend(chunk)
                if len(chunks) > MAX_BODY_BYTES:
                    too_large = True
                    break
            body = bytes(chunks[:MAX_BODY_BYTES])
            request._body = body

        if too_large:
            response = JSONResponse({"detail": "Request body too large"}, status_code=413)
        else:
            try:
                response = await call_next(request)
            except Exception:
                LOGGER.exception("Unhandled honeypot request error")
                response = JSONResponse({"detail": "Internal server error"}, status_code=500)
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if request.url.path != "/healthz":
            event = RequestEvent.from_asgi(request, response, category, body)
            active_recorder.record(event)
        return response
