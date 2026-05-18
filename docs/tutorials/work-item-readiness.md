# From Thin Work Item to Prompt-Ready Item

This walkthrough teaches the normal path from a captured work item to a prompt
that a human or Codex can execute. It uses
`WI-ASSIST-INSTALLABILITY-HARDENING` as the motivating pattern: the item is valid
project-control data, but it starts too thin for a bounded implementation prompt.

## 1. Confirm structural validity

```bash
lrh work-items validate
```

A passing result means LRH can load and reason about the work item. It does not
mean the item is ready to implement.

## 2. Inspect lifecycle signals

```bash
lrh work-items audit --format md
```

Read the audit as a factual report. If it points to missing evidence or weak
traceability, collect or link the evidence before closeout decisions.

## 3. Diagnose prompt readiness

```bash
lrh work-items readiness WI-ASSIST-INSTALLABILITY-HARDENING
```

For a thin work item, expect diagnostics about missing execution-facing sections
such as `Scope`, `Required Changes`, `Acceptance Criteria`, or `Validation`.
That is a refinement need, not a validation failure.

## 4. Render a refinement request

```bash
lrh request ready-work-item WI-ASSIST-INSTALLABILITY-HARDENING
```

Submit the rendered request to a reviewer or assistant. The output should help a
human produce a normal edit to the work-item file. Unresolved context should stay
visible as open questions.

## 5. Generate the implementation prompt

After the work-item refinement is reviewed and committed, re-run readiness and
then render the prompt:

```bash
lrh work-items readiness WI-ASSIST-INSTALLABILITY-HARDENING
lrh request prompt-from-work-item WI-ASSIST-INSTALLABILITY-HARDENING
```

The prompt is now a bounded execution request. After execution, collect evidence
and use a run report to support closeout review.
