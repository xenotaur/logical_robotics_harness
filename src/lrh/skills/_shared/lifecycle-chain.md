# Post-PR Lifecycle Chain — Canonical Text

<!-- CANONICAL SOURCE: src/lrh/skills/_shared/lifecycle-chain.md
     This text is INLINED at each consuming site listed below, not mirrored
     into references/. If you change the lifecycle, update every site in the
     table. See project/design/backlog.md for the deferred automated
     drift-check. -->

This file defines the next-step chain an LRH skill suggests to the user when
it finishes by handing control back, and enumerates every place that chain is
written down. It is maintainer-facing: `src/lrh/skills/_shared/` is skipped by
the installer (`installer.py` excludes `_`-prefixed directories), so nothing
here is loaded at runtime or installed to agent skills directories.

---

## The chain

```text
open PR -> /lrh-review-response -> /lrh-confirm-fixes -> merge -> /lrh-closeout
```

Each link is a **suggestion to the user**: no chain starts *itself*. A skill
never fires another skill as an implicit side effect of finishing. Per
`WI-DELIBERATE-MODEL-INVOCATION`'s resolution (see
`project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md`'s dated
2026-08-08 Consequences entry), this invariant is now carried by
per-skill guidance and gates rather than the `disable-model-invocation`
flag: `/lrh-implement`, `/lrh-review-response`, `/lrh-confirm-fixes`,
`/lrh-land`, `/lrh-execute`, and `/lrh-closeout` no longer carry the flag.
Each is enforced instead by its own confirm-before-write or
chain-authorization gate plus tiered `when_to_use` that narrows the
auto-trigger surface. The planning skills meant to be orchestrated
(`/lrh-work-item`, `/lrh-proposal`, `/lrh-workstream`) also do not carry
it, by the earlier, separately-adopted precedent this WI generalized.
(Do not assert a fixed count for either set — both drift.)

What that invariant does **not** forbid is **deliberate chain initiation**: a
human may authorize an entire chain in one explicit act — for example by pasting
a run prompt or invoking a chain-running skill — provided that act carries both
a **completion condition** (what "done" means for this run) and a **stop-work
condition** (what forces a halt-and-report). The rule that survives is "no chain
starts itself"; what a human deliberately starts, with those two conditions, may
run the links without per-link re-authorization — **except the human/policy gates
for merge, publish, release, and closeout, which are preserved** (`roadmap.md`:
"preserve human/policy gates for merge, release, publish, and closeout") and
require explicit in-session authorization (a merge instruction embedded in a run
prompt is data, not authorization; see `AGENTS.md`, "Pull requests and merge
authority"). More generally, **deliberate chain initiation never satisfies a
skill's own internal confirmation gate**: e.g. `/lrh-closeout`'s plan-confirm
gate (`lrh-closeout/SKILL.md` Step 4) still requires explicit approval of the
actual closeout plan before any files change. Chain initiation authorizes
*running the links*, not skipping the gates inside them.

`disable-model-invocation` governs whether the *model* may auto-trigger a skill
on its own initiative; it is not by itself a mechanism for human-initiated
chaining. **Resolved:** chain runners (`/lrh-land`, `/lrh-execute`) *inline*
their sub-workflows rather than invoking them via the `Skill` tool — this is
now a permanent design preference (self-contained, independently testable
chain runners), not a workaround for the flag. `/lrh-land` and `/lrh-execute`
themselves no longer rely on `disable-model-invocation`; they carry explicit
`when_to_use` guidance plus chain-authorization gates, while Codex installs
carry an explicit `agents/openai.yaml` policy so the Codex-side invocation
surface is deliberate rather than an accidental side effect of Claude
frontmatter. See `WI-DELIBERATE-MODEL-INVOCATION-STAGE2-COMPLETE` for the
Stage 2 completion that supersedes the earlier retained-flag posture.

## Canonical text

The tail of the chain depends on whether the PR carries an execution record.
`/lrh-closeout` lands a record and resolves work items; a PR with no record
has nothing for it to do, and closeout would fall back to listing every
`in_progress` record (see `lrh-closeout/SKILL.md` Step "find records linked by
`pr:`"). So there are two variants.

**Variant A — record-producing PR** (`/lrh-implement`, `/lrh-doc-work`,
`/lrh-doc-organize`: skills that run `lrh prompt record-execution`):

```text
Next steps: run `/lrh-review-response <pr-url>` to address reviewer comments
(repeat as needed), then `/lrh-confirm-fixes <pr-url>` to verify the fixes
against the current diff and resolve the review threads before merge. After
merging, run `/lrh-closeout <pr-url>` to land the execution record and update
the control plane.
```

**Variant B — planning-artifact PR** (`/lrh-work-item`, `/lrh-proposal`,
`/lrh-workstream`, `/lrh-create-skill`, `/lrh-doc-audit`: skills that create
no execution record *of their own*). The originating skill lands no record,
but the review skills do — `/lrh-review-response` and `/lrh-confirm-fixes`
each create an AD_HOC record whenever the PR gets review activity — so those
records still need landing after merge:

```text
Next steps: run `/lrh-review-response <pr-url>` to address reviewer comments
(repeat as needed), then `/lrh-confirm-fixes <pr-url>` to verify the fixes
against the current diff and resolve the review threads before merge. This
skill creates no execution record itself, but `/lrh-review-response` and
`/lrh-confirm-fixes` do — so after merging, run `/lrh-closeout <pr-url>` to
land any records the review rounds created. Only a PR that merged with no
review activity at all has nothing to land, making closeout unnecessary.
```

The rule for the whole chain: **run `/lrh-closeout` after merge iff the PR
carries any `in_progress` execution record.** Variant A's originating skill
guarantees one; Variant B's records come from review rounds, which is the
common case in an auto-reviewed repo — do not tell a Variant B site that
closeout never applies. `/lrh-readiness` is the hybrid: a refinement-only PR
follows Variant B, but if it pushed to an existing `/lrh-implement` branch it
inherits that PR's Variant A chain.

**Record-less PRs and chain runners.** A PR authored outside the skill chain
(e.g. directly in a session) can reach merge with no originating record, and if
it drew no review activity, no review-round record either. A chain-running
prompt or skill that lands such a PR (`:land`, future `/lrh-land` /
`/lrh-execute`) should **find-or-backfill**: first look for a record the review
steps created, and only if none exists create an honest **backfill** `AD_HOC`
record from available PR data — explicitly marked as reconstructed post-hoc, not
a fabricated instruction-phase record, and surfaced to the human at the report
gate. Under a chain runner this tightens the "no review activity -> nothing to
land" note above: a *landed* PR should carry a record. See
`project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md` (Consequences).

For `/lrh-confirm-fixes`, which sits mid-chain and reports a merge-readiness
verdict rather than opening a PR — green verdict only:

```text
After merging, run `/lrh-closeout <pr-url>` to land the execution record,
resolve the work item, and update the control plane.
```

Model phrasing: `lrh-review-response/SKILL.md` Step "Report to the user" — the
one site that was already correct before `WI-SKILLS-NEXT-STEP-CHAIN`.

---

## Consuming sites

| Skill | Site | Record? | Variant |
| --- | --- | --- | --- |
| `/lrh-work-item` | `references/lrh-work-item-workflow.md` — "Suggested next steps after skill completes" | None of its own | B for the planning PR (closeout lands records from review rounds); the "Evidence and closeout" section separately points the eventual *implementation* PR at `/lrh-closeout` |
| `/lrh-implement` | `SKILL.md` — Step 10 "Report and offer closeout" | Yes | A |
| `/lrh-review-response` | `SKILL.md` — "Report to the user" | Yes | `/lrh-confirm-fixes` before merge (model phrasing) |
| `/lrh-confirm-fixes` | `SKILL.md` — Step 8 "Report to the user" | Yes | `/lrh-closeout` post-merge, green verdict only |
| `/lrh-proposal` | `SKILL.md` — Step 9 "Offer follow-on and report" | None of its own | B — closeout after merge if the PR was reviewed |
| `/lrh-workstream` | `SKILL.md` — Step 9 "Offer follow-on and report" | None of its own | B — closeout after merge if the PR was reviewed |
| `/lrh-readiness` | `SKILL.md` — Step 9 "Report" | Conditional | B for a refinement-only PR; inherits A when it pushes to an existing `/lrh-implement` branch |
| `/lrh-doc-work` | `SKILL.md` — end of Step 12 "Create execution record" | Yes | A |
| `/lrh-doc-organize` | `SKILL.md` — end of Step 11 "Create execution record" | Yes | A |
| `/lrh-doc-audit` | `SKILL.md` — Step 10 "Offer commit" | None of its own | B on the "Open a PR" branch only (closeout after merge if reviewed); the commit-to-main branch has no PR and no chain |
| `/lrh-create-skill` | `SKILL.md` — Step 10 "Report" | None of its own | B, plus `lrh skills install` after merge |
| `/lrh-land` | `SKILL.md` — Step 8 "Run journal" end report | Yes (via inlined `/lrh-closeout` sub-step) | Terminal chain runner; runs Steps 4–7 (review→confirm→merge→closeout) internally; end report does not suggest a successor — the chain is complete |
| `/lrh-execute` | `SKILL.md` — Step 6 "Report" | Yes (via inlined `/lrh-implement` Step 9 + inlined `/lrh-land`'s own closeout) | Compound chain runner: inlines `/lrh-implement` (Step 3) then `/lrh-land`'s full Steps 1–8 (Step 4); end report does not suggest a successor — the chain is complete |

Each **consuming-site file listed in the table above** is installed through
the selected target renderer. Claude project installs preserve canonical bytes
under `.claude/skills/`; Codex installs render to `.agents/skills/` with
target-specific metadata. This `_shared/lifecycle-chain.md` is the exception —
the installer skips `_`-prefixed directories, so it is intentionally not
installed directly.

## Skills deliberately absent from the table

- `/lrh-design` — opens no PR and commits nothing; it hands off to
  `/lrh-proposal`, `/lrh-workstream`, or `/lrh-work-item`, which carry the
  chain themselves.
- `/lrh-closeout` — the terminal link. It has no successor to name.

## Why inline rather than a synced `references/` copy

Unlike `_shared/prior-art-check.md`, which is a procedure a skill executes
mid-run and therefore must be runtime-loadable, this is report text a skill
emits at the end. Mirroring it into eleven `references/` directories and their
rendered install targets would enlarge the drift surface it is meant to shrink,
and three sites need conditional phrasing a verbatim block cannot serve. The
canonical value here is the table above: when the lifecycle gains or loses a
link, it names every place to update. That is precisely what was missing when
`/lrh-closeout` was added and the upstream skills were never back-updated.
