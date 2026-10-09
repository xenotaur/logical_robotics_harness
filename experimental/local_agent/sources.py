"""Pinned, tracked-only source access for context packets.

Every source is read from a Git object at an explicit commit, never from the
working tree. Untracked content, excluded private paths, binary data, and
over-budget text are rejected or visibly truncated rather than silently
included.
"""

from __future__ import annotations

import dataclasses
import fnmatch
import hashlib
import io
import pathlib
import subprocess
import tarfile

from local_agent import settings
from lrh.conversations import sensitivity
from lrh.shared import sensitivity_rules


class SourceError(ValueError):
    """Raised when a requested source is not allowed into a packet."""


@dataclasses.dataclass(frozen=True)
class SourceRef:
    """Provenance for one source included in a context packet."""

    source_id: str
    repo_label: str
    commit: str
    path: str
    blob_id: str
    sha256: str
    line_start: int
    line_end: int
    total_lines: int
    included_bytes: int
    total_bytes: int
    truncated: bool
    relation: str
    sensitivity_warnings: tuple[str, ...] = ()
    # High-severity findings the owner confirmed with --allow-flagged.
    allowed_findings: tuple[dict[str, object], ...] = ()

    def as_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)


def _git(repo: pathlib.Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", "replace").strip()
        raise SourceError(f"git {' '.join(args)} failed: {message}")
    return completed.stdout


def split_lines(text: str) -> list[str]:
    """Split on ``\n`` only, keeping line ends, so numbers match Git and editors.

    ``str.splitlines`` also splits on form feeds and other separators, which
    would shift packet line numbers away from the source file's.
    """
    if not text:
        return []
    parts = text.split("\n")
    lines = [part + "\n" for part in parts[:-1]]
    if parts[-1]:
        lines.append(parts[-1])
    return lines


def list_tracked_files(repo: pathlib.Path, commit: str) -> list[str]:
    """Repository-relative paths of files tracked at ``commit``."""
    # -z: unquoted names, NUL-separated (newlines in names stay intact).
    output = _git(repo, "ls-tree", "-r", "-z", "--name-only", commit)
    # surrogateescape: a name that is not valid UTF-8 survives decoding and is
    # then rejected by ``check_path_allowed`` instead of crashing the listing.
    decoded = output.decode("utf-8", errors="surrogateescape")
    return [name for name in decoded.split("\0") if name]


def repo_root(start: pathlib.Path) -> pathlib.Path:
    """The Git top-level directory containing ``start``."""
    output = _git(start, "rev-parse", "--show-toplevel")
    return pathlib.Path(output.decode("utf-8").strip())


def resolve_commit(repo: pathlib.Path, revision: str) -> str:
    """Return the full commit SHA for ``revision`` in ``repo``."""
    output = _git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
    return output.decode("utf-8").strip()


def unsafe_path_char(char: str) -> bool:
    """C0/C1 controls, DEL, or an undecodable byte (a surrogate escape)."""
    code = ord(char)
    return code < 0x20 or 0x7F <= code <= 0x9F or 0xDC80 <= code <= 0xDCFF


def shown_path(path: str) -> str:
    """A path safe to print or put in a prompt: quoted if it has unsafe chars."""
    return ascii(path) if any(unsafe_path_char(c) for c in path) else path


def check_path_allowed(project_relative_path: str) -> None:
    """Reject paths that stage 0 never copies into a packet."""
    if any(0xDC80 <= ord(char) <= 0xDCFF for char in project_relative_path):
        raise SourceError("path is not valid UTF-8")
    if any(unsafe_path_char(char) for char in project_relative_path):
        # Never echo such a path: it could smuggle text into headers.
        raise SourceError("path contains control characters")
    normalized = project_relative_path.replace("\\", "/")
    if normalized.startswith("/") or ".." in normalized.split("/"):
        raise SourceError(f"path must be relative and confined: {normalized}")
    # Match private subtrees at any depth (``sub/project/executions/...``).
    bounded = f"/{normalized}".lower()
    for prefix in settings.EXCLUDED_PROJECT_PREFIXES:
        if f"/{prefix}" in bounded:
            raise SourceError(f"excluded private path: {normalized}")
    *directories, basename = normalized.lower().split("/")
    for pattern in settings.CREDENTIAL_NAME_PATTERNS:
        if fnmatch.fnmatchcase(basename, pattern):
            raise SourceError(f"excluded credential-like path: {normalized}")
    for directory in directories:
        for pattern in settings.CREDENTIAL_DIR_PATTERNS:
            if fnmatch.fnmatchcase(directory, pattern):
                raise SourceError(f"excluded credential-like path: {normalized}")


def high_findings(text: str) -> list[dict[str, object]]:
    """High-severity scanner findings as structured records, never values.

    Each record holds ``category``, ``rule_id``, and the 1-based
    ``start_line``/``end_line`` of the match (``None`` when unknown). Any
    severity other than medium counts as high, as in ``check_text_allowed``.
    """
    records: list[dict[str, object]] = []
    scan = sensitivity.scan_text_for_sensitive_findings(text)
    for finding in scan.findings:
        if finding.severity == sensitivity_rules.SEVERITY_MEDIUM:
            continue
        end_line = finding.line_number
        if finding.line_number is not None and finding.end_offset is not None:
            last = max(finding.start_offset or 0, finding.end_offset - 1)
            end_line = text.count("\n", 0, last) + 1
        records.append(
            {
                "category": finding.category,
                "rule_id": finding.rule_id,
                "start_line": finding.line_number,
                "end_line": end_line,
            }
        )
    return records


def check_text_allowed(
    repo_path: str, text: str, allow: frozenset[str] = frozenset()
) -> tuple[str, ...]:
    """Apply proposal Decision 3's severity rule (a best-effort guard).

    A high-severity finding (secret, token, private key, URL credentials,
    payment card, government ID) excludes the source. Medium-severity findings
    (email, IP address, phone) do not; their categories are returned as
    warnings. Any severity other than medium is treated as high. Errors and
    warnings name categories only, never matched content.

    ``allow`` holds high-severity categories the owner explicitly overrode
    for this source (``--allow-flagged``); any other high category still
    excludes it.
    """
    scan = sensitivity.scan_text_for_sensitive_findings(text)
    blocking = sorted(
        {
            finding.category
            for finding in scan.findings
            if finding.severity != sensitivity_rules.SEVERITY_MEDIUM
            and finding.category not in allow
        }
    )
    if blocking:
        raise SourceError(
            f"excluded by sensitivity scan ({', '.join(blocking)}): {repo_path}"
        )
    return tuple(sorted({finding.category for finding in scan.findings}))


def _join(project_dir: str, project_relative_path: str) -> str:
    if project_dir in ("", "."):
        return project_relative_path
    return f"{project_dir.rstrip('/')}/{project_relative_path}"


def read_tracked_text(
    repo: pathlib.Path, commit: str, repo_path: str
) -> tuple[str, bytes, str]:
    """Return ``(text, raw_bytes, blob_id)`` for a tracked text file at ``commit``.

    Raises:
        SourceError: if the path is untracked at that commit or not UTF-8 text.
    """
    object_name = f"{commit}:{repo_path}"
    object_type = _git(repo, "cat-file", "-t", object_name).decode().strip()
    if object_type != "blob":
        raise SourceError(f"not a tracked file at {commit[:12]}: {repo_path}")
    blob_id = _git(repo, "rev-parse", object_name).decode().strip()
    raw = _git(repo, "cat-file", "blob", blob_id)
    if b"\x00" in raw:
        raise SourceError(f"binary content rejected: {repo_path}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SourceError(f"non-UTF-8 content rejected: {repo_path}") from error
    return text, raw, blob_id


def make_source(
    *,
    repo: pathlib.Path,
    repo_label: str,
    commit: str,
    project_dir: str,
    project_relative_path: str,
    source_id: str,
    relation: str,
    max_bytes: int,
    allow: frozenset[str] = frozenset(),
) -> tuple[SourceRef, str]:
    """Load one allowed source, truncating on a line boundary to ``max_bytes``.

    ``allow`` lifts the scanner exclusion for those high-severity categories
    only (the owner's ``--allow-flagged``); path exclusions always apply.
    """
    check_path_allowed(project_relative_path)
    repo_path = _join(project_dir, project_relative_path)
    text, raw, blob_id = read_tracked_text(repo, commit, repo_path)
    warnings = check_text_allowed(repo_path, text, allow)
    high = high_findings(text) if allow else []
    if allow:
        found = {str(finding["category"]) for finding in high}
        if not found:
            raise SourceError(f"no high-severity finding to override: {repo_path}")
        extra = sorted(allow - found)
        if extra:
            # The override must name exactly the categories present.
            raise SourceError(
                f"override names categories not found ({', '.join(extra)}): "
                f"{repo_path}"
            )
    lines = split_lines(text)
    kept: list[str] = []
    used = 0
    for line in lines:
        size = len(line.encode("utf-8"))
        if used + size > max_bytes:
            break
        kept.append(line)
        used += size
    truncated = len(kept) < len(lines)
    # Only findings in the kept lines are actually sent (and so listed).
    allowed = tuple(
        finding
        for finding in high
        if finding["start_line"] is None or int(finding["start_line"]) <= len(kept)
    )
    ref = SourceRef(
        source_id=source_id,
        repo_label=repo_label,
        commit=commit,
        path=repo_path,
        blob_id=blob_id,
        sha256=hashlib.sha256(raw).hexdigest(),
        line_start=1 if kept else 0,
        line_end=len(kept),
        total_lines=len(lines),
        included_bytes=used,
        total_bytes=len(raw),
        truncated=truncated,
        relation=relation,
        sensitivity_warnings=warnings,
        allowed_findings=allowed,
    )
    return ref, "".join(kept)


def materialize_project_tree(
    repo: pathlib.Path, commit: str, project_dir: str, destination: pathlib.Path
) -> pathlib.Path:
    """Extract the tracked ``project/`` tree at ``commit`` into ``destination``.

    Returns the extracted project root (the directory containing ``project/``).
    Only tracked content at the pinned commit is extracted, so a dirty working
    tree never mixes into readiness evaluation.
    """
    tree_path = _join(project_dir, "project")
    archive = _git(repo, "archive", "--format=tar", commit, "--", tree_path)
    if not hasattr(tarfile, "data_filter"):
        # Never fall back to unfiltered extraction of archive members.
        raise SourceError(
            "safe tar extraction filters require Python >= 3.11.4; upgrade Python"
        )
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        tar.extractall(destination, filter="data")
    if project_dir in ("", "."):
        return destination
    return destination / project_dir
