---
name: lrh-codex-export
description: 'Export the current or specified Codex task through LRH''s Codex app-server
  conversation exporter. Use when the user wants a Claude-/export-like durable private
  capture of a Codex session. Wraps `lrh conversation archive-codex-thread`, then
  verifies the artifact with `lrh conversation inspect-export` and reports metadata
  only.

  '
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
  `lrh conversation archive-codex-thread`,
  `lrh conversation export-codex-thread`, and
  `lrh conversation inspect-export`.

The relevant CLI guarantees are:

- `archive-codex-thread` writes routine captures into LRH's durable private
  session archive under a Codex date-bucketed subtree.
- `archive-codex-thread --scratch` is the explicit ephemeral dogfood path.
- every archive export attempt writes `attempt.json` before app-server access
  and updates it with success or failure metadata.
- `export-codex-thread` reads through the Codex app-server `thread/read` API.
- `--thread-id` defaults to `CODEX_THREAD_ID`.
- low-level `export-codex-thread` requires caller-supplied `--out` and
  `--raw-out` paths; `--raw-out` must be absolute and outside the current Git
  worktree.
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

### Step 2 -- Choose archive mode

Default to LRH's durable private session archive. The archive root resolves as:

1. `--archive-root` when supplied by the user;
2. `LRH_SESSION_ARCHIVE_ROOT`;
3. `~/.local/share/lrh/session-archive`.

Codex exports live below that root under `codex/exports/YYYY/MM/`. Do not choose
`${TMPDIR:-/tmp}` for routine capture.

Use scratch mode only when the user explicitly asks for an ephemeral dogfood or
debug capture. Scratch mode is intentionally not the default:

```bash
SCRATCH_FLAG="--scratch"
```

### Step 3 -- Confirm before writing

**Mandatory confirm-before-write gate, regardless of invocation route** (see
`lrh-create-skill/references/frontmatter-guide.md`'s `disable-model-invocation`
guidance: `when_to_use` narrows the auto-trigger surface, but the actual
write-protection is an explicit confirm gate inside the skill). This step
exists because the archive is durable and permanent by default (Step 2) --
capture is not a reversible, self-cleaning action the way an ephemeral
`/tmp` write would be.

State the resolved `THREAD_ID` and the destination (durable archive path, or
explicitly "ephemeral scratch capture" if scratch mode applies) and wait for
explicit confirmation before proceeding to Step 4. Skip asking only when the
user's own message in this turn already explicitly requested this export by
name or thread id -- do not skip based on `CODEX_THREAD_ID` being set alone,
since an inferred or ambient thread id is exactly the auto-invocation case
this gate exists to catch.

### Step 4 -- Run the export

Run the durable archive wrapper with a restrictive umask so generated files are
created user-only:

```bash
(
  umask 077
  lrh conversation archive-codex-thread \
    --thread-id "$THREAD_ID" \
    --timeout-seconds 20
)
```

If the user explicitly requested scratch mode, include `--scratch` and report
the output as ephemeral:

```bash
(
  umask 077
  lrh conversation archive-codex-thread \
    --thread-id "$THREAD_ID" \
    --scratch \
    --timeout-seconds 20
)
```

In restricted or sandboxed environments, app-server access may require approval
because Codex local state can live under `~/.codex`. If the command fails due
to sandbox, permission, or local-state access restrictions, report the failure
and rerun only through the environment's approval mechanism. Do not fall back to
scraping local storage files directly.

### Step 5 -- Inspect the export

Immediately inspect the Markdown artifact against the raw source capture. Use
the paths printed by `archive-codex-thread`:

```bash
lrh conversation inspect-export \
  "$EXPORT_PATH" \
  --source "$RAW_PATH" \
  --format json
```

Treat a nonzero inspector exit as a failed export verification. Report the
failure and keep the files private for debugging.

### Step 6 -- Report metadata only

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

### Step 7 -- Close out

Tell the user whether the export is verified and where the private files live.
If scratch mode was used, say the files are ephemeral. If the user wants a
committed LRH artifact, explain that raw exports are non-authoritative private
context and must be reviewed and promoted into a separate sanitized project
artifact before commit.
