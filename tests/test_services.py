"""HTTP smoke tests for every deployable FastAPI service."""

from __future__ import annotations

import base64
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

    def test_archive_crack_trap_serves_only_example_archives(self) -> None:
        module = load_service(
            "test_archive_crack_app",
            "categories/archive-crack-trap/app.py",
        )
        client = TestClient(module.create_app())

        listing = client.get("/vault")
        self.assertIn("testserver/downloads/EXAMPLE-backup.zip", listing.text)
        self.assertIn("archive_crack_listing", latest_event()["signals"])

        archive_response = client.get("/downloads/EXAMPLE-backup.zip")
        self.assertIn(b"EXAMPLE", archive_response.content)
        with zipfile.ZipFile(io.BytesIO(archive_response.content)) as archive:
            info = archive.getinfo("EXAMPLE-known-plaintext.txt")
            self.assertTrue(info.flag_bits & 1)
            plaintext = archive.read(info, pwd=b"EXAMPLE-PASSWORD")
        self.assertIn(b"EXAMPLE NO CREDENTIALS", plaintext)
        self.assertIn("archive_crack_zipcrypto_download", latest_event()["signals"])

        known = client.get("/known/EXAMPLE-known-plaintext.txt")
        self.assertEqual(known.content, module.KNOWN_PLAINTEXT)
        self.assertIn("archive_crack_known_plaintext", latest_event()["signals"])

        attempt = client.post("/api/v1/archive/unlock", json={"password": "guess"})
        self.assertEqual(attempt.status_code, 401)
        self.assertTrue(attempt.json()["attempt_digest"].startswith("EXAMPLE_SHA256_"))
        self.assertIn("archive_crack_password_attempt", latest_event()["signals"])

    def test_session_cookie_trap_logs_tamper_without_authorizing(self) -> None:
        module = load_service(
            "test_session_cookie_app",
            "categories/session-cookie-trap/app.py",
        )
        client = TestClient(module.create_app())

        issued = client.get("/session/issue")
        self.assertIn("session=EXAMPLE_CBC_", issued.headers["set-cookie"])
        self.assertIn("testserver/admin", issued.text)
        self.assertIn("session_cookie_issue", latest_event()["signals"])

        self.assertEqual(client.get("/admin").status_code, 403)
        tampered = TestClient(module.create_app()).get(
            "/admin",
            headers={"Cookie": "session=EXAMPLE_CBC_MODIFIED"},
        )
        self.assertEqual(tampered.status_code, 200)
        self.assertIn("EXAMPLE Admin Console", tampered.text)
        self.assertIn("session_cookie_tamper", latest_event()["signals"])

        decoded = client.post("/api/v1/session/decode", json={"cookie": "modified"})
        self.assertEqual(decoded.json()["integrity"], "EXAMPLE_NONE_ADVERTISED")
        self.assertTrue(decoded.json()["submission_digest"].startswith("EXAMPLE_SHA256_"))
        self.assertIn("session_cookie_decode", latest_event()["signals"])

    def test_link_preview_search_never_fetches_or_queries(self) -> None:
        module = load_service(
            "test_link_preview_search_app",
            "categories/link-preview-search-trap/app.py",
        )
        client = TestClient(module.create_app())

        landing = client.get("/")
        self.assertIn("testserver/api/preview", landing.text)
        self.assertIn("link_preview_landing", latest_event()["signals"])

        submitted_url = "http://169.254.169.254/latest/meta-data/"
        preview = client.post("/api/preview", json={"url": submitted_url})
        self.assertEqual(preview.json()["target_class"], "EXAMPLE_METADATA_TARGET")
        self.assertNotIn(submitted_url, preview.text)
        self.assertIn("testserver/preview/cache/EXAMPLE-PREVIEW-001", preview.text)
        self.assertIn("link_preview_ssrf_probe", latest_event()["signals"])
        self.assertIn("link_preview_metadata_target", latest_event()["signals"])

        search = client.get("/api/search", params={"q": "1' AND pg_sleep(5)--"})
        self.assertIn(search.json()["match"], {"EXAMPLE_TRUE", "EXAMPLE_FALSE"})
        self.assertIn(
            search.json()["timing_class"],
            {"EXAMPLE_DELAYED_BRANCH", "EXAMPLE_FAST_BRANCH"},
        )
        self.assertIn("link_preview_sqli_probe", latest_event()["signals"])
        self.assertIn("link_preview_time_sqli_probe", latest_event()["signals"])

    def test_secrets_vault_trap_returns_deterministic_progress(self) -> None:
        module = load_service(
            "test_secrets_vault_app",
            "categories/secrets-vault-trap/app.py",
        )
        client = TestClient(module.create_app())

        listing = client.get("/vault")
        self.assertIn("testserver/api/v1/vault/unlock", listing.text)
        self.assertIn("EXAMPLE_credentials.json.enc", listing.text)
        self.assertIn("secrets_vault_listing", latest_event()["signals"])

        payload = {"phrase": "one-of-many-guesses", "pin": "1234"}
        first = client.post("/api/v1/vault/unlock", json=payload)
        second = client.post("/api/v1/vault/unlock", json=payload)
        self.assertEqual(first.status_code, 401)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(first.json()["status"], "EXAMPLE_UNLOCK_INCOMPLETE")
        self.assertNotIn(payload["phrase"], first.text)
        self.assertTrue(first.json()["attempt_digest"].startswith("EXAMPLE_SHA256_"))
        self.assertIn("secrets_vault_guess", latest_event()["signals"])

        export = client.get("/api/v1/vault/export")
        self.assertEqual(export.status_code, 423)
        self.assertIn("secrets_vault_export_followup", latest_event()["signals"])

    def test_script_drop_trap_serves_inert_text_without_execution(self) -> None:
        module = load_service(
            "test_script_drop_app",
            "categories/script-drop-trap/app.py",
        )
        client = TestClient(module.create_app())

        catalog = client.get("/scripts")
        self.assertIn("testserver/downloads/EXAMPLE-audit.ps1", catalog.text)
        self.assertIn("testserver/api/v1/execute", catalog.text)
        self.assertIn("script_drop_catalog", latest_event()["signals"])

        powershell = client.get("/downloads/EXAMPLE-audit.ps1")
        self.assertIn("EXAMPLE analysis-only", powershell.text)
        self.assertNotIn("Invoke-", powershell.text)
        self.assertIn("script_drop_powershell_download", latest_event()["signals"])

        submitted_script = "Write-Output should-not-run"
        execution = client.post(
            "/api/v1/execute",
            json={"script": submitted_script},
        )
        self.assertEqual(execution.json()["status"], "EXAMPLE_EXECUTION_DISABLED")
        self.assertNotIn(submitted_script, execution.text)
        self.assertTrue(
            execution.json()["submission_digest"].startswith("EXAMPLE_SHA256_")
        )
        self.assertIn("script_drop_execute_attempt", latest_event()["signals"])

        analysis = client.get("/analysis/EXAMPLE-SCRIPT-001")
        self.assertEqual(analysis.json()["capabilities"], ["EXAMPLE_NONE"])
        self.assertIn("script_drop_analysis_followup", latest_event()["signals"])

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

        environment = client.get("/.env")
        self.assertIn(b"EXAMPLE", environment.content)
        self.assertIn("testserver", environment.text)
        self.assertIn(b"EXAMPLE INVALID PRIVATE KEY", client.get("/.ssh/id_rsa").content)
        self.assertIn("합성 허니팟", client.get("/.환경").text)
        config = client.get("/config.json").json()
        self.assertIn("testserver", config["gcp"]["client_email"])
        korean_config = client.get("/설정.json").json()
        self.assertEqual(korean_config["데이터베이스"]["호스트"], "testserver")

    def test_graphql_introspection_is_finite_and_mutations_fail(self) -> None:
        module = load_service("test_graphql_server", "categories/graphql-trap/server.py")
        client = TestClient(module.create_app())

        response = client.post(
            "/graphql",
            json={"query": "query { __schema { queryType { name } } }"},
        )
        self.assertEqual(response.json()["data"]["__schema"]["queryType"]["name"], "Query")
        users = client.post("/graphql", json={"query": "query { users { email } }"})
        self.assertIn("testserver", users.json()["data"]["users"][0]["email"])
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
        role = client.get(
            "/latest/meta-data/iam/security-credentials/EXAMPLE-DECOY-ROLE"
        )
        self.assertEqual(role.status_code, 200)
        self.assertIn("EXAMPLE-NOT-A-VALID-AWS-ACCESS-KEY", role.text)
        self.assertIn("cloud_credential_probe", latest_event()["signals"])

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

    def test_mcp_server_returns_only_fixed_protocol_fixtures(self) -> None:
        module = load_service(
            "test_mcp_server_app",
            "categories/mcp-server-trap/app.py",
        )
        client = TestClient(module.create_app())

        discovery = client.get("/.well-known/mcp.json")
        self.assertEqual(discovery.status_code, 200)
        self.assertIn("testserver", discovery.json()["endpoint"])

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
        self.assertIn("testserver", card["url"])

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
        store = client.get("/v1/vector_stores/EXAMPLE_STORE_ID").json()
        self.assertIn("testserver", store["metadata"]["documentation_url"])

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
        self.assertIn("testserver", download.json()["artifact_uri"])
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
        self.assertIn("testserver", manifest.text)
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

    def test_git_remote_trap_logs_clone_and_secret_fetch(self) -> None:
        module = load_service(
            "test_git_remote_trap_app",
            "categories/git-remote-trap/app.py",
        )
        client = TestClient(module.create_app())

        refs = client.get(
            "/acme/secret-project.git/info/refs",
            params={"service": "git-upload-pack"},
        )
        self.assertIn("git-upload-pack", refs.text)
        self.assertIn("git_remote_clone_attempt", latest_event()["signals"])
        # pkt-line framing validation: each packet is "<4-hex len><payload>",
        # len includes the 4-char prefix; len==0 is a flush-pkt (no payload)
        stream = refs.text
        packets = 0
        while stream:
            declared = int(stream[:4], 16)
            if declared == 0:  # flush-pkt
                stream = stream[4:]
                continue
            packet = stream[:declared]
            self.assertEqual(len(packet), declared, f"pkt-line length mismatch: {packet[:60]!r}")
            stream = stream[declared:]
            packets += 1
        self.assertGreaterEqual(packets, 3)  # service line + 2 refs

        upload = client.post("/acme/secret-project.git/git-upload-pack")
        self.assertEqual(upload.status_code, 200)
        self.assertIn("git_remote_upload_pack", latest_event()["signals"])

        metadata = client.get("/repos/acme/secret-project")
        self.assertEqual(metadata.json()["full_name"], "acme/secret-project")
        self.assertIn("git_remote_gh_metadata", latest_event()["signals"])

        secret = client.get("/repos/acme/secret-project/contents/.env")
        self.assertIn("base64", secret.json()["encoding"])
        self.assertIn("git_remote_secret_fetch", latest_event()["signals"])

        aws = client.get("/repos/acme/secret-project/contents/.aws/credentials")
        decoded = base64.b64decode(aws.json()["content"]).decode("utf-8")
        self.assertIn("EXAMPLE_AKIA", decoded)
        self.assertIn("git_remote_secret_fetch", latest_event()["signals"])

        commits = client.get("/repos/acme/secret-project/commits")
        self.assertEqual(commits.json()[0]["sha"].startswith("EXAMPLE-SHA"), True)
        self.assertIn("git_remote_gh_commits", latest_event()["signals"])

        branches = client.get("/repos/acme/secret-project/branches")
        self.assertEqual(len(branches.json()), 2)
        self.assertIn("git_remote_gh_branches", latest_event()["signals"])

        unknown = client.get("/repos/evil/repo")
        self.assertEqual(unknown.status_code, 404)

        bad_service = client.get("/acme/secret-project.git/info/refs")
        self.assertEqual(bad_service.status_code, 404)

    def test_oauth_sso_never_issues_tokens(self) -> None:
        module = load_service(
            "test_oauth_sso_app",
            "categories/oauth-sso-trap/app.py",
        )
        client = TestClient(module.create_app())

        discovery = client.get("/.well-known/openid-configuration")
        self.assertIn("oauth/devicecode", discovery.text)
        self.assertIn("testserver", discovery.json()["issuer"])
        self.assertIn("oauth_oidc_discovery", latest_event()["signals"])

        jwks = client.get("/oauth/jwks")
        self.assertIn("EXAMPLE-KID-0001", jwks.text)
        self.assertIn("oauth_jwks", latest_event()["signals"])

        bad_client = client.get("/oauth/authorize", params={"client_id": "wrong"})
        self.assertEqual(bad_client.status_code, 400)
        self.assertIn("invalid_client", bad_client.text)

        token = client.post("/oauth/token", json={"grant_type": "authorization_code"})
        self.assertEqual(token.status_code, 400)
        self.assertIn("invalid_grant", token.text)
        self.assertIn("oauth_token_exchange", latest_event()["signals"])

        device = client.post("/oauth/devicecode")
        self.assertIn("EXAMPLE_DEVICE_CODE_0001", device.text)
        self.assertIn("oauth_device_code", latest_event()["signals"])

        poll = client.post("/oauth/token/device")
        self.assertEqual(poll.status_code, 400)
        self.assertIn("authorization_pending", poll.text)
        self.assertIn("oauth_device_token_poll", latest_event()["signals"])

        login = client.get("/login")
        self.assertIn("Sign in", login.text)
        self.assertIn("oauth_login_page", latest_event()["signals"])

        submit = client.post("/login", data={"username": "EXAMPLE", "password": "EXAMPLE"})
        self.assertIn("invalid_grant", submit.text)
        self.assertIn("oauth_login_submit", latest_event()["signals"])

        consent = client.get("/consent")
        self.assertIn("Authorize application", consent.text)
        self.assertIn("oauth_consent_page", latest_event()["signals"])

        device_submit = client.post("/device", data={"user_code": "EXAMPLE-USER-CODE"})
        self.assertEqual(device_submit.status_code, 400)
        self.assertIn("access_denied", device_submit.text)
        self.assertIn("oauth_device_submit", latest_event()["signals"])

if __name__ == "__main__":
    unittest.main()
