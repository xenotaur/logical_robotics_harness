# Work-Item Readiness Workflow

## Purpose

This design note defines the lifecycle vocabulary between a structurally valid LRH work item and a
work item that is ready to render as a direct implementation prompt. It is a design-plane alignment
record only; it does not implement new CLI behavior, change `prompt-from-work-item` readiness gates,
or make `lrh work-items validate` stricter for thin proposed work items.

Dogfooding exposed the gap with `WI-ASSIST-INSTALLABILITY-HARDENING`: the work item is structurally
valid and passes normal work-item validation, but `lrh request prompt-from-work-item` blocks it from
becoming an implementation prompt because the Markdown body lacks execution sections such as
`Scope`, `Required Changes`, and `Validation`. That is a useful failure mode, but the vocabulary and
command boundaries need to be explicit before LRH adds a readiness-diagnosis command or an assistive
readying workflow.

## Lifecycle vocabulary

```text
capture
  A work item exists and has valid frontmatter / basic metadata.

validate
  The work item is structurally and referentially valid.

audit
  The work item has traceability/lifecycle signals checked.

readiness
  The work item has the execution sections needed for implementation prompting.

ready/refine
  An assist workflow proposes missing sections using referenced context.

prompt
  `prompt-from-work-item` renders a direct implementation prompt.

execute
  Human/Codex performs the work.

report
  `run-report-from-work-item` summarizes evidence and supports closeout.
```

The lifecycle states are intentionally not all frontmatter statuses. They describe checkpoints in a
workflow that may be inspected by deterministic commands, assisted by request renderers, and reviewed
by humans before lifecycle moves or closeout.

## Distinctions

### Valid work item

A valid work item satisfies deterministic work-item hygiene: parseable frontmatter, a reliable ID,
valid status/bucket semantics, valid reference shapes, and dependency consistency. Validity means LRH
can load and reason about the item as project-control data. It does not mean the item has enough
implementation detail to send directly to Codex or another executor.

`lrh work-items validate` should not fail thin proposed work items merely because they are not
implementation-ready. Proposed items are often useful capture artifacts: they may record a problem,
priority, dependency, or acceptance sketch before scope and validation details are known. Treating
thin capture artifacts as validation failures would make early planning noisy and would collapse
planning hygiene into execution readiness.

### Audited work item

An audited work item has deterministic lifecycle and traceability signals checked by
`lrh work-items audit`. Audit can report facts such as missing traceability links, terminal items
without resolution metadata, or execution records attached to non-terminal items. Audit is still not a
semantic reviewer and should not decide that acceptance criteria are complete.

### Ready work item

A ready work item has enough execution-facing Markdown content for implementation prompting. For the
current `prompt-from-work-item` surface, readiness includes sections such as `Scope`,
`Required Changes`, `Acceptance Criteria`, and `Validation`. Readiness is narrower than full project
validity: it answers whether the selected work item is sufficiently specified to generate a bounded
implementation prompt.

### Promptable work item

A promptable work item has passed readiness gates for the prompt renderer and is not blocked by
status, explicit blocked state, or human-only suitability signals. A ready item may still be
non-promptable if it is marked blocked, already terminal, or explicitly requires human design review
before implementation.

### Implementation prompt

An implementation prompt is a rendered, reviewable request produced after readiness gates pass. It
packages the work-item context, repository guidance, scope, required changes, validation commands,
and final response requirements. It is an input to human/Codex execution, not proof that execution
happened.

### Evidence-backed run report / closeout

A run report is a deterministic, evidence-oriented summary of a manual or dry-run execution attempt.
It should cite supplied validation results, evidence references, artifacts, unresolved risks, and
human verification tasks. Closeout remains human-reviewed: reports support lifecycle decisions, but
they do not automatically move work items, roadmap entries, focus, or status.

## Command boundary

The intended command split is:

| Boundary | Command | Kind | Responsibility |
| --- | --- | --- | --- |
| Structural validation | `lrh work-items validate` | deterministic | Check work-item hygiene and references without requiring implementation-ready sections. |
| Lifecycle audit | `lrh work-items audit` | deterministic | Report traceability and lifecycle signals without semantic closure decisions. |
| Readiness diagnosis | `lrh work-items readiness` | deterministic | Diagnose missing implementation-prompt sections and promptability blockers for selected work items. |
| Readiness refinement | `lrh request ready-work-item` | assistive | Render a human-reviewable refinement request that proposes missing sections from referenced context. |
| Prompt generation | `lrh request prompt-from-work-item` | assistive | Render a direct implementation prompt only after readiness/promptability gates pass. |
| Run reporting | `lrh request run-report-from-work-item` | assistive | Render an evidence-backed post-execution report from explicit caller-supplied results and evidence. |

Command responsibilities should stay separated by authority:

```text
deterministic:
  validate, audit, readiness

assistive:
  ready-work-item, prompt-from-work-item, run-report-from-work-item

human-reviewed:
  lifecycle moves, evidence closeout, roadmap/focus changes
```

The readiness command should diagnose; it should not rewrite work items. The readying request should
assist; it should not mutate source files automatically. Prompt and report generation should continue
to render artifacts for review instead of dispatching agents, creating branches, merging pull
requests, or closing project-control records.

## Dogfood case: `WI-ASSIST-INSTALLABILITY-HARDENING`

`WI-ASSIST-INSTALLABILITY-HARDENING` motivates the split. It captures a real packaging concern,
links to existing planning context, and is valid enough for LRH to load, validate, and audit. However,
when selected for implementation prompting it is too thin: it lacks the body sections needed to bound
execution, especially `Scope`, `Required Changes`, and `Validation`.

The correct response is not to make `lrh work-items validate` fail this item. The correct response is
for a future deterministic readiness command to explain why the item is not promptable, and for a
future assistive readying request to help a human produce a reviewable enriched work item before
`prompt-from-work-item` is used.

## Follow-up implementation sequence

1. `WI-WORK-ITEMS-READINESS-CLI-MVP` — add deterministic readiness diagnostics without mutation.
2. `WI-REQUEST-READY-WORK-ITEM-MVP` — add an assistive request that proposes missing execution
   sections for human review.
3. `WI-WORKFLOW-DOCS-READINESS-AUDIT-PROMPTING` — update workflow documentation once the CLI and
   request surfaces exist.

These follow-ups should remain narrow and should not resolve `WI-ASSIST-INSTALLABILITY-HARDENING` as
part of the readiness-workflow implementation.
