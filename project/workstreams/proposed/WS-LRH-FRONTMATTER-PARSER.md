---
id: WS-LRH-FRONTMATTER-PARSER
kind: planning_node
title: LRH Frontmatter Parser Consolidation and Content Safety
status: proposed
stage: designed
origin: design_review
summary: Consolidate LRH's two hand-rolled frontmatter YAML parsers onto PyYAML, migrate unsafe existing content, and add a lint guard to prevent recurrence, per PROP-LRH-FRONTMATTER-PARSER.
related_focus: []
related_roadmap: []
related_design:
  - project/design/proposals/proposed/lrh-frontmatter-parser/00_proposal.md
work_items:
  - WI-FRONTMATTER-PARSER-CONSOLIDATION
  - WI-FRONTMATTER-MIGRATION-LINT-GUARD
exit_criteria:
  - src/lrh/control/parser.py and src/lrh/control/validator.py share a single PyYAML-based frontmatter parser; lrh validate and lrh work-items validate agree on well-formed frontmatter
  - The 3 identified datetime consumers (prompt_workflow_records.py, prompt_workflow_slug.py, prompt_workflow_search.py) handle datetime/date values explicitly, with tests
  - Every file with a colon-collapse list item or syntax-error scalar (27 at the original 2026-08 audit, 30 at re-verification before filing the implementation work items -- count drifts as content lands, re-locate at implementation time) is fixed; lrh validate and the real-project-tree loader test pass with 0 errors
  - lrh project doctor --fix-frontmatter migration tool exists, dry-run by default, and has been run (dry-run) and manually reviewed against LRH's own project/ tree before any --apply
  - lrh validate includes a lexical lint guard for the four confirmed unsafe-plain-scalar patterns (colon-collapse, reserved-indicator start, mid-scalar comment truncation, implicit non-string typing), and lrh project doctor --fix-frontmatter shares the same detector so migration and lint can never disagree
  - Frontmatter-authoring skills (lrh-work-item, lrh-workstream, lrh-proposal, lrh-closeout, lrh-execute) updated with the "always quote free text" guidance
  - WI-VALIDATOR-YAML-PARSER and WI-PARSER-HARDENING are closed as superseded
---

## Purpose

This workstream groups the design, implementation, and validation of
PROP-LRH-FRONTMATTER-PARSER: consolidating LRH's two independently
hand-rolled frontmatter parsers onto a single PyYAML-based parser, safely
migrating existing content that violates YAML's plain-scalar grammar, and
adding a permanent lint guard plus authoring guidance so the class of bug
that motivated this work cannot silently recur.

## Scope

- Replace `src/lrh/control/parser.py`'s `_parse_frontmatter_mapping` and
  `src/lrh/control/validator.py`'s `_parse_simple_yaml` with one shared
  `yaml.safe_load`-based parser.
- Patch the 3 identified downstream consumers of raw `created_at` values
  for explicit `datetime`/`date` handling.
- Fix the files already found by manual audit to be incompatible with real
  YAML (colon-collapse list items, hard syntax errors on backtick/multi-colon
  scalars; count drifts as new content lands, re-locate at implementation
  time rather than relying on a cached count).
- Build and dry-run (then, after manual review, apply) a reusable content
  migration tool exposed via `lrh project doctor --fix-frontmatter`.
- Add a raw-text lexical lint guard to `lrh validate` and update
  frontmatter-authoring skill guidance.
- Close `WI-VALIDATOR-YAML-PARSER` and `WI-PARSER-HARDENING` as superseded
  by `PROP-LRH-FRONTMATTER-PARSER`.

## Prior Art Check

### Duplication search
- In-repo: Related — `project/work_items/abandoned/WI-VALIDATOR-YAML-PARSER.md`
  proposed replacing `src/lrh/control/validator.py`'s `_parse_simple_yaml` with a
  production-grade parser, scoped only to `src/lrh/control/validator.py` and without
  awareness of the content-compatibility findings this workstream's
  governing proposal documents.
- Sibling repos: None identified — not individually checked for local
  parser forks; this workstream assumes downstream repos (LCATS,
  Taurcode, Taurworks, prosoc, Velumin, Replication Vector) inherit LRH's
  parser as-is.
- External libraries: See `PROP-LRH-FRONTMATTER-PARSER`'s Prior Art
  Check — PyYAML chosen; ruamel.yaml and strictyaml evaluated and ruled
  out.
- Recommendation: Proceed — this workstream supersedes
  `WI-VALIDATOR-YAML-PARSER` rather than duplicating it.

### Demand search
- Work items: Found — `WI-VALIDATOR-YAML-PARSER` (superseded by this
  workstream's governing proposal; closed in the same PR that files this
  workstream).
- Proposals: None found beyond `PROP-LRH-FRONTMATTER-PARSER` itself.
- Backlog: No matching entries.
- Recommendation: No further action — supersession already actioned.

## Work Items

- **WI-FRONTMATTER-PARSER-CONSOLIDATION** — parser/validator consolidation
  onto `yaml.safe_load`, datetime consumer patches, content fixes for the
  files already found incompatible with real YAML, and the non-string
  list-item schema check. Note: a narrower, independently-landed fix
  (commit `2e1af28d`, PR #574) already patched the specific reported
  crash directly on `control/parser.py`; this work item's broader scope
  (consolidation, `validator.py`, content fixes, datetime handling) is
  unaffected and still required.
- **WI-FRONTMATTER-MIGRATION-LINT-GUARD** — shared unsafe-scalar detector,
  `lrh validate` lint category, `lrh project doctor --fix-frontmatter`
  migration tool, frontmatter-authoring skill guidance updates.
  `depends_on: [WI-FRONTMATTER-PARSER-CONSOLIDATION]`.

## Exit Criteria

See frontmatter `exit_criteria:`.

## Non-Goals

- Does not run the migration tool against any repo other than LRH itself.
- Does not adopt ruamel.yaml or strictyaml.
- Does not attempt to enumerate every possible YAML landmine in the lint
  guard beyond the four confirmed classes.

## Relationship to Design

- Design proposal: `project/design/proposals/proposed/lrh-frontmatter-parser/00_proposal.md`
- Superseded work item: `project/work_items/abandoned/WI-VALIDATOR-YAML-PARSER.md`

## Open Questions

- Should the migration tool's allow-list fallback mode be built now or
  deferred until a downstream repo needs it? Deferred to work item
  scoping.
