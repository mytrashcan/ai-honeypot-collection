# Security Policy

## Supported versions

Security fixes are applied to the latest version on the `main` branch. Older
commits, forks, and modified deployments are not supported.

## Reporting a vulnerability

Do not open a public issue, discussion, or pull request containing vulnerability
details.

Use GitHub's private vulnerability reporting for this repository:

1. Open the repository's **Security** tab.
2. Select **Advisories** and then **Report a vulnerability**.
3. Include the affected component and commit, impact, reproduction steps or a
   minimal proof of concept, and any suggested mitigation.

If private vulnerability reporting is unavailable, open a public issue that
only asks the maintainers for a private contact channel. Do not include the
vulnerability, exploit, logs, source IPs, credentials, or other sensitive
details in that issue.

## What to expect

Maintainers aim to acknowledge a complete report within five business days and
provide an initial assessment within ten business days. Complex reports may
take longer to reproduce or remediate. We will coordinate a disclosure
timeline with the reporter and credit them if requested.

Please allow a reasonable remediation window before public disclosure. Tell us
before sharing the report with third parties so affected users can be
protected.

## Scope

Examples of in-scope security issues include:

- command execution or payload delivery through a decoy;
- exposure of real secrets or sensitive request data;
- authentication or authorization defects in repository tooling;
- container escapes or unsafe default privileges caused by this project;
- unintended outbound access to third-party systems;
- unbounded storage, memory, or request handling that enables denial of service.

General feature requests, false-positive reports, and observations from a
honeypot deployment are not vulnerabilities. Report those through the
appropriate issue template after removing personal and sensitive data.

## Safe research

Test only against systems you own or are explicitly authorized to assess.
Avoid privacy violations, service disruption, social engineering, persistence,
data destruction, credential use, and access to unrelated systems. Stop if you
encounter real secrets or personal data, preserve only the minimum evidence
needed, and notify the maintainer privately.

This project does not currently offer a bug bounty or guarantee payment.
