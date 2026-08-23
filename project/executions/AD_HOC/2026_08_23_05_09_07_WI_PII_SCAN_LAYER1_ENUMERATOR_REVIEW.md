---
execution_id: 2026_08_23_05_09_07_WI_PII_SCAN_LAYER1_ENUMERATOR_REVIEW
prompt_id: PROMPT(AD_HOC:WI_PII_SCAN_LAYER1_ENUMERATOR_REVIEW)[2026-08-23T05:02:24+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_23_04_17_54_WI_PII_SCAN_LAYER1_ENUMERATOR
pr: https://github.com/xenotaur/logical_robotics_harness/pull/616
commit: 923d9c26a60defbe77aadab3dca8e448b031a929
created_at: 2026-08-23T05:09:07+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/616
session_transcript: claude-app:cf93c405-ed0f-409d-946f-7451a1cb2f7c
---

# Summary

Addressed seven open review comments from `chatgpt-codex-connector` and
`copilot-pull-request-reviewer` on PR #616 (`WI-PII-SCAN-LAYER1-ENUMERATOR`),
via `/lrh-execute`'s inlined `/lrh-land`/`/lrh-review-response` protocol.

Note on `rerun_of`: linked to the implementation primary record
(`pr: #616`), not the same-slug creation record under `AD_HOC`
(`pr: #596`) — same slug collision pattern documented for
`WI-PII-SCAN-RULE-TAXONOMY`'s review round on PR #604.

# Result

Triaged seven comments, six valid and fixed, one deliberately deferred:

1. **Rename destinations invisible to Layer 1** (P1) — `enumerate_added_paths`
   only reported add-time names via `--diff-filter=A`, so a benign path
   renamed to a suspicious one (e.g. `notes.txt`→`passport.pdf`) never
   reached Layer 1. Fixed: `--diff-filter=AR --name-status --find-renames`,
   reporting the rename destination.
2. **Stale caller path stamped on historical commits** (P1) —
   `enumerate_commits_for_paths` always used the caller's input path for
   every returned commit, breaking `git show <commit>:<path>` for
   pre-rename commits where that path didn't exist yet. Fixed: parses
   `--name-status` per commit and reports the path as it actually existed
   at that commit.
3. **Path globs matched basename only** (P2, plus a duplicate from
   copilot) — a directory-qualified rule like `private/*.txt` could never
   match. Fixed: glob matching now runs against the full normalized path;
   filename-keyword matching stays basename-only.
4. **Fixture repos not pinned to `main`** (P1) — tests assumed
   `init.defaultBranch=main` and explicitly `checkout main`; fails on
   systems defaulting to `master`. Fixed: `git init -q -b main` explicit.
5. **`load_config` doesn't validate TOML types** — could crash downstream
   (e.g. `glob.lower()` on a non-string). Fixed: validates `useDefault` is
   a bool and both lists are lists of strings, raising `PiiConfigError`.
6. **`enumerate_commits_for_paths` is O(n) subprocesses** — deliberately
   deferred and disclosed in the docstring rather than fixed, matching
   this work item's own pre-existing Risk Notes on untested large-repo
   performance.

Fixing #1 and #2 surfaced a new bug during implementation: `--follow -m`
together can report the same commit twice for a rename commit (once per
differing parent) — fixed by deduplicating per path, independently
re-verified against a scratch repo before committing.

Pushed as commit `2ef795d4` to the open PR branch.

# Validation

- `PYTHONPATH=<worktree>/src python -m unittest tests.pii_tests.enumerate_test tests.pii_tests.config_test tests.pii_tests.layer1_test -v` — 25 tests, OK.
- Full suite: `PYTHONPATH=<worktree>/src python -m unittest discover -s tests -p '*_test.py'` — 1327 tests, OK.
- `scripts/format --check --diff` / `scripts/lint` — clean (after
  re-fixing tool-version drift, reset again by a concurrent session in
  this shared conda environment).
- `lrh validate` — 0 errors, 0 warnings.
- All rename/merge/glob fixes independently verified against scratch git
  repos before landing (empirical git-command verification, not just
  code inspection).

# Follow-up

- Run `/lrh-confirm-fixes` against PR #616 to verify these fixes and
  resolve the review threads.
