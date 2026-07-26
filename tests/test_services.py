"""HTTP smoke tests for every deployable FastAPI service."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType

try:
    import fastapi  # noqa: F401
    from fastapi.testclient import TestClient
except ModuleNotFoundError:
    FASTAPI_AVAILABLE = False
else:
    FASTAPI_AVAILABLE = True

ROOT = Path(__file__).parents[1]
EVENT_DIRECTORY = tempfile.TemporaryDirectory()
os.environ["HONEYPOT_LOG_PATH"] = str(Path(EVENT_DIRECTORY.name) / "events.jsonl")


def load_service(name: str, relative_path: str) -> ModuleType:
    """Load a hyphenated category module under a unique test name."""

    path = ROOT / relative_path
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


@unittest.skipUnless(FASTAPI_AVAILABLE, "FastAPI is installed in CI/service images")
class ServiceSmokeTests(unittest.TestCase):
    """Verify safe response contracts and important detection signals."""

    def test_web_scanner_decoys(self) -> None:
        module = load_service("test_web_scanner_app", "categories/web-scanner-trap/app.py")
        client = TestClient(module.create_app())

        self.assertIn(b"EXAMPLE", client.get("/.env").content)
        self.assertEqual(client.get("/actuator/health").json()["status"], "UP")
        self.assertEqual(client.get("/openapi.json").json()["openapi"], "3.1.0")
        oversized = client.post("/api/v1/", content=b"x" * 65_537)
        self.assertEqual(oversized.status_code, 413)

    def test_credential_decoys_are_obviously_invalid(self) -> None:
        module = load_service(
            "test_credential_honey_server",
            "categories/credential-honey/server.py",
        )
        client = TestClient(module.create_app())

        self.assertIn(b"EXAMPLE", client.get("/.env").content)
        self.assertIn(b"EXAMPLE INVALID PRIVATE KEY", client.get("/.ssh/id_rsa").content)

    def test_c2_decoy_never_returns_a_stage(self) -> None:
        module = load_service("test_c2_decoy_server", "categories/c2-decoy/server.py")
        client = TestClient(module.create_app())

        response = client.get("/assets/example.woff")
        self.assertEqual(response.content, b"EXAMPLE-DECOY-FONT-NO-SHELLCODE")
        self.assertEqual(client.post("/submit.php", content=b"opaque").status_code, 204)

    def test_graphql_introspection_is_finite_and_mutations_fail(self) -> None:
        module = load_service("test_graphql_server", "categories/graphql-trap/server.py")
        client = TestClient(module.create_app())

        response = client.post(
            "/graphql",
            json={"query": "query { __schema { queryType { name } } }"},
        )
        self.assertEqual(response.json()["data"]["__schema"]["queryType"]["name"], "Query")
        mutation = client.post("/graphql", json={"query": "mutation { deleteAll }"})
        self.assertEqual(mutation.status_code, 400)

    def test_metadata_protocol_headers(self) -> None:
        module = load_service(
            "test_cloud_metadata_server",
            "categories/cloud-metadata-trap/server.py",
        )
        client = TestClient(module.create_app())

        self.assertEqual(client.get("/computeMetadata/v1/project/project-id").status_code, 403)
        gcp = client.get(
            "/computeMetadata/v1/project/project-id",
            headers={"Metadata-Flavor": "Google"},
        )
        self.assertIn(b"EXAMPLE", gcp.content)
        self.assertEqual(client.get("/metadata/instance?api-version=2025-04-07").status_code, 400)

    def test_agentic_canary_is_benign(self) -> None:
        module = load_service("test_agentic_lure_server", "categories/agentic-lure/server.py")
        client = TestClient(module.create_app())

        page = client.get("/")
        self.assertIn(b"AUTHORIZED SECURITY AUTOMATION CANARY", page.content)
        response = client.get("/_canary/EXAMPLE-AI-AGENT-CHECK")
        self.assertIn("No commands were run", response.json()["safety"])


if __name__ == "__main__":
    unittest.main()
