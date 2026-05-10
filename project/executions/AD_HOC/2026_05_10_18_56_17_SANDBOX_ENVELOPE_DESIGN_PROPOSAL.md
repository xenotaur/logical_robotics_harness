---
execution_id: 2026_05_10_18_56_17_SANDBOX_ENVELOPE_DESIGN_PROPOSAL
prompt_id: PROMPT(AD_HOC:SANDBOX_ENVELOPE_DESIGN_PROPOSAL)[2026-05-09T00:00:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-10T18:56:17+00:00
---

# Summary

Add a documentation-only constitutional sandbox envelope design proposal under
`project/design/proposals/`, with a proposal-set README and top-level proposal
index entry.

# Result

Created a proposed design proposal set for the constitutional sandbox envelope.
The proposal documents a capability-limited, policy-checked, sandboxed,
auditable, and interruptible authority boundary for future `lrh run`, agent
adapter, MCP, and external resource access. It covers security motivation,
LRH architectural placement, layered design, capability APIs, dangerous
capabilities, policy precedence, sandbox runtime options, evidence logging,
e-stop/revocation behavior, constitutional review, staged implementation,
tradeoffs, open questions, non-goals, and the recommended design principle.

Updated the design proposals README so the new proposal set is discoverable.
No runtime behavior, code, tests, or unrelated execution records were changed.

# Validation

- `lrh prompt check-execution --prompt-id "PROMPT(AD_HOC:SANDBOX_ENVELOPE_DESIGN_PROPOSAL)[2026-05-09T00:00:00-04:00]" --project-root .` found no prior execution records before implementation.
- `scripts/version tools` completed before task-phase validation; Black and Ruff
  were available, while pylint and conda were not installed in this environment.
- `lrh validate` completed with 0 errors and 0 warnings.

# Follow-up

If the proposal is adopted later, follow-up implementation should proceed in
small control-plane-first slices rather than jumping directly to deep
multi-agent orchestration or broad MCP/cloud integrations.
