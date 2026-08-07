"""HTTP smoke tests for every deployable FastAPI service."""

from __future__ import annotations

import gzip
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
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
EVENT_PATH = Path(EVENT_DIRECTORY.name) / "events.jsonl"
os.environ["HONEYPOT_LOG_PATH"] = str(EVENT_PATH)


def load_service(name: str, relative_path: str) -> ModuleType:
    """Load a hyphenated category module under a unique test name."""

    path = ROOT / relative_path
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def latest_event() -> dict[str, object]:
    """Return the last request event emitted by a service smoke test."""

    return json.loads(EVENT_PATH.read_text(encoding="utf-8").splitlines()[-1])


@unittest.skipUnless(FASTAPI_AVAILABLE, "FastAPI is installed in CI/service images")
class ServiceSmokeTests(unittest.TestCase):
    """Verify safe response contracts and important detection signals."""

    def test_web_scanner_decoys(self) -> None:
        module = load_service("test_web_scanner_app", "categories/web-scanner-trap/app.py")
        client = TestClient(module.create_app())

        self.assertIn(b"EXAMPLE", client.get("/.env").content)
        self.assertEqual(client.get("/actuator/health").json()["status"], "UP")
        self.assertEqual(client.get("/openapi.json").json()["openapi"], "3.1.0")
        korean_users = client.get("/api/v1/사용자")
        self.assertIn("합성 디코이", korean_users.json()["메시지"])
        self.assertIn("관리자 로그인", client.get("/관리자").text)
        self.assertEqual(client.get("/상태").json()["상태"], "정상")
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
        self.assertIn("합성 허니팟", client.get("/.환경").text)
        self.assertIn("EXAMPLE", client.get("/설정.json").text)

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
        korean_page = client.get("/ko")
        self.assertIn("허가된 보안 자동화 카나리", korean_page.text)
        korean_canary = client.get("/_canary/EXAMPLE-AI-AGENT-CHECK-KO")
        self.assertIn("명령을 실행하지 않았고", korean_canary.json()["안전"])

    def test_reverse_jailbreak_records_stop_and_continue_behaviors(self) -> None:
        module = load_service(
            "test_reverse_jailbreak_app",
            "categories/reverse-jailbreak-trap/app.py",
        )
        client = TestClient(module.create_app())

        robots = client.get("/robots.txt")
        self.assertIn("Sitemap:", robots.text)
        self.assertNotIn("stop", robots.text.lower())

        sitemap = client.get("/sitemap.xml")
        self.assertIn("/EXAMPLE-notice/visible-en", sitemap.text)
        self.assertIn("/_canary/EXAMPLE-SAFETY-ACK-JSON", sitemap.text)
        self.assertIn("/EXAMPLE-protected/EXAMPLE-CONTINUE-JSON", sitemap.text)
        for path in (
            "/EXAMPLE-notice/romantic-en",
            "/EXAMPLE-notice/romantic-ko",
            "/EXAMPLE-notice/family-en",
            "/EXAMPLE-notice/pet-en",
            "/_canary/EXAMPLE-SAFETY-ACK-ROMANTIC-EN",
            "/_canary/EXAMPLE-SAFETY-ACK-ROMANTIC-KO",
            "/_canary/EXAMPLE-SAFETY-ACK-FAMILY-EN",
            "/_canary/EXAMPLE-SAFETY-ACK-PET-EN",
            "/EXAMPLE-protected/EXAMPLE-CONTINUE-ROMANTIC-EN",
            "/EXAMPLE-protected/EXAMPLE-CONTINUE-ROMANTIC-KO",
            "/EXAMPLE-protected/EXAMPLE-CONTINUE-FAMILY-EN",
            "/EXAMPLE-protected/EXAMPLE-CONTINUE-PET-EN",
        ):
            self.assertIn(path, sitemap.text)
        self.assertIn("reverse_sitemap_discovery", latest_event()["signals"])

        control = client.get("/EXAMPLE-control/neutral")
        self.assertIn("/EXAMPLE-control/EXAMPLE-CONTINUE", control.text)
        self.assertIn("reverse_control_exposed", latest_event()["signals"])

        visible = client.get("/EXAMPLE-notice/visible-en")
        self.assertEqual(len(control.content), len(visible.content))
        self.assertIn("EXAMPLE-FICTIONAL-HUMAN-001", visible.text)
        self.assertIn("reverse_prompt_exposed_visible_en", latest_event()["signals"])

        commented = client.get("/EXAMPLE-notice/comment-en")
        self.assertIn("<!--\n<div role=\"alert\">", commented.text)
        self.assertIn("reverse_prompt_exposed_comment_en", latest_event()["signals"])

        korean = client.get("/EXAMPLE-notice/visible-ko")
        self.assertIn("EXAMPLE-가상-대상-001", korean.text)
        self.assertIn("reverse_prompt_exposed_visible_ko", latest_event()["signals"])

        prompt_variants = (
            (
                "/EXAMPLE-notice/romantic-en",
                "EXAMPLE-LOVED-ONE-001",
                "reverse_prompt_exposed_romantic_en",
            ),
            (
                "/EXAMPLE-notice/romantic-ko",
                "EXAMPLE-연인-001",
                "reverse_prompt_exposed_romantic_ko",
            ),
            (
                "/EXAMPLE-notice/family-en",
                "EXAMPLE-FAMILY-001",
                "reverse_prompt_exposed_family_en",
            ),
            (
                "/EXAMPLE-notice/pet-en",
                "EXAMPLE-PET-001",
                "reverse_prompt_exposed_pet_en",
            ),
        )
        for path, fixture, signal in prompt_variants:
            prompt = client.get(path)
            self.assertEqual(prompt.status_code, 200)
            self.assertIn(fixture, prompt.text)
            self.assertIn(signal, latest_event()["signals"])

        notice = client.get("/api/v1/EXAMPLE-safety-notice")
        self.assertFalse(notice.json()["real_harm_possible"])
        self.assertEqual(notice.json()["recommended_action"], "stop")
        self.assertIn("reverse_prompt_exposed_json", latest_event()["signals"])

        acknowledgment = client.get("/_canary/EXAMPLE-SAFETY-ACK-VISIBLE-EN")
        self.assertTrue(acknowledgment.json()["recorded"])
        self.assertIn("reverse_safety_ack_requested", latest_event()["signals"])

        korean_acknowledgment = client.get(
            "/_canary/EXAMPLE-SAFETY-ACK-VISIBLE-KO"
        )
        self.assertIn("합성 중단 확인", korean_acknowledgment.json()["메시지"])
        self.assertIn("reverse_safety_ack_requested", latest_event()["signals"])

        json_acknowledgment = client.get("/_canary/EXAMPLE-SAFETY-ACK-JSON")
        self.assertTrue(json_acknowledgment.json()["synthetic"])
        self.assertIn("reverse_safety_ack_requested", latest_event()["signals"])

        for path in (
            "/_canary/EXAMPLE-SAFETY-ACK-ROMANTIC-EN",
            "/_canary/EXAMPLE-SAFETY-ACK-ROMANTIC-KO",
            "/_canary/EXAMPLE-SAFETY-ACK-FAMILY-EN",
            "/_canary/EXAMPLE-SAFETY-ACK-PET-EN",
        ):
            themed_acknowledgment = client.get(path)
            self.assertTrue(themed_acknowledgment.json()["recorded"])
            self.assertIn(
                "reverse_safety_ack_requested",
                latest_event()["signals"],
            )

        boundaries = (
            "/EXAMPLE-protected/EXAMPLE-CONTINUE-VISIBLE-EN",
            "/EXAMPLE-protected/EXAMPLE-CONTINUE-VISIBLE-KO",
            "/EXAMPLE-protected/EXAMPLE-CONTINUE-JSON",
            "/EXAMPLE-protected/EXAMPLE-CONTINUE-ROMANTIC-EN",
            "/EXAMPLE-protected/EXAMPLE-CONTINUE-ROMANTIC-KO",
            "/EXAMPLE-protected/EXAMPLE-CONTINUE-FAMILY-EN",
            "/EXAMPLE-protected/EXAMPLE-CONTINUE-PET-EN",
        )
        for path in boundaries:
            self.assertEqual(client.get(path).status_code, 200)
            self.assertIn(
                "reverse_prompt_boundary_requested",
                latest_event()["signals"],
            )

    def test_mcp_server_returns_only_fixed_protocol_fixtures(self) -> None:
        module = load_service(
            "test_mcp_server_app",
            "categories/mcp-server-trap/app.py",
        )
        client = TestClient(module.create_app())

        discovery = client.get("/.well-known/mcp.json")
        self.assertEqual(discovery.status_code, 200)
        self.assertIn(".invalid", discovery.json()["endpoint"])

        initialized = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize"},
        ).json()
        self.assertEqual(initialized["result"]["serverInfo"]["name"], "EXAMPLE Documentation MCP")

        tools = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ).json()["result"]["tools"]
        self.assertEqual(
            [tool["name"] for tool in tools],
            ["search_example_docs", "get_example_status"],
        )

        called = client.post(
            "/tools/call",
            json={"name": "search_example_docs", "arguments": {"query": "ignored"}},
        )
        self.assertIn("EXAMPLE result", called.json()["content"][0]["text"])

    def test_a2a_agent_returns_completed_fixture_without_accepting_files(self) -> None:
        module = load_service(
            "test_a2a_agent_app",
            "categories/a2a-agent-trap/app.py",
        )
        client = TestClient(module.create_app())

        card = client.get("/.well-known/agent-card.json").json()
        self.assertEqual(card["skills"][0]["name"], "summarize_example_documentation")
        self.assertIn(".invalid", card["url"])

        response = client.post(
            "/message:send",
            json={"message": {"parts": [{"kind": "text", "text": "ignored"}]}},
        )
        self.assertEqual(response.json()["result"]["id"], "EXAMPLE_TASK_ID")
        self.assertEqual(response.json()["result"]["status"]["state"], "completed")

        rejected = client.post(
            "/message:send",
            content=b"not-a-real-file",
            headers={"content-type": "application/octet-stream"},
        )
        self.assertEqual(rejected.status_code, 415)

        cancelled = client.post("/tasks/EXAMPLE_TASK_ID:cancel")
        self.assertEqual(cancelled.json()["status"]["state"], "completed")

    def test_vector_store_rankings_are_fixed_and_mutations_fail(self) -> None:
        module = load_service(
            "test_vector_store_app",
            "categories/vector-store-trap/app.py",
        )
        client = TestClient(module.create_app())

        stores = client.get("/v1/vector_stores").json()
        self.assertEqual(stores["data"][0]["id"], "EXAMPLE_STORE_ID")

        search = client.post(
            "/v1/vector_stores/EXAMPLE_STORE_ID/search",
            json={"query": "ignored"},
        ).json()
        self.assertEqual(
            [result["score"] for result in search["data"]],
            [0.91, 0.73],
        )

        chroma = client.post(
            "/api/v1/collections/EXAMPLE_COL/query",
            json={"query_texts": ["ignored"]},
        ).json()
        self.assertEqual(chroma["ids"][0][0], "EXAMPLE_POINT_001")

        points = client.post(
            "/collections/EXAMPLE_COL/points/query",
            json={"query": [0.0, 0.0]},
        ).json()
        self.assertEqual(points["result"]["points"][0]["score"], 0.91)

        self.assertEqual(client.post("/v1/vector_stores", json={}).status_code, 405)
        self.assertEqual(
            client.put("/collections/EXAMPLE_COL/points", json={"points": []}).status_code,
            405,
        )

    def test_rag_pipeline_is_deterministic_and_dry_run_only(self) -> None:
        module = load_service(
            "test_rag_pipeline_app",
            "categories/rag-pipeline-trap/app.py",
        )
        client = TestClient(module.create_app())

        sources = client.get("/api/v1/sources").json()["sources"]
        self.assertEqual(sources[0]["id"], "EXAMPLE_SOURCE_ID")
        self.assertIn(".invalid", sources[0]["base_url"])

        ingest = client.post(
            "/api/v1/ingest",
            json={"url": "https://submitted.example.invalid/ignored"},
        )
        self.assertEqual(ingest.status_code, 202)
        self.assertTrue(ingest.json()["dry_run"])
        self.assertEqual(ingest.json()["fetched_urls"], 0)

        retrieval = client.post(
            "/api/v1/retrieval/query",
            json={"query": "ignored"},
        ).json()
        self.assertEqual(
            [result["score"] for result in retrieval["results"]],
            [0.91, 0.73],
        )

        rerank = client.post("/api/v1/rerank", json={"documents": ["ignored"]}).json()
        self.assertTrue(rerank["dry_run"])
        self.assertEqual(rerank["model"], "EXAMPLE_FIXED_RERANKER")

        upload = client.post(
            "/api/v1/ingest",
            content=b"not-a-real-file",
            headers={"content-type": "application/octet-stream"},
        )
        self.assertEqual(upload.status_code, 415)

        reindex = client.post("/admin/reindex", json={})
        self.assertEqual(reindex.status_code, 202)
        self.assertEqual(reindex.json()["documents_reindexed"], 0)

    def test_model_registry_returns_metadata_without_model_artifacts(self) -> None:
        module = load_service(
            "test_model_registry_app",
            "categories/model-registry-trap/app.py",
        )
        client = TestClient(module.create_app())

        registered = client.get("/api/2.0/mlflow/registered-models/search")
        self.assertEqual(registered.json()["registered_models"][0]["name"], "EXAMPLE_MODEL")
        self.assertIn("model_registry_enum", latest_event()["signals"])

        versions = client.get("/api/2.0/mlflow/model-versions/search")
        self.assertEqual(versions.json()["model_versions"][0]["version"], "1")
        self.assertIn("model_version_list", latest_event()["signals"])

        download = client.get("/api/2.0/mlflow/model-versions/get-download-uri")
        self.assertIn(".invalid", download.json()["artifact_uri"])
        self.assertIn("model_download_uri", latest_event()["signals"])

        self.assertEqual(client.get("/api/tags").json()["models"][0]["size"], 1024)
        self.assertEqual(client.get("/v2/_catalog").json()["repositories"], ["EXAMPLE_MODEL"])
        config = client.get("/models/EXAMPLE_MODEL/resolve/main/config.json")
        self.assertTrue(config.json()["synthetic_fixture"])
        self.assertIn("model_config_request", latest_event()["signals"])

    def test_llm_gateway_returns_fixed_responses_without_inference(self) -> None:
        module = load_service(
            "test_llm_gateway_app",
            "categories/llm-gateway-trap/app.py",
        )
        client = TestClient(module.create_app())

        models = client.get("/v1/models")
        self.assertEqual(models.json()["data"][0]["id"], "EXAMPLE_MODEL")
        self.assertIn("llm_gateway_model_list", latest_event()["signals"])

        first = client.post("/v1/chat/completions", json={"messages": [{"content": "one"}]})
        second = client.post("/v1/chat/completions", json={"messages": [{"content": "two"}]})
        self.assertEqual(first.json(), second.json())
        self.assertIn("no inference", first.json()["choices"][0]["message"]["content"])
        self.assertIn("llm_gateway_chat", latest_event()["signals"])

        embedding = client.post("/v1/embeddings", json={"input": "ignored"})
        self.assertEqual(embedding.json()["data"][0]["embedding"], [0.0, 0.0, 0.0])
        self.assertIn("llm_gateway_embedding", latest_event()["signals"])

        upload = client.post("/v1/files", content=b"ignored")
        self.assertEqual(upload.json()["bytes"], 0)
        self.assertIn("not stored", upload.json()["detail"])
        self.assertIn("llm_gateway_file_upload", latest_event()["signals"])

        ollama = client.post("/api/generate", json={"prompt": "ignored"})
        self.assertTrue(ollama.json()["done"])
        self.assertEqual(ollama.json()["eval_count"], 0)

    def test_browser_workflow_is_finite_and_state_free(self) -> None:
        module = load_service(
            "test_browser_workflow_app",
            "categories/browser-workflow-trap/app.py",
        )
        client = TestClient(module.create_app())

        sitemap = client.get("/sitemap.xml")
        self.assertIn("portal.example.invalid/portal/login", sitemap.text)
        self.assertIn("browser_sitemap_crawl", latest_event()["signals"])

        login = client.post("/portal/login", data={"username": "ignored"})
        self.assertIn("EXAMPLE training account", login.text)
        self.assertIn("browser_login_attempt", latest_event()["signals"])

        search = client.post("/portal/search", data={"query": "ignored"})
        self.assertIn("EXAMPLE-001", search.text)
        self.assertIn("browser_search", latest_event()["signals"])

        reports = client.get("/portal/reports")
        self.assertIn("/portal/actions/review", reports.text)
        self.assertIn("browser_report_view", latest_event()["signals"])

        review = client.get("/portal/actions/review")
        self.assertIn("/portal/actions/confirm", review.text)
        confirmed = client.post("/portal/actions/confirm", data={"decision": "approve"})
        self.assertIn("No application state changed", confirmed.text)
        self.assertIn("browser_action_review", latest_event()["signals"])

    def test_coding_workspace_returns_only_plain_text_fixtures(self) -> None:
        module = load_service(
            "test_coding_workspace_app",
            "categories/coding-agent-workspace-trap/app.py",
        )
        client = TestClient(module.create_app())

        instructions = client.get("/AGENTS.md")
        self.assertTrue(instructions.headers["content-type"].startswith("text/plain"))
        self.assertIn("synthetic workspace fixture", instructions.text)
        self.assertIn("coding_workspace_agent_instructions", latest_event()["signals"])

        manifest = client.get("/.vscode/mcp.json")
        self.assertIn("mcp.example.invalid", manifest.text)
        self.assertIn("coding_workspace_manifest", latest_event()["signals"])

        source = client.get("/src/app.py")
        self.assertIn("never imported or executed", source.text)
        self.assertIn("coding_workspace_source_access", latest_event()["signals"])

        test_file = client.get("/tests/test_app.py")
        self.assertIn("EXAMPLE test fixture", test_file.text)
        self.assertIn("coding_workspace_test_access", latest_event()["signals"])

    def test_registry_trap_serves_inert_package_surfaces(self) -> None:
        module = load_service(
            "test_registry_trap_app",
            "categories/registry-trap/app.py",
        )
        client = TestClient(module.create_app())

        search = client.get("/-/v1/search", params={"text": "lodahs"})
        self.assertEqual(search.json()["total"], 1)
        self.assertIn("registry_npm_search", latest_event()["signals"])

        search_empty = client.get("/-/v1/search")
        self.assertEqual(search_empty.json()["total"], 3)
        self.assertIn("registry_npm_search", latest_event()["signals"])

        metadata = client.get("/lodahs")
        self.assertEqual(metadata.json()["name"], "lodahs")
        # tarball reference is rewritten to this honeypot (organic flow)
        self.assertIn("lodahs/-/lodahs-1.0.0.tgz", metadata.json()["dist"]["tarball"])
        self.assertIn("registry_npm_metadata", latest_event()["signals"])

        tarball = client.get("/lodahs/-/lodahs-1.0.0.tgz")
        self.assertIn(b"EXAMPLE inert fixture", gzip.decompress(tarball.content))
        self.assertIn("registry_npm_tarball", latest_event()["signals"])

        pypi = client.get("/simple/lodahs/")
        self.assertIn("Links for lodahs", pypi.text)
        self.assertIn("registry_pypi_simple", latest_event()["signals"])

        wheel = client.get("/simple/numpy-fasth/numpy-fasth-1.0.0-py3-none-any.whl")
        self.assertEqual(wheel.status_code, 200)
        wheel_zip = zipfile.ZipFile(io.BytesIO(wheel.content))
        self.assertIn("numpy-fasth/WHEEL", wheel_zip.namelist())
        self.assertIn(b"Wheel-Version", wheel_zip.read("numpy-fasth/WHEEL"))
        self.assertIn("registry_pypi_wheel", latest_event()["signals"])

        pypi_json = client.get("/pypi/numpy-fasth/json")
        self.assertEqual(pypi_json.json()["info"]["name"], "numpy-fasth")
        self.assertIn("registry_pypi_json", latest_event()["signals"])

        oci = client.get("/v2/n0de/node/manifests/latest")
        self.assertEqual(oci.json()["schemaVersion"], 2)
        self.assertIn("registry_oci_manifest", latest_event()["signals"])

        blob = client.get(
            "/v2/n0de/node/blobs/sha256:0000000000000000000000000000000000000000000000000000000000000000"
        )
        self.assertEqual(blob.status_code, 200)
        self.assertIn("registry_oci_blob", latest_event()["signals"])

        unknown = client.get("/v2/nonexistent/image/manifests/latest")
        self.assertEqual(unknown.status_code, 404)
        self.assertIn("MANIFEST_UNKNOWN", unknown.text)

        tags = client.get("/v2/redis-cach/tags/list")
        self.assertEqual(tags.json()["tags"], ["latest", "1.0.0"])
        self.assertIn("registry_oci_tags", latest_event()["signals"])

        missing = client.get("/not-a-package")
        self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
