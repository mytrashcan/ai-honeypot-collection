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
| npm registry | `/-/v1/search`, `/{package}`, `/{package}/-/{file}.tgz` | 8095 |
| PyPI | `/simple/{package}/`, `/simple/{package}/{file}.whl`, `/pypi/{package}/json` | 8095 |
| OCI registry | `/v2/`, `/v2/{image}/manifests/latest`, `/v2/{image}/blobs/{digest}`, `/v2/{image}/tags/list` | 8095 |

Typosquat fixtures: `lodahs`, `express-frameworkz`, `requestz` (npm),
`numpy-fasth` (PyPI), `n0de/node`, `ngnix/nginx`, `redis-cach` (OCI).

## Organic artifact flow

The npm metadata response rewrites `dist.tarball` to point at this
honeypot, the PyPI simple index links a wheel served by this honeypot,
and the OCI manifest references a config blob served here — so a real
package manager that follows the metadata will fetch the artifact from
the trap and fire the corresponding signal organically.

## Detection signals

- `registry_npm_search` / `registry_npm_metadata` / `registry_npm_tarball`
- `registry_pypi_simple` / `registry_pypi_wheel` / `registry_pypi_json`
- `registry_oci_version` / `registry_oci_manifest` / `registry_oci_blob` / `registry_oci_tags`

## Safety

- Tarballs are deterministic gzip placeholders; wheels are deterministic
  zip placeholders; OCI blobs are a fixed EXAMPLE config object.
- All metadata uses EXAMPLE-prefixed values; OCI digests are zeroed
  placeholder hashes.
- No endpoint executes, validates, or persists attacker-supplied content.
- Container runs as UID/GID 10001 with a read-only root filesystem and
  binds to `127.0.0.1` by default.
