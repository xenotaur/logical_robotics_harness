# `lrh memory`

## Command purpose

`lrh memory` reads and writes an agent's per-project memory corpus: a
`MEMORY.md` index plus one Markdown file per memory, stored under
`~/.claude/projects/<project-slug>/memory/` (or `--claude-projects-root`).
Every write goes through the same validated path (`write`, `import`,
and `transfer` all converge on one internal writer), so a memory file
is well-formed by construction rather than by convention. Eleven
subcommands cover four stages: write-side (`write`, `list`, `validate`,
`repair`, `recover-orphans`), archive-side (`sync`), read-side (`read`,
`search`), and portability (`export`, `import`, `transfer`).

## Organization

```bash
lrh memory write <name> --description ... --type ... --agent ...
lrh memory list
lrh memory validate
lrh memory repair <name> --set FIELD=VALUE
lrh memory recover-orphans
lrh memory sync
lrh memory read <name>
lrh memory search <query>
lrh memory export --output <bundle>
lrh memory import --input <bundle>
lrh memory transfer --from <path-or-slug> --to <path-or-slug>
```

All eleven subcommands accept `--project-root` (default `.`) except
`transfer`, which instead resolves both endpoints from `--from`/`--to`
(see below). All accept `--claude-projects-root` to override the
default `~/.claude/projects`.

## `lrh memory write`

Validate and write one memory file, plus its `MEMORY.md` index entry.

```bash
lrh memory write feedback-x --description "..." --type feedback --agent claude_app
lrh memory write feedback-x --description "..." --type feedback --agent claude_app --body-file body.md
echo "body text" | lrh memory write feedback-x --description "..." --type feedback --agent claude_app
```

- `name` (positional, required): kebab-case memory name.
- `--description` (required), `--type` (required, one of `user`,
  `feedback`, `project`, `reference`), `--agent` (required): recorded as
  `metadata.authored_by`.
- `--applies-to`: comma-separated agent list; defaults to `--agent`.
- `--body-file`: path to the memory body; omit to read the body from
  stdin.
- `--force`: overwrite even if the existing file's `authored_by`
  differs from `--agent`. Without `--force`, a cross-agent overwrite
  fails with `MemoryValidationError` (exit `1`); a same-agent
  overwrite (revising your own memory) always succeeds.

The memory file is written before its `MEMORY.md` index entry, so an
interruption between the two always fails toward an unindexed-but-
complete file — the state `validate` reports as `unindexed` and
`repair` fixes by re-running this same write path.

**Preserves unknown frontmatter keys on overwrite.** Overwriting an
existing memory (a same-agent revision, or `--force`) preserves any
frontmatter key outside this command's own schema — the same guarantee
`repair` has. `import`/`transfer` carry a bundled record's unknown
metadata through as well, on both a new-file write and an overwrite; on
overwrite, the incoming record's value wins for a key both sides share,
but a destination-only key is kept. A destination that's readable but has
an extra this module can't safely re-nest (a block sequence, for
example) fails the overwrite loudly rather than silently dropping it — a
truly unreadable or malformed destination degrades to "nothing to
preserve" instead, the same tolerance `--force` already has for that
case.

### Linked git worktrees share the main checkout's corpus

When `--project-root` (default `.`) is inside a linked git worktree, every
subcommand that takes it (all except `transfer`'s `--from`/`--to`)
resolves the corpus of the worktree's **main checkout** instead of a
worktree-suffixed one. Claude Code names a worktree session's transcript
bucket after the literal working directory (`...--claude-worktrees-<name>`)
but keys its auto-memory on the main repository, so a corpus keyed on the
worktree path is one no future session reads. `write` prints a
`note: ... is a linked git worktree; using the memory corpus of its main
checkout ...` line to stderr when this mapping applies. A non-git
directory, a bare repository, and a submodule are never remapped.
Detection compares `git rev-parse --git-dir` with `--git-common-dir`, so it
needs `git` on `PATH`; without it the path is used as given. `transfer`
keeps its literal path-or-slug semantics, so it can still address a
worktree-suffixed corpus explicitly. `sync` and `export` derive their
archive path and `exported_from_slug` provenance from the main checkout as
well, so a worktree session never creates a second, worktree-suffixed
archive or false export origin.

## `lrh memory recover-orphans`

Copy memories that were written to a worktree-suffixed corpus (before the
mapping above, or by an older `lrh` build) into the project's canonical
corpus.

```bash
lrh memory recover-orphans
lrh memory recover-orphans --apply
lrh memory recover-orphans --apply --include-unattributed --format json
```

- Scans `--claude-projects-root` for `<canonical-slug>--claude-worktrees-*`
  directories that contain a `memory/` directory. Underscores in the
  directory name are treated as hyphens, so buckets written by builds that
  predate the underscore fix (`WI-PROJECT-SLUG-SYMLINK-RESOLUTION`) are
  found too. Only Claude Code's own `.claude/worktrees/` layout is
  recognised.
- Dry-run unless `--apply`: prints one `<action>: <path>` line per file
  and writes nothing.
- Non-destructive: `cp -n` semantics. An existing canonical file is never
  overwritten (a differing one is reported as `conflict`, a byte-identical
  one as `identical`), originals are left in place, and `MEMORY.md` gains
  an entry for each file copied. With `--apply`, a byte-identical canonical
  file that has no index entry is appended to the index (an existing
  index line is never rewritten, but a file you deliberately left
  unindexed is indexed), so a run interrupted between the copy and the
  index write heals on rerun. The copy is an atomic no-clobber (`os.link`),
  so a concurrent `write` is never overwritten and no partial file can be
  left behind; a filesystem without hard-link support, or any other
  per-file I/O failure, is reported as `conflict`/`malformed` and the run
  continues.
- Files with no `metadata.authored_by` (unknown provenance) are reported
  as `unattributed` and skipped unless `--include-unattributed`.
  Files that fail the same structural checks `validate` applies (missing
  `name`, `description`, or a valid `metadata.type`) and unparseable
  files are reported as `malformed` and skipped. Symlinked bucket or
  `memory/` directories are ignored, and a symlinked memory file is
  reported as `malformed` (`symlink; not followed`), matching `read` and
  `search`.
- `--format json` emits `source_dir`, `filename`, `action`, and `detail`
  per file. Actions: `would_copy`, `copied`, `identical`, `conflict`,
  `unattributed`, `malformed`.

## `lrh memory list`

List the `MEMORY.md` index.

```bash
lrh memory list
lrh memory list --agent claude_app
lrh memory list --format json
```

- `--agent`: filter to entries authored by this agent.
- `--format {text,json}`: defaults to `text`. With no index found,
  prints `no memory index found for this project` and exits `0`.

## `lrh memory validate`

Audit a memory corpus, classifying every file into one of four buckets,
plus one independent cross-cutting check.

```bash
lrh memory validate
lrh memory validate --format json
```

- `--format {text,json}`: defaults to `text`.

Buckets: **conforming** (complete, indexed), **legacy** (missing
`authored_by`, a `repair` candidate), **unindexed** (no `MEMORY.md`
entry — unreachable by `list` but still found by `search`, which scans
memory files directly rather than the index; a `repair` candidate), and
**malformed** (missing `name`/`description`/`metadata.type`). Always
exits `0`; the counts and per-bucket file lists are the output to act on.

**`name_mismatch`** is independent of the four buckets above — a file can
be `conforming` by every other measure and still appear here. It lists a
file whose `name:` field doesn't map back to its own on-disk filename
(e.g. a `name:` missing the type prefix the filename carries). Left
unfixed, `repair` on such a file used to silently write a second,
differently-named file instead of correcting the original; `repair` now
always writes back to the file it opened, correcting the `name:` field
to match in the process.

## `lrh memory repair`

Conservative, structural-only fix-up of one memory's frontmatter.

```bash
lrh memory repair feedback-x --set metadata.authored_by=claude_app
lrh memory repair feedback-x --set metadata.authored_by=claude_app --dry-run
```

- `name` (positional, required).
- `--set FIELD=VALUE`: repeatable; sets one frontmatter field per flag.
- `--dry-run`: report what would be repaired without writing.

**Preserves unknown frontmatter keys.** Any key outside this schema
(`name`/`description`/`metadata.{type,authored_by,applies_to}`) — for
example Claude Code auto-memory's own `node_type`, `originSessionId`,
and `modified` on a memory it wrote before this command's schema
existed — is carried through byte-for-byte, not merely semantically: an
unquoted ISO timestamp survives exactly as written, rather than being
reformatted by a YAML parse-then-dump round trip. A preserved key can
never shadow or override a canonical field. A memory with only
canonical keys repairs to the same output as before this guarantee
existed. A preserved key's value must fit on its own line (a scalar, a
null, or a single-line flow collection); a value that spans further
lines (a block sequence or block scalar), a `metadata:` line written
with inline flow-mapping content, or a key duplicated in the source
fails with a clear error instead of guessing.

**Always writes back to the file it read.** The destination path is
derived from the `name` argument used to locate the file, never from
the frontmatter's own `name:` field — a memory whose `name:` omits a
type prefix its filename carries (`lrh memory validate`'s
`name_mismatch` bucket) is still repaired in place, and its `name:`
field is corrected to match. This is not the renaming `--set
name=<...>` refuses above: nothing lets the caller choose an unrelated
new name.

## `lrh memory sync`

Mirror this project's memory corpus into the durable archive root,
snapshotting any changed file's prior content first.

```bash
lrh memory sync
lrh memory sync --archive-root /path/to/archive
lrh memory sync --dry-run
```

- `--archive-root`: local archive root. Defaults to
  `$LRH_SESSION_ARCHIVE_ROOT`, else `~/.local/share/lrh/session-archive`.
- `--dry-run`: report what would be mirrored without writing anything.

Only changed files are mirrored — a real sync compares content by
SHA-256 hash, `--dry-run` by a direct byte comparison; both agree on
whether a file changed, and an unchanged file is silently skipped
either way. When a destination file *would* be
overwritten, its prior content is snapshotted first — this
snapshot-before-overwrite invariant is `sync`'s own safety guarantee
and is not shared by `import`/`transfer` below.

## `lrh memory read`

Print one memory's full frontmatter and body.

```bash
lrh memory read feedback-x
lrh memory read feedback-x --format json
```

- `name` (positional, required).
- `--format {text,json}`: defaults to `text` (raw file content, prefixed
  with its path). `json` emits `name`, `path`, `frontmatter`, `body`.

## `lrh memory search`

Deterministic, case-folded substring search over a memory corpus's
frontmatter and body — no semantic ranking, modeled on `lrh search`'s
own precedent.

```bash
lrh memory search "heredoc"
lrh memory search "heredoc" --agent claude_app --type feedback
lrh memory search "heredoc" --case-sensitive --format json
```

- `query` (positional, required).
- `--agent`, `--type {user,feedback,project,reference}`: optional filters.
- `--case-sensitive`: exact-case matching; default is case-folded.
- `--format {text,json}`: defaults to `text`.

Exits `0` if any memory matched, `1` if none did — the same convention
as `grep`, not an error condition.

## `lrh memory export`

Export selected memories to a portable JSON-Lines bundle.

```bash
lrh memory export --output bundle.jsonl --agent claude_app
lrh memory export --output bundle.jsonl --name feedback-x --name feedback-y
```

- `--output` (required): bundle output path.
- `--name`: repeatable; restrict to these memory names.
- `--agent`: restrict to memories authored by this agent.

**At least one of `--name` or `--agent` is required** — `export`
refuses to run unfiltered, so a bare `export --output bundle.jsonl`
fails with `MemoryValidationError` (exit `1`) rather than silently
exporting an entire corpus.

## `lrh memory import`

Import a portable JSONL bundle, writing each record through `write`'s
own validated path — never a second, less-validated write mechanism.

```bash
lrh memory import --input bundle.jsonl
lrh memory import --input bundle.jsonl --name feedback-x
lrh memory import --input bundle.jsonl --force
lrh memory import --input bundle.jsonl --dry-run
```

- `--input` (required): bundle input path.
- `--name`: repeatable; restrict import to these memory names.
- `--force`: required to overwrite an existing destination memory whose
  content actually differs — same-agent, legacy (no `authored_by`), or
  a differing `authored_by`. An incoming record that's already
  byte-identical to the destination is written through regardless
  (an idempotent re-import). See "Overwrite safety" below.
- `--dry-run`: report what would be written, without touching the
  filesystem.

Prints one `wrote:`/`would write:`/`error:` line per record, then a
summary line (`import complete: N written, M errors`, or the `dry-run:`
equivalent). Exits `1` if any record errored, else `0`.

**Overwrite safety.** `--force` is required to overwrite an existing
destination memory whose content actually differs — same-agent, legacy
(no `authored_by`), or a differing `authored_by` (a genuine cross-agent
conflict). An incoming record that's already byte-identical to the
destination is written through with no `--force` and no snapshot (an
idempotent re-import is not an overwrite). For every other case except
the differing-`authored_by` one, the destination's prior content is
snapshotted first, into
`<memory_dir>/history/<filename-stem>.<short-hash>.md` (deduplicated by
content hash, no timestamp — the same version is never snapshotted
twice). Note that `<filename-stem>` is the on-disk form, not the
kebab-case memory name — hyphens become underscores (`feedback-x` →
`feedback_x.md`), same as every other memory file. See
[`WI-LRH-MEMORY-TRANSFER-SAFETY`](../../../project/work_items/resolved/WI-LRH-MEMORY-TRANSFER-SAFETY.md)
for the history of this guard.

**A bundle is untrusted input.** A record's `preserved_top_level_lines`/
`preserved_metadata_lines` (unknown frontmatter keys carried from the
source) are rejected — the whole record errors, nothing is written — if
any line names a canonical key (`name`/`description`/`metadata.
{type,authored_by,applies_to}`, which YAML would otherwise resolve as a
silently-overriding duplicate) or contains an embedded newline. A bundle
written before this preservation existed, which instead carried extras
inside the full `metadata` dict, is still read correctly: its extras are
recovered from `metadata` when the newer fields are absent from the
record entirely.

## `lrh memory transfer`

Move memories between two corpora through a temporary bundle — a thin
`export` + `import` wrapper, so the caller never manages an
intermediate file.

```bash
lrh memory transfer --from /path/to/source-project --to /path/to/dest-project --agent claude_app
lrh memory transfer --from source-project-slug --to dest-project-slug --name feedback-x
lrh memory transfer --from /path/to/source --to /path/to/dest --agent claude_app --dry-run
```

- `--from`, `--to` (both required): each accepts either a project root
  **path** or a literal project **slug**. A value containing a path
  separator (`/` or `\`), or exactly `.`/`..`, is always resolved as a
  path (via the same `project_slug_for_path` derivation every other
  memory command uses); any other value is always treated as a literal
  slug — this holds regardless of whether that slug's directory already
  exists, so a fresh destination corpus (`--to a-new-slug`) works
  correctly rather than silently falling through to a misresolved path.
  Unlike `--to`, `--from` has no legitimate "doesn't exist yet" case: if
  it resolves to a corpus directory that doesn't exist, `transfer` fails
  loudly with `MemoryValidationError` (exit `1`) rather than silently
  reporting `0 written, 0 errors` — the error names the resolved slug
  and suggests a `./` prefix if a relative path was intended.
- `--name`, `--agent`: same filters as `export` — and the same
  requirement: at least one of `--name` or `--agent` is required
  (`transfer` reads its source through `export`'s own filtered path),
  so an unfiltered `transfer` fails with `MemoryValidationError`
  (exit `1`) rather than silently moving an entire corpus.
- `--force`, `--dry-run`: same semantics as `import`.

Reports the same `wrote:`/`would write:`/`error:` lines and summary as
`import`, and shares `import`'s overwrite-safety guarantee above —
`transfer`'s whole purpose is moving memories between corpora that are
not both "the current project," so a cross-project refresh workflow
relies on that guard specifically; see
[`WI-LRH-MEMORY-TRANSFER-SAFETY`](../../../project/work_items/resolved/WI-LRH-MEMORY-TRANSFER-SAFETY.md)
for the history of this guard and the earlier bare-relative-slug
resolution bug fixed alongside it.

## Related how-to guidance

- [Back up and restore project memory](../../how-to/back-up-and-restore-project-memory.md) —
  the `sync` workflow.
- [Move memories between projects](../../how-to/move-memories-between-projects.md) —
  the `export`/`import`/`transfer` workflow.
