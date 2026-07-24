---
execution_id: 2026_07_23_18_33_27_FIX_POST_PR_NEXT_STEP_CHAIN
prompt_id: PROMPT(WI-SKILLS-NEXT-STEP-CHAIN:FIX_POST_PR_NEXT_STEP_CHAIN)[2026-07-23T18:24:04-04:00]
work_item: WI-SKILLS-NEXT-STEP-CHAIN
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/412
commit: 697518e
created_at: 2026-07-23T18:33:27-04:00
agent: claude_app
instruction_source: WI-SKILLS-NEXT-STEP-CHAIN
session_transcript: claude-app:b8ccff86-7173-4b64-858b-1dc6f386f062
---

# Summary

Repair the post-PR next-step chain
(`/lrh-review-response` → `/lrh-confirm-fixes` → merge → `/lrh-closeout`)
across the LRH skills, and record the canonical chain once at
`src/lrh/skills/_shared/lifecycle-chain.md` with an index of every consuming
site. Guidance text only — no behavioral or workflow-step changes.

Files the work item and its implementation in a single PR: the design
question the work item exists to resolve was settled in the work item itself,
so there is no intervening decision point that would justify splitting.

# Result

## Audit

Every skill was checked for whether it opens a PR and whether it names the
chain. Findings before this change:

| Skill | Opens PR | Named `/lrh-review-response` | Named `/lrh-closeout` | Action |
| --- | --- | --- | --- | --- |
| `/lrh-work-item` | yes (Step 8) | no | no | fixed |
| `/lrh-implement` | yes | yes | no (hand-rolled closeout) | fixed |
| `/lrh-review-response` | no | n/a | n/a | none — already correct; used as model phrasing |
| `/lrh-confirm-fixes` | no | yes | only negatively | fixed |
| `/lrh-proposal` | yes (Step 8) | no | no | fixed |
| `/lrh-workstream` | yes (Step 8) | no | no | fixed |
| `/lrh-readiness` | yes (Step 8, conditional) | no | no | fixed |
| `/lrh-doc-work` | yes (Step 11) | no | no | fixed |
| `/lrh-doc-organize` | yes (Step 10) | no | no | fixed |
| `/lrh-doc-audit` | offered (Step 10) | no | no | fixed, PR branch only |
| `/lrh-create-skill` | yes (Step 9) | no | no | fixed |
| `/lrh-design` | no | n/a | n/a | none — verified: `grep -n "git commit\|gh pr\|git push" src/lrh/skills/lrh-design/SKILL.md` returns nothing |
| `/lrh-closeout` | no | n/a | n/a | none — terminal link, no successor to name |

Ten sites needed the chain. The defect was broader than the three sites named
in the originating prompt: five further PR-opening skills (`/lrh-proposal`,
`/lrh-workstream`, `/lrh-readiness`, `/lrh-doc-work`, `/lrh-doc-organize`,
`/lrh-create-skill`) had the same gap, plus `/lrh-doc-audit` on its optional
PR path.

Installed mirrors at `~/.claude/skills/` were confirmed byte-identical to
`.claude/skills/` before editing — no user-modification drift to reconcile.

## Design decision — canonical source, inline delivery

Ten sites is past the four-site threshold at which a shared document earns
its sync cost, so option (a) as originally recommended does not hold. But the
established `_shared/` mechanism — mirror the master into each consuming
skill's `references/` as a `SYNCED COPY` — is the wrong instrument here:

1. `_shared/prior-art-check.md` is a ~120-line procedure executed mid-run, so
   it must be runtime-loadable. The chain is ~5 lines of report text emitted
   at the end; loading a file to learn what to say costs every run of ten
   skills for no benefit.
2. Mirroring would produce twenty copies (ten `references/` plus ten
   `.claude/` mirrors) against ten inline sites — a larger drift surface than
   the one it is meant to shrink.
3. Three sites need conditional phrasing a verbatim block cannot serve:
   `/lrh-readiness` only opens a PR when Step 5 created a branch,
   `/lrh-doc-audit` only on the PR path, `/lrh-create-skill` must also
   mention `lrh skills install`.

Resolution: (b)'s canonical source with (a)'s delivery.
`src/lrh/skills/_shared/lifecycle-chain.md` defines the chain once and
enumerates every consuming site in a table; each site inlines the text in its
own voice. The root cause of this bug was not copies drifting — it was that
nobody knew where to look when `/lrh-closeout` was added. A grep-able index
of consuming sites addresses that directly. `_shared/` is skipped by the
installer, so the new file adds no installed-file surface and needs no
`.claude/` mirror.

## Changes

- **New:** `src/lrh/skills/_shared/lifecycle-chain.md` — canonical chain
  text, consuming-site table, and the skills deliberately absent from it.
- `lrh-work-item/references/lrh-work-item-workflow.md` — "Suggested next
  steps" split into two explicitly-labelled orthogonal paths: **PR lifecycle**
  (the chain, new) and **item refinement** (the pre-existing
  `lrh work-items ...` CLI commands, unchanged). Notes that merging the
  planning PR does not resolve the work item. "Evidence and closeout" reduced
  from a hand-rolled four-step procedure to a pointer at `/lrh-closeout`.
- `lrh-implement/SKILL.md` — Step 10 gains `/lrh-confirm-fixes` between
  review response and merge; the manual "move the work item to `resolved/`"
  instruction replaced by `/lrh-closeout`.
- `lrh-confirm-fixes/SKILL.md` — Step 8 report gains `/lrh-closeout` as an
  explicit post-merge next step, green verdict only. The "What This Skill
  Does Not Do" disclaimer reworded from "Does not trigger `/lrh-closeout`" to
  scope the exclusion to automatic *invocation*, and to state that closeout
  is still the user's next step.
- `lrh-proposal`, `lrh-workstream`, `lrh-doc-work`, `lrh-doc-organize`,
  `lrh-create-skill` — chain added to the final report, alongside each
  skill's existing next-step content rather than replacing it.
- `lrh-readiness` — chain added, conditioned on whether Step 8 opened a new
  PR or pushed to an existing one.
- `lrh-doc-audit` — chain added to the "Open a PR" branch only, with an
  explicit note that the commit-to-main path has no PR.
- `lrh-create-skill` — chain plus a note that `lrh skills install` is
  required after merge; merging alone does not install the new skill.
- All ten edits mirrored into `.claude/skills/`.

No Execution Steps, quality checklist, or frontmatter was restructured. Where
a skill had no Report step (`/lrh-doc-work`, `/lrh-doc-organize`), the
guidance was appended to the existing final step rather than adding one.

# Validation

- `scripts/version tools` — ruff 0.15.12, black 26.3.1, pylint 2.16.2;
  Black matches the repository expectation, so formatting/lint/test proceeded.
- `scripts/format --check --diff` — 179 files unchanged.
- `scripts/lint` — ruff all checks passed; black 179 files unchanged.
- `scripts/test` — 796 tests, `OK`, exit 0. No source-code change was made,
  so the suite was expected to be unaffected, and was.
- `lrh validate` — 0 errors, 0 warnings.
- `lrh work-items validate` — no warnings for `WI-SKILLS-NEXT-STEP-CHAIN`.
  Three pre-existing `unresolved-metadata-reference` warnings on
  `WI-SKILLS-LRH-DOC-{AUDIT,ORGANIZE,WORK}` are untouched by this change and
  are recorded as follow-up below.
- `lrh work-items readiness --status proposed` —
  `WI-SKILLS-NEXT-STEP-CHAIN` reports `prompt_ready: yes`, no blocking, no
  warnings.
- `diff -r src/lrh/skills .claude/skills` — differences only for `_shared`,
  `installer.py`, `__init__.py`, `__pycache__`, all expected.

# Follow-up

- **Reinstall required.** `~/.claude/skills/` is a copy, not a symlink.
  Merging does not update it; run `lrh skills install --dry-run --diff`, then
  `lrh skills install`, and report the per-skill status.
- **Pre-existing, out of scope for this work item.**
  `WI-SKILLS-LRH-DOC-AUDIT`, `WI-SKILLS-LRH-DOC-ORGANIZE`, and
  `WI-SKILLS-LRH-DOC-WORK` all carry
  `related_design: project/design/proposals/proposed/lrh-doc-skills/00_proposal.md`,
  which now resolves nowhere — the proposal moved to `adopted/`. Three
  `unresolved-metadata-reference` warnings from `lrh work-items validate`.
  Worth a separate cleanup work item.
- The automated `_shared/` drift check remains deferred to
  `project/design/backlog.md`; `lifecycle-chain.md` is covered by it when it
  lands, and its consuming-site table is the manual stand-in until then.
