# Contributing to Logical Robotics Harness (LRH)

Thank you for your interest in contributing to LRH.

This document is a contributor gateway: it explains how to contribute effectively, safely,
and with minimal process overhead. It does **not** replace canonical project documents.

If this is your first contribution, start here, then follow the linked sources of truth.

---

## Welcome and scope

LRH is a reusable harness for structured, evidence-backed, agent-assisted workflows.
Contributions should strengthen that mission while keeping the repository reusable across
multiple independent client projects.

In practical terms:

- Keep the harness generic (not hard-coded to this repository only).
- Keep project-control artifacts human-readable.
- Keep changes inspectable and auditable.

Canonical context:

- Project mission and structure: [`README.md`](README.md)
- Agent/repository operating constraints: [`AGENTS.md`](AGENTS.md)
- Contribution/editing discipline: [`STYLE.md`](STYLE.md)

---

## Contribution principles

### 1) Small, scoped, reviewable changes

Prefer minimal diffs with clear intent.
Do not include unrelated reformatting, renaming, or speculative cleanup.

### 2) Explicit project state and auditability

Important state should be visible in version control and easy to trace in review.
Avoid hidden state transitions, undocumented behavior, or opaque automation side effects.

### 3) Evidence over assertion

Claims like "done", "fixed", or "validated" must be backed by evidence.
Examples include:

- test output
- validation command output
- logs
- generated artifacts
- review notes
- other inspectable outputs

### 4) Preserve human control

Humans set intent, scope, and acceptance criteria.
Automation and AI can assist, but should not silently override project direction.

### 5) "Don't be evil" (operational interpretation)

For LRH, this means:

- do good work;
- do no hidden harm;
- preserve human control;
- leave evidence.

And specifically, do **not**:

- deceive reviewers;
- obscure important risk;
- erase or rewrite audit history without explicit reason;
- invent validation outcomes;
- silently override project intent;
- weaken safety/guardrail expectations for convenience.

---

## Ways to contribute

You can help by contributing in any of these modes:

- **Code**: features, fixes, reliability, ergonomics
- **Tests**: better coverage, determinism, regression guards
- **Documentation**: clarity, onboarding, examples, architecture notes
- **Control-plane quality**: improving `project/` coherence and traceability
- **Review**: issue triage, PR feedback, failure reproduction

When in doubt, prefer contributions that strengthen the first validation slice
(centered around `lrh validate`) and make status/evidence easier to trust.

---

## Before starting work

1. Read key docs:
   - [`AGENTS.md`](AGENTS.md)
   - [`STYLE.md`](STYLE.md)
   - [`README.md`](README.md)
   - [`PROMPTS.md`](PROMPTS.md) (for meaningful prompt-driven work)
   - [`REVIEWS.md`](REVIEWS.md) (review/repair protocol)

2. Understand control-plane intent in `project/`:
   - principles, goal, roadmap, focus, work items, evidence, status, guardrails

3. Confirm your change scope:
   - what problem you are solving
   - what files are in scope
   - what evidence will demonstrate success

4. Keep the planned PR narrow.

---

## Development workflow

Use repository scripts and documented entry points.

Typical task-phase validation flow:

```bash
scripts/version tools
scripts/format --check --diff
scripts/lint
scripts/test
lrh validate
```

Notes:

- For documentation-only changes, run only relevant lightweight checks.
- Do not claim any check passed unless you actually ran it.
- If tool versions are missing/mismatched, report setup/cache mismatch clearly.

---

## Pull request expectations

A good LRH pull request is:

- small and focused
- easy to review
- evidence-backed
- aligned with repository conventions

PRs should include:

- **what** changed
- **why** it changed
- **validation performed** (exact commands and outcomes)
- **follow-up** (if anything remains)

Avoid broad, unrelated, or speculative diffs.
If additional cleanup is useful, propose it as a separate follow-up change.

---

## AI-assisted contribution rules

AI-assisted changes are welcome and held to the **same** quality bar as human-authored work.

Requirements:

- Keep scope bounded to the requested task.
- Preserve repository conventions and architecture boundaries.
- Do not fabricate tests, outputs, benchmarks, logs, or review results.
- Do not create sweeping unrelated edits.
- Ensure a human can understand and audit the resulting diff.

AI help should increase clarity and throughput, not reduce traceability or trust.

---

## Prompt-driven workflow and execution records

For meaningful prompt-driven changes, use prompt IDs and execution records.

Canonical guidance:

- Prompt workflow and soft idempotence: [`PROMPTS.md`](PROMPTS.md)
- Execution-record schema/statuses: [`project/executions/README.md`](project/executions/README.md)

Key expectations:

- Use `AD_HOC` when no work item applies.
- Check for prior execution records before running a prompt.
- Treat prior records as historical evidence; do not rewrite unrelated history.
- Keep records concise and useful.
- Keep this workflow lightweight; tiny obvious fixes should not be blocked by process overhead.

---

## Control-plane source of truth

`project/` is LRH's human-readable source of truth for the control plane.

The project schema is organized as:

**Principles → Project Goal → Roadmap → Current Focus → Work Items → Evidence → Status**

Contributions that affect project intent, execution state, or completion claims should keep this
stack coherent and auditable.

---

## Review and conduct

All participants are expected to follow the code of conduct:

- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)

For review/repair behavior and validation protocol, see:

- [`REVIEWS.md`](REVIEWS.md)

Assume good faith, provide actionable feedback, and keep discussion evidence-based.

---

## Where to find more detail

Start with these canonical documents:

- Project overview and commands: [`README.md`](README.md)
- Agent and repository rules: [`AGENTS.md`](AGENTS.md)
- Style and change-scope discipline: [`STYLE.md`](STYLE.md)
- Prompt and execution-record process: [`PROMPTS.md`](PROMPTS.md)
- Execution-record format: [`project/executions/README.md`](project/executions/README.md)
- Review protocol: [`REVIEWS.md`](REVIEWS.md)
- Control-plane source documents: [`project/`](project/)

If a guideline appears to conflict:

1. follow direct maintainer instructions,
2. then repository policy docs,
3. then general conventions.

When uncertain, choose the more conservative, auditable, and human-reviewable path.
