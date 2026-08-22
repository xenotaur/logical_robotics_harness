---
resolution: "Implemented and merged in PR #601 (commit 834ac0a9): assessed and removed the orphaned disable-model-invocation flag, added when_to_use guidance and a confirm-before-write gate, committed a persistent Codex openai.yaml, propagated to all corpora."
blocked_reason: null
blocked: false
id: WI-CODEX-EXPORT-INVOCATION-FLAG-REMOVAL
title: Remove disable-model-invocation flag from lrh-codex-export
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-INVOCATION-AND-GATE-RESET
related_design:
  - project/memory/decisions/DEC-SELF-REVIEW-RECURSION-GUARD.md
depends_on:
  - WI-DELIBERATE-MODEL-INVOCATION
  - WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - promote_reference_skills
acceptance:
  - A recorded assessment states explicitly why lrh-codex-export does or does not need a platform-enforced recursion guard analogous to lrh-self-review's, grounded in the skill's actual dispatch/chain behavior rather than assumed from precedent
  - If the flag is removed, when_to_use guidance is added narrowing invocation to explicit user requests, consistent with the skill's existing privacy and safety posture
  - A persistent src/lrh/skills/lrh-codex-export/agents/openai.yaml with policy.allow_implicit_invocation:false is committed to source before or alongside the flag removal, verified to survive a fresh lrh skills install --target codex (which shutil.rmtree's the installed skill directory and only regenerates agents/openai.yaml from source, not by deriving it from disable-model-invocation once that flag is gone)
  - disable-model-invocation is absent from the source and all installed-corpus mirrors (.claude/skills/, .agents/skills/, .gemini/plugins/lrh/skills/), and from repo-local and user-scope Claude/Codex/Antigravity installs, not just the source tree
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/lrh-codex-export/SKILL.md
  - src/lrh/skills/lrh-codex-export/agents/openai.yaml
  - .claude/skills/lrh-codex-export/SKILL.md
  - .agents/skills/lrh-codex-export/SKILL.md
  - .agents/skills/lrh-codex-export/agents/openai.yaml
  - .gemini/plugins/lrh/skills/lrh-codex-export/SKILL.md
---

# Remove disable-model-invocation flag from lrh-codex-export

## Summary

`src/lrh/skills/lrh-codex-export/SKILL.md` still carries `disable-model-invocation: true`,
unlike the 9 skills `WI-DELIBERATE-MODEL-INVOCATION` already cleared to
`when_to_use` guidance and the 4 skills
`WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE` closed out with the same
treatment (`lrh-self-review` additionally got a platform-enforced recursion
guard, `DEC-SELF-REVIEW-RECURSION-GUARD`). This work item makes the same
evaluation for `lrh-codex-export` and, if no gap justifies keeping the flag,
removes it following the established pattern.

## Problem / Context

`lrh-codex-export` was added later, in PR #532, after
`WI-DELIBERATE-MODEL-INVOCATION`'s scope was already fixed at 13 flagged
skills (9 cleared, 4 deliberately retained). It was never evaluated by that
work item or by its Stage 2 completion follow-up — not a deliberate
retention, an orphan by omission. Nothing currently blocks legitimate
invocation of this skill from being flagged the same stochastic way the
other 13 skills were before their own resolutions (`00_proposal.md:62-79`
documents the general failure mode: the flag blocks mid-sentence compound
instructions and one skill offering another, not just malicious invocation).

### Prior Art Check

**Duplication search.** No existing work item owns this. `git grep -rl "lrh-codex-export" project/design/proposals/ project/workstreams/` finds
only `lrh-codex-export`'s own origin proposal/workstream
(`WS-LRH-CODEX-APP-SERVER-EXPORT`, resolved) — neither mentions the flag.
`project/design/backlog.md` has no entry.

**Demand search.** Demand is implicit in the same policy
`WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE` and
`DEC-SELF-REVIEW-RECURSION-GUARD` already established for this family of
skills — no explicit backlog/proposal entry names `lrh-codex-export`
specifically.

**Recommendation.** Proceed as a small, standalone item, matching the
pattern used for the self-review recursion guard (PR #566): assess the
actual risk first, don't assume the precedent transfers uncritically.

## Scope

- Assess `lrh-codex-export` for any gap analogous to what justified
  retaining the flag on the 4 originally-retained skills: subagent
  dispatch/recursion risk (`lrh-self-review`), an ungated fast path
  (`lrh-confirm-fixes`), or an unverified consent path
  (`lrh-land`/`lrh-execute`). The skill as currently written is a
  single-shot CLI wrapper (`lrh conversation export-codex-thread` /
  `inspect-export`) with no subagent dispatch, no chain authorization gate,
  and no merge/closeout step — structurally closer to the 9 already-cleared
  skills than the 4 retained ones, but this must be confirmed explicitly
  against the skill's actual current text, not assumed from that summary.
- If the assessment finds no unmitigated gap: remove the flag and add
  `when_to_use` guidance.
- If the assessment finds a real gap: keep the flag, record why explicitly
  (a governing note or DEC), and do not remove it as part of this item —
  same discipline `WI-DELIBERATE-MODEL-INVOCATION`'s own acceptance
  criteria used for the 4 skills it retained.
- Propagate any change to all installed corpora: `.claude/skills/`,
  `.agents/skills/`, `.gemini/plugins/lrh/skills/` (Antigravity), and
  repo-local plus user-scope Claude/Codex/Antigravity installs via
  `lrh skills install`.

## Required Changes

1. Read `src/lrh/skills/lrh-codex-export/SKILL.md` in full against the
   recursion/gap criteria above and record the assessment's conclusion
   explicitly.
2. If clear to remove: delete `disable-model-invocation: true`, add
   `when_to_use` guidance narrowing invocation to explicit user requests
   (matching the skill's existing Safety Rules posture around explicit
   thread IDs and private data handling).
3. **Before or alongside step 2, commit a persistent
   `src/lrh/skills/lrh-codex-export/agents/openai.yaml`** with
   `policy.allow_implicit_invocation: false`, matching the pattern already
   committed at `src/lrh/skills/lrh-self-review/agents/openai.yaml`. This is
   required, not optional: `_copy_skill_from_source`
   (`src/lrh/skills/installer.py`) `shutil.rmtree`s the entire installed
   skill directory before rewriting it, and `CodexSkillRenderer` only
   regenerates `agents/openai.yaml` when source `disable-model-invocation`
   is `True` — today that file exists only as an installer-derived artifact
   at `.agents/skills/lrh-codex-export/agents/openai.yaml`, with no source
   copy. Removing the flag without first committing a persistent source
   copy means the next `lrh skills install --target codex` silently deletes
   the file and permits implicit invocation of a privacy-sensitive exporter.
4. Run `lrh skills install` for `--target claude|codex|antigravity` with
   both `--local` and `--scope user`, and verify both the flag's absence
   and `agents/openai.yaml`'s presence in each resulting Codex corpus, not
   just `src/`.
5. Record the decision — a short note or DEC entry, whichever this
   project's promotion bar calls for given the size of the change.

## Non-Goals

- Does not touch the 4 skills `WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE`
  already resolved.
- Does not re-open or expand `WI-GATE-POLICY-CASCADE-STAGE3`'s scope.
- Does not modify the underlying CLI exporter, its privacy rules, or its
  Safety Rules section.
- Does not assume the flag should be removed — the assessment in Required
  Changes step 1 is a real decision point, not a formality.
- **Registration status update (2026-08-21, confirm-fixes round 2):** this
  WI was initially left out of `WS-INVOCATION-AND-GATE-RESET`'s
  `work_items:` list (review-flagged, PR #571, Codex P2) with a stated
  rationale that `WI-GATE-POLICY-CASCADE-STAGE3`'s implementation, PR #577,
  was concurrently open and touching the same workstream file. That
  rationale was stale the moment it was written — `gh pr view 577` shows
  PR #577 merged at `2026-08-21T15:57:07Z`, roughly 17 minutes before the
  commit that added the deferral text. A substitute `/lrh-self-review`
  pass caught the discrepancy; the WI has now been registered in
  `WS-INVOCATION-AND-GATE-RESET`'s `work_items:` list, appended after the
  Stage 5-7 item since it is a side-fix outside the sequential Stage 1-7
  plan, not part of it.

## Acceptance Criteria

Consult the `acceptance:` frontmatter field, which is the authoritative
list.

## Validation

- `lrh validate`
- `PYTHONPATH=src python -m lrh.cli.main skills check --target all --local`
- `scripts/format --check --diff`
- `scripts/lint`

## Risk Notes

- `lrh-codex-export` handles private conversation transcript data — even
  though this item's own scope is invocation-policy only, do not let a
  `when_to_use` rewrite loosen any of the skill's existing Safety Rules
  around not printing transcript text or committing raw captures.
- If the assessment in Required Changes step 1 finds a real gap, resist the
  urge to remove the flag anyway "for consistency" with the other 13 skills
  — that is exactly the premature-removal mistake this program's own
  history (`DEC-SELF-REVIEW-RECURSION-GUARD`) already had to correct once.
