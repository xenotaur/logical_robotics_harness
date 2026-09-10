"""Content-bound allowlist for `lrh pii scan`.

Auto-discovers a repo-committed `.lrh-pii-allowlist` file, `.gitleaksignore`-
style: one fingerprint per line, with an optional trailing `# reason`
comment. Each fingerprint is `sha256(path + rule_id + content_digest)`
(`PROP-LRH-PII-SCAN` Decision 6, as revised during PR #591 review):
`chatgpt-codex-connector` found that a location-only fingerprint
(`sha256(path + rule_id)`) would let one approved benign match silently
suppress a later, genuinely sensitive value at the same path/rule. Binding
the fingerprint to `content_digest` means approval only ever covers the
exact value it was given for - a different value at the same location
produces a different fingerprint and is never suppressed.
"""

from __future__ import annotations

import hashlib
import pathlib

ALLOWLIST_FILENAME = ".lrh-pii-allowlist"


def compute_fingerprint(path: str, rule_id: str, content_digest: str) -> str:
    """Return the content-bound allowlist fingerprint for one finding."""
    return hashlib.sha256(
        f"{path}:{rule_id}:{content_digest}".encode("utf-8")
    ).hexdigest()


def load_allowlist(project_root: pathlib.Path) -> frozenset[str]:
    """Load fingerprints from `.lrh-pii-allowlist` at `project_root`. A
    trailing `# reason` comment on a line is stripped, not required; blank
    and comment-only lines are ignored. Returns an empty set if no
    allowlist file exists - an absent allowlist suppresses nothing."""
    allowlist_path = project_root / ALLOWLIST_FILENAME
    if not allowlist_path.exists():
        return frozenset()
    fingerprints: set[str] = set()
    for line in allowlist_path.read_text(encoding="utf-8").splitlines():
        fingerprint = line.split("#", 1)[0].strip()
        if fingerprint:
            fingerprints.add(fingerprint)
    return frozenset(fingerprints)


def is_allowlisted(fingerprint: str, allowlist: frozenset[str]) -> bool:
    return fingerprint in allowlist
