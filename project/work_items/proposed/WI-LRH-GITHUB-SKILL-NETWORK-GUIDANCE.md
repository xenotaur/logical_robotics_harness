---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-GITHUB-SKILL-NETWORK-GUIDANCE
title: Add bounded network-escalation guidance to GitHub-backed LRH skills
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
  - WS-LRH-GITHUB-EXECUTION-RESILIENCE
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - refresh_credentials
acceptance:
  - A canonical shared procedure states that local-only commands run normally and GitHub, remote-Git, PR, review, and GitHub-backed LRH commands may require approved network execution.
  - The procedure requires one bounded retry through the approved path, then a clear blocker report when approval is unavailable or the retry fails.
  - The procedure requires the correct absolute project root and does not recommend credential refresh for DNS or connection failures.
  - All in-scope GitHub-consuming canonical skills incorporate the procedure, and Claude/Codex rendered targets are regenerated and checked for drift.
  - "`lrh validate` reports 0 errors."
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/_shared/github-network-execution.md
  - src/lrh/skills/lrh-implement/SKILL.md
  - src/lrh/skills/lrh-workstream/SKILL.md
  - src/lrh/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-closeout/SKILL.md
  - src/lrh/skills/lrh-review-response/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md
  - src/lrh/skills/lrh-pr-triage/SKILL.md
---

# Add bounded network-escalation guidance to GitHub-backed LRH skills

## Summary

Codex managed sandboxes can deny DNS and HTTPS in normal execution while the
same GitHub commands succeed through approved network execution. GitHub-backed
skills currently explain the workflow but not this recovery path, so agents can
stall or misdiagnose a platform restriction as a repository or credential fault.

## Problem / Context

The direct evidence is a normal-versus-approved execution comparison: Python
DNS, `curl`, and GraphQL all failed normally and all succeeded when network
execution was approved. The existing backlog already records this missing
Codex-friendly guidance at `project/design/backlog.md:1071-1075`.

### Duplication search

- In-repo: Existing approval wording is present in
  `src/lrh/skills/lrh-codex-export/SKILL.md`; no GitHub-network procedure exists.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed by extracting a reusable procedure from the existing
  approval precedent.

### Demand search

- Work items: No matching proposed item found.
- Proposals: No matching proposal found.
- Backlog: Matching unimplemented Codex skill-adaptation entry found.
- Recommendation: Proceed and close the backlog demand through this item.

## Scope

- Create one canonical maintainer-facing procedure and incorporate its runtime
  guidance into the GitHub-consuming skills.
- Regenerate the supported rendered targets from canonical skill sources.
- Keep the guidance backend-neutral while naming approved network execution as
  the Codex recovery mechanism.

## Required Changes

1. Create `src/lrh/skills/_shared/github-network-execution.md` with the
   normal/elevated execution distinction, one-retry rule, project-root check,
   credential-safety rule, and blocker-reporting rule.
2. Add concise references to the procedure in the affected canonical skills.
3. Regenerate `.claude/skills/` and `.agents/skills/` for every touched skill.
4. Run `lrh validate` and the target drift checks.

## Non-Goals

- Do not make every command elevated.
- Do not add automatic credential changes.
- Do not silently use `--no-remote` when a remote idempotence check is required.
- Do not add live network calls to unit tests.

## Acceptance Criteria

- A failing Codex session following the guidance requests approved network
  execution for the GitHub-dependent step and does not loop in the normal
  sandbox.
- Local-only validation remains documented as normal execution.
- The guidance says that unavailable approval is a blocker, not permission to
  guess, skip remote checks, or refresh credentials.
- Canonical and rendered skill targets are consistent.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `lrh skills check --target claude --local --source current-repo`
- `lrh skills check --target codex --local --source current-repo`
- `diff -r src/lrh/skills/ .claude/skills/`

## Risk Notes

- Over-broad escalation guidance could weaken least-privilege practice; keep the
  procedure limited to commands that contact GitHub or remote Git.
- Generated target drift could leave one agent backend without the recovery
  path; target checks are required evidence.
