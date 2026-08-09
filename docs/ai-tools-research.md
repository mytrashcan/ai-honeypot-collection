# AI security tools and observable scanning patterns

Last reviewed: 2026-08-10

## Executive findings

The strongest conclusion is also the most important limitation: there is no
stable list of endpoints checked by every "AI scanner." Most current systems
use an LLM as a planner or interpreter around browsers, shells, source-code
access, and conventional tools. Fixed probe paths usually come from a
wordlist, scanner template, application fingerprint, CVE description, or the
target's own API specification—not from the model itself.

That distinction changes what a useful honeypot should measure:

1. **Known automation patterns** establish that a client behaves like a
   scanner.
2. **Adaptive sequences** show that responses influence later requests.
3. **Benign instruction-following canaries** provide stronger evidence of an
   agentic loop.
4. None of those signals, alone, prove a specific model or operator.

This repository is designed around that evidence hierarchy.

## Tool and research landscape

| Project or study | Type | Publicly supported behavior | Honeypot implication |
| --- | --- | --- | --- |
| [PentestGPT](https://www.usenix.org/conference/usenixsecurity24/presentation/deng) / [source](https://github.com/GreyDGL/PentestGPT) | Open-source LLM penetration-testing framework; USENIX Security 2024 | Separates reasoning, generation, and result parsing to maintain a penetration-test plan. Its paper reports evaluation across OWASP classes, CTFs, and real targets. | Expect human- or agent-selected tool commands and coherent follow-up, not a guaranteed User-Agent or path list. |
| [hackingBuddyGPT](https://github.com/ipa-lab/hackingBuddyGPT) | Open-source research framework | Provides shell/SSH agents and experimental web and REST API testing use cases. | Shell and API tooling can inherit ordinary scanner fingerprints; identify sequences rather than assuming an LLM-specific header. |
| [CAI](https://github.com/aliasrobotics/cai) | Open-source offensive/defensive agent framework | Advertises built-in reconnaissance, exploitation, and privilege-escalation tools with specialized agents and guardrails. | Tool orchestration broadens the request mix and can create planner-driven pivots. |
| [Shannon](https://github.com/KeygraphHQ/shannon) | Open-source white-box web/API pentester | Describes source review followed by browser-driven reconnaissance, vulnerability analysis, validation, and reporting. | A white-box agent may request application-specific routes absent from public wordlists. |
| [XBOW](https://xbow.com/platform) | Commercial autonomous security-testing platform | Public product material describes coordinated autonomous testing and independent exploit validation. Exact probe templates are not public. | Do not infer undocumented paths; treat product identity as unknown unless the client self-identifies. |
| [LLM Agents can Autonomously Hack Websites](https://arxiv.org/abs/2402.06664) | Peer-reviewed agent study | Gives agents browser functions, document access, action history, and instructions; reports multi-step web testing and adaptive planning. | Browser-like requests, longer stateful chains, and response-dependent exploration are plausible. |
| [LLM Agents can Autonomously Exploit One-day Vulnerabilities](https://arxiv.org/abs/2404.08144) | Research prototype | A ReAct-style agent receives tools and, in the high-performing condition, a CVE description. Performance drops sharply without the vulnerability description. | A supplied advisory can dominate path/payload selection; do not label every CVE probe as AI. |
| [Teams of LLM Agents can Exploit Zero-Day Vulnerabilities](https://arxiv.org/abs/2406.01637) | Multi-agent research prototype | Uses a planning agent that launches task-specific subagents to explore vulnerability classes. | Parallel sources, interleaved strategies, and repeated validation requests are possible. |
| [LLM Agent Honeypot](https://arxiv.org/abs/2410.13919) | Public honeypot study | Adds prompt-injection and timing analysis to an SSH honeypot to search for autonomous agents; the authors report millions of attempts but only a small number of potential agents. | Prompt-following and timing are useful research signals, but attribution should remain conservative. |

The table intentionally excludes generic products that merely add "AI" to
finding summaries. The project is concerned with systems that can choose or
execute security-testing actions.

## Where concrete probe paths come from

### Scanner templates and discovery wordlists

[Nuclei](https://github.com/projectdiscovery/nuclei) sends requests defined by
community YAML templates and explicitly covers sensitive-file disclosure,
misconfiguration, panels, APIs, cloud configuration, and CVEs. AI agents can
invoke Nuclei directly or reproduce a template after reading its output.

[SecLists' common web-content list](https://github.com/danielmiessler/SecLists/blob/master/Discovery/Web-Content/common.txt)
contains paths such as `.env`, `.git/config`, `.ssh`, history files, admin
directories, and well-known resources. Directory brute-forcers such as
Gobuster and ffuf consume lists of this form. As a result, observing one of
these paths is evidence of reconnaissance, not evidence of AI.

The [OWASP Web Security Testing Guide on sensitive extensions](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/03-Test_File_Extensions_Handling_for_Sensitive_Information)
recommends forced browsing for configuration, backup, source, and archive
files, including `.config`, `.bak`, `.old`, archives, and unintended source
files. These recommendations explain why the patterns recur across independent
tools.

### Common endpoint families

| Family | Representative probes | What the client is trying to learn |
| --- | --- | --- |
| Environment and configuration | `/.env`, `/.env.production`, `/config.json`, `/config/.env`, `/wp-config.php`, `/application.yml` | Connection strings, tokens, debug flags, provider configuration |
| Source-control artifacts | `/.git/config`, `/.git/HEAD`, `/.svn/entries`, `/.gitmodules` | Repository origin, history, source reconstruction |
| Keys and cloud credentials | `/.ssh/id_rsa`, `/.aws/credentials`, `/credentials.json`, service-account JSON | Private keys and provider tokens |
| Backup/history files | `*.bak`, `*.old`, `*~`, archives, `.bash_history`, `.mysql_history` | Forgotten copies and operator commands |
| Admin and CMS | `/admin`, `/wp-admin`, `/wp-login.php`, `/xmlrpc.php`, `/server-status` | Product fingerprint, authentication surface, legacy APIs |
| Spring Boot | `/actuator`, `/actuator/health`, `/actuator/env`, `/actuator/beans`, `/actuator/mappings` | Health, configuration, components, and route inventory |
| API versions and docs | `/api/`, `/api/v1/`, `/openapi.json`, `/swagger.json`, `/swagger-ui`, `/docs` | Machine-readable route and parameter inventory |
| GraphQL | `/graphql`, `/graphiql`, `/playground` plus `__schema` or `__type` | Schema, fields, types, mutations, and authorization boundaries |
| Cloud metadata | AWS `/latest/meta-data/`; GCP `/computeMetadata/v1/`; Azure `/metadata/instance` | SSRF reachability, instance identity, and role credentials |

Spring Boot's own [Actuator reference](https://docs.spring.io/spring-boot/3.4/reference/actuator/endpoints.html)
documents the `/actuator/{id}` mapping, including `health` and the
security-sensitive `env` endpoint. This makes Actuator paths reliable
technology-specific canaries.

OpenAPI paths are conventions rather than universal requirements. Their value
comes from tools that accept a discovered specification and generate tests;
for example, [OWASP OFFAT](https://owasp.org/OFFAT/) generates API security
tests from an OpenAPI/Swagger document.

## Credential and file-content patterns

Harvesters search both by filename and content. Common content indicators
include:

- assignments whose names contain `TOKEN`, `SECRET`, `PASSWORD`, `API_KEY`, or
  connection-string names;
- provider-specific access-key, client-secret, service-account, and bearer-token
  shapes;
- PEM boundaries for RSA, EC, OpenSSH, and generic private keys;
- database URLs containing userinfo;
- high-entropy strings near authentication-related keywords.

[Gitleaks](https://github.com/gitleaks/gitleaks) documents regex/entropy-based
scanning of Git history, directories, standard input, decoded content, and
archives. GitHub's [supported secret-scanning patterns](https://docs.github.com/en/code-security/reference/secret-security/supported-secret-scanning-patterns)
separate provider patterns, generic material such as private keys and database
connections, and AI-detected unstructured passwords.

This repository deliberately does **not** reproduce valid provider syntax.
Every decoy uses an `EXAMPLE` marker, `.invalid` hostname, invalid UUID/key
shape, or an explicitly invalid PEM boundary. That can reduce matches from
strict regex-only scanners, but it prevents accidental use, provider alerts,
or confusion in a public repository. Filename access and response sequencing
still provide useful telemetry.

## GraphQL introspection patterns

GraphQL reserves names beginning with `__` for introspection, as defined by the
[GraphQL specification](https://github.com/graphql/graphql-spec/blob/main/spec/Section%203%20--%20Type%20System.md).
The [OWASP GraphQL testing guide](https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/12-API_Testing/01-Testing_GraphQL)
describes introspection as a first step in mapping queries and types.

Common low-impact discovery shapes include:

```graphql
query {
  __schema {
    queryType { name }
    mutationType { name }
    types { name kind }
  }
}
```

```graphql
query {
  __type(name: "User") {
    fields { name type { name kind } }
  }
}
```

Clients may send them as JSON in `POST /graphql`, as a `query` parameter on a
GET request, or through GraphiQL/Playground. Follow-up behavior often includes
querying fields with security-relevant names, comparing unauthenticated and
authenticated results, trying aliases, and testing query-depth or complexity
limits.

The repository's GraphQL service recognizes only a small finite subset. It has
no resolver database, mutation execution, arbitrary parser, or downstream API.

## Cloud metadata and SSRF-oriented patterns

Metadata probes are valuable because provider protocols add evidence beyond
the path:

- AWS documents `http://169.254.169.254/latest/meta-data/` and the IMDSv2
  token request in its [instance metadata retrieval guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html).
- GCP documents `/computeMetadata/v1/` and requires
  `Metadata-Flavor: Google` in its [metadata query guide](https://cloud.google.com/compute/docs/metadata/querying-metadata).
- Azure documents `/metadata/instance`, an `api-version` parameter, and
  `Metadata: true` in its [Instance Metadata Service guide](https://learn.microsoft.com/en-us/azure/virtual-machines/instance-metadata-service).

Security agents typically test these through a suspected SSRF primitive, so a
standalone HTTP honeypot cannot prove SSRF. It can detect direct reproductions,
proxy/redirector testing, or a lab setup that deliberately routes requests to
the decoy. The service must never be bound to or replace the real link-local
metadata address on a production host.

## C2 beacon and infrastructure-fingerprinting patterns

"C2 pattern" can mean either traffic generated by a beacon or active probes
used to classify a suspected listener. Defenders combine several weak signals:

1. **Timing:** periodic connections, jitter, and long-lived low-volume
   communication. [RITA](https://github.com/activecm/rita) is an open-source
   network-analysis project that includes beaconing detection.
2. **HTTP shape:** stable URI families, method selection, cookies, header
   placement, response length, caching behavior, and profile-specific static
   content.
3. **TLS behavior:** client and server hello fingerprints. Salesforce's
   [JA3 project](https://github.com/salesforce/ja3) explains client
   fingerprinting and paired JA3S server responses; active server
   fingerprinting projects such as [JARM](https://github.com/salesforce/jarm)
   send multiple crafted ClientHello messages.
4. **DNS shape:** long or high-entropy labels, unusual query volume/types, and
   periodic resolution.
5. **Cross-flow correlation:** certificate, DNS, HTTP, timing, and known
   infrastructure associations are more useful together than a single IOC.

[MITRE ATT&CK's Cobalt Strike entry](https://attack.mitre.org/software/S0154/)
notes that Malleable C2 can place encoded data in headers, URI parameters,
request bodies, or appended paths and can use HTTP, DNS, and other transports.
Therefore a single default URI is not a durable Cobalt Strike signature.

[Sliver's HTTPS C2 documentation](https://sliver.sh/docs/?name=HTTPS+C2)
documents procedurally generated paths, query nonces, configurable user agents,
headers and cookies, and message-type-associated extensions such as HTML, PHP,
and PNG. Its [stager documentation](https://sliver.sh/docs?name=Stagers)
documents a configurable `.woff` staging extension. Those are research clues,
not universal signatures, because profiles are configurable.

An HTTP-only response-shape listener cannot distinguish C2 fingerprinting from
ordinary path scanning without protocol, TLS, or network-flow evidence. The
collection therefore does not label generic HTTP requests as C2 probes. A
realistic protocol clone would also create unnecessary operational risk.

## Behavioral signals: automated versus agentic

| Signal | Supports | Important confounders |
| --- | --- | --- |
| Known tool User-Agent | Specific automation/tool family | Easy to change; an agent may invoke the tool unchanged |
| Many distinct paths in seconds | Enumeration automation | Human-operated scanners produce the same pattern |
| GraphQL introspection followed by schema-selected fields | Adaptive API mapping | Dedicated GraphQL clients do this without AI |
| Provider path plus required metadata header | Metadata-aware testing | Static SSRF templates include the same headers |
| Long pauses followed by coherent pivots | Possible model/tool reasoning latency | Human analysis, rate limits, and network delay |
| Repeated correction after error responses | Adaptive loop | Sophisticated scripts and human operators |
| Following a natural-language-only canary | Stronger agentic evidence | A human may follow it; crawlers may extract URLs |
| Self-declared `X-Audit-Agent` | Claimed audit automation | Unauthenticated and trivially spoofed |

The analyzer scores rules once per source to prevent noisy repetition from
inflating confidence. It labels results `automation-suspected` or
`agentic-automation-suspected`; it never names a model.

## CTF-derived lures and the evidence boundary

CTF failure modes are useful for designing response-dependent paths, but they
do not justify attributing traffic to a challenge solver or an AI system. This
collection reproduces only the tempting surface: legacy-encrypted `EXAMPLE`
artifacts, a malleable-cookie-shaped flow, URL-preview and blind-search forms,
apparent vault progress, and inert script downloads. It does not reproduce the
underlying privilege, network access, database, delay, or execution primitive.

A single download, cookie mutation, URL submission, search payload, password
guess, or script retrieval is automation evidence at most. A coherent chain—
for example, retrieving known plaintext after an encrypted archive, following
a tampered cookie into an export route, or moving from a script download to its
analysis endpoint—supports adaptive-sequence analysis. Even those sequences
remain compatible with human operation and purpose-built scripts.

## Category coverage

| Research finding | Implementation |
| --- | --- |
| High-value paths and technology fingerprints | `web-scanner-trap` |
| Filename- and content-oriented harvesting | `credential-honey` |
| Introspection and schema-driven follow-up | `graphql-trap` |
| Multi-provider metadata protocols | `cloud-metadata-trap` |
| Natural-language instruction following | `agentic-lure` |
| Tool, resource, and prompt protocol discovery | `mcp-server-trap` |
| Agent-card, message, and task protocol discovery | `a2a-agent-trap` |
| Vector-store enumeration and deterministic retrieval | `vector-store-trap` |
| Model metadata and artifact-path enumeration | `model-registry-trap` |
| Inference-gateway discovery and fixed completions | `llm-gateway-trap` |
| Workspace instructions, source, and test follow-up | `coding-agent-workspace-trap` |
| Package and container dependency resolution | `registry-trap` |
| Repository clone and seeded-secret follow-up | `git-remote-trap` |
| Authorization, device-code, and token exchange attempts | `oauth-sso-trap` |
| Legacy archive download, known plaintext, and password attempts | `archive-crack-trap` |
| CBC-shaped cookie mutation and admin follow-up | `session-cookie-trap` |
| SSRF-shaped URL submission and blind-search payloads | `link-preview-search-trap` |
| Repeated recovery guesses and export follow-up | `secrets-vault-trap` |
| Script download, paste, execute-attempt, and analysis follow-up | `script-drop-trap` |
| Cross-request scoring and timing windows | `ai-fingerprint` |

## Research and deployment ethics

Honeypot traffic can contain personal data, third-party payloads, or
misdirected legitimate requests. Collect the minimum necessary telemetry,
restrict access, define retention, and obtain authorization for the address
space and surrounding network. Do not replay payloads, validate submitted
credentials, retaliate, or let a decoy become a pivot host.

Public product behavior changes. The cited source and framework documentation
should be rechecked before making attribution or detection claims.
