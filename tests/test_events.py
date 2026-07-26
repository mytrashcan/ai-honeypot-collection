"""Unit tests for request-event normalization and persistence."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from honeypot_common.events import EventRecorder, RequestEvent


class EventRecorderTests(unittest.TestCase):
    """Verify append-only JSONL behavior."""

    def test_record_writes_one_json_object(self) -> None:
        event = RequestEvent(
            event_id="event-1",
            timestamp="2026-07-27T00:00:00+00:00",
            category="test",
            source_ip="192.0.2.10",
            forwarded_for_present=False,
            method="GET",
            path="/.env",
            query_keys=[],
            endpoint="env",
            status=200,
            user_agent="unit-test",
            content_type="",
            accept="*/*",
            body_size=0,
            body_sha256="",
            header_names=["accept", "user-agent"],
            signals=["synthetic"],
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            EventRecorder(path).record(event)
            saved = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(saved["event_id"], "event-1")
        self.assertEqual(saved["source_ip"], "192.0.2.10")
        self.assertEqual(saved["signals"], ["synthetic"])


if __name__ == "__main__":
    unittest.main()
