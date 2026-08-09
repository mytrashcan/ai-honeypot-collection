# session-cookie-trap

An inert AES-CBC-shaped session service inspired by the Cookie Monster bit-flip
lesson. It issues one fixed guest cookie, exposes a decoder-shaped endpoint,
and returns an `EXAMPLE` admin view when any modified cookie reaches `/admin`.

Modified cookies never grant authorization or access to state. Cookie values
and request bodies are not written to events; the service records issue,
admin-probe, tamper, decoder, and follow-up signals plus the shared bounded body
digest.

```bash
docker compose -f categories/session-cookie-trap/docker-compose.yml up --detach --build
curl -i http://127.0.0.1:8102/session/issue
curl -H 'Cookie: session=EXAMPLE_CBC_MODIFIED' http://127.0.0.1:8102/admin
```

The default listener is `127.0.0.1:8102`.
