# AI fingerprint analyzer

`analyzer.py` scores JSONL events produced by the honeypots. It is intentionally
conservative:

- known scanner User-Agents and rapid path diversity indicate automation;
- GraphQL and metadata signals increase confidence in protocol-aware testing;
- following the natural-language canary is treated as stronger agentic
  evidence;
- no rule attributes traffic to a vendor or model.

The rule file uses JSON syntax, which is valid YAML 1.2 and can be parsed with
Python's standard library.

```bash
python3 analyzer.py ../../events.jsonl
python3 analyzer.py --json web.jsonl graphql.jsonl agentic.jsonl
```

Scores are heuristic leads. A human using a scanner, a scripted crawler, NAT,
proxies, and spoofed headers can all confound classification.
