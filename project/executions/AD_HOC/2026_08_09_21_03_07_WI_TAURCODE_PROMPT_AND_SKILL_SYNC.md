---
execution_id: 2026_08_09_21_03_07_WI_TAURCODE_PROMPT_AND_SKILL_SYNC
prompt_id: PROMPT(AD_HOC:WI_TAURCODE_PROMPT_AND_SKILL_SYNC)[2026-08-09T21:02:03+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/535
commit: 98b128ed733a7b125a68f7d5d8db1308e6b62fd6
created_at: 2026-08-09T21:03:07+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-TAURCODE-PROMPT-AND-SKILL-SYNC.md
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
---

# Summary

Create `WI-TAURCODE-PROMPT-AND-SKILL-SYNC`, making concrete the Taurcode handoff
that `PROP-INVOCATION-AND-GATE-RESET` names but deliberately excludes from
Stage 3's cascade.

# Result

Created `project/work_items/proposed/WI-TAURCODE-PROMPT-AND-SKILL-SYNC.md`
(`type: operation`, `status: proposed`).

Taurcode state measured directly rather than assumed. It is stale in **two
distinct ways**, which the work item separates because they need different
fixes:

**Defect 1 — the prompts assume bot review is the review mechanism.**
`prompts/taurcode/land.md` (180 lines) Step 1 is "Wait for review to ACTUALLY
land," on the premise that "Automated reviewers post minutes after the PR opens
or is pushed." Accurate today; half-wrong after Stage 1, when bot review fires
only on PR open and every later round is a synchronous `/lrh-self-review` pass
with nothing to wait for. `execute.md` (173 lines) carries the same assumption.
Both reference gate/review concepts six and seven times.

Worth recording: the prompts contain **no retrigger commands** — verified by
grep across `prompts/`. So this defect is a stale *model of how review arrives*,
not Taurcode issuing retriggers. That distinction matters for scoping and was
not obvious before checking.

**Defect 2 — vendored LRH skills are stale.** `.claude/skills/` holds thirteen
LRH skills, **ten still carrying `disable-model-invocation`**. Its
`lrh-confirm-fixes/SKILL.md` is 373 lines against LRH's current 674, and its
`references/` contains only `confirm-fixes-workflow.md` — no
`round-cap-gate.md`, so that copy predates the round-cap mechanism entirely.

The two are bundled because they must land together: refreshing the skills while
the prompts still describe the old review model would leave the halves
disagreeing.

**Sequencing encoded, not left to judgement.** `forbidden_actions` carries
`sync_before_stages_1_and_2_land`, since syncing to a moving target would need
doing twice.

**Paths are Taurcode-relative and the work item says so explicitly**, because
every other artifact in this packet uses LRH-relative paths and a reader could
otherwise look for `prompts/taurcode/land.md` in the wrong repository.

A first Required Change asks whether Taurcode already has its own planning
artifact for this — if so, that is the better home and this item should link
rather than duplicate. A sixth asks for a decision on whether Taurcode should
continue vendoring LRH skills at all, given it maintains parallel prompts for
the same workflows; that question is scoped to *recording a decision*, not
acting on it.

# Validation

- `lrh prompt check-execution --slug wi-taurcode-prompt-and-skill-sync
  --work-item AD_HOC` → exit 0, no prior record.
- `lrh validate` → 0 errors, 1 warning (pre-existing, unrelated).
- `lrh work-items readiness WI-TAURCODE-PROMPT-AND-SKILL-SYNC` →
  `prompt_ready: yes`.
- Taurcode state measured directly: prompt line counts, the absence of retrigger
  commands across `prompts/`, the ten flagged skills, and the 373-vs-674 line
  divergence in `lrh-confirm-fixes/SKILL.md` with its missing
  `round-cap-gate.md` reference.

# Follow-up

No PR opened; the branch is pushed without one, so no automatic bot review
fires.

`related_workstreams:` left empty — the fourth work item in this packet without
a workstream home. No workstream covers cross-repository operations.

**Updated 2026-08-09:** brought into `WS-CROSS-REPO-CODE-HEALTH`'s scope later in the same session. Whether it is currently in that workstream's `work_items:` depends on sequencing — consult that field rather than this note, which is not kept in sync with it.

**Taurcode is not currently quiet:** `main` had three modified files and three
open PRs when measured. Unlike `velumin` and `replication_vector`, a quiet
window cannot be assumed and must be confirmed before starting — recorded in the
work item's Risk Notes.
