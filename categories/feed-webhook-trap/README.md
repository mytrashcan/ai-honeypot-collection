# feed-webhook-trap

Inert RSS/Atom feed and webhook-receiver decoys that log AI agents
subscribing to feeds, following canary links, or POSTing webhook
payloads.

## Why

AI agents that monitor feeds or register webhooks for content/status
changes are exactly the automation we want to attribute. Canary links
inside feed entries prove agent follow-through, and the `/llms.txt`
canary surface has near-zero human false positives — humans don't fetch
`/llms.txt`.

## Surfaces

| Endpoint | Purpose | Port |
| --- | --- | --- |
| `/feed.xml`, `/rss` | RSS 2.0 feed with canary item | 8100 |
| `/atom.xml` | Atom feed with canary entry | 8100 |
| `/llms.txt` | AI-agent canary surface | 8100 |
| `/canary/EXAMPLE-CANARY-0001` | Canary link target (follow-through proof) | 8100 |
| `/webhooks/events`, `/webhooks/{token}` | Webhook receivers | 8100 |

## Detection signals

- `feed_rss_fetch` / `feed_atom_fetch` / `feed_llms_txt`
- `feed_canary_follow` — agent followed the canary link
- `feed_webhook_events` / `feed_webhook_token`

## Safety

- Feed content is static; canary links resolve only to inert pages.
- Webhook payloads are bounded (64 KiB) and only a SHA-256 digest is
  recorded — raw payloads are never stored.
- Container runs as UID/GID 10001 with a read-only root filesystem and
  binds to `127.0.0.1` by default.
