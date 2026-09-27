---
id: WS-LRH-GITHUB-EXECUTION-RESILIENCE
kind: planning_node
title: Resilient GitHub-backed LRH execution across restricted sandboxes
status: proposed
stage: planned
origin: ad_hoc
summary: Track the operational guidance, LRH diagnostics, and external incident work needed to keep GitHub-backed LRH workflows usable when a Codex sandbox restricts network access.
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_design: []
work_items:
  - WI-LRH-GITHUB-SKILL-NETWORK-GUIDANCE
  - WI-LRH-GH-ERROR-CLASSIFICATION
  - WI-CODEX-MANAGED-SANDBOX-NETWORK-INCIDENT
exit_criteria:
  - GitHub-consuming LRH skills document least-privilege network escalation and blocker reporting.
  - LRH distinguishes invalid project roots, missing gh executables, and GitHub or network command failures.
  - Hermetic tests cover the GitHub wrapper failure classifications.
  - A sanitized Codex/OpenAI incident report and follow-up status are recorded.
  - Canonical validation and rendered skill-target checks pass.
---

# Resilient GitHub-backed LRH execution across restricted sandboxes

## Purpose

This workstream coordinates the small operational and code-quality changes
needed when LRH workflows run in a Codex managed sandbox whose default network
policy cannot resolve GitHub. The immediate trigger was a reproducible contrast:
normal sandbox execution failed DNS, HTTPS, and GraphQL checks, while the same
commands succeeded through approved network execution.

The stream also captures a separate LRH diagnostic defect: an invalid subprocess
working directory is currently reported as `gh CLI not found`. Keeping the
platform incident, skill guidance, and wrapper fix together makes the recovery
path traceable without coupling LRH to a particular vendor executor.

## Scope

- Add backend-neutral guidance to GitHub-consuming skills: use normal execution
  for local work, request approved network execution for GitHub operations, retry
  once, and stop clearly when approval is unavailable.
- Improve the LRH `gh` wrapper's classification of project-root, executable,
  command, and output failures.
- File and track a sanitized Codex/OpenAI networking incident using the observed
  normal-versus-approved execution evidence.

## Prior Art Check

### Duplication search

- In-repo: Related backlog entry at `project/design/backlog.md:1071-1075` and
  existing approval wording in `src/lrh/skills/lrh-codex-export/SKILL.md`; no
  existing proposed workstream covers this combined scope.
- Sibling repos: None identified.
- External libraries: None identified; this is workflow guidance and LRH error
  handling rather than a library-selection problem.
- Recommendation: Proceed, while closing the existing backlog demand through
  the work items below.

### Demand search

- Work items: No matching proposed work item found.
- Proposals: No matching proposal found.
- Backlog: Found the unimplemented Codex skill-adaptation entry requiring
  sandbox/network escalation guidance and graceful fallback semantics.
- Recommendation: Proceed and reference the backlog demand in implementation
  evidence.

## Work Items

- **WI-LRH-GITHUB-SKILL-NETWORK-GUIDANCE** — document and propagate the
  approved network-execution procedure across GitHub-consuming skills.
- **WI-LRH-GH-ERROR-CLASSIFICATION** — distinguish invalid `cwd`, missing `gh`,
  nonzero GitHub/network exits, and malformed output in the LRH wrapper.
- **WI-CODEX-MANAGED-SANDBOX-NETWORK-INCIDENT** — file and maintain a
  sanitized external incident report with reproducible comparison evidence.

## Non-Goals

- Fixing Codex or macOS networking inside LRH.
- Refreshing, replacing, exposing, or reauthorizing credentials.
- Silently replacing remote checks with local-only checks.
- Adding live network dependencies to the ordinary unit-test suite.
- Expanding LRH into a vendor-specific executor or sandbox manager.

## Exit Criteria

- Each in-scope work item has accepted evidence and is linked to this
  workstream.
- Normal local-only work remains usable without escalation.
- GitHub-dependent skills give agents a bounded recovery path and preserve
  network failures as blockers when approval is unavailable.
- The LRH wrapper no longer mislabels an invalid project root as a missing
  executable.
- `lrh validate`, canonical formatting/lint/test checks, and skill-target
  drift checks pass.
