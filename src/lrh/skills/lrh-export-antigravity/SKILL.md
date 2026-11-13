---
name: lrh-export-antigravity
description: >
  Export the current or specified Google Antigravity session transcript into a private,
  non-authoritative Markdown export artifact. Use when the user asks to export,
  capture, or archive an Antigravity conversation session. Wraps `lrh conversation
  export-antigravity-session`, verifies the artifact with `lrh conversation
  inspect-export`, and reports metadata-only terminal status.
when_to_use: >
  Invoke only when the user explicitly asks to export, capture, or archive
  an Antigravity session transcript log for later private review. Do not
  invoke proactively or infer the intent from a passing mention of
  exporting — by default this skill writes a durable, permanent copy into
  the user's local session archive (not a self-cleaning temp file), so
  invocation should always trace to a direct request, not an agent's own
  judgment call. A user-typed `/lrh-export-antigravity` invocation is
  itself the explicit request — it states the resolved transcript and
  destination and proceeds without a separate confirmation; a
  model-initiated invocation (offered proactively, or chained from another
  skill or workflow) still requires an explicit confirmation before
  writing. `--force` is the one exception: it always waits for
  confirmation, even for a typed invocation, since it can overwrite an
  existing export. Supports explicit `--transcript-path`,
  `--conversation-id`, or `--latest` discovery, defaulting to a durable
  private session archive when `--out` is omitted.
argument-hint: "[--out OUTPUT.md] [--transcript-path PATH | --conversation-id ID | --latest]"
---

# lrh-export-antigravity Skill

This skill provides session transcript export capability via `/lrh-export-antigravity` inside LRH. It wraps the `lrh conversation export-antigravity-session` CLI subcommand, converts raw Antigravity JSONL transcript logs into standardized Markdown export artifacts with frontmatter metadata, and verifies the generated artifact using `lrh conversation inspect-export`.

This workflow operates strictly under LRH privacy and non-authoritative export rules: it writes private Markdown artifacts to durable local session archive paths (or explicit `--out` overrides) with user-only file permissions (`umask 077` / mode `0600`) without printing raw transcript text to terminal output or modifying repository control-plane state.

---

## Inputs

Provide one of the mutually exclusive discovery flags or transcript path arguments (and optional `--out OUTPUT.md`):

```bash
# Export using durable private archive default
/lrh-export-antigravity --latest

# Export using explicit transcript path and custom output override
/lrh-export-antigravity --transcript-path ~/.gemini/antigravity/brain/<id>/.system_generated/logs/transcript.jsonl --out export.md

# Export using conversation ID discovery
/lrh-export-antigravity --conversation-id <conversation-id>
```

### Additional Options
- `--out PATH`: Optional path for destination Markdown export file. When omitted, defaults to a durable private session archive path (`<archive_root>/antigravity/exports/<YYYY>/<MM>/<session-id>.md`) derived via `resolve_archive_root()`.
- `--archive-root PATH`: Optional private session archive root override.
- `--force`: Overwrite destination file if it already exists.
- `--no-scan-sensitive`: Skip heuristic sensitive content scanning.
- `--source-id ID`: Record explicit custom session source identifier in metadata.

---

## Running `lrh`

**If `lrh` is not on PATH**, every `lrh` command in this workflow can run
from an LRH checkout as `PYTHONPATH=src python3 -m lrh.cli.main ...` with
the same subcommand and flags. That covers the capability checks
(`--help`), session or thread resolution, the export itself, and
`inspect-export`. Use the same prefix for all of them in a given run.

An editable `lrh` install can also point at a different checkout than the
one you are working in (`pip show lrh` reports its "Editable project
location"), and `lrh version` reports install-time metadata rather than the
code that actually runs. When in doubt inside an LRH checkout, prefer the
`PYTHONPATH=src` form.

---

## Execution Procedure

Work through these steps in order:

### Step 1 — Resolve Transcript Input

**This step is read-only.** It never calls `export-antigravity-session` —
that command writes the durable artifact as soon as it runs, which would
create the file before Step 2's confirmation gate. Use only local file
checks here.

`<appDataDir>` is `--app-data-dir` when supplied, else
`~/.gemini/antigravity`.

Every route must end with one concrete file, `<transcript_file>`. Steps 3
and 4 both pass that same file, so the file exported is the file verified;
the exporter's own output does not name the transcript it read.

1. **Explicit transcript path**: If `--transcript-path PATH` is given (or provided in session metadata/context as `transcriptPath`), verify the file exists on disk. That file is `<transcript_file>`.
2. **Conversation ID**: If `--conversation-id ID` is given, use `<appDataDir>/brain/<id>/.system_generated/logs/transcript.jsonl` if it exists, else `transcript_full.jsonl` in the same directory. If neither exists, stop and report it.
3. **Latest session**: If `--latest` is given, find the most recently modified file matching `<appDataDir>/brain/*/.system_generated/logs/transcript.jsonl` or `transcript_full.jsonl`. If none exists, stop and report it.

These are the same rules the exporter applies for `--conversation-id` and
`--latest`; resolving them here only fixes the file before anything is
written.

A live session's transcript is still being written. **When the transcript
may belong to a live session (the `--latest` route, or this session's own
`transcriptPath` from context), say so wherever the transcript is stated
(Step 2) and in the final report (Step 5): the export is a snapshot up to
the moment it runs.**

### Step 2 — State or Confirm Before Writing

**Write-protection gate, regardless of invocation route.** `when_to_use`
narrows the auto-trigger surface, but the actual write-protection is this
step, because the archive is durable and permanent by default (`--out`
omitted). Both branches below state the same things: the resolved
`<transcript_file>` and the destination (the durable archive under
`<archive_root>/antigravity/exports/YYYY/MM/`, or the explicit `--out`
path), plus the live-session snapshot note from Step 1 when it applies.
They differ only in whether they wait for a reply.

**First, check for a dangerous flag — this overrides the invocation-source
branch below, even for a typed invocation.** The list has one entry:
`--force`. If the invocation includes `--force`, state the transcript and
destination, state explicitly that an existing file at that destination
would be **overwritten**, and wait for explicit confirmation before Step 3.
This is a check on the flag's presence, not on whether a file actually
exists there.

**Otherwise, how this invocation arrived decides the branch:**

- **User-typed invocation.** The current turn is the literal slash command
  naming `/lrh-export-antigravity` (or its deprecated alias
  `/lrh-antigravity-export`), typed by the user this turn (it arrives
  as `<command-message>`/`<command-name>` tags, or the equivalent explicit
  textual invocation the platform surfaces). A typed command is the
  explicit request. State the transcript and destination as information
  and proceed to Step 3 without waiting for a reply.
- **Model-initiated invocation.** Any other route — a proactive offer, or a
  call chained from another skill or workflow. State the same transcript
  and destination, then wait for explicit confirmation before Step 3.
- **Ambiguous.** If the invocation signal cannot be confidently read,
  treat it as model-initiated and wait for confirmation. Never guess that
  it was typed: an unintended durable write is exactly what this gate
  exists to prevent.

### Step 3 — Run Exporter CLI

Execute the exporter CLI subcommand with restrictive file creation umask (`umask 077`):

```bash
( umask 077 && lrh conversation export-antigravity-session \
  --transcript-path <transcript_file> \
  [--out <output_path>] \
  [--archive-root <archive_root>] \
  [--force] \
  [--source-id <source_id>] \
  [--no-scan-sensitive] )
```

If `--out` is omitted, the CLI outputs the durable session archive destination path.
Pass `--archive-root` through whenever the user supplied it, so the export
lands under the root Step 2 stated.

Always pass the `<transcript_file>` resolved in Step 1 as
`--transcript-path`, even for the `--conversation-id` and `--latest`
routes, so the exporter cannot pick a different file (for example, a
newer transcript that appeared after Step 2).

**If the destination already exists** (typically a same-session re-export
without `--force`), the exporter refuses to overwrite it and this step
fails. To replace it, re-run with `--force`. That takes Step 2's
dangerous-flag path: state that the existing file at the destination will
be overwritten, and wait for explicit confirmation. Alternatively, choose a
different `--out`.

### Step 4 — Verify Export Artifact

Run the LRH export inspector supplying the same `<transcript_file>` from Step 1 (`--source <transcript_file>`) to verify frontmatter schema validity, source SHA-256 integrity, and summary statistics:

```bash
lrh conversation inspect-export <output_path> --source <transcript_file>
```

Confirm exit code 0 and a `Source hash:` of either `match` or
`match_source_grew`; both are a verified export. `match_source_grew` means
the live transcript grew after the export read it but its recorded prefix
still matches (the normal case for a still-running session). The export is
a snapshot as of the moment it ran. A true `mismatch` (nonzero exit) means
the source no longer matches what was exported: an earlier byte changed,
the source shrank, or (for an export with no recorded byte count) the
whole file differs. Among hash comparisons, that is the only failing
result. Any nonzero exit is a failed verification, though, including
`source_missing`, `source_not_file`, `source_unreadable`, and a
`transcript_statistics` mismatch. Report it and keep the files private for
debugging.

### Step 5 — Terminal Summary

Report metadata-only terminal status to the user. Do not print raw transcript body text to stdout or stderr.

Present a summary table with verbatim manifest metadata:

| Field | Value |
|---|---|
| **Exported Artifact** | `<output_path>` |
| **Source ID** | `<source_id>` |
| **Source SHA-256** | `<source_sha256>` |
| **Verification** | `match` or `match_source_grew (+N bytes since export)` |
| **Privacy** | `private` |
| **Sensitivity** | `none_detected` (or `potential`, `unscanned`) |
| **Warnings** | `<warning_count>` |

A `potential` sensitivity status means the heuristic scanner flagged
strings that need a human review before the export is shared anywhere. It
does not mean the export failed. `unscanned` means no scan was run (for
example, `--no-scan-sensitive`). `none_detected` is not a guarantee that the
content is safe to share.

When Step 1's snapshot note applied, repeat it: the export covers the
transcript only up to the moment it ran.

