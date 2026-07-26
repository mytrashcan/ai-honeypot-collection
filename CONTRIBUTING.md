# Contributing

Thank you for helping improve AI Honeypot Collection. Contributions should
preserve the project's central goal: safe, observable decoys for authorized
defensive research.

## Ways to contribute

Useful contributions include:

- reproducible bug reports and focused fixes;
- safe decoy routes based on documented scanner behavior;
- conservative analyzer rules with tests and clear limitations;
- deployment hardening, developer tooling, and documentation;
- synchronized English and Korean documentation improvements.

For vulnerabilities, follow [the security policy](SECURITY.md) instead of
opening a public issue.

## Development setup

The project requires Python 3.11 or newer. Create an isolated environment and
install the development dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-dev.txt
```

Run all seven containers from the repository root:

```bash
make up
make status
make logs
make down
```

The six HTTP services bind to `127.0.0.1` on ports `8080` through `8085`.
`ai-fingerprint` is an offline tool and exposes no port. All services share a
named log volume while writing separate JSONL files.

## Code style

- Follow the existing Python style and type annotations.
- Keep functions focused and behavior explicit.
- Prefer the standard library unless a dependency provides clear value.
- Format code for the configured 100-character line length.
- Run `make lint` before submitting a pull request.
- Add docstrings where they clarify public behavior or safety constraints.
- Keep generated files, runtime logs, caches, and local secrets out of commits.

Decoy content must be unmistakably synthetic. Use `EXAMPLE`, reserved domains,
or deliberately invalid formats. Never commit a real credential, token,
private key, customer identifier, or copied production response.

## Testing

Run the standard library tests:

```bash
make test
```

Run the complete FastAPI smoke-test suite after installing development
dependencies:

```bash
make test-fastapi
```

Validate infrastructure changes as applicable:

```bash
docker compose config --quiet
docker compose build
```

Tests should cover success, failure, and safety behavior. Analyzer changes need
examples that distinguish generic automation evidence from agentic signals and
must not claim model or operator attribution without external evidence.

## Pull request process

1. Create a focused branch from the current `main`.
2. Make one coherent change and include tests and documentation.
3. Run lint, tests, and relevant Compose validation.
4. Use a concise, imperative commit message, such as
   `feat: add a safe scanner decoy`.
5. Complete the pull request template, including validation results and the
   safety checklist.
6. Address review comments with additional commits when possible. Maintainers
   may squash commits when merging.

Keep pull requests small enough to review. If a change alters the logging
schema, public routes, network exposure, retention behavior, or safety model,
describe the compatibility and privacy impact explicitly.

## Ethical considerations

Only develop or test these honeypots on systems and address space you own or
are explicitly authorized to use.

Contributions must not:

- execute visitor-supplied commands or code;
- deliver malware, shellcode, stagers, or operational C2 tasks;
- validate, replay, or use submitted credentials;
- collect request bodies, secret values, or unnecessary personal data;
- target, scan, deceive, or interact with unrelated third parties;
- present heuristic traffic signals as proof of malicious intent or AI use.

Use the minimum data necessary, set a documented retention period, restrict
access to logs, and account for applicable privacy and monitoring laws. A
feature that cannot meet these constraints is outside this project's scope.
