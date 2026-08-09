---
execution_id: 2026_08_09_04_20_06_WI_DELIBERATE_MODEL_INVOCATION
prompt_id: PROMPT(WI-DELIBERATE-MODEL-INVOCATION:WI_DELIBERATE_MODEL_INVOCATION)[2026-08-09T03:55:48+00:00]
work_item: WI-DELIBERATE-MODEL-INVOCATION
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/533
commit:
agent: claude_app
instruction_source: project/work_items/proposed/WI-DELIBERATE-MODEL-INVOCATION.md
session_transcript: pending
created_at: 2026-08-09T04:20:06+00:00
---

# Summary

Implements `WI-DELIBERATE-MODEL-INVOCATION`'s Required Changes: removes
`disable-model-invocation` from the 9 tier-1/2/3 skills whose gate
placement was audited and confirmed sufficient, adding a tiered
`when_to_use` to each; leaves the 4 excluded skills (`lrh-self-review`,
`lrh-confirm-fixes`, `lrh-land`, `lrh-execute`) untouched, each for a
specific tracked gap; cascades the resolution into `_shared/lifecycle-chain.md`,
`lrh-create-skill`'s authoring guidance, and `project/executions/README.md`.

# Result

- Removed `disable-model-invocation: true` and added a tiered `when_to_use`
  in both `src/lrh/skills/` and `.claude/skills/` for: `lrh-closeout`,
  `lrh-create-skill`, `lrh-design`, `lrh-doc-audit`, `lrh-doc-organize`,
  `lrh-doc-work`, `lrh-implement`, `lrh-readiness`, `lrh-review-response`.
  Each `when_to_use` cites the skill's actual confirm-gate step number,
  cross-checked against the skill's own `### Step N` heading.
- Did not touch `lrh-self-review`, `lrh-confirm-fixes`, `lrh-land`,
  `lrh-execute` — each keeps the flag per the WI's tier 2a/2b/3a exclusions.
- `_shared/lifecycle-chain.md`: replaced the now-false "most skills carry
  the flag" claim and the "flag blocks invoking them" inlining rationale
  with the tiered resolution, cross-linked to
  `DEC-DELIBERATE-CHAIN-INITIATION.md`'s dated 2026-08-08 Consequences entry.
- Rewrote `lrh-create-skill/references/{lrh-skill-pattern.md,frontmatter-guide.md,worked-example.md}`
  so new skills don't default to the flag for "high-consequence" work —
  including fixing `worked-example.md`'s own contrast table, which had
  cited `lrh-create-skill` itself as needing the flag (now stale, since
  this PR removes it from `lrh-create-skill`).
- Added a CHAIN-NOTE placement / find-or-backfill section to
  `project/executions/README.md`, cross-referencing
  `lrh-land/references/land-workflow.md`'s canonical format tables rather
  than duplicating them.
- `installer.py`: **superseded by Round 2 below** — the initial
  verification (this bullet, originally) concluded no code change was
  needed for `disable-model-invocation`/preload behavior, which held. But
  the automatic first-push review caught a real, separate `installer.py`
  gap this initial pass missed: `when_to_use` wasn't in
  `CodexSkillRenderer._CODEX_STRIPPED_FRONTMATTER_KEYS`, so it survived
  into Codex-rendered frontmatter and broke Codex's own schema validation.
  Fixed in Round 2.

## Round 2 — review findings and fixes (commit `75e833ce`)

PR #533's automatic first-push review (Codex + Copilot) surfaced two real
findings:

- Codex (P1) — `CodexSkillRenderer` stripped `argument-hint` and
  `disable-model-invocation` for Codex installs but not `when_to_use`,
  which Codex's own frontmatter schema doesn't recognize; installing any
  of the newly `when_to_use`-carrying skills to a Codex target produced an
  invalid `SKILL.md`. Pre-existing gap (predates this PR — `lrh-work-item`/
  `lrh-proposal`/`lrh-workstream` already had `when_to_use` with no flag),
  but this PR's 9 additional skills raised it from 3 affected skills to
  12. **Fixed**: added `when_to_use` to
  `_CODEX_STRIPPED_FRONTMATTER_KEYS`, plus a dedicated regression test
  (`test_codex_target_strips_when_to_use_without_disable_model_invocation`)
  covering the no-flag case this PR's pattern uses.
- Copilot (P2) — `lrh-create-skill/SKILL.md`'s own body (not just its
  `references/` files) still framed `disable-model-invocation` as the
  direct answer to "should this skill be explicit-only" in its Step 2
  interview question, Step 7 frontmatter checklist, and final Quality
  Checklist — contradicting the tiered guidance this PR wrote into
  `references/lrh-skill-pattern.md`. **Fixed**: rewrote all three sites to
  point authors at `when_to_use` + the confirm gate first, reserving the
  flag for a specific confirmed gap.

Both threads resolved via `resolveReviewThread`. Full test suite re-run
after a tool-version drift (`scripts/develop` re-run per
`feedback_codex_tool_env_can_revert_midrun`): 1066 tests, OK.

## Round 3 — final self-review pass (commit `24ea1985`)

`git diff --check origin/main...HEAD` flagged trailing whitespace on two
blank frontmatter lines (`rerun_of:`, `commit:`) in this very record —
fixed directly. A cold-context self-review subagent confirmed the fix was
clean and, independently, caught that this Result section's original
`installer.py` bullet (above) was now stale relative to Round 2's actual
change — corrected in place rather than left contradicting Round 2.

# Validation

- `lrh validate` — 0 errors (1 pre-existing, unrelated warning), all three
  rounds
- `lrh work-items validate` — no findings
- `scripts/test` — 1065 tests OK (round 1), 1066 tests OK (rounds 2–3,
  after the new installer regression test)
- `scripts/format --check --diff`, `scripts/lint` — clean (2 pre-existing,
  unrelated lint errors in `tests/conversations_tests/antigravity_export_test.py`,
  confirmed present on `main` before this branch via `git stash`)
- `diff -r src/lrh/skills/<name>/ .claude/skills/<name>/` — clean for all
  9 edited skills and the 3 edited `lrh-create-skill` reference files
- `git diff --check origin/main...HEAD` — clean as of round 3
- `/lrh-self-review` — three passes: diff-mode before first push (Step
  7.5), PR-mode after round 2's fixes, PR-mode final pass after round 3's
  whitespace fix. Each independently re-verified its own top finding
  directly rather than accepting the subagent's report — one finding
  (a subagent's `lrh validate` "35 errors" claim, PR #518's own self-review,
  not this PR) was caught not holding up under re-verification; the
  installer.py staleness finding above (this PR) did hold up and was fixed.
- CI (`coverage`, `tests`, `installed-wheel-smoke`, `lint`,
  `Check workflow files`) — green on the final commit; round 1's CI showed
  `tests`/`coverage`/`lint` failing from a pre-existing, unrelated `main`
  break (PR #526's `antigravity_export_test.py` imports `pytest`, not a
  CI dependency) that resolved itself by round 3 without action here

# Follow-up

- Not this WI (tracked separately): add a diff-mode confirm gate to
  `lrh-self-review` before its flag can be removed; add a confirm step to
  `lrh-confirm-fixes`'s empty-thread fast path before its flag can be
  removed; design a way to verify a genuine human-typed slash-command
  invocation (or restrict `skip_if_opted_in`) before `lrh-land`/`lrh-execute`
  can drop theirs.
- `session_transcript: pending` should be updated to
  `claude-app:<host-uuid-stem>` after the session ends.
