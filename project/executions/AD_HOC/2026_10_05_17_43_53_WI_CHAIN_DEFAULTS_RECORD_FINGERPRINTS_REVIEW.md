---
execution_id: 2026_10_05_17_43_53_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_REVIEW
prompt_id: PROMPT(AD_HOC:WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_REVIEW)[2026-10-05T17:40:58+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_10_01_02_25_46_WI_CHAIN_DEFAULTS_RECORD_FINGERPRINTS_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/753
commit: 
created_at: 2026-10-05T17:43:53+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/753
session_transcript: pending
---

# Summary

Review-response round 4 on PR #753, run inline from `/lrh-land` Step 5.

Re-verification confirmed the round-3 P2 fix (stamp-bound store) as
Clear-satisfied. It also reported three new P3s, which brought the run back
to its stop condition.

The user chose to fix all three. They also agreed a settle-now P3 policy:
- the verifier checks only these three fixes;
- any further P3 goes to Follow-up, not another round;
- if the three fixes are confirmed, the run goes straight to the merge ask.

The fixes are in commit `7e8a6a48`.

# Result

- **P3: consent offer after a PR-branch re-confirm.** Fixed. Required
  Changes 5 now offers Step 4's consent grant only on a checkout whose
  profile carries the new stamp. On the PR-branch path it does not offer
  the grant. It tells the user to grant from a checkout with the new
  profile, because Step 4 would otherwise hash the PR branch's old yaml.
- **P3: unscoped `stale: false` acceptance.** Fixed. Both the frontmatter
  acceptance and the body acceptance now apply to the checkout whose profile
  `restamp` wrote. A body criterion was added for the PR-branch consent
  behaviour.
- **P3: the stamp identified a base commit, not a re-stamp act.** Fixed.
  - The store is now bound to `(confirmed_commit, confirmed_at)`.
  - `confirmed_commit` is compared as a full resolved SHA, using the
    `rev-parse --verify` call at `src/lrh/gate_staleness.py:602`, which
    must now capture its result.
  - `check_gate_staleness` gains an optional `confirmed_at`; omitting it
    fails closed.
  - The `check-staleness` CLI gains `--confirmed-at`.
  - `chain_defaults_status.py` passes `confirmed_at` through.
  - The shared bash snippet and its inlined copy pass `confirmed_at` too
    (Required Changes 4).
  - The docs item and tests were extended to match, covering a matching
    commit with a different `confirmed_at`, a short-SHA profile, and an
    omitted `confirmed_at`.

# Validation

- `PYTHONPATH=src python -m lrh.cli.main validate`: 0 errors, 0 warnings.
- `scripts/test`: OK.
- `scripts/lint` and `scripts/format --check --diff` were not run because of
  local tool-version pins (ruff 0.15.12 required vs 0.15.0 installed; black
  26.3.1 required vs 25.11.0 installed). This PR changes Markdown only.

# Follow-up

- Confirm-fixes: scoped verification of these three fixes, then the
  `_CONFIRM` record and the merge ask.
