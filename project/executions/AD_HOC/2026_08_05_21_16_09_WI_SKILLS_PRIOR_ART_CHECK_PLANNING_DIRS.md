---
execution_id: 2026_08_05_21_16_09_WI_SKILLS_PRIOR_ART_CHECK_PLANNING_DIRS
prompt_id: PROMPT(AD_HOC:WI_SKILLS_PRIOR_ART_CHECK_PLANNING_DIRS)[2026-08-05T13:20:13-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/493
commit: 3355716
created_at: 2026-08-05T21:16:09+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILLS-PRIOR-ART-CHECK-PLANNING-DIRS.md
session_transcript: claude-app:9925d25c-1dab-4b64-bfa1-b484c2fa75fe
---

# Summary

Created `WI-SKILLS-PRIOR-ART-CHECK-PLANNING-DIRS`: fix the shared
`prior-art-check.md` procedure's duplication search to cover
`project/workstreams/` and `project/work_items/`, not just
`project/design/proposals/`. Filed directly following a real incident
(PR #466, closed unmerged) where this gap let a workstream duplicate an
existing sibling workstream without the skill's own check catching it.

# Result

Ran the `/lrh-work-item` skill procedure (invocable this session via the
Skill tool). Confirmed no existing WI/proposal/backlog entry already
requested this fix; found the governing `WS-PRIOR-ART-CHECK` workstream
(resolved) but its Non-Goals cover only automated drift-checking, a
different concern — cited it via `related_workstreams` for lineage rather
than reopening it.

One schema correction made during validation: initially cited
`WS-PRIOR-ART-CHECK` under `related_design` (a workstream path), which
`lrh validate` flagged as `unresolved-metadata-reference` — `related_design`
does not resolve `project/workstreams/` paths. Moved the reference to
`related_workstreams: [WS-PRIOR-ART-CHECK]`, which validated cleanly (the
relation-field validator's `workstream_ids` set spans all status buckets,
not only active/proposed).

Also noted, not fixed here (separate, smaller finding): `/lrh-work-item`'s
own Step 4 documents a `--slug` mode for `lrh prompt check-execution`
(`DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT` / `WI-SLUG-IDEMPOTENCE-CLI-TOOLING`)
that the installed `lrh` CLI does not actually support (`--slug` is not a
recognized argument) — fell back to the manual local-search +
exact-`--prompt-id` check pattern instead. Out of scope for this work item.

Created `project/work_items/proposed/WI-SKILLS-PRIOR-ART-CHECK-PLANNING-DIRS.md`;
opened PR #493.

# Validation

- `lrh validate` — 0 errors, 0 warnings.
- `lrh work-items validate` — 0 errors, 0 warnings for this WI specifically
  (13 pre-existing warnings elsewhere in the repo, unrelated).

# Follow-up

- Run `/lrh-execute WI-SKILLS-PRIOR-ART-CHECK-PLANNING-DIRS` to implement the
  fix (edit the canonical file + 10 synced copies), open the implementation
  PR, and land it end-to-end.
- Separately worth a future look: the `lrh prompt check-execution --slug`
  CLI/doc mismatch noted above.
