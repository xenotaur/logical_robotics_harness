---
execution_id: 2026_09_30_00_07_52_LOCAL_AGENT_TOY_LADDER
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_TOY_LADDER)[2026-09-29T23:30:57+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/759
commit: 
created_at: 2026-09-30T00:07:52+00:00
agent: claude_app
instruction_source: ad_hoc conversation — owner-requested in-place revision of PROP-LOCAL-AGENT-DOGFOOD to a toy ladder (option 2)
session_transcript: pending
---

# Summary

A control-plane revision of `PROP-LOCAL-AGENT-DOGFOOD`, made in place at the
owner's request. The formal stage-0 pilot is replaced with a toy ladder: small,
usable local-model prototypes judged from automatic evidence, with heavy gates
starting at the first toy that can change files or run commands.

The owner halted the pilot at runbook step 3 for three reasons: the manual
timed-baseline protocol was disproportionate for read-only prototypes; the
smoke run returned empty output; and the overall goal is iteratively more
useful local agents built from small usable components.

# Result

- **Proposal:**
  - Decisions 1, 3, 4, and 7 are rewritten.
  - The Toy Ladder Approval replaces the Stage-0 Lane Approval: T0 and T1 are
    approved, T2 is not.
  - A new Experimental PR Process section (`experimental/` and execution
    records only) is added, along with a revision note.
  - The safety design (Decision 6) and the local-only checks are preserved.
- **WS-LOCAL-AGENT-DOGFOOD:** re-scoped.
- **WI-LOCAL-AGENT-001:** re-scoped to T0 ask and T1 brief; still active.
- **WI-LOCAL-AGENT-002:** re-scoped to T2; still proposed.
- **`experiments/01`:** superseded, and kept as history.
- **Wording updates:** focus, execution framework, parent WS, READMEs, and
  prototype banners.

The diff-mode self-review found nine issues, all fixed. See
`2026_09_30_00_07_12_LOCAL_AGENT_TOY_LADDER_SELFREVIEW`.

# Validation

- Format and lint clean.
- `scripts/test --log`: Ran 1903 tests, OK.
- `experimental/local_agent/test`: OK.
- `lrh validate`: 0 errors, 0 warnings.
- Readiness: both WIs `prompt_ready`.

# Follow-up

- Next is the T0 `ask` prototype PR, the first under the Experimental PR
  Process. It includes the thinking-mode fix.
- The optional `/lrh-config-gates` change to the repository stop-work default
  remains the owner's call.
