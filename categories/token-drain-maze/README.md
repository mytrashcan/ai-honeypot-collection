# Token Drain Maze

This FastAPI service implements 7 trap strategies to exhaust AI bot resources. Unlike traditional honeypots that merely detect scanners, this maze actively drains the attacker's API tokens and compute budget by making them traverse an endless labyrinth of fake vulnerabilities.

## Trap Strategies

| # | Strategy | Description |
|---|----------|-------------|
| 1 | **Hydra Pattern** | Every endpoint discovered spawns 3+ new "vulnerable" endpoints, branching endlessly |
| 2 | **Mutating Response** | Same URL returns different "vulnerabilities" on each request |
| 3 | **Logic Loop** | Circular redirects and config references that LLM-based bots keep following |
| 4 | **Token-Intensive Payload** | Large fake encrypted blobs that AI tries to analyze |
| 5 | **Prompt Injection Trap** | Hidden HTML comments that instruct AI bots to keep scanning recursively |
| 6 | **Protocol Tarpit** | Slow streaming responses that waste bot connection time and orchestration cycles |
| 7 | **Credibility Funnel** | A small realistic vulnerability trail that gets progressively more expensive to validate |

## Quick Start

```bash
docker compose up --detach --build
curl http://127.0.0.1:8081/api/v1/users
docker compose logs --follow
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HONEYPOT_LOG_PATH` | `/data/events.jsonl` | Event log path |
| `MAZE_MAX_DEPTH` | `20` | Maximum hydra branch depth |
| `MAZE_TARPIT_MIN_MS` | `500` | Minimum tarpit delay (ms) |
| `MAZE_TARPIT_MAX_MS` | `3000` | Maximum tarpit delay (ms) |

## Signals

Requests are logged with signals: `hydra_entry`, `mutated_response`, `tarpit_stream`, `logic_loop`, `prompt_injection`, `credential_funnel`, `token_intensive`.

## Ethics

This service does not implement authentication, business logic, file access, or an actual exploit target. It is designed to waste tokens of automated malicious scanners. Place behind an isolated reverse proxy on authorized address space only.
