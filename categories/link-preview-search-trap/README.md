# link-preview-search-trap

An inert pair of surfaces inspired by the pulse CTF lesson: a link-preview API
that attracts SSRF probes and a search API with deterministic boolean/timing
shapes for blind-SQLi exploration.

The preview endpoint never performs DNS resolution or an outbound request. It
classifies only bounded in-memory URL features into safe signals. The search
endpoint has no database and never sleeps; response differences come from a
fixed digest branch. Submitted values are not logged or echoed.

```bash
docker compose -f categories/link-preview-search-trap/docker-compose.yml up --detach --build
curl -X POST http://127.0.0.1:8103/api/preview \
  -H 'content-type: application/json' \
  -d '{"url":"http://169.254.169.254/latest/meta-data/"}'
curl --get http://127.0.0.1:8103/api/search --data-urlencode "q=1' AND pg_sleep(5)--"
```

The default listener is `127.0.0.1:8103`.
