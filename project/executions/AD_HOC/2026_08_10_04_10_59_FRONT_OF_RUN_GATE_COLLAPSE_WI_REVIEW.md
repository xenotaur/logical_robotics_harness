---
execution_id: 2026_08_10_04_10_59_FRONT_OF_RUN_GATE_COLLAPSE_WI_REVIEW
prompt_id: PROMPT(AD_HOC:FRONT_OF_RUN_GATE_COLLAPSE_WI_REVIEW)[2026-08-10T03:51:04+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_10_03_12_27_WI_FRONT_OF_RUN_GATE_COLLAPSE
pr: https://github.com/xenotaur/logical_robotics_harness/pull/536
commit:
created_at: 2026-08-10T04:10:59+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/536
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
---

# Summary

Round 1 review response for PR #536. Two comments, both fixed, pushed as
`198b7e5f`. One from `chatgpt-codex-connector` (P2, exit-criterion drift), one
from `copilot-pull-request-reviewer` (an internally inconsistent count).

# Result

## Comment 1 — Codex P2, exit-criterion duplication — fixed at the cause

**Premise verified independently before acting**, both halves. The body of
`WS-INVOCATION-AND-GATE-RESET.md` did carry a second copy of the Stage 3 exit
criterion, and the file itself instructed — at `:168` as of `0389abe2`, the
commit under review; that line no longer exists, since this response deleted
it — that the two lists be kept in sync, noting that a prior independent review
had already caught them drifting on the `skip_if_opted_in` clause. The PR had updated only the
frontmatter, so the body could have certified Stage 3 complete without
Decision 11.

Two remedies were available: sync the copies, or remove the duplication. The
second was chosen after the human was offered both and picked it. The body's
`## Exit Criteria` list is replaced by a pointer at the authoritative
`exit_criteria:` field, with the reasoning recorded in place: a mutable list
kept in two places is two things to get right and one thing that will
eventually be wrong, and exit criteria are where being wrong is most expensive,
since they gate whether the workstream may close. The duplication had already
failed twice, and leaving it inside the workstream that delivers a proposal
about restatement drift would have been self-refuting.

**Precedent checked rather than assumed.** Five sibling workstreams already
carry a populated `exit_criteria:` with no body restatement, spanning every
bucket: `WS-EXECUTION-FRAMEWORK` and `WS-CI-CAPABILITY-SCAFFOLDING` (proposed),
`WS-LRH-ASSISTANTS` (active), `WS-PRIOR-ART-CHECK` and `WS-SKILLS` (resolved).

**The departure is recorded, not hidden.**
`lrh-workstream/references/workstream-body-guide.md:96` still says the section
"mirrors and expands" the frontmatter list, and `lrh-workstream/SKILL.md:107-109`
tells authors to produce both. Convention and practice disagree; reconciling
them is carried as a follow-up in `WI-FRONT-OF-RUN-GATE-COLLAPSE`'s Risk Notes
rather than done here, since it changes a skill this PR does not otherwise
touch.

## Comment 2 — Copilot, the stop count — real defect, wrong stated reason

Copilot reported that "eight" was inconsistent because the list contains nine
entries. The arithmetic was actually sound: nine stops listed, one marked
`(conditional)`, therefore eight unconditional, which is what the sentence
claimed. But `eight unconditional human stops — [nine-item list]` reads as
though the list enumerates the eight, so the presentation was genuinely
confusing even though the number was right.

Reworded to state both numbers — "nine human stops, eight of them
unconditional" — and the Decision 11 cross-reference now reads "down from the
eight unconditional stops enumerated in §3". The finding was accepted; its
stated reason was not, and the response thread says so rather than conceding an
error that was not made.

## Three self-corrections made before commit

Recorded because each is an instance of the failure pattern this PR's own
proposal documents — checking a narrower surface than the claim covers:

- **Sibling-workstream count.** Written as "three"; actually five. The first
  survey used shell globs over `proposed/` and `active/` only; the verification
  used `git ls-files` over all workstream buckets.
- **Body-guide citation.** Written as `:94`; actually `:96`.
- **Cross-reference target.** A pointer to "Decision 11's Risk Notes" was
  wrong — Decision 11 has no Risk Notes section; the work item does. Repointed
  to `WI-FRONT-OF-RUN-GATE-COLLAPSE`.

All three were caught by verifying the claims after writing them and before
committing, not by a reviewer.

## Note on `rerun_of` resolution

The skill's documented Step 7 search converts the branch slug to upper-underscore
form and greps execution filenames: `front-of-run-gate-collapse-wi` →
`FRONT_OF_RUN_GATE_COLLAPSE_WI`, which matches nothing. The primary record is
named `..._WI_FRONT_OF_RUN_GATE_COLLAPSE.md` — derived from the work item ID,
not the branch — so the two orderings differ and the documented search returns
empty. Resolved instead by matching on the `pr:` field. Worth noting for the
skill: a WI-creation branch suffixed to avoid colliding with its future
implementation branch will systematically miss this search.

# Validation

- `lrh prompt check-execution --slug front-of-run-gate-collapse-wi-review
  --work-item AD_HOC --no-remote` → exit 0, no prior record.
- PR identity verified before any edit: branch and `headRefOid` both matched
  the local checkout at `f9f4cc73`, state `OPEN`.
- `scripts/version tools` → recorded.
- `scripts/format --check --diff` → PASS, 196 files unchanged.
- `scripts/lint` → PASS.
- `scripts/test` → **1071 tests, OK**, exit 0.
- `lrh validate` → 0 errors, 1 warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-SESSION-ARCHIVE-SYNC`,
  pre-existing, not in this diff).
- `git diff --cached --check` → clean.
- Committed content verified with `git show HEAD:<path>` rather than a clean
  `git status`: zero remaining `Stage 3 landed:` body duplications, the
  five-sibling sentence present, and both reworded count sites confirmed at
  `:129` and `:728`.

# Follow-up

`commit:` left empty until closeout.

No bot retrigger was performed and none should be, per the standing constraint
this PR's own proposal exists to formalize. Both bots reviewed `0389abe2`;
`HEAD` is now `198b7e5f`, so no automated reviewer has seen the fixes. If an
independent pass on the current commit is wanted before merge, the substitute
is `/lrh-self-review`, not a retrigger.

One item deferred deliberately: reconciling
`lrh-workstream/references/workstream-body-guide.md:96` and
`lrh-workstream/SKILL.md:107-109` with the practice this response adopts. It is
recorded in `WI-FRONT-OF-RUN-GATE-COLLAPSE`'s Risk Notes and is out of scope
for a planning-artifact PR that touches no skills.
