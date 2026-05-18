# Evidence-backed status

LRH treats status as a claim that should be grounded in evidence.

A status document is useful when it helps a reader answer, "What is true right now, and why should
I believe it?" It is less useful when it merely sounds confident.

## What counts as evidence

Evidence can be any durable artifact that supports or limits a status claim, such as:

- test results;
- lint or validation output;
- release smoke logs;
- CI run summaries;
- screenshots;
- metrics;
- review notes;
- design review outcomes;
- reports from investigation work;
- approval or rejection records.

Evidence should be specific enough that a maintainer can inspect it later. It does not have to be
large or complicated; a concise execution record or command transcript can be enough for the claim
being made.

## Status should not outrun evidence

LRH's status layer should avoid unsupported optimism. For example:

- "implemented" should point to merged code, tests, or other completion evidence;
- "validated" should point to the validation command or review result;
- "blocked" should point to the constraint or failing check;
- "ready" should be tied to acceptance criteria, readiness metadata, or review evidence.

If evidence is incomplete, the status should say so. A clear yellow or blocked status is better
than a green summary that hides uncertainty.

## Evidence in the control-plane stack

In the control-plane stack, evidence sits before status:

```text
Work Items → Evidence → Status
```

That order matters. Work items describe intended or completed units of work. Evidence records what
actually happened. Status synthesizes the current state from focus, work items, and evidence.

## Evidence and prompt-driven work

Prompt-driven changes often create an execution record under `project/executions/`. That record can
capture what prompt ran, what changed, what validation was attempted, and what follow-up remains.
It is not a replacement for tests or project evidence, but it helps reviewers trace the work from
prompt to result.

For meaningful work, the execution record should be concise and useful:

- summarize the change;
- record whether it landed, failed, was superseded, or was reverted;
- list validation commands and results;
- note follow-up work if needed.

## Evidence is not only success evidence

Negative evidence is valuable. Failed checks, blocked approvals, missing dependencies, stale
summaries, and rejected approaches all help future maintainers avoid repeating mistakes. LRH should
preserve these outcomes instead of deleting them to keep status tidy.

## `docs/` versus `project/`

This explanation teaches the evidence-backed status concept. The current authoritative status and
evidence for LRH live under `project/status/` and `project/evidence/`. If those artifacts disagree
with this page, treat the project artifacts as the current project state and update this explanation
only as a human-facing summary.

Authoritative and related sources:

- [current status](../../project/status/current_status.md);
- [evidence directory](../../project/evidence/);
- [execution records README](../../project/executions/README.md);
- [architecture design](../../project/design/architecture.md).
