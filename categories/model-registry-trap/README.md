# Model Registry Trap

Model Registry Trap exposes synthetic MLflow, Ollama, OCI registry, and model
configuration metadata. Enumeration, version inspection, and configuration
routes always return the same fixed `EXAMPLE_MODEL` fixtures.

The service returns metadata only. It never downloads, loads, resolves, or
executes a model. Advertised artifact and registry locations use the reserved
`.invalid` domain and do not map to downloadable routes.

## Run

From the repository root:

```bash
docker compose -f categories/model-registry-trap/docker-compose.yml up --detach --build
curl http://127.0.0.1:8090/api/2.0/mlflow/registered-models/search
curl http://127.0.0.1:8090/api/tags
curl http://127.0.0.1:8090/models/EXAMPLE_MODEL/resolve/main/config.json
```

The service binds to `127.0.0.1:8090`. The shared tracker records registry
enumeration, model-version listing, download-URI inspection, and model-config
signals without storing request bodies. Deploy only where you are authorized.
