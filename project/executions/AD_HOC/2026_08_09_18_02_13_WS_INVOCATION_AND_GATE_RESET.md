---
execution_id: 2026_08_09_18_02_13_WS_INVOCATION_AND_GATE_RESET
prompt_id: PROMPT(AD_HOC:WS_INVOCATION_AND_GATE_RESET)[2026-08-09T17:58:40+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-08-09T18:02:13+00:00
agent: claude_app
instruction_source: project/workstreams/proposed/WS-INVOCATION-AND-GATE-RESET.md
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
---

# Summary

Create `WS-INVOCATION-AND-GATE-RESET` to govern delivery of
`PROP-INVOCATION-AND-GATE-RESET` Stages 1, 2, 3, 3.5, 5, 6, and 7, completing
the planning-artifact set assembled for whole-set review.

# Result

Created `project/workstreams/proposed/WS-INVOCATION-AND-GATE-RESET.md`
(`status: proposed`, `stage: assessed`, `origin: incident`).

`stage: assessed` rather than `designed` deliberately: the options were reviewed
and directions chosen across this session, but the governing proposal is still
`status: proposed` and has not been through review, so claiming "design
reviewed, approach locked" would overstate it.

**Ownership boundaries observed rather than assumed.** Two checks shaped the
frontmatter:

- **Stage 4 excluded.** `WS-LRH-CHAIN-DEFAULTS` already lists
  `WI-LRH-CHAIN-DEFAULTS-INCREMENT-2` in its own `work_items:`, so claiming
  Stage 4 here would create duplicate ownership. Cross-linked via
  `related_workstreams:` instead, following `DEC-DELIBERATE-CHAIN-INITIATION`'s
  Alternatives #3 reasoning for cross-linking rather than folding.
- **`WI-DELIBERATE-MODEL-INVOCATION` left unclaimed.** It declares
  `related_workstreams: [WS-EXECUTION-FRAMEWORK]`, but that workstream's
  `work_items:` list does *not* include it — so it is related to, not owned by,
  any workstream. Stage 2 completes it, which would make this workstream a
  legitimate home, but claiming it unilaterally would be an ownership change
  made without asking. Recorded in the body's Prior Art Check as an offer.

`work_items:` is deliberately empty rather than speculative; the planned
per-stage decomposition is described in the body instead, since none of those
work items exist yet.

Decisions resolved earlier in the same turn were folded into the governing
proposal before this workstream was written, so its exit criteria reflect them:
the retrigger escape hatch is manual-only outside the skills (recorded in
Decision 2), and `PROP-REVIEW-WAIT-POSTURE` is rescoped to its Decision 3
bounded-poll wait mechanism rather than closed.

# Validation

- `lrh prompt check-execution --slug ws-invocation-and-gate-reset
  --work-item AD_HOC` → exit 0, no prior record.
- `lrh validate` → 0 errors, 1 warning. The warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-SESSION-ARCHIVE-SYNC`)
  is pre-existing and unrelated. This workstream is `proposed`, not `active`, so
  its empty `work_items:` does not trigger the same rule.
- Schema conformance checked against `validator.py:58-70`:
  `WORKSTREAM_REQUIRED_FIELDS`, `WORKSTREAM_KINDS`, `WORKSTREAM_STATUS`, and
  `WORKSTREAM_STAGE` — `assessed` is in the allowed stage vocabulary.
- Non-ASCII scan run after writing; a stray CJK character introduced in the
  Purpose section was caught and corrected. Remaining non-ASCII are em-dashes,
  consistent with the rest of the corpus.

# Follow-up

No PR opened. The branch is pushed to `origin` without a PR, which triggers no
automatic bot review — the posture chosen for this artifact set.

Open offer: link `WI-DELIBERATE-MODEL-INVOCATION` into this workstream's
`work_items:`, since Stage 2 completes it and no workstream currently owns it.

Three open questions remain in the governing proposal: the provisional cap
threshold (recommendation: 3, the only value with in-repo precedent), Taurcode
cascade scope (recommendation: tracked separately), and Stage 5b triage capacity
(recommendation: the 8 related open PRs, with the three stale Bolt PRs swept
separately).
