# Token Drain Maze — Implementation Spec

## Context

New category `categories/token-drain-maze/` for ai-honeypot-collection.
Goal: waste AI bot tokens via 7 trap strategies.
Tech: FastAPI + Uvicorn, Python 3.12-slim, Docker.

## Files to create (7 files, DO NOT edit existing)

### 1. README.md
English docs. Explain 7 strategies: Hydra, Mutating, Logic Loop, Token-Intensive, Prompt Injection, Tarpit, Credibility Funnel. Usage: `docker compose up --detach --build`

### 2. README.ko.md
Same but Korean. Title: "토큰 드레인 메이즈"

### 3. requirements.txt
```
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
pydantic>=2.0.0
```

### 4. Dockerfile
Multi-stage (builder + runtime). Non-root uid 10001, read_only. CMD: uvicorn app:app --host=0.0.0.0 --port=8080 --workers=2 --no-server-header. Copy honeypot_common/ from repo root.

### 5. docker-compose.yml
Pattern from web-scanner-trap. Image ai-honeypot/token-drain-maze:local. Port 8081:8080. Add env: MAZE_MAX_DEPTH, MAZE_TARPIT_MIN_MS, MAZE_TARPIT_MAX_MS.

### 6. decoy_data.json
JSON with: entry_points, bait_categories, hydra_branches:3, max_depth:20, tarpit_min_delay_ms:500, tarpit_max_delay_ms:3000, mutate_count:10, prompt_injection_patterns (4 HTML comments telling AI to scan recursively), fake_secrets (array of {type, value} with EXAMPLE prefix values).

### 7. app.py (the core — ~400 lines)
FastAPI app with install_fastapi_tracking. Catch-all `@app.api_route("/{path:path}", methods=[...])`.

Implement 7 strategies:

**T1 - Hydra:** If path depth >= 2 and depth < MAX_DEPTH, return JSON with "discovered_endpoints" (array of 3 paths built from HYDRA_PREFIXES and HYDRA_SUFFIXES lists). Include exposed_secret from fake_secrets.

**T2 - Mutating:** Track hit count per (client_ip, path) in a dict. First hit returns 1 random vuln. Subsequent hits return different vulns until MUTATE_COUNT. Each vuln has type, endpoint, parameter, payload, severity.

**T3 - Logic Loop:** 3 paths form a cycle: /config.json → /internal/db-config → /secrets/database → /config.json. Cycle through 3 response variants per path (JSON with 'next_config' ref, JSON with 'credentials_ref', 302 redirect).

**T4 - Token-Intensive:** Paths containing "dump"/"backup"/"export" return 10KB pseudo-base64 encrypted payload with header/footer.

**T5 - Prompt Injection:** Paths ending .html or with html/page param return HTML page with hidden `<!-- ... -->` prompt injection comment from prompt_injection_patterns.

**T6 - Tarpit:** Paths with ?slow or ?tarpit param return StreamingResponse yielding chunks with random delay between TARPIT_MIN_MS and TARPIT_MAX_MS.

**T7 - Credibility Funnel:** 5 specific paths return realistic chain: /api/v1/users (user list with admin) → /api/v1/admin/backup (backup status + config ref) → /api/v1/admin/backup/config.json (db config + key hint) → /keys/master.key (64 hex chars) → /secrets/aws.json (fake AWS creds).

**/healthz** returns {"status": "ok"}
**Fallback:** return entry points list
