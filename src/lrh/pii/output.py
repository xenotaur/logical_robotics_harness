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

`still_in_working_tree` is computed from `HEAD`'s *current* content, not
from `finding.commit == HEAD` - that equality is neither necessary nor
sufficient: a finding's own commit not being `HEAD` doesn't mean its
content is gone (an unrelated later commit could leave the flagged file
untouched), and `commit == HEAD` doesn't guarantee the flagged content is
still there either (PR #650 review, `chatgpt-codex-connector` P1).
Instead, a finding is still present if the file's content at `HEAD` is
byte-identical to its content at `finding.commit` - a Layer 1 finding's
`content_digest` already *is* that commit's blob SHA, so it's compared to
`HEAD`'s blob SHA directly; a Layer 2 finding's `content_digest` is only a
substring hash, so its full-file blob SHA at `finding.commit` is fetched
separately for the same byte-identical comparison. This is a
conservative check - unchanged file content trivially still contains the
flagged value, but a file that changed elsewhere while still containing
the same flagged value is reported as no longer present (a disclosed
false-negative bias, not a mark of certainty either way).

Raises `Layer1BlobReadError` for a `git rev-parse <commit>:<path>`
failure that isn't the path being absent from that commit - the same
missing-path-vs-unexpected-failure distinction `lrh.pii.layer2` already
makes for its own git reads, so a repository-corruption or partial-clone
read failure surfaces instead of being silently treated as "not found"
(PR #650 review, `copilot-pull-request-reviewer`).
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

# PROP-LRH-PII-SCAN Decision 7's documented output contract.
MATCHED_LAYER_1 = "path"
MATCHED_LAYER_2 = "content"

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


class Layer1BlobReadError(Exception):
    """Raised when `git rev-parse <commit>:<path>` fails for a reason other
    than the path being absent from that commit (e.g. repository
    corruption, a missing promisor blob in a partial clone)."""


_MISSING_PATH_STDERR_MARKERS = (
    "does not exist in",
    "exists on disk, but not in",
    "invalid object name",
)


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
    the path is absent from that commit's tree. Any other failure raises
    `Layer1BlobReadError` rather than being treated as an ordinary miss."""
    result = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", f"{commit}:{path}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        if any(marker in result.stderr for marker in _MISSING_PATH_STDERR_MARKERS):
            return None
        stderr_text = result.stderr.strip()
        raise Layer1BlobReadError(
            f"git rev-parse {commit}:{path} failed unexpectedly: {stderr_text}"
        )
    return result.stdout.strip()


def _still_in_working_tree(
    project_root: pathlib.Path,
    head: str,
    commit: str,
    path: str,
    content_digest: str,
    matched_layer: str,
) -> bool:
    """True iff `path`'s content at `head` is byte-identical to its content
    at `commit` - see the module docstring for why commit-ID equality
    alone is neither necessary nor sufficient."""
    head_digest = _blob_sha(project_root, head, path)
    if head_digest is None:
        return False
    finding_commit_digest = (
        content_digest
        if matched_layer == MATCHED_LAYER_1
        else _blob_sha(project_root, commit, path)
    )
    return head_digest == finding_commit_digest


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
                    still_in_working_tree=_still_in_working_tree(
                        project_root,
                        head,
                        path_commit.commit,
                        finding.path,
                        digest,
                        MATCHED_LAYER_1,
                    ),
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
                still_in_working_tree=_still_in_working_tree(
                    project_root,
                    head,
                    finding.commit,
                    finding.path,
                    finding.content_digest,
                    MATCHED_LAYER_2,
                ),
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
