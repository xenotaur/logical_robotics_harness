# Round-Cap Gate — Reference

Where `/lrh-confirm-fixes` Step 8's round-cap check comes from, exactly
what it bounds, and the state schema it reads and writes. Read this before
implementing or modifying Step 8's round-cap logic.

---

## Why this exists

PR #442 in this repo drove Step 8's bot-retrigger loop for 14 rounds — 13
real findings, each fixed and re-triggered — while its own CHAIN-NOTE
recorded `cycles=1`, because `cycles` counts
`/lrh-review-response` ↔ `/lrh-confirm-fixes` *invocations*, not the
bot-retrigger batches that actually happened inside a single Step 8 run
(`project/executions/AD_HOC/2026_07_30_05_33_51_LRH_MERGE_GATE_POLICY_391AEF_CONFIRM.md:54-61,102`).
GitHub Copilot's review-bot credit pool is shared across every concurrently
active project in this workspace, with no per-repo partitioning at the
platform level — an unattended long loop on one repo can silently draw
down budget an unrelated, higher-priority repo needs. `DEC-DELIBERATE-CHAIN-INITIATION`
already requires a human-set stop-work condition before any chain of these
rounds runs automatically; this mechanism turns that into a persistent,
recurring, numeric checkpoint instead of prose re-elicited each run.

## What "round" means

One **bot-retrigger batch**: a single pass of Step 8's `gh pr comment
"@codex review"` / `gh pr comment "@copilot review"` mentions (or whichever
reviewers `REVIEWS.md` documents), issued together. This is the unit PR
#442's incident actually repeated 14 times — not `cycles`, which stayed at
`1` throughout that incident and would never have triggered a
cycles-based cap.

## What this bounds — and what it does not

This check governs **only** `/lrh-confirm-fixes` Step 8's own
bot-retrigger action. It does **not**:

- Gate `/lrh-review-response` — that skill has no bot-retrigger action to
  gate (verified by inspection: no `@codex review`/`@copilot review` call
  exists anywhere in `lrh-review-response/SKILL.md`). If a future item
  gives it one, this scope boundary needs revisiting so that addition
  doesn't silently bypass the cap.
- See or limit Jules-originated PR activity, or any human-driven review
  request — both are structurally outside this skill's reach (Codex and
  Jules cannot invoke Claude Code skills at all; see
  `WI-TEMPLATE-AUDIT-WORK-ITEMS.md:47-53`).
- Bound aggregate GitHub Copilot spend — it bounds one specific mechanism
  (unattended, automatic retrigger escalation), not total platform usage.
  No GitHub billing/usage API is queried; the human supplies portfolio
  context (what else is running, what's urgent) at the gate, since no
  automated source for that currently exists in this project.

## State schema

One JSON file per PR, at `project/executions/round_state/<pr-slug>.json`
(`<pr-slug>` derived the same way branch slugs are elsewhere — lower-kebab
from the PR's branch name). Deliberately **not** a `.md` file:
`lrh validate`'s execution-record scan globs `project/executions/**/*.md`
(`src/lrh/control/validator.py`), so a non-`.md` extension keeps this file
outside that validation surface without needing a schema exemption.

```json
{
  "pr": "<pr-url>",
  "ceiling": 3,
  "completed_count": 0,
  "pending_attempt": null
}
```

- `ceiling` — the currently authorized round limit. Starts at 3 (the
  default first suggestion); updated synchronously whenever the human
  authorizes a new value at the three-way gate. Never reset or
  reconstructed from CHAIN-NOTE — CHAIN-NOTE is written post-hoc, only at
  closeout, and would be stale or absent for an in-progress PR.
- `completed_count` — number of retrigger batches promoted to completed.
  Incremented as soon as any mention in a batch is confirmed submitted
  (see "Any-side-effect-counts promotion" below) — not gated on the whole
  batch succeeding.
- `pending_attempt` — `null` when no batch is in flight. Set, synchronously,
  to the list of reviewers about to be mentioned *before* the `gh pr
  comment` calls for a batch are issued; cleared when that batch is
  promoted or discarded. A non-null value found at the start of a new
  invocation means a prior run died mid-batch and must be reconciled
  before anything else happens.

## Check-then-attempt ordering

Before starting a batch: check `completed_count >= ceiling`. If true, stop
— present the three-way gate, do not start the batch. If false, persist
`pending_attempt` and start the batch, promoting to
`completed_count + 1` as soon as the first mention in it is confirmed
submitted.

Worked example, ceiling 3: batches 1, 2, and 3 each pass the check
(`0 >= 3`, `1 >= 3`, `2 >= 3` are all false) and raise the count to 3; a
4th batch is blocked, since `3 >= 3` is true, before it starts. Ceiling
`N` means `N` batches are allowed to run; the gate fires before the
`(N+1)`th.

## Any-side-effect-counts promotion

A batch is promoted to completed the moment **any** mention in it is
confirmed submitted — not only after every mention in the batch succeeds.
Requiring full-batch success before counting creates a real cost-cap
loophole: a batch where one mention posts and another fails could be
retried indefinitely, each retry a real, credit-consuming external side
effect, without the counted round ever reaching the ceiling. An ambiguous
submission result (a network timeout with no confirmed server-side
outcome) is treated as submitted, not unsubmitted — conservative toward
counting more, never fewer, side-effect-bearing attempts. Unsubmitted
mentions from a partially-successful batch may be retried without
incrementing the counter again, since the round is already counted.

## Crash-recovery reconciliation

Every invocation of the round-cap check reconciles `pending_attempt`
*before* running the ceiling check for a new batch. If a process died
between persisting an attempt and promoting it, a restart would otherwise
see the stale, lower `completed_count`, pass the ceiling check, and start
another full batch — exceeding the cap the attempt marker exists to
prevent. Reconciliation treats an orphaned attempt as completed if it may
have produced any submission (conservative, same rule as promotion);
otherwise it is discarded without incrementing.

## The three-way gate

Fires only when the ceiling check blocks. Presents: current
`completed_count`, `ceiling`, and a one-line findings summary from prior
rounds if derivable from earlier review comments. The human answers one
of:

- **Authorize a new ceiling** — default suggestion sequence is
  3 → 10 → 20; beyond 20, ask for the next value directly rather than
  computing a further default (no formula — 30, 40, or doubling are all
  equally plausible and none is grounded). The actual next ceiling is
  always human-supplied, never auto-applied. Written to `ceiling`
  synchronously before the next batch starts.
- **Deny and stop** — no further batches; the PR's review state as of the
  last completed batch stands.
- **Pause** — defer the decision; no batch starts until the human
  responds.

This is the one point in Step 8 that always requires an explicit human
answer — never an inferred signal, and never satisfied by a bot response.

## CHAIN-NOTE relationship

The round-cap counter (`completed_count`) is a distinct, finer-grained
metric from CHAIN-NOTE's `cycles` field — see
`src/lrh/skills/lrh-land/references/land-workflow.md`'s `stops`/`note`
field docs for how a round-cap gate crossing should be recorded there.
`cycles` and `completed_count` measure different things and are not
interchangeable.
