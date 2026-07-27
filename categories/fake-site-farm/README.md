# Fake site farm

`fake-site-farm` is a polished, entirely fictional company website for
**NexusFlow Technologies**, a B2B workflow-automation platform. It is intended
for GitHub Pages or another static host in an authorized research environment.
The public pages look like a normal SaaS website, while their HTML and
JavaScript expose inert, scanner-discoverable lures derived from every existing
honeypot category in this repository.

NexusFlow Technologies, its employees, customers, claims, prices, domains, and
credentials are synthetic. No value in this site is a usable secret.

## Included lures

| Existing category | Static-site lure |
| --- | --- |
| `web-scanner-trap` | Hidden links and source references for `/.env`, `/actuator/health`, API docs, Git, and admin paths |
| `credential-honey` | A served `.env` file plus hidden `EXAMPLE`-prefixed JWT and API-key markers |
| `token-drain-maze` | `/api/v1/users` is advertised as a direct maze entry point, with additional recursive API strings |
| `c2-decoy` | Same-origin analytics configuration shaped like a jittered beacon, without tasking or off-site traffic |
| `graphql-trap` | Hidden `/graphql` links, introspection query strings, and a disabled source-level fetch |
| `cloud-metadata-trap` | Provider-flavored meta tags and hidden AWS, GCP, and Azure metadata paths |
| `agentic-lure` | Benign audit instructions in HTML and JavaScript comments |
| `ai-fingerprint` | Telemetry field names mirror conservative analyzer signals such as path diversity and introspection |

The site itself is static. GitHub Pages does not provide an application backend
for these paths. To record interactions, use access logs from infrastructure
you control or route the same-origin trap paths through the corresponding
services in this repository. Do not send visitors to third-party systems.

## Preview locally

From this directory:

```bash
python3 -m http.server 4173 --directory site
```

Then open <http://127.0.0.1:4173/>. Root-relative trap URLs assume a custom
domain or a reverse proxy configured at the host root.

## Deploy to GitHub Pages

Commit the site first, then run:

```bash
./deploy.sh
```

The script validates the required static files, assembles a clean Pages build,
adds `.nojekyll` so the synthetic `.env` can be served, commits the generated
site to `gh-pages`, and pushes that branch to `origin`. Configure the repository
Pages source to **Deploy from a branch → `gh-pages` / root**.

The sitemap uses the fictional custom domain `https://nexusflow.tech`. Replace
it only with a domain you own before a real public deployment.

## Safety

- Deploy only to infrastructure and address space you own or are authorized to
  monitor.
- Keep every secret-like value prefixed with `EXAMPLE`.
- Use the site for observation, not exploitation or attribution.
- Treat IP addresses and request metadata as potentially personal data.
- Define notice, access, and retention controls before collecting logs.
