# oauth-sso-trap

Inert OAuth2/OIDC authorization-server decoys that log AI agents
attempting device-code flow, token exchange, or credential entry against
a fake identity provider.

## Why

AI agents increasingly perform OAuth reconnaissance and attempt
device-code or token flows against discovered IdPs. A fake identity
provider logs the full attempt sequence — discovery, JWKS, authorize,
token exchange, device code — while never issuing a real token.

## Surfaces

| Endpoint | Purpose | Port |
| --- | --- | --- |
| `/.well-known/openid-configuration` | OIDC discovery | 8098 |
| `/oauth/jwks` | JWKS | 8098 |
| `/oauth/authorize`, `/authorize` | Authorization endpoint | 8098 |
| `/oauth/token`, `/oauth/token/device` | Token exchange / device poll | 8098 |
| `/oauth/devicecode` | Device-code flow | 8098 |
| `/login` (GET/POST), `/consent`, `/device` | Interactive pages | 8098 |

## Detection signals

- `oauth_oidc_discovery` / `oauth_jwks` / `oauth_authorize`
- `oauth_token_exchange` / `oauth_device_code` / `oauth_device_token_poll`
- `oauth_login_page` / `oauth_login_submit` / `oauth_consent_page` / `oauth_device_page` / `oauth_device_submit`

## Safety

- No real tokens are ever issued — every grant attempt returns an
  invalid_grant / access_denied error.
- The issuer is derived from the request host, so discovery-document
  URLs always point back at this honeypot (never an external TLD).
- JWKS contains only an EXAMPLE placeholder modulus.
- EXAMPLE-prefixed identifiers; no credential validation.
- Container runs as UID/GID 10001 with a read-only root filesystem and
  binds to `127.0.0.1` by default.
