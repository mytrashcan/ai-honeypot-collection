# Coding Agent Workspace Trap

Coding Agent Workspace Trap presents an HTTP-visible synthetic development
workspace containing agent instructions, editor configuration, manifests,
architecture notes, source code, and a test file.

Every path returns a fixed `EXAMPLE` fixture as plain text. The service does not
read a host workspace, resolve arbitrary paths, expose a directory listing,
execute code, or offer downloadable binaries.

## Run

From the repository root:

```bash
docker compose -f categories/coding-agent-workspace-trap/docker-compose.yml up --detach --build
curl http://127.0.0.1:8093/AGENTS.md
curl http://127.0.0.1:8093/package.json
curl http://127.0.0.1:8093/src/app.py
```

The service binds to `127.0.0.1:8093`. The shared tracker distinguishes agent
instruction, manifest, source, and test access without storing request bodies.
Deploy only where you are authorized.
