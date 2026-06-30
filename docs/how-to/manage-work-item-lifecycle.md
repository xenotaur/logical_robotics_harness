# Manage the Work-Item Lifecycle

Use this guide when a work item exists and you need to decide whether to audit,
refine, prompt, execute, or close it with evidence. The workflow keeps three
authorities separate:

- deterministic checks report facts;
- assistive requests render reviewable prompts and artifacts;
- humans make lifecycle, scope, and closeout decisions.

## End-to-end command sketch

```bash
lrh work-items validate
lrh work-items audit --format md
lrh work-items readiness --status proposed --format md
lrh request ready-work-item WI-ASSIST-INSTALLABILITY-HARDENING
# review/apply refinement PR
lrh request prompt-from-work-item WI-ASSIST-INSTALLABILITY-HARDENING
# optional: for execution-ready items, render a dry-run/manual packet before execution
lrh request run-packet-from-work-item WI-EXAMPLE --out /tmp/run-packet.md
# after implementation/evidence
lrh request run-report-from-work-item WI-ASSIST-INSTALLABILITY-HARDENING \
  --outcome success \
  --validation-result "scripts/test :: pass :: local output" \
  --evidence project/evidence/EV-EXAMPLE.md
```

The example item is intentionally useful because it shows a valid but initially
not-ready work item. `WI-ASSIST-INSTALLABILITY-HARDENING` records a real
packaging concern and passes structural validation, but its body is too thin for
a bounded implementation prompt until a reviewer adds execution-facing sections.

## Audit stale proposed work items

1. Run structural validation first:

   ```bash
   lrh work-items validate
   ```

2. Generate human-readable and, when useful, machine-readable audit reports:

   ```bash
   lrh work-items audit --format md
   lrh work-items audit --format json
   ```

3. Review audit findings against concrete repository evidence: code, tests,
   documentation, execution records, evidence files, run reports, and review
   notes.
4. Move or resolve only items whose acceptance criteria are clearly supported.
   Keep ambiguous items proposed and record why they remain open.

Do not use `audit` as an automatic closeout tool. It reports deterministic
signals; it does not decide whether work is semantically complete.

## Make a thin work item ready

1. Diagnose readiness for a selected item or status bucket:

   ```bash
   lrh work-items readiness WI-ASSIST-INSTALLABILITY-HARDENING
   lrh work-items readiness --status proposed --format md
   ```

2. If required sections are missing, render a refinement request:

   ```bash
   lrh request ready-work-item WI-ASSIST-INSTALLABILITY-HARDENING
   ```

3. Review the rendered request and apply any accepted refinements in a normal
   documentation/control-plane change. Turn uncertain details into `Open
   Questions` rather than invented scope.
4. Re-run readiness before generating an implementation prompt.

Do not use `validate` as the gate for this step: valid capture items are allowed
to be thin. Do not expect `readiness` or `ready-work-item` to mutate files in the
MVP; both are review-support surfaces.

## Generate a Codex implementation prompt

After readiness issues are resolved, render a direct implementation prompt:

```bash
lrh request prompt-from-work-item WI-EXAMPLE
```

Use `prompt-from-work-item` only when the selected item has enough scope,
required changes, acceptance criteria, and validation details to bound execution.
The rendered prompt is an input to a human or agent; it is not evidence that work
has been executed.

## Produce run packets, reports, and closeout artifacts

For execution-ready work items that opt into run metadata, render a run packet
before manual or dry-run execution:

```bash
lrh request run-packet-from-work-item WI-EXAMPLE --out /tmp/run-packet.md
```

After implementation work and evidence collection, render a report from supplied
results:

```bash
lrh request run-report-from-work-item WI-EXAMPLE \
  --outcome success \
  --run-packet /tmp/run-packet.md \
  --validation-result "scripts/test :: pass :: local output" \
  --validation-result "lrh validate :: pass :: local output" \
  --evidence project/evidence/EV-EXAMPLE.md \
  --artifact docs/how-to/manage-work-item-lifecycle.md \
  --out /tmp/run-report.md
```

Use the report as closeout support, not as an automatic lifecycle transition.
Human review should confirm that required evidence exists before moving work
items, status, focus, or roadmap records.

## What makes a work item ready: examples

A work item can be structurally valid — passes `lrh work-items validate` — while
still being too thin to generate a bounded implementation prompt. The difference
is whether the Markdown body contains the execution-facing sections that
`prompt-from-work-item` requires.

**Valid but not ready** (passes `validate`, blocked by `readiness`):

```markdown
## Summary

Harden template loading to use package resources.

## Problem / Context

Templates are loaded via source-tree-relative paths, which breaks installed packages.
```

Running `lrh work-items readiness WI-EXAMPLE` on this item reports:

```
- prompt_ready: no
- blocking:
  - missing section: Scope
  - missing section: Required Changes
  - missing section: Acceptance Criteria
  - missing section: Validation
```

**Ready and promptable** (passes `validate` and `readiness`):

```markdown
## Summary

Harden template loading to use package resources.

## Scope

Replace source-tree-relative path construction in `template_resolver.py` with
`importlib.resources.files(...)` so templates load correctly from both source
checkouts and installed wheels.

## Required Changes

- Edit `src/lrh/assist/template_resolver.py` to use `importlib.resources`.
- Add or extend smoke tests under `tests/smoke/` to verify `lrh request`
  loads templates correctly after `pip install`.

## Acceptance Criteria

- Template loading uses package resources rather than source-tree-relative paths.
- Smoke tests verify `lrh request` behavior from an installed package context.

## Validation

- `scripts/test` — all unit tests pass.
- `scripts/smoke` — smoke tests pass against an installed wheel.
- `lrh validate` — 0 errors.
```

Use `lrh request ready-work-item WI-EXAMPLE` to render a non-mutating request
that proposes the missing sections based on the work item's existing metadata
and referenced context. Review and apply what fits; leave uncertain details as
`Open Questions` rather than invented scope.

## Design reference

The vocabulary used here — valid, audited, ready, promptable, executed,
evidence-closed — is defined in
[`project/design/work_item_readiness_workflow.md`](../../project/design/work_item_readiness_workflow.md).
That design note also documents the reasoning behind keeping `lrh work-items validate`
permissive toward thin proposed items.

## When not to use each command

- Do not use `validate` to reject thin but structurally valid proposed items.
- Do not use `audit` to make semantic closure decisions by itself.
- Do not use `readiness` expecting it to refine or rewrite a work item.
- Do not use `ready-work-item` as an automatic mutation tool; it renders an
  assistive refinement request.
- Do not use `prompt-from-work-item` before readiness issues are resolved.
- Do not use `run-packet-from-work-item` as permission to execute autonomously.
- Do not use `run-report-from-work-item` before implementation evidence exists.
