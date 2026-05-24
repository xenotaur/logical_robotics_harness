# Documentation audit and organization workflow

LRH documentation-request workflows separate diagnosis from intervention:

```text
audit_docs    -> produce a documentation audit prompt
organize_docs -> produce a scoped implementation prompt based on the audit
```

## Why LRH separates diagnosis from intervention

Separating `audit_docs` from `organize_docs` keeps documentation changes reviewable and bounded. Teams can inspect the audit first, agree on priorities, and then generate focused implementation prompts rather than jumping directly into broad reorganization.

## Why the audit artifact matters

The audit output is a durable, reviewable intermediate artifact. It captures findings, gaps, and recommended sequencing that can be discussed before edits begin. This supports evidence-backed planning and reduces churn from ad hoc restructuring.

## How Diátaxis guides the workflow

Diátaxis provides quality lenses (tutorials, how-to, reference, explanations) without forcing a mechanical folder recipe. The audit should assess whether content serves the right reader intent, while still respecting the repository's existing structure and constraints.

## Control plane versus human-facing docs

In LRH, `project/` remains the authoritative control plane, while `docs/` is the human-facing layer. Docs-organization prompts should improve usability and discoverability without replacing control-plane authority or duplicating mutable project state.

## Relationship to future automation

Today these commands generate prompts only. They can later be connected to work items, execution records, and possible `lrh run` orchestration, but that integration is not currently implemented.
