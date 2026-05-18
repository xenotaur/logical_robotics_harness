---
id: PROP-LRH-CONVERSATIONS-CHATGPT-PDF-IMPORT
type: design_proposal
title: ChatGPT PDF Conversation Conversion Adapter
status: proposed
created_on: 2026-05-18
updated_on: 2026-05-18
implementation_status: not_started
parent: PROP-LRH-CONVERSATIONS-STORAGE-INTEROP
related_design:
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
  - project/design/proposals/proposed/lrh-conversations-storage-interop/README.md
supersedes: []
superseded_by: null
---

# ChatGPT PDF Conversation Conversion Adapter

## Summary

LRH should eventually provide a focused, local adapter that converts ChatGPT
browser **Save as PDF** conversation exports into LRH-controlled Markdown
transcripts. The adapter is an early manual capture path for the broader LRH
Conversations, Storage, and External Agent Interop proposal: it helps users
bring external ChatGPT conversation context into reviewable project-local files
without treating those files as authoritative project state.

This document is design-only. It records the intended command contract,
transcript metadata, privacy and sensitivity defaults, and implementation
boundaries. It does not implement the converter, sensitivity scanner, CLI
command, storage layer, OCR, redaction, model calls, conversation ledger, or
public export workflow.

## Purpose

The first practical flow is:

```text
ChatGPT online conversation
  -> browser Save as PDF
  -> lrh conversation convert-pdf
  -> Markdown transcript
```

The purpose of the adapter is to convert ChatGPT conversation PDFs into
Markdown transcripts suitable for LRH conversation dogfooding. The output is a
transcript artifact that can preserve context and provenance for later human
review. It is **not** authoritative LRH project state, does not mark work
complete, and does not promote any content into design, evidence, status,
execution, or work-item records.

## Supported input

The first adapter should support only digitally generated ChatGPT conversation
PDFs that include an extractable text layer. It should reject or warn clearly
when the input is outside that narrow scope.

Explicitly out of scope for the first adapter:

- scanned PDFs;
- image-only PDFs;
- OCR-heavy import;
- encrypted PDFs;
- arbitrary PDF-to-perfect-Markdown conversion;
- perfect speaker or turn reconstruction.

The adapter should prefer useful, deterministic transcript capture over an
illusion of perfect reconstruction. If reliable PDF markers for turns or
speakers are unavailable, the first implementation may emit normalized text
with provenance metadata and warnings instead of guessed turn boundaries.

## Core design decisions

1. **Conversion is local and deterministic.** Given the same input PDF,
   adapter version, and options, conversion should produce stable output.
2. **No LLM call is made during conversion.** Transcript conversion must not
   depend on model interpretation or summarization.
3. **No cloud service is contacted during conversion.** The adapter should be
   safe to run on private transcripts without network access.
4. **Output defaults to `privacy: private`.** A transcript produced from a
   ChatGPT PDF should begin as private unless the user explicitly selects a
   different policy.
5. **Output defaults to `authority: non_authoritative_context`.** Converted
   transcripts are context artifacts, not accepted facts or project state.
6. **Sensitivity is tracked separately from privacy.** Private content may or
   may not contain secrets, personal data, credentials, or other sensitive
   material.
7. **Sensitivity detection is conservative flagging, not certification.** A
   clean scan means no obvious findings were detected by the configured local
   scanner; it does not certify that the transcript is safe to publish.
8. **Redaction is separate from detection.** The first scanner may flag likely
   issues, but redaction workflows should be designed and implemented later.
9. **Public export or promotion must be explicit.** Later storage/export code
   should block public export by default when sensitivity is `potential` or
   `confirmed`.
10. **Turn segmentation is optional/later unless reliable markers exist.** The
    adapter should not invent high-confidence speaker structure from weak PDF
    layout clues.

## Proposed command contract

Future command:

```bash
lrh conversation convert-pdf INPUT.pdf --out OUTPUT.md
```

Initial defaults:

```text
privacy: private
authority: non_authoritative_context
scan_sensitive: true
```

Suggested later options:

```bash
--source chatgpt-pdf
--privacy private|shared_private|public|secret
--durability transient|session|durable|versioned|sealed
--scan-sensitive / --no-scan-sensitive
--include-page-breaks
--no-frontmatter
--force
--debug-extraction-dir DIR
```

Expected command behavior:

- read one local PDF file;
- keep privacy and durability as separate policy axes;
- preflight that the file is a supported, extractable-text PDF;
- write one Markdown transcript to `--out`;
- refuse to overwrite an existing output path unless `--force` is supplied;
- include frontmatter unless `--no-frontmatter` is supplied;
- scan for sensitive-looking content by default;
- perform all work locally without model calls or cloud services;
- report warnings for lossy extraction, unsupported features, removed
  boilerplate, uncertain turn boundaries, or scanner limitations.

## Conversion pipeline

The intended pipeline is:

```text
PDF input
  -> preflight
  -> extract text
  -> normalize pages
  -> remove boilerplate
  -> repair paragraphs/code-ish blocks
  -> run sensitivity scan
  -> emit Markdown with frontmatter
```

Pipeline notes:

- **Preflight** should check that the input exists, is a PDF, is not encrypted,
  and appears to have an extractable text layer.
- **Extract text** should use a deterministic local PDF text extractor selected
  during implementation.
- **Normalize pages** should preserve enough page context for provenance and
  optional page-break emission.
- **Remove boilerplate** should target repeated browser/PDF generation noise
  when confidently recognized, including repeated PDFCrowd or print footers,
  repeated URLs, timestamps, and page counters.
- **Repair paragraphs/code-ish blocks** should improve readability without
  pretending to perfectly reconstruct the original HTML chat. The first pass
  may handle common hard-wrapped paragraphs, fenced-code-like regions, and
  list indentation conservatively.
- **Run sensitivity scan** should use the local scanner described below unless
  disabled by explicit option.
- **Emit Markdown with frontmatter** should include provenance, privacy,
  authority, extraction, scanner, and warning metadata.

## Markdown output format

The default output should be a Markdown transcript with YAML frontmatter. A
representative frontmatter block is:

```yaml
---
kind: lrh_conversation_transcript
schema_version: 1
source_format: pdf
source_tool: chatgpt
source_adapter: chatgpt_pdf
privacy: private
sensitivity: potential
sensitivity_scan:
  status: scanned
  scanner: lrh_builtin_sensitive_scan
  scanner_version: 1
  finding_count: 2
  categories:
    - email
    - possible_secret
authority: non_authoritative_context
source_file: ChatGPT - LRH Project.pdf
source_file_sha256: "<sha256>"
page_count: 85
extracted_at: "<timestamp>"
adapter_version: 1
warnings: []
---
```

The transcript body should preserve the extracted conversation text in a
readable form. If the adapter cannot reliably split turns, it should say so in
`warnings` and avoid misleading speaker labels.

`sensitivity: none_detected` means the configured scanner found no obvious
sensitivity patterns. It does **not** mean the transcript is certified safe to
publish, safe to commit, or free of confidential material.

## Sensitivity model

Supported `sensitivity` values:

```text
unscanned
none_detected
potential
confirmed
```

Semantics:

- `unscanned`: no sensitivity scan was run, either because the user disabled it
  or the scan failed before producing a result.
- `none_detected`: the local scanner found no obvious sensitive patterns.
- `potential`: the local scanner found possible sensitive content such as an
  email address, token-like string, path containing a username, private URL, or
  other configured category.
- `confirmed`: a human or later workflow has explicitly marked the transcript
  as containing sensitive content.

The first implementation should use a conservative local scanner and should not
call external services. Scanner findings are triage signals for review and
policy gates, not proof that all sensitive material has or has not been found.

## Architecture sketch

Eventual code locations:

```text
src/lrh/conversations/
  __init__.py
  pdf_import.py
  sensitivity.py

tests/conversations_tests/
  pdf_import_test.py
  sensitivity_test.py
```

The proposed module boundary keeps conversation-specific import and sensitivity
logic separate from the control-plane document loader. It also leaves room for
future storage and promotion code without making the PDF adapter depend on a
conversation ledger.

## Dogfood dataset guidance

The converter enables a dogfood corpus of Markdown transcripts for LRH
conversation work. Raw private transcripts should not be committed to the
public repository. A future local or private corpus layout could use categories
such as:

```text
public-reviewed/
private-local/
transient-local/
synthetic-fixtures/
```

Guidance:

- `public-reviewed/` is only for transcripts intentionally reviewed and cleared
  for public use.
- `private-local/` is for durable local or private workspace transcripts that
  must not be committed to public repositories.
- `transient-local/` is for scratch transcripts that may be deleted after a
  session or experiment.
- `synthetic-fixtures/` is for fabricated or sanitized fixtures suitable for
  tests and documentation.

Tests for the adapter should use synthetic fixtures or tiny generated PDFs with
known content, not real private ChatGPT exports.

## Non-goals

This design note and the initial adapter do not implement:

- conversation storage ledger;
- SQLite backend;
- `lrh conversation import` into private state;
- `lrh conversation ask`;
- redaction;
- OCR;
- MCP, GitHub, or GPT Actions integration;
- chat-to-run;
- public export workflow.

## Open follow-up work

- Choose the deterministic local PDF extraction library and fixture strategy.
- Define the exact transcript body conventions after testing real browser PDF
  output patterns.
- Design the local sensitivity scanner categories and warning schema.
- Decide where private-local transcript corpora live outside the public LRH
  repository.
- Add user-facing documentation only after the command exists.
