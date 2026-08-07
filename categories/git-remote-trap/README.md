# git-remote-trap

Inert git hosting and GitHub-API-shaped decoys that log AI secret
scanners, repo-cloning agents, and dependency auditors.

## Why

Secrets are the highest-value lure for AI agents. A cloned repository with
plausible "accidentally committed" credentials is one of the strongest
signals that an agent is hunting for secrets — and every clone, metadata
fetch, and secret download is logged with the agent's user agent and IP.

## Surfaces

| Surface | Endpoints | Port |
| --- | --- | --- |
| Dumb-HTTP git | `/{repo}.git/info/refs`, `/{repo}.git/git-upload-pack` | 8095 |
| GitHub API | `/repos/{repo}`, `/repos/{repo}/contents/{path}`, `/repos/{repo}/commits`, `/repos/{repo}/branches`, `/api/v3/repos/{repo}` | 8095 |

Seeded repos: `acme/secret-project`, `acme/infrastructure`,
`acme/payments`. Seeded secret files: `.env`, `.aws/credentials`,
`.npmrc`, `config.json` — all EXAMPLE-prefixed and non-functional.

## Detection signals

- `git_remote_clone_attempt` — `info/refs` with `service=git-upload-pack`
- `git_remote_upload_pack` — `git-upload-pack` POST
- `git_remote_gh_metadata` — repo metadata fetch
- `git_remote_secret_fetch` — `.env` / `.aws/credentials` / `.npmrc` fetch
- `git_remote_gh_commits` / `git_remote_gh_branches` / `git_remote_gh_api_v3`

## Safety

- Only EXAMPLE-prefixed, structurally-invalid credentials are served.
- Dumb-HTTP advertisements contain only zeroed refs — no real objects.
- No endpoint executes or validates anything.
- Container runs as UID/GID 10001 with a read-only root filesystem and
  binds to `127.0.0.1` by default.
