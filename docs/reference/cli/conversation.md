# `lrh conversation`

Conversation commands convert and inspect local conversation artifacts without
importing them into LRH project state.

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
- `--no-scan-sensitive` — skip the local heuristic sensitivity scanner and mark
  transcript frontmatter as `sensitivity: unscanned`.

### Exit behavior

The command returns nonzero for missing inputs, encrypted or unreadable PDFs,
PDFs without extractable text, converter failures, and existing outputs when
`--force` is not supplied.

On success it prints a concise deterministic summary, including output path,
page count when available, privacy, sensitivity status, and warning count.
Extraction warnings and potential sensitivity findings are printed as warnings.
