---
execution_id: 2026_08_18_22_13_02_LRH_SECRETS_COMMAND_DESIGN_202D8D_REVIEW
prompt_id: PROMPT(AD_HOC:LRH_SECRETS_COMMAND_DESIGN_202D8D_REVIEW)[2026-08-18T21:31:55+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/562
commit: 65cdb3ec7e3cdf6a388cd0400fef9cf63090aed6
created_at: 2026-08-18T22:13:02+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/562
session_transcript: claude-app:d6f0fa6c-efde-4a0e-9394-feecdf190d9e
---

# Summary

Addressed 3 open review comments (`chatgpt-codex-connector`, 2x P1, 1x
P2) on PR #562, run via `/lrh-land`'s inlined Step 4
(`/lrh-review-response`). `rerun_of` is left empty: the branch-slug-based
target-verification search (`UPPER_SLUG=LRH_SECRETS_COMMAND_DESIGN_202D8D`,
derived from this session's auto-named worktree branch
`claude/lrh-secrets-command-design-202d8d`) found no matching candidate,
since the branch name does not follow the `/lrh-implement`
`<username>/<type>/<slug>` convention this lookup assumes. The true
primary record for this PR —
`project/executions/AD_HOC/2026_08_18_21_24_29_LRH_SECRETS_COMMAND.md` —
was identified separately by `/lrh-land` Step 1's own PR-URL-based search,
which is a different algorithm from this skill's branch-slug lookup (see
`/lrh-land/references/land-workflow.md` § A separate, narrower algorithm
for the two slug-based `rerun_of` searches); noted here narratively for
traceability rather than in the `rerun_of` field.

# Result

Fixed all 3 comments in the design-only work-item/proposal text (this PR
has no implementation yet, so "fixing" means correcting the spec):

1. **P1 — literal-string secret verification** (`discussion_r3808027200`):
   `WI-SECRETS-PURGE`'s verification step used `git log --all -S <secret>
   --pickaxe-regex`, which interprets `<secret>` as a regex — a secret
   containing regex metacharacters could produce a false "clean" or an
   invalid-regex abort. Dropped `--pickaxe-regex`; `-S<string>` alone is
   already a literal match. Updated `PROP-LRH-SECRETS-COMMAND` Decision 4
   and `WI-SECRETS-PURGE` Required Changes/Acceptance/Risk Notes
   accordingly.
2. **P1 — runtime-enforce the reviewed-replacements gate**
   (`discussion_r3808027204`): documenting that `--replacements` should be
   `review --apply`'s output was not enforcement — `purge --apply
   --replacements out/replacements.txt` (the unreviewed draft, under any
   filename) was still valid input. Fix: `review --apply` now writes a
   fixed marker line, `# lrh-secrets-reviewed v1`, as the first line of
   `replacements.reviewed.txt`; `purge` hard-fails before any clone if
   that marker is missing, then strips it before the file reaches
   `git-filter-repo`. Updated `PROP-LRH-SECRETS-COMMAND` Decision 3's
   revision, `WI-SECRETS-REVIEW` Required Changes item 1, and
   `WI-SECRETS-PURGE` Required Changes item 1a/Acceptance/Risk Notes.
3. **P2 — real `git-filter-repo` test belongs in the smoke suite**
   (`discussion_r3808027209`): moved the real-binary mirror-clone/verify
   integration test from `tests/secrets_tests/purge_test.py` to a new
   `tests/smoke/secrets_purge_smoke.py`, run via `scripts/smoke`, per
   `AGENTS.md:164-166`'s testing policy (unit tests stay hermetic; real
   install/binary checks go in `tests/smoke/*_smoke.py`). Updated
   `WI-SECRETS-PURGE` Required Changes/Acceptance/Validation/
   `artifacts_expected` and `PROP-LRH-SECRETS-COMMAND`'s Implementation
   Plan accordingly.

Nothing was skipped — all 3 comments passed presence/validity/feasibility
and were fixed.

# Validation

- `lrh validate` — 0 errors, 0 warnings
- `scripts/version tools` — Ruff 0.15.0, Black 25.11.0 confirmed
- `scripts/format --check --diff`, `scripts/lint`, `scripts/test` — not
  run: this round only touched Markdown control-plane files (`00_proposal.md`,
  `WI-SECRETS-PURGE.md`, `WI-SECRETS-REVIEW.md`, `WS-SECRETS-COMMAND.md`),
  no Python files changed, so these are not applicable this round. (Also
  noting for the record: `scripts/format --check --diff` independently
  reported a pre-existing environment tool-version mismatch — required
  Black `26.3.1` vs. installed `25.11.0` — unrelated to this round's
  content, since no Python was touched.)

# Follow-up

- Fixes are design-text corrections only; the marker-line and
  literal-string-verification requirements still need to be implemented
  and tested when `WI-SECRETS-PURGE`/`WI-SECRETS-REVIEW` are built.
- `session_transcript` is populated from `$CLAUDE_CODE_HOST_SESSION_ID`
  for this session; confirm it resolves to a durable pointer if the
  session backend changes.
