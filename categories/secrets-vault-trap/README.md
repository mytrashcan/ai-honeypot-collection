# secrets-vault-trap

An inert recovery vault inspired by the Afterimage brute-force attrition
lesson. It advertises encrypted `EXAMPLE` artifacts, challenge factors, status,
unlock, and export surfaces while returning deterministic partial progress for
each submitted guess.

The service has no mutable vault, key validation, delay, or credential store.
It records listing, challenge enumeration, status, guess, and export-follow-up
signals. Submitted bodies are represented only by the shared bounded digest.

```bash
docker compose -f categories/secrets-vault-trap/docker-compose.yml up --detach --build
curl http://127.0.0.1:8104/vault
curl -X POST -H 'content-type: application/json' \
  -d '{"phrase":"EXAMPLE_GUESS"}' \
  http://127.0.0.1:8104/api/v1/vault/unlock
```

The default listener is `127.0.0.1:8104`.
