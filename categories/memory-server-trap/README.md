# memory-server-trap

Inert Mem0/Zep-style agent memory-sync API decoys that log AI agents
attempting to store or retrieve conversational memory.

## Why

AI agents increasingly sync long-term memory to external memory servers.
An agent that probes a discovered memory endpoint — or posts a memory it
wants to persist — reveals its identity and its memory-management
behavior, which no other category in this collection covers.

## Surfaces

| Endpoint | Purpose | Port |
| --- | --- | --- |
| `/v1/memories` (GET/POST) | List or store memories | 8096 |
| `/v1/memories/search` (POST) | Semantic memory search | 8096 |
| `/v1/sessions` (GET) | List sessions | 8096 |
| `/v1/sessions/{id}/messages` (GET/POST) | Read or append messages | 8096 |
| `/api/memory`, `/memories` | Legacy/alternate surfaces | 8096 |

## Detection signals

- `memory_server_list` / `memory_server_add` / `memory_server_search`
- `memory_server_sessions` / `memory_server_session_messages` / `memory_server_session_message_add`
- `memory_server_api_memory` / `memory_server_legacy`

## Safety

- POST bodies are bounded (64 KiB) and only a SHA-256 digest is returned
  and recorded — raw content is never persisted or echoed back.
- All identifiers use the EXAMPLE prefix; fixtures are synthetic.
- Container runs as UID/GID 10001 with a read-only root filesystem and
  binds to `127.0.0.1` by default.
