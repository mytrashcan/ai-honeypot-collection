# Deployment guide

The safest default is a disposable lab host with loopback-only bindings. A
public sensor requires network isolation, a privacy/retention decision, and
authorization from the address-space owner.

## Prerequisites

- Docker Engine with Docker Compose v2 or later
- A Linux host or VM dedicated to research
- Storage and log access restricted to the research team
- An explicit monitoring and retention policy

## Local deployment

Choose one category and run its Compose project:

```bash
cd categories/graphql-trap
docker compose config --quiet
docker compose up --detach --build
docker compose ps
curl http://127.0.0.1:8083/healthz
```

Stop it without deleting the event volume:

```bash
docker compose down
```

Delete the volume only after exporting any required evidence and confirming
the applicable retention policy:

```bash
docker compose down --volumes
```

## Port map

| Service | Loopback port |
| --- | ---: |
| Web scanner | `8080` |
| Credential honey | `8081` |
| GraphQL | `8083` |
| Cloud metadata | `8084` |
| Agentic lure | `8085` |
| MCP server | `8086` |
| A2A agent | `8087` |
| Vector store | `8088` |
| Model registry | `8090` |
| LLM gateway | `8091` |
| Coding-agent workspace | `8093` |
| Package registry | `8095` |
| Git remote | `8096` |
| OAuth/SSO | `8098` |
| Archive crack | `8101` |
| Session cookie | `8102` |
| Link preview and search | `8103` |
| Secrets vault | `8104` |
| Script drop | `8105` |

Override one port for a local conflict:

```bash
HONEYPOT_PORT=9080 docker compose up --detach
```

## Production boundary

Before any internet-facing deployment:

1. Place the host in a dedicated DMZ/VPC/subnet with no route to production
   applications, secrets, control planes, or metadata services.
2. Deny outbound traffic by default. The services need no egress after their
   images are built.
3. Put a maintained reverse proxy or load balancer in front for TLS,
   connection limits, and network-level logs.
4. Expose only the intended listener. Keep Docker and administrative ports
   private.
5. Ship stdout/JSONL events to append-only storage with access control and a
   short, documented retention period.
6. Monitor disk, memory, container health, and request volume. Apply upstream
   rate/size limits as well as the application's 64 KiB body limit.
7. Patch the host and rebuild images regularly.

Do not colocate a honeypot with customer data. Do not give it cloud IAM roles.
Do not mount the Docker socket, host filesystem, SSH keys, or production log
directories.

## Important cloud-metadata warning

The metadata trap is an ordinary HTTP decoy that recognizes provider path and
header shapes. Never bind it to `169.254.169.254`, change host routes to replace
the real metadata service, or deploy it where it could interfere with cloud
instance identity. Test SSRF routing only inside an isolated lab.

## Event storage

Each Compose project creates a named `events` volume mounted at `/data`.
Discover its concrete Docker name with:

```bash
docker volume ls
docker compose exec -T graphql-trap sh -c 'wc -l /data/events.jsonl'
```

Prefer log shipping from stdout rather than routinely entering a container.
The JSONL file is a local fallback. It includes source IPs, which may be
regulated personal data.

The recorder intentionally excludes:

- request bodies (only a bounded byte count and SHA-256 digest are kept);
- query parameter values;
- header values other than non-sensitive content metadata;
- cookies and authorization values.

## Analysis

Copy an exported JSONL file to a trusted analysis host:

```bash
python3 categories/ai-fingerprint/analyzer.py exported-events.jsonl
```

Combine multiple service exports:

```bash
python3 categories/ai-fingerprint/analyzer.py \
  web-events.jsonl graphql-events.jsonl agentic-events.jsonl
```

Treat all verdicts as leads for manual review. NAT, proxies, scanners operated
by humans, and spoofable headers limit source-level inference.

## Incident handling

If a decoy receives credible traffic:

1. Preserve the relevant event lines and surrounding network/reverse-proxy
   logs.
2. Record clock source, image digest, configuration, and deployment topology.
3. Check whether the source touched any non-decoy asset; the honeypot itself
   cannot answer that.
4. Follow the organization's incident-response and legal escalation process.
5. Do not contact, scan back, exploit, or submit captured values to third-party
   services.

## Updates and rollback

Build a candidate image, test it on loopback, then replace the running service.
Retain the previous image digest for rollback. Configuration and code are
stateless; the `events` volume is the only local persistent state.
