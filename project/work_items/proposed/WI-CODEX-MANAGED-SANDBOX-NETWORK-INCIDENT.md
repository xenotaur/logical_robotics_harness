---
resolution: null
blocked_reason: null
blocked: false
id: WI-CODEX-MANAGED-SANDBOX-NETWORK-INCIDENT
title: File and track the Codex managed-sandbox GitHub networking incident
type: operation
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
  - create_report
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - refresh_credentials
  - print_tokens
  - include_private_transcripts
acceptance:
  - A sanitized OpenAI/Codex bug report records normal-versus-approved execution results, timestamps, and session/executor context where exposed.
  - The report distinguishes sandbox network policy from LRH, GitHub CLI, repository, and credential hypotheses.
  - The report contains no tokens, authorization headers, full API bodies, private transcripts, or private repository contents.
  - Follow-up status records whether the platform exposes a durable network-policy or executor fix.
required_evidence:
  - manual_review
  - validation_output
artifacts_expected:
  - project/evidence/EV-CODEX-MANAGED-SANDBOX-NETWORK.md
---

# File and track the Codex managed-sandbox GitHub networking incident

## Summary

Normal Codex sandbox execution failed Python DNS, `curl`, and GraphQL checks,
while the same commands succeeded with explicitly approved network execution in
the same working directory, repository, `gh` version, and credential context.
This is sufficient for a platform incident report, while remaining separate
from the confirmed LRH `cwd`/`gh CLI not found` classification defect.

## Problem / Context

The incident prevents GitHub-backed LRH idempotence, review, and closeout
workflows from progressing in affected sessions. The normal-versus-approved
comparison is the key evidence; authentication should not be changed until the
affected execution path can reach GitHub.

### Duplication search

- In-repo: Related evidence and backlog notes exist, but no proposed incident
  operation item exists.
- Sibling repos: LCATS supplied comparison evidence; no separate implementation
  was identified.
- External libraries: None identified; the action is incident reporting and
  follow-up.
- Recommendation: Proceed as a bounded operation.

### Demand search

- Work items: No matching proposed item found.
- Proposals: No matching proposal found.
- Backlog: Related Codex sandbox/network guidance demand found at
  `project/design/backlog.md:1071-1075`.
- Recommendation: Proceed and preserve the sanitized evidence for follow-up.

## Scope

- Prepare the external bug report and maintain a local evidence artifact.
- Record normal and approved execution outcomes without exposing secrets.
- Re-test only when platform changes or a new executor policy is available.

## Required Changes

1. Create `project/evidence/EV-CODEX-MANAGED-SANDBOX-NETWORK.md` with sanitized
   reproduction steps, timestamps, exit codes, and conclusions.
2. File the external report through the appropriate OpenAI/Codex support path.
3. Record the report date, non-secret reference, and follow-up state in the
   evidence artifact.

## Non-Goals

- Do not change GitHub credentials or keychain state.
- Do not modify Codex settings or attempt to bypass approval controls.
- Do not claim a platform fix until an affected session succeeds without the
  previously required escalation.
- Do not include private transcripts or raw authorization-bearing diagnostics.

## Acceptance Criteria

- The evidence artifact is reviewable without secret-bearing output.
- The external report includes the deterministic normal-versus-approved test.
- The report identifies the likely sandbox network-policy layer and lists the
  unresolved executor/provisioning alternatives.
- Follow-up ownership and next diagnostic are explicit.

## Validation

- `lrh validate`
- manual review of the sanitized evidence artifact
- `git diff --check`

## Risk Notes

- Platform support may need session or executor identifiers that are not exposed;
  record them as unavailable rather than inventing them.
- Repeated diagnostics should be bounded to avoid wasting approval prompts or
  creating misleadingly large evidence logs.
