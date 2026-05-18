# LRH conversations

This package contains small, reusable helpers for conversation import and
analysis workflows.

## Sensitivity scanner

`lrh.conversations.sensitivity` provides a local deterministic heuristic scanner
for flagging potential sensitive content in conversation transcripts. It is a
safety rail only: it does not certify that content is safe to publish, does not
redact source text, and public export should still require human review.

## ChatGPT PDF import

`lrh.conversations.pdf_import` converts text-layer ChatGPT PDFs into
private-by-default Markdown transcripts with deterministic cleanup, FlateDecode
stream support, and optional sensitivity scanning metadata.
