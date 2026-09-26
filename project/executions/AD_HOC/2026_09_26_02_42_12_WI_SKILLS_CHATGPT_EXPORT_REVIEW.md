---
execution_id: 2026_09_26_02_42_12_WI_SKILLS_CHATGPT_EXPORT_REVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_CHATGPT_EXPORT_REVIEW)[2026-09-26T02:38:01+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_09_26_01_04_09_WI_SKILLS_CHATGPT_EXPORT_REVIEW
pr: https://github.com/xenotaur/logical_robotics_harness/pull/720
commit:
created_at: 2026-09-26T02:42:12+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/720
session_transcript: pending
---

# Summary

Third review-response round for PR #720, addressing the P3 non-thread
findings from the round-2 substitute self-review
(`2026_09_26_01_59_18_WI_SKILLS_CHATGPT_EXPORT_CONFIRM_SELFREVIEW`) on
`_CONFIRM` HEAD `e30a713a`. Same-land-run continuation of the round-2
`_REVIEW` record authored earlier in this session; the user chose "fix now"
and confirmed the edit list live.

# Result

Fix commit: `9e31cc383a352bd4588727cbe32bd56fe1ca0362`.

- **Nit 1 (fixed):** WI frontmatter `acceptance:` now matches the body —
  added a capability-dependent compatibility-notice item, added capability
  notices and CLI argument/reporting behavior to the tests item, and the
  validation item now names `scripts/format --check --diff`, `scripts/lint`,
  `scripts/test`, and `lrh validate`.
- **Nit 2 (fixed):** Required Change 8 and the body Acceptance Criteria test
  line now require tests that capability-dependent skills produce the
  compatibility notice without workflow rewriting.
- **Nit 3 (fixed):** Required Change 3 now says a canonical
  `agents/openai.yaml` is not copied into the ChatGPT bundle but is still read
  to detect manual-only skills; Required Change 4 notes `agents/` is not part
  of the bundle; Required Change 8 tests the exclusion.
- **Nit 4 (fixed, user decision):** adopted proposal
  `implementation_status: implemented` → `partial` (repo precedent for a
  scheduled-but-unbuilt stage). `implemented_by` unchanged — it lists
  implemented WIs; `WI-SKILLS-CHATGPT-EXPORT` joins it at its own closeout.
- **Nit 5a (fixed):** Required Change 9 now calls out correcting the how-to
  guide's "Extending for Other Assistants" section, which says ChatGPT would
  be added via `lrh skills install --target <name>`.
- **Nit 5b (skipped — scope):** stale proposal-set `README.md` status
  predates this PR.
- **Nit 5c (skipped — validity):** the round-2 `_CONFIRM` and `_REVIEW`
  records' differing `rerun_of` targets each follow their own skill's
  documented rule.

# Validation

- `scripts/test` with `PYTHONPATH=<checkout>/src`: 1718 tests, OK.
- `lrh validate` (this checkout's source): 0 errors, 0 warnings.
- `lrh work-items readiness WI-SKILLS-CHATGPT-EXPORT`: ready.
- `scripts/format`/`scripts/lint` not runnable locally (black 25.11.0 vs.
  pinned 26.3.1); diff is Markdown-only; CI's pinned lint job is the
  evidence. No config bypass used.

# Follow-up

Reply on the PR citing the fix commit, then run confirm-fixes round 3 and a
round-3 substitute self-review on the new `_CONFIRM` HEAD.
