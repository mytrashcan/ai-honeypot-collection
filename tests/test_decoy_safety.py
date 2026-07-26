"""Static safety assertions for public synthetic credential material."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class DecoySafetyTests(unittest.TestCase):
    """Prevent accidental replacement of explicit examples with real values."""

    def test_environment_values_are_explicit_examples(self) -> None:
        env_path = ROOT / "categories" / "credential-honey" / ".env"
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            _, value = line.split("=", 1)
            self.assertTrue(
                "EXAMPLE" in value or ".invalid" in value,
                msg=f"unsafe-looking decoy value in {env_path}: {line}",
            )

    def test_config_strings_are_examples_or_structural_labels(self) -> None:
        config_path = ROOT / "categories" / "credential-honey" / "config.json"
        document = json.loads(config_path.read_text(encoding="utf-8"))
        serialized = json.dumps(document)

        self.assertIn("EXAMPLE", serialized)
        self.assertNotIn("AKIA", serialized)
        self.assertNotIn("BEGIN PRIVATE KEY", serialized)
        self.assertIn("BEGIN EXAMPLE INVALID PRIVATE KEY", serialized)


if __name__ == "__main__":
    unittest.main()
