---
name: lrh-antigravity-export
description: >
  Export the current or specified Google Antigravity session transcript into a private,
  non-authoritative Markdown export artifact. Use when the user asks to export,
  capture, or archive an Antigravity conversation session. Wraps `lrh conversation
  export-antigravity-session`, verifies the artifact with `lrh conversation
  inspect-export`, and reports metadata-only terminal status.
when_to_use: >
  Invoke when the user asks to export, capture, or archive an Antigravity
  session transcript log. Supports explicit `--transcript-path`, `--conversation-id`,
  or `--latest` discovery, defaulting to a durable private session archive when `--out` is omitted.
argument-hint: "[--out OUTPUT.md] [--transcript-path PATH | --conversation-id ID | --latest]"
---

# lrh-antigravity-export Skill

This skill provides session transcript export capability via `/lrh-antigravity-export` inside LRH. It wraps the `lrh conversation export-antigravity-session` CLI subcommand, converts raw Antigravity JSONL transcript logs into standardized Markdown export artifacts with frontmatter metadata, and verifies the generated artifact using `lrh conversation inspect-export`.

This workflow operates strictly under LRH privacy and non-authoritative export rules: it writes private Markdown artifacts to durable local session archive paths (or explicit `--out` overrides) with user-only file permissions (`umask 077` / mode `0600`) without printing raw transcript text to terminal output or modifying repository control-plane state.

---

## Inputs

Provide one of the mutually exclusive discovery flags or transcript path arguments (and optional `--out OUTPUT.md`):

```bash
# Export using durable private archive default
/lrh-antigravity-export --latest

# Export using explicit transcript path and custom output override
/lrh-antigravity-export --transcript-path ~/.gemini/antigravity/brain/<id>/.system_generated/logs/transcript.jsonl --out export.md

# Export using conversation ID discovery
/lrh-antigravity-export --conversation-id <conversation-id>
```

### Additional Options
- `--out PATH`: Optional path for destination Markdown export file. When omitted, defaults to a durable private session archive path (`<archive_root>/antigravity/exports/<YYYY>/<MM>/<session-id>.md`) derived via `resolve_archive_root()`.
- `--archive-root PATH`: Optional private session archive root override.
- `--force`: Overwrite destination file if it already exists.
- `--no-scan-sensitive`: Skip heuristic sensitive content scanning.
- `--source-id ID`: Record explicit custom session source identifier in metadata.

---

## Execution Procedure

Work through these steps in order:

### Step 1 — Resolve Transcript Input

Determine the input route:
1. **Explicit transcript path**: If `--transcript-path PATH` is given (or provided in session metadata/context as `transcriptPath`), verify the file exists on disk.
2. **Conversation ID**: If `--conversation-id ID` is given, discover the transcript file under `<appDataDir>/brain/<id>/.system_generated/logs/transcript.jsonl` (or `transcript_full.jsonl`).
3. **Latest session**: If `--latest` is given, discover the newest transcript file under `<appDataDir>/brain/`.

### Step 2 — Run Exporter CLI

Execute the exporter CLI subcommand with restrictive file creation umask (`umask 077`):

```bash
( umask 077 && lrh conversation export-antigravity-session \
  --transcript-path <transcript_file> \
  [--out <output_path>] \
  [--force] \
  [--source-id <source_id>] \
  [--no-scan-sensitive] )
```

If `--out` is omitted, the CLI outputs the durable session archive destination path.

**If `lrh` is not on PATH.** From an LRH checkout, run the same
subcommand with the same flags as
`PYTHONPATH=src python3 -m lrh.cli.main conversation ...`. An editable
`lrh` install can also point at a different checkout than the one you are
working in (`pip show lrh` reports its "Editable project location"), and
`lrh version` reports install-time metadata rather than the code that
actually runs. When in doubt inside an LRH checkout, prefer the
`PYTHONPATH=src` form.

**If the destination already exists** (typically a same-session re-export
without `--force`), the exporter refuses to overwrite it and this step
fails. To replace it, re-run with `--force`, which **overwrites** the
existing file at the destination; tell the user that before re-running.
Alternatively, choose a different `--out`. This skill has no
confirm-before-write gate today (that question is
`WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT`), and this note adds none.

### Step 3 — Verify Export Artifact

Run the LRH export inspector supplying the source transcript file (`--source <transcript_file>`) to verify frontmatter schema validity, source SHA-256 integrity, and summary statistics:

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

### Step 4 — Terminal Summary

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

