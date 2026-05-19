# Import ChatGPT PDF Conversations (`lrh conversation convert-pdf`)

This guide explains how to convert a ChatGPT web conversation PDF into a local Markdown transcript so you can review and selectively promote useful content into durable LRH artifacts.

## Why this feature exists

Conversation material is often useful context for follow-up work, evidence notes, and draft artifacts. `lrh conversation convert-pdf` provides a private-by-default, local conversion step so users can preserve context before manual review and promotion.

## Supported input

The converter currently supports:

- Digitally generated ChatGPT/browser PDFs with an extractable text layer.

Not supported yet:

- Scanned PDFs.
- Image-only PDFs.
- OCR.
- Perfect conversation-turn reconstruction.
- Automatic public publishing.

## Save a ChatGPT conversation as PDF

1. Open the conversation in the ChatGPT web UI.
2. Use your browser print flow (`Print` / `Save as PDF`).
3. Save the PDF locally with a clear name, for example `ChatGPT - Example.pdf`.

## Convert the PDF to Markdown

```bash
lrh conversation convert-pdf "ChatGPT - Example.pdf" --out chatgpt-example.md
```

The command is local: it does not call external services during conversion.

## Output metadata and meaning

When frontmatter is enabled (default), LRH adds transcript metadata including:

- `privacy`
- `sensitivity`
- `authority`
- source file hash
- page count
- extraction warnings

Example synthetic frontmatter snippet:

```yaml
privacy: private
sensitivity: none_detected
authority: non_authoritative_context
source_adapter: chatgpt_pdf
```

### `privacy: private`

`privacy: private` means the generated transcript should be treated as non-public by default and reviewed manually before any commit or publication workflow.

### Sensitivity values

- `none_detected`: no heuristic match was found.
- `potential`: one or more heuristic matches were found and require human review.
- `unscanned`: scanning was skipped (for example `--no-scan-sensitive`).

Sensitivity scanning is heuristic and does **not** certify that content is safe.

## Dogfood classification model

For local dogfooding, use this classification model:

- `public-reviewed`: manually reviewed and safe to commit.
- `private-local`: useful local transcript that should not be committed.
- `transient-local`: temporary extraction output for experiments.
- `synthetic-fixtures`: fake/sanitized examples suitable for tests and docs.

## Safety guidance

- Raw private transcripts should **not** be committed by default.
- Public release requires explicit human review.
- Sensitivity findings should block public export/promotion by default in future storage workflows.
- No external service is contacted during conversion.
- The command does not redact content.

Until redaction and storage import workflows are finalized, treat conversion as a local capture/review step and manually review transcripts before committing or publishing.
