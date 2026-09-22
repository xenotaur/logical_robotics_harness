---
name: lrh-export-claude
description: >
  Export the current or specified Claude Code session transcript into a
  private, non-authoritative Markdown export artifact. Use when the user
  asks to export, capture, or archive a Claude Code conversation session.
  Wraps `lrh conversation export-claude-session`, verifies the artifact
  with `lrh conversation inspect-export`, and reports metadata-only
  terminal status.
when_to_use: >
  Invoke only when the user explicitly asks to export, capture, or archive
  a Claude Code session transcript for later private review. Do not
  invoke proactively or infer the intent from a passing mention of
  exporting — by default this skill writes a durable, permanent copy into
  the user's local session archive (not a self-cleaning temp file), so
  invocation should always trace to a direct request, not an agent's own
  judgment call. With no discovery flag, defaults to exporting the current
  session. A user-typed `/lrh-export-claude` invocation is itself the
  explicit request — it states the resolved session and destination and
  proceeds without a separate confirmation; a model-initiated invocation
  (offered proactively, or chained from another skill or workflow) still
  requires an explicit confirmation before writing. `--force` is the one
  exception: it always waits for confirmation, even for a typed invocation,
  since it can overwrite an existing export. Also supports explicit
  `--transcript-path`, `--session-id`, or `--latest` discovery, defaulting
  to a durable private session archive when `--out` is omitted.
argument-hint: "[--out OUTPUT.md] [--transcript-path PATH | --session-id ID | --current | --latest]"
---

# lrh-export-claude Skill

This skill is a thin workflow wrapper around the LRH CLI. It does not
duplicate the Python exporter, inspect undocumented Claude Code storage
internals, or promote private transcript text into LRH project state.

The goal is to safely capture a Claude Code session transcript for later
private review, parallel to Claude's own `/export` habit, while preserving
LRH's privacy and authority boundaries.

---

## Inputs

All discovery flags are optional. With none supplied, this skill exports
the **current session** — the one this invocation is running in:

```bash
# Export the current session (the default; no flag needed)
/lrh-export-claude

# Export using durable private archive default, most recent in this project
/lrh-export-claude --latest

# Export using explicit transcript path and custom output override
/lrh-export-claude --transcript-path ~/.claude/projects/<project>/<session-id>.jsonl --out export.md

# Export using session ID discovery
/lrh-export-claude --session-id <session-id>
```

`--current`, `--transcript-path`, `--session-id`, and `--latest` are
mutually exclusive; supply at most one. Unlike Codex's single-thread-id
resolver, older versions of this skill had no ambient default and always
asked which flag to use — Claude Code sessions do have an ambient
identity (`CLAUDE_CODE_SESSION_ID`), resolved the same way `--current`
resolves it, so a bare invocation no longer needs to ask.

### Additional Options

- `--out PATH` — optional path for the destination Markdown export file.
  When omitted, defaults to a durable private session archive path
  (`<archive_root>/claude/exports/<YYYY>/<MM>/<session-id>.md`). This is
  never asked about — see Step 3.
- `--app-data-dir PATH` — path to Claude Code's application data directory
  (default: `$CLAUDE_CONFIG_DIR`, or `~/.claude` if unset). Used by Step 1's
  own metadata-only resolution for every route. Also forwarded to Step 4's
  exporter call, but only for the current-session default (or explicit
  `--current`) route, which resolves against it directly — see Step 4. Not
  needed for `--transcript-path`, `--session-id`, or `--latest`, since all
  three are already resolved to an exact file by
  Step 1.
- `--archive-root PATH` — optional private session archive root override.
- `--force` — overwrite the destination file if it already exists. This
  never allows the source transcript and output to be the same file, even
  with `--force`. Always asks for confirmation before Step 4 when present
  — the one flag Step 3 treats as dangerous, regardless of whether the
  invocation is otherwise typed or model-initiated.
- `--source-id ID` — optional explicit session identifier to record in
  metadata (defaults to the transcript filename stem).
- `--no-scan-sensitive` — skip the local heuristic sensitivity scanner and
  mark frontmatter as `sensitivity: unscanned`.
- `--include-system-attachments` — include internal system-context
  attachment records in the export; skipped by default since they are not
  part of the visible conversation.
- `--include-subagents` — inline full subagent transcripts instead of only
  referencing them by id and description.

---

## Reference Knowledge

Use the repository CLI documentation as the command contract:

- `docs/reference/cli/conversation.md` for
  `lrh conversation current-claude-session-id`,
  `lrh conversation export-claude-session`, and
  `lrh conversation inspect-export`.

The relevant CLI guarantees are:

- `current-claude-session-id` is metadata-only: it reports the current
  session id, its `claude-app:<uuid>` host pointer, and the resolved
  transcript path without exporting, reading, or printing transcript
  content, and fails clearly (never guessing) when the session can't be
  resolved;
- the command is local and private-by-default: it writes one Markdown file
  at `--out`, or a durable session-archive path when `--out` is omitted;
- `export-claude-session --current` resolves the session the same way, and
  never falls back to `--latest` if it can't; every successful export,
  regardless of discovery flag, prints a `Source transcript: <path>` line
  naming the file it actually read;
- generated frontmatter defaults to `privacy: private` and
  `authority: non_authoritative_context`;
- the source SHA-256, export timestamp, adapter version, warning list,
  sensitivity metadata, and transcript statistics are preserved in the
  frontmatter;
- the output file is created with user-only (`0600`) permissions from the
  first write, not chmod-ed afterward;
- passing the transcript itself as `--out` is rejected, even with
  `--force`;
- malformed transcript lines are collected as warnings rather than treated
  as fatal errors, since Claude Code's own documentation describes its
  JSONL transcript format as internal and version-dependent;
- sensitivity scanning is heuristic and does not certify that output is
  safe to publish;
- `inspect-export` validates manifest shape, transcript statistics, and
  source hash without printing transcript body text. A source that has
  only grown since export (the normal case for a live session, which is
  still being written) reports `match_source_grew`, not `mismatch` — both
  are a verified export; `mismatch` alone is a failed one.

---

## Safety Rules

Follow these rules for every run:

1. Do not commit Markdown exports or transcript excerpts.
2. Do not inspect undocumented Claude Code storage internals directly (raw
   JSONL scraping, session-index files, etc.). Use
   `lrh conversation export-claude-session`, which applies the documented,
   defensive-parsing adapter this project maintains.
3. Do not print transcript text during routine verification. Avoid `cat`,
   `head`, `tail`, `sed`, pagers, and line-based previews of the export.
4. Use `lrh conversation inspect-export` for human- and machine-checkable
   metadata.
5. If the user explicitly asks to view transcript content, confirm that
   they intend to display private conversation text before showing
   bounded excerpts.

---

## Execution Steps

Work through these steps in order.

### Step 1 — Resolve session input

**This step is read-only.** It never calls `export-claude-session` — that
command writes the durable artifact as soon as it runs, which would
create the file before Step 3's confirmation gate for a model-initiated
invocation. Everything here uses only metadata-only commands or local
file checks.

First resolve `<app_data_dir>`: `--app-data-dir` when supplied by the
user, else `$CLAUDE_CONFIG_DIR`, else `~/.claude`.

Determine the input route:

1. **No discovery flag (the default), or explicit `--current`**: both mean
   the same thing — run
   `lrh conversation current-claude-session-id --app-data-dir <app_data_dir> --format json`.
   On success, its `session_id` and `transcript_path` fields are what
   Step 3 states; the actual export in Step 4 uses `--current`, which
   resolves the same session again on its own (metadata-only resolution
   has no side effect to grow stale between the two calls within one
   invocation). On failure (`CLAUDE_CODE_SESSION_ID` unset, or the glob
   under `<app_data_dir>/projects/*/` matches zero or more than one
   transcript), the current session cannot be resolved — ask the user
   which of `--transcript-path`, `--session-id`, or `--latest` to use
   instead, the same as older versions of this skill always did.
2. **Explicit transcript path**: if `--transcript-path PATH` is given,
   verify the file exists on disk. `<transcript_file>` is that path, and
   Step 4 passes it through as `--transcript-path` unchanged.
3. **Session ID**: if `--session-id ID` is given, resolve it yourself by
   globbing `<app_data_dir>/projects/*/<ID>.jsonl`. Zero matches or more
   than one match is an error — report it and ask for an explicit
   `--transcript-path` to disambiguate rather than guessing. Exactly one
   match becomes `<transcript_file>`, passed through as `--transcript-path`
   in Step 4.
4. **Latest session**: if `--latest` is given, resolve it yourself,
   read-only, so Step 3 can state a real destination before Step 4 runs
   (the default `--out` filename is derived from the resolved session's
   id, which Step 3 must be able to show). `export-claude-session --latest`
   is scoped by default to the invoking working directory's own Claude
   project — mirror that scoping rather than searching every project:
   compute `<project_slug>` by taking the absolute path of the current
   working directory and replacing every `/`, `.`, and `_` with `-`
   (Claude Code's own project-bucket naming rule), then glob
   `<app_data_dir>/projects/<project_slug>/*.jsonl`. Zero matches is an
   error — report it (mention `--all-projects` exists on the CLI itself
   as a manual fallback, not exposed by this skill). Sort by modification
   time and take the most recent; ties break arbitrarily, matching the
   CLI's own undocumented tie behavior. That becomes `<transcript_file>`,
   passed through as `--transcript-path` in Step 4 — the same treatment
   as route 3, and for the same reason: Step 3 needs a concrete file
   before it can state what will be written.

Every route now resolves a concrete file (or, for route 1, a concrete
session id) before Step 3, so Step 3 always has a real destination to
state. Step 4 passes `--transcript-path <transcript_file>` for routes
2–4; for route 1 it passes `--current` instead of reusing this step's
resolved path directly, since `--current` is the exporter's own
purpose-built flag for "the current session" and needs no path handed to
it. Whichever route ran, Step 5's verification always uses the
`Source transcript:` line Step 4's own output prints, not a value
resolved here.

A live session's transcript is still being written. **Note this
explicitly wherever the session is stated to the user (Step 3) and in
the final report (Step 6): an export of the current or latest session is
a snapshot up to the moment of export, and excludes anything written to
the transcript afterward.**

### Step 2 — Choose archive mode

Default to LRH's durable private session archive. The archive root
resolves as:

1. `--archive-root` when supplied by the user;
2. `LRH_SESSION_ARCHIVE_ROOT`;
3. `~/.local/share/lrh/session-archive`.

Claude exports live below that root under `claude/exports/YYYY/MM/`.

### Step 3 — State or confirm before writing

**Write-protection gate, regardless of invocation route** (see
`lrh-create-skill/references/frontmatter-guide.md`'s
`disable-model-invocation` guidance: `when_to_use` narrows the
auto-trigger surface, but the actual write-protection is inside the
skill). This step exists because the archive is durable and permanent by
default (Step 2) — capture is not a reversible, self-cleaning action the
way an ephemeral `/tmp` write would be. Both branches below state the
same two things: the resolved session (path, session id, "current", or
"latest") and the destination (durable archive path, or the explicit
`--out` override), plus the live-session snapshot note from Step 1 when
the route is "current" or "latest". They differ only in whether they
wait for a reply.

**First, check for a dangerous flag — this overrides the invocation-source
branch below, even for a typed invocation.** Currently this list has one
entry: `--force`. If the invocation includes `--force`, state the resolved
session and destination, state explicitly that an existing file at that
destination would be overwritten, and wait for explicit confirmation
before proceeding to Step 4 — regardless of whether the invocation was
user-typed. This is a static check on the flag's presence, not a live
filesystem check for whether a file actually exists there: predicting the
exact default destination would mean duplicating the exporter's own
path-and-sanitization formula (`claude_export.py:488-498`) inside this
skill, and a future drift between the two would silently produce a wrong
answer — the same class of bug two other findings in this skill's own
review caught. Asking on every `--force`, even the rare case where nothing
would actually be overwritten, is the safe direction to be imprecise in.
This list is intentionally short and explicit; a future dangerous flag
gets added here by name, not inferred.

**Otherwise, how this invocation arrived decides which branch applies:**

- **User-typed invocation.** The current turn is the literal slash
  command — it arrives as `<command-message>`/`<command-name>` tags (or
  the equivalent explicit textual invocation the current platform
  surfaces) naming `/lrh-export-claude`, typed by the user this turn. A
  human typing the command is the explicit request by construction (per
  the decision recorded 2026-09-20), regardless of what flags accompany
  it or how the message is phrased — "Yes, please execute
  `/lrh-export-claude`" counts exactly the same as a bare
  `/lrh-export-claude`. State the resolved session and destination as
  information — including the durable-archive note — and proceed
  directly to Step 4 without waiting for a reply. Do not also ask about
  the discovery route or `--out`; nothing here is a question.
- **Model-initiated invocation.** Any other route into this skill — a
  proactive offer, or a call chained from another skill or workflow, with
  no literal user-typed slash command this turn. State the same resolved
  session and destination, then wait for explicit confirmation before
  proceeding to Step 4, exactly as before.
- **Ambiguous.** If the invocation signal cannot be confidently read —
  for instance, no reliable way this turn to check for a `<command-name>`
  tag — treat it as model-initiated and wait for confirmation. Never
  guess it was typed when unsure: the durable archive write is exactly
  the case this gate exists to protect, and a false "typed" classification
  would skip the one check meant to catch an unintended write.

### Step 4 — Run the export

Run the exporter with a restrictive umask so generated files are created
user-only. Pass exactly the discovery flag Step 1 determined:

- Route 1 (no flag, or explicit `--current`): `--current`, plus
  `--app-data-dir <app_data_dir>` — this route defers its actual
  resolution to this command, exactly like Step 1's own
  `current-claude-session-id` call, so the same `<app_data_dir>` from
  Step 1 must be forwarded, or a non-default `--app-data-dir` the user
  supplied would silently resolve against the exporter's own default
  instead.
- Route 2 (`--transcript-path`): `--transcript-path <transcript_file>`
  resolved in Step 1. `--app-data-dir` is not needed — the path is
  already exact.
- Route 3 (`--session-id`): `--transcript-path <transcript_file>` resolved
  in Step 1 — passed as an explicit path, not the bare `--session-id`
  flag, so the exact file this step exports is the exact file already
  disambiguated. `--app-data-dir` is not needed for the same reason.
- Route 4 (`--latest`): `--transcript-path <transcript_file>` resolved in
  Step 1 — the same treatment as route 3, for the same reason: the exact
  file Step 3 already stated is the exact file this step exports.
  `--app-data-dir` is not needed here either.

Only route 1 needs `--app-data-dir` forwarded to this command; routes 2–4
always pass an already-exact `--transcript-path` instead. Pick the one
line below matching the route Step 1 determined — this is not a single
command with optional parts, since a real shell would parse `(...|...)`
as syntax, not a placeholder:

```bash
# Route 1 — no flag, or explicit --current
( umask 077
  lrh conversation export-claude-session --current --app-data-dir <app_data_dir> \
    [--out OUTPUT.md] [--archive-root PATH] [--force] [--source-id ID] \
    [--no-scan-sensitive] [--include-system-attachments] [--include-subagents] )

# Routes 2-4 — --transcript-path, --session-id, or --latest
( umask 077
  lrh conversation export-claude-session --transcript-path <transcript_file> \
    [--out OUTPUT.md] [--archive-root PATH] [--force] [--source-id ID] \
    [--no-scan-sensitive] [--include-system-attachments] [--include-subagents] )
```

If `--out` is omitted, the CLI prints the durable session archive
destination path. Read the `Source transcript: <path>` line from this
command's own output and keep it — Step 5 verifies against exactly this
value, not anything resolved earlier.

### Step 5 — Inspect the export

Immediately verify the Markdown artifact against the source transcript,
using the `Source transcript:` path Step 4's own output printed — not a
value resolved in Step 1:

```bash
lrh conversation inspect-export \
  <output_path> \
  --source <source_transcript_from_step_4>
```

Confirm exit code 0 and a `Source hash:` of either `match` or
`match_source_grew` — both are a verified export. `match_source_grew`
means the live transcript grew after the export read it (the normal case
for a live session); the text output includes a "source grew by N bytes"
line, which the report in Step 6 should mention. Any nonzero exit code —
which includes `Source hash: mismatch`, since the inspector never reports
`mismatch` with exit 0 — is a failed export verification: report the
failure and keep the files private for debugging.

### Step 6 — Report metadata only

Summarize the export using only command output and inspector metadata:

| Field | Value |
|---|---|
| **Exported Artifact** | `<output_path>` |
| **Source ID** | `<source_id>` |
| **Source SHA-256** | `<source_sha256>` |
| **Verification** | `match` or `match_source_grew (+N bytes since export)` |
| **Privacy** | `private` |
| **Sensitivity** | `none_detected` (or `potential`, `unscanned`) |
| **Warnings** | `<warning_count>` |

For a "current" or "latest" export, restate the snapshot note from Step 1:
this export is current up to the moment it ran, and does not include
anything written to the transcript afterward.

Do not paste transcript body text into chat. Do not run line-based
previews to "spot check" the Markdown; the frontmatter can be followed
immediately by private transcript content.

### Step 7 — Close out

Tell the user whether the export is verified and where the private file
lives. If the user wants a committed LRH artifact, explain that raw
exports are non-authoritative private context and must be reviewed and
promoted into a separate sanitized project artifact before commit.
