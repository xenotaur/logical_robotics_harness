"""Decisions-file-gated triage for `lrh secrets review`.

Turns hand-editing `scan`'s draft `replacements.txt` into an auditable,
CI-checkable step. Reads `<out-dir>/findings.json` (written by `lrh secrets
scan`), dedupes to the unique secrets found, and compares each against an
explicit `--decisions` file. Default mode prints an annotated report;
`--check` exits nonzero if any finding lacks a recorded decision;
`--apply` requires every finding decided and writes the finalized
`<out-dir>/replacements.reviewed.txt` - a name distinct from `scan`'s
draft `<out-dir>/replacements.txt`, which this command never overwrites.

`replacements.reviewed.txt` is intended to be the file a future
`lrh secrets purge` command will accept via its `--replacements` flag,
rejecting `scan`'s draft `replacements.txt` outright (`purge` does not
exist in this repo yet - see `WI-SECRETS-PURGE`). The enforcement
mechanism `purge` will use is a fixed first line, `# lrh-secrets-reviewed
v1`, checked before doing anything else, not just the filename.

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

A finding is "undecided" unless it has both a `decision` of exactly
`keep` or `ignore` *and* a non-empty `reason` - a decision with no
recorded rationale is not auditable and does not count as decided.

Missing or malformed inputs (`--out-dir` not a directory, `findings.json`
absent, `findings.json`/the decisions file not parseable, a decisions
entry not shaped as expected) raise `ReviewInputError` rather than
letting a raw parse exception or stack trace reach the user - an
*existing but empty* `findings.json` is a legitimate clean scan and is
not an error; a *missing* one means `scan` was never run against this
`--out-dir` and must not be silently treated as "nothing found".
"""

from __future__ import annotations

import dataclasses
import json
import pathlib

import yaml

MARKER_LINE = "# lrh-secrets-reviewed v1"

_VALID_DECISIONS = ("keep", "ignore")


class ReviewInputError(Exception):
    """Raised for a missing/malformed --out-dir, findings.json, or decisions file."""


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

    def is_decided(self) -> bool:
        return self.decision in _VALID_DECISIONS and bool(self.reason.strip())


_UNDECIDED = Decision("", "")


def load_findings(out_dir: pathlib.Path) -> list[dict]:
    if not out_dir.is_dir():
        raise ReviewInputError(f"{out_dir} is not a directory")
    findings_path = out_dir / "findings.json"
    if not findings_path.exists():
        raise ReviewInputError(
            f"{findings_path} not found -- run `lrh secrets scan --out-dir "
            f"{out_dir}` first"
        )
    if findings_path.stat().st_size == 0:
        return []
    try:
        with findings_path.open() as f:
            return json.load(f)
    except json.JSONDecodeError as err:
        raise ReviewInputError(f"{findings_path} is not valid JSON: {err}") from err


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
    if decisions_path is None:
        return {}
    if not decisions_path.exists():
        raise ReviewInputError(f"{decisions_path} not found")
    try:
        with decisions_path.open() as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as err:
        raise ReviewInputError(f"{decisions_path} is not valid YAML: {err}") from err
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ReviewInputError(
            f"{decisions_path} must be a YAML mapping of "
            "<secret> -> {decision, reason}"
        )
    decisions: dict[str, Decision] = {}
    for secret, entry in raw.items():
        if entry is None:
            entry = {}
        if not isinstance(entry, dict):
            raise ReviewInputError(
                f"{decisions_path}: entry for a secret must be a mapping with "
                f"decision/reason keys, got {entry!r}"
            )
        decisions[secret] = Decision(
            decision=str(entry.get("decision", "")),
            reason=str(entry.get("reason", "")),
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
            if not self.decisions.get(secret, _UNDECIDED).is_decided()
        ]

    def kept(self) -> list[tuple[str, str]]:
        return [
            (secret, placeholder)
            for secret, placeholder in self.secrets
            if self.decisions.get(secret, _UNDECIDED).is_decided()
            and self.decisions[secret].decision == "keep"
        ]


def build_report(
    out_dir: pathlib.Path, decisions_path: pathlib.Path | None
) -> ReviewReport:
    findings = load_findings(out_dir)
    secrets = unique_secrets(findings)
    decisions = load_decisions(decisions_path)
    return ReviewReport(secrets=secrets, decisions=decisions)


def invalidate_stale_reviewed(out_dir: pathlib.Path) -> None:
    """Remove a leftover replacements.reviewed.txt from an earlier successful
    --apply, so a later failed --apply in the same --out-dir never leaves a
    stale, marker-bearing file that could be mistaken for current, validated
    review output."""
    reviewed_path = out_dir / "replacements.reviewed.txt"
    if reviewed_path.exists():
        reviewed_path.unlink()


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
        if decision is None or not decision.is_decided():
            status = "UNDECIDED"
        else:
            status = f"{decision.decision} ({decision.reason})"
        lines.append(f"  {placeholder}: {status}")

    undecided = report.undecided()
    if undecided:
        lines.append(f"\n{len(undecided)} finding(s) undecided.")
    else:
        lines.append("\nAll findings decided.")
    return "\n".join(lines)
