---
execution_id: 2026_08_09_19_57_46_WI_SIBLING_REPO_VALIDATE_CI_AND_CONTRIBUTOR_IDS
prompt_id: PROMPT(AD_HOC:WI_SIBLING_REPO_VALIDATE_CI_AND_CONTRIBUTOR_IDS)[2026-08-09T19:56:03+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-08-09T19:57:46+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SIBLING-REPO-VALIDATE-CI-AND-CONTRIBUTOR-IDS.md
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
---

# Summary

Create `WI-SIBLING-REPO-VALIDATE-CI-AND-CONTRIBUTOR-IDS` to add `lrh validate`
to `velumin` and `replication_vector` CI and then remediate their contributor
ids, in that order, sequenced late in the current program.

# Result

Created
`project/work_items/proposed/WI-SIBLING-REPO-VALIDATE-CI-AND-CONTRIBUTOR-IDS.md`
(`type: operation`, `status: proposed`).

Written after assessing whether to make the change immediately, since both
repositories were paused. The assessment recommended against the rename now and
for capturing it as sequenced work — the author agreed and asked for this work
item.

**Two assumptions corrected by checking during that assessment:**

1. **"velumin is mid-work on a PR."** It has **0 open PRs**, a clean tree, and
   its worktree branch has no commits ahead of `main` and no diff. The only
   dirty path is untracked build output
   (`webgpu_vector_lib/web/smoke-out/`). The window was quieter than reported.
2. **"Neither repository has CI running `lrh validate`."** Both *do* have
   `.github/workflows/validate.yml` running `scripts/validate`. An initial grep
   for the literal string `lrh validate` in `.github/workflows/` returned zero
   and was nearly written up as "no CI." Reading the scripts showed the real
   shape: both run `version → format → lint → test → baseline` with **no
   control-plane step**. The gap is a missing line in an existing script, not a
   missing workflow — a materially smaller and more precise fix.

**Why sequencing is the work item's core content.** An id rename is normally
self-checking, because `owner:` is cross-validated against contributor ids
(`validator.py:1371-1403`), so an incomplete rename fails loudly. That net does
not exist in these repositories' CI. Renaming first would rely on a
verification that is assumed rather than performed — the exact pattern this
session caught three times. The work item therefore forbids renaming before the
CI step lands and is confirmed green, and encodes that as
`forbidden_actions: rename_ids_before_ci_lands`.

**Measured state**, via `git grep` per `AGENTS.md`'s evidence convention:
`velumin` 39 references (35 `owner:` + 4 list), `replication_vector` 18
(18 + 0), total 57. Both registries carry `id: project maintainers` — with a
space — and an empty `github:`. Both repositories currently report
`0 errors, 0 warnings` from `lrh validate`, so nothing is broken today; this is
hygiene, not repair.

The replacement id value is deliberately left open, matching
`PROP-CONTRIBUTOR-IDENTITY-CONTRACT` Open Question 2. An operations task should
not pre-empt a contract decision that has three live candidates.

The work item also records a **quiet-window precondition** as an executable
check (open PRs, working tree, worktree branches, `lrh validate`) rather than
leaving "land it in a quiet window" as an untestable instruction. The author
notes both repositories are low-frequency and single-threaded, so the window can
be created deliberately rather than waited for.

# Validation

- `lrh prompt check-execution --slug wi-sibling-repo-validate-ci-and-contributor-ids
  --work-item AD_HOC` → exit 0, no prior record.
- `lrh validate` (LRH) → 0 errors, 1 warning (pre-existing, unrelated).
- `lrh work-items readiness WI-SIBLING-REPO-VALIDATE-CI-AND-CONTRIBUTOR-IDS` →
  `prompt_ready: yes`.
- Target-repository state checked directly: `gh pr list` (0 open each),
  `git status --porcelain`, `git worktree list`, and `lrh validate` run inside
  each repository (`0 errors, 0 warnings` both).
- Reference counts taken with `git grep`, not filesystem `grep -r`. An earlier
  filesystem count in the same session reported 75 for these two repositories
  rather than 57, because it walked `.claude/worktrees/` copies.

# Follow-up

No PR opened; the branch is pushed without one, so no automatic bot review
fires.

`related_workstreams:` left empty — no existing workstream covers contributor
identity or sibling-repo operations, and `PROP-CONTRIBUTOR-IDENTITY-CONTRACT`
has no workstream of its own yet. If that proposal gains one, this work item
should move under it.

**Updated 2026-08-09:** adopted by `WS-CROSS-REPO-CODE-HEALTH` later in the same session; the item is no longer unowned.

Sequenced late by design: nothing depends on it, both repositories validate
clean today, and it should not compete for attention with the
invocation-and-gate reset.
