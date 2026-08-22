"""Minimal project/sessions/ index: host<->child session identity capture.

Stage 1 of PROP-LRH-SESSION-ARCHIVE-SYNC added identity capture (host id,
child id aliases, title, PRs, branch/written_branches fields reserved for
later fork stitching). Stage 2 (WI-SESSION-ARCHIVE-SYNC-RECONCILER) adds
the archive reconciler: mirroring raw transcripts into a durable local
archive, harvesting /export metadata.json for the host<->child<->PR
mapping on pointers that already dangle, and the discover/link lookups
that read the resulting archive and index. Stage 3 adds the metadata-only
lrh sessions report coverage check; it still does not implement index
*enrichment* (era-general keys, multi-export dedup) or the weekly/
hook-triggered sync -- those remain later work. It does not change the
session_transcript scalar/sequence grammar.
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime
import fcntl
import hashlib
import json
import os
import pathlib
import re
import typing
import zipfile

from lrh import prompt_workflow_records
from lrh.atomic_write import atomic_write, atomic_write_bytes

MALFORMED_SESSION_TRANSCRIPT_PREFIX = "<malformed-session-transcript"


@dataclasses.dataclass(frozen=True)
class SessionRecord:
    """One session's identity, keyed by its host id."""

    host_id: str
    child_ids: tuple[str, ...] = ()
    title: str | None = None
    prs: tuple[str, ...] = ()
    branch: str | None = None
    written_branches: tuple[str, ...] = ()
    updated_at: str | None = None

    def to_json_dict(self) -> dict[str, typing.Any]:
        return {
            "host_id": self.host_id,
            "child_ids": list(self.child_ids),
            "title": self.title,
            "prs": list(self.prs),
            "branch": self.branch,
            "written_branches": list(self.written_branches),
            "updated_at": self.updated_at,
        }


@dataclasses.dataclass(frozen=True)
class SessionReportFinding:
    """One metadata-only session archive report finding."""

    category: str
    execution_id: str
    work_item: str
    status: str
    path: str
    session_transcript: str
    reason: str
    pr: str | None = None

    def to_json_dict(self) -> dict[str, typing.Any]:
        return {
            "category": self.category,
            "execution_id": self.execution_id,
            "work_item": self.work_item,
            "status": self.status,
            "path": self.path,
            "session_transcript": self.session_transcript,
            "reason": self.reason,
            "pr": self.pr,
        }


@dataclasses.dataclass(frozen=True)
class SessionReport:
    """Metadata-only archive coverage report for execution records."""

    records_checked: int
    pointers_checked: int
    archived: int
    terminal_none: int
    pending: tuple[SessionReportFinding, ...]
    dangling: tuple[SessionReportFinding, ...]
    unarchived: tuple[SessionReportFinding, ...]
    unsupported: tuple[SessionReportFinding, ...]
    missing: tuple[SessionReportFinding, ...]

    @property
    def findings(self) -> tuple[SessionReportFinding, ...]:
        return (
            *self.pending,
            *self.dangling,
            *self.unarchived,
            *self.unsupported,
            *self.missing,
        )

    def to_json_dict(self) -> dict[str, typing.Any]:
        return {
            "records_checked": self.records_checked,
            "pointers_checked": self.pointers_checked,
            "archived": self.archived,
            "terminal_none": self.terminal_none,
            "pending": [finding.to_json_dict() for finding in self.pending],
            "dangling": [finding.to_json_dict() for finding in self.dangling],
            "unarchived": [finding.to_json_dict() for finding in self.unarchived],
            "unsupported": [finding.to_json_dict() for finding in self.unsupported],
            "missing": [finding.to_json_dict() for finding in self.missing],
        }


def index_path(project_root: str | pathlib.Path) -> pathlib.Path:
    return pathlib.Path(project_root) / "project" / "sessions" / "index.jsonl"


def load_session_index(
    project_root: str | pathlib.Path,
) -> dict[str, SessionRecord]:
    """Load the committed index. Missing file is not an error -- empty index."""

    path = index_path(project_root)
    records: dict[str, SessionRecord] = {}
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        host_id = data["host_id"]
        records[host_id] = SessionRecord(
            host_id=host_id,
            child_ids=tuple(data.get("child_ids") or ()),
            title=data.get("title"),
            prs=tuple(data.get("prs") or ()),
            branch=data.get("branch"),
            written_branches=tuple(data.get("written_branches") or ()),
            updated_at=data.get("updated_at"),
        )
    return records


def build_session_report(
    project_root: str | pathlib.Path,
    *,
    archive_root: str | pathlib.Path | None = None,
    since_created_at: str | None = None,
) -> SessionReport:
    """Build a deterministic, metadata-only report of session archive coverage.

    The report reads execution-record frontmatter, ``project/sessions`` index
    rows, Claude archive filenames, and Codex ``attempt.json`` files. It does
    not read raw transcript JSONL bodies, Codex ``raw.json`` captures, or
    Markdown transcript bodies.
    """

    root = pathlib.Path(project_root)
    resolved_archive_root = resolve_archive_root(archive_root)
    index = load_session_index(root)
    archived_child_ids = _archived_claude_child_ids(resolved_archive_root)
    archived_codex_thread_ids = _archived_codex_thread_ids(resolved_archive_root)
    since = _since_created_at_datetime(since_created_at)
    records = [
        record
        for record in prompt_workflow_records.load_execution_records(root)
        if _record_is_in_report_window(record, since)
    ]

    archived = 0
    terminal_none = 0
    pending: list[SessionReportFinding] = []
    dangling: list[SessionReportFinding] = []
    unarchived: list[SessionReportFinding] = []
    unsupported: list[SessionReportFinding] = []
    missing: list[SessionReportFinding] = []
    pointers_checked = 0

    for record in records:
        values = _session_transcript_values(record.frontmatter)
        if not values:
            missing.append(
                _finding(
                    root,
                    record,
                    "",
                    category="missing",
                    reason="execution record has no session_transcript field",
                )
            )
            continue
        for value in values:
            pointers_checked += 1
            if value == "none":
                terminal_none += 1
                continue
            if value == "pending":
                pending.append(
                    _finding(
                        root,
                        record,
                        value,
                        category="pending",
                        reason="session_transcript is still pending",
                    )
                )
                continue
            if value.startswith(MALFORMED_SESSION_TRANSCRIPT_PREFIX):
                unsupported.append(
                    _finding(
                        root,
                        record,
                        value,
                        category="unsupported",
                        reason=("session_transcript value is malformed or empty"),
                    )
                )
                continue
            scheme, sep, identifier = value.partition(":")
            if not sep or not scheme or not identifier:
                unsupported.append(
                    _finding(
                        root,
                        record,
                        value,
                        category="unsupported",
                        reason="session_transcript is not a scheme-prefixed pointer",
                    )
                )
                continue
            if scheme == "claude-app":
                host_id = identifier.removeprefix("local_")
                indexed = index.get(host_id)
                if indexed is None:
                    dangling.append(
                        _finding(
                            root,
                            record,
                            value,
                            category="dangling",
                            reason=(
                                "claude-app host id is not present in "
                                "project/sessions/index.jsonl"
                            ),
                        )
                    )
                elif any(
                    child_id in archived_child_ids for child_id in indexed.child_ids
                ):
                    archived += 1
                else:
                    unarchived.append(
                        _finding(
                            root,
                            record,
                            value,
                            category="unarchived",
                            reason=(
                                "indexed claude-app session has no archived "
                                "top-level JSONL transcript"
                            ),
                        )
                    )
                continue
            if scheme == "codex-app":
                if identifier in {"current-task", "current-thread"}:
                    dangling.append(
                        _finding(
                            root,
                            record,
                            value,
                            category="dangling",
                            reason=(
                                "codex-app pointer is a placeholder, not a "
                                "durable thread id"
                            ),
                        )
                    )
                elif identifier in archived_codex_thread_ids:
                    archived += 1
                else:
                    unarchived.append(
                        _finding(
                            root,
                            record,
                            value,
                            category="unarchived",
                            reason=(
                                "codex-app thread id has no successful "
                                "durable archive attempt"
                            ),
                        )
                    )
                continue
            unsupported.append(
                _finding(
                    root,
                    record,
                    value,
                    category="unsupported",
                    reason=(
                        "archive coverage check is not implemented for "
                        f"scheme {scheme!r}"
                    ),
                )
            )

    return SessionReport(
        records_checked=len(records),
        pointers_checked=pointers_checked,
        archived=archived,
        terminal_none=terminal_none,
        pending=tuple(pending),
        dangling=tuple(dangling),
        unarchived=tuple(unarchived),
        unsupported=tuple(unsupported),
        missing=tuple(missing),
    )


def _session_transcript_values(frontmatter: dict[str, typing.Any]) -> tuple[str, ...]:
    if "session_transcript" not in frontmatter:
        return ()
    value = frontmatter.get("session_transcript")
    raw_values = value if isinstance(value, list) else [value]
    values: list[str] = []
    for raw_value in raw_values:
        if isinstance(raw_value, str):
            cleaned = raw_value.strip().strip("'\"")
            if cleaned:
                values.append(cleaned)
            else:
                values.append(_malformed_session_transcript_value(raw_value))
        else:
            values.append(_malformed_session_transcript_value(raw_value))
    return tuple(values)


def _malformed_session_transcript_value(value: typing.Any) -> str:
    kind = "empty" if isinstance(value, str) else type(value).__name__
    return f"{MALFORMED_SESSION_TRANSCRIPT_PREFIX}:{kind}>"


def _finding(
    project_root: pathlib.Path,
    record: prompt_workflow_records.ExecutionRecord,
    session_transcript: str,
    *,
    category: str,
    reason: str,
) -> SessionReportFinding:
    try:
        path = str(record.path.relative_to(project_root))
    except ValueError:
        path = str(record.path)
    return SessionReportFinding(
        category=category,
        execution_id=record.execution_id,
        work_item=record.work_item,
        status=record.status,
        path=path,
        session_transcript=session_transcript,
        reason=reason,
        pr=record.pr or None,
    )


def _record_is_in_report_window(
    record: prompt_workflow_records.ExecutionRecord,
    since_created_at: datetime.datetime | None,
) -> bool:
    if since_created_at is None:
        return True
    record_created = _parse_iso_datetime(record.created_at)
    if record_created is None:
        return False
    return record_created >= since_created_at


def _since_created_at_datetime(value: str | None) -> datetime.datetime | None:
    if value is None:
        return None
    parsed = _parse_iso_datetime(value)
    if parsed is None:
        raise ValueError("since_created_at must be an ISO timestamp")
    return parsed


def _parse_iso_datetime(value: str) -> datetime.datetime | None:
    """Parse common ISO forms to UTC for chronological comparisons."""

    stripped = value.strip()
    if stripped.endswith("Z"):
        stripped = f"{stripped[:-1]}+00:00"
    try:
        parsed = datetime.datetime.fromisoformat(stripped)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.astimezone(datetime.timezone.utc)


def _archived_claude_child_ids(archive_root: pathlib.Path) -> set[str]:
    raw_root = archive_root / "raw"
    if not raw_root.exists():
        return set()
    child_ids: set[str] = set()
    for project_dir in sorted(
        p for p in raw_root.iterdir() if not p.is_symlink() and p.is_dir()
    ):
        for transcript in sorted(
            p for p in project_dir.glob("*.jsonl") if not p.is_symlink() and p.is_file()
        ):
            child_ids.add(transcript.stem)
    return child_ids


def _archived_codex_thread_ids(archive_root: pathlib.Path) -> set[str]:
    codex_root = archive_root / "codex"
    if not codex_root.exists():
        return set()
    thread_ids: set[str] = set()
    attempt_paths: list[pathlib.Path] = []
    for dirpath, dirnames, filenames in os.walk(codex_root, followlinks=False):
        current_dir = pathlib.Path(dirpath)
        dirnames[:] = [
            dirname for dirname in dirnames if not (current_dir / dirname).is_symlink()
        ]
        if "attempt.json" in filenames:
            attempt_path = current_dir / "attempt.json"
            if not attempt_path.is_symlink() and attempt_path.is_file():
                attempt_paths.append(attempt_path)
    for attempt_path in sorted(attempt_paths):
        try:
            data = json.loads(attempt_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        if data.get("ephemeral") is True:
            continue
        if data.get("status") not in {"succeeded", "imported"}:
            continue
        thread_id = data.get("thread_id")
        if isinstance(thread_id, str) and thread_id:
            thread_ids.add(thread_id)
    return thread_ids


def _merge(
    existing: SessionRecord | None,
    *,
    host_id: str,
    child_id: str | None,
    title: str | None,
    pr: str | None,
    branch: str | None,
    written_branches: typing.Sequence[str] | None,
    updated_at: str,
) -> SessionRecord:
    child_ids = set(existing.child_ids) if existing else set()
    if child_id:
        child_ids.add(child_id)
    prs = set(existing.prs) if existing else set()
    if pr:
        prs.add(pr)
    written = set(existing.written_branches) if existing else set()
    if written_branches:
        written.update(written_branches)
    return SessionRecord(
        host_id=host_id,
        child_ids=tuple(sorted(child_ids)),
        title=title if title is not None else (existing.title if existing else None),
        prs=tuple(sorted(prs)),
        branch=(
            branch if branch is not None else (existing.branch if existing else None)
        ),
        written_branches=tuple(sorted(written)),
        updated_at=updated_at,
    )


def record_session_observation(
    project_root: str | pathlib.Path,
    *,
    host_id: str,
    updated_at: str,
    child_id: str | None = None,
    title: str | None = None,
    pr: str | None = None,
    branch: str | None = None,
    written_branches: typing.Sequence[str] | None = None,
) -> pathlib.Path:
    """Merge one observation into the session identity for ``host_id``.

    Idempotent and dedup-by-host-id, latest-wins for scalar fields
    (title/branch), union for set-valued fields (child_ids/prs/
    written_branches). Rewrites the whole index sorted by host_id so the
    file is byte-stable across repeated observations and diffs cleanly.
    """

    if not host_id:
        raise ValueError("host_id is required")
    records = load_session_index(project_root)
    records[host_id] = _merge(
        records.get(host_id),
        host_id=host_id,
        child_id=child_id,
        title=title,
        pr=pr,
        branch=branch,
        written_branches=written_branches,
        updated_at=updated_at,
    )
    path = index_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(records[key].to_json_dict(), sort_keys=True)
        for key in sorted(records)
    ]
    content = "\n".join(lines) + ("\n" if lines else "")
    atomic_write(path, content)
    return path


# ---------------------------------------------------------------------------
# Archive root resolution
# ---------------------------------------------------------------------------

ARCHIVE_ROOT_ENV_VAR = "LRH_SESSION_ARCHIVE_ROOT"
_SESSION_ID_DIR = re.compile(
    r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-" r"[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$"
)


def default_archive_root() -> pathlib.Path:
    """Default local archive root when neither an override nor the env var
    is set. The proposal's archive-root-location open question is not
    resolved by this default -- it is only a starting point, and both
    ``--archive-root`` and ``LRH_SESSION_ARCHIVE_ROOT`` take precedence."""

    return pathlib.Path.home() / ".local" / "share" / "lrh" / "session-archive"


def resolve_archive_root(
    override: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """Resolve the archive root: ``override`` > env var > default."""

    if override:
        return pathlib.Path(override).expanduser()
    env_value = os.environ.get(ARCHIVE_ROOT_ENV_VAR)
    if env_value:
        return pathlib.Path(env_value).expanduser()
    return default_archive_root()


# ---------------------------------------------------------------------------
# Raw-JSONL mirroring (append-safe, never truncates a growing transcript)
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class DiscoveredTranscript:
    """One local session archive source and its destination context."""

    path: pathlib.Path
    slug: str
    relative_path: pathlib.Path

    @property
    def is_top_level(self) -> bool:
        return len(self.relative_path.parts) == 1


def _top_level_transcripts(
    claude_projects_root: pathlib.Path,
) -> list[DiscoveredTranscript]:
    discovered: list[DiscoveredTranscript] = []
    for project_dir in sorted(
        p for p in claude_projects_root.iterdir() if not p.is_symlink() and p.is_dir()
    ):
        slug = project_dir.name
        for jsonl_path in sorted(
            p for p in project_dir.glob("*.jsonl") if not p.is_symlink() and p.is_file()
        ):
            discovered.append(
                DiscoveredTranscript(
                    path=jsonl_path,
                    slug=slug,
                    relative_path=pathlib.Path(jsonl_path.name),
                )
            )
    return discovered


def _is_session_artifact_dir(name: str, known_session_ids: set[str]) -> bool:
    if name in known_session_ids:
        return True
    return bool(_SESSION_ID_DIR.fullmatch(name))


def _nested_session_files(session_dir: pathlib.Path) -> list[pathlib.Path]:
    nested_files: list[pathlib.Path] = []
    for dirpath, dirnames, filenames in os.walk(session_dir, followlinks=False):
        current_dir = pathlib.Path(dirpath)
        dirnames[:] = [
            dirname for dirname in dirnames if not (current_dir / dirname).is_symlink()
        ]
        for filename in filenames:
            nested_file = current_dir / filename
            if not nested_file.is_symlink() and nested_file.is_file():
                nested_files.append(nested_file)
    return sorted(nested_files)


def discover_transcripts(
    claude_projects_root: pathlib.Path,
) -> list[DiscoveredTranscript]:
    """All local Claude Code transcript artifacts to mirror.

    Top-level transcripts still come from ``<root>/<slug>/<session-id>.jsonl``.
    Nested session-adjacent artifacts are discovered under
    ``<root>/<any-slug>/<session-id>/`` only when ``session-id`` matches a
    top-level transcript anywhere under the root; those files are archived
    under the owning top-level transcript's slug. Orphaned session-id
    directories with no matching top-level transcript are archived under
    their local slug as a best-effort fallback.
    """

    if not claude_projects_root.exists():
        return []

    top_level = _top_level_transcripts(claude_projects_root)
    session_id_to_slug = {item.path.stem: item.slug for item in top_level}
    known_session_ids = set(session_id_to_slug)
    discovered = list(top_level)

    for project_dir in sorted(
        p for p in claude_projects_root.iterdir() if not p.is_symlink() and p.is_dir()
    ):
        local_slug = project_dir.name
        for session_dir in sorted(
            p for p in project_dir.iterdir() if not p.is_symlink() and p.is_dir()
        ):
            session_id = session_dir.name
            if not _is_session_artifact_dir(session_id, known_session_ids):
                continue
            owner_slug = session_id_to_slug.get(session_id, local_slug)
            for nested_file in _nested_session_files(session_dir):
                relative_path = pathlib.Path(session_id) / nested_file.relative_to(
                    session_dir
                )
                discovered.append(
                    DiscoveredTranscript(
                        path=nested_file,
                        slug=owner_slug,
                        relative_path=relative_path,
                    )
                )
    return sorted(discovered, key=lambda item: (item.slug, item.relative_path.parts))


@dataclasses.dataclass(frozen=True)
class MirrorResult:
    source: pathlib.Path
    dest: pathlib.Path
    copied: bool


def mirror_transcript(
    source: pathlib.Path,
    archive_root: pathlib.Path,
    *,
    project_slug: str,
    relative_path: str | pathlib.Path | None = None,
) -> MirrorResult:
    """Mirror ``source`` into ``<archive_root>/raw/<project_slug>/<relative_path>``.

    Re-copies whenever the source has grown or changed, and is a no-op
    when unchanged -- comparing size/mtime, not mere existence, per the
    append-safety requirement: a session can remain active across several
    syncs, and its transcript grows during that time. The archived copy is
    written atomically (temp file + rename), so an interrupted copy never
    leaves a truncated file in place of a complete earlier one -- the
    destination is either the old complete copy or the new complete copy,
    never a partial write.

    The never-shrink invariant is a hard floor on size, independent of
    mtime: a source smaller than the already-archived copy is **never**
    copied, even if its mtime is newer (e.g. a rewritten, truncated, or
    restored-from-backup source) -- an mtime-only trigger would otherwise
    let a newer-but-smaller source overwrite a larger archived copy,
    silently losing already-archived content.
    """

    dest_relative_path = (
        pathlib.Path(relative_path)
        if relative_path is not None
        else pathlib.Path(source.name)
    )
    if dest_relative_path.is_absolute() or ".." in dest_relative_path.parts:
        raise ValueError("relative_path must be a safe relative path")
    dest = archive_root / "raw" / project_slug / dest_relative_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    src_stat = source.stat()
    if dest.exists():
        dest_stat = dest.stat()
        if src_stat.st_size < dest_stat.st_size:
            return MirrorResult(source=source, dest=dest, copied=False)
        if (
            src_stat.st_size == dest_stat.st_size
            and src_stat.st_mtime <= dest_stat.st_mtime
        ):
            return MirrorResult(source=source, dest=dest, copied=False)
    atomic_write_bytes(dest, source.read_bytes())
    return MirrorResult(source=source, dest=dest, copied=True)


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclasses.dataclass(frozen=True)
class SnapshotMirrorResult:
    source: pathlib.Path
    dest: pathlib.Path
    copied: bool
    snapshot: pathlib.Path | None


@contextlib.contextmanager
def _locked_dest(dest: pathlib.Path) -> typing.Iterator[None]:
    """Hold an exclusive lock for the duration of one dest's read-snapshot-write.

    Without this, two overlapping ``mirror_file_with_snapshot`` calls for the
    same ``dest`` (e.g. two concurrent ``lrh memory sync`` processes racing a
    fast-changing source) can each read the same prior content, snapshot it,
    and overwrite -- silently dropping whichever version landed on ``dest``
    between the two reads: it is never the one snapshotted (both callers
    snapshotted the same earlier version) and never the one left current
    (the later writer's own source overwrites it), violating the "no version
    is ever unrecoverable" invariant this function exists to provide. A
    POSIX advisory lock on a sibling lock file serializes the whole
    read-compare-snapshot-write sequence per destination, the same pattern
    ``prompt_workflow_memory._locked_index`` uses for the same reason.
    """

    dest.parent.mkdir(parents=True, exist_ok=True)
    lock_path = dest.parent / f".{dest.name}.lock"
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def mirror_file_with_snapshot(
    source: pathlib.Path,
    dest: pathlib.Path,
    *,
    history_dir: pathlib.Path,
    timestamp: str,
) -> SnapshotMirrorResult:
    """Mirror ``source`` to ``dest``, snapshotting prior ``dest`` content first.

    A generalization of :func:`mirror_transcript` for sources that are
    legitimately edited or shrunk, not append-only -- ``mirror_transcript``'s
    never-shrink invariant assumes the source only grows, which holds for
    JSONL transcripts but not for memory files (the installed
    ``consolidate-memory`` skill routinely merges duplicates and prunes
    stale entries, a legitimate shrink). This compares by content hash
    instead of size/mtime, and on any change, preserves the file currently
    at ``dest`` under ``history_dir`` before overwriting it -- so no prior
    version is ever unrecoverable, but shrinkage is never treated as
    corruption or blocked.

    Snapshot filenames follow ``<dest-stem>.<timestamp>.<shorthash><dest-suffix>``
    under ``history_dir`` -- derived from ``dest.stem``/``dest.suffix``, not a
    hard-coded ``.md``, so a ``.md`` destination doesn't get a doubled
    extension and a non-``.md`` destination keeps its own extension rather
    than silently becoming a ``.md`` file. Keyed by the *prior* content's
    hash so the same snapshot is never written twice for an unchanged prior
    version. The whole read-compare-snapshot-write sequence runs under
    :func:`_locked_dest` so two overlapping mirrors of the same ``dest``
    cannot race each other into dropping an intermediate version.
    """

    data = source.read_bytes()
    source_hash = content_hash(data)

    with _locked_dest(dest):
        snapshot: pathlib.Path | None = None
        if dest.exists():
            existing = dest.read_bytes()
            if content_hash(existing) == source_hash:
                return SnapshotMirrorResult(
                    source=source, dest=dest, copied=False, snapshot=None
                )
            history_dir.mkdir(parents=True, exist_ok=True)
            short_hash = content_hash(existing)[:12]
            snapshot = (
                history_dir / f"{dest.stem}.{timestamp}.{short_hash}{dest.suffix}"
            )
            atomic_write_bytes(snapshot, existing)
        atomic_write_bytes(dest, data)
        return SnapshotMirrorResult(
            source=source, dest=dest, copied=True, snapshot=snapshot
        )


_SESSION_ID_FIELD = "sessionId"


def collect_child_id_aliases(jsonl_path: pathlib.Path) -> set[str]:
    """Distinct ``sessionId`` values found on any line of ``jsonl_path``.

    A transcript's filename stem names only its *current* child id. On a
    resumed lineage, earlier lines can carry a different, still-valid
    child id that appears in no filename anywhere -- scanning every line
    is what makes alias collection complete rather than filename-only.
    Malformed lines are skipped rather than raising, since a transcript is
    append-only application data, not a format this module controls.
    """

    aliases: set[str] = set()
    if not jsonl_path.exists():
        return aliases
    for line in jsonl_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        session_id = data.get(_SESSION_ID_FIELD)
        if isinstance(session_id, str) and session_id:
            aliases.add(session_id)
    return aliases


def reconcile_child_id_aliases(
    project_root: str | pathlib.Path,
    jsonl_path: pathlib.Path,
    *,
    updated_at: str,
) -> tuple[str, frozenset[str]] | None:
    """Fold every line-level ``sessionId`` alias in ``jsonl_path`` into the
    index, for whichever host id the index already associates with any one
    of them.

    Raw JSONL alone cannot resolve a *new* host id (Decision 1 of the
    governing proposal), so this only extends an *already-known* mapping:
    if none of the transcript's aliases are yet linked to a host, this is a
    no-op and returns ``None`` -- the export-metadata harvest (or a future
    Stage 3 recovery pass) is what establishes the first link. Once any one
    alias is known, every other alias found in the same file (including
    ones that appear in no filename anywhere, per PR #435's documented
    case) is recorded as a further child id of that same host.

    Returns ``(host_id, newly_added_aliases)`` when it added at least one
    new alias, else ``None``.
    """

    aliases = collect_child_id_aliases(jsonl_path)
    if not aliases:
        return None
    child_to_host: dict[str, str] = {}
    for record in load_session_index(project_root).values():
        for child_id in record.child_ids:
            child_to_host[child_id] = record.host_id
    known_host_ids = {child_to_host[a] for a in aliases if a in child_to_host}
    if not known_host_ids:
        return None
    # Ambiguous if the file's aliases are already split across more than
    # one host in the index -- do not guess which one to extend.
    if len(known_host_ids) > 1:
        return None
    host_id = next(iter(known_host_ids))
    existing_record = load_session_index(project_root).get(host_id)
    already_known = set(existing_record.child_ids) if existing_record else set()
    new_aliases = aliases - already_known
    if not new_aliases:
        return None
    for alias in sorted(new_aliases):
        record_session_observation(
            project_root, host_id=host_id, updated_at=updated_at, child_id=alias
        )
    return host_id, frozenset(new_aliases)


# ---------------------------------------------------------------------------
# /export zip metadata harvest (identity fields only -- never bodies/logs)
# ---------------------------------------------------------------------------

# Exactly the identity fields the governing proposal's archive layout
# reserves (Decision 2): sessionId (host), cliSessionId (child), prNumber,
# prs[], branch, title. Never transcript bodies or logs/ -- those stay
# out by construction, since only these keys are ever read out of the zip.
EXPORT_IDENTITY_FIELDS = (
    "sessionId",
    "cliSessionId",
    "prNumber",
    "prs",
    "branch",
    "title",
)


class ExportMetadataError(Exception):
    """The export zip does not contain a usable ``metadata.json``."""


def harvest_export_metadata(export_zip: pathlib.Path) -> dict[str, typing.Any]:
    """Read only the permitted identity fields from an ``/export`` zip's
    ``metadata.json`` -- never the transcript body or the bundled ``logs/``,
    which is not opened or listed at all."""

    try:
        with zipfile.ZipFile(export_zip) as archive:
            with archive.open("metadata.json") as handle:
                raw = json.load(handle)
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as error:
        raise ExportMetadataError(
            f"{export_zip}: not a valid export zip with metadata.json"
        ) from error
    if not isinstance(raw, dict):
        raise ExportMetadataError(f"{export_zip}: metadata.json is not an object")
    return {key: raw[key] for key in EXPORT_IDENTITY_FIELDS if key in raw}


def session_key_from_metadata(metadata: dict[str, typing.Any]) -> str | None:
    """The host id (``local_`` prefix stripped) named by harvested metadata."""

    session_id = metadata.get("sessionId")
    if not isinstance(session_id, str) or not session_id:
        return None
    return session_id.removeprefix("local_")


def export_pr_urls(metadata: dict[str, typing.Any]) -> list[str]:
    """PR URLs named by harvested metadata, from the ``prs[]`` list."""

    urls: list[str] = []
    for entry in metadata.get("prs") or ():
        if isinstance(entry, dict):
            url = entry.get("url")
            if isinstance(url, str) and url:
                urls.append(url)
    return urls


def exports_path(archive_root: pathlib.Path, session_key: str) -> pathlib.Path:
    return archive_root / "exports" / session_key / "metadata.json"


def persist_export_metadata(
    archive_root: pathlib.Path,
    session_key: str,
    metadata: dict[str, typing.Any],
) -> pathlib.Path:
    """Atomically write the sanitized identity-fields-only metadata copy
    so Stage 3 can rebuild or enrich the index later (recovering
    ``written_branches``/``cwd``, multi-export latest-wins) even if the
    original export zip is subsequently deleted -- per Decision 2's
    archive layout, this copy is what makes the harvest re-derivable."""

    dest = exports_path(archive_root, session_key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    atomic_write(dest, content)
    return dest


def sync_export(
    project_root: str | pathlib.Path,
    archive_root: pathlib.Path,
    export_zip: pathlib.Path,
    *,
    updated_at: str,
) -> SessionRecord | None:
    """Harvest one ``/export`` zip, persist its sanitized metadata copy,
    then upsert the resulting host<->child<->PR mapping into the index.

    Returns ``None`` (with the persisted copy still written) when the
    metadata has no usable host id -- there is nothing to key an index
    entry on, but the archived metadata copy remains valid for later
    reconciliation.
    """

    metadata = harvest_export_metadata(export_zip)
    session_key = session_key_from_metadata(metadata)
    persist_export_metadata(archive_root, session_key or export_zip.stem, metadata)
    if session_key is None:
        return None

    child_id = metadata.get("cliSessionId")
    title = metadata.get("title")
    branch = metadata.get("branch")
    pr_urls = export_pr_urls(metadata) or [None]
    # metadata.json can name several PRs (prs[]); record_session_observation
    # merges one PR per call, so fold each in with its own call -- the
    # first call also carries child_id/title/branch, the rest are pure
    # PR-set unions against the record the first call just wrote.
    first_child_id = child_id if isinstance(child_id, str) and child_id else None
    first_title = title if isinstance(title, str) else None
    first_branch = branch if isinstance(branch, str) else None
    for index, pr_url in enumerate(pr_urls):
        record_session_observation(
            project_root,
            host_id=session_key,
            updated_at=updated_at,
            child_id=first_child_id if index == 0 else None,
            title=first_title if index == 0 else None,
            pr=pr_url,
            branch=first_branch if index == 0 else None,
        )
    return load_session_index(project_root).get(session_key)


# ---------------------------------------------------------------------------
# discover / link lookups
# ---------------------------------------------------------------------------

_PROJECT_SLUG_UNSAFE = re.compile(r"[/.]")


def project_slug_for_path(path: str | pathlib.Path) -> str:
    """Claude Code's own project-slug rule: normalize ``/`` and ``.`` to
    ``-`` in the absolute path, matching how it names
    ``~/.claude/projects/<slug>/``.

    Verified against every real directory under ``~/.claude/projects/``
    on this machine: a `.claude/worktrees/...` path segment becomes
    `-claude-worktrees-...` (the leading dot *is* replaced), while a
    repository name containing a literal underscore (e.g.
    ``replication_vector``) is preserved as-is -- underscore is **not**
    replaced. An earlier revision of this function replaced ``_`` instead
    of ``.``, which silently broke resolution for every
    ``.claude/worktrees/`` path -- this project's own most common working
    layout.
    """

    absolute = str(pathlib.Path(path).expanduser().resolve())
    return _PROJECT_SLUG_UNSAFE.sub("-", absolute)


@dataclasses.dataclass(frozen=True)
class DiscoveredSession:
    child_id: str
    path: pathlib.Path
    size_bytes: int
    mtime: float
    host_id: str | None


def discover_sessions_for_project(
    project_root: str | pathlib.Path,
    claude_projects_root: pathlib.Path,
    *,
    project_path: str | pathlib.Path | None = None,
) -> list[DiscoveredSession]:
    """List local transcripts for one project, cross-referenced against the
    committed index for host-id resolution where harvest has already
    resolved one -- archive/export awareness, not local-filesystem-only."""

    target = project_path if project_path is not None else project_root
    slug = project_slug_for_path(target)
    project_dir = claude_projects_root / slug
    child_to_host: dict[str, str] = {}
    for record in load_session_index(project_root).values():
        for child_id in record.child_ids:
            child_to_host[child_id] = record.host_id
    results: list[DiscoveredSession] = []
    jsonl_paths = sorted(project_dir.glob("*.jsonl")) if project_dir.exists() else []
    for jsonl_path in jsonl_paths:
        stat = jsonl_path.stat()
        child_id = jsonl_path.stem
        results.append(
            DiscoveredSession(
                child_id=child_id,
                path=jsonl_path,
                size_bytes=stat.st_size,
                mtime=stat.st_mtime,
                host_id=child_to_host.get(child_id),
            )
        )
    return results


class LinkLookupError(Exception):
    """A child id could not be resolved to exactly one host id."""


def resolve_host_id_for_child(project_root: str | pathlib.Path, child_id: str) -> str:
    """Resolve ``child_id`` to its host id via the committed index.

    Raises ``LinkLookupError`` if the child id is unknown, or -- should a
    data anomaly ever alias the same child id under two host ids -- if the
    resolution is ambiguous; a caller must never guess in that case.
    """

    matches = [
        record.host_id
        for record in load_session_index(project_root).values()
        if child_id in record.child_ids
    ]
    if not matches:
        raise LinkLookupError(f"no session in the index has child id {child_id!r}")
    if len(matches) > 1:
        raise LinkLookupError(
            f"child id {child_id!r} is aliased under multiple host ids: {matches!r}"
        )
    return matches[0]
