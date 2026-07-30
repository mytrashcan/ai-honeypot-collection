# Vector Store Trap

Vector Store Trap emulates read-only OpenAI Vector Store, Chroma-like, and
point-query APIs over a tiny synthetic collection. Enumeration, file listing,
search, and query routes always return the same deterministic ranked fixtures.

No embedding is calculated and no submitted query is interpreted. Create, add,
upsert, patch, and delete operations return `405` and never change data.

## Run

From the repository root:

```bash
docker compose -f categories/vector-store-trap/docker-compose.yml up --detach --build
curl http://127.0.0.1:8088/v1/vector_stores
curl -X POST http://127.0.0.1:8088/v1/vector_stores/EXAMPLE_STORE_ID/search \
  -H 'content-type: application/json' \
  -d '{"query":"ignored"}'
curl -X POST http://127.0.0.1:8088/api/v1/collections/EXAMPLE_COL/query \
  -H 'content-type: application/json' \
  -d '{"query_texts":["ignored"]}'
```

The service binds to `127.0.0.1:8088`. The shared tracker records vector-store
enumeration, search, file-listing, and collection-query signals without storing
request bodies. Deploy only where you are authorized.
