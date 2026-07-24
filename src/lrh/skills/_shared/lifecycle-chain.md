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
here is loaded at runtime or installed to `~/.claude/skills/`.

---

## The chain

```text
open PR -> /lrh-review-response -> /lrh-confirm-fixes -> merge -> /lrh-closeout
```

Each link is a **suggestion to the user**, never an automatic invocation. The
planning skills carry `disable-model-invocation: true` deliberately, and no
skill should call another as a side effect of finishing.

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

Each **consuming-site file listed in the table above** also exists as a
byte-identical mirror under `.claude/skills/`; edit both copies. This
`_shared/lifecycle-chain.md` is the exception — the installer skips
`_`-prefixed directories, so it is intentionally not mirrored and has no
`.claude/` counterpart.

## Skills deliberately absent from the table

- `/lrh-design` — opens no PR and commits nothing; it hands off to
  `/lrh-proposal`, `/lrh-workstream`, or `/lrh-work-item`, which carry the
  chain themselves.
- `/lrh-closeout` — the terminal link. It has no successor to name.

## Why inline rather than a synced `references/` copy

Unlike `_shared/prior-art-check.md`, which is a procedure a skill executes
mid-run and therefore must be runtime-loadable, this is report text a skill
emits at the end. Mirroring it into eleven `references/` directories (plus
eleven `.claude/` mirrors) would enlarge the drift surface it is meant to
shrink, and three sites need conditional phrasing a verbatim block cannot
serve. The canonical value here is the table above: when the lifecycle gains
or loses a link, it names every place to update. That is precisely what was
missing when `/lrh-closeout` was added and the upstream skills were never
back-updated.
