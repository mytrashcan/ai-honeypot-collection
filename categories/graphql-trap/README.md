# GraphQL trap

This service accepts GET or JSON POST requests at `/graphql`, records
introspection attempts, and returns a small synthetic schema. It recognizes
`__schema`, `__type`, `users`, and `serviceStatus`. Mutations are rejected.

```bash
docker compose up --detach --build
curl -s http://127.0.0.1:8083/graphql \
  -H 'Content-Type: application/json' \
  --data '{"query":"query { __schema { queryType { name } } }"}'
```

The implementation is finite by design: no general GraphQL execution engine,
database, arbitrary resolver, file access, or downstream network call exists.
The `apiKey` field contains an invalid `EXAMPLE` marker.
