# LRH conversations

This package contains small, reusable helpers for conversation import and
analysis workflows.

## Sensitivity scanner

`lrh.conversations.sensitivity` provides a local deterministic heuristic scanner
for flagging potential sensitive content in conversation transcripts. It is a
safety rail only: it does not certify that content is safe to publish, does not
redact source text, and public export should still require human review.

## ChatGPT PDF import

`lrh.conversations.pdf_import` provides the first local, dependency-free
ChatGPT browser-PDF transcript conversion helper and backs the
`lrh conversation convert-pdf INPUT.pdf --out OUTPUT.md` CLI command. It
preflights local PDF files,
rejects trailer-declared encryption, extracts simple text-layer `Tj` and `TJ`
operands with PDF string-escape handling, writes private-by-default Markdown
frontmatter, and runs the local sensitivity scanner unless disabled. The
extractor is not OCR and reports warnings when page count or turn boundaries are
uncertain.

## Codex file export

`lrh.conversations.codex_file_export` converts an explicit local Codex
transcript/source text file into a private, non-authoritative Markdown artifact
with `ConversationExportManifest` frontmatter. It backs the
`lrh conversation convert-codex-file INPUT --out OUTPUT.md` CLI command. The
adapter is intentionally file-based: callers provide the source and output
paths, output is rejected if it collides with the source even under `--force`,
and no undocumented Codex app storage internals are inspected.
