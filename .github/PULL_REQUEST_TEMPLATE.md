## Summary

Describe what changed, why it is needed, and which categories or tools are
affected.

## Related issue

Link an issue or write `N/A`.

## Change type

- [ ] Honeypot or analyzer behavior
- [ ] Infrastructure or developer tooling
- [ ] Documentation or translation
- [ ] Bug fix
- [ ] Other

## Validation

List the commands you ran and their results.

```text
make test
make lint
docker compose config --quiet
```

## Safety and privacy

- [ ] Decoy values are synthetic, invalid, and clearly marked as examples.
- [ ] The change does not add command execution, payload delivery, C2 tasking,
      credential validation, or access to third-party systems.
- [ ] Logging remains bounded and does not store credential values, cookies,
      authorization headers, query values, or request bodies.
- [ ] New network behavior is loopback-bound by default and uses least privilege.
- [ ] I considered false positives and did not claim AI attribution from HTTP
      behavior alone.

## Documentation

- [ ] Tests cover the change or I explained why tests are not applicable.
- [ ] User-facing documentation is updated or not required.
- [ ] English and Korean documentation remain consistent where applicable.

## Reviewer notes

Call out security-sensitive decisions, compatibility concerns, or areas that
need particular attention.
