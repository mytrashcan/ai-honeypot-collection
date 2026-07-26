# AI Honeypot Collection

`ai-honeypot-collection` is a set of safe, observable HTTP decoys for studying
automated and AI-assisted security reconnaissance. The services expose inert
versions of paths that scanners prioritize, record request metadata as JSONL,
and return only unmistakably synthetic data.

The repository is defensive research infrastructure. It contains no exploit
delivery, credential validation, command execution, C2 tasking, or real
secrets.

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
| [`c2-decoy`](categories/c2-decoy/) | Inert HTTP response shapes for C2-fingerprinting research | `8082` |
| [`graphql-trap`](categories/graphql-trap/) | Finite, read-only GraphQL schema and introspection responses | `8083` |
| [`cloud-metadata-trap`](categories/cloud-metadata-trap/) | AWS, GCP, and Azure metadata path/header canaries | `8084` |
| [`agentic-lure`](categories/agentic-lure/) | Benign natural-language instruction-following canary | `8085` |
| [`ai-fingerprint`](categories/ai-fingerprint/) | Offline, conservative analysis of combined JSONL events | n/a |

The last two deployable categories were added from the research: cloud metadata
probing has provider-specific protocol signals, while prompt-following is one
of the few observations more specific to an agent than to a fixed wordlist.

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
- The C2 decoy never decodes messages, stages payloads, or issues tasks.
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
