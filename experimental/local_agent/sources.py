"""Pinned, tracked-only source access for context packets.

Every source is read from a Git object at an explicit commit, never from the
working tree. Untracked content, excluded private paths, binary data, and
over-budget text are rejected or visibly truncated rather than silently
included.
"""

from __future__ import annotations

import dataclasses
import hashlib
import io
import pathlib
import subprocess
import tarfile

from local_agent import settings


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


def resolve_commit(repo: pathlib.Path, revision: str) -> str:
    """Return the full commit SHA for ``revision`` in ``repo``."""
    output = _git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
    return output.decode("utf-8").strip()


def check_path_allowed(project_relative_path: str) -> None:
    """Reject paths that stage 0 never copies into a packet."""
    normalized = project_relative_path.replace("\\", "/")
    if normalized.startswith("/") or ".." in normalized.split("/"):
        raise SourceError(f"path must be relative and confined: {normalized}")
    for prefix in settings.EXCLUDED_PROJECT_PREFIXES:
        if normalized.startswith(prefix):
            raise SourceError(f"excluded private path: {normalized}")


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
