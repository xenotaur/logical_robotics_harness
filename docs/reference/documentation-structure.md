# Documentation Structure

LRH human-facing documentation uses a lightweight, GitHub-rendered, Diátaxis-inspired structure. This page is the placement guide for future documentation changes.

## Top-level structure

```text
docs/
  README.md
  tutorials/
  how-to/
  reference/
  explanations/
  conversations/
```

The sections are destinations for future content migration. This scaffold intentionally does not move or rewrite all existing documentation.

## Authority boundary

`docs/` is not the authoritative LRH project control plane. Authoritative project state remains in [`../../project/`](../../project/), including active work items, evidence, status, design proposals, and durable decisions.

Human-facing docs should:

- teach users and maintainers how to use LRH;
- explain accepted concepts and rationale;
- document stable commands, schemas, and file formats;
- link to `project/` when state, evidence, or design authority matters.

Human-facing docs should not duplicate the project control plane or create a second source of truth for active LRH state.

## Placement rules

### Tutorials

Use [`../tutorials/`](../tutorials/) for complete guided learning paths. Choose tutorials when the reader needs to learn by following a sequence from start to finish.

Do not use tutorials for command catalogs, schema definitions, or narrow task recipes.

### How-to guides

Use [`../how-to/`](../how-to/) for task-specific operational instructions. Choose how-to guides when the reader already has a goal and needs practical steps to complete it.

Do not use how-to guides for exhaustive reference facts or rationale-only discussions.

### Reference

Use [`./`](./) for exact, stable behavior. Put command details under [`cli/`](cli/) and file-format or schema details under [`schemas/`](schemas/).

Do not use reference pages for broad narratives, project plans, or content that is still unsettled design work.

### Explanations

Use [`../explanations/`](../explanations/) for concepts, rationale, and design background. Explanations may link to authoritative decisions or proposals in `project/`, but should not replace them.

Do not use explanations for step-by-step procedures or exact schema contracts.

### Conversations

Use [`../conversations/`](../conversations/) for user-facing workflows involving conversation capture, import, review, and promotion into durable LRH artifacts.

Do not put raw conversation archives here unless they are curated into stable user-facing guidance.

## Migration guidance

Follow-up migration PRs should be small and low-noise:

1. Move or split one coherent document at a time.
2. Preserve relative links or add minimal compatibility links when needed.
3. Avoid large rewrites while moving content.
4. Keep README navigation current for each affected folder.
5. Link to `project/` artifacts instead of copying active project-control state.

Existing documents such as [`../release.md`](../release.md) and [`../project-setup/`](../project-setup/) remain in place until focused follow-up PRs decide whether and how to migrate them.
