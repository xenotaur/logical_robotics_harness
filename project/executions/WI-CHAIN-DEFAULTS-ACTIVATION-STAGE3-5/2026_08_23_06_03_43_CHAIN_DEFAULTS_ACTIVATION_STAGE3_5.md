---
execution_id: 2026_08_23_06_03_43_CHAIN_DEFAULTS_ACTIVATION_STAGE3_5
prompt_id: PROMPT(WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5:CHAIN_DEFAULTS_ACTIVATION_STAGE3_5)[2026-08-23T05:41:29+00:00]
work_item: WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5
status: landed
rerun_of: 
agent: claude_app
instruction_source: project/work_items/proposed/WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5.md
session_transcript: claude-app:81eca1c8-36fa-493d-b0e5-08c0501ec1d0
pr: https://github.com/xenotaur/logical_robotics_harness/pull/618
commit: 3c0b590f7b9c341781194158e7046838926a54e3
created_at: 2026-08-23T06:03:43+00:00
---

# Summary

Activates the chain-defaults `skip_if_opted_in` mechanism under the Stage
3.5 compensating control (`human_initiated_invocation_evidence`,
`DEC-GATE-POLICY-CASCADE` Decision 4), per
`WI-CHAIN-DEFAULTS-ACTIVATION-STAGE3-5`. Run as part of an `/lrh-execute`
chain (third of a planned 1-2-3 PR sequence: housekeeping fixes -> this ->
`WI-LRH-CHAIN-DEFAULTS-INCREMENT-3`).

# Result

Verified `human_initiated_invocation_evidence` is present, named, and
checkable in `DEC-GATE-POLICY-CASCADE.md` (Decision point 4, five
sub-checks). Wired it into the `skip_if_opted_in` eligibility text in both
`src/lrh/skills/_shared/chain-defaults.md` (canonical) and
`src/lrh/skills/lrh-land/references/land-workflow.md` (its full inlined
copy) as a new "requirement 6," additional to `DEC-CHAIN-INIT-SKIP-CONSENT`'s
existing five requirements, not a replacement for any of them. Missing
evidence falls back to `always_confirm` for that run only, per the DEC's own
"does not block the run" language.

`project/config/chain-defaults.yaml` left untouched: `chain_init_confirmation`
stays `always_confirm`; `skip_if_opted_in` is not shipped as the default
configuration (acceptance criterion satisfied trivially by not changing it).
`confirmed_commit`/`confirmed_at` are runtime-managed fields stamped by the
existing propose-and-confirm flow on live confirmation, not something this
diff needed to hand-edit.

Propagated the edited `land-workflow.md` into `.claude/skills/lrh-land/`
and `.agents/skills/lrh-land/`; verified byte-identical via `diff` after
propagation.

`/lrh-self-review` diff-mode pass (execution record:
`2026_08_23_06_02_17_CHAIN_DEFAULTS_ACTIVATION_STAGE3_5_SELFREVIEW`) found
two non-blocking prose issues in the new text (a circular ordering claim, a
duplicated clause) -- both fixed before push -- and flagged a fourth mirror
(`.gemini/plugins/lrh/skills/lrh-land/references/land-workflow.md`, not
named in this WI's `artifacts_expected`) as pre-existing drift. **That
pre-existing-drift claim was wrong** -- caught by `chatgpt-codex-connector`'s
review on the resulting PR #618: `.gemini` and `src` were byte-identical at
the parent commit, so this diff introduced the drift, not inherited it.
Fixed in the review-response round: synced `.gemini`'s copy to match; see
that round's own execution record.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `scripts/format --check --diff` / `scripts/lint`: pre-existing environment
  tool-version mismatch (black 25.11.0 vs. required 26.3.1; ruff 0.15.0 vs.
  required 0.15.12), unrelated to this markdown-only change -- same
  environment issue seen on PR #609 in this same session.
- Mirror parity: `diff` confirms `src/lrh/skills/lrh-land/references/land-workflow.md`
  matches `.claude/skills/lrh-land/references/land-workflow.md` and
  `.agents/skills/lrh-land/references/land-workflow.md` exactly.

# Follow-up

- Report restart requirement: any in-flight `/lrh-land`/`/lrh-execute`
  session must restart to pick up this change, since the propose-and-confirm
  flow is inlined text read at skill-invocation time, not re-read mid-run.
