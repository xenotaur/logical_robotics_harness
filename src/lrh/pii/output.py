"""Unified `pii_findings.json` / text-summary output for `lrh pii scan`.

Assembles Layer 1 (`lrh.pii.layer1`) and Layer 2 (`lrh.pii.layer2`)
findings into one schema (`PROP-LRH-PII-SCAN` Decision 7, as revised during
PR #591 review): `{path, rule_id, category, severity, confidence, commit,
content_digest, still_in_working_tree, matched_layer}`.

Layer 1 findings carry no commit or content of their own - `Layer1Finding`
flags a path by name/extension, not content. This module expands each
Layer-1-flagged path across every commit that touched it
(`lrh.pii.enumerate.enumerate_commits_for_paths`) to produce one output row
per (path, commit), so Layer 1 findings get the same per-commit granularity
and `content_digest` (the git blob SHA at that commit - the file's whole
content is what Layer 1 flagged) that Layer 2 findings already carry
(a hash of the matched substring only - see `lrh.pii.layer2`).

`still_in_working_tree` is a cheap proxy, not a fresh re-scan of `HEAD`:
`enumerate_commits_for_paths` includes `HEAD` among the commits it walks
(via `--all`), so a finding whose own `commit` equals the current `HEAD`
SHA is, by construction, still present in the working tree.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import subprocess

from lrh.pii import allowlist as pii_allowlist
from lrh.pii import enumerate as pii_enumerate
from lrh.pii import layer1 as pii_layer1
from lrh.pii import layer2 as pii_layer2

MATCHED_LAYER_1 = "layer1"
MATCHED_LAYER_2 = "layer2"

_LAYER1_CATEGORY = "misplaced_document"
_LAYER1_SEVERITY = "high"
_LAYER1_CONFIDENCE = "medium"

DISCLOSURE_TEXT = (
    "lrh pii scan is a local, deterministic heuristic scanner. It does not "
    "perform OCR, ML/NLP content classification, or any cloud DLP lookup. "
    "Its detection rules are a disclosed, reviewable starter set, not a "
    "claim of completeness."
)


@dataclasses.dataclass(frozen=True)
class Finding:
    path: str
    rule_id: str
    category: str
    severity: str
    confidence: str
    commit: str
    content_digest: str
    still_in_working_tree: bool
    matched_layer: str


def _current_head(project_root: pathlib.Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _blob_sha(project_root: pathlib.Path, commit: str, path: str) -> str | None:
    """Return the git blob object SHA for `path` at `commit`, or `None` if
    it can't be resolved (e.g. the path is absent from that commit)."""
    result = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", f"{commit}:{path}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def build_findings(
    project_root: pathlib.Path,
    layer1_findings: list[pii_layer1.Layer1Finding],
    layer2_findings: list[pii_layer2.Layer2Finding],
) -> list[Finding]:
    """Assemble Layer 1 and Layer 2 findings into the unified output schema."""
    head = _current_head(project_root)
    findings: list[Finding] = []

    for finding in layer1_findings:
        # Queried per finding, not batched across all layer1_findings: each
        # PathCommit.path is the *historical* name a path had at that
        # specific commit (which can differ from finding.path for a
        # renamed file), so batching and re-grouping by that historical
        # name would silently drop every commit reached only under a
        # pre-rename name (found in review - reproduced against a
        # rename-history scratch repo before this fix).
        path_commits = pii_enumerate.enumerate_commits_for_paths(
            project_root, [finding.path]
        )
        for path_commit in path_commits:
            # The blob-SHA lookup must use the name that existed in the
            # tree at path_commit.commit (path_commit.path), not
            # finding.path - the current/canonical name did not exist yet
            # at a pre-rename commit.
            digest = _blob_sha(project_root, path_commit.commit, path_commit.path)
            if digest is None:
                continue
            findings.append(
                Finding(
                    path=finding.path,
                    rule_id=finding.rule_id,
                    category=_LAYER1_CATEGORY,
                    severity=_LAYER1_SEVERITY,
                    confidence=_LAYER1_CONFIDENCE,
                    commit=path_commit.commit,
                    content_digest=digest,
                    still_in_working_tree=(path_commit.commit == head),
                    matched_layer=MATCHED_LAYER_1,
                )
            )

    for finding in layer2_findings:
        findings.append(
            Finding(
                path=finding.path,
                rule_id=finding.rule_id,
                category=finding.category,
                severity=finding.severity,
                confidence=finding.confidence,
                commit=finding.commit,
                content_digest=finding.content_digest,
                still_in_working_tree=(finding.commit == head),
                matched_layer=MATCHED_LAYER_2,
            )
        )

    return findings


def filter_allowlisted(
    findings: list[Finding], allowlist: frozenset[str]
) -> list[Finding]:
    """Return `findings` with every allowlisted entry removed."""
    return [
        finding
        for finding in findings
        if not pii_allowlist.is_allowlisted(
            pii_allowlist.compute_fingerprint(
                finding.path, finding.rule_id, finding.content_digest
            ),
            allowlist,
        )
    ]


def render_json(findings: list[Finding]) -> str:
    return json.dumps(
        [dataclasses.asdict(finding) for finding in findings], indent=2, sort_keys=True
    )


def render_text_summary(findings: list[Finding]) -> str:
    lines = [f"{len(findings)} finding(s)."]
    for finding in findings:
        lines.append(
            f"- {finding.path} [{finding.matched_layer}] {finding.rule_id} "
            f"({finding.severity}/{finding.confidence}) @ {finding.commit[:8]}"
        )
    lines.append("")
    lines.append(DISCLOSURE_TEXT)
    return "\n".join(lines)
