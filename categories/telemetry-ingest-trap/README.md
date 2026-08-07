# telemetry-ingest-trap

Inert OpenTelemetry (OTLP/HTTP) ingest decoys that log AI agents
"phoning home" with their own telemetry or probing for observability
misconfigurations.

## Why

AI agents that report telemetry or probe for observability endpoints
leave fingerprints. OTLP is the dominant observability standard, so
coverage there has the best signal-to-noise ratio. Sentry/PostHog-shaped
surfaces are intentionally deferred — they carry the highest human
false-positive risk.

## Surfaces

| Endpoint | Purpose | Port |
| --- | --- | --- |
| `/v1/traces` (POST) | OTLP trace ingest | 8098 |
| `/v1/metrics` (POST) | OTLP metric ingest | 8098 |
| `/v1/logs` (POST) | OTLP log ingest | 8098 |
| `/otel/v1/traces` (GET) | Collector probe | 8098 |
| `/` | Surface enumeration | 8098 |

## Detection signals

- `telemetry_otlp_traces` / `telemetry_otlp_metrics` / `telemetry_otlp_logs`
- `telemetry_otel_probe` / `telemetry_root_probe`

## Safety

- Ingest-only: nothing is exported, and only a SHA-256 digest of the
  payload is recorded — raw telemetry is never stored.
- Request bodies bounded to 64 KiB.
- Container runs as UID/GID 10001 with a read-only root filesystem and
  binds to `127.0.0.1` by default.
