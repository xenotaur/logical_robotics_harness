# Semantic Work-Item Lifecycle Audit Request

Use this request after running the deterministic lifecycle audit:

```bash
lrh work-items audit --format md
```

==================================================
OBJECTIVE
==================================================

Review one or more work items conservatively against repository evidence. The deterministic audit output is a starting point only; do not close, abandon, supersede, or split a work item unless concrete repository evidence supports the recommendation.

==================================================
INPUTS TO READ
==================================================

- deterministic audit output from `lrh work-items audit --format md` or `--format json`
- each reviewed work-item file under `project/work_items/`
- related roadmap, focus, design, workstream, status, evidence, and execution-record files referenced by the work item or audit
- relevant source, test, packaging, documentation, and script files needed to evaluate acceptance criteria

==================================================
REVIEW METHOD
==================================================

For each reviewed work item:

1. Identify the declared objective, scope, acceptance criteria, required evidence, dependencies, and lifecycle metadata.
2. Compare each acceptance criterion with current repository state.
3. Distinguish deterministic facts from semantic judgments.
4. Cite concrete repository evidence for every recommendation.
5. Treat missing evidence as a gap, not as implicit completion.
6. Avoid optimistic closure for ambiguous, partially complete, or underspecified items.
7. Prefer follow-up work items for residual acceptance criteria instead of overclaiming completion.

==================================================
CLASSIFICATION OPTIONS
==================================================

Classify each reviewed work item as exactly one of:

- keep proposed
- promote to active
- mark resolved
- mark abandoned
- mark superseded by another item
- split into follow-up work items
- needs human design review

Only recommend exact metadata changes or file moves when evidence is strong. Otherwise, leave the item in its current bucket and state the uncertainty.

==================================================
OUTPUT FORMAT
==================================================

# Semantic Work-Item Audit Report

## Reviewed Items

- `<WORK_ITEM_ID>` — `<classification>`

## Findings by Work Item

### `<WORK_ITEM_ID>`

- Current status/bucket:
- Recommended classification:
- Evidence:
  - `<path>`: `<fact>`
- Acceptance criteria assessment:
  - `<criterion>` — satisfied / not satisfied / unclear, with citation
- Recommended metadata/file changes:
  - none, or exact proposed status/resolution/path updates
- Follow-up work items needed:
  - none, or concise follow-up title/objective
- Uncertainty:
  - explicit unknowns and why they prevent automatic closure

## Conservative Closeout Notes

Summarize which items should remain unchanged and why. Explicitly warn against resolving ambiguous items without additional human review or evidence.
