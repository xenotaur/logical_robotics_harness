---
execution_id: 2026_08_22_19_42_22_GATE_POLICY_AUDIT_HOUSEKEEPING
prompt_id: PROMPT(AD_HOC:GATE_POLICY_AUDIT_HOUSEKEEPING)[2026-08-22T19:42:05+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-08-22T19:42:22+00:00
---

# Summary

Ad hoc governance-hygiene fixes surfaced during a confirm-gate policy audit
conversation (interrogating `PROP-INVOCATION-AND-GATE-RESET`,
`DEC-DELIBERATE-CHAIN-INITIATION`, and `PROP-LRH-CHAIN-DEFAULTS` against
observed `/lrh-land` session behavior). This is the first PR in a planned
1-2-3 sequence: this housekeeping fix, then `WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5`,
then `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` on top of it — landed as three
separate PRs, not bundled, since the latter two share files
(`project/config/chain-defaults.yaml`, `src/lrh/skills/_shared/chain-defaults.md`,
`src/lrh/skills/lrh-land/references/land-workflow.md`) and this project's own
`WS-INVOCATION-AND-GATE-RESET` history already recorded that sequencing, not
bundling, is the correct response to that kind of overlap.

# Result

Three fixes, no code/skill-behavior changes:

1. `DEC-DELIBERATE-CHAIN-INITIATION.md` — edited principle 1's "chain
   initiation by itself does not satisfy a skill's own internal confirmation
   gate" sentence in place to carry the `DEC-SINGLE-ASK-RUN-GATES` restatement
   narrowing directly (with the closeout/merge-collapse example), rather than
   leaving the categorical sentence unedited and relying solely on a trailing
   forward-pointing note. Summary paragraph updated to match.
2. `project/design/proposals/proposed/lrh-chain-defaults/00_proposal.md` —
   corrected stale frontmatter: `implementation_status: not_started` ->
   `partial` and `implemented_by: []` -> `[WI-LRH-CHAIN-DEFAULTS-INCREMENT-1]`,
   since that increment already shipped under this proposal while its
   frontmatter still claimed nothing had started. Also corrected one inline
   path reference to `WS-LRH-CHAIN-DEFAULTS.md` to point at its new location.
3. `project/workstreams/proposed/WS-LRH-CHAIN-DEFAULTS.md` -> moved to
   `project/workstreams/active/` with `status: proposed -> active` and
   `stage: conceived -> executing`, since it already has a resolved work item
   (`WI-LRH-CHAIN-DEFAULTS-INCREMENT-1`) under it and two more (Increment 3,
   Stage 3.5's follow-on) about to land. Updated the corresponding path
   reference in `project/design/proposals/proposed/review-wait-posture/00_proposal.md`.

# Validation

- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- `WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5` (next PR in the sequence).
- `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` (final PR in the sequence, built on top
  of the above).
