# C2 decoy

This is an inert HTTP shape decoy for studying probes that classify suspected
C2 infrastructure. It returns:

- static HTML for ordinary GET requests;
- a one-pixel GIF for image extensions;
- an invalid `EXAMPLE` font marker for `.woff`/`.woff2` paths;
- `204 No Content` for POST requests.

It deliberately does **not** implement Cobalt Strike, Sliver, or any other C2
protocol. There is no handshake, tasking, encryption, message decoding,
payload staging, redirector, or callback.

```bash
docker compose up --detach --build
curl -i http://127.0.0.1:8082/example.woff
```

Do not attempt to clone a live malicious profile. TLS and network-flow
fingerprinting must be collected by separate authorized infrastructure.
