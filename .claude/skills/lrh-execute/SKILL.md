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

**Inlined invocation, by design, not as an interim step:** Steps 3–4 inline
the sub-skill workflows (read the target `SKILL.md`'s steps and execute them
directly), the same pattern `/lrh-land` uses for its own Steps 4–7.
`WI-DELIBERATE-MODEL-INVOCATION` resolved this as permanent — see
`/lrh-land/references/land-workflow.md` § Interim Invocation Pattern for why
`PROP-LRH-LAND-EXECUTE` Decision 7's original upgrade-to-`Skill()` plan is
superseded.

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

1. **`/lrh-implement/SKILL.md`** — inlined at Step 3. Resolve this as an
   installed sibling skill (the same `/skill-name/SKILL.md` reference
   style `/lrh-land` itself uses for the sub-skills *it* inlines), not a
   hardcoded `src/lrh/skills/...` path — `/lrh-execute` may be installed
   into a client repository via `lrh skills install`, where no
   `src/lrh/skills/` tree exists at all. The installed location is
   whatever the selected agent skills directory resolves it to.
2. **`/lrh-land/SKILL.md`** and its `references/land-workflow.md` —
   inlined at Step 4, resolved the same way.

The WS-ID → ready-WI selection rule (Step 1) and the run journal shape
(Step 5) are quoted in full inline below, not loaded from
`PROP-LRH-LAND-EXECUTE`'s proposal file at runtime — that file lives only in
the LRH harness repo itself and would not exist in a client repository
this skill is installed into. `PROP-LRH-LAND-EXECUTE` is cited by name
for provenance only, not as a required preload.

---

## Execution Steps

Work through these steps in order. Do not skip Step 2 (chain authorization
gate) — it must precede Step 3.

### Step 1 — Resolve the target work item

**Given `WI-ID`:** enforce `depends_on` — read the work item's
frontmatter. Each entry is a bare `WI-*` ID with no embedded status;
locate that WI's own file the same way the `WS-ID` case below locates a
workstream file, since a dependency can live in any status bucket:

```bash
find project/work_items/ -name "<dependency-WI-ID>.md"
```

Every entry must have `status: resolved`. If any entry is not resolved
(or its file can't be found at all — report that distinctly, not as
"not resolved"), stop and report which one, and do not proceed to Step 2.

**Given `WS-ID`:** find the next ready WI per `PROP-LRH-LAND-EXECUTE`'s
exact rule ("Chosen scope", `00_proposal.md:221-225`): "find the next
**ready WI** (status `proposed`, `depends_on` satisfied, `prompt_ready:
yes` in `lrh work-items readiness` structured output — not merely a zero
exit code — and no `in_progress` or `landed` execution record), then
proceed as WI-ID." That rule presupposes an ordered candidate list, which
comes from the workstream itself:

```bash
find project/workstreams/ -name "<WS-ID>.md"
```

(workstreams live under `proposed/`, `active/`, `resolved/`, or
`abandoned/` — locate the file rather than assuming a bucket). Read its
frontmatter `work_items:` list, and evaluate its entries **in list
order** — do not evaluate WIs from any other workstream, and do not
guess an ordering the workstream file doesn't state. For each candidate,
in order:

```bash
lrh work-items readiness <candidate-WI-ID> --format md
```

Check its `prompt_ready` field specifically (not the command's exit
code), and check `status: proposed`, `depends_on` satisfied (same
lookup as the `WI-ID` case above — `find project/work_items/ -name
"<dependency-WI-ID>.md"` per entry, every entry `resolved`), and no
`in_progress`/`landed` execution record:

```bash
grep -rh "^status: \(in_progress\|landed\)" project/executions/<candidate-WI-ID>/ 2>/dev/null
```

(no output means no *blocking* record — `failed`/`reverted`/`superseded`
records don't disqualify a candidate, only `in_progress`/`landed` do,
matching the rule's own wording; an unfiltered `^status:` grep would
wrongly disqualify on any prior record regardless of its value). Take
the **first** candidate in `work_items:` order that satisfies all of the
above. **Stop and report if no ready WI exists — do not propose creating
one.** Creation actions ("create a work item," "create a workstream,"
"create a proposal") belong to `/lrh-next`, not this skill; proposing
them here would blur the verb "execute" into something it isn't.

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

**Run the chain-defaults propose-and-confirm flow before eliciting
conditions from scratch** — canonical source:
`src/lrh/skills/_shared/chain-defaults.md`, also inlined in
`/lrh-land/references/land-workflow.md` § Chain-defaults
propose-and-confirm flow. It pre-fills the conditions below from
`project/config/chain-defaults.yaml` (proposing the steelmanned defaults on
first encounter), and under `chain_init_confirmation: skip_if_opted_in`
with valid user-local consent and no special condition firing, may skip
the live confirming reply entirely — always falling back to the live-reply
path below otherwise.

Elicit from the user (or, under a validated `skip_if_opted_in` skip, display
without asking):
1. **Completion condition** — what "done" means for this whole run
   (pre-filled from the stored profile, or "PR merged and work item
   resolved" on first encounter).
2. **Stop-work condition** — what forces a halt-and-report (pre-filled
   from the stored profile, or "any failing test, unexpected reviewer
   finding, or CI failure that isn't a quick fix" on first encounter).

Wait for explicit approval of both conditions, unless the skip path above
applied. Do not proceed past this step without either the user confirming
them or a validated skip. If the user's live reply diverges from the
stored values, apply the profile-update offer at the end of the run rather
than silently persisting the override.

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

Read `/lrh-implement/SKILL.md` and execute **all** of its steps — 1, 1.5,
2, 3, 4, 5, 6, 7, 8, 9, 10, including Step 1.5 (prior-art check), not just
"1 through 10" read as excluding the decimal-numbered step — directly in
this session, for the `WI-ID` resolved in Step 1. This mints a prompt ID,
checks idempotence, confirms the implementation plan (its own Step 4 gate
— see the note above), implements the change, validates, and opens a PR
with a populated execution record.

**Populate the execution record's `pr:` field before proceeding to Step
4.** `/lrh-implement`'s own Step 9 does not do this — its
`record-execution` call and its "immediately edit" instruction populate
`agent`, `instruction_source`, and `session_transcript`, but not `pr:`,
even though the PR already exists by then (Step 8 ran first). Pass it
directly: `lrh prompt record-execution ... --pr <pr-url-from-step-8>`.
Without this, `/lrh-land`'s Step 1 primary-record search (which matches
on `pr: <pr-url>`) finds nothing, falls back to an `AD_HOC` backfill, and
closeout's matrix does not resolve a WI for `AD_HOC` — the target `WI-ID`
would stay `proposed` even after the PR merges, silently defeating this
skill's own advertised end-to-end guarantee. (This is a gap in
`/lrh-implement/SKILL.md` itself, not unique to inlining it here — see
`project/design/backlog.md` for the broader fix.)

**If `/lrh-implement`'s own steps stop and report** (e.g. an idempotence
check finds a prior `landed`/`in_progress` record), do not attempt to
route around it — but do not just return either: go to Step 5 first and
record this as a `stopped` action, then report. Skipping straight to
reporting on a stop makes the run journal's own `result: stopped` value
unreachable.

### Step 4 — Land (inline `/lrh-land`)

Read `/lrh-land/SKILL.md` and execute its Steps 1–8 directly in this
session, for the PR opened in Step 3. This runs review-response,
confirm-fixes (including Step 8's provisional no-progress review cap —
reuse it as-is; do not build a second, parallel review-cap mechanism), the
merge gate, and closeout.

If `/lrh-land`'s own steps stop and report, same principle as Step 3: go
to Step 5 first and record it as a `stopped` action, then report — do not
skip straight to reporting.

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

- [ ] For a `WS-ID` input: candidates drawn only from that workstream's
      own `work_items:` list, evaluated in list order; resolved to a
      ready WI using the structured `prompt_ready` field, not a bare exit
      code; no creation action proposed if none was ready
- [ ] For a `WI-ID` input (direct or resolved): `depends_on` enforced
      before Step 2
- [ ] Chain authorization gate (Step 2) completed before Step 3; both
      completion condition and stop-work condition stated and confirmed
- [ ] `/lrh-implement`'s own Step 4 plan-confirm gate was not bypassed
      when Step 3 reached it
- [ ] `/lrh-implement`'s own Step 1.5 (prior-art check) was not skipped
- [ ] Step 3's execution record has `pr:` populated before Step 4 starts
- [ ] `/lrh-land`'s own Step 2 chain-authorization gate was not bypassed
      when Step 4 reached it
- [ ] `/lrh-land`'s own Quality Checklist satisfied for the Step 4 portion
      (REVIEW-LANDED check, SHA-locked merge command, closeout on `main`,
      CHAIN-NOTE placement)
- [ ] If Step 3 or Step 4 stopped, a `stopped` action was recorded in the
      run journal (Step 5) before reporting — not skipped past
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
