---
execution_id: 2026_08_29_16_54_07_EXECUTE_EARLY_CREATION_PR_CHECK
prompt_id: PROMPT(WI-EXECUTE-EARLY-CREATION-PR-CHECK:EXECUTE_EARLY_CREATION_PR_CHECK)[2026-08-29T15:54:22+00:00]
work_item: WI-EXECUTE-EARLY-CREATION-PR-CHECK
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/651
commit: e540c8883084965c80c583767d8a870c3f5e9e95
created_at: 2026-08-29T16:54:07+00:00
agent: claude_code
instruction_source: project/work_items/proposed/WI-EXECUTE-EARLY-CREATION-PR-CHECK.md
session_transcript: claude-app:local_02330303-d423-49f8-9864-aeac6023c0b9
---

# Summary

Implemented `WI-EXECUTE-EARLY-CREATION-PR-CHECK`: added a precondition
check to `/lrh-execute` Step 1 that verifies the target `WI-ID`'s own
file exists on `origin/main` before running readiness, closing the gap
where a local checkout still sitting on an unmerged WI-creation branch
would report a false-confidence `prompt_ready: yes`.

# Result

Edited `src/lrh/skills/lrh-execute/SKILL.md` Step 1: added the creation-PR
existence check (`git ls-tree -r --name-only origin/main --
project/work_items/`) to the `WI-ID` branch as a hard stop, and to the
`WS-ID` branch as a skip-and-continue ineligibility condition (per the
next-ready-WI selection rule -- aborting the whole run on the first
blocked candidate would incorrectly exclude a later, fully-ready
candidate). Added a new reference doc,
`src/lrh/skills/lrh-execute/references/creation-pr-check.md`, documenting
the full rationale and a best-effort PR-naming mechanism for the stop
message.

**Algorithm reuse vs. adaptation** (per this WI's acceptance criteria):
the existence check itself is *not* modeled on `/lrh-land`'s primary-record
provenance-check algorithm -- that algorithm exists to disambiguate which
of several execution records is primary for an *already-known* PR, a
genuinely hard problem; this check's question ("does this exact, known
file exist at this exact ref") has no equivalent ambiguity, so `git
ls-tree` against `origin/main` is used directly as ground truth. What *is*
reused is the algorithm's underlying principle -- gather broadly, narrow
to an exact match, never guess when ambiguous -- applied to the
best-effort PR-naming enrichment: anchored on `/lrh-work-item`'s own
`instruction_source: project/work_items/<bucket>/<WI-ID>.md` convention
(an exact-match anchor, verified against all 82 real occurrences in
`project/executions/AD_HOC/` before relying on it) rather than a
branch-derived slug glob, since no branch exists yet at `/lrh-execute`
Step 1.

Propagated to the `.claude/`, `.agents/`, and `.gemini/` mirrors via `lrh
skills install --local --target all --source current-repo --force`.
That command also surfaced ~18 files of **pre-existing, unrelated** mirror
drift (confirmed via `git log` timestamps: `src/` files last touched by
recent PRs while their mirror counterparts were untouched since as far
back as 2026-08-22) spanning several other skills, including
`lrh-implement`, which this WI's `forbidden_actions` explicitly bars
touching. Left those files unstaged and uncommitted in the working tree
rather than committing them or discarding them (`git checkout --` was
blocked by this session's permission policy) -- they remain as harmless,
unpushed local noise; only the intended `lrh-execute`-scoped files were
staged and committed.

A proactive diff-mode `/lrh-self-review` pass ran before this PR's first
push (see the companion `_SELFREVIEW` execution record) and came back
clean.

# Validation

- `scripts/version tools`: pyright not installed (pre-existing environment
  gap, unrelated to this markdown-only change)
- `lrh validate`: 0 errors (1 pre-existing, unrelated warning in a
  different WI file, `WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT.md`)
- `scripts/format --check --diff`: clean, 241 files unchanged
- `scripts/lint`: all checks passed
- `scripts/test`: 1493 tests, OK
- Mirror consistency: all 4 copies of the new reference doc verified
  byte-identical via direct `diff`; `SKILL.md` mirrors differ only in
  pre-existing YAML frontmatter style, not content

# Follow-up

None outstanding from implementation. Next: PR review/confirm-fixes/merge/
closeout via the inlined `/lrh-land` chain.
