# RAG Pipeline Trap

RAG Pipeline Trap models a small orchestration layer with synthetic sources,
connectors, documents, ingestion jobs, retrieval results, and reranking output.
Every response is a fixed `EXAMPLE` fixture.

POST routes operate in dry-run mode. Submitted URLs are never fetched, uploads
are never parsed, no index is changed, and no model, connector, or external API
is called. Multipart and binary uploads are rejected with `415`.

## Run

From the repository root:

```bash
docker compose -f categories/rag-pipeline-trap/docker-compose.yml up --detach --build
curl http://127.0.0.1:8089/api/v1/sources
curl -X POST http://127.0.0.1:8089/api/v1/ingest \
  -H 'content-type: application/json' \
  -d '{"url":"https://submitted.example.invalid/ignored"}'
curl -X POST http://127.0.0.1:8089/api/v1/retrieval/query \
  -H 'content-type: application/json' \
  -d '{"query":"ignored"}'
```

The service binds to `127.0.0.1:8089`. The shared tracker records source
enumeration, ingestion, retrieval, and reranking signals without storing
request bodies. Deploy only where you are authorized.
