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

The API validates before strict typed loading by default. Validation-reportable
structural errors therefore return a `ValidationSummary` instead of raising from
strict loader indexes. Callers that have already validated can pass an existing
validation report, and specialized callers can opt out of validation when they
intentionally want loader-only interpretation.

The returned object exposes immutable tuples and read-only mapping views for its
shared summaries. It does not expose the mutable loader or planning-tree backing
objects directly.

The API does not execute work, mutate repositories, create branches, dispatch
agents, or create pull requests. `lrh serve` uses this read/interpretation layer
for project summaries, the read-only `/meta` operational swimlane dashboard, and
registered-project operational detail pages at `/project/<project_id>`, plus
design/workstream traceability drill-down pages at
`/project/<project_id>/designs/<design_id>` and
`/project/<project_id>/workstreams/<workstream_id>`;
work-item readiness/detail pages at
`/project/<project_id>/work-items/<work_item_id>` and prompt preview workbench
pages at `/project/<project_id>/work-items/<work_item_id>/prompt`;
future `validate`, `snapshot`, `request`, `serve`, and `run --dry-run` work should
prefer the same layer when they need shared project-state inference rather than
re-deriving it from raw frontmatter dictionaries.
