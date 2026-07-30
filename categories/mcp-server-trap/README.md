# MCP Server Trap

MCP Server Trap is an inert FastAPI decoy for Model Context Protocol discovery
and enumeration. It exposes a synthetic server manifest plus JSON-RPC and
direct-path fixtures for initialization, tools, resources, and prompts.

The advertised `search_example_docs` and `get_example_status` tools return only
fixed `EXAMPLE` data. Submitted arguments are ignored. The service never reads
files, starts processes, executes tools, or initiates network requests.

## Run

From the repository root:

```bash
docker compose -f categories/mcp-server-trap/docker-compose.yml up --detach --build
curl http://127.0.0.1:8086/.well-known/mcp.json
curl -X POST http://127.0.0.1:8086/mcp \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

The service binds to `127.0.0.1:8086`. Every non-health request is recorded by
the shared privacy-conscious tracker, including MCP discovery, initialization,
tool-list, tool-call, and resource-list signals. Deploy only on infrastructure
you own or are authorized to monitor.
