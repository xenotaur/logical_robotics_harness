# `lrh sessions`

`lrh sessions` reconciles execution-record session pointers with the private
local session archive. It is metadata-oriented: commands inspect execution
frontmatter, `project/sessions/index.jsonl`, archive filenames, export
metadata, and attempt markers rather than printing raw transcript bodies.

## `lrh sessions sync`

```bash
lrh sessions sync \
  [--claude-projects-root ROOT] \
  [--exports-dir DIR] \
  [--archive-root ROOT] \
  [--project-root .] \
  [--dry-run]
```

Mirrors Claude Code JSONL transcripts into the private archive and optionally
harvests `session-export-*.zip` `metadata.json` identity fields into
`project/sessions/index.jsonl`.

**Scan scope is machine-wide, not project-scoped.** Without
`--claude-projects-root`, `sync` walks every project bucket under
`~/.claude/projects/` and mirrors transcripts from all of them into
`<archive-root>/raw/<project-slug>/`, whichever repository `--project-root`
names. This is intentional: the archive is a cross-project, private,
machine-local store. `--project-root` only selects which
`project/sessions/index.jsonl` receives child-id aliases and harvested
identity rows. Aliases are only added for host ids already present in that
index, so transcripts from unrelated projects are copied into the archive but
never indexed into this repository.

The `session-export-*.zip` bundles that `--exports-dir` reads are produced by
the Claude desktop app, not the Claude Code CLI. Their `metadata.json` is the
app's own per-session record: host `sessionId`, `cliSessionId`, `prs[]`,
`branch`, `title`, and `writtenBranches`. These zips were historically made by
typing `/export` in a desktop Code-tab session. As of desktop app 2.7032.0,
that in-session `/export` reports "not available for this session", and no
visible menu item replaces it. The app still contains the zip builder, which
writes to `~/Downloads`, but today it can only be reached through an agent's
session-management `export_transcript` tool. In practice, then, this harvest
path is retroactive-only and rarely fed. Forward identity capture through
`lrh prompt record-session-alias` at `/lrh-implement` and `/lrh-closeout` is
the primary path. `/lrh-export-claude` Markdown exports are a separate
artifact, and this harvest does not read them.

Archive root resolution is:

1. `--archive-root`;
2. `LRH_SESSION_ARCHIVE_ROOT`;
3. `~/.local/share/lrh/session-archive`.

`--dry-run` reports planned mirror/harvest actions without writing files.

## `lrh sessions closeout-sync`

```bash
lrh sessions closeout-sync \
  [--claude-projects-root ROOT] \
  [--exports-dir DIR] \
  [--archive-root ROOT] \
  [--project-root .] \
  [--dry-run]
```

Runs the same archive reconciler as `sync`, but wraps the output with a
closeout-oriented heading and completion line. `/lrh-closeout` uses this command
path so the archive refresh is visible in the closeout transcript and failure
handling remains separate from execution-record edits.

`--dry-run` is safe for checking what closeout would attempt without writing to
the private archive or `project/sessions/index.jsonl`.

## `lrh sessions schedule`

```bash
lrh sessions schedule \
  [--project-root .] \
  [--claude-projects-root ROOT] \
  [--exports-dir DIR] \
  [--archive-root ROOT] \
  [--lrh-command lrh] \
  [--label LABEL] \
  [--weekday 0-7] \
  [--hour 0-23] \
  [--minute 0-59] \
  [--output PATH]
```

Renders or writes an inspectable weekly launchd plist that runs
`lrh sessions sync` for the chosen project. It does not install, load, unload,
or hide a background job; the human remains in control of setup and removal.

Use an absolute `--lrh-command` when launchd will not inherit a shell `PATH`, for
example:

```bash
LRH_SESSIONS_LABEL="org.lrh.sessions.$(basename "$PWD")"
lrh sessions schedule \
  --project-root "$PWD" \
  --lrh-command "$(command -v lrh)" \
  --label "$LRH_SESSIONS_LABEL" \
  --output "$HOME/Library/LaunchAgents/$LRH_SESSIONS_LABEL.plist"
```

Inspect before loading:

```bash
plutil -lint "$HOME/Library/LaunchAgents/$LRH_SESSIONS_LABEL.plist"
plutil -p "$HOME/Library/LaunchAgents/$LRH_SESSIONS_LABEL.plist"
```

Load, inspect, and disable with launchd:

```bash
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/$LRH_SESSIONS_LABEL.plist"
launchctl print "gui/$(id -u)/$LRH_SESSIONS_LABEL"
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/$LRH_SESSIONS_LABEL.plist"
```

After scheduled or closeout-triggered sync, use `lrh sessions report` to inspect
remaining metadata-only coverage gaps.

## `lrh sessions discover`

```bash
lrh sessions discover \
  [--claude-projects-root ROOT] \
  [--project-path PATH] \
  [--project-root .] \
  [--format text|json]
```

Lists local Claude transcripts for a project path, cross-referenced against the
committed session index when a host id is known.

## `lrh sessions link`

```bash
lrh sessions link --execution-id ID --child-id CHILD_ID [--project-root .]
```

Promotes a child id to a host-keyed `claude-app:<host-id>` pointer on one
execution record once the index has made that mapping authoritative. The command
fails cleanly if the child id is unknown or ambiguous.

## `lrh sessions report`

```bash
lrh sessions report \
  [--archive-root ROOT] \
  [--project-root .] \
  [--since-created-at ISO_TIMESTAMP] \
  [--format text|json]
```

Reports execution-record session pointers that need attention:

- `pending` — the record still has `session_transcript: pending`.
- `dangling` — the pointer is a placeholder or cannot be resolved through the
  committed index.
- `unarchived` — the pointer is resolvable, but no matching durable private
  archive artifact was found.
- `unsupported` — the pointer uses a scheme this report does not yet know how
  to check.
- `missing` — the execution record has no `session_transcript` field.

Successful `claude-app:` coverage is determined from the committed
`project/sessions/index.jsonl` host-to-child mapping plus archived top-level
JSONL filenames under `<archive-root>/raw/`. Successful `codex-app:` coverage is
determined from non-ephemeral Codex `attempt.json` markers under
`<archive-root>/codex/` with `status: succeeded` or `status: imported` and a
matching `thread_id`.

The report does not read raw transcript bodies, Codex `raw.json` captures, or
Markdown transcript bodies. Text output is intended for human closeout/dogfood
review; JSON output is deterministic for scripts.

Use `--since-created-at` to scope the report to a rollout era, for example to
check only execution records produced after both-identifier capture landed.
