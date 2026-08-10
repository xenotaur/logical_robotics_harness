---
execution_id: 2026_08_09_21_13_27_WS_CROSS_REPO_CODE_HEALTH
prompt_id: PROMPT(AD_HOC:WS_CROSS_REPO_CODE_HEALTH)[2026-08-09T21:11:52+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-08-09T21:13:27+00:00
agent: claude_app
instruction_source: project/workstreams/proposed/WS-CROSS-REPO-CODE-HEALTH.md
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
---

# Summary

Create `WS-CROSS-REPO-CODE-HEALTH` and adopt the five harness-consistency work
items that had no workstream home, recording the synergies and collisions that
only became visible once they were considered together.

# Result

Created `project/workstreams/proposed/WS-CROSS-REPO-CODE-HEALTH.md`
(`status: proposed`, `stage: conceived`, `origin: follow_up`) and added the
reciprocal `related_workstreams:` link to all five.

**Amended 2026-08-09:** a later review found that listing every item in
`work_items:` made two of them dispatchable before their blocking reset stages;
`WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION` and `WI-TAURCODE-PROMPT-AND-SKILL-SYNC`
were withheld from that field as a result. All five remain in scope. Consult the
workstream's `work_items:` for current membership rather than this record.

## A correction to the premise that prompted this

The trigger was an observation that four consecutive work items had
`related_workstreams: []`, framed as those four revealing a gap. Measuring
before writing showed **fifteen** work items are currently unowned, and **ten of
them predate this session** — test-layout migration (3), documentation (2), CLI
wiring tests, work-audit and work-remains features, template audit, and a
doc-related-design repoint.

So the gap is real but older and wider than the framing suggested, and the four
items did not reveal it. The workstream therefore takes **five** items into scope on the
basis of fit, and its Scope section explicitly declines to sweep the other ten:
"Adopting an item here should be a judgement about fit, not a way to clear a
list." Absorbing all fifteen would have produced a catch-all with no coherent
exit criteria.

## Synergies found only by looking at the set together

- **S1 — item order changes.** `WI-LRH-SEARCH-COUNT-PROVENANCE`'s candidate
  scopes already include the installed skill corpus, and items 4 and 5 both end
  with "verify against the installed corpus, not the source tree." Built first,
  that tool makes both verifications mechanical; built last, both hand-roll it.
  The workstream sequences it first for that reason.
- **S2 — the CI gap is three repositories, not two.** Taurcode has **no
  `scripts/validate` at all**, and none of its seven workflows runs
  `lrh validate` — the same gap
  `WI-SIBLING-REPO-VALIDATE-CI-AND-CONTRIBUTOR-IDS` fixes for `velumin` and
  `replication_vector`. That work item previously listed `taurcode` as a clean
  exclusion; it now records it as an open question, since writing the same CI
  step twice is the default outcome of leaving it unstated.
- **S3 — item 2 needs the propagation step the reset now carries.** Fixing
  branch creation in eight skills changes nothing until `lrh skills install`
  runs and the installed copies are verified.

## Collisions

- **C1 — a direct file collision with `WS-INVOCATION-AND-GATE-RESET`.**
  `WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION` declares
  `src/lrh/skills/lrh-land/SKILL.md` and
  `src/lrh/skills/lrh-land/references/land-workflow.md` in
  `artifacts_expected`; the reset's Stages 1 and 2 modify **both**, verified
  against the exploration branch. Neither workstream's artifacts mentioned the
  other's claim on those files. This is the clearest justification for the
  workstream existing — the collision is invisible from inside either work item.
- **C2 — item 2 cites a snippet Stage 1 deletes.** Already noted inside that
  work item; recorded at workstream level because it is a sequencing fact
  between two workstreams.
- **C3 — item 3 obsoletes a workaround owned elsewhere.**
  `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3` (owned by `WS-LRH-CHAIN-DEFAULTS`) carries
  a prose "DO NOT START" banner only because a proposed item cannot be marked
  blocked. When item 3 lands, that banner should be replaced by real frontmatter
  — and nothing currently schedules that follow-through, since
  `WS-LRH-CHAIN-DEFAULTS` has no reason to watch item 3.

# Validation

- `lrh prompt check-execution --slug ws-cross-repo-code-health --work-item AD_HOC`
  → exit 0, no prior record.
- `lrh validate` → 0 errors, 1 warning (pre-existing, unrelated) after each of:
  creating the workstream, adding five reciprocal links, and amending the
  sibling-repo work item's scope.
- Prior-art check: no existing workstream titled or scoped around health,
  hygiene, cross-repository, or fleet concerns.
- Unowned-item census taken by grepping `related_workstreams: []` across
  `project/work_items/proposed/`, and pre-existence confirmed per item with
  `git cat-file -e origin/main:<path>`.
- C1 verified by comparing the work item's `artifacts_expected` against
  `git show --stat` on the exploration branch, not by reading either document's
  prose.

# Follow-up

No PR opened; the branch is pushed without one, so no automatic bot review
fires.

`WS-CROSS-REPO-CODE-HEALTH` is `stage: conceived` rather than `assessed`: the
items are written and validated, but the workstream's own sequencing has not
been reviewed by anyone other than its author, and S2 leaves a real scoping
choice open.

Two items to carry forward that this workstream records but does not own:

1. C1's resolution — item 2 should land after the reset's Stage 2, which needs
   confirming when both are scheduled rather than assumed now.
2. C3's follow-through — `WS-LRH-CHAIN-DEFAULTS` should be told when item 3
   lands so `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3`'s banner is removed rather than
   left as a permanent workaround for a fixed problem.
