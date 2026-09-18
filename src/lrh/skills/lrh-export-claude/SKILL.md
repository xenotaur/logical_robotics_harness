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
  judgment call. Supports explicit `--transcript-path`, `--session-id`, or
  `--latest` discovery, defaulting to a durable private session archive
  when `--out` is omitted.
argument-hint: "[--out OUTPUT.md] [--transcript-path PATH | --session-id ID | --latest]"
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

Provide one of the mutually exclusive discovery flags, and optional
`--out OUTPUT.md`:

```bash
# Export using durable private archive default
/lrh-export-claude --latest

# Export using explicit transcript path and custom output override
/lrh-export-claude --transcript-path ~/.claude/projects/<project>/<session-id>.jsonl --out export.md

# Export using session ID discovery
/lrh-export-claude --session-id <session-id>
```

If no argument is supplied, ask the user which of `--transcript-path`,
`--session-id`, or `--latest` to use before proceeding — unlike Codex's
single-thread-id resolver, Claude Code sessions have no equivalent
ambient environment variable to default to.

### Additional Options

- `--out PATH` — optional path for the destination Markdown export file.
  When omitted, defaults to a durable private session archive path
  (`<archive_root>/claude/exports/<YYYY>/<MM>/<session-id>.md`).
- `--app-data-dir PATH` — path to Claude Code's application data directory
  (default: `$CLAUDE_CONFIG_DIR`, or `~/.claude` if unset).
- `--archive-root PATH` — optional private session archive root override.
- `--force` — overwrite the destination file if it already exists. This
  never allows the source transcript and output to be the same file, even
  with `--force`.
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
  `lrh conversation export-claude-session` and
  `lrh conversation inspect-export`.

The relevant CLI guarantees are:

- the command is local and private-by-default: it writes one Markdown file
  at `--out`, or a durable session-archive path when `--out` is omitted;
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
  source hash without printing transcript body text.

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

### Step 1 — Resolve transcript input

Determine the input route:

1. **Explicit transcript path**: if `--transcript-path PATH` is given,
   verify the file exists on disk.
2. **Session ID**: if `--session-id ID` is given, pass it directly —
   `export-claude-session` discovers the transcript by globbing
   `<app-data-dir>/projects/*/<ID>.jsonl` and errors on more than one
   match rather than silently picking one.
3. **Latest session**: if `--latest` is given, pass it directly —
   `export-claude-session` discovers the most recently modified
   transcript file under `<app-data-dir>/projects/*/*.jsonl`.

If none of the three was supplied and none can be inferred from the
user's own message this turn, ask which one to use before proceeding.

### Step 2 — Choose archive mode

Default to LRH's durable private session archive. The archive root
resolves as:

1. `--archive-root` when supplied by the user;
2. `LRH_SESSION_ARCHIVE_ROOT`;
3. `~/.local/share/lrh/session-archive`.

Claude exports live below that root under `claude/exports/YYYY/MM/`.

### Step 3 — Confirm before writing

**Mandatory confirm-before-write gate, regardless of invocation route**
(see `lrh-create-skill/references/frontmatter-guide.md`'s
`disable-model-invocation` guidance: `when_to_use` narrows the
auto-trigger surface, but the actual write-protection is an explicit
confirm gate inside the skill). This step exists because the archive is
durable and permanent by default (Step 2) — capture is not a reversible,
self-cleaning action the way an ephemeral `/tmp` write would be.

State the resolved discovery route (transcript path, session id, or
"latest") and the destination (durable archive path, or the explicit
`--out` override) and wait for explicit confirmation before proceeding to
Step 4. Skip asking only when the user's own message in this turn already
explicitly requested this export by name, path, or session id — do not
skip based on a discovery flag being inferable alone, since an inferred
or ambient target is exactly the auto-invocation case this gate exists to
catch.

### Step 4 — Run the export

Run the exporter with a restrictive umask so generated files are created
user-only:

```bash
( umask 077
  lrh conversation export-claude-session \
    [--transcript-path PATH | --session-id ID | --latest] \
    [--out OUTPUT.md] \
    [--archive-root PATH] \
    [--force] \
    [--source-id ID] \
    [--no-scan-sensitive] \
    [--include-system-attachments] \
    [--include-subagents] )
```

If `--out` is omitted, the CLI prints the durable session archive
destination path.

### Step 5 — Inspect the export

Immediately verify the Markdown artifact against the source transcript:

```bash
lrh conversation inspect-export \
  <output_path> \
  --source <transcript_file>
```

Confirm exit code 0 and `Source hash: match`. Treat a nonzero inspector
exit as a failed export verification — report the failure and keep the
files private for debugging.

### Step 6 — Report metadata only

Summarize the export using only command output and inspector metadata:

| Field | Value |
|---|---|
| **Exported Artifact** | `<output_path>` |
| **Source ID** | `<source_id>` |
| **Source SHA-256** | `<source_sha256>` |
| **Privacy** | `private` |
| **Sensitivity** | `none_detected` (or `potential`, `unscanned`) |
| **Warnings** | `<warning_count>` |

Do not paste transcript body text into chat. Do not run line-based
previews to "spot check" the Markdown; the frontmatter can be followed
immediately by private transcript content.

### Step 7 — Close out

Tell the user whether the export is verified and where the private file
lives. If the user wants a committed LRH artifact, explain that raw
exports are non-authoritative private context and must be reviewed and
promoted into a separate sanitized project artifact before commit.
