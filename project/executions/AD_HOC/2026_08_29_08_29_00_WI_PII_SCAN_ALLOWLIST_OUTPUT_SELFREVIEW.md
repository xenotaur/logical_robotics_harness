---
execution_id: 2026_08_29_08_29_00_WI_PII_SCAN_ALLOWLIST_OUTPUT_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_PII_SCAN_ALLOWLIST_OUTPUT_SELFREVIEW)[2026-08-29T08:28:49+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/650
commit: a5404d88f2ff7795fceb344a31ff02a61e91aa36
created_at: 2026-08-29T08:29:00+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/650
session_transcript: claude-app:cf93c405-ed0f-409d-946f-7451a1cb2f7c
---

# Summary

Diff-mode `/lrh-self-review` pass on the `WI-PII-SCAN-ALLOWLIST-OUTPUT`
implementation (`src/lrh/pii/allowlist.py`, `src/lrh/pii/output.py`, the
`content_digest` extension to `src/lrh/pii/layer2.py`, and their tests),
run from `/lrh-implement` Step 7.5 before the PR's first push.
`rerun_of` is empty by construction — this pass ran before the primary
implementation record existed.

# Result

Dispatched a cold-context `general-purpose` subagent against the branch
diff (`git diff <merge-base-with-origin/main>`, not bare `main`, since
this worktree's local `main` ref is stale — it is never updated here
because `main` stays checked out in the primary worktree), with the WI
spec and the touched/referenced modules as orientation. It
found and reproduced one real bug: `output.build_findings` grouped Layer
1's per-commit results (from `enumerate_commits_for_paths`) by their
*historical* path name but looked them up by the finding's *current*
path, silently dropping every commit reached only under a pre-rename
name.

Independently re-verified the finding myself (mandatory Step 4) by
building a scratch repo (add `notes.txt` → rename to `passport.pdf`) and
confirming `build_findings` returned only the rename commit — the add
commit and its `content_digest` were missing entirely from output.
Confirmed the bug was real, then fixed it in `output.py` by querying
`enumerate_commits_for_paths` once per Layer 1 finding (instead of
batching across all findings and re-grouping by historical path
afterward) and using the historical path name — not the current/
canonical name — for the blob-SHA lookup. Re-verified the fix resolves
it: both commits now appear, with matching `content_digest` (content was
unchanged across the rename) and correct `still_in_working_tree` flags.
Added a regression test
(`test_layer1_finding_keeps_pre_rename_commits_not_only_post_rename`).

Re-ran the full validation sequence after the fix (per this skill's Step
7.5 instruction to re-validate when fixes are applied): 29/29 targeted
tests pass, full suite 1502 tests OK, format/lint clean, `lrh validate`
clean. Proceeded to push regardless of the finding, per Decision 4 — the
PR's first real bot round still runs next.

# Validation

- `tests.pii_tests.allowlist_test`, `tests.pii_tests.output_test`,
  `tests.pii_tests.layer2_test` — 29/29 pass (re-run after the fix).
- Full suite — 1502 tests, OK.
- `lrh validate` — 0 errors (1 pre-existing unrelated warning).
- Independent re-verification of the finding, performed by the invoking
  session directly (scratch-repo reproduction before and after the fix).

# Follow-up

- None. The PR's first real bot review round runs next per
  `/lrh-implement` Step 8, unaffected by this pass's findings.
