# Back up and restore project memory

## Purpose

Use `lrh memory sync` to mirror a project's memory corpus into a durable
archive root outside the project — so an agent's accumulated memory
survives even if the project's own `~/.claude/projects/<slug>/memory/`
directory is lost, and so an edited or shrunk memory file's prior content
is recoverable. See [`lrh memory`](../reference/cli/memory.md) for the
full command reference.

## Prerequisites

- At least one memory file already written (`lrh memory write`).
- An archive root outside the project's own memory corpus — nesting either
  inside the other causes `sync` to re-mirror its own prior output on every
  run. The default (`$LRH_SESSION_ARCHIVE_ROOT`, else
  `~/.local/share/lrh/session-archive`) satisfies this automatically for a
  normal project layout; only override `--archive-root` if you know your
  layout differs.

## Step 1 — Preview with `--dry-run`

See what a sync would do before writing anything:

```bash
lrh memory sync --dry-run
```

```
would mirror: /home/user/.claude/projects/-home-user-myproject/memory/MEMORY.md -> /home/user/.local/share/lrh/session-archive/raw/-home-user-myproject/memory/MEMORY.md
would mirror: /home/user/.claude/projects/-home-user-myproject/memory/cache_notes.md -> /home/user/.local/share/lrh/session-archive/raw/-home-user-myproject/memory/cache_notes.md
dry-run: 2 memory file(s) considered
```

Every `*.md` file under the corpus is considered, including `MEMORY.md`
itself.

## Step 2 — Run the sync

```bash
lrh memory sync
```

```
mirrored: .../memory/MEMORY.md -> .../raw/-home-user-myproject/memory/MEMORY.md
mirrored: .../memory/cache_notes.md -> .../raw/-home-user-myproject/memory/cache_notes.md
sync complete: 2 mirrored, 0 unchanged
```

Only changed files are mirrored — a real sync compares content by SHA-256
hash, so running it again immediately reports `0 mirrored, N unchanged`
with no writes:

```bash
lrh memory sync
```

```
sync complete: 0 mirrored, 2 unchanged
```

## Step 3 — Edit a memory, then sync again to see the snapshot

When a file that was already mirrored changes — including a legitimate
shrink, such as a `consolidate-memory` pass merging duplicates — `sync`
snapshots the *prior* archived content before overwriting it, so no
version is ever unrecoverable:

```bash
lrh memory write cache-notes --description "..." --type feedback --agent claude_app --force <<< "revised notes"
lrh memory sync
```

```
mirrored: .../memory/cache_notes.md -> .../raw/-home-user-myproject/memory/cache_notes.md
  snapshot: /home/user/.local/share/lrh/session-archive/history/-home-user-myproject/memory/cache_notes.20260828T065204Z.d278eec348c9.md
sync complete: 1 mirrored, 1 unchanged
```

The snapshot filename is `<stem>.<timestamp>.<short-hash>.<suffix>` under
`<archive-root>/history/<project-slug>/memory/` (a 12-character prefix of
the prior content's SHA-256, not the full digest). The filename includes
the timestamp, not just the hash — a value that recurs later (an
`A → B → A` cycle) is snapshotted again under a fresh timestamp, since the
per-sync check only skips writing when *this run's* prior content is
byte-identical to what's already at the destination, not against every
past snapshot's content.

## Step 4 — Restore from the archive

There is no `lrh memory restore` command — recovery is a plain file copy
from the archive root back into the project's own memory directory
(`~/.claude/projects/<project-slug>/memory/`, or wherever
`--claude-projects-root` points). If the corpus directory was lost
entirely — the scenario this guide exists for — restore the whole
directory recursively rather than one file at a time, since `cp` does
not create missing parent directories on its own:

```bash
cp -r /home/user/.local/share/lrh/session-archive/raw/-home-user-myproject/memory \
      /home/user/.claude/projects/-home-user-myproject/memory
```

For a single file into an existing corpus, `mkdir -p` the destination
directory first if it doesn't already exist, then copy the one file:

```bash
mkdir -p /home/user/.claude/projects/-home-user-myproject/memory
cp /home/user/.local/share/lrh/session-archive/raw/-home-user-myproject/memory/cache_notes.md \
   /home/user/.claude/projects/-home-user-myproject/memory/cache_notes.md
```

To recover an *older* version instead of the latest archived one, copy
from the matching timestamped file under `history/` rather than `raw/`.
After restoring, run `lrh memory validate` to confirm the corpus and its
`MEMORY.md` index are consistent.

## Related reference and how-to guidance

- [`lrh memory`](../reference/cli/memory.md) — full command reference for
  all 10 subcommands.
- [Move memories between projects](move-memories-between-projects.md) —
  the `export`/`import`/`transfer` workflow for copying memories to a
  *different* project's corpus, rather than backing up the same one.
