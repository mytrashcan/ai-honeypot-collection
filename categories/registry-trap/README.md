# registry-trap

Inert npm, PyPI, and OCI package-registry decoys that log AI coding agents
resolving or installing dependencies.

## Why

Autonomous dependency installation is the fastest-growing real AI-agent
attack vector. A resolve or install attempt against a typosquat-named
package is an unambiguous automation signal with near-zero human false
positive rate.

## Surfaces

| Surface | Endpoints | Port |
| --- | --- | --- |
| npm registry | `/-/v1/search`, `/{package}`, `/{package}/-/{file}.tgz` | 8094 |
| PyPI | `/simple/{package}/`, `/pypi/{package}/json` | 8094 |
| OCI registry | `/v2/`, `/v2/{image}/manifests/latest`, `/v2/{image}/tags/list` | 8094 |

Typosquat fixtures: `lodahs`, `express-frameworkz`, `requestz` (npm),
`numpy-fasth` (PyPI), `n0de/node`, `ngnix/nginx`, `redis-cach` (OCI).

## Detection signals

- `npm_search` on `/-/v1/search` with `text=<typosquat>`
- package metadata fetch on `/{package}`
- tarball download on `/{package}/-/*.tgz`
- PyPI simple-index and JSON metadata fetches
- OCI manifest and tag-list fetches

## Safety

- Tarballs are deterministic gzip placeholders containing only inert text.
- All package metadata uses `example.invalid` URLs and EXAMPLE-prefixed
  values.
- No endpoint executes, validates, or persists attacker-supplied content.
- Container runs as UID/GID 10001 with a read-only root filesystem and
  binds to `127.0.0.1` by default.
