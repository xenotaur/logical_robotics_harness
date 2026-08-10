---
execution_id: 2026_08_10_23_45_25_WI_RETRIGGER_REMOVAL_STAGE1
prompt_id: PROMPT(AD_HOC:WI_RETRIGGER_REMOVAL_STAGE1)[2026-08-10T23:40:46+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/541
commit:
agent: claude_app
instruction_source: project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
created_at: 2026-08-10T23:45:25+00:00
---

# Summary

Create `WI-RETRIGGER-REMOVAL-STAGE1`, implementing `PROP-INVOCATION-AND-GATE-RESET`
Stage 1: remove GitHub bot retrigger commands from `lrh-confirm-fixes`
fleet-wide. Filed after confirming retrigger commands are still live in
`src/`, `~/.claude/skills/`, and `~/.agents/skills/` (the Codex-target
install directory, newly populated now that Codex has skill support), and
after an agent session burned roughly $5 of review credits on a retrigger
today from an unpatched corpus.

# Result

Created `project/work_items/proposed/WI-RETRIGGER-REMOVAL-STAGE1.md`
(`type: operation`, `status: proposed`), committed as `dd4bf099` on branch
`xenotaur/chore/retrigger-removal-stage1-wi`, opened as PR #541.

Seven required changes: strip the retrigger commands from
`lrh-confirm-fixes/SKILL.md` and `round-cap-gate.md` in both `src/` and
`.claude/skills/`; rescope PR #522 to its retained Decision 3; remove
`self_review_preference` from the chain-defaults profile; mark the two
stalled-reviewer backlog entries obsolete; run `lrh skills install` for
both the Claude and Codex targets; verify the retrigger strings are absent
from all three installed corpora, not the source tree alone; re-stamp
`confirmed_commit`.

## The corpus finding this WI is built around

Verified directly rather than assumed: `~/.claude/skills/lrh-confirm-fixes/`
still carries both retrigger commands, and so does
`~/.agents/skills/lrh-confirm-fixes/` -- the directory
`src/lrh/skills/installer.py:429`'s `_default_skills_dir` resolves to for
the Codex install target. That second corpus is new information this
session surfaced: the governing proposal and workstream previously named
only `~/.claude/skills/` verification, written before Codex picked up LRH
skill support. This work item's acceptance criteria name all three corpora
explicitly, plus a restart reminder for both Claude Code and Codex sessions
-- a stale session keeps retriggering regardless of what lands, since it
keeps the copy it loaded at start.

Antigravity is explicitly named out of scope: it has shipped no skill
support yet, so it carries no installed corpus to fix.

## Prior-art check

**Duplication search -- no duplicate.** No existing work item names
retrigger removal; `git grep -li "retrigger removal" project/work_items/`
returned nothing. `WI-DELIBERATE-MODEL-INVOCATION` (Stage 2, resolved via
PR #533) and `WI-FRONT-OF-RUN-GATE-COLLAPSE` (Stage 3, proposed) cover
later stages of the same proposal and do not touch `lrh-confirm-fixes`'s
retrigger mechanism.

**Demand search -- demand recorded and now urgent.**
`PROP-INVOCATION-AND-GATE-RESET` names this as Stage 1, first in its
strictly sequential implementation plan. Today's $5 leak is fresh,
first-hand demand evidence beyond the proposal's own argument.

# Validation

- `lrh prompt check-execution --slug wi-retrigger-removal-stage1
  --work-item AD_HOC` → exit 0, no prior record.
- `lrh validate` → 0 errors, 1 warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-SESSION-ARCHIVE-SYNC`,
  pre-existing and not in this diff).
- `lrh work-items readiness WI-RETRIGGER-REMOVAL-STAGE1 --format md` →
  `prompt_ready: yes`, no blocking reasons, no warnings.
- `git diff --cached --check` → clean.
- The `~/.agents/skills/` finding was verified directly (file listing plus
  grep for the retrigger strings), not inferred from the user's report
  alone.

# Follow-up

`commit:` left empty until closeout.

Per the human's explicit instruction: this PR is opened deliberately to
spend the one automatic bot-review round this repository triggers on open,
since surfacing issues early on a WI that itself governs retrigger removal
is worth that one cost. Any *subsequent* round must switch to
`/lrh-self-review` rather than a manual retrigger -- consistent with the
standing constraint `PROP-INVOCATION-AND-GATE-RESET` exists to formalize,
and explicit here so a later round doesn't default back to the documented
skill behavior.

No `depends_on` blocker -- Stage 2 is already resolved and nothing in this
work item's scope touches Stage 3's files. Not added to
`WS-INVOCATION-AND-GATE-RESET`'s `work_items:`, which stays empty pending
stage sequencing, matching the disposition already used for
`WI-FRONT-OF-RUN-GATE-COLLAPSE`.
