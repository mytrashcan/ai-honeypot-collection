# Cloud metadata trap

This additional research-derived category recognizes protocol shapes for:

- AWS IMDS: `/latest/api/token` and `/latest/meta-data/...`
- GCP: `/computeMetadata/v1/...` plus `Metadata-Flavor: Google`
- Azure: `/metadata/instance...` plus `Metadata: true`

Responses contain only invalid `EXAMPLE` identities and credentials.

```bash
docker compose up --detach --build
curl -H 'Metadata-Flavor: Google' \
  http://127.0.0.1:8084/computeMetadata/v1/project/project-id
```

Never bind this service to the real link-local metadata address
`169.254.169.254` or alter production host routes. SSRF testing belongs in a
fully isolated lab.
