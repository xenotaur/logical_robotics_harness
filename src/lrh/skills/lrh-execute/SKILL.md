---
name: lrh-execute
description: >
  Implement one work item end-to-end and land it: resolve the target
  (a WI-ID directly, or the next ready WI under a WS-ID), enforce
  depends_on, run a chain authorization gate, then inline /lrh-implement
  to build and open a PR, and inline /lrh-land to review, confirm, merge,
  and close it out. Use when the user wants to go from "implement this
  work item" to "it's merged" in one traceable session, without manually
  chaining /lrh-implement and /lrh-land themselves.
disable-model-invocation: true
argument-hint: "[WI-ID or WS-ID]"
---

# lrh-execute Skill

This skill is Phase 2 of `PROP-LRH-LAND-EXECUTE` (`/lrh-land` is Phase 1).
It is the compound "implement a work item and land it" skill: given a
`WI-ID`, or a `WS-ID` to resolve to its next ready work item, it enforces
`depends_on`, runs its own chain authorization gate, then drives the work
item through `/lrh-implement` and hands the resulting PR to `/lrh-land`
for the full review → confirm → merge → closeout chain — in one session.

**Interim invocation:** Steps 3–4 inline the sub-skill workflows (read the
target `SKILL.md`'s steps and execute them directly), the same pattern
`/lrh-land` uses for its own Steps 4–7. After `WI-DELIBERATE-MODEL-INVOCATION`
lands, upgrade to direct `Skill` tool calls — a one-step `SKILL.md` edit,
per `PROP-LRH-LAND-EXECUTE` Decision 7.

---

## Inputs

Provide a work item ID or workstream ID as the argument:

```
/lrh-execute WI-SKILLS-LRH-SETUP
/lrh-execute WS-SKILLS
```

A `WI-*` ID implements that item directly. A `WS-*` ID resolves to the
workstream's next ready work item first (Step 1), then proceeds
identically.

---

## Reference Knowledge

Load before running any step:

1. **`src/lrh/skills/lrh-implement/SKILL.md`** — inlined at Step 3.
2. **`src/lrh/skills/lrh-land/SKILL.md`** and its
   `references/land-workflow.md` — inlined at Step 4.
3. **`project/design/proposals/proposed/lrh-land-execute/00_proposal.md`**
   — "Chosen scope" (WS-ID → ready-WI selection rule) and Decision 8 (run
   journal shape), both quoted in full below so this skill does not need
   its own duplicate reference file for a two-rule scope.

---

## Execution Steps

Work through these steps in order. Do not skip Step 2 (chain authorization
gate) — it must precede Step 3.

### Step 1 — Resolve the target work item

**Given `WI-ID`:** enforce `depends_on` — read the work item's frontmatter;
every entry must have `status: resolved`. If any entry is not resolved,
stop and report which one, and do not proceed to Step 2.

**Given `WS-ID`:** find the next ready WI per `PROP-LRH-LAND-EXECUTE`'s
exact rule ("Chosen scope", `00_proposal.md:221-225`): "find the next
**ready WI** (status `proposed`, `depends_on` satisfied, `prompt_ready:
yes` in `lrh work-items readiness` structured output — not merely a zero
exit code — and no `in_progress` or `landed` execution record), then
proceed as WI-ID." Use:

```bash
lrh work-items readiness <candidate-WI-ID> --format md
```

and check its `prompt_ready` field specifically (not the command's exit
code) before treating a candidate as ready. **Stop and report if no ready
WI exists — do not propose creating one.** Creation actions ("create a
work item," "create a workstream," "create a proposal") belong to
`/lrh-next`, not this skill; proposing them here would blur the verb
"execute" into something it isn't.

Once resolved to a `WI-ID` either way, this becomes the target for every
step below.

### Step 2 — Chain authorization gate

Per `DEC-DELIBERATE-CHAIN-INITIATION`, this gate must be reached before
any automated link runs — before `/lrh-implement` in Step 3, not deferred
to `/lrh-land`'s own later gate in Step 4 (by the time that gate is
reached, implementation and PR creation have already happened). Present
the full planned chain to the user:

```
Planned chain for <WI-ID>:
  [Step 3] /lrh-implement (inline) — build the change, open a PR
  [Step 4] /lrh-land (inline) — review-response, confirm-fixes, merge
           gate, closeout, for the PR from Step 3
```

Elicit from the user:
1. **Completion condition** — what "done" means for this whole run (e.g.,
   "PR merged and work item resolved").
2. **Stop-work condition** — what forces a halt-and-report (e.g., "any
   failing test, unexpected reviewer finding, or CI failure that isn't a
   quick fix").

Wait for explicit approval of both conditions. Do not proceed past this
step without the user confirming them.

**This gate does not exempt the gates inside the sub-skills inlined
below.** `/lrh-implement`'s own Step 4 (confirm the implementation plan)
and `/lrh-land`'s own Step 2 (chain authorization gate, for the landing
portion specifically) still fire when reached — chain initiation
authorizes running the links, not skipping their internal gates, the same
principle `/lrh-land` itself applies to the sub-skills *it* inlines. When
`/lrh-land`'s Step 2 is reached in Step 4 below, its completion/stop-work
conditions may be satisfied by re-confirming the conditions already
established here, if the human agrees they still apply, rather than
re-eliciting them from scratch.

### Step 3 — Implement (inline `/lrh-implement`)

Read `src/lrh/skills/lrh-implement/SKILL.md` and execute its Steps 1–10
directly in this session, for the `WI-ID` resolved in Step 1. This mints
a prompt ID, checks idempotence, confirms the implementation plan (its
own Step 4 gate — see the note above), implements the change, validates,
and opens a PR with a populated execution record.

Stop and report if `/lrh-implement`'s own steps stop and report (e.g. an
idempotence check finds a prior `landed`/`in_progress` record) — do not
attempt to route around an inlined sub-skill's own stop condition.

### Step 4 — Land (inline `/lrh-land`)

Read `src/lrh/skills/lrh-land/SKILL.md` and execute its Steps 1–8
directly in this session, for the PR opened in Step 3. This runs
review-response, confirm-fixes (including `round-cap-gate.md`'s
bot-retrigger ceiling — reuse it as-is; do not build a second, parallel
retrigger mechanism), the merge gate, and closeout.

Stop and report if `/lrh-land`'s own steps stop and report — same
principle as Step 3.

### Step 5 — Run journal

Append a structured YAML entry to a scratchpad run journal (not
committed), per `PROP-LRH-LAND-EXECUTE` Decision 8 (`00_proposal.md:294-315`).
Minimum shape:

```yaml
run_id: <datetime-slug>
node: <WS-ID or WI-ID this run started from>
completion_condition: <user-provided at Step 2>
stop_work_condition: <user-provided at Step 2>
actions:
  - type: execute_wi
    wi: <WI-ID resolved in Step 1>
    prompt_id: <PROMPT(...) minted in Step 3>
    pr: <pr-url from Step 3>
    result: pr_open | merged | stopped
    chain_note: <one-line CHAIN-NOTE text from Step 4's closeout>
findings:
  - <gap or observation surfaced during this run>
```

Store the journal at `<scratchpad>/lrh-execute-run-journal.yaml` — a
separate file from `/lrh-land`'s own `<scratchpad>/lrh-land-run-journal.yaml`
(written again, independently, when Step 4 inlines `/lrh-land`'s own Step
8 for the landing portion). This is explicitly a **prototype**, per
Decision 8, for the run report and CHAIN-NOTE accumulation
`PROP-WORKSTREAM-EXECUTION-FRAMEWORK` §5 describes.

### Step 6 — Report

Report to the user:
- The resolved `WI-ID` (and, if input was a `WS-ID`, which WI it resolved
  to and why).
- PR URL and merge commit (from Step 4).
- Execution record path and prompt ID (from Step 3).
- CHAIN-NOTE summary (from Step 4's closeout).
- Any friction or stops encountered during the run.

---

## Quality Checklist

Before reporting completion, verify:

- [ ] For a `WS-ID` input: resolved to a ready WI using the structured
      `prompt_ready` field, not a bare exit code; no creation action
      proposed if none was ready
- [ ] For a `WI-ID` input (direct or resolved): `depends_on` enforced
      before Step 2
- [ ] Chain authorization gate (Step 2) completed before Step 3; both
      completion condition and stop-work condition stated and confirmed
- [ ] `/lrh-implement`'s own Step 4 plan-confirm gate was not bypassed
      when Step 3 reached it
- [ ] `/lrh-land`'s own Step 2 chain-authorization gate was not bypassed
      when Step 4 reached it
- [ ] `/lrh-land`'s own Quality Checklist satisfied for the Step 4 portion
      (REVIEW-LANDED check, SHA-locked merge command, closeout on `main`,
      CHAIN-NOTE placement)
- [ ] Run journal entry appended to `<scratchpad>/lrh-execute-run-journal.yaml`
- [ ] `lrh validate` reports 0 errors after Step 4's closeout

---

## What This Skill Does Not Do

- Does not create work items, workstreams, or proposals when no ready WI
  exists for a `WS-ID` input — that is `/lrh-next`'s scope, not this
  skill's; it stops and reports instead.
- Does not implement `/lrh-next` or `/lrh-run-tree` — Phases 3–4 of
  `PROP-LRH-LAND-EXECUTE`, explicitly deferred.
- Does not bypass any internal confirmation gate inside the inlined
  sub-skills (`/lrh-implement` Step 4, `/lrh-land` Step 2, or any gate
  `/lrh-land` itself inlines) — chain initiation authorizes running the
  links, not skipping their internal gates.
- Does not build a second, parallel bot-retrigger mechanism — reuses
  `round-cap-gate.md` via the inlined `/lrh-land` → confirm-fixes chain.
- Does not implement multiple work items in one invocation — one `WI-ID`
  (direct or `WS-ID`-resolved) per run, mirroring `/lrh-implement`'s own
  constraint.
- Does not implement a persistent run journal — the scratchpad journal is
  a prototype (per `PROP-LRH-LAND-EXECUTE` Decision 8).
