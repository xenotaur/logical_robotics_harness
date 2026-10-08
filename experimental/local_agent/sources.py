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
    output = _git(repo, "ls-tree", "-r", "--name-only", commit)
    return [line for line in output.decode("utf-8").splitlines() if line]


def repo_root(start: pathlib.Path) -> pathlib.Path:
    """The Git top-level directory containing ``start``."""
    output = _git(start, "rev-parse", "--show-toplevel")
    return pathlib.Path(output.decode("utf-8").strip())


def resolve_commit(repo: pathlib.Path, revision: str) -> str:
    """Return the full commit SHA for ``revision`` in ``repo``."""
    output = _git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
    return output.decode("utf-8").strip()


def check_path_allowed(project_relative_path: str) -> None:
    """Reject paths that stage 0 never copies into a packet."""
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


def check_text_allowed(repo_path: str, text: str) -> tuple[str, ...]:
    """Apply proposal Decision 3's severity rule (a best-effort guard).

    A high-severity finding (secret, token, private key, URL credentials,
    payment card, government ID) excludes the source. Medium-severity findings
    (email, IP address, phone) do not; their categories are returned as
    warnings. Any severity other than medium is treated as high. Errors and
    warnings name categories only, never matched content.
    """
    scan = sensitivity.scan_text_for_sensitive_findings(text)
    blocking = sorted(
        {
            finding.category
            for finding in scan.findings
            if finding.severity != sensitivity_rules.SEVERITY_MEDIUM
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
) -> tuple[SourceRef, str]:
    """Load one allowed source, truncating on a line boundary to ``max_bytes``."""
    check_path_allowed(project_relative_path)
    repo_path = _join(project_dir, project_relative_path)
    text, raw, blob_id = read_tracked_text(repo, commit, repo_path)
    warnings = check_text_allowed(repo_path, text)
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
