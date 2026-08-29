# `lrh memory`

## Command purpose

`lrh memory` reads and writes an agent's per-project memory corpus: a
`MEMORY.md` index plus one Markdown file per memory, stored under
`~/.claude/projects/<project-slug>/memory/` (or `--claude-projects-root`).
Every write goes through the same validated path (`write`, `import`,
and `transfer` all converge on one internal writer), so a memory file
is well-formed by construction rather than by convention. Ten
subcommands cover four stages: write-side (`write`, `list`, `validate`,
`repair`), archive-side (`sync`), read-side (`read`, `search`), and
portability (`export`, `import`, `transfer`).

## Organization

```bash
lrh memory write <name> --description ... --type ... --agent ...
lrh memory list
lrh memory validate
lrh memory repair <name> --set FIELD=VALUE
lrh memory sync
lrh memory read <name>
lrh memory search <query>
lrh memory export --output <bundle>
lrh memory import --input <bundle>
lrh memory transfer --from <path-or-slug> --to <path-or-slug>
```

All ten subcommands accept `--project-root` (default `.`) except
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

Audit a memory corpus, classifying every file into one of four buckets.

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

## `lrh memory repair`

Conservative, structural-only fix-up of one memory's frontmatter.

```bash
lrh memory repair feedback-x --set metadata.authored_by=claude_app
lrh memory repair feedback-x --set metadata.authored_by=claude_app --dry-run
```

- `name` (positional, required).
- `--set FIELD=VALUE`: repeatable; sets one frontmatter field per flag.
- `--dry-run`: report what would be repaired without writing.

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
- `--force`: required to overwrite any existing destination memory —
  same-agent, legacy (no `authored_by`), or a differing `authored_by`.
  See "Overwrite safety" below.
- `--dry-run`: report what would be written, without touching the
  filesystem.

Prints one `wrote:`/`would write:`/`error:` line per record, then a
summary line (`import complete: N written, M errors`, or the `dry-run:`
equivalent). Exits `1` if any record errored, else `0`.

**Overwrite safety.** `--force` is required to overwrite *any* existing
destination memory — same-agent, legacy (no `authored_by`), or a
differing `authored_by` (a genuine cross-agent conflict). For every case
except the differing-`authored_by` one, the destination's prior content
is snapshotted first, into `<memory_dir>/history/<name>.<short-hash>.md`
(deduplicated by content hash, no timestamp — the same version is never
snapshotted twice). See
[`WI-LRH-MEMORY-TRANSFER-SAFETY`](../../../project/work_items/resolved/WI-LRH-MEMORY-TRANSFER-SAFETY.md)
for the history of this guard.

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
