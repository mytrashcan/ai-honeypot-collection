"""Legacy archive lures for observing download and password-cracking workflows."""

from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from honeypot_common import install_fastapi_tracking, mark_signal

DECOY_PATH = Path(__file__).with_name("decoy_data.json")
KNOWN_PLAINTEXT = (
    b"EXAMPLE KNOWN PLAINTEXT FOR ARCHIVE ANALYSIS\n"
    b"EXAMPLE NO CREDENTIALS OR PRIVATE DATA\n"
)
ZIP_ENTRY_NAME = "EXAMPLE-known-plaintext.txt"
ZIP_PASSWORD = b"EXAMPLE-PASSWORD"
ZIP_CRYPTO_FLAG = 0x0001
ZIP_DOS_DATE = ((2026 - 1980) << 9) | (1 << 5) | 1


def _load_decoys() -> dict[str, Any]:
    """Load fixed archive metadata."""

    with DECOY_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _crc32_byte(value: int, crc: int) -> int:
    """Apply the PKZIP CRC primitive to one byte."""

    updated = crc ^ value
    for _ in range(8):
        updated = (updated >> 1) ^ (0xEDB88320 if updated & 1 else 0)
    return updated & 0xFFFFFFFF


class _ZipCryptoEncoder:
    """Encode bytes with the traditional PKZIP stream cipher."""

    def __init__(self, password: bytes) -> None:
        self._key0 = 0x12345678
        self._key1 = 0x23456789
        self._key2 = 0x34567890
        for value in password:
            self._update_keys(value)

    def _update_keys(self, value: int) -> None:
        self._key0 = _crc32_byte(value, self._key0)
        self._key1 = (self._key1 + (self._key0 & 0xFF)) & 0xFFFFFFFF
        self._key1 = (self._key1 * 134775813 + 1) & 0xFFFFFFFF
        self._key2 = _crc32_byte(self._key1 >> 24, self._key2)

    def encrypt(self, content: bytes) -> bytes:
        """Return encrypted bytes while updating the cipher keys."""

        encrypted = bytearray()
        for value in content:
            temporary = self._key2 | 2
            encrypted.append(value ^ (((temporary * (temporary ^ 1)) >> 8) & 0xFF))
            self._update_keys(value)
        return bytes(encrypted)


def _legacy_zipcrypto_archive() -> bytes:
    """Build one deterministic, standards-compatible ZipCrypto archive."""

    filename = ZIP_ENTRY_NAME.encode("utf-8")
    checksum = zlib.crc32(KNOWN_PLAINTEXT) & 0xFFFFFFFF
    encryption_header = b"EXAMPLE-HDR" + bytes((checksum >> 24,))
    encoder = _ZipCryptoEncoder(ZIP_PASSWORD)
    encrypted_content = encoder.encrypt(encryption_header + KNOWN_PLAINTEXT)

    local_header = struct.pack(
        "<IHHHHHIIIHH",
        0x04034B50,
        20,
        ZIP_CRYPTO_FLAG,
        0,
        0,
        ZIP_DOS_DATE,
        checksum,
        len(encrypted_content),
        len(KNOWN_PLAINTEXT),
        len(filename),
        0,
    )
    local_record = local_header + filename + encrypted_content
    central_record = struct.pack(
        "<IHHHHHHIIIHHHHHII",
        0x02014B50,
        20,
        20,
        ZIP_CRYPTO_FLAG,
        0,
        0,
        ZIP_DOS_DATE,
        checksum,
        len(encrypted_content),
        len(KNOWN_PLAINTEXT),
        len(filename),
        0,
        0,
        0,
        0,
        0,
        0,
    ) + filename
    end_record = struct.pack(
        "<IHHHHIIH",
        0x06054B50,
        0,
        0,
        1,
        1,
        len(central_record),
        len(local_record),
        0,
    )
    return local_record + central_record + end_record


ZIP_ARCHIVE = _legacy_zipcrypto_archive()
SEVEN_ZIP_PLACEHOLDER = b"7z\xbc\xaf'\x1cEXAMPLE-7Z-ARCHIVE-NO-PRIVATE-DATA"


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def create_app() -> FastAPI:
    """Create the independently deployable archive-cracking trap."""

    app = FastAPI(
        title="EXAMPLE Archive Vault",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    decoys = _load_decoys()
    install_fastapi_tracking(app, "archive-crack-trap")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    @app.get("/vault")
    def archive_listing(request: Request) -> JSONResponse:
        mark_signal(request, "archive_crack_listing")
        base = _base_url(request)
        archives = [
            {**archive, "download_url": f"{base}{archive['download_path']}"}
            for archive in decoys["archives"]
        ]
        return JSONResponse(
            {
                "service": "EXAMPLE_ARCHIVE_VAULT",
                "archives": archives,
                "known_plaintext_url": f"{base}/known/EXAMPLE-known-plaintext.txt",
                "unlock_url": f"{base}/api/v1/archive/unlock",
            }
        )

    @app.get("/downloads/EXAMPLE-backup.zip")
    def zip_download(request: Request) -> Response:
        mark_signal(request, "archive_crack_download", "archive_crack_zipcrypto_download")
        return Response(
            ZIP_ARCHIVE,
            media_type="application/zip",
            headers={
                "Content-Disposition": 'attachment; filename="EXAMPLE-backup.zip"',
                "X-Archive-Format": "EXAMPLE-ZIPCRYPTO",
            },
        )

    @app.get("/downloads/EXAMPLE-backup.7z")
    def seven_zip_download(request: Request) -> Response:
        mark_signal(request, "archive_crack_download", "archive_crack_7z_download")
        return Response(
            SEVEN_ZIP_PLACEHOLDER,
            media_type="application/x-7z-compressed",
            headers={"Content-Disposition": 'attachment; filename="EXAMPLE-backup.7z"'},
        )

    @app.get("/known/EXAMPLE-known-plaintext.txt")
    def known_plaintext(request: Request) -> PlainTextResponse:
        mark_signal(request, "archive_crack_known_plaintext")
        return PlainTextResponse(KNOWN_PLAINTEXT.decode("ascii"))

    @app.get("/api/v1/archive/status/EXAMPLE-ARCHIVE-001")
    def archive_status(request: Request) -> JSONResponse:
        mark_signal(request, "archive_crack_status")
        return JSONResponse(decoys["status"])

    @app.post("/api/v1/archive/unlock")
    def unlock_archive(request: Request) -> JSONResponse:
        body = request.scope.get("honeypot_body", b"")
        digest = hashlib.sha256(body).hexdigest()
        mark_signal(request, "archive_crack_password_attempt")
        return JSONResponse(
            {
                "status": "EXAMPLE_LOCKED",
                "detail": "EXAMPLE PASSWORD REJECTED",
                "attempt_digest": f"EXAMPLE_SHA256_{digest}",
            },
            status_code=401,
        )

    return app


app = create_app()
