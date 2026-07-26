"""Unit tests for the automation heuristic analyzer."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "categories" / "ai-fingerprint" / "analyzer.py"
SPEC = importlib.util.spec_from_file_location("ai_fingerprint_analyzer", MODULE_PATH)
assert SPEC and SPEC.loader
ANALYZER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ANALYZER
SPEC.loader.exec_module(ANALYZER)


class AnalyzerTests(unittest.TestCase):
    """Exercise conservative scoring and sequence detection."""

    def setUp(self) -> None:
        rules_path = MODULE_PATH.with_name("rules.yaml")
        self.rules, self.sequence = ANALYZER.load_rules(rules_path)

    def test_agentic_canary_requires_strong_signal(self) -> None:
        events = [
            {
                "source_ip": "192.0.2.20",
                "path": "/_canary/EXAMPLE-AI-AGENT-CHECK",
                "signals": ["agentic_canary_followed"],
                "header_names": ["x-audit-agent"],
                "timestamp": datetime.now(UTC).isoformat(),
            }
        ]
        result = ANALYZER.analyze(events, self.rules, self.sequence)[0]

        self.assertEqual(result.verdict, "agentic-automation-suspected")
        self.assertGreaterEqual(result.score, 8)

    def test_rapid_path_diversity_flags_automation_only(self) -> None:
        start = datetime.now(UTC)
        events = [
            {
                "source_ip": "192.0.2.30",
                "path": f"/probe-{index}",
                "timestamp": (start + timedelta(seconds=index)).isoformat(),
            }
            for index in range(5)
        ]
        result = ANALYZER.analyze(events, self.rules, self.sequence)[0]

        self.assertIn("rapid-path-diversity", result.matched_rules)
        self.assertEqual(result.verdict, "insufficient-evidence")

    def test_common_scanner_is_not_mislabeled_as_ai(self) -> None:
        events = [
            {
                "source_ip": "192.0.2.40",
                "path": "/",
                "user_agent": "Nuclei - Open-source project",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        ]
        result = ANALYZER.analyze(events, self.rules, self.sequence)[0]

        self.assertEqual(result.verdict, "automation-suspected")
        self.assertEqual(result.ai_specific_matches, 0)


if __name__ == "__main__":
    unittest.main()
