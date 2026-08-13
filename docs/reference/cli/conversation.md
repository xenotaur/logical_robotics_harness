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

Raw Codex exports remain private, non-authoritative context. They are not
imported into the `project/` control plane and do not become evidence,
decisions, work items, or status until a separate reviewed promotion step
creates those artifacts. Sensitivity scanning is heuristic and does not certify
that an export is safe to publish.

This contract is used by the file-based Codex adapter, inspector, and
safe-default `lrh serve` archive viewer below. It does not implement any change
to execution-record `session_transcript` pointer grammar.

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
  when the environment variable is set.
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
  inspector compares its SHA-256 digest to manifest `source_sha256`.

### Reported Signals

- manifest validity and schema metadata;
- privacy and authority boundaries;
- sensitivity status, sensitivity-scan metadata, and warning count;
- manifest transcript statistics and recomputed artifact body statistics;
- source-hash status: `not_supplied`, `match`, `mismatch`, `source_missing`,
  `source_not_file`, `source_unreadable`, or `not_available`.

Valid file-export artifacts can contain one renderer-added trailing newline in
the Markdown body; the inspector accounts for that when comparing byte and
character counts. Additional body changes are reported as
`transcript_statistics` mismatches.

### Exit behavior

The command returns:

- `0` when the artifact is valid and any supplied source hash matches;
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
