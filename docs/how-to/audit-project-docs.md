# Audit project docs request prompts

## Purpose

Use `lrh request audit_docs` to generate a documentation-audit prompt for a downstream assistant. The command writes or prints a Markdown prompt; it does not modify your documentation tree.

## Prerequisites

- Run from a repository root, or pass explicit roots.
- Identify the product root (`--project-root`) when your repo has nested projects.
- Decide where to write the generated prompt with `--out`, or omit `--out` to print to stdout.

## Commands

Standard layout (`docs/`, `project/`, package at repository root):

```bash
lrh request audit_docs \
  --repo-root . \
  --project-root . \
  --docs-root docs \
  --control-root project \
  --out audit-docs.prompt.md
```

Nested LCATS-style layout:

```bash
lrh request audit_docs \
  --repo-root . \
  --project-root ./lcats \
  --docs-root ./lcats/docs \
  --control-root ./lcats/project \
  --package-root ./lcats/lcats \
  --out audit-docs.prompt.md
```

## Expected output

- A Markdown prompt asking a downstream assistant to audit documentation quality and structure.
- Suggested audit artifact path is embedded using `--audit-output` (or its default) so the follow-up organization step can consume a concrete audit file.
- No docs files are changed by this command.

## Related guides

- [Organize project docs from an audit artifact](organize-project-docs.md)
- [CLI reference: `lrh request`](../reference/cli/request.md)
