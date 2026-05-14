# LRH package internals

The package keeps reusable harness code under `src/lrh/` and keeps the
repository's own human-authored control-plane documents under `project/`.

## Shared core state API

`lrh.core_state` is the small read-only state interpretation surface for CLI and
assist consumers that need a common view of project state. It composes the
existing control loader, validator, and planning-tree index into typed summary
objects for:

- project identity and current focus
- validation/readiness diagnostics
- workstreams and work items with parent/child planning relationships
- active leaf work items
- evidence references
- prompt-rendering inputs

The API does not execute work, mutate repositories, create branches, dispatch
agents, or create pull requests. Future `validate`, `snapshot`, `request`,
`serve`, and `run --dry-run` work should prefer this read/interpretation layer
when they need shared project-state inference rather than re-deriving it from raw
frontmatter dictionaries.
