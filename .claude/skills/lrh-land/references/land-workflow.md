# /lrh-land Workflow Reference

This file is the algorithmic reference for `/lrh-land`. Load it at the
start of the skill (before Step 1) so all rule definitions are available
during execution.

---

## Five Glue-Logic Rules

These rules are applied as explicit algorithmic steps, not re-derived from
prose each run. Source: `PROP-LRH-LAND-EXECUTE` Decision 3.

| Logic | Rule |
|---|---|
| **Primary record selection** | `grep pr: <url>` across `project/executions/`; exclude `*_REVIEW.md`, `*_CONFIRM.md`, `*_CLOSEOUT_NOTE.md` from results |
| **Found-or-backfill** | Found → body is immutable; CHAIN-NOTE goes in a new `_CLOSEOUT_NOTE` record with `rerun_of:`. Not found → backfill record authored directly; CHAIN-NOTE in that record |
| **CHAIN-NOTE placement** | Always in the record being *authored* this run; never appended to an already-merged record body |
| **Main-worktree-lock** | When all worktrees have `main` checked out: `git fetch → checkout -b tmp-<slug> origin/main → apply changes → push tmp-<slug>:main → delete tmp-<slug>` |
| **Stale-branch safety** | Before reusing a planning-PR branch: `git diff origin/main <branch> --stat` must confirm zero net lines |

**Multi-round review-response naming.** A single `/lrh-land` run can invoke
`/lrh-review-response` more than once (Step 4's loop). Each round reuses the
*same* slug — do not append a round-number suffix (e.g. `-round2`) to
disambiguate. `lrh prompt record-execution`'s timestamp prefix gives each
round a distinct filename in the normal case (it's second-resolution and
errors rather than overwrites on an exact collision), and every round's
file still ends in the literal `_REVIEW.md`. A round-numbered suffix like
`_REVIEW_ROUND2.md`
breaks the primary-record-selection exclusion above (`grep -v "_REVIEW\.md$"`
only matches the literal suffix) — a later `/lrh-land` re-run could pick up
that file as the primary record instead of excluding it. If the round number
needs to be recorded, put it in the record body or the CHAIN-NOTE's `cycles`
field, not the filename.

---

## CHAIN-NOTE Format

```text
cycles=<N>; stops=<N>; gates=[<gate-list>]; friction=<phrase or none>; note="<free text>"
```

Field definitions:

| Field | Description |
|---|---|
| `cycles` | Number of review-response → confirm-fixes iterations in this run |
| `stops` | Number of times the chain halted before reaching completion, **including round-cap gate crossings** (see below) |
| `gates` | Human gates encountered, e.g. `[merge]` or `[merge, confirm]` |
| `friction` | Brief phrase describing the primary friction source, or `none` |
| `note` | Free text; record design findings, backfill path, noteworthy deviations, or **round-cap ceilings authorized this run** (see below) |

**Round-cap counter vs. `cycles`.** `/lrh-confirm-fixes` Step 8's round-cap
gate (`src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md`)
counts bot-retrigger batches — a finer-grained, separate metric from
`cycles`, which counts whole review-response ↔ confirm-fixes iterations.
A single `cycles` count can span many round-cap batches (this is exactly
what happened on PR #442: `cycles=1` while the round-cap-relevant count
would have been 14). Do not conflate the two, and do not derive one from
the other.

Each time the round-cap gate blocks and the human is asked to authorize a
new ceiling, deny, or pause: count it toward `stops`, and record the
ceiling the human authorized (or "denied"/"paused") in `note`, e.g.
`note="round-cap: authorized ceiling 3->10"`.

Example:

```text
cycles=2; stops=0; gates=[merge]; friction=stale-review; note="Codex reviewed first commit only; second review pass required after rebase."
```

Example with a round-cap crossing:

```text
cycles=1; stops=1; gates=[merge]; friction=none; note="round-cap: authorized ceiling 3->10 after 3 real findings"
```

---

## Found-or-Backfill Matrix

| Condition | Record action | CHAIN-NOTE location |
|---|---|---|
| Primary record found | Body is **immutable** — do not edit | New `_CLOSEOUT_NOTE` record; frontmatter must include `rerun_of: <primary-record-id>` |
| No primary record | Author a new backfill `AD_HOC` record in `project/executions/AD_HOC/` | Directly in the `# Result` section of the backfill record being authored |

A **primary record** is one whose filename does NOT end with `_REVIEW.md`,
`_CONFIRM.md`, or `_CLOSEOUT_NOTE.md`, and whose `pr:` field matches the
PR URL.

A `_CLOSEOUT_NOTE` record must be placed in the same execution directory
bucket as the primary record (e.g., `project/executions/WI-FOO/` if the
primary is there, not `AD_HOC/`).

---

## Run Journal Skeleton

The run journal is a prototype scratchpad file (not committed to the repo).
Append one entry per `/lrh-land` invocation. Minimum shape from
`PROP-LRH-LAND-EXECUTE` Decision 8:

```yaml
run_id: <datetime-slug>
node: <WS-ID or WI-ID associated with this PR, or AD_HOC>
completion_condition: <user-provided at Step 2>
stop_work_condition: <user-provided at Step 2>
actions:
  - type: land_pr
    wi: <WI-ID or AD_HOC>
    prompt_id: <PROMPT(...)>
    pr: <pr-url>
    result: merged | stopped
    chain_note: <one-line CHAIN-NOTE text>
findings:
  - <gap or observation surfaced during this run>
```

Store the journal at: `<scratchpad>/lrh-land-run-journal.yaml`

The `<scratchpad>` path is the session scratchpad directory reported at the
start of the Claude Code session.

---

## Interim Invocation Pattern

Steps 4–7 in Phase 1 inline the sub-skill workflows: read the target
`SKILL.md` and execute its steps directly within the current session. This
avoids requiring `WI-DELIBERATE-MODEL-INVOCATION` to land before `/lrh-land`
can ship.

Sub-skills to inline per step:

| Step | Sub-skill to inline |
|---|---|
| Step 4 (review-response) | `/lrh-review-response/SKILL.md` |
| Step 5 (confirm-fixes) | `/lrh-confirm-fixes/SKILL.md` |
| Step 7 (closeout) | `/lrh-closeout/SKILL.md` |

After `WI-DELIBERATE-MODEL-INVOCATION` lands (which removes
`disable-model-invocation: true` from the lifecycle skills), upgrade Steps
4–7 to direct `Skill` tool calls. The upgrade is a one-step `SKILL.md` edit
per step and does not require a new PR or a WI of its own. Source:
`PROP-LRH-LAND-EXECUTE` Decision 7.
