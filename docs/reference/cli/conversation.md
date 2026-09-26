# `lrh conversation`

Conversation commands convert and inspect local conversation artifacts without
importing them into LRH project state.

## Codex Export Manifest Contract

Codex conversation exports use a private, non-authoritative manifest contract
before any file adapter, inspector command, or viewer is implemented. The typed
helpers live in `lrh.conversations.export_manifest`.

The manifest kind is `lrh_codex_conversation_export` with `schema_version: 1`.
Default Codex manifests are private and contextual:

- `source_tool: codex`
- `source_adapter: codex_manual_export`
- `privacy: private`
- `authority: non_authoritative_context`
- `sensitivity: unscanned`
- `sensitivity_scan: {status: not_scanned}`

Required provenance fields are:

- `source_sha256` — lowercase SHA-256 hex digest for the source export.
- `exported_at` — timezone-aware ISO-8601 export timestamp.
- `adapter_version` — manifest adapter version.
- `warnings` — deterministic warning list.
- `transcript_statistics` — `byte_count`, `character_count`, `line_count`, and
  optional `turn_count` / `message_count`.

`source_id` is optional and should be present when the exporting adapter has a
stable Codex session or thread identifier.

`source_byte_count` is optional, a non-negative integer, and emitted only when
set. It records how many source bytes were hashed to produce `source_sha256`.
The Claude and Antigravity exporters record it because their source is a live
transcript log that keeps growing after the export; the Codex exporters hash a
frozen raw capture and do not set it. Manifests without it, and the schema
version (still `1`), are unaffected.

Raw Codex exports remain private, non-authoritative context. They are not
imported into the `project/` control plane and do not become evidence,
decisions, work items, or status until a separate reviewed promotion step
creates those artifacts. Sensitivity scanning is heuristic and does not certify
that an export is safe to publish.

This contract is used by the file-based Codex adapter, inspector, and
safe-default `lrh serve` archive viewer below. It does not implement any change
to execution-record `session_transcript` pointer grammar.

## `lrh conversation current-codex-thread-id`

```bash
lrh conversation current-codex-thread-id
lrh conversation current-codex-thread-id --field session-transcript
lrh conversation current-codex-thread-id --format json
```

Reports the current Codex task/thread id and the matching LRH execution-record
pointer without exporting, reading, or printing transcript content. This is the
metadata-only resolver used by `/lrh-codex-session`, `/lrh-codex-export`,
`export-codex-thread`, and `archive-codex-thread`.

The session pointer form is:

```yaml
session_transcript: codex-app:<thread-id>
```

This value is a Codex task/thread pointer. It is not an export attempt id,
archive directory, `attempt.json` path, raw JSON path, Markdown export path, or
timestamp. Export attempts can be repeated for the same thread id; the
`codex-app:<thread-id>` pointer remains the stable execution-record identity
when Codex exposes the same thread id through `CODEX_THREAD_ID`.

### Options

- `--thread-id ID` — Codex thread id to report. Defaults to `CODEX_THREAD_ID`
  when the environment variable is set.
- `--format text|json` — output format. Text is the default.
- `--field all|thread-id|session-transcript` — single-field text output for
  scripts and closeout records.

### Exit behavior

The command returns nonzero for missing or whitespace-only thread ids. Terminal
output is metadata-only and does not include transcript body text.

## `lrh conversation convert-codex-file`

```bash
lrh conversation convert-codex-file INPUT.txt --out OUTPUT.md
```

Converts an explicit local Codex transcript or source text file into a UTF-8
Markdown artifact with `ConversationExportManifest` frontmatter. The command is
intentionally file-based: the caller supplies both the source path and output
path, and LRH does not inspect undocumented Codex app storage internals.

The command is local and private-by-default:

- it writes one Markdown file at `--out`;
- it rejects source/output path collisions even when `--force` is supplied;
- it does not import the transcript into a ledger, database, project control
  directory, or private state store;
- generated frontmatter defaults to `privacy: private` and
  `authority: non_authoritative_context`;
- the source SHA-256, export timestamp, adapter version, warning list,
  sensitivity metadata, and transcript statistics are preserved in the
  frontmatter;
- sensitivity scanning is heuristic and does not certify that output is safe to
  publish.

### Options

- `--out OUTPUT.md` — required Markdown export output path.
- `--force` — overwrite an existing output file. This never allows the source
  and output to be the same file.
- `--source-id ID` — optional stable Codex session or thread identifier to
  record in `source_id`.
- `--no-scan-sensitive` — skip the local heuristic sensitivity scanner and mark
  transcript frontmatter as `sensitivity: unscanned`.

### Exit behavior

The command returns nonzero for missing, non-file, unreadable, or non-UTF-8
inputs; existing outputs when `--force` is not supplied; source/output path
collisions; and output write failures.

On success it prints a concise deterministic summary with the output path,
privacy, sensitivity status, and warning count. Potential sensitive findings are
also reported as warnings on stderr.

## `lrh conversation export-codex-thread`

```bash
lrh conversation export-codex-thread \
  --thread-id THREAD_ID \
  --out EXPORT.md \
  --raw-out "$HOME/.lrh/private/codex/THREAD_ID.raw.json"
```

Exports a stored Codex thread through the Codex app-server `thread/read` API.
The command starts `codex app-server --listen stdio://`, performs the JSON-RPC
`initialize` / `initialized` / `thread/read` sequence with
`includeTurns: true`, writes a private raw JSON capture, and renders a Markdown
artifact with `ConversationExportManifest` frontmatter.

The command is local and private-by-default:

- it writes one Markdown file at `--out`;
- it writes one raw JSON capture at `--raw-out`, using file mode `0600` on
  platforms that support POSIX permissions;
- generated frontmatter records `source_tool: codex`, `source_adapter:
  codex_app_server_thread_read`, `source_id: THREAD_ID`, `privacy: private`,
  and `authority: non_authoritative_context`;
- `source_sha256` is the SHA-256 digest of the exact raw JSON bytes written to
  `--raw-out`;
- terminal output is metadata-only and does not print transcript text;
- reasoning items are omitted from rendered Markdown by default and recorded as
  warnings; private raw JSON retains the original app-server response for local
  audit;
- `fileChange` and `webSearch` items are rendered as metadata-only sections;
- the manifest records `codex_trust_state_unverified` because this adapter does
  not perform executable signature, notarization, or quarantine diagnostics;
- bounded Codex app-server stderr diagnostics are relayed on stderr and recorded
  with manifest warning `codex_app_server_stderr_diagnostics`;
- sensitivity scanning is heuristic and does not certify that output is safe to
  publish.

If macOS, an endpoint-security tool, or another platform trust mechanism reports
that the configured Codex executable is blocked, quarantined, replaced, or
otherwise suspicious, stop exporting and investigate that executable before
treating the output as reliable. The trust warning is deliberately retained in
the manifest until a separate trust-diagnostics workflow can replace it with a
more specific signal.

### Options

- `--thread-id ID` — Codex thread id to export. Defaults to `CODEX_THREAD_ID`
  when the environment variable is set, using the same resolver as
  `current-codex-thread-id`.
- `--out EXPORT.md` — required Markdown export output path.
- `--raw-out RAW.json` — required private raw JSON capture output path. This
  must be an absolute path outside the current Git worktree; LRH rejects
  repository-local raw captures so `git add -A` cannot accidentally publish the
  complete app-server response.
- `--codex PATH` — Codex executable path. Defaults to `CODEX`, then `codex`.
- `--force` — overwrite existing output files. This never allows `--out` and
  `--raw-out` to be the same file.
- `--timeout-seconds N` — timeout for each app-server response.
- `--no-scan-sensitive` — skip the local heuristic sensitivity scanner and mark
  transcript frontmatter as `sensitivity: unscanned`.

### Exit behavior

The command returns nonzero for missing thread ids, invalid timeouts, output
collisions, existing outputs when `--force` is not supplied, app-server startup
failures, malformed app-server responses, app-server JSON-RPC errors, timeouts,
repository-local raw capture paths, and output write failures.

On success it prints a concise deterministic summary with the Markdown output
path, raw capture path, privacy, sensitivity status, warning count, turn count,
message count, item-type counts, and raw source hash. Potential sensitive
findings are also reported as warnings on stderr.

## `lrh conversation archive-codex-thread`

```bash
lrh conversation archive-codex-thread --thread-id THREAD_ID
lrh conversation archive-codex-thread --thread-id THREAD_ID --scratch
```

Exports a Codex thread through the same app-server adapter as
`export-codex-thread`, but chooses the output paths automatically and writes an
`attempt.json` marker for every attempt. This is the durable default used by
`/lrh-codex-export`.

The archive root resolves in this order:

1. `--archive-root`;
2. `LRH_SESSION_ARCHIVE_ROOT`;
3. `~/.local/share/lrh/session-archive`.

Routine exports are written under
`<archive-root>/codex/exports/YYYY/MM/lrh-codex-export-<timestamp>-<thread>/`.
The archive directory is created with restrictive permissions where supported.
LRH rejects archive roots that resolve inside the current Git worktree.
`attempt.json` is written before app-server access starts, then updated with
success or failure outcome, output paths, source hash, and validation status.

Use `--scratch` only for explicitly ephemeral dogfood or debugging captures.
Scratch output is reported with `Ephemeral: yes` and is not the durable archive
default.

### Options

- `--thread-id ID` — Codex thread id to export. Defaults to `CODEX_THREAD_ID`
  when the environment variable is set, using the same resolver as
  `current-codex-thread-id`.
- `--archive-root ROOT` — session archive root override.
- `--scratch` — write to an explicit ephemeral scratch directory instead of the
  durable archive.
- `--scratch-root ROOT` — scratch parent directory; requires `--scratch`.
- `--codex PATH` — Codex executable path. Defaults to `CODEX`, then `codex`.
- `--timeout-seconds N` — timeout for each app-server response.
- `--no-scan-sensitive` — skip the local heuristic sensitivity scanner.

### Exit behavior

The command returns nonzero for missing thread ids, invalid timeouts, invalid
scratch options, app-server/export failures, write failures, and failed
manifest/source-hash validation. Terminal output is metadata-only and does not
print transcript body text.

## `lrh conversation import-codex-exports`

```bash
lrh conversation import-codex-exports "$HOME/Workspace/Promptspace/CodexExports"
```

Imports existing LRH Codex export directories into the durable archive without
printing transcript bodies. The source may be one export directory or a parent
directory containing immediate child export directories.

Each imported directory is copied under
`<archive-root>/codex/imports/YYYY/MM/`. Valid directories containing both
`export.md` and `raw.json` are inspected with `inspect-export` and classified as
`imported`. Missing files are preserved as explicit `partial` or `empty`
attempts with an `attempt.json` marker, so an empty rescued directory cannot be
mistaken for a successful export. LRH rejects archive roots that resolve inside
the current Git worktree, and copied `export.md`, `raw.json`, and
`attempt.json` files are chmod'd private where supported.

### Options

- `SOURCE` — directory containing one Codex export or child export directories.
- `--archive-root ROOT` — session archive root override.
- `--dry-run` — report classification without copying or writing attempts.
- `--force` — replace an existing imported directory with the same destination
  name.

### Exit behavior

The command returns nonzero for missing/non-directory sources, destination write
failures, and other archive errors. On success it prints one metadata-only line
per source directory plus a status-count summary.

## `lrh conversation inspect-export`

```bash
lrh conversation inspect-export EXPORT.md --format text
lrh conversation inspect-export EXPORT.md --source INPUT.txt --format json
```

Inspects a local Codex Markdown export artifact with
`ConversationExportManifest` frontmatter. The command validates manifest shape,
reports privacy/authority/sensitivity metadata, recomputes transcript body
statistics, and optionally verifies the recorded source SHA-256 against an
explicit `--source` path.

The inspector is metadata-only by default. Text and JSON output report counts,
hashes, statuses, warnings, and diagnostics; they do not print raw transcript
body, snippets, or message text. This keeps terminal scrollback and CI logs from
accidentally echoing private conversation content.

### Options

- `--format text|json` — output format. `text` is concise and human-readable;
  `json` is deterministic and automation-friendly.
- `--source SOURCE` — optional original source file. When supplied, the
  inspector compares its SHA-256 digest to manifest `source_sha256`. When the
  manifest also records `source_byte_count` and the source is now longer, only
  that recorded prefix is hashed (see "Source growth" below).

### Reported Signals

- manifest validity and schema metadata;
- privacy and authority boundaries;
- sensitivity status, sensitivity-scan metadata, and warning count;
- manifest transcript statistics and recomputed artifact body statistics;
- source-hash status: `not_supplied`, `match`, `match_source_grew`, `mismatch`,
  `source_missing`, `source_not_file`, `source_unreadable`, or `not_available`.
  JSON output also carries `expected_byte_count` and `actual_byte_count` (null
  when the manifest recorded no byte count or the source was not read).

### Source growth

A Claude or Antigravity transcript is an append-only log that is usually still
being written when it is exported, so the whole file hashes differently later
even though the exported bytes are intact. When the manifest records
`source_byte_count` N and the source is longer than N, the inspector hashes the
first N bytes:

- equal to `source_sha256`: status `match_source_grew`. The artifact is valid
  and the command exits `0`. Text output adds a line stating how many bytes the
  source has grown since export, and the reported `actual` hash is the hash of
  that recorded prefix (the value that was compared).
- different: `mismatch`, because an earlier byte changed.

A source shorter than N is `mismatch`. A source exactly N bytes long is compared
whole, as before. A manifest with no `source_byte_count` (older exports, and
Codex) is always compared whole, so a grown source is `mismatch` for those.

This assumes the source only ever grows by appending. If a transcript is
rewritten in place (for example by compaction), the prefix hash differs and the
result is still `mismatch`, which is the safe outcome.

Valid file-export artifacts can contain one renderer-added trailing newline in
the Markdown body; the inspector accounts for that when comparing byte and
character counts. Additional body changes are reported as
`transcript_statistics` mismatches.

### Exit behavior

The command returns:

- `0` when the artifact is valid and any supplied source hash matches or
  matches on its recorded prefix (`match_source_grew`);
- `1` when the artifact was read but validation fails, including malformed
  manifests, body-statistic drift, hash mismatches, or missing/non-file supplied
  sources;
- `2` when the export artifact itself cannot be inspected, such as missing,
  non-file, unreadable, or non-UTF-8 input.

## Viewing Codex exports with `lrh serve`

```bash
lrh serve --codex-archive-root private/codex-conversations
```

`lrh serve` can list and view Codex Markdown exports only from explicitly
configured archive roots. Relative `--codex-archive-root` paths are resolved
under `--project-root`, and the option may be supplied more than once.

The archive viewer keeps the same privacy and authority boundary as the
adapter and inspector:

- `/conversations/codex` lists configured roots and export metadata.
- `/conversations/codex/<export_id>` renders one transcript body as escaped
  inert HTML text after explicit selection.
- `/api/conversations/codex` and `/api/conversations/codex/<export_id>` return
  deterministic metadata without transcript body text.
- Missing archive roots are reported as diagnostics instead of becoming
  arbitrary filesystem browsing.
- Exports remain private, non-authoritative context until separately reviewed
  and promoted into LRH project-control artifacts.

## `lrh conversation convert-pdf`

```bash
lrh conversation convert-pdf INPUT.pdf --out OUTPUT.md
```

Converts a local ChatGPT PDF conversation export into a UTF-8 Markdown
transcript. The command targets digitally generated ChatGPT/browser PDFs with an
extractable text layer. It does **not** perform OCR and does not support scanned
PDFs.

The command is local and private-by-default:

- it writes one Markdown file at `--out`;
- it does not import the transcript into a ledger, database, project control
  directory, or private state store;
- generated frontmatter defaults to `privacy: private` and
  `authority: non_authoritative_context`;
- sensitivity scanning is heuristic and does not certify that output is safe to
  publish.

### Options

- `--out OUTPUT.md` — required Markdown transcript output path.
- `--force` — overwrite an existing output file.
- `--no-frontmatter` — write only the extracted transcript text and omit
  privacy, authority, sensitivity, and other transcript metadata.
- `--no-scan-sensitive` — skip the local heuristic sensitivity scanner and mark
  transcript frontmatter as `sensitivity: unscanned` when frontmatter is written.

### Exit behavior

The command returns nonzero for missing inputs, encrypted or unreadable PDFs,
PDFs without extractable text, converter failures, and existing outputs when
`--force` is not supplied.

On success it prints a concise deterministic summary, including output path,
page count when available, metadata status, and warning count. When frontmatter
is written, the summary includes privacy and sensitivity status. Extraction
warnings and potential sensitivity findings are printed as warnings.

## `lrh conversation export-antigravity-session`

```bash
lrh conversation export-antigravity-session --latest
lrh conversation export-antigravity-session --transcript-path PATH --out OUTPUT.md
lrh conversation export-antigravity-session --conversation-id CONVERSATION_ID
```

Converts a local Google Antigravity session transcript log (JSONL) into a
private, non-authoritative Markdown export artifact: a direct local-file
read, not a live API call, mirroring the same defensive-parsing discipline
as the other conversation adapters — malformed lines are collected as
warnings rather than treated as fatal errors.

The command is local and private-by-default:

- it writes one Markdown file at `--out`, or a durable session-archive path
  when `--out` is omitted;
- generated frontmatter defaults to `privacy: private` and
  `authority: non_authoritative_context`;
- the source SHA-256, export timestamp, adapter version, warning list,
  sensitivity metadata, and transcript statistics are preserved in the
  frontmatter;
- the output file's permissions are restricted to user-only (`0600`) after
  the write completes, on a best-effort basis (a platform or filesystem
  that doesn't support `chmod` does not fail the export);
- passing the transcript itself (or a symlink, hardlink, or path alias of it)
  as `--out` is rejected, even with `--force`;
- sensitivity scanning is heuristic and does not certify that output is safe
  to publish.

### Session discovery

Exactly one of the following is required:

- `--transcript-path PATH` — an explicit path to a session transcript JSONL
  file.
- `--conversation-id CONVERSATION_ID` — discover the transcript at
  `<app-data-dir>/brain/<CONVERSATION_ID>/.system_generated/logs/transcript.jsonl`,
  falling back to `transcript_full.jsonl` in the same directory if the first
  doesn't exist; an error if neither exists.
- `--latest` — discover the most recently modified transcript file
  (`transcript.jsonl` or `transcript_full.jsonl`) under
  `<app-data-dir>/brain/*/.system_generated/logs/`. Ties on modification
  time are broken silently (no ambiguity error) in favor of an arbitrary
  one of the tied files.

### Options

- `--app-data-dir APP_DATA_DIR` — path to Antigravity's application data
  directory (default: `~/.gemini/antigravity`).
- `--out OUTPUT.md` — Markdown export output path (default: durable session
  archive, under `<archive_root>/antigravity/exports/<YYYY>/<MM>/<source-id>.md`,
  where `<YYYY>/<MM>` is the UTC export date and any character in
  `<source-id>` other than a letter, digit, `-`, or `_` becomes `_`).
- `--archive-root PATH` — optional private session archive root override.
  It only takes effect when `--out` is omitted (it is ignored otherwise),
  and the resolved archive root must be outside the current Git worktree.
- `--force` — overwrite an existing output file. This never allows the source
  and output to be the same file.
- `--source-id ID` — optional explicit session identifier to record in
  `source_id` (defaults to the conversation ID segment of the transcript
  path when derivable from its `brain/<id>/...` structure, else a
  12-character SHA-256 prefix of the transcript content).
- `--no-scan-sensitive` — skip the local heuristic sensitivity scanner and
  mark transcript frontmatter as `sensitivity: unscanned`.

### Exit behavior

The command returns nonzero for a missing, non-file, non-UTF-8, or
otherwise unreadable transcript input; a `--conversation-id` that
resolves to no transcript file; a `--latest` discovery where
`<app-data-dir>/brain` does not exist or contains no transcript files (not
for ties, which are resolved silently — see Session discovery above); an
archive root that cannot be resolved, or that resolves inside the current
Git worktree, when `--out` is omitted; an existing output when `--force` is not supplied; a source/output path
collision (even with `--force`), reported as `error: ...` on stderr; and
output write failures.

On success it prints a concise deterministic summary with the output path,
source ID, source SHA-256, privacy, sensitivity status, and warning count.
Potential sensitive findings are also reported as warnings on stderr.

## `lrh conversation current-claude-session-id`

```bash
lrh conversation current-claude-session-id
lrh conversation current-claude-session-id --field transcript-path
lrh conversation current-claude-session-id --format json
```

Reports the current Claude Code session's id, host pointer, and resolved
transcript path without exporting, reading, or printing transcript content.
This is the metadata-only resolver `export-claude-session --current` uses
internally, and the one callers should use to learn the current session's
transcript path instead of re-deriving the glob rule in prose. The
`/lrh-session-id-claude` skill wraps it for agent workflows: it adds the
session's title and branch, resolves other sessions through the desktop
app's `list_sessions`, and is what `/lrh-closeout`, `/lrh-land`, and
`/lrh-implement` use to resolve Claude session pointers.

It reads `CLAUDE_CODE_SESSION_ID` (required) and, if set,
`CLAUDE_CODE_HOST_SESSION_ID` (its `local_` prefix stripped) to derive the
session pointer:

```yaml
session_transcript: claude-app:<host-uuid-stem>
```

`CLAUDE_CODE_SESSION_ID` and `CLAUDE_CODE_HOST_SESSION_ID` are set by the
Claude Code desktop app in every session window observed so far; their
availability under a plain CLI invocation, an IDE integration, or a headless
run has not been verified, and this command fails clearly rather than
guessing when either the session id is unset or the transcript cannot be
found.

The transcript path is resolved the same way `export-claude-session
--session-id` finds it: by globbing `<app-data-dir>/projects/*/<session-id>.jsonl`
(honouring `CLAUDE_CONFIG_DIR`/`--app-data-dir`, with `CLAUDE_CONFIG_DIR`
read from the same isolated environment as the session id when the caller
supplies one). Matches are filtered to actual files, so a directory that
happens to be named `<session-id>.jsonl` is never mistaken for a transcript.
Zero or more than one file match is an error, not a silent guess. An unset
or empty `CLAUDE_CODE_HOST_SESSION_ID` does not fail the command — the
session id and transcript path can still be resolved on their own — it only
leaves `session_transcript` (and the text output's `Session transcript:`
line) reported as `unknown`.

### Options

- `--app-data-dir APP_DATA_DIR` — path to Claude Code's application data
  directory (default: `$CLAUDE_CONFIG_DIR`, or `~/.claude` if unset).
- `--format text|json` — output format. Text is the default.
- `--field all|session-id|session-transcript|transcript-path` — single-field
  text output for scripts and closeout records.

### Exit behavior

The command returns `0` on success and `2` when the session cannot be
resolved: `CLAUDE_CODE_SESSION_ID` unset, empty, or containing whitespace;
an embedded path separator; a transcript glob that matches zero or more
than one file; or an app-data directory naming an unresolvable named-user
home (e.g. `~missing-user/.claude`). It never falls back to
`--latest`-style discovery.

## `lrh conversation export-claude-session`

```bash
lrh conversation export-claude-session --latest
lrh conversation export-claude-session --current
lrh conversation export-claude-session --transcript-path PATH --out OUTPUT.md
lrh conversation export-claude-session --session-id SESSION_ID
```

Converts a local Claude Code session transcript log (JSONL) into a private,
non-authoritative Markdown export artifact, mirroring
`export-antigravity-session`'s design: a direct local-file read, not a live
API call, since Claude Code exposes no documented RPC boundary for reading a
finished session's full history. Claude Code's own documentation describes
its JSONL transcript format as internal and version-dependent, so this
command applies the same defensive-parsing discipline as the Antigravity
adapter: malformed lines are collected as warnings rather than treated as
fatal errors.

The command is local and private-by-default:

- it writes one Markdown file at `--out`, or a durable session-archive path
  when `--out` is omitted;
- generated frontmatter defaults to `privacy: private` and
  `authority: non_authoritative_context`;
- the source SHA-256, export timestamp, adapter version, warning list,
  sensitivity metadata, and transcript statistics are preserved in the
  frontmatter;
- the output file is created with user-only (`0600`) permissions from the
  first write, not chmod-ed afterward;
- passing the transcript itself as `--out` is rejected, even with `--force`;
- sensitivity scanning is heuristic and does not certify that output is safe
  to publish.

### Session discovery

Exactly one of the following is required:

- `--transcript-path PATH` — an explicit path to a session transcript JSONL
  file.
- `--session-id SESSION_ID` — discover the transcript by globbing
  `<app-data-dir>/projects/*/<SESSION_ID>.jsonl`. More than one match is an
  error requiring `--transcript-path` to disambiguate, not a silent
  first-match pick; the session id itself must not contain a path separator
  or glob metacharacter (both are rejected/escaped before matching).
- `--current` — export the current Claude Code session, resolved the same
  way `current-claude-session-id` resolves it (from `CLAUDE_CODE_SESSION_ID`).
  Unlike `--latest`, this never falls back to any other discovery mode: if
  the current session cannot be resolved, the command fails with the same
  clear error `current-claude-session-id` would report, rather than
  exporting a different session.
- `--latest` — discover the most recently modified transcript file under
  `<app-data-dir>/projects/<current-project>/*.jsonl`, scoped by default to
  the invoking working directory's own Claude project (see
  `--all-projects`). The working directory used for scoping is the shell's
  logical `$PWD` when it names the same directory as the physical working
  directory, else the OS-resolved physical path — this matters for a
  symlinked checkout (for example, macOS's `/tmp`), where Claude Code's own
  project-bucket naming preserves the literal, unresolved path. Ties (equal
  modification times) are resolved silently, by whichever match `sort()`
  happens to order first — not documented further.

### Options

- `--app-data-dir APP_DATA_DIR` — path to Claude Code's application data
  directory (default: `$CLAUDE_CONFIG_DIR`, or `~/.claude` if unset).
- `--all-projects` — with `--latest`, search
  `<app-data-dir>/projects/*/*.jsonl` across every Claude project instead of
  scoping to the invoking working directory's own project. Restores the
  whole-projects behaviour `--latest` had before project scoping. Rejected
  (exit `2`) when passed without `--latest`, since it has no effect there.
- `--out OUTPUT.md` — Markdown export output path (default: durable session
  archive, under `<archive_root>/claude/exports/<YYYY>/<MM>/<session-id>.md`).
- `--archive-root PATH` — optional private session archive root override.
- `--force` — overwrite an existing output file. This never allows the
  source transcript and output to be the same file.
- `--source-id ID` — optional explicit session identifier to record in
  `source_id` (defaults to the transcript filename stem).
- `--no-scan-sensitive` — skip the local heuristic sensitivity scanner and
  mark transcript frontmatter as `sensitivity: unscanned`.
- `--include-system-attachments` — include internal system-context
  attachment records (`deferred_tools_delta`, `agent_listing_delta`,
  `mcp_instructions_delta`, `skill_listing`) in the export; skipped by
  default since they are not part of the visible conversation.
- `--include-subagents` — inline full subagent transcripts (from sibling
  `<session-id>/subagents/agent-*.jsonl` files) instead of only referencing
  them by id and description.

### Exit behavior

The command returns nonzero for missing, non-file, or non-UTF-8 transcript
inputs; an invalid or ambiguous `--session-id`; a `--current` session that
cannot be resolved (never falls back to `--latest`); existing outputs when
`--force` is not supplied; source/output path collisions (even with
`--force`); and output write failures.

On success it prints a concise deterministic summary: the output path, a
`Source transcript:` line with the resolved transcript path (so callers can
read it instead of re-deriving the discovery rule themselves), source ID,
source SHA-256, privacy, sensitivity status, and warning count. Potential
sensitive findings are also reported as warnings on stderr.
