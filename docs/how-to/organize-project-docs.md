# Organize project docs request prompts

## Purpose

Use `lrh request organize_docs` to generate a scoped documentation-organization prompt. The command creates a prompt artifact for a downstream assistant; it does not reorganize docs directly.

## Prerequisites

- Have a documentation audit artifact available (recommended for reliable scope and sequencing).
- Know your project roots (`--project-root`, `--docs-root`, `--control-root`) for standard or nested layouts.

## Command

Nested LCATS-style layout with an audit artifact:

```bash
lrh request organize_docs \
  --repo-root . \
  --project-root ./lcats \
  --docs-root ./lcats/docs \
  --control-root ./lcats/project \
  --audit-file ./lcats/project/audits/YYYY-MM-DD-docs-audit.md \
  --out organize-docs.prompt.md
```

## Expected output

- A Markdown implementation prompt scoped to docs-organization work.
- If `--audit-file` is provided, the audit content is injected into the prompt context.
- No documentation files are modified by this command itself.

## Related guides

- [Audit project docs request prompts](audit-project-docs.md)
- [CLI reference: `lrh request`](../reference/cli/request.md)
