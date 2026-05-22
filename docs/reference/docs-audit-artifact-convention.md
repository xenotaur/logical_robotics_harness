# Docs audit artifact convention (v1)

This reference defines a lightweight, Markdown-first convention for LRH documentation audit artifacts.

## Purpose

A docs audit is a reviewable intermediate artifact between documentation discovery and documentation reorganization.

In the intended two-stage workflow:

1. `lrh request audit_docs` should produce a prompt that asks an implementation agent to inspect the repository and write a docs audit.
2. `lrh request organize_docs` should produce a prompt that consumes that audit and scopes one documentation organization PR.

This document defines the artifact contract only. It does **not** implement either request command.

## Relationship to Diátaxis

The audit should classify current and target documentation using Diátaxis reader-need categories:

- tutorials
- how-to guides
- reference
- explanations

Diátaxis should be treated as a reader-need model, not just a folder recipe. The audit may recommend structure changes, but should explain the reader need each recommendation serves.

## Relationship to LRH project state

A docs audit does not replace authoritative project-control artifacts.

- `project/` remains authoritative project-control-plane state.
- `docs/` is the human-facing learning, task, reference, and explanation layer.
- docs audits help plan documentation changes, but do not supersede authoritative project artifacts.

## Recommended artifact path

Recommended path pattern:

```text
<control-root>/audits/YYYY-MM-DD-docs-audit.md
```

This allows audited repositories to keep audits near other control-plane artifacts while remaining portable to nonstandard repository layouts.

## Minimal frontmatter (version 1)

Use lightweight YAML frontmatter at the top of the Markdown file:

```yaml
---
id: AUDIT-DOCS-YYYY-MM-DD
audit_type: docs
schema_version: 1
status: proposed
repo_root: .
project_root: .
docs_root: docs
control_root: project
package_roots: []
framework: diataxis
recommended_next_prompt: organize_docs
recommended_phase: scaffold
---
```

Field intent:

- `repo_root`: repository root relative to the audit location or execution context.
- `project_root`: product/project root when it differs from repository root.
- `docs_root`: primary human-docs root.
- `control_root`: control-plane root (often `project` under `project_root`).
- `package_roots`: one or more package roots in repositories with nonstandard or multiple package locations.

These path fields are intentionally explicit so audits can describe layouts where repository root, project root, docs root, control root, and package roots differ.

## Required headings (version 1)

A version-1 docs audit should include these headings:

```markdown
# Documentation audit

## Summary

## Scope and roots inspected

## Current documentation inventory

## Current project and package layout

## Diátaxis classification

## Navigation findings

## Accuracy findings

## Stale or ambiguous links

## Project-control-plane vs human-docs boundary

## Recommended target documentation structure

## Recommended phased PRs

## Proposed first PR scope

## Risks and cautions

## Validation commands for follow-up PRs
```

Small subheadings are allowed, but these top-level sections should remain explicit so future prompts can reliably consume the artifact.

## Future validation note

Future LRH tooling may validate docs-audit frontmatter fields and required headings.

Validator implementation is intentionally out of scope for this convention PR.
