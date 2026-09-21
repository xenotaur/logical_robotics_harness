---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-BRANCH-PROTECTION-PROBE-AND-GUIDE
title: Probe base-branch rules in /lrh-land and document recommended branch protection
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - modify_repo_settings
  - weaken_human_gate
acceptance:
  - /lrh-land Steps 2 and 6 report the base branch's active rules using the read-only rules/branches/<base> endpoint (the probe already documented in lrh-confirm-fixes/references/confirm-fixes-workflow.md), naming whether a pull_request rule and a required_status_checks rule exist
  - When neither rule exists, the summaries carry an advisory line that the closeout-PR merge is gated only by the agent-side verifier; the advisory is informational and never blocks or authorizes anything
  - The probe never modifies repository settings and degrades to a stated "rules unavailable" line when the endpoint cannot be read
  - A new how-to at docs/how-to/project-setup/branch-protection.md covers ruleset setup, required status checks, solo-maintainer settings (zero required approvals or a bypass list), and the auto-merge opt-in
  - Every external claim in the how-to (GitHub plan limits for private repos, gh pr merge --auto behavior, required-check renaming gotcha) is verified against GitHub's documentation and cited before it is written
  - The how-to states plainly that most client repos are unprotected and that the skills work there; protection is a recommendation, not a requirement
  - .claude/skills mirror is byte-identical to src/lrh/skills; .agents/skills and .gemini/plugins/lrh/skills are regenerated via lrh skills install
  - lrh chain-defaults check-staleness output is reported, and scripts/test, scripts/lint, scripts/format --check --diff and lrh validate are all clean
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - docs/how-to/project-setup/branch-protection.md
  - docs/how-to/project-setup/README.md
  - .claude/skills/lrh-land/
  - .agents/skills/
  - .gemini/plugins/lrh/skills/
---

## Summary

Make `/lrh-land` aware of the base branch's protection rules, so a mixed fleet
of protected and unprotected repos is handled explicitly, and document the
recommended protection setup for users who want the platform to enforce the
gates as well.

## Problem / Context

Branch protection is a per-repo GitHub setting, but the skill text ships to
every repo that runs `lrh skills install`, so the skill cannot assume it.
This repo's `main` has rulesets for `deletion`, `non_fast_forward` and
`copilot_code_review` only: no `pull_request` rule and no
`required_status_checks` rule, so a direct fast-forward push works
technically, `allow_auto_merge` is false, and there is no required CI to
wait on. `lrh-confirm-fixes/references/confirm-fixes-workflow.md:235-262`
already probes `rules/branches/<base>` and branches on the count of
`required_status_checks` rules; that probe generalizes.

Design discussion outcome: with the mechanical closeout-PR verifier
(`WI-LRH-CLOSEOUT-PR-VERIFIER`) as the portable core, the probe tells the human
what backstop exists on top of it: a `pull_request` rule with required
approvals makes GitHub itself demand a separate approver (so the merge falls
back to the human), required checks make CI green platform-enforced, and no
rules mean the verifier is the only guard.

Prior art check:

- **Duplication:** none for the how-to; the rules probe exists only inside
  `confirm-fixes-workflow.md` for CI waits.
- **Demand:** no existing work item; it arises from the closeout-PR design.

## Scope

- A read-only probe and advisory lines in `/lrh-land` Steps 2 and 6.
- A how-to page and its index entry.
- Mirror sync and installer regeneration.

## Required Changes

- Add the probe and advisory text to `/lrh-land`, outside marked
  `GATE-DEFINITION` regions where possible; flag every touch of a marked
  region and treat it as a gate-semantics change.
- Write `docs/how-to/project-setup/branch-protection.md` and link it from the
  project-setup README.
- Verify and cite the external GitHub claims before stating them.

## Non-Goals

- The skill never changes repo settings; users apply protection themselves.
- No new gate, no change to merge authorization.
- No requirement that a repo be protected for the skills to work.

## Acceptance Criteria

- The probe, advisory, how-to and citation requirements above.
- Mirrors in sync; `check-staleness` output reported; all validation commands
  below clean.

## Validation

- scripts/test
- scripts/lint
- scripts/format --check --diff
- lrh validate
- lrh chain-defaults check-staleness --confirmed-commit <confirmed_commit> --project-root .
- diff -r src/lrh/skills/lrh-land .claude/skills/lrh-land

## Risk Notes

- The advisory must stay informational; making it block a run would be a new
  gate.
- GitHub plan limits vary; the how-to must not overpromise for private repos.
- Editing marked regions invalidates stored skip-consent (one re-grant).
