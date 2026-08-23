---
execution_id: 2026_08_23_04_17_54_WI_PII_SCAN_LAYER1_ENUMERATOR
prompt_id: PROMPT(WI-PII-SCAN-LAYER1-ENUMERATOR:WI_PII_SCAN_LAYER1_ENUMERATOR)[2026-08-22T20:00:20+00:00]
work_item: WI-PII-SCAN-LAYER1-ENUMERATOR
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/616
commit: pending
created_at: 2026-08-23T04:17:54+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-PII-SCAN-LAYER1-ENUMERATOR.md
session_transcript: "claude-app:cf93c405-ed0f-409d-946f-7451a1cb2f7c"
---

# Summary

Implemented `WI-PII-SCAN-LAYER1-ENUMERATOR` via `/lrh-execute`'s inlined
`/lrh-implement`: the git-plumbing full-history path enumerator, `.lrh-pii.toml`
config auto-discovery, and the Layer 1 file-type/path/filename detector.

# Result

Created `src/lrh/pii/enumerate.py` (`enumerate_added_paths`,
`enumerate_commits_for_paths` — the latter taking an arbitrary path set
per the PR #596 review requirement), `src/lrh/pii/config.py` (`.lrh-pii.toml`
auto-discovery, `[extend] useDefault = true` semantics, disclosed
defaults), and `src/lrh/pii/layer1.py` (glob/keyword heuristic detector).
Added `tests/pii_tests/{enumerate,config,layer1}_test.py` (20 tests).

**Pre-push self-review (Step 7.5) found and fixed two real issues before
this ever reached a PR:**

1. Both `git log` invocations lacked `-m`, so a path introduced only by
   a merge commit's own tree (git suppresses merge-commit diffs by
   default) was invisible to both enumeration functions — verified
   independently against a scratch repo (a file existed in the actual
   tree but neither function found it). Fixed by adding `-m`. This
   surfaced a second bug: `--follow -m` together can report the same
   commit twice (once per differing parent) — fixed by deduplicating per
   path in `enumerate_commits_for_paths`.
2. `layer1.flag_path`'s glob matching was case-sensitive on POSIX
   (`fnmatch.fnmatch`'s case-folding is a no-op there), unlike the
   already-case-insensitive keyword matching — verified independently
   (`fnmatch.fnmatch('Statement.PDF', '*.pdf')` returns `False`). Fixed
   by lowercasing both sides before matching.

Both fixes are covered by new tests. Pushed as commit in PR #616.

# Validation

- `PYTHONPATH=<worktree>/src python -m unittest discover -s tests -p
  '*_test.py'` — 1322 tests, OK (post-fix).
- `scripts/format --check --diff` / `scripts/lint` — clean (after
  re-fixing tool-version drift, reset by a concurrent session in this
  shared conda environment multiple times during this work).
- `lrh validate` — 0 errors, 0 warnings.
- Independent cold-context self-review (diff-mode, mandatory per
  `/lrh-implement` Step 7.5) — 2 findings, both independently
  re-verified by the invoking session directly (scratch-repo
  reproduction for the merge-commit gap, direct `fnmatch` check for the
  case-sensitivity gap) before fixing.

# Follow-up

- Run `/lrh-review-response`/`/lrh-confirm-fixes` on PR #616, then merge
  and `/lrh-closeout` to resolve `WI-PII-SCAN-LAYER1-ENUMERATOR`.
- `WI-PII-SCAN-LAYER2-CONTENT` depends on this item and
  `WI-PII-SCAN-RULE-TAXONOMY` (already merged) — both dependencies will
  be satisfied once this PR merges.
