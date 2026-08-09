---
execution_id: 2026_08_09_16_21_23_CONTRIBUTOR_IDENTITY_CONTRACT
prompt_id: PROMPT(AD_HOC:CONTRIBUTOR_IDENTITY_CONTRACT)[2026-08-09T16:19:24+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-08-09T16:21:23+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/contributor-identity-contract/00_proposal.md
session_transcript: claude-app:3c4e404b-8420-4a62-9c3f-f5dcccfa5400
---

# Summary

Capture `PROP-CONTRIBUTOR-IDENTITY-CONTRACT`, formalizing `id` as a stable
repo-local identifier and `github` as the cross-repository correlation key, after
measurement showed a prior `prosocial` session's contributor-divergence analysis
had an inverted premise.

# Result

Created
`project/design/proposals/proposed/contributor-identity-contract/00_proposal.md`,
committed as `cfcb4ba4` on branch `claude/self-review-command-prefs-68c9f9`,
joining the planning-artifact set assembled for review as a whole.

Five design decisions: the `id`/`github` contract; explicit rejection of
id-value unification as redundant; `github` required for `type: human` and
optional for `type: agent`; remediation of four distinct registry defects; and a
slug-format constraint on `id`.

## Measurement that corrected the triggering premise

The `prosocial` session's report — that LRH and LCATS diverged and that
standardizing on the GitHub handle meant roughly 150 changes in LCATS — was
wrong in three respects, each verified directly:

- **Counts inverted.** LCATS carries 18 tracked contributor-id references
  (9 `owner:`, 9 list entries), all already `xenotaur`, so it needs zero changes
  in that direction. LRH carries 276 (140 `owner:`, 135 list, 1 registry) and
  would have absorbed the entire cost. **(Figures corrected — see the
  Correction section below. This record originally stated 180 for LCATS.)**
- **Direction backwards.** LRH records `id: anthony` *and* `github: xenotaur` as
  distinct fields; LCATS records `id: xenotaur` with `github` empty. LCATS lost
  the mapping rather than simplifying it.
- **Unification unnecessary.** `github` is the correlation key; populating it
  makes id-value consistency redundant.

## Fleet survey

Surveyed every repository under `~/Workspace` with an LRH `project/contributors`
directory. Seven found, in four states:

- **Conformant:** `logical_robotics_harness` (`anthony`/`xenotaur`), `taurcode`
  (identical to LRH), `taurworks` (`xenotaur`/`xenotaur`, plus four agent
  entries).
- **Missing correlation key:** `LCATS` (`id: xenotaur`, `github` empty).
- **Malformed id:** `replication_vector` and `velumin`, both
  `id: project maintainers` — with a space.
- **Stub missing a required field:** `taurworks-safety`
  (`id: CONTRIBUTORS-INIT`, no `type:`), which is already in
  `CONTRIBUTOR_REQUIRED_FIELDS` — so that registry either fails `lrh validate`
  today or is never validated.
- **No registry at all:** `prosocial`, which nonetheless has an `owner:`
  reference pointing at an undefined contributor.

Two findings materially strengthened the proposal beyond its original brief.
First, `taurcode` already matches LRH exactly, so LRH's pattern is the de facto
fleet convention rather than an idiosyncrasy. Second, `taurworks`'s agent
entries are direct evidence that `id` and `github` must be separable:
`github-copilot` → `copilot-pull-request-reviewer`, `jules` →
`google-labs-jules`, `codex` → `chatgpt-codex-connector`. No value-unification
scheme could produce those mappings.

## Grounding the "not load-bearing" caveat

`Contributor.github` is declared at `src/lrh/control/models.py:114` but has no
consumer anywhere in `src/lrh/`, and `github` does not appear in
`src/lrh/control/validator.py` at all; `CONTRIBUTOR_REQUIRED_FIELDS` is
`{"id", "type", "roles", "display_name", "status"}` (`validator.py:11`). This is
recorded in the proposal as an honest weakening of the "LRH is more correct"
claim, and is why validator enforcement is in scope rather than deferred.

## Correction carried into the proposal

*(The two figures quoted in this subsection — 8,506 URLs and ~250 look-alikes —
are themselves wrong, from the same measurement error. See the Correction
section at the end of this record. Left as written to preserve what the run
actually believed at the time.)*

An earlier turn of the analysis called renaming in LCATS "catastrophic" because
of its 8,506 `github.com/xenotaur` URLs. That overstated the risk: anchored
patterns never match a URL, and `owner:` is cross-validated
(`validator.py:1371-1403`), so an incomplete rename fails loudly. The proposal
records the accurate argument instead — reviewability, given roughly 250
look-alike non-id uses in LCATS (API paths, branch prefixes, a fork name).

# Validation

- `lrh prompt check-execution --slug contributor-identity-contract
  --work-item AD_HOC` → exit 0, no prior record.
- `lrh validate` → 0 errors, 1 warning. The warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-SESSION-ARCHIVE-SYNC`)
  is pre-existing and unrelated.
- `git diff --cached --check` → clean.
- Fleet **registry** survey (the seven-repo `id`/`type`/`github` table) run with
  `.claude/worktrees/` copies excluded — that half is sound, and an independent
  review re-derived every value in it.
- **The reference *counts* were NOT run that way, contrary to what this record
  originally certified.** See the Correction section below. This bullet
  previously read "Fleet survey run directly against each repository's working
  tree, excluding `.claude/worktrees/` copies to avoid double-counting," which
  was true of the registry table and false of the counts, but written as though
  it covered both.

## Correction (2026-08-09, post-review)

An independent cold-context subagent review caught two related factual errors in
this record and in the proposal it produced. Both were re-verified directly
before correcting, and both trace to one root cause.

**Root cause.** The count commands used filesystem `grep -r`, which sees
`.claude/worktrees/` checkouts and untracked files. LCATS has ten worktree
entries, so every tracked file was counted ten times:

    git grep -c "^owner: xenotaur" -- '*.md'   →  9   (tracked, correct)
    grep -rn --include=*.md "^owner: xenotaur" →  90  (9 worktrees x 9 + 9 real)

**Error 1 — LCATS counts inflated 10x.** Stated 180 contributor-id references
(90 + 90); actual is 18 (9 + 9). `github.com/xenotaur` URLs stated as 8,506;
actual tracked is 898. The "roughly 250 look-alike non-id uses" figure came from
the same inflated source and is likewise overstated.

**Error 2 — `prosocial`'s orphan `owner:` reference does not exist.** Stated
that `prosocial` has an `owner:` reference pointing at an undefined contributor.
`git grep '^owner:'` returns zero tracked matches there; the single hit was an
untracked file in a worktree checkout, and it read `owner: anthony`, not
`xenotaur`.

**What survives.** The proposal's conclusion is unchanged and in fact
strengthened: the LRH-absorbs-the-cost asymmetry is 276 vs 18 rather than
276 vs 180. LRH's own 276 was independently confirmed correct at the authoring
commit. The seven-repo registry survey — including the `taurworks` agent-handle
mappings that supply the proposal's strongest evidence — is accurate, since it
did exclude worktrees.

**What weakens.** Decision 2's *secondary* reviewability argument rested on the
inflated look-alike count and is no longer load-bearing; the proposal now says
so explicitly and leans on the primary argument instead. Open Question 4 lost
its motivating instance and is reframed as a general-principle question.

**Process note.** This is precisely the failure mode
`feedback_verify_repo_wide_audit_claims` warns about — a "grep found N" claim
that is silently wrong — and the record compounded it by certifying a
verification step that was performed for one half of the survey and not the
other. A new Open Question 5 in the proposal asks whether this project should
standardize on `git grep` for decision-feeding counts.

# Follow-up

No PR opened, consistent with assembling the planning artifacts for review as a
whole and with the standing constraint that opening a PR triggers automatic bot
review.

Four open questions carried in the proposal: whether Decision 5's id-format rule
should be split out; what `replication_vector` and `velumin` should use instead
of `project maintainers`; whether `taurworks-safety`'s stub is a bug or intended
scaffolding; and whether existing `owner:` references should be audited against
their registries, as `prosocial`'s orphan reference suggests.

Cross-repository remediation (Decision 4, step 4) is specified here but must be
executed per-repo by hand — LRH planning artifacts govern this repository only.
