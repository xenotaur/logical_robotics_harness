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
ChatGPT browser-PDF transcript conversion helper. It preflights local PDF files,
rejects trailer-declared encryption, extracts simple text-layer `Tj` and `TJ`
operands with PDF string-escape handling, writes private-by-default Markdown
frontmatter, and runs the local sensitivity scanner unless disabled. The
extractor is not OCR and reports warnings when page count or turn boundaries are
uncertain.
