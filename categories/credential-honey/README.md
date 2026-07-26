# Credential honey

This service records retrieval of filenames sought by credential harvesters:

- `/.env`, `/.env.production`, and `/config/.env`
- `/config.json`, `/credentials.json`
- `/.aws/credentials`
- `/.ssh/id_rsa`

All values are intentionally invalid and visibly prefixed with `EXAMPLE`.
Nothing calls a provider, validates a token, or contains usable key material.

```bash
./deploy.sh
curl http://127.0.0.1:8081/.env
docker compose logs --follow
```

`deploy.sh` verifies the synthetic tracking marker before building. It starts
only the local Compose project and does not copy files into an existing web
root.
