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

- **Counts inverted.** LCATS carries 180 contributor-id references (90 `owner:`,
  90 list entries), all already `xenotaur`, so it needs zero changes in that
  direction. LRH carries 276 (140 `owner:`, 135 list, 1 registry) and would have
  absorbed the entire cost.
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
- Fleet survey run directly against each repository's working tree, excluding
  `.claude/worktrees/` copies to avoid double-counting.

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
