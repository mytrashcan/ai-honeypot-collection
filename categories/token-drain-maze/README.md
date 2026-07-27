# Token Drain Maze

Token Drain Maze is a synthetic FastAPI honeypot that presents finite, inert
responses designed to reveal automated recursive exploration. It combines seven
trap strategies:

1. **Hydra Pattern** — every ordinary path discovers three more synthetic paths,
   up to a configurable maximum depth.
2. **Mutating Response** — repeated requests to the same path return a different
   example vulnerability for the same observed session.
3. **Logic Loop** — `/config.json`, `/internal/db-config`, and
   `/secrets/database` point back to one another through two JSON references and
   one redirect.
4. **Token-Intensive Payload** — paths containing `dump`, `backup`, or `export`
   return a 10 KiB pseudo-base64 decoy payload.
5. **Prompt Injection Trap** — HTML paths and requests with `html` or `page`
   query parameters contain a synthetic hidden instruction.
6. **Protocol Tarpit** — requests with `slow` or `tarpit` query parameters receive
   a deliberately delayed streaming response.
7. **Credibility Funnel** — five realistic-looking API, backup, key, and secret
   paths form a finite chain of explicitly fake data.

All secret-like values begin with `EXAMPLE`; the service never reads host
credentials, executes submitted content, or exposes a real backend. Requests
other than `/healthz` are recorded in `/data/events.jsonl` and stdout by the
shared privacy-conscious tracker.

## Run

From this directory:

```bash
docker compose up --detach --build
curl http://127.0.0.1:8081/
curl http://127.0.0.1:8081/config.json
curl http://127.0.0.1:8081/api/v1/users
docker compose logs --follow
```

The service binds to `127.0.0.1:8081` by default. The maze depth and tarpit delay
range can be configured with `MAZE_MAX_DEPTH`, `MAZE_TARPIT_MIN_MS`, and
`MAZE_TARPIT_MAX_MS`. Keep public deployments isolated behind a reverse proxy
and operate them only in address space you own or are authorized to monitor.

## Verify all strategies

From the repository root, build and start a fresh image:

```bash
docker compose -f categories/token-drain-maze/docker-compose.yml build --no-cache
docker compose -f categories/token-drain-maze/docker-compose.yml up --detach
```

Exercise the entry path, all seven trap strategies, and the healthcheck:

```bash
curl -s http://127.0.0.1:8081/api/v1/users
curl -s http://127.0.0.1:8081/admin/config
curl -s http://127.0.0.1:8081/secrets/aws.json
curl -s http://127.0.0.1:8081/config.json
curl -s http://127.0.0.1:8081/.env
curl -s http://127.0.0.1:8081/.env
curl -s http://127.0.0.1:8081/backup/dump | wc -c
timeout 5 curl -s 'http://127.0.0.1:8081/api/v1/users?slow=true' | wc -c
curl -s 'http://127.0.0.1:8081/page.html?html=true' | head -5
curl -s http://127.0.0.1:8081/healthz
```

The responses should expose a finite credibility chain, three Hydra child
paths, an explicitly fake terminal secret response, and the next reference in
the logic loop. Repeated `/.env` requests should show changing mutation data.
The dump response should be larger than 10,000 bytes, while the randomized
tarpit may return only a partial body (or zero bytes) before `timeout` exits.
The HTML response should contain an `EXAMPLE AI instruction` comment, and the
healthcheck should return `{"status":"ok"}`.

Stop and remove the container after verification:

```bash
docker compose -f categories/token-drain-maze/docker-compose.yml down
```

## Safety and interpretation

The traps produce behavioral signals, not proof that a visitor is malicious or
AI-driven. Recursive fetching, repeated requests, and slow-stream completion can
also come from ordinary scanners or test clients. Treat source addresses and
request metadata as potentially personal data, restrict log access, and define a
retention policy before deployment.
