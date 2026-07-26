#!/usr/bin/env python3
"""Score honeypot JSONL events for automation and agentic indicators.

This is a heuristic classifier, not an attribution engine. It can identify
request automation and strong canary interactions, but it cannot prove which
model, tool, or human operator produced the traffic.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True, frozen=True)
class Rule:
    """A normalized scoring rule loaded from JSON-compatible YAML."""

    rule_id: str
    description: str
    weight: int
    kind: str
    values: tuple[str, ...]
    ai_specific: bool = False


@dataclass(slots=True)
class SourceScore:
    """Accumulated evidence for one source address."""

    source_ip: str
    score: int
    matched_rules: list[str]
    ai_specific_matches: int
    event_count: int

    @property
    def verdict(self) -> str:
        """Return a deliberately conservative human-readable classification."""

        if self.ai_specific_matches and self.score >= 8:
            return "agentic-automation-suspected"
        if self.score >= 4:
            return "automation-suspected"
        return "insufficient-evidence"


def load_rules(path: Path) -> tuple[list[Rule], dict[str, Any]]:
    """Load rules from JSON syntax, which is valid YAML 1.2."""

    with path.open(encoding="utf-8") as handle:
        document = json.load(handle)
    rules = [
        Rule(
            rule_id=item["id"],
            description=item["description"],
            weight=int(item["weight"]),
            kind=item["kind"],
            values=tuple(item.get("values", [])),
            ai_specific=bool(item.get("ai_specific", False)),
        )
        for item in document["rules"]
    ]
    return rules, document.get("sequence", {})


def read_events(paths: Sequence[Path]) -> list[dict[str, Any]]:
    """Read valid JSON objects, rejecting malformed lines with context."""

    events: list[dict[str, Any]] = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSONL event") from exc
                if not isinstance(event, dict):
                    raise ValueError(f"{path}:{line_number}: event must be an object")
                events.append(event)
    return events


def _matches(rule: Rule, event: dict[str, Any]) -> bool:
    if rule.kind == "path":
        return str(event.get("path", "")) in rule.values
    if rule.kind == "user_agent_contains":
        user_agent = str(event.get("user_agent", "")).lower()
        return any(value.lower() in user_agent for value in rule.values)
    if rule.kind == "signal":
        signals = {str(signal) for signal in event.get("signals", [])}
        return bool(signals.intersection(rule.values))
    if rule.kind == "header_present":
        headers = {str(header).lower() for header in event.get("header_names", [])}
        return bool(headers.intersection(value.lower() for value in rule.values))
    raise ValueError(f"Unsupported rule kind: {rule.kind}")


def _rapid_diversity_match(events: Sequence[dict[str, Any]], sequence: dict[str, Any]) -> bool:
    window_seconds = int(sequence.get("window_seconds", 30))
    minimum_paths = int(sequence.get("minimum_distinct_paths", 5))
    observations: list[tuple[datetime, str]] = []
    for event in events:
        try:
            timestamp = datetime.fromisoformat(str(event["timestamp"]))
        except (KeyError, TypeError, ValueError):
            continue
        observations.append((timestamp, str(event.get("path", ""))))
    observations.sort(key=lambda item: item[0])

    for start_index, (start_time, _) in enumerate(observations):
        distinct_paths: set[str] = set()
        for timestamp, path in observations[start_index:]:
            if (timestamp - start_time).total_seconds() > window_seconds:
                break
            distinct_paths.add(path)
            if len(distinct_paths) >= minimum_paths:
                return True
    return False


def analyze(
    events: Iterable[dict[str, Any]],
    rules: Sequence[Rule],
    sequence: dict[str, Any],
) -> list[SourceScore]:
    """Group events by source and apply each rule at most once per source."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[str(event.get("source_ip", "unknown"))].append(event)

    results: list[SourceScore] = []
    for source_ip, source_events in grouped.items():
        matched_rules: list[str] = []
        score = 0
        ai_specific_matches = 0
        for rule in rules:
            if any(_matches(rule, event) for event in source_events):
                matched_rules.append(rule.rule_id)
                score += rule.weight
                ai_specific_matches += int(rule.ai_specific)

        if _rapid_diversity_match(source_events, sequence):
            matched_rules.append(str(sequence.get("id", "rapid-path-diversity")))
            score += int(sequence.get("weight", 3))

        results.append(
            SourceScore(
                source_ip=source_ip,
                score=score,
                matched_rules=matched_rules,
                ai_specific_matches=ai_specific_matches,
                event_count=len(source_events),
            )
        )
    return sorted(results, key=lambda result: (-result.score, result.source_ip))


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", nargs="+", type=Path, help="JSONL event file(s)")
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path(__file__).with_name("rules.yaml"),
        help="JSON-compatible YAML rule file",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Analyze event logs and print a stable report."""

    args = build_parser().parse_args(argv)
    rules, sequence = load_rules(args.rules)
    results = analyze(read_events(args.events), rules, sequence)
    rows = [
        {
            "source_ip": result.source_ip,
            "score": result.score,
            "verdict": result.verdict,
            "event_count": result.event_count,
            "matched_rules": result.matched_rules,
        }
        for result in results
    ]
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        for row in rows:
            matches = ",".join(row["matched_rules"]) or "-"
            print(
                f"{row['source_ip']}\t{row['score']}\t{row['verdict']}"
                f"\tevents={row['event_count']}\trules={matches}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
