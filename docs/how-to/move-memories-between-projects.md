# Move memories between projects

## Purpose

Use `lrh memory export`/`import` to move memories through a portable
JSONL bundle, or `lrh memory transfer` (a thin `export` + `import`
wrapper) to move them directly between two projects' corpora in one
command. See [`lrh memory`](../reference/cli/memory.md) for the full
command reference.

## Prerequisites

- A source project with at least one memory written.
- Know whether the destination is an existing project (a normal
  `--project-root` path) or a fresh corpus that has never been written
  to yet (`transfer` handles this case correctly; `export`+`import`
  handles it too, since `import` creates the destination's `memory/`
  directory if absent).

## Step 1 — Export requires an explicit filter

There is no unfiltered "export everything" default — `export`/`transfer`
both refuse to run without at least one of `--name` or `--agent`:

```bash
lrh memory export --output bundle.jsonl --project-root /path/to/source-project
```

```
error: export/transfer require an explicit --name or --agent filter -- there is no unfiltered export-everything default
```

Add a filter:

```bash
lrh memory export --output bundle.jsonl --project-root /path/to/source-project --agent claude_app
```

```
exported: 1 memory(ies) -> bundle.jsonl
```

## Step 2 — Import the bundle into a destination

```bash
lrh memory import --input bundle.jsonl --project-root /path/to/dest-project
```

```
wrote: cache-notes
import complete: 1 written, 0 errors
```

## Step 3 — Or skip the bundle with `transfer`

`transfer`'s `--from`/`--to` each accept either a project root **path**
or a literal project **slug** — but a bare name with no path separator
is *always* treated as a literal slug, never as a relative path, even if
that slug's corpus doesn't exist yet:

```bash
lrh memory transfer --from spoke1 --to hub --agent claude_app
```

```
error: --from 'spoke1' resolved to slug 'spoke1' (/home/user/.claude/projects/spoke1/memory), which does not exist -- nothing to transfer. A bare name with no path separator is always treated as a literal project slug; if you meant a relative directory, prefix it with './' (e.g. --from ./spoke1) to reference it as a path instead.
```

If you meant a sibling directory, prefix it with `./` (or use an absolute
path) so it resolves as a path instead of a slug:

```bash
lrh memory transfer --from ./spoke1 --to ./hub --agent claude_app --dry-run
lrh memory transfer --from ./spoke1 --to ./hub --agent claude_app
```

```
would write: cache-notes
dry-run: 1 memory(ies) considered, 0 would error
wrote: cache-notes
import complete: 1 written, 0 errors
```

`--to` has no equivalent restriction — a fresh, not-yet-existing slug or
path is the normal case for a destination and works correctly either way.

## Step 4 — A same-agent or legacy overwrite requires `--force`

Re-running `import`/`transfer` against a destination memory that already
exists — written by the same agent, or a legacy record with no
`authored_by` at all — refuses to proceed without `--force`:

```bash
lrh memory transfer --from ./spoke1 --to ./hub --agent claude_app
```

```
error: cache-notes: cache_notes.md already exists (authored_by 'claude_app'); transfer/import refuses to overwrite it without --force
import complete: 0 written, 1 errors
```

With `--force`, the overwrite proceeds — and the destination's *prior*
content is snapshotted first, into
`<dest-corpus>/history/<filename-stem>.<content-hash>.md`
(no timestamp — keyed by content hash only, so the same prior version is
never snapshotted twice):

```bash
lrh memory transfer --from ./spoke1 --to ./hub --agent claude_app --force
```

```
wrote: cache-notes
import complete: 1 written, 0 errors
```

A destination memory with a genuinely *different* `authored_by` (a real
cross-agent conflict) also requires `--force` — but that case is **not**
snapshotted, since it predates this same-agent/legacy safety guard and is
handled by `write`'s own pre-existing cross-agent check.

For the same-agent/legacy/malformed case specifically, if the incoming
content is already byte-identical to the destination, the write is a
no-op regardless of `--force` — nothing changes, and no snapshot is
taken. A genuine cross-agent overwrite has no such no-op check — with
`--force`, it always rewrites the destination unconditionally.

## Related reference and how-to guidance

- [`lrh memory`](../reference/cli/memory.md) — full command reference for
  all 10 subcommands.
- [Back up and restore project memory](back-up-and-restore-project-memory.md) —
  the `sync` workflow for archiving a project's own corpus, rather than
  moving memories to a *different* project.
