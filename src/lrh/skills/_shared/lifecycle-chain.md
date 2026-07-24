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

**Variant B — planning-artifact PR with no record** (`/lrh-work-item`,
`/lrh-proposal`, `/lrh-workstream`, `/lrh-create-skill`, `/lrh-doc-audit`:
skills that create no execution record). The chain ends at merge:

```text
Next steps: run `/lrh-review-response <pr-url>` to address reviewer comments
(repeat as needed), then `/lrh-confirm-fixes <pr-url>` to verify the fixes
against the current diff and resolve the review threads before merge, then
merge. This PR creates no execution record, so `/lrh-closeout` does not apply
— there is nothing to land.
```

Do not append `/lrh-closeout` to a Variant B site: the skill produces no
record for closeout to act on, so the suggestion dead-ends. `/lrh-readiness`
is a hybrid — a refinement-only PR is Variant B, but if it pushed to an
existing `/lrh-implement` branch it inherits that PR's Variant A chain.

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
| `/lrh-work-item` | `references/lrh-work-item-workflow.md` — "Suggested next steps after skill completes" | No (planning PR) | B for the planning PR (ends at merge); the "Evidence and closeout" section separately points the eventual *implementation* PR at `/lrh-closeout` |
| `/lrh-implement` | `SKILL.md` — Step 10 "Report and offer closeout" | Yes | A |
| `/lrh-review-response` | `SKILL.md` — "Report to the user" | Yes | `/lrh-confirm-fixes` before merge (model phrasing) |
| `/lrh-confirm-fixes` | `SKILL.md` — Step 8 "Report to the user" | Yes | `/lrh-closeout` post-merge, green verdict only |
| `/lrh-proposal` | `SKILL.md` — Step 9 "Offer follow-on and report" | No | B |
| `/lrh-workstream` | `SKILL.md` — Step 9 "Offer follow-on and report" | No | B |
| `/lrh-readiness` | `SKILL.md` — Step 9 "Report" | Conditional | B for a refinement-only PR; inherits A when it pushes to an existing `/lrh-implement` branch |
| `/lrh-doc-work` | `SKILL.md` — end of Step 12 "Create execution record" | Yes | A |
| `/lrh-doc-organize` | `SKILL.md` — end of Step 11 "Create execution record" | Yes | A |
| `/lrh-doc-audit` | `SKILL.md` — Step 10 "Offer commit" | No | B on the "Open a PR" branch only; the commit-to-main branch has no PR and no chain |
| `/lrh-create-skill` | `SKILL.md` — Step 10 "Report" | No | B, plus `lrh skills install` after merge |

Every site above also exists as a byte-identical mirror under
`.claude/skills/`. Edit both.

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
