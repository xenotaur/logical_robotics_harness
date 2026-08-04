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

This contract is used by the file-based Codex adapter below. It does not yet
implement `lrh conversation inspect-export`, `lrh serve` archive viewing, or any
change to execution-record `session_transcript` pointer grammar.

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
