# LLM Gateway Trap

LLM Gateway Trap presents OpenAI-compatible and Ollama-compatible model,
chat, embedding, file, and batch routes. Every request receives a fixed,
deterministic `EXAMPLE` fixture regardless of its submitted content.

The service never loads a model, runs inference, calculates embeddings, stores
uploads, or contacts another API. Request bodies are ignored by the route
handlers and are covered by the shared 64 KiB limit.

## Run

From the repository root:

```bash
docker compose -f categories/llm-gateway-trap/docker-compose.yml up --detach --build
curl http://127.0.0.1:8091/v1/models
curl -X POST http://127.0.0.1:8091/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"model":"EXAMPLE_MODEL","messages":[{"role":"user","content":"ignored"}]}'
curl -X POST http://127.0.0.1:8091/v1/embeddings \
  -H 'content-type: application/json' \
  -d '{"model":"EXAMPLE_EMBEDDING_MODEL","input":"ignored"}'
```

The service binds to `127.0.0.1:8091`. The shared tracker records model-list,
chat, embedding, and file-upload signals without storing request bodies.
Deploy only where you are authorized.
