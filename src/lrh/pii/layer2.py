"""Layer 2 scoped content-pattern detector for `lrh pii scan`.

Runs the shared PII/secret rule taxonomy (`lrh.shared.sensitivity_rules`,
via `lrh.conversations.sensitivity.scan_text_for_sensitive_findings`)
against file content fetched at specific historical commits, not just the
current working tree - reusing `lrh.pii.enumerate.enumerate_commits_for_paths`
for the per-commit fetch set.

Scope is controlled by `PiiConfig.content_scan_scope` (`PROP-LRH-PII-SCAN`
Decision 2, as revised during PR #591 review): `"flagged"` (default) scans
only files Layer 1 already flagged by path/filename heuristic, to avoid
false-positiving on legitimate content in ordinary repo files (e.g. a
contributor's email in `CODEOWNERS`); `"all-text"` extends scanning to
every text path ever added, trading precision for recall.

Under `"all-text"`, every text path's *entire* per-commit history is
requested from the enumerator, not just each path's current working-tree
content - a text file added benign, later modified to add PII, then
subsequently cleaned or reverted, would otherwise have no revision Layer 2
ever sees (PR #596 review, `chatgpt-codex-connector` P1).

PDF content is extracted via `lrh.conversations.pdf_import.extract_pdf_text`
rather than a second, parallel PDF parser. Plain text is decoded directly.
Any other content - other binary formats, an encrypted or non-text-layer
PDF, undecodable bytes - is skipped; this is a disclosed detection gap
(no OCR, no binary-format text extraction), not a bug to route around.

A path/commit pair is scanned at most once even when `all_paths` contains
both sides of a rename: `enumerate_commits_for_paths` follows the
destination back through the source (and vice versa via `--follow`), so
requesting both names for a renamed file returns the same underlying
commits twice, under each name (PR #646 review, `chatgpt-codex-connector`).
`content_findings_for_paths` deduplicates by `(commit, path)` before
scanning so a finding isn't counted twice for one real occurrence.

A `git show` failure is treated as an unscannable blob (deleted-at-that-
commit, the common case) only when git's own stderr says the path is
absent from that commit. Any other failure - repository corruption, a
missing promisor blob in a partial clone, or any other read error -
raises `Layer2ContentReadError` instead of being silently skipped, since
swallowing it would let a full-history scan appear clean while actually
missing content (PR #646 review, `chatgpt-codex-connector`).
"""

from __future__ import annotations

import dataclasses
import pathlib
import subprocess

from lrh.conversations import pdf_import, sensitivity
from lrh.pii import config as pii_config
from lrh.pii import enumerate as pii_enumerate


@dataclasses.dataclass(frozen=True)
class Layer2Finding:
    path: str
    commit: str
    rule_id: str
    category: str
    severity: str
    confidence: str
    redacted_preview: str
    line_number: int | None


class Layer2ContentReadError(Exception):
    """Raised when `git show` fails for a reason other than the path being
    absent from that commit (e.g. repository corruption, a missing
    promisor blob in a partial clone)."""


_MISSING_PATH_STDERR_MARKERS = (
    "does not exist in",
    "exists on disk, but not in",
)


def _read_content_at_commit(
    project_root: pathlib.Path, commit: str, path: str
) -> bytes | None:
    """Return the raw bytes for `path` as it existed at `commit`, or `None`
    if the path was absent from the tree at that commit (e.g. deleted).
    Any other `git show` failure raises `Layer2ContentReadError` rather
    than being treated as an unscannable-but-harmless case."""
    result = subprocess.run(
        ["git", "-C", str(project_root), "show", f"{commit}:{path}"],
        capture_output=True,
    )
    if result.returncode != 0:
        stderr_text = result.stderr.decode("utf-8", errors="replace")
        if any(marker in stderr_text for marker in _MISSING_PATH_STDERR_MARKERS):
            return None
        raise Layer2ContentReadError(
            f"git show {commit}:{path} failed unexpectedly: {stderr_text.strip()}"
        )
    return result.stdout


def _extract_text(path: str, raw_bytes: bytes) -> str | None:
    """Return decoded text to scan for `path`'s content, or `None` if the
    content isn't scannable under this layer's disclosed gaps."""
    if path.lower().endswith(".pdf"):
        try:
            extraction = pdf_import.extract_pdf_text(raw_bytes)
        except pdf_import.PdfImportError:
            return None
        return extraction.text
    try:
        return raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None


def content_findings_for_paths(
    project_root: pathlib.Path,
    flagged_paths: list[str],
    all_paths: list[str],
    config: pii_config.PiiConfig,
) -> list[Layer2Finding]:
    """Scan content for PII/secrets, scoped per `config.content_scan_scope`:
    `flagged_paths` (Layer 1's output) by default, or `all_paths` (every
    text path Layer 1 was given) under `"all-text"`."""
    target_paths = (
        all_paths
        if config.content_scan_scope == pii_config.CONTENT_SCAN_SCOPE_ALL_TEXT
        else flagged_paths
    )
    path_commits = list(
        dict.fromkeys(
            pii_enumerate.enumerate_commits_for_paths(project_root, target_paths)
        )
    )

    findings: list[Layer2Finding] = []
    for path_commit in path_commits:
        raw_bytes = _read_content_at_commit(
            project_root, path_commit.commit, path_commit.path
        )
        if raw_bytes is None:
            continue
        text = _extract_text(path_commit.path, raw_bytes)
        if text is None:
            continue
        scan_result = sensitivity.scan_text_for_sensitive_findings(text)
        for finding in scan_result.findings:
            findings.append(
                Layer2Finding(
                    path=path_commit.path,
                    commit=path_commit.commit,
                    rule_id=finding.rule_id,
                    category=finding.category,
                    severity=finding.severity,
                    confidence=finding.confidence,
                    redacted_preview=finding.redacted_preview,
                    line_number=finding.line_number,
                )
            )
    return findings
