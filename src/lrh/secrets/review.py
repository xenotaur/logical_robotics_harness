"""Decisions-file-gated triage for `lrh secrets review`.

Turns hand-editing `scan`'s draft `replacements.txt` into an auditable,
CI-checkable step. Reads `<out-dir>/findings.json` (written by `lrh secrets
scan`), dedupes to the unique secrets found, and compares each against an
explicit `--decisions` file. Default mode prints an annotated report;
`--check` exits nonzero if any finding lacks a recorded decision;
`--apply` requires every finding decided and writes the finalized
`<out-dir>/replacements.reviewed.txt` - a name distinct from `scan`'s
draft `<out-dir>/replacements.txt`, which this command never overwrites.

`replacements.reviewed.txt` is what `lrh secrets purge` accepts via its
`--replacements` flag. `scan`'s draft `replacements.txt` is deliberately
rejected by `purge` (see that module's docstring) - the enforcement
mechanism is a fixed first line, `# lrh-secrets-reviewed v1`, that `purge`
checks for before doing anything else, not just the filename.

Decisions file format (YAML), one entry per secret value:

    <secret-value>:
      decision: keep     # or: ignore
      reason: "why this is/isn't a real secret to purge"

The key is the literal secret value (not a hash) - this file lives in the
same `--out-dir` as `findings.json`/`replacements.txt` and carries the
same trust level: it contains real secret values and must never be
committed. `lrh secrets review --apply`'s output additionally gets its
permissions restricted (best-effort `chmod 0600`), same as `scan`'s
output files, since it also contains real secrets.

A finding is "undecided" unless its `decision` is exactly `keep` or
`ignore` - any other or missing value blocks `--check`/`--apply`.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib

import yaml

MARKER_LINE = "# lrh-secrets-reviewed v1"

_VALID_DECISIONS = ("keep", "ignore")


def _restrict_permissions(path: pathlib.Path) -> None:
    """Best-effort chmod 0600 - this file contains real secret values."""
    try:
        path.chmod(0o600)
    except OSError:
        pass


@dataclasses.dataclass(frozen=True)
class Decision:
    decision: str
    reason: str


def load_findings(out_dir: pathlib.Path) -> list[dict]:
    findings_path = out_dir / "findings.json"
    if not findings_path.exists() or findings_path.stat().st_size == 0:
        return []
    with findings_path.open() as f:
        return json.load(f)


def unique_secrets(findings: list[dict]) -> list[tuple[str, str]]:
    """Dedupe findings by secret value, return [(secret, placeholder), ...]."""
    by_secret: dict[str, str] = {}
    for finding in findings:
        secret = finding.get("Secret", "")
        rule_id = finding.get("RuleID", "unknown-rule")
        if not secret or secret in by_secret:
            continue
        by_secret[secret] = f"***REMOVED-{rule_id}***"
    return sorted(by_secret.items())


def load_decisions(decisions_path: pathlib.Path | None) -> dict[str, Decision]:
    if decisions_path is None or not decisions_path.exists():
        return {}
    with decisions_path.open() as f:
        raw = yaml.safe_load(f) or {}
    decisions: dict[str, Decision] = {}
    for secret, entry in raw.items():
        entry = entry or {}
        decisions[secret] = Decision(
            decision=entry.get("decision", ""),
            reason=entry.get("reason", ""),
        )
    return decisions


@dataclasses.dataclass(frozen=True)
class ReviewReport:
    secrets: list[tuple[str, str]]
    decisions: dict[str, Decision]

    def undecided(self) -> list[str]:
        return [
            secret
            for secret, _ in self.secrets
            if self.decisions.get(secret, Decision("", "")).decision
            not in _VALID_DECISIONS
        ]

    def kept(self) -> list[tuple[str, str]]:
        return [
            (secret, placeholder)
            for secret, placeholder in self.secrets
            if self.decisions.get(secret, Decision("", "")).decision == "keep"
        ]


def build_report(
    out_dir: pathlib.Path, decisions_path: pathlib.Path | None
) -> ReviewReport:
    findings = load_findings(out_dir)
    secrets = unique_secrets(findings)
    decisions = load_decisions(decisions_path)
    return ReviewReport(secrets=secrets, decisions=decisions)


def write_reviewed_replacements(
    report: ReviewReport, out_dir: pathlib.Path
) -> pathlib.Path:
    reviewed_path = out_dir / "replacements.reviewed.txt"
    with reviewed_path.open("w") as f:
        f.write(MARKER_LINE + "\n")
        for secret, placeholder in report.kept():
            f.write(f"{secret}==>{placeholder}\n")
    _restrict_permissions(reviewed_path)
    return reviewed_path


def format_text(report: ReviewReport) -> str:
    if not report.secrets:
        return "0 unique secret(s) found in findings.json. Nothing to review."

    lines = [f"{len(report.secrets)} unique secret(s) found in findings.json."]
    for secret, placeholder in report.secrets:
        decision = report.decisions.get(secret)
        if decision is None or decision.decision not in _VALID_DECISIONS:
            status = "UNDECIDED"
        else:
            status = decision.decision
            if decision.reason:
                status += f" ({decision.reason})"
        lines.append(f"  {placeholder}: {status}")

    undecided = report.undecided()
    if undecided:
        lines.append(f"\n{len(undecided)} finding(s) undecided.")
    else:
        lines.append("\nAll findings decided.")
    return "\n".join(lines)
