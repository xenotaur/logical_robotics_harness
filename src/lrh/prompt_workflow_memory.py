"""Core logic for ``lrh memory`` -- validated writes to Claude Code's
per-project memory corpus (``~/.claude/projects/<slug>/memory/``).

Implements Stage 1 of PROP-LRH-MEMORY-COMMAND: ``write``, ``list``,
``validate``, and ``repair`` (Decision 9's fast follow-up), plus Stage 2's
``sync`` (WI-LRH-MEMORY-ARCHIVE-SIDE, Decisions 5-6). Resolves the corpus
path via ``project_slug_for_path`` (reused from ``prompt_workflow_sessions``,
not reimplemented -- see that proposal's Decision 4). Does not implement
``read``/``search``/``export``/``import``/``transfer`` -- those are
separate work items.
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime
import fcntl
import os
import pathlib
import re
import typing

import yaml

from lrh import prompt_workflow_sessions
from lrh.atomic_write import atomic_write
from lrh.prompt_workflow_sessions import project_slug_for_path

MEMORY_DIRNAME = "memory"
INDEX_FILENAME = "MEMORY.md"
VALID_TYPES = ("user", "feedback", "project", "reference")
_NAME_PATTERN = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
_TITLE_PREFIXES = VALID_TYPES


class MemoryValidationError(Exception):
    """A memory write, repair, or read request is structurally invalid."""


def default_claude_projects_root() -> pathlib.Path:
    return pathlib.Path.home() / ".claude" / "projects"


def memory_dir_for_project(
    project_root: str | pathlib.Path,
    claude_projects_root: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """Resolve the memory corpus directory for ``project_root``.

    Internal path resolution is the point -- callers never supply the
    corpus path directly, so "wrong location" (the defect that orphaned
    an entire bucket's memory files, per the findings audit) cannot
    happen through this command.
    """

    root = (
        pathlib.Path(claude_projects_root).expanduser()
        if claude_projects_root
        else default_claude_projects_root()
    )
    slug = project_slug_for_path(project_root)
    return root / slug / MEMORY_DIRNAME


def filename_for(name: str) -> str:
    """Map a kebab-case ``name`` to its on-disk filename.

    Matches the convention already present in this machine's real memory
    corpus: frontmatter ``name:`` is kebab-case, the filename is the same
    slug with hyphens replaced by underscores (e.g. ``name:
    feedback-gh-api-jq-arg-flag`` on disk as
    ``feedback_gh_api_jq_arg_flag.md``).
    """

    return name.replace("-", "_") + ".md"


def _validate_name(name: str) -> None:
    if not name or not _NAME_PATTERN.fullmatch(name):
        raise MemoryValidationError(
            "name must be a non-empty kebab-case slug "
            f"(e.g. 'feedback-foo-bar'), got {name!r}"
        )


def _validate_new_write_fields(
    name: str, description: str, type_: str, agent: str
) -> None:
    _validate_name(name)
    if not description or not description.strip():
        raise MemoryValidationError("description must not be empty")
    if type_ not in VALID_TYPES:
        raise MemoryValidationError(f"type must be one of {VALID_TYPES}, got {type_!r}")
    if not agent or not agent.strip():
        raise MemoryValidationError(
            "agent (recorded as metadata.authored_by) is required"
        )


def read_frontmatter_and_body(text: str) -> tuple[dict[str, typing.Any], str]:
    """Split a memory Markdown file into its YAML frontmatter and body.

    Uses ``yaml.safe_load`` (not the constrained ``lrh.control.parser``
    parser, which rejects the nested ``metadata:`` mapping this schema
    requires) so ``metadata.type``/``metadata.authored_by``/
    ``metadata.applies_to`` parse correctly.
    """

    if not text.startswith("---\n"):
        raise MemoryValidationError(
            "memory file must begin with YAML frontmatter delimiter '---'"
        )
    closing = text.find("\n---", 4)
    if closing == -1:
        raise MemoryValidationError(
            "memory file is missing the closing YAML frontmatter delimiter '---'"
        )
    frontmatter_text = text[4:closing]
    body_start = text.find("\n", closing + 1)
    # `.lstrip("\n")`, not a bare slice: the blank line between the closing
    # `---` and the body is a separator, not content -- without stripping
    # it, every read body carries one spurious leading newline relative to
    # what `_render_memory_file()` wrote (it always `.strip("\n")`s the
    # body on write), so a verbatim consumer like the planned `lrh memory
    # read` would print an extra blank line no caller ever wrote.
    body = text[body_start + 1 :].lstrip("\n") if body_start != -1 else ""
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as error:
        raise MemoryValidationError(f"invalid YAML frontmatter: {error}") from error
    if not isinstance(frontmatter, dict):
        raise MemoryValidationError("frontmatter must be a YAML mapping")
    return frontmatter, body


def _render_memory_file(
    *,
    name: str,
    description: str,
    type_: str,
    authored_by: str,
    applies_to: typing.Sequence[str],
    body: str,
) -> str:
    """Render frontmatter through ``yaml.safe_dump``, not hand-built strings.

    A naive ``f"description: {description}"`` interpolation produces
    invalid or silently-reinterpreted YAML for any value containing a
    colon, a leading special character, or an embedded newline (e.g.
    ``--description 'Rule: retain evidence'``) -- exactly the accepted-
    but-malformed-output bug ``yaml.safe_dump`` exists to prevent, since
    it quotes/escapes every scalar it needs to and leaves the rest bare,
    the same guarantee :func:`read_frontmatter_and_body`'s
    ``yaml.safe_load`` counts on to parse it back correctly.
    """

    applies_to_list = list(applies_to) if applies_to else [authored_by]
    frontmatter = {
        "name": name,
        "description": description,
        "metadata": {
            "type": type_,
            "authored_by": authored_by,
            "applies_to": applies_to_list,
        },
    }
    frontmatter_text = yaml.safe_dump(
        frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True
    )
    return "---\n" + frontmatter_text + "---\n\n" + body.strip("\n") + "\n"


def _derive_title(name: str) -> str:
    words = name.replace("-", " ").replace("_", " ").split()
    if words and words[0] in _TITLE_PREFIXES:
        words = words[1:]
    return " ".join(words) if words else name


@contextlib.contextmanager
def _locked_index(index_path: pathlib.Path) -> typing.Iterator[None]:
    """Hold an exclusive lock for the duration of one index read-modify-write.

    Atomic rename alone (:func:`atomic_write`) only protects a single
    file's own write from truncation -- it does not serialize two
    concurrent callers' read-then-replace of the *same* file. Without
    this lock, two agents writing different memories at once can each
    read the same ``MEMORY.md``, append only their own entry, and
    atomically replace it; the later replacement silently discards the
    earlier caller's entry even though both memory files were written
    successfully. A POSIX advisory lock (``fcntl.flock``) on a sibling
    lock file serializes the whole read-modify-write sequence instead.
    """

    index_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = index_path.parent / f".{index_path.name}.lock"
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def _ensure_index_entry(
    index_path: pathlib.Path, *, filename: str, name: str, description: str
) -> bool:
    """Add or refresh ``filename``'s one-line entry in ``MEMORY.md``.

    Returns whether the index changed. Matching by the ``(filename)`` link
    target, not the whole line, so refreshing an entry's description does
    not create a duplicate. The whole read-modify-write happens under
    :func:`_locked_index` so a concurrent writer's entry is never lost.
    """

    hook = description if len(description) <= 150 else description[:147] + "..."
    entry_line = f"- [{_derive_title(name)}]({filename}) — {hook}"

    with _locked_index(index_path):
        if index_path.exists():
            lines = index_path.read_text(encoding="utf-8").splitlines()
        else:
            lines = ["# Memory Index"]

        marker = f"]({filename})"
        for i, line in enumerate(lines):
            if marker in line:
                if line == entry_line:
                    return False
                lines[i] = entry_line
                atomic_write(index_path, "\n".join(lines) + "\n")
                return True

        lines.append(entry_line)
        atomic_write(index_path, "\n".join(lines) + "\n")
        return True


@dataclasses.dataclass(frozen=True)
class WriteResult:
    memory_path: pathlib.Path
    index_path: pathlib.Path
    index_updated: bool


def write_memory(
    project_root: str | pathlib.Path,
    name: str,
    *,
    description: str,
    type_: str,
    agent: str,
    body: str,
    applies_to: typing.Sequence[str] | None = None,
    claude_projects_root: str | pathlib.Path | None = None,
    force: bool = False,
) -> WriteResult:
    """Validate and write one memory file, then update its ``MEMORY.md`` entry.

    Crash-consistency ordering (PROP-LRH-MEMORY-COMMAND Decision 4): the
    memory-file rename happens *before* the ``MEMORY.md`` rename. An
    interruption between the two always fails toward an unindexed-but-
    content-complete file -- the "unindexed" category :func:`validate_corpus`
    detects (independent of frontmatter completeness) and
    :func:`repair_memory` fixes by re-running this same write path -- never
    toward an index entry pointing at a file that was never written.
    """

    _validate_new_write_fields(name, description, type_, agent)
    applies_to = tuple(applies_to) if applies_to else (agent,)

    memory_dir = memory_dir_for_project(project_root, claude_projects_root)
    memory_dir.mkdir(parents=True, exist_ok=True)
    filename = filename_for(name)
    memory_path = memory_dir / filename

    if memory_path.exists() and not force:
        existing_frontmatter, _ = read_frontmatter_and_body(
            memory_path.read_text(encoding="utf-8")
        )
        existing_metadata = existing_frontmatter.get("metadata") or {}
        existing_authored_by = (
            existing_metadata.get("authored_by")
            if isinstance(existing_metadata, dict)
            else None
        )
        if existing_authored_by and existing_authored_by != agent:
            raise MemoryValidationError(
                f"{filename} is authored_by {existing_authored_by!r}; "
                f"refusing to overwrite as {agent!r} without --force"
            )

    content = _render_memory_file(
        name=name,
        description=description,
        type_=type_,
        authored_by=agent,
        applies_to=applies_to,
        body=body,
    )
    # Memory-file rename first -- see the crash-consistency note above.
    atomic_write(memory_path, content)

    index_path = memory_dir / INDEX_FILENAME
    index_updated = _ensure_index_entry(
        index_path, filename=filename, name=name, description=description
    )
    return WriteResult(
        memory_path=memory_path, index_path=index_path, index_updated=index_updated
    )


@dataclasses.dataclass(frozen=True)
class IndexEntry:
    filename: str
    line: str
    authored_by: str | None


def list_memories(
    project_root: str | pathlib.Path,
    *,
    claude_projects_root: str | pathlib.Path | None = None,
    agent: str | None = None,
) -> list[IndexEntry]:
    """Return the ``MEMORY.md`` index, optionally filtered by ``authored_by``."""

    memory_dir = memory_dir_for_project(project_root, claude_projects_root)
    index_path = memory_dir / INDEX_FILENAME
    if not index_path.exists():
        return []

    entries: list[IndexEntry] = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ["):
            continue
        match = re.search(r"\]\(([^)]+)\)", stripped)
        if match is None:
            continue
        filename = match.group(1)
        # A crafted or corrupted index line could point outside the corpus
        # (e.g. `../../secret.md`) -- only ever resolve a flat filename
        # matching what filename_for() itself can produce, never a path
        # with separators or a traversal segment.
        if (
            not filename
            or "/" in filename
            or "\\" in filename
            or filename in (".", "..")
        ):
            continue
        authored_by = None
        candidate = memory_dir / filename
        if candidate.exists():
            try:
                frontmatter, _ = read_frontmatter_and_body(
                    candidate.read_text(encoding="utf-8")
                )
            except MemoryValidationError:
                frontmatter = {}
            metadata = frontmatter.get("metadata") or {}
            if isinstance(metadata, dict):
                authored_by = metadata.get("authored_by")
        if agent is not None and authored_by != agent:
            continue
        entries.append(
            IndexEntry(filename=filename, line=stripped, authored_by=authored_by)
        )
    return entries


@dataclasses.dataclass(frozen=True)
class ValidationReport:
    malformed: tuple[str, ...]
    unindexed: tuple[str, ...]
    legacy: tuple[str, ...]
    conforming: tuple[str, ...]


def _indexed_filenames(index_path: pathlib.Path) -> set[str]:
    if not index_path.exists():
        return set()
    filenames: set[str] = set()
    for line in index_path.read_text(encoding="utf-8").splitlines():
        match = re.search(r"\]\(([^)]+)\)", line.strip())
        if match:
            filenames.add(match.group(1))
    return filenames


def validate_corpus(
    project_root: str | pathlib.Path,
    claude_projects_root: str | pathlib.Path | None = None,
) -> ValidationReport:
    """Audit a memory corpus: malformed, unindexed, legacy, or conforming.

    Four tiers, not the two-tier malformed/legacy split alone. Scanning
    only file *contents* cannot detect the exact crash state Decision 4's
    write ordering intentionally permits: an interruption between the
    memory-file rename and the ``MEMORY.md`` rename leaves a
    content-complete file -- even one with ``authored_by`` set -- that is
    unreachable by recall because nothing links to it. That file must not
    be reported as ``conforming`` just because its own frontmatter is
    valid, so index membership is checked independently of frontmatter
    shape:

    - *malformed* -- missing ``name``/``description``/``metadata.type``,
      the original 19-file defect, unreachable by recall.
    - *unindexed* -- frontmatter is structurally fine (name/description/
      type present) but the file has no ``MEMORY.md`` entry -- also
      unreachable by recall, regardless of whether ``authored_by`` is
      set. Checked before the legacy/conforming split below, since an
      unindexed file's ``authored_by`` status doesn't change that it's
      unreachable either way.
    - *legacy* -- indexed and structurally conforming to the pre-existing
      schema, simply predating ``metadata.authored_by`` -- reachable and
      correct, just unattributed, and a :func:`repair_memory` candidate
      per Decision 3's grandfathering clause.
    - *conforming* -- indexed, with ``authored_by`` set.

    Only ``write`` enforces ``authored_by`` as a hard requirement; this
    reports its absence as a separate, non-error category.
    """

    memory_dir = memory_dir_for_project(project_root, claude_projects_root)
    malformed: list[str] = []
    unindexed: list[str] = []
    legacy: list[str] = []
    conforming: list[str] = []

    if not memory_dir.exists():
        return ValidationReport(malformed=(), unindexed=(), legacy=(), conforming=())

    indexed = _indexed_filenames(memory_dir / INDEX_FILENAME)

    for path in sorted(memory_dir.glob("*.md")):
        if path.name == INDEX_FILENAME:
            continue
        try:
            frontmatter, _ = read_frontmatter_and_body(path.read_text(encoding="utf-8"))
        except MemoryValidationError:
            malformed.append(path.name)
            continue

        name = frontmatter.get("name")
        description = frontmatter.get("description")
        metadata = frontmatter.get("metadata")
        type_ = metadata.get("type") if isinstance(metadata, dict) else None
        if not name or not description or type_ not in VALID_TYPES:
            malformed.append(path.name)
            continue

        if path.name not in indexed:
            unindexed.append(path.name)
            continue

        authored_by = (
            metadata.get("authored_by") if isinstance(metadata, dict) else None
        )
        if not authored_by:
            legacy.append(path.name)
        else:
            conforming.append(path.name)

    return ValidationReport(
        malformed=tuple(malformed),
        unindexed=tuple(unindexed),
        legacy=tuple(legacy),
        conforming=tuple(conforming),
    )


def repair_memory(
    project_root: str | pathlib.Path,
    name: str,
    *,
    sets: dict[str, str],
    claude_projects_root: str | pathlib.Path | None = None,
    dry_run: bool = False,
) -> pathlib.Path:
    """Conservative, structural-only fix-up of one existing memory's frontmatter.

    Never touches body content. Preserves the original ``authored_by``
    unless ``sets`` explicitly includes ``metadata.authored_by`` -- a
    structural fix is not a re-authoring. Routes through
    :func:`write_memory`'s own validated path (not a separate write
    mechanism), per the same discipline already applied to ``import``.
    """

    slug = name[: -len(".md")] if name.endswith(".md") else name
    _validate_name(slug)

    memory_dir = memory_dir_for_project(project_root, claude_projects_root)
    filename = filename_for(slug)
    memory_path = memory_dir / filename
    if not memory_path.exists():
        raise MemoryValidationError(
            f"no memory file found for {name!r} at {memory_path}"
        )

    if "name" in sets:
        raise MemoryValidationError(
            "repair does not support renaming a memory via --set name=<...>; "
            "it would leave the original file and its old index entry orphaned "
            "as a stale duplicate. Repair is structural-field-only by design."
        )

    frontmatter, body = read_frontmatter_and_body(
        memory_path.read_text(encoding="utf-8")
    )
    raw_metadata = frontmatter.get("metadata")
    # A malformed repair target's `metadata` key can itself be a
    # non-mapping value (e.g. `metadata: broken`) -- dict(raw_metadata)
    # would raise TypeError in that case rather than the intended
    # MemoryValidationError. Since repair exists to recover from exactly
    # this kind of malformed state, treat a non-mapping metadata as
    # empty and let --set populate it, rather than crashing.
    metadata = dict(raw_metadata) if isinstance(raw_metadata, dict) else {}
    merged_name = frontmatter.get("name", slug)
    merged_description = frontmatter.get("description", "")

    for key, value in sets.items():
        if key == "metadata.authored_by":
            metadata["authored_by"] = value
        elif key == "metadata.applies_to":
            metadata["applies_to"] = [
                item.strip() for item in value.split(",") if item.strip()
            ]
        elif key == "metadata.type":
            metadata["type"] = value
        elif key == "description":
            merged_description = value
        else:
            raise MemoryValidationError(f"unsupported --set key: {key!r}")

    authored_by = metadata.get("authored_by")
    if not authored_by:
        raise MemoryValidationError(
            f"{memory_path} has no authored_by to preserve or override; "
            "pass --set metadata.authored_by=<agent> explicitly"
        )
    type_ = metadata.get("type")
    if type_ not in VALID_TYPES:
        raise MemoryValidationError(
            f"{memory_path} has no valid metadata.type to repair against "
            f"(got {type_!r}); pass --set metadata.type=<one of {VALID_TYPES}>"
        )

    if dry_run:
        return memory_path

    applies_to = metadata.get("applies_to") or [authored_by]
    result = write_memory(
        project_root,
        merged_name,
        description=merged_description,
        type_=type_,
        agent=authored_by,
        applies_to=applies_to,
        body=body,
        claude_projects_root=claude_projects_root,
        force=True,
    )
    return result.memory_path


def _utc_now_compact() -> str:
    """A filesystem-safe timestamp for snapshot filenames (no ``:``)."""

    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


@dataclasses.dataclass(frozen=True)
class SyncEntry:
    source: pathlib.Path
    dest: pathlib.Path
    copied: bool
    snapshot: pathlib.Path | None


def sync_memory(
    project_root: str | pathlib.Path,
    *,
    claude_projects_root: str | pathlib.Path | None = None,
    archive_root: str | pathlib.Path | None = None,
    dry_run: bool = False,
    timestamp: str | None = None,
) -> list[SyncEntry]:
    """Mirror a project's memory corpus into the durable archive root.

    Reuses :func:`prompt_workflow_sessions.mirror_file_with_snapshot`
    (Decision 6's snapshot-before-overwrite invariant, not
    ``mirror_transcript``'s never-shrink invariant, which would wrongly
    block a legitimate ``consolidate-memory`` shrink). Mirrors every
    ``*.md`` file under the corpus, including ``MEMORY.md`` itself, into
    ``<archive_root>/raw/<slug>/memory/**`` -- matching ``sessions
    sync``'s own ``raw/<slug>/`` layout, per Decision 5's "independent
    subcommand, shared conventions" choice.
    """

    memory_dir = memory_dir_for_project(project_root, claude_projects_root)
    if not memory_dir.exists():
        return []

    resolved_archive_root = prompt_workflow_sessions.resolve_archive_root(
        archive_root
    ).resolve()
    resolved_memory_dir = memory_dir.resolve()
    # Either direction of nesting (archive root inside the memory corpus, or
    # vice versa) has the same failure mode: the next run's `rglob("*.md")`
    # would pick up the archive's own prior output and re-mirror it one level
    # deeper, growing without bound. Equality is covered by both `in` checks
    # (a path is always a member of its own `(self, *self.parents)` tuple).
    if resolved_memory_dir in (resolved_archive_root, *resolved_archive_root.parents):
        raise MemoryValidationError(
            f"archive root {resolved_archive_root} is nested under (or equal "
            f"to) the memory corpus {resolved_memory_dir}; each sync would "
            "re-mirror its own prior output, growing without bound -- choose "
            "an archive root outside the memory corpus"
        )
    if resolved_archive_root in (resolved_memory_dir, *resolved_memory_dir.parents):
        raise MemoryValidationError(
            f"memory corpus {resolved_memory_dir} is nested under (or equal "
            f"to) the archive root {resolved_archive_root}; each sync would "
            "re-mirror its own prior output, growing without bound -- choose "
            "an archive root outside the memory corpus"
        )

    project_slug = project_slug_for_path(project_root)
    resolved_timestamp = timestamp or _utc_now_compact()

    entries: list[SyncEntry] = []
    for path in sorted(memory_dir.rglob("*.md")):
        relpath = path.relative_to(memory_dir)
        dest = resolved_archive_root / "raw" / project_slug / MEMORY_DIRNAME / relpath
        if dry_run:
            source_data = path.read_bytes()
            copied = not dest.exists() or dest.read_bytes() != source_data
            entries.append(
                SyncEntry(source=path, dest=dest, copied=copied, snapshot=None)
            )
            continue
        history_dir = (
            resolved_archive_root
            / "history"
            / project_slug
            / MEMORY_DIRNAME
            / relpath.parent
        )
        result = prompt_workflow_sessions.mirror_file_with_snapshot(
            path, dest, history_dir=history_dir, timestamp=resolved_timestamp
        )
        entries.append(
            SyncEntry(
                source=path,
                dest=result.dest,
                copied=result.copied,
                snapshot=result.snapshot,
            )
        )
    return entries
