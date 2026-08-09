# archive-crack-trap

An inert archive vault inspired by the ZipCrypto known-plaintext lesson. It
serves a real traditional-PKZIP encrypted archive, the matching `EXAMPLE`
plaintext sample, a 7z-shaped placeholder, and a password-unlock endpoint.

The encrypted entry contains only fixed `EXAMPLE` text. The service never runs
cracking tools, accepts uploads, or releases credentials. It records separate
signals for listing, archive downloads, known-plaintext retrieval, status
checks, and password attempts; submitted bodies are represented only by the
shared bounded digest.

```bash
docker compose -f categories/archive-crack-trap/docker-compose.yml up --detach --build
curl http://127.0.0.1:8101/vault
curl --output EXAMPLE-backup.zip \
  http://127.0.0.1:8101/downloads/EXAMPLE-backup.zip
```

The default listener is `127.0.0.1:8101`.
