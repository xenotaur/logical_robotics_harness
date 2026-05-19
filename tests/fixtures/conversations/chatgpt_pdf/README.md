# ChatGPT PDF Conversation Fixtures

This fixture directory is for **sanitized/synthetic** conversation-conversion examples only.

## Rules

- Do not commit raw private transcripts from real conversations.
- Do not commit PDFs or Markdown that contain sensitive or identifying data.
- Prefer synthetic fixtures that exercise expected converter output shape.

## Recommended local dogfood classes

- `public-reviewed`: manually reviewed and safe to commit.
- `private-local`: local-only transcript; do not commit.
- `transient-local`: temporary output for experiments; do not commit.
- `synthetic-fixtures`: fake/sanitized fixture data that may be committed.

## Suggested fixture content

- Small `.expected.md` outputs with representative frontmatter fields.
- Minimal warning/sensitivity examples using synthetic text.

Keep fixtures small, deterministic, and human-reviewable.
