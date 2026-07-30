---
id: DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT
---

# Pre-Mint Slug Idempotence Is a Default, Not a Mandate

Status: accepted
Date: 2026-07-30

## Summary

Filename-slug search against an execution bucket (matched to the complete
trailing filename segment, not a substring) is authoritative evidence for
detecting a prior run of the same logical slug *before* a prompt ID exists
to check exactly — a case the existing exact-ID lookup rule cannot cover,
since `lrh prompt label` mints a fresh timestamped ID every call. What a
skill does with a match beyond "block or don't" is a **default starting
point**, not a rule `PROMPTS.md` enumerates and enforces for every skill
and every status value. A skill that deviates documents its own deviation
locally, with a one-line rationale — the same way `lrh-confirm-fixes`
already does.

## Context

- `PROMPTS.md`'s "Soft idempotence before execution" section states that
  exploratory search must never drive blocking or rerun decisions — only
  an exact `prompt_id` lookup (`lrh prompt check-execution`) is
  authoritative. But `lrh-review-response`, `lrh-proposal`,
  `lrh-work-item`, and `lrh-workstream` all search
  `project/executions/AD_HOC/` by filename slug *before* minting a prompt
  ID, and treat a match as authoritative for blocking — because the
  exact-ID mechanism genuinely cannot answer "has this slug run before,"
  there being no ID yet to look up (harness PR #438, then #440).
- PR #440 first tried to resolve this by writing one universal status
  matrix into `PROMPTS.md` covering every skill's behavior on every
  possible match status. Three review rounds each found a real gap in
  that matrix: an undefined placeholder, a substring-match false positive,
  a missing-directory error, status-blind blocking, missing `rerun_of`
  propagation, ambiguous-match handling, a missed third copy of the rule
  (`project/executions/README.md`), and finally — the one that prompted
  this decision — two structural gaps rather than typos: (a)
  `src/lrh/skills/lrh-confirm-fixes/SKILL.md:177-187` already documents a **deliberate**
  deviation ("Unlike `/lrh-review-response`'s hard stop on a prior record,
  a prior `_CONFIRM` record here is **not** a blocker — re-verification is
  cheap and safe, since live thread state may have legitimately changed
  between rounds (Decision 12)" — citing
  `project/design/proposals/adopted/lrh-confirm-fixes/00_proposal.md`
  Decision 12) that the universal matrix contradicted; (b) the `planned`
  status exists in the vocabulary but fit none of the matrix's three
  buckets (blocking / non-blocking / ambiguous).
- Each fix to the matrix reliably surfaced the next gap — the matrix was
  trying to be a complete specification of behavior that individual skills
  already owned and, in `lrh-confirm-fixes`'s case, had already
  legitimately diverged from with a documented reason.
- `lrh-confirm-fixes`'s existing citation of its own Decision 12 is a
  precedent already working in this repo: a skill states a default,
  deviates from it, and cites why — without the shared policy document
  trying to anticipate and encode every skill's exception in advance.

## Decision

`PROMPTS.md`'s "Pre-mint duplicate detection by slug" subsection (and its
mirrors in `project/executions/README.md` and the `project_bootstrap`
template stubs) states two things, and only two things, as centrally
authoritative:

1. **The invariant.** A filename search matched to the complete trailing
   segment of the slug (not a bare substring) is authoritative evidence
   for the narrow "has this slug already produced a record" question —
   distinct from, and not subject to, the general rule against exploratory
   search driving blocking decisions.
2. **The default.** Absent a documented reason to differ: a match with a
   blocking-shaped status (`landed`/`in_progress`) stops and reports
   unless the prompt explicitly asks for a rerun; a match with a
   terminal-shaped status (`failed`/`reverted`/`superseded`) is summarized
   and continued past. This is explicitly labeled a default, not a
   requirement every skill must implement identically.

Everything else — exhaustive status coverage (including `planned`),
multi-match precedence, cross-branch/cross-worktree detection, and any
skill's reason for deviating from the default — is **not** re-derived or
enumerated in `PROMPTS.md`. A skill that needs to diverge, or that
encounters a status/scenario the default doesn't cover, documents its own
behavior locally with a short rationale, following the
`lrh-confirm-fixes`/Decision-12 pattern — it does not require amending
this shared document first.

## Rationale

- Mirrors this repo's own working precedent (`lrh-confirm-fixes` citing
  Decision 12) instead of inventing a new mechanism for the same problem.
- Applies ordinary policy/mechanism separation: a shared policy document
  should state the invariant that must never be violated and a sensible
  default, not exhaustively specify every subsystem's behavior — that is
  what caused `PROMPTS.md` and actual skill behavior to drift apart
  (`lrh-review-response` never matched what PR #438/#440 described as "the
  applied pattern") and what caused three straight review rounds to keep
  finding the next gap in an ever-expanding matrix.
- Resolves the `lrh-confirm-fixes` contradiction without editing that
  skill under review pressure on an unrelated docs PR, and without
  silently dropping the contradiction (the previous state) either — it
  removes the false claim that a universal matrix binds it.

## Alternatives considered

1. **Keep expanding the universal matrix** to cover `planned`, multi-match
   precedence, and an explicit carve-out for `lrh-confirm-fixes`.
   Pros: one table, fully explicit. Cons: demonstrated three times over to
   reliably find another gap on the next review round; every new skill or
   status value becomes a required edit to a shared, increasingly load-bearing
   document.
2. **Make slug-based discovery non-blocking everywhere**, complying with
   the pre-existing general rule literally. Pros: no exception to
   maintain. Cons: turns every rerun path interactive by default, a real
   behavior change to four working skills under review pressure — rejected
   earlier in this same thread (harness PR #438/#440) for the same reason.
3. **Build a real CLI mechanism** (e.g. `check-execution --slug`) so
   slug-based duplicate detection becomes tested, authoritative tooling
   rather than a hand-rolled `find` in prose. The most complete long-term
   answer, and still tracked (see `project/design/backlog.md`
   "Filename-slug idempotence search drives blocking, contrary to
   `PROMPTS.md`") — but real CLI feature work, not a fit for an in-flight
   docs PR, and this decision doesn't need it to be correct: the
   invariant/default split is stable however the mechanism is eventually
   implemented.

## Consequences

- `PROMPTS.md`, `project/executions/README.md`, and both
  `project_bootstrap/prompt_workflow` stub copies restate the invariant
  and the labeled default, and no longer claim a specific list of skills
  "applies the pattern" in full — `lrh-proposal`/`lrh-work-item`/
  `lrh-workstream` follow the default; `lrh-review-response` predates it
  and is tracked as a follow-up to align (`project/design/backlog.md`
  "Idempotence-check refinements deferred from PR #438", item 5).
  `lrh-confirm-fixes`'s status-handling deviation (Decision 12) remains
  correct and needs no change, but its own `find` at
  `src/lrh/skills/lrh-confirm-fixes/SKILL.md:180-181` uses the same
  unanchored substring glob as `lrh-review-response` — it does **not**
  yet meet this record's trailing-segment invariant either, and is
  tracked alongside `lrh-review-response` in the same backlog item
  (item 5, retitled to cover both).
- The `planned`-status gap is **not** resolved centrally here — no skill
  has yet needed a concrete answer for it. Deferred to whichever skill
  first needs it, at which point it gets a real, use-case-grounded answer
  instead of a guessed one bolted onto this decision.
- This is the **third** promoted `project/memory/decisions/*.md` file —
  `precedence_semantics.md` was first, `DEC-DELIBERATE-CHAIN-INITIATION.md`
  second (2026-07-24), this one third. The `/lrh-decision` skill idea in
  `project/design/backlog.md` was deferred pending "a second
  `project/memory/decisions/*.md` file... created by hand"; that
  condition was already met by the second file without the backlog entry
  being updated, and this third one makes it unambiguous — noted there
  directly rather than left to be rediscovered again.

## Revisit conditions

Revisit when:

- a skill actually needs to handle a `planned`-status pre-mint match, and
  the answer that emerges there suggests the default itself should change
  (not just that one skill's local documentation);
- `lrh-review-response` is brought up to the default (item 5 in the
  "Idempotence-check refinements deferred from PR #438" backlog entry) —
  confirm at that point whether it adopts the default as-is or documents
  its own deviation;
- the CLI-tooling alternative (option 3 above) is built, at which point
  this record's invariant/default split should be re-examined against
  whatever the CLI actually enforces.
