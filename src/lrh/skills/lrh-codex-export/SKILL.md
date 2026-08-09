---
name: lrh-codex-export
description: >
  Export the current or specified Codex task through LRH's Codex app-server
  conversation exporter. Use when the user wants a Claude-/export-like
  durable private capture of a Codex session. Wraps
  `lrh conversation export-codex-thread`, then verifies the artifact with
  `lrh conversation inspect-export` and reports metadata only.
disable-model-invocation: true
argument-hint: "[THREAD_ID]"
---

# lrh-codex-export Skill

This skill is a thin workflow wrapper around the LRH CLI. It does not duplicate
the Python exporter, inspect undocumented Codex storage internals, or promote
private transcript text into LRH project state.

The goal is to safely capture a Codex task transcript for later private review,
parallel to Claude's `/export` habit, while preserving LRH's privacy and
authority boundaries.

---

## Inputs

Provide a Codex thread id as the optional argument:

```text
/lrh-codex-export 019fc43f-e2d9-7503-88cb-9d9a8136c111
```

If no argument is supplied, default to `CODEX_THREAD_ID` when it is set. If
neither an argument nor `CODEX_THREAD_ID` is available, ask the user for the
Codex thread id before proceeding.

---

## Reference Knowledge

Use the repository CLI documentation as the command contract:

- `docs/reference/cli/conversation.md` for
  `lrh conversation export-codex-thread` and
  `lrh conversation inspect-export`.

The relevant CLI guarantees are:

- `export-codex-thread` reads through the Codex app-server `thread/read` API.
- `--thread-id` defaults to `CODEX_THREAD_ID`.
- `--raw-out` is required, must be absolute, and must be outside the current
  Git worktree.
- the raw JSON capture is private and written with restrictive file mode where
  supported.
- terminal output is metadata-only.
- `inspect-export` validates manifest shape, transcript statistics, and source
  hash without printing transcript body text.

---

## Safety Rules

Follow these rules for every run:

1. Do not commit raw JSON captures, Markdown exports, or transcript excerpts.
2. Choose absolute private output paths outside the current Git worktree,
   especially for `--raw-out`.
3. Do not inspect undocumented Codex app storage internals. Use
   `lrh conversation export-codex-thread`, which talks to the documented
   app-server boundary used by this project.
4. Do not print transcript text during routine verification. Avoid `cat`,
   `head`, `tail`, `sed`, pagers, and line-based previews of `EXPORT.md`.
5. Use `lrh conversation inspect-export` for human- and machine-checkable
   metadata.
6. If the user explicitly asks to view transcript content, confirm that they
   intend to display private conversation text before showing bounded excerpts.
7. If macOS, endpoint security, or Codex reports that the Codex executable is
   blocked, quarantined, replaced, or suspicious, stop and investigate the
   executable before treating the export as reliable.

---

## Execution Steps

Work through these steps in order.

### Step 1 -- Resolve the thread id

If the user supplied an argument, use it as `THREAD_ID`.

If no argument was supplied, check:

```bash
printf '%s\n' "$CODEX_THREAD_ID"
```

If `CODEX_THREAD_ID` is non-empty, use that value as `THREAD_ID`.

If no thread id is available, stop and ask the user for the Codex thread id.

### Step 2 -- Choose private output paths

Create a private absolute output directory outside the current Git worktree.
For routine dogfood or ad hoc capture, prefer the platform temporary directory
from `TMPDIR`, falling back to `/tmp`. On macOS, `TMPDIR` or `/tmp` may resolve
under `/private`, but the skill should not hard-code `/private/tmp`:

```bash
EXPORT_ID="$(date -u +%Y%m%dT%H%M%SZ)"
TMP_ROOT="${TMPDIR:-/tmp}"
TMP_ROOT="${TMP_ROOT%/}"
EXPORT_DIR="$(mktemp -d "$TMP_ROOT/lrh-codex-export-$EXPORT_ID.XXXXXX")"
chmod 700 "$EXPORT_DIR"
EXPORT_PATH="$EXPORT_DIR/export.md"
RAW_PATH="$EXPORT_DIR/raw.json"
```

If the user wants a durable private archive instead of an ephemeral dogfood
capture, choose an absolute path under the user's private archive location,
such as `$HOME/.lrh/private/codex/<safe-thread-or-run-id>/`, but still keep it
outside the project Git worktree unless the user has explicitly designed and
approved a sanitized committed artifact.

### Step 3 -- Run the export

Run the CLI exporter with a restrictive umask so the Markdown transcript is
created user-only as well as the raw capture:

```bash
(
  umask 077
  lrh conversation export-codex-thread \
    --thread-id "$THREAD_ID" \
    --out "$EXPORT_PATH" \
    --raw-out "$RAW_PATH" \
    --timeout-seconds 20
)
chmod 600 "$EXPORT_PATH" "$RAW_PATH"
```

If the output files already exist and the user wants to replace them, rerun with
`--force`. Do not use `--force` for source/output path collisions or for
repository-local raw captures.

In restricted or sandboxed environments, app-server access may require approval
because Codex local state can live under `~/.codex`. If the command fails due
to sandbox, permission, or local-state access restrictions, report the failure
and rerun only through the environment's approval mechanism. Do not fall back to
scraping local storage files directly.

### Step 4 -- Inspect the export

Immediately inspect the Markdown artifact against the raw source capture:

```bash
lrh conversation inspect-export \
  "$EXPORT_PATH" \
  --source "$RAW_PATH" \
  --format json
```

Treat a nonzero inspector exit as a failed export verification. Report the
failure and keep the files private for debugging.

### Step 5 -- Report metadata only

Summarize the export using only command output and inspector metadata:

- Markdown export path.
- Raw capture path.
- privacy, authority, and sensitivity.
- warning count and sensitivity-scan status.
- source-hash status.
- turn count, message count, and artifact statistics when present.
- any trust or app-server diagnostics recorded as warnings.

Do not paste transcript body text into chat. Do not run line-based previews to
"spot check" the Markdown; the frontmatter can be followed immediately by
private transcript content.

### Step 6 -- Close out

Tell the user whether the export is verified and where the private files live.
If the files are ephemeral under `/private/tmp`, say so. If the user wants a
committed LRH artifact, explain that raw exports are non-authoritative private
context and must be reviewed and promoted into a separate sanitized project
artifact before commit.
