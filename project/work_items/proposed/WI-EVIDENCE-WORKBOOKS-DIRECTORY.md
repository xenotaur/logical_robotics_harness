---
resolution: null
blocked_reason: null
blocked: false
id: WI-EVIDENCE-WORKBOOKS-DIRECTORY
title: Create workbooks/ directory and initial loop-iteration evidence script
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design:
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
  - project/design/proposals/proposed/workstream-execution-framework/05_layer5_observability_and_evidence.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - modify_ci_pipeline
acceptance:
  - workbooks/README.md exists and documents purpose, non-enforcement, and promotion path
  - workbooks/loop_iteration_stats.py identifies review/confirm records by work_item=AD_HOC plus rerun_of, not by filename suffix alone, and reports pass counts per PR plus an aggregate summary without asserting an automated clean/dirty verdict
  - workbooks/ is not referenced by scripts/lint, scripts/test, or any .github/workflows/*.yml file
  - WI-EVIDENCE-WORKBOOKS-DIRECTORY appears in project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md's work_items list
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - workbooks/README.md
  - workbooks/loop_iteration_stats.py
  - project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md
---

## Summary

Create a top-level `workbooks/` directory for plain-Python, quasi-one-off
scripts that are not yet promoted to `src/lrh/`, and populate it with a
first script that computes empirical review/CI-response iteration counts
from `project/executions/` records.

## Problem / Context

`WI-BOUNDED-STABILIZATION-LOOP-DESIGN` needs real iteration-limit and
stop-condition numbers (e.g. `max_review_iterations`), not guesses, before
it can move past `proposed`. That data already exists as a byproduct of
running `/lrh-implement` → `/lrh-review-response` → `/lrh-confirm-fixes` →
`/lrh-closeout` by hand — each `/lrh-review-response` round leaves its own
`*_REVIEW.md` execution record and each `/lrh-confirm-fixes` pass leaves a
`*_CONFIRM.md` record, both carrying a `pr:` field — but nothing currently
aggregates it. A prior discussion in this session evaluated three ways to
house the aggregation script (a session-scratchpad throwaway, a new `lrh
evidence` CLI command, and a new mode of `lrh search`) and rejected all
three: the scratchpad isn't rerunnable by future sessions; a new CLI
command is premature relative to the still-`proposed` Layer 2 durable
run-state package that will define the real per-run evidence model
(`project/focus/development_agenda.md:29-31`); and extending `lrh search`
would contradict that command's own documented "exploratory, not
authoritative" contract (`src/lrh/prompt_workflow_search.py:56-59`). A
fourth option — a dedicated top-level `workbooks/` directory, loosely
modeled on LCATS's `lcats/notebooks/`/`lcats/KMo/` precedent
(https://github.com/xenotaur/LCATS/tree/main/lcats) but with an explicit
README convention neither of those directories has — was selected instead.

### Duplication search
- In-repo: No existing `workbooks/` (or similarly named) directory found;
  `datasets/` is the closest existing precedent for a tracked, non-package
  top-level directory with no special packaging/lint/test configuration.
- Sibling repos: See LCATS `lcats/notebooks/` and `lcats/KMo/`
  (https://github.com/xenotaur/LCATS) — the same informal-script-directory
  pattern, undocumented in both cases.
- External libraries: None identified — this is a repository-organization
  convention, not a capability to implement or adopt from a library.
- Recommendation: Proceed

### Demand search
- Work items: None found matching "workbooks" or "evidence directory".
- Proposals: Found: `PROP-WORKSTREAM-LAYER5-OBSERVABILITY-EVIDENCE` —
  "Layer 5 — Observability and Evidence" (does not satisfy this item — see
  Non-Goals; that proposal is deep future infrastructure gated behind
  unimplemented Layers 1-4 and covers typed evidence extracted from
  runtime traces, not retrospective analysis of existing Markdown
  execution records).
- Backlog: No matching entries.
- Recommendation: No action to close/link; proceed, with an explicit
  non-goal distinguishing this item's informal directory from Layer 5b's
  typed `project/evidence/` record system.

## Scope

- Create a top-level `workbooks/` directory for plain-Python, non-package
  scripts that are not yet promoted to `src/lrh/` and are not enforced by
  default lint/test/CI.
- Document the directory's purpose, non-enforcement, and promotion path in
  `workbooks/README.md`.
- Add the first occupant script, computing empirical review/CI-response
  iteration counts from `project/executions/` records, as evidence for
  `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`.

## Required Changes

1. Create `workbooks/` at the repository root.
2. Create `workbooks/README.md` stating: what belongs here (exploratory /
   evidence-gathering scripts, not production logic), that
   `scripts/lint`/`scripts/test`/CI do not cover this directory by
   default, and the promotion path (logic that proves useful moves into
   `src/lrh/` with tests under STYLE.md's normal rules).
3. Create `workbooks/loop_iteration_stats.py` — a plain-Python CLI script
   with no new dependencies that loads `project/executions/` records via
   `lrh.prompt_workflow_records.load_execution_records()` and reports, per
   PR and in aggregate, how many review-response and confirm-fixes passes
   occurred. A record counts as a review-response or confirm-fixes pass
   only if `work_item == "AD_HOC"` **and** it carries a non-empty
   `rerun_of` pointing back to a record for the same PR — matching the
   convention in `references/review-response-workflow.md:38-43` (review
   response and confirm-fixes executions always live under `AD_HOC`, with
   `rerun_of` linking back to the primary). Filename suffix (`_REVIEW.md` /
   `_CONFIRM.md`) alone is not a valid cohort predicate: a primary
   work-item record's own slug can end in "review" or "confirm" and would
   be miscounted (see Risk Notes). The script does not claim to determine
   which pass was the first "clean" one — see Risk Notes for why that
   verdict isn't machine-readable today — it reports pass counts and, for
   each `_CONFIRM.md` pass, the record path plus a best-effort extracted
   verdict line (if the body contains one) labeled as unverified prose,
   not a computed classification.
4. Add `WI-EVIDENCE-WORKBOOKS-DIRECTORY` to
   `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`'s
   `work_items:` list.

## Non-Goals

- Do not name the directory or the script `evidence/` / `lrh evidence` —
  that CLI surface and the `project/evidence/` path are already reserved
  by the proposed `PROP-WORKSTREAM-LAYER5-OBSERVABILITY-EVIDENCE` design
  for typed, schema-validated `EvidenceRecord`s extracted from runtime
  traces; this item's output is an informal retrospective script, not a
  Layer 5b evidence record.
- Do not add `workbooks/` to `scripts/lint`, `scripts/test`, or any
  `.github/workflows/*.yml` default targets — content here is
  intentionally outside the STYLE.md "write and pass tests" / "pass lint
  and formatting" bar until something in it is promoted.
- Do not implement `lrh evidence`, an evidence-record schema, or any other
  part of the Layer 5 observability/evidence proposal.
- Do not add Jupyter notebook tooling (`ipykernel`, `nbconvert`,
  `nbstripout`) — the first occupant is a plain `.py` script; notebooks
  remain a future option only if genuinely visual/exploratory work later
  warrants adopting that toolchain.
- Do not register a `lrh workbooks` subcommand or otherwise wire this
  directory into the `lrh` CLI.
- Do not add a structured `verdict:`/clean-pass frontmatter field to the
  execution-record schema — the current gap (see Risk Notes) is real, but
  fixing the schema is separate future work, not part of this directory's
  first script.

## Acceptance Criteria

- `workbooks/README.md` exists and documents purpose, non-enforcement,
  and promotion path.
- `workbooks/loop_iteration_stats.py` runs against `project/executions/`
  and reports review/confirm round counts per PR plus an aggregate
  summary.
- `workbooks/` is not referenced by `scripts/lint`, `scripts/test`, or any
  `.github/workflows/*.yml` file.
- `WI-EVIDENCE-WORKBOOKS-DIRECTORY` appears in
  `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`'s
  `work_items:` list.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- `python workbooks/loop_iteration_stats.py --format text`

## Risk Notes

- **No machine-readable clean-pass marker exists.** Verified against PR
  #400: three `_CONFIRM.md` records
  (`project/executions/AD_HOC/2026_07_18_04_07_14_..._CONFIRM.md`,
  `..._04_34_27_..._CONFIRM.md`, `..._04_42_32_..._CONFIRM.md`) all carry
  `status: landed`, but their actual verdicts ("not green" / "green" / a
  correction of an earlier mis-ordered "green" claim) exist only as
  unstructured body prose, not a queryable field. The script must not
  assert which round was "the" clean pass — it can only report pass counts
  and surface each pass's prose for a human to read. A future WI could add
  a structured `verdict:` field to `_CONFIRM.md` records; out of scope here
  (see Non-Goals).
- **Filename suffix is not a valid review/confirm cohort predicate.**
  Verified against PR #413:
  `project/executions/WI-SKILLS-NEXT-STEP-CHAIN/2026_07_24_00_08_21_ADDRESS_412_REVIEW.md`
  is the *primary* work-item execution record (its slug happens to end in
  "review" because it addresses PR #412's review feedback), while the
  actual `/lrh-review-response` side-record for PR #413 is
  `project/executions/AD_HOC/2026_07_24_00_31_50_LRH_NEXT_STEP_CHAIN_FOLLOWUP_REVIEW.md`.
  Counting by `_REVIEW.md`/`_CONFIRM.md` suffix alone would have counted
  both — reporting 2 rounds instead of 1. The script must instead cohort by
  `work_item == "AD_HOC"` plus a `rerun_of` back-link, per Required Change
  3.
- The script's iteration counts will undercount true escalation events:
  bot-vs-human thread tagging currently exists only transiently in the
  `/lrh-confirm-fixes` confirm-gate UI
  (`src/lrh/skills/lrh-confirm-fixes/SKILL.md:52-55`) and is not persisted
  into execution-record frontmatter, so "how many threads needed a human
  decision" cannot be recovered retroactively from `project/executions/`
  alone. Treat this as an open question to hand to
  `WI-BOUNDED-STABILIZATION-LOOP-DESIGN` rather than inventing a number.
- An undocumented `workbooks/` directory can accumulate unmaintained
  scripts the same way `lcats/notebooks/` and `lcats/KMo/` did. The
  README's promotion-path language is a mitigation, not a guarantee —
  revisit if the directory grows past a handful of files with nothing
  ever graduating to `src/lrh/`.

## Dependencies / Order

No blocking `depends_on`. This item's output is intended as evidence for
`project/work_items/proposed/WI-BOUNDED-STABILIZATION-LOOP-DESIGN.md`,
which is still `proposed` and currently has no numeric basis for its
`max_review_iterations`/`max_ci_iterations` acceptance criteria — that
item should read this one's script output before those numbers are
finalized, but does not need to be resequenced ahead of this item.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-EXECUTION-FRAMEWORK.md`
- Design (parent): `project/design/proposals/proposed/workstream-execution-framework/00_proposal.md`
- Design (naming-collision context): `project/design/proposals/proposed/workstream-execution-framework/05_layer5_observability_and_evidence.md`
- Related work item: `project/work_items/proposed/WI-BOUNDED-STABILIZATION-LOOP-DESIGN.md`
