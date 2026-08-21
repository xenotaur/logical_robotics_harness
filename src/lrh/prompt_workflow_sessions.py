"""Minimal project/sessions/ index: host<->child session identity capture.

Stage 1 of PROP-LRH-SESSION-ARCHIVE-SYNC added identity capture (host id,
child id aliases, title, PRs, branch/written_branches fields reserved for
later fork stitching). Stage 2 (WI-SESSION-ARCHIVE-SYNC-RECONCILER) adds
the archive reconciler: mirroring raw transcripts into a durable local
archive, harvesting /export metadata.json for the host<->child<->PR
mapping on pointers that already dangle, and the discover/link lookups
that read the resulting archive and index. It does not implement
lrh sessions report or index *enrichment* (era-general keys, multi-export
dedup) -- those are Stage 3 -- nor the weekly/hook-triggered sync -- Stage
4. It does not change the session_transcript scalar/sequence grammar.
"""

from __future__ import annotations

import contextlib
import dataclasses
import fcntl
import hashlib
import json
import os
import pathlib
import re
import typing
import zipfile

from lrh.atomic_write import atomic_write, atomic_write_bytes


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
_SESSION_ID_DIR = re.compile(r"^[0-9A-Fa-f][0-9A-Fa-f-]{7,}$")


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
    for jsonl_path in sorted(claude_projects_root.glob("*/*.jsonl")):
        slug = jsonl_path.parent.name
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
    return bool(_SESSION_ID_DIR.fullmatch(name) and any(c.isdigit() for c in name))


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

    for project_dir in sorted(p for p in claude_projects_root.iterdir() if p.is_dir()):
        local_slug = project_dir.name
        for session_dir in sorted(p for p in project_dir.iterdir() if p.is_dir()):
            session_id = session_dir.name
            if not _is_session_artifact_dir(session_id, known_session_ids):
                continue
            owner_slug = session_id_to_slug.get(session_id, local_slug)
            for nested_file in sorted(p for p in session_dir.rglob("*") if p.is_file()):
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
