"""Core logic for ``lrh memory`` -- validated writes to Claude Code's
per-project memory corpus (``~/.claude/projects/<slug>/memory/``).

Implements Stage 1 of PROP-LRH-MEMORY-COMMAND: ``write``, ``list``,
``validate``, and ``repair`` (Decision 9's fast follow-up), Stage 2's
``sync`` (WI-LRH-MEMORY-ARCHIVE-SIDE, Decisions 5-6), Stage 3's ``read``/
``search`` (WI-LRH-MEMORY-READ-SIDE, Decision 7), and Stage 4's
``export``/``import``/``transfer`` (WI-LRH-MEMORY-PORTABILITY, Decision 8).
Resolves the corpus path via ``project_slug_for_path`` (reused from
``prompt_workflow_sessions``, not reimplemented -- see that proposal's
Decision 4).
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime
import fcntl
import json
import os
import pathlib
import re
import subprocess
import tempfile
import typing

import yaml

from lrh import prompt_workflow_sessions
from lrh.atomic_write import atomic_write, atomic_write_bytes
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
    slug = project_slug_for_path(canonical_project_root(project_root))
    return root / slug / MEMORY_DIRNAME


def canonical_project_root(project_root: str | pathlib.Path) -> pathlib.Path:
    """Map a linked git worktree to its main checkout; otherwise return
    ``project_root`` unchanged.

    Claude Code keys a session's *transcript* bucket on the literal cwd
    (a worktree gets a ``--claude-worktrees-<name>`` suffixed slug) but
    keys its auto-memory corpus on the main repository, so a memory
    written to the worktree's own slug lands where no future session
    reads it. Detection compares ``git rev-parse --git-dir`` with
    ``--git-common-dir``: they differ only in a linked worktree. A
    non-git directory, a missing ``git``, a bare repository, or a
    submodule (git-dir equals git-common-dir) all fall through to the
    unmodified path. The result is git's own spelling of the main
    checkout path -- it does not follow symlinks itself, but git may
    already have resolved one.
    """

    root = pathlib.Path(project_root).expanduser()
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--git-dir", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return root
    lines = completed.stdout.splitlines()
    if completed.returncode != 0 or len(lines) != 2:
        return root
    # ``root / <git output>`` deliberately relies on pathlib discarding
    # ``root`` when git prints an absolute path (the linked-worktree case).
    git_dir = os.path.realpath(root / lines[0])
    common_dir = os.path.realpath(root / lines[1])
    if git_dir == common_dir or os.path.basename(common_dir) != ".git":
        return root
    return pathlib.Path(os.path.dirname(common_dir))


def worktree_mapping_note(project_root: str | pathlib.Path) -> str | None:
    """Return a one-line explanation when ``project_root`` is mapped to a
    different (main-checkout) corpus, else ``None``."""

    canonical = canonical_project_root(project_root)
    if project_slug_for_path(canonical) == project_slug_for_path(project_root):
        return None
    return (
        f"note: {pathlib.Path(project_root).resolve()} is a linked git worktree; "
        f"using the memory corpus of its main checkout {canonical}"
    )


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


def _split_frontmatter_text_and_body(text: str) -> tuple[str, str]:
    """Split a memory Markdown file into its raw (unparsed) frontmatter
    text and its body, on the ``---`` delimiters. Shared by
    :func:`read_frontmatter_and_body` (which parses the frontmatter text as
    YAML) and :func:`repair_memory` (which also needs the raw text, to
    preserve unknown lines byte-for-byte -- see
    :func:`_extract_preserved_frontmatter_lines`)."""

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
    return frontmatter_text, body


def read_frontmatter_and_body(text: str) -> tuple[dict[str, typing.Any], str]:
    """Split a memory Markdown file into its YAML frontmatter and body.

    Uses ``yaml.safe_load`` (not the constrained ``lrh.control.parser``
    parser, which rejects the nested ``metadata:`` mapping this schema
    requires) so ``metadata.type``/``metadata.authored_by``/
    ``metadata.applies_to`` parse correctly.
    """

    frontmatter_text, body = _split_frontmatter_text_and_body(text)
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as error:
        raise MemoryValidationError(f"invalid YAML frontmatter: {error}") from error
    if not isinstance(frontmatter, dict):
        raise MemoryValidationError("frontmatter must be a YAML mapping")
    return frontmatter, body


_CANONICAL_TOP_LEVEL_KEYS = frozenset({"name", "description", "metadata"})
_CANONICAL_METADATA_KEYS = frozenset({"type", "authored_by", "applies_to"})


class _UnsupportedPreservedKey(MemoryValidationError):
    """An unknown frontmatter key's value is not a single-line scalar, or
    ``metadata:`` itself carries inline flow content -- see
    :func:`_extract_preserved_frontmatter_lines`."""


def _extract_preserved_frontmatter_lines(
    frontmatter_text: str,
) -> tuple[list[str], list[str]]:
    """Split a raw (pre-parse) frontmatter block's unknown keys out of the
    canonical ones (``name``/``description``/``metadata``, and inside
    ``metadata``: ``type``/``authored_by``/``applies_to``).

    Returns ``(preserved_top_level_lines, preserved_metadata_lines)`` --
    kept as two *separate* lists, not one merged list, because they must
    be re-emitted at different nesting depths in the output: a top-level
    unknown key belongs after the whole ``metadata:`` block, while a
    ``metadata``-nested unknown key belongs *inside* it. Concatenating
    them into one undifferentiated list (an earlier version of this
    function did) can interleave a top-level line between the
    metadata-nested lines and the metadata mapping they belong to,
    producing frontmatter that no longer parses as YAML at all.

    Lines are captured verbatim, not re-serialized, so an unquoted scalar
    (an ISO timestamp, for example) survives byte-for-byte instead of
    being rewritten by a YAML parse-then-dump round trip (``yaml.safe_load``
    parses an unquoted ``2026-08-19T04:27:39.225Z`` into a ``datetime``,
    and ``safe_dump`` then emits it as
    ``2026-08-19 04:27:39.225000+00:00`` -- a different string).

    Scoped to *top-level* keys and to keys nested exactly one level under
    ``metadata:`` -- this module's own schema never nests deeper. Each
    preserved key's own line (whatever it holds -- a plain scalar, a
    null, or a single-line flow collection like ``tags: [a, b]``, all of
    which every real Claude-Code-auto-memory key observed --
    ``node_type``, ``originSessionId``, ``modified`` -- and this module's
    own writer produce) is captured and preserved verbatim as-is. Only a
    value that *continues onto further lines* -- a block sequence
    (``tags:`` followed by ``- a``/``- b`` on their own lines), a block
    scalar (``|``/``>``), or any other multi-line form -- cannot be
    safely re-nested at the correct depth by a line-based split, and
    repair is conservative by design (Decision 9): it raises
    :class:`_UnsupportedPreservedKey` for that case rather than guess and
    risk silently dropping or misplacing content. Likewise, ``metadata:``
    written with inline flow-*mapping* content on its own line (e.g.
    ``metadata: {type: x, extra: y}``) is rejected the same way, since
    its extra keys cannot be reliably separated from the canonical ones
    without a real YAML parse -- the very round trip this function exists
    to avoid for value fidelity. A non-mapping ``metadata:`` scalar (e.g.
    the malformed ``metadata: broken`` :func:`repair_memory` separately
    recovers from) is not rejected here -- it simply has no extra keys to
    preserve.
    """

    lines = frontmatter_text.split("\n")
    preserved_top_level: list[str] = []
    preserved_metadata: list[str] = []
    seen_top_level_keys: set[str] = set()
    seen_metadata_keys: set[str] = set()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if line[:1].isspace():
            # A continuation line encountered before any top-level key has
            # started (should not happen in a well-formed document) --
            # nothing to attach it to; drop it rather than misfile it.
            i += 1
            continue
        key_match = re.match(r"^(\S[^:]*):(.*)$", line)
        if key_match is None:
            # Not a recognizable ``key: value`` line at this indent (e.g. a
            # continuation of a folded/multi-line scalar) -- keep attached
            # to whichever key most recently started; nothing to extract
            # from it on its own.
            i += 1
            continue
        key = key_match.group(1).strip()
        inline_value = key_match.group(2).strip()
        block_start = i
        i = _consume_frontmatter_block(lines, i + 1, key_indent=0)
        block_lines = lines[block_start:i]
        if key == "metadata":
            if inline_value.startswith("{"):
                # Flow-style mapping (e.g. `metadata: {type: x, extra: y}`)
                # -- its extra keys can't be reliably separated from the
                # canonical ones without a real YAML parse. A non-mapping
                # scalar value (e.g. `metadata: broken`, already-malformed
                # input `repair_memory` is designed to recover from
                # separately) has no extra keys to preserve either way, so
                # it is not rejected here -- there is simply nothing to do.
                raise _UnsupportedPreservedKey(
                    "repair cannot preserve extra keys from a 'metadata:' "
                    "line written with inline flow content "
                    f"({line!r}); rewrite it as a block mapping first"
                )
            j = 1
            while j < len(block_lines):
                nested_match = re.match(r"^\s+(\S[^:]*):(.*)$", block_lines[j])
                if nested_match is None:
                    j += 1
                    continue
                nested_key = nested_match.group(1).strip()
                nested_indent = len(block_lines[j]) - len(block_lines[j].lstrip())
                nested_start = j
                j = _consume_frontmatter_block(
                    block_lines, j + 1, key_indent=nested_indent
                )
                nested_block = block_lines[nested_start:j]
                if nested_key in _CANONICAL_METADATA_KEYS:
                    continue
                if len(nested_block) != 1:
                    raise _UnsupportedPreservedKey(
                        f"repair cannot preserve metadata.{nested_key!r}: "
                        "its value spans multiple lines "
                        "(a block sequence or multi-line scalar), which a "
                        "line-based preservation cannot safely re-nest"
                    )
                # A missing inline value on `nested_block[0]` is not
                # rejected here -- `weird:` alone (with no continuation
                # line, already guaranteed by the length-1 check above) is
                # ordinary YAML for a null scalar, not an unrepresentable
                # nested block; the line is preserved verbatim either way.
                if nested_key in seen_metadata_keys:
                    # A duplicate key in the source is itself malformed
                    # YAML semantics (a parser silently keeps only the
                    # last occurrence) -- splicing both lines through
                    # verbatim would reproduce that same silent collapse
                    # in the output with no warning. Every other
                    # unrepresentable shape this function encounters is
                    # rejected rather than guessed at; a duplicate key is
                    # no different.
                    raise _UnsupportedPreservedKey(
                        f"repair cannot preserve metadata.{nested_key!r}: "
                        "it appears more than once in the source "
                        "frontmatter, which is already ambiguous YAML"
                    )
                seen_metadata_keys.add(nested_key)
                preserved_metadata.append(nested_block[0])
        elif key not in _CANONICAL_TOP_LEVEL_KEYS:
            if len(block_lines) != 1:
                raise _UnsupportedPreservedKey(
                    f"repair cannot preserve top-level key {key!r}: its "
                    "value spans multiple lines (a block sequence or "
                    "multi-line scalar), which a line-based preservation "
                    "cannot safely re-nest"
                )
            # A missing `inline_value` is not rejected here for the same
            # reason as the metadata-nested case above (`custom:` alone is
            # a valid null scalar, not an unrepresentable nested block).
            if key in seen_top_level_keys:
                raise _UnsupportedPreservedKey(
                    f"repair cannot preserve top-level key {key!r}: it "
                    "appears more than once in the source frontmatter, "
                    "which is already ambiguous YAML"
                )
            seen_top_level_keys.add(key)
            preserved_top_level.append(block_lines[0])
    return preserved_top_level, preserved_metadata


def _consume_frontmatter_block(
    lines: typing.Sequence[str], start: int, *, key_indent: int
) -> int:
    """Return the index just past the lines that continue a ``key:`` line
    written at ``key_indent``, starting the scan at ``start`` (the line
    right after the key's own line).

    A continuation is either (a) a line indented *more* than the key --
    the conventional nested-content/continuation case -- or (b) a line at
    *exactly* the key's own indentation whose stripped text starts with
    ``- `` or is exactly ``-`` -- a YAML block sequence written at the
    same indentation as its key (``tags:\\n- a\\n- b``), the idiomatic and
    most common block-sequence style, and one PyYAML's own ``safe_dump``
    itself produces (see :func:`_render_memory_file`). Without case (b), a
    sibling-indented sequence looks identical, line by line, to a bare
    ``key:`` followed by unrelated content -- exactly the shape of a
    genuine null-valued scalar (``custom:`` alone) -- so failing to
    recognize it as *this key's own* content would let its items fall
    through as unrecognized lines and be silently dropped instead of
    correctly flagged (via the caller's length check) as an
    unrepresentable multi-line value.

    A blank or comment line is looked *past*, never consumed outright:
    PyYAML tolerates either inside a block sequence (``tags:\\n\\n- a\\n- b``
    and ``tags:\\n# note\\n- a\\n- b`` both parse the same as without the
    interruption), so neither can itself decide whether the block
    continues -- only what follows it can. Consuming such a line
    unconditionally (an earlier version of this function did, for blank
    lines only) would inflate a genuinely single-line key's block by one
    line whenever it happened to be followed by a blank/comment line
    before the next real key, misclassifying it as unsupported; *not*
    looking past one at all would instead terminate a real block
    sequence's scan the moment a blank or comment line appeared inside
    it, silently dropping the sequence items that come after -- exactly
    the class of data loss this function exists to prevent (a comment
    line reproduces the same failure mode a blank line does, just via a
    different trigger, since both are structurally invisible to YAML).
    Looking ahead past any run of blank/comment lines to find the next
    substantive line, and only advancing past them when that line
    actually continues the block, avoids both failure modes.
    """

    i = start
    while i < len(lines):
        peek = i
        while peek < len(lines) and (
            not lines[peek].strip() or lines[peek].strip().startswith("#")
        ):
            peek += 1
        if peek >= len(lines):
            break
        candidate = lines[peek]
        candidate_indent = len(candidate) - len(candidate.lstrip())
        if candidate_indent > key_indent:
            i = peek + 1
            continue
        if candidate_indent == key_indent and (
            candidate.lstrip() == "-" or candidate.lstrip().startswith("- ")
        ):
            i = peek + 1
            continue
        break
    return i


def _render_memory_file(
    *,
    name: str,
    description: str,
    type_: str,
    authored_by: str,
    applies_to: typing.Sequence[str],
    body: str,
    preserved_top_level_lines: typing.Sequence[str] = (),
    preserved_metadata_lines: typing.Sequence[str] = (),
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

    ``preserved_top_level_lines``/``preserved_metadata_lines`` (from
    :func:`_extract_preserved_frontmatter_lines`) are appended verbatim,
    never re-serialized, so their exact text (including any timestamp a
    YAML round trip would otherwise reformat) survives unchanged. They
    are rendered at *different* nesting depths -- the top-level and
    ``metadata`` dicts are ``yaml.safe_dump``-ed separately and then
    combined, specifically so a metadata-nested preserved line can be
    spliced inside the ``metadata:`` block rather than appended after it
    finishes; concatenating both preserved groups into one flat, appended
    block (an earlier version of this function did) can place a
    metadata-nested line after an unrelated top-level line, producing
    frontmatter that no longer parses as YAML at all. Canonical fields
    always take precedence: a preserved line can never carry ``name``,
    ``description``, or a ``metadata.{type,authored_by,applies_to}`` key,
    since those keys are excluded before this function ever sees them.
    """

    applies_to_list = list(applies_to) if applies_to else [authored_by]
    top_level_text = yaml.safe_dump(
        {"name": name, "description": description},
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )
    metadata_text = yaml.safe_dump(
        {
            "type": type_,
            "authored_by": authored_by,
            "applies_to": applies_to_list,
        },
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )
    metadata_lines = ["  " + line for line in metadata_text.rstrip("\n").split("\n")]
    metadata_lines.extend(preserved_metadata_lines)
    frontmatter_lines = (
        top_level_text.rstrip("\n").split("\n") + ["metadata:"] + metadata_lines
    )
    frontmatter_lines.extend(preserved_top_level_lines)
    frontmatter_text = "\n".join(frontmatter_lines) + "\n"
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


@contextlib.contextmanager
def _locked_memory_path(path: pathlib.Path) -> typing.Iterator[None]:
    """Hold an exclusive lock for the duration of one memory file's
    read-snapshot-write sequence -- the same pattern :func:`_locked_index`
    uses for ``MEMORY.md``, and :func:`prompt_workflow_sessions._locked_dest`
    uses for ``sync``'s own snapshot-before-overwrite.

    Without this, two concurrent forced ``transfer``/``import`` calls
    targeting the same destination memory can each read the same prior
    content, snapshot it, and overwrite -- silently dropping whichever
    version landed on the destination between the two reads (never
    snapshotted, never left current). A POSIX advisory lock on a sibling
    lock file serializes the whole guard-check-then-write sequence per
    destination path.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.parent / f".{path.name}.lock"
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


def _write_memory_into_dir(
    memory_dir: pathlib.Path,
    name: str,
    *,
    description: str,
    type_: str,
    agent: str,
    body: str,
    applies_to: typing.Sequence[str] | None = None,
    force: bool = False,
    dry_run: bool = False,
    preserved_top_level_lines: typing.Sequence[str] = (),
    preserved_metadata_lines: typing.Sequence[str] = (),
) -> WriteResult:
    """Core of :func:`write_memory`, taking an already-resolved ``memory_dir``.

    Factored out so :func:`import_memories`/:func:`transfer_memories` can
    write through this exact validated path against a directly-resolved
    corpus directory (``transfer``'s ``--to`` may name a slug rather than a
    project path -- see :func:`_resolve_memory_dir`) without re-deriving a
    slug from a string that was never a filesystem path to begin with.

    ``dry_run`` runs every validation and conflict check below -- field
    validation, the cross-agent overwrite guard -- without touching the
    filesystem at all (no directory creation, no file write), so a caller
    previewing an import/transfer sees exactly the same accept/reject
    outcome a real run would produce, not merely "well-formed enough to
    reach this function."

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

    filename = filename_for(name)
    memory_path = memory_dir / filename
    index_path = memory_dir / INDEX_FILENAME

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

    if dry_run:
        return WriteResult(
            memory_path=memory_path, index_path=index_path, index_updated=False
        )

    memory_dir.mkdir(parents=True, exist_ok=True)
    content = _render_memory_file(
        name=name,
        description=description,
        type_=type_,
        authored_by=agent,
        applies_to=applies_to,
        body=body,
        preserved_top_level_lines=preserved_top_level_lines,
        preserved_metadata_lines=preserved_metadata_lines,
    )
    # Memory-file rename first -- see the crash-consistency note above.
    atomic_write(memory_path, content)

    index_updated = _ensure_index_entry(
        index_path, filename=filename, name=name, description=description
    )
    return WriteResult(
        memory_path=memory_path, index_path=index_path, index_updated=index_updated
    )


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
    preserved_top_level_lines: typing.Sequence[str] = (),
    preserved_metadata_lines: typing.Sequence[str] = (),
) -> WriteResult:
    """Validate and write one memory file, then update its ``MEMORY.md`` entry."""

    memory_dir = memory_dir_for_project(project_root, claude_projects_root)
    return _write_memory_into_dir(
        memory_dir,
        name,
        description=description,
        type_=type_,
        agent=agent,
        body=body,
        applies_to=applies_to,
        force=force,
        preserved_top_level_lines=preserved_top_level_lines,
        preserved_metadata_lines=preserved_metadata_lines,
    )


@dataclasses.dataclass(frozen=True)
class IndexEntry:
    filename: str
    line: str
    authored_by: str | None


def _list_memories_in_dir(
    memory_dir: pathlib.Path, *, agent: str | None = None
) -> list[IndexEntry]:
    """Core of :func:`list_memories`, taking an already-resolved ``memory_dir``."""

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


def list_memories(
    project_root: str | pathlib.Path,
    *,
    claude_projects_root: str | pathlib.Path | None = None,
    agent: str | None = None,
) -> list[IndexEntry]:
    """Return the ``MEMORY.md`` index, optionally filtered by ``authored_by``."""

    memory_dir = memory_dir_for_project(project_root, claude_projects_root)
    return _list_memories_in_dir(memory_dir, agent=agent)


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


def _structural_problem(frontmatter: dict[str, typing.Any]) -> str | None:
    """Return why ``frontmatter`` is structurally malformed (missing
    ``name``/``description``/``metadata.type``, or an invalid type), or
    ``None`` when it conforms. Shared by :func:`validate_corpus` and
    :func:`recover_orphan_memories` so recovery never introduces a file the
    corpus validator would immediately classify as malformed."""

    metadata = frontmatter.get("metadata")
    type_ = metadata.get("type") if isinstance(metadata, dict) else None
    if not frontmatter.get("name"):
        return "missing name"
    if not frontmatter.get("description"):
        return "missing description"
    if type_ not in VALID_TYPES:
        return f"missing or invalid metadata.type ({type_!r})"
    return None


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

        metadata = frontmatter.get("metadata")
        if _structural_problem(frontmatter) is not None:
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

    Also preserves any frontmatter key outside this module's own schema
    (``name``/``description``/``metadata.{type,authored_by,applies_to}``),
    such as Claude Code auto-memory's ``node_type``/``originSessionId``/
    ``modified`` -- byte-for-byte, not merely semantically, since a
    parse-then-``yaml.safe_dump`` round trip reformats an unquoted
    timestamp. See :func:`_extract_preserved_frontmatter_lines`. A
    preserved key can never shadow a canonical one: canonical fields are
    excluded from extraction before this function ever sees them.
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

    original_text = memory_path.read_text(encoding="utf-8")
    frontmatter, body = read_frontmatter_and_body(original_text)
    raw_frontmatter_text, _ = _split_frontmatter_text_and_body(original_text)
    preserved_top_level_lines, preserved_metadata_lines = (
        _extract_preserved_frontmatter_lines(raw_frontmatter_text)
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
        preserved_top_level_lines=preserved_top_level_lines,
        preserved_metadata_lines=preserved_metadata_lines,
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

    project_slug = project_slug_for_path(canonical_project_root(project_root))
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


# ---------------------------------------------------------------------------
# Portability: export / import / transfer (PROP-LRH-MEMORY-COMMAND Decision 8)
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ExportResult:
    output_path: pathlib.Path
    count: int


@dataclasses.dataclass(frozen=True)
class ImportEntry:
    name: str
    written: bool
    error: str | None


def _require_export_filter(
    names: typing.Sequence[str] | None, agent: str | None
) -> None:
    """Open Question 1 (resolved): no unfiltered "export everything"
    fallback. A full-corpus export/import could itself exceed the
    200-line ``MEMORY.md`` ceiling on the receiving end -- require a
    deliberate ``--name``/``--agent`` filter instead of guessing."""

    if not names and not agent:
        raise MemoryValidationError(
            "export/transfer require an explicit --name or --agent filter "
            "-- there is no unfiltered export-everything default"
        )


def _export_records_from_dir(
    memory_dir: pathlib.Path,
    project_slug: str,
    *,
    names: typing.Sequence[str] | None = None,
    agent: str | None = None,
) -> list[dict[str, typing.Any]]:
    _require_export_filter(names, agent)
    entries = _list_memories_in_dir(memory_dir, agent=agent)
    if names:
        wanted_filenames = {filename_for(n) for n in names}
        entries = [e for e in entries if e.filename in wanted_filenames]
    records: list[dict[str, typing.Any]] = []
    for entry in entries:
        path = memory_dir / entry.filename
        frontmatter, body = read_frontmatter_and_body(path.read_text(encoding="utf-8"))
        records.append(
            {
                "name": frontmatter.get("name"),
                "description": frontmatter.get("description"),
                "metadata": frontmatter.get("metadata"),
                "body": body,
                "exported_from_slug": project_slug,
            }
        )
    return records


def _write_bundle(
    output_path: pathlib.Path, records: list[dict[str, typing.Any]]
) -> None:
    """Write a portable bundle: one JSON object per memory, one per line
    (JSONL, matching ``project/sessions/index.jsonl``'s own convention --
    Open Question 2, resolved)."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, sort_keys=True) for record in records]
    content = "\n".join(lines) + ("\n" if lines else "")
    atomic_write(output_path, content)


def _read_bundle(input_path: pathlib.Path) -> list[typing.Any]:
    """Parse a bundle's lines as JSON. Does not require each line to decode
    to an object -- a malformed line (a JSON list, string, or number) is
    passed through as-is; :func:`_import_records_into_dir` is the layer
    responsible for rejecting it as a clean per-record error rather than
    crashing, since it is the one place both a bare CLI file read and a
    ``transfer``-internal bundle share."""

    records: list[typing.Any] = []
    for line in input_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def export_memories(
    project_root: str | pathlib.Path,
    *,
    output: str | pathlib.Path,
    names: typing.Sequence[str] | None = None,
    agent: str | None = None,
    claude_projects_root: str | pathlib.Path | None = None,
) -> ExportResult:
    """Export selected memories to a portable JSONL bundle with
    ``exported_from_slug`` provenance. Requires an explicit ``names``/
    ``agent`` filter -- see :func:`_require_export_filter`."""

    memory_dir = memory_dir_for_project(project_root, claude_projects_root)
    project_slug = project_slug_for_path(canonical_project_root(project_root))
    records = _export_records_from_dir(
        memory_dir, project_slug, names=names, agent=agent
    )
    output_path = pathlib.Path(output)
    _write_bundle(output_path, records)
    return ExportResult(output_path=output_path, count=len(records))


def _guard_import_overwrite(
    memory_dir: pathlib.Path,
    filename: str,
    *,
    agent: str | None,
    new_content: str | None,
    force: bool,
    dry_run: bool,
) -> None:
    """Guard ``transfer``/``import``'s write path against silently
    destroying a same-agent, legacy (no ``authored_by``), or malformed
    destination memory -- the same-agent case ``_write_memory_into_dir``
    itself intentionally leaves unconditional (so ``write_memory``'s own
    "revise my own memory" path keeps working), and the legacy case
    (``existing_authored_by`` absent) currently bypasses that function's
    cross-agent check entirely (``if existing_authored_by and
    existing_authored_by != agent`` -- an absent value is falsy, so the
    check never fires). This guard is deliberately a separate, additional
    check at ``transfer``/``import``'s own call site, not folded into
    ``_write_memory_into_dir``, so ``write_memory``'s behavior is
    unaffected (Required Change #2). Caller must hold
    :func:`_locked_memory_path` for ``memory_dir / filename`` for the
    duration of this call *and* the subsequent ``_write_memory_into_dir``
    call -- otherwise two concurrent forced overwrites of the same
    destination can each snapshot the same prior version and lose an
    intermediate one.

    Raises :class:`MemoryValidationError` when the destination exists,
    its ``authored_by`` is absent, unreadable/malformed, or matches
    ``agent``, and ``force`` was not given. A genuine cross-agent
    mismatch is left entirely to ``_write_memory_into_dir``'s own
    existing check (already requires ``force``, no snapshot -- out of
    this guard's scope).

    A destination whose frontmatter fails to parse (or whose bytes are
    not valid UTF-8) is treated the same as a legacy record -- not a
    hard error independent of ``force`` -- since
    ``_write_memory_into_dir`` itself already tolerates this: when
    ``force=True`` it skips parsing the destination entirely and
    overwrites unconditionally. This guard must not regress that; it
    snapshots the malformed file's raw bytes rather than failing to
    parse them.

    ``new_content`` is the exact bytes ``_write_memory_into_dir`` is
    about to write, pre-rendered by the caller (or ``None`` if it could
    not be computed, e.g. a malformed record whose own validation will
    reject it downstream anyway) -- when the destination's current
    content already equals it byte-for-byte, this is a genuine no-op
    (nothing would change), so no snapshot is taken at all. Without
    this, an unbounded sequence of identical-content snapshot files
    accumulates across repeated ``--force`` runs of an unchanged
    corpus, which ``sync`` itself would go on to recursively archive
    every round.

    When the overwrite is permitted (``force`` given), content genuinely
    differs, and this is not a ``dry_run``, snapshots the destination's
    current content into ``<memory_dir>/history/`` first -- keyed by
    content hash only (not a timestamp), so the same prior version is
    never snapshotted twice regardless of how many times it recurs --
    mirroring ``sync``'s own snapshot-before-overwrite invariant
    (``prompt_workflow_sessions.mirror_file_with_snapshot``). ``dry_run``
    performs the same accept/reject check but never touches the
    filesystem, matching ``_write_memory_into_dir``'s own ``dry_run``
    contract.
    """

    path = memory_dir / filename
    if not path.exists():
        return

    try:
        existing_bytes = path.read_bytes()
    except OSError as exc:
        raise MemoryValidationError(
            f"{filename} exists but could not be read: {exc}"
        ) from exc

    malformed = False
    existing_authored_by: str | None = None
    try:
        existing_frontmatter, _ = read_frontmatter_and_body(
            existing_bytes.decode("utf-8")
        )
        existing_metadata = existing_frontmatter.get("metadata") or {}
        existing_authored_by = (
            existing_metadata.get("authored_by")
            if isinstance(existing_metadata, dict)
            else None
        )
    except (MemoryValidationError, UnicodeDecodeError):
        malformed = True

    if existing_authored_by and existing_authored_by != agent:
        return  # genuine cross-agent conflict -- _write_memory_into_dir's own job

    if new_content is not None and existing_bytes == new_content.encode("utf-8"):
        return  # the write would change nothing -- no snapshot needed

    if not force:
        if malformed:
            reason = "malformed or unreadable frontmatter"
        elif existing_authored_by:
            reason = f"authored_by {existing_authored_by!r}"
        else:
            reason = "no authored_by (a legacy pre-schema record)"
        raise MemoryValidationError(
            f"{filename} already exists ({reason}); transfer/import refuses "
            "to overwrite it without --force"
        )

    if dry_run:
        return

    short_hash = prompt_workflow_sessions.content_hash(existing_bytes)[:12]
    history_dir = memory_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    stem = pathlib.Path(filename).stem
    suffix = pathlib.Path(filename).suffix
    snapshot_path = history_dir / f"{stem}.{short_hash}{suffix}"
    if not snapshot_path.exists():
        atomic_write_bytes(snapshot_path, existing_bytes)


def _import_records_into_dir(
    memory_dir: pathlib.Path,
    records: list[typing.Any],
    *,
    names: typing.Sequence[str] | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> list[ImportEntry]:
    if names:
        wanted = set(names)
        records = [
            record
            for record in records
            if isinstance(record, dict) and record.get("name") in wanted
        ]

    results: list[ImportEntry] = []
    for record in records:
        if not isinstance(record, dict):
            results.append(
                ImportEntry(
                    name=repr(record),
                    written=False,
                    error="bundle record is not a JSON object",
                )
            )
            continue

        name = record.get("name")
        metadata = record.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        agent = metadata.get("authored_by")
        applies_to = metadata.get("applies_to")
        type_ = metadata.get("type")
        description = record.get("description")
        body = record.get("body") or ""
        try:
            if applies_to is not None and not isinstance(applies_to, (list, tuple)):
                # A string applies_to would not raise inside
                # _write_memory_into_dir -- `tuple("not-a-list")` silently
                # succeeds, splitting the string into one bogus applies_to
                # entry per character, rather than crashing or being
                # rejected. Reject it explicitly at the bundle boundary
                # instead of writing corrupted metadata.
                raise MemoryValidationError(
                    "bundle record 'metadata.applies_to' must be a list, "
                    f"got {type(applies_to).__name__}"
                )
            if isinstance(name, str) and name:
                # Same-agent/legacy/malformed overwrite guard -- transfer/
                # import's own call site only (Required Change #2);
                # write_memory's direct path is untouched. _validate_name
                # must run *before* the guard, not after: the guard builds
                # a filesystem path from `name` (via filename_for) and
                # reads whatever it finds there -- an unvalidated bundle
                # `name` containing `../` segments would let a crafted
                # import record read an arbitrary file outside the corpus
                # and copy its content into <memory_dir>/history/ as a
                # side effect, even though the record is ultimately (and
                # only afterward) rejected with a clean-looking "not a
                # valid kebab-case slug" error. Raising here produces the
                # exact same error message _write_memory_into_dir's own
                # validation would, just before any filesystem access
                # rather than after.
                _validate_name(name)
                # Pre-render the exact bytes this write would produce, so
                # the guard can detect a genuine no-op (existing content
                # already matches) and skip snapshotting it -- without
                # this, a repeated --force run over an unchanged corpus
                # accumulates an unbounded sequence of identical-content
                # snapshot files. A render failure here (e.g. a
                # malformed record whose own fields are wrong types) is
                # left as None; the guard then treats the destination as
                # unconditionally "would change," and
                # _write_memory_into_dir's own validation below still
                # rejects the record on its actual merits.
                try:
                    normalized_applies_to = (
                        tuple(applies_to) if applies_to else (agent,)
                    )
                    new_content: str | None = _render_memory_file(
                        name=name,
                        description=description,
                        type_=type_,
                        authored_by=agent,
                        applies_to=normalized_applies_to,
                        body=body,
                    )
                except (TypeError, AttributeError, yaml.YAMLError):
                    new_content = None
                dest_path = memory_dir / filename_for(name)
                with _locked_memory_path(dest_path):
                    _guard_import_overwrite(
                        memory_dir,
                        filename_for(name),
                        agent=agent,
                        new_content=new_content,
                        force=force,
                        dry_run=dry_run,
                    )
                    # Routes through the exact same validated path
                    # write_memory() uses -- rejecting anything write
                    # itself would reject -- not a second, less-validated
                    # write mechanism. ``dry_run`` here runs every
                    # validation/conflict check without touching the
                    # filesystem, so a dry-run preview reports the same
                    # accept/reject outcome a real import would, not
                    # merely "well-formed enough to reach this call."
                    # Held under the same lock as the guard above so the
                    # whole read-snapshot-write sequence is one atomic
                    # unit per destination.
                    _write_memory_into_dir(
                        memory_dir,
                        name,
                        description=description,
                        type_=type_,
                        agent=agent,
                        body=body,
                        applies_to=applies_to,
                        force=force,
                        dry_run=dry_run,
                    )
                results.append(ImportEntry(name=name, written=not dry_run, error=None))
                continue
            _write_memory_into_dir(
                memory_dir,
                name,
                description=description,
                type_=type_,
                agent=agent,
                body=body,
                applies_to=applies_to,
                force=force,
                dry_run=dry_run,
            )
            results.append(ImportEntry(name=name, written=not dry_run, error=None))
        except MemoryValidationError as exc:
            results.append(ImportEntry(name=name, written=False, error=str(exc)))
        except (TypeError, AttributeError) as exc:
            # Defensive: a bundle record can be a well-formed JSON object
            # with an incorrectly-typed field (e.g. `description: 7` or
            # `metadata.applies_to: "not-a-list"`) that only fails once it
            # reaches string/sequence operations deep inside validation or
            # rendering -- this must still produce a clean ImportEntry, not
            # an uncaught traceback.
            results.append(ImportEntry(name=name, written=False, error=str(exc)))
    return results


def import_memories(
    project_root: str | pathlib.Path,
    *,
    input: str | pathlib.Path,
    names: typing.Sequence[str] | None = None,
    force: bool = False,
    dry_run: bool = False,
    claude_projects_root: str | pathlib.Path | None = None,
) -> list[ImportEntry]:
    """Import a portable JSONL bundle, writing each record through
    :func:`write_memory`'s own validated path (never a duplicate
    write mechanism)."""

    memory_dir = memory_dir_for_project(project_root, claude_projects_root)
    records = _read_bundle(pathlib.Path(input))
    return _import_records_into_dir(
        memory_dir, records, names=names, force=force, dry_run=dry_run
    )


def _resolve_memory_dir(
    path_or_slug: str | pathlib.Path,
    claude_projects_root: str | pathlib.Path | None,
) -> tuple[pathlib.Path, str]:
    """Resolve a ``transfer`` ``--from``/``--to`` argument as either a
    literal project slug or a project root path (slug derived via
    :func:`project_slug_for_path`, same as every other memory command) --
    ``transfer`` is the only command that needs this dual form, since its
    whole point is moving memories *between* two corpora that are not both
    "the current project".

    A value with no path separators (and not ``.``/``..``) is *always*
    treated as a literal slug -- never gated on the destination's
    ``memory/`` directory already existing. An earlier revision required
    ``<claude_projects_root>/<value>/memory`` to already exist before
    accepting the literal-slug interpretation; that silently broke the
    normal ``--to <fresh-slug>`` case this command exists to support (a
    destination corpus that doesn't exist yet), falling through to
    :func:`project_slug_for_path` instead -- which resolves the bare slug
    string as a *relative filesystem path from the current working
    directory*, silently writing into a derived corpus for whatever
    directory that happened to name, while still reporting success.

    ``pathlib``'s ``/`` operator silently discards its left operand
    whenever the right operand is itself absolute, so ``root /
    literal_slug`` for an absolute ``path_or_slug`` (the normal shape of a
    project-root argument) would resolve to ``<path_or_slug>/memory`` --
    entirely outside ``claude_projects_root``. A genuine slug from
    :func:`project_slug_for_path` never contains a forward slash (it
    replaces ``/``, ``.``, and ``_`` with ``-``); the bare-slug check below
    separately excludes a literal backslash too, so restricting the
    literal-slug branch to values containing neither never misclassifies a
    real slug as a path, and unconditionally accepting it (once so
    restricted) never misclassifies a real path as a slug either.
    """

    root = (
        pathlib.Path(claude_projects_root).expanduser()
        if claude_projects_root
        else default_claude_projects_root()
    )
    literal_slug = str(path_or_slug)
    looks_like_bare_slug = (
        "/" not in literal_slug
        and "\\" not in literal_slug
        and literal_slug not in (".", "..")
    )
    if looks_like_bare_slug:
        return root / literal_slug / MEMORY_DIRNAME, literal_slug
    slug = project_slug_for_path(path_or_slug)
    return root / slug / MEMORY_DIRNAME, slug


def transfer_memories(
    *,
    from_: str | pathlib.Path,
    to: str | pathlib.Path,
    names: typing.Sequence[str] | None = None,
    agent: str | None = None,
    force: bool = False,
    dry_run: bool = False,
    claude_projects_root: str | pathlib.Path | None = None,
) -> list[ImportEntry]:
    """Move memories between two corpora through a temp bundle -- a thin
    export+import wrapper (PROP-LRH-MEMORY-COMMAND Decision 8), so the
    caller never manages an intermediate file themselves."""

    from_dir, from_slug = _resolve_memory_dir(from_, claude_projects_root)
    to_dir, _ = _resolve_memory_dir(to, claude_projects_root)
    if not from_dir.exists():
        # `--from` (unlike `--to`) has no legitimate "fresh, not-yet-existing
        # bucket" case -- there is nothing to move from a corpus that was
        # never written. A bare relative directory name with no path
        # separator (e.g. `--from spoke1`) is always resolved as a literal
        # project slug (see `_resolve_memory_dir`), so a caller who actually
        # meant a sibling directory gets silently routed to a slug bucket
        # that has never existed, and previously fell straight through to
        # exporting/importing zero records -- reported as an innocuous
        # `0 written, 0 errors` with no indication anything was wrong. Fail
        # loudly here instead, so that silent no-op is impossible.
        raise MemoryValidationError(
            f"--from {from_!r} resolved to slug {from_slug!r} "
            f"({from_dir}), which does not exist -- nothing to transfer. "
            "A bare name with no path separator is always treated as a "
            "literal project slug; if you meant a relative directory, "
            f"prefix it with './' (e.g. --from ./{from_}) to reference it "
            "as a path instead."
        )
    records = _export_records_from_dir(from_dir, from_slug, names=names, agent=agent)
    with tempfile.TemporaryDirectory() as tmp:
        bundle_path = pathlib.Path(tmp) / "transfer-bundle.jsonl"
        _write_bundle(bundle_path, records)
        bundle_records = _read_bundle(bundle_path)
        return _import_records_into_dir(
            to_dir, bundle_records, force=force, dry_run=dry_run
        )


# ---------------------------------------------------------------------------
# Read-side: read / search (PROP-LRH-MEMORY-COMMAND Decision 7)
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ReadResult:
    name: str
    path: pathlib.Path
    frontmatter: dict[str, typing.Any]
    body: str
    content: str


def read_memory(
    project_root: str | pathlib.Path,
    name: str,
    *,
    claude_projects_root: str | pathlib.Path | None = None,
) -> ReadResult:
    """Read one memory's full frontmatter and body, given only its name."""

    _validate_name(name)
    memory_dir = memory_dir_for_project(project_root, claude_projects_root)
    filename = filename_for(name)
    path = memory_dir / filename
    if not path.exists():
        raise MemoryValidationError(f"no memory named {name!r} found ({filename})")
    if path.is_symlink():
        # _validate_name blocks path traversal via the name itself, but a
        # symlink placed directly in the corpus (feedback-x.md -> /etc/passwd)
        # bypasses that entirely -- Path.read_text() follows symlinks by
        # default, so an unchecked read here could print content from
        # anywhere on disk, not just the resolved corpus.
        raise MemoryValidationError(
            f"{filename} is a symlink; refusing to read outside the memory corpus"
        )
    content = path.read_text(encoding="utf-8")
    frontmatter, body = read_frontmatter_and_body(content)
    return ReadResult(
        name=name, path=path, frontmatter=frontmatter, body=body, content=content
    )


@dataclasses.dataclass(frozen=True)
class MemorySearchMatch:
    name: str
    path: pathlib.Path
    authored_by: str | None
    contexts: list[str]


@dataclasses.dataclass(frozen=True)
class MemorySearchResult:
    query: str
    matches: list[MemorySearchMatch]
    case_sensitive: bool
    agent: str = ""
    type_: str = ""

    @property
    def match_count(self) -> int:
        return len(self.matches)

    @property
    def exit_code(self) -> int:
        return 0 if self.matches else 1


def _comparable(value: str, *, case_sensitive: bool) -> str:
    if case_sensitive:
        return value
    return value.casefold()


def _compact_context(value: str) -> str:
    compacted = " ".join(value.split())
    if len(compacted) <= 160:
        return compacted
    return compacted[:157].rstrip() + "..."


def _memory_stringify(value: typing.Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _memory_searchable_segments(
    frontmatter: dict[str, typing.Any], body: str
) -> list[tuple[str, str]]:
    segments: list[tuple[str, str]] = []
    for key in sorted(frontmatter):
        segments.append((f"frontmatter.{key}", _memory_stringify(frontmatter[key])))
    for line_number, line in enumerate(body.splitlines(), start=1):
        if line.strip():
            segments.append((f"body:{line_number}", line.strip()))
    return segments


def search_memories(
    project_root: str | pathlib.Path,
    query: str,
    *,
    agent: str = "",
    type_: str = "",
    case_sensitive: bool = False,
    claude_projects_root: str | pathlib.Path | None = None,
) -> MemorySearchResult:
    """Deterministic, case-folded substring search over a memory corpus's
    frontmatter and body text.

    Modeled directly on
    :func:`lrh.prompt_workflow_search.search_execution_records`'s design
    (Decision 7: exploratory substring matching only, no semantic or
    relevance-ranked search).
    """

    if query == "":
        raise MemoryValidationError("query must not be empty")

    memory_dir = memory_dir_for_project(project_root, claude_projects_root)
    comparable_query = _comparable(query, case_sensitive=case_sensitive)

    matches: list[MemorySearchMatch] = []
    if memory_dir.exists():
        for path in sorted(memory_dir.glob("*.md")):
            if path.name == INDEX_FILENAME:
                continue
            if path.is_symlink():
                # Path.read_text() follows symlinks by default -- a symlink
                # placed directly in the corpus could point outside it
                # entirely. Skip it rather than aborting the whole search,
                # matching how a malformed/unreadable entry is handled below.
                continue
            try:
                raw_content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                # A single unreadable or non-UTF-8 *.md file must not abort
                # the whole search -- skip it and keep returning matches
                # from the remaining memories, matching the existing
                # execution-record search's per-record resilience.
                continue
            try:
                frontmatter, body = read_frontmatter_and_body(raw_content)
            except MemoryValidationError:
                # A malformed/legacy memory has no valid frontmatter to
                # filter or attribute by -- but its content is still real,
                # searchable text, and is exactly the population this
                # command family exists to help inspect and repair.
                # Skip it only when an --agent/--type filter was requested
                # (unanswerable without valid metadata); otherwise search
                # its raw content as a single opaque blob rather than
                # silently excluding it from results.
                if agent or type_:
                    continue
                comparable_raw = _comparable(raw_content, case_sensitive=case_sensitive)
                if comparable_query in comparable_raw:
                    matches.append(
                        MemorySearchMatch(
                            name=path.stem,
                            path=path,
                            authored_by=None,
                            contexts=[f"content: {_compact_context(raw_content)}"],
                        )
                    )
                continue
            metadata = frontmatter.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}
            authored_by = metadata.get("authored_by")
            if agent and authored_by != agent:
                continue
            if type_ and metadata.get("type") != type_:
                continue

            contexts: list[str] = []
            for label, text in _memory_searchable_segments(frontmatter, body):
                comparable_text = _comparable(text, case_sensitive=case_sensitive)
                if comparable_query in comparable_text:
                    contexts.append(f"{label}: {_compact_context(text)}")
                if len(contexts) >= 3:
                    break
            if contexts:
                matches.append(
                    MemorySearchMatch(
                        name=frontmatter.get("name") or path.stem,
                        path=path,
                        authored_by=authored_by,
                        contexts=contexts,
                    )
                )

    return MemorySearchResult(
        query=query,
        matches=matches,
        case_sensitive=case_sensitive,
        agent=agent,
        type_=type_,
    )


# ---------------------------------------------------------------------------
# Orphan recovery: worktree-suffixed corpora -> canonical corpus
# ---------------------------------------------------------------------------

_WORKTREE_SLUG_MARKER = "--claude-worktrees-"


@dataclasses.dataclass(frozen=True)
class OrphanEntry:
    """One orphaned memory file and what recovery did (or would do) with it.

    ``action`` is one of ``copied`` / ``would_copy`` (new in the canonical
    corpus), ``identical`` (already present, same bytes), ``conflict``
    (present with different bytes -- never overwritten),
    ``unattributed`` (no ``metadata.authored_by``: provenance unknown, so
    reported only unless explicitly included), or ``malformed``.
    """

    source_dir: pathlib.Path
    filename: str
    action: str
    detail: str = ""


def find_orphan_memory_dirs(
    project_root: str | pathlib.Path,
    claude_projects_root: str | pathlib.Path | None = None,
) -> list[pathlib.Path]:
    """List worktree-suffixed ``memory/`` directories belonging to this
    project's canonical corpus.

    A directory matches when its name, with underscores normalised to
    hyphens (older ``lrh`` builds preserved them -- see
    WI-PROJECT-SLUG-SYMLINK-RESOLUTION), starts with
    ``<canonical-slug>--claude-worktrees-``. Only Claude Code's own
    ``.claude/worktrees/`` layout is recognised.
    """

    root = (
        pathlib.Path(claude_projects_root).expanduser()
        if claude_projects_root
        else default_claude_projects_root()
    )
    canonical_slug = project_slug_for_path(canonical_project_root(project_root))
    prefix = canonical_slug + _WORKTREE_SLUG_MARKER
    if not root.is_dir():
        return []
    found = []
    for child in sorted(root.iterdir()):
        if child.name.replace("_", "-").startswith(prefix):
            memory_dir = child / MEMORY_DIRNAME
            # Like ``read``/``search``, never follow a symlinked bucket or
            # corpus directory: it could point outside the projects root.
            if child.is_symlink() or memory_dir.is_symlink():
                continue
            if memory_dir.is_dir():
                found.append(memory_dir)
    return found


def recover_orphan_memories(
    project_root: str | pathlib.Path,
    *,
    claude_projects_root: str | pathlib.Path | None = None,
    apply: bool = False,
    include_unattributed: bool = False,
) -> list[OrphanEntry]:
    """Copy orphaned worktree-suffixed memories into the canonical corpus.

    Non-destructive by construction: ``cp -n`` semantics (an existing
    canonical file is never overwritten -- a differing one is reported as
    a ``conflict``), originals are left in place, and the canonical
    ``MEMORY.md`` gains an entry for each file copied -- and, on ``apply``,
    for a byte-identical canonical file that was never indexed (appended
    only, never rewriting an existing line; heals a run interrupted between
    the copy and the index write). Dry-run unless ``apply``.
    """

    canonical_dir = memory_dir_for_project(project_root, claude_projects_root)
    entries: list[OrphanEntry] = []
    for source_dir in find_orphan_memory_dirs(project_root, claude_projects_root):
        for source in sorted(source_dir.glob("*.md")):
            if source.name == INDEX_FILENAME:
                continue
            entries.append(
                _recover_one(
                    source_dir,
                    source,
                    canonical_dir,
                    apply=apply,
                    include_unattributed=include_unattributed,
                )
            )
    return entries


def _recover_one(
    source_dir: pathlib.Path,
    source: pathlib.Path,
    canonical_dir: pathlib.Path,
    *,
    apply: bool,
    include_unattributed: bool,
) -> OrphanEntry:
    if source.is_symlink():
        return OrphanEntry(
            source_dir, source.name, "malformed", "symlink; not followed"
        )
    try:
        content = source.read_bytes()
        frontmatter, _ = read_frontmatter_and_body(content.decode("utf-8"))
    except (OSError, MemoryValidationError, UnicodeDecodeError) as error:
        return OrphanEntry(source_dir, source.name, "malformed", str(error))
    problem = _structural_problem(frontmatter)
    if problem is not None:
        return OrphanEntry(source_dir, source.name, "malformed", problem)

    metadata = frontmatter.get("metadata")
    authored_by = metadata.get("authored_by") if isinstance(metadata, dict) else None
    if not authored_by and not include_unattributed:
        return OrphanEntry(
            source_dir,
            source.name,
            "unattributed",
            "no metadata.authored_by; pass --include-unattributed to copy",
        )

    dest = canonical_dir / source.name
    name = str(frontmatter.get("name") or source.stem.replace("_", "-"))
    description = str(frontmatter.get("description") or "")

    def _existing_state() -> OrphanEntry | None:
        if not dest.exists():
            return None
        try:
            if dest.read_bytes() == content:
                return OrphanEntry(source_dir, source.name, "identical")
        except OSError as error:
            return OrphanEntry(
                source_dir,
                source.name,
                "conflict",
                f"canonical path unreadable ({error}); left untouched",
            )
        return OrphanEntry(
            source_dir,
            source.name,
            "conflict",
            "canonical file differs; left untouched",
        )

    def _index() -> None:
        _ensure_index_entry(
            canonical_dir / INDEX_FILENAME,
            filename=source.name,
            name=name,
            description=description,
        )

    existing = _existing_state()
    if existing is not None:
        if apply and existing.action == "identical":
            # Heal a run interrupted between the copy and the index write:
            # the file is already there, but nothing links to it. Append
            # only -- never rewrite an existing (possibly hand-edited) line.
            if source.name not in _indexed_filenames(canonical_dir / INDEX_FILENAME):
                _index()
        return existing
    if not apply:
        return OrphanEntry(source_dir, source.name, "would_copy")

    # ``os.link`` fails atomically if ``dest`` already exists, so a concurrent
    # ``write`` landing after the checks above is never overwritten -- unlike
    # a lock, this needs no cooperation from the other writer (``write``
    # does not take ``_locked_memory_path``).
    canonical_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=canonical_dir, prefix=f".{source.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        try:
            os.link(tmp_name, dest)
        except FileExistsError:
            return _existing_state() or OrphanEntry(
                source_dir,
                source.name,
                "conflict",
                "canonical path already exists; left untouched",
            )
        except OSError as error:
            # ``os.link`` is the only atomic no-clobber primitive used here,
            # so an unsupported/failed link (FAT/exFAT, some network mounts,
            # a link limit) is reported per entry rather than falling back
            # to a non-atomic create that could leave a partial file.
            return OrphanEntry(
                source_dir,
                source.name,
                "conflict",
                f"could not link into canonical corpus ({error}); left untouched",
            )
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp_name)
    _index()
    return OrphanEntry(source_dir, source.name, "copied")
