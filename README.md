# AI Honeypot Collection

`ai-honeypot-collection` is a set of safe, observable HTTP decoys for studying
automated and AI-assisted security reconnaissance. The services expose inert
versions of paths that scanners prioritize, record request metadata as JSONL,
and return only unmistakably synthetic data.

The repository is defensive research infrastructure. It contains no exploit
delivery, credential validation, command execution, C2 tasking, or real
secrets.

## 🌐 Languages

- [English](README.md)
- [한국어](README.ko.md)

## Why AI-focused honeypots?

Modern security agents combine model-driven planning with browsers, shells,
and conventional scanners. The underlying tools still enumerate familiar
assets such as `/.env`, `/actuator`, `/graphql`, and cloud metadata paths, but
an agent may adapt its next action from the response, revisit promising
branches, or follow natural-language instructions.

No HTTP request can prove that an LLM produced it. This project therefore
separates:

- **automation evidence**, such as scanner user agents and rapid path
  diversity;
- **agentic evidence**, such as following a benign instruction canary; and
- **attribution**, which is deliberately left unresolved without external
  evidence.

See [the research review](docs/ai-tools-research.md) for the evidence and
limitations behind that model.

## Categories

| Category | Purpose | Default port |
| --- | --- | ---: |
| [`web-scanner-trap`](categories/web-scanner-trap/) | Decoy API, Spring Actuator, WordPress, Git, environment, and API-doc paths | `8080` |
| [`credential-honey`](categories/credential-honey/) | Clearly fake environment, cloud credential, and SSH-key files | `8081` |
| [`graphql-trap`](categories/graphql-trap/) | Finite, read-only GraphQL schema and introspection responses | `8083` |
| [`cloud-metadata-trap`](categories/cloud-metadata-trap/) | AWS, GCP, and Azure metadata path/header canaries | `8084` |
| [`agentic-lure`](categories/agentic-lure/) | Benign natural-language instruction-following canary | `8085` |
| [`mcp-server-trap`](categories/mcp-server-trap/) | Inert MCP discovery, tool, resource, and prompt fixtures | `8086` |
| [`a2a-agent-trap`](categories/a2a-agent-trap/) | Fixed Agent Card, message, and task protocol fixtures | `8087` |
| [`vector-store-trap`](categories/vector-store-trap/) | Read-only vector-store enumeration and deterministic ranking fixtures | `8088` |
| [`model-registry-trap`](categories/model-registry-trap/) | MLflow, Ollama, OCI, and model-config metadata fixtures | `8090` |
| [`llm-gateway-trap`](categories/llm-gateway-trap/) | Fixed OpenAI- and Ollama-compatible gateway responses | `8091` |
| [`coding-agent-workspace-trap`](categories/coding-agent-workspace-trap/) | Synthetic agent instructions, manifests, source, and tests | `8093` |
| [`registry-trap`](categories/registry-trap/) | Inert npm, PyPI, and OCI registry decoys for dependency-resolving agents | `8095` |
| [`git-remote-trap`](categories/git-remote-trap/) | Seeded secret repo + GitHub-API decoys for repo-cloning secret scanners | `8096` |
| [`oauth-sso-trap`](categories/oauth-sso-trap/) | Inert OAuth2/OIDC authorization server for device-code/token attempts | `8098` |
| [`archive-crack-trap`](categories/archive-crack-trap/) | Legacy-encrypted archive, known-plaintext, and password-attempt lures | `8101` |
| [`session-cookie-trap`](categories/session-cookie-trap/) | CBC-shaped guest-cookie tamper and admin-follow-up signals | `8102` |
| [`link-preview-search-trap`](categories/link-preview-search-trap/) | Non-fetching URL-preview lure and deterministic blind-search responses | `8103` |
| [`secrets-vault-trap`](categories/secrets-vault-trap/) | Stateless recovery guesses with deterministic partial-progress responses | `8104` |
| [`script-drop-trap`](categories/script-drop-trap/) | Side-effect-free script downloads and execution-shaped submissions | `8105` |
| [`ai-fingerprint`](categories/ai-fingerprint/) | Offline, conservative analysis of combined JSONL events | n/a |

Cloud metadata probing has provider-specific protocol signals, while
prompt-following is one of the few observations more specific to an agent than
to a fixed wordlist. Ports `8101` through `8105` turn CTF lessons into inert
observation surfaces: they preserve the tempting follow-up sequence without
performing decryption, authorization, network fetching, database queries,
delays, or script execution.

## Quick start

Each honeypot is independently deployable. Docker Compose binds to loopback by
default:

```bash
cd categories/web-scanner-trap
docker compose up --detach --build
curl http://127.0.0.1:8080/.env
docker compose logs --follow
```

Events are appended to `/data/events.jsonl` in the service's named Docker
volume and mirrored to standard output. Analyze an exported log with:

```bash
python3 categories/ai-fingerprint/analyzer.py events.jsonl
python3 categories/ai-fingerprint/analyzer.py --json events.jsonl
```

Read the [deployment guide](docs/deployment-guide.md) before exposing any
service outside a local lab.

## Logging model

Every non-health request records:

- UTC timestamp and random event ID;
- socket source IP and whether a forwarded-for header was present;
- method, path, query parameter **names**, endpoint, and response status;
- selected content metadata and header **names**;
- bounded body size and SHA-256 digest, not the submitted body;
- safe route-derived signals such as `graphql_introspection`.

Authorization values, cookies, query values, and request bodies are not stored.
Operators remain responsible for notice, retention, access control, and local
privacy law.

## Safety properties

- All credential-like values start with `EXAMPLE`, use invalid syntax, or use
  the reserved `.invalid` domain.
- Containers run as UID/GID `10001`, use a read-only root filesystem, drop all
  Linux capabilities, set `no-new-privileges`, and have memory/PID limits.
- Ports bind to `127.0.0.1` unless an operator deliberately changes the
  deployment.
- CTF-derived lures never crack archives, authorize cookies, fetch submitted
  URLs, query a database, delay responses, or execute submitted text.
- GraphQL is finite and mutation-free.
- Request bodies are capped at 64 KiB.

## Development

The code requires Python 3.11 or newer.

```bash
ruff check .
python3 -m unittest discover -s tests -v
python3 -m compileall -q honeypot_common categories tests
for file in categories/*/docker-compose.yml; do
  docker compose -f "$file" config --quiet
done
```

Service smoke tests run when FastAPI is installed; otherwise they are skipped
locally and exercised by CI.

## Ethical use

Deploy only on systems and address space you own or are explicitly authorized
to monitor. Do not impersonate a third party, collect unnecessary personal
data, connect these decoys to production secrets, or use observations to
attack a visitor. Isolate the services, deny unnecessary egress, publish a
retention policy, and treat source IPs as potentially personal data.

This repository is not a substitute for an IDS, WAF, incident-response
program, or legal review. A match is a research signal, not proof of malicious
intent or AI authorship.

## License

MIT
