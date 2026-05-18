# Why Work-Item Validation, Audit, Readiness, and Prompting Are Separate

LRH intentionally separates work-item checkpoints so early planning remains easy
while execution and closeout stay evidence-backed.

## Valid is not ready

A valid work item has good source hygiene: parseable frontmatter, a stable ID,
status-bucket consistency, valid references, and coherent dependencies. Proposed
items are allowed to be capture artifacts. They may describe a real problem while
leaving implementation scope and validation details for later refinement.

Readiness asks a narrower execution question: does this selected item have enough
sections and detail to render a bounded implementation prompt? Keeping readiness
out of validation prevents early planning notes from becoming noisy validation
failures.

## Audit is not closeout

Audit reports deterministic lifecycle and traceability signals. It can identify
weak links, terminal metadata issues, or surprising execution-record references,
but it cannot know whether acceptance criteria are semantically satisfied.
Closeout still requires human review against concrete evidence.

## Prompting is not execution

`ready-work-item`, `prompt-from-work-item`, `run-packet-from-work-item`, and
`run-report-from-work-item` render artifacts for review. They do not dispatch an
agent, mutate branches, open pull requests, run tests, merge, publish, or move
work-item lifecycle records. The rendered artifacts help humans and agents do
bounded work; they are not proof that the work happened.

## Evidence closure remains human-reviewed

Run reports summarize supplied validation results, artifacts, evidence
references, risks, and review tasks. They can support lifecycle moves, but they
should not replace evidence files, test output, logs, screenshots, metrics, or
review notes. A work item is evidence-closed only when a reviewer can connect the
acceptance criteria to concrete evidence.
