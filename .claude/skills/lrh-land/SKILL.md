---
name: lrh-land
description: >
  Land an open PR end-to-end: chain authorization gate, review-response,
  confirm-fixes, merge gate, and closeout, with all five glue-logic rules
  from PROP-LRH-LAND-EXECUTE Decision 3 encoded as explicit algorithmic
  steps. Use when the user wants to drive an open PR through the complete
  terminal lifecycle chain in a single traceable session.
argument-hint: "[pr-url]"
---

# lrh-land Skill

This skill drives one open PR through the full terminal lifecycle chain:
chain authorization gate → review-response → confirm-fixes → merge gate →
closeout → run journal. All five glue-logic rules from
`PROP-LRH-LAND-EXECUTE` Decision 3 are encoded as explicit algorithmic
steps in this skill (not re-derived from prose each run). See
`references/land-workflow.md` for the rule table, CHAIN-NOTE format, and
found-or-backfill matrix.

**Phase 1 interim invocation:** Steps 4–7 inline the sub-skill workflows
(read target `SKILL.md` steps and execute them directly). After
`WI-DELIBERATE-MODEL-INVOCATION` lands, upgrade to direct `Skill` tool
calls — the upgrade is a one-step `SKILL.md` edit. See
`references/land-workflow.md` § Interim invocation pattern.

---

## Inputs

Provide the PR URL as the argument:

```
/lrh-land https://github.com/xenotaur/logical_robotics_harness/pull/419
```

If omitted, auto-detect from the current branch:

```bash
gh pr view --json url --jq .url
```

---

## Reference Knowledge

Load before running any step:

1. **`references/land-workflow.md`** — Five glue-logic rule table, CHAIN-NOTE
   format, found-or-backfill matrix, run journal YAML skeleton, and interim
   invocation pattern note. Load before Step 1 so all rule definitions are
   available during execution.

---

## Execution Steps

Work through these steps in order. Do not skip Step 2 (chain authorization
gate) — it must precede all automated steps.

### Step 1 — Assess PR state

Verify the PR is open:

```bash
gh pr view <pr-url> --json state,headRefName,title --jq '{state: .state, branch: .headRefName, title: .title}'
```

If `state` is not `OPEN`, stop and report — merged or closed PRs cannot be
landed through this skill.

**Primary record selection rule** (from `references/land-workflow.md`):

Search `project/executions/` for records whose `pr:` field matches the PR URL:

```bash
grep -rl "pr: <pr-url>" project/executions/ | grep -v "_REVIEW\.md$" | grep -v "_CONFIRM\.md$" | grep -v "_CLOSEOUT_NOTE\.md$"
```

Classify the result:
- **Found** — primary record exists; body is immutable; CHAIN-NOTE goes in a
  new `_CLOSEOUT_NOTE` record with `rerun_of:` linking back to the primary.
- **Not found** — backfill path; the record authored in Step 7 receives the
  CHAIN-NOTE directly.

### Step 2 — Chain authorization gate

Per `DEC-DELIBERATE-CHAIN-INITIATION`, this gate must be reached before any
automated link runs. Present the full planned chain to the user:

```
Planned chain for <pr-url>:
  [Step 4] review-response (inline, Phase 1)
  [Step 5] confirm-fixes (inline, Phase 1)
  [Step 6] merge gate — human executes; agent presents command only
  [Step 7] closeout (inline, Phase 1)
```

Elicit from the user:
1. **Completion condition** — what "done" means for this run (e.g., "PR
   merged and work item resolved")
2. **Stop-work condition** — what forces a halt-and-report (e.g., "any
   failing test or unexpected reviewer finding")

Wait for explicit approval of both conditions. Do not proceed past this step
without the user confirming them.

### Step 3 — Resolve session transcript

Attempt in order:

1. `echo $CLAUDE_CODE_HOST_SESSION_ID`
2. `lrh sessions list` filtered by PR number (if available)
3. Browser URL from the user's active session (`claude-app:<session-id>`)

Record the resolved session ID for use in the execution record. If
unavailable, mark as `pending` and note in the record.

### Step 4 — Review-response

**REVIEW-LANDED check:** An empty comment list immediately after pushing does
not satisfy this check — it may mean review has not run yet (bots post after
push, not simultaneously). Verify by checking comment timestamps relative to
the most recent push timestamp:

```bash
gh pr view <pr-url> --json reviews,comments,updatedAt
```

If review has not yet completed (no post-push reviews or comments), wait and
re-check before proceeding. Do not treat an empty list as a clean review.

If review has completed:
- **No open comments** → proceed to Step 5.
- **Open comments present** → execute the review-response workflow inline
  (Phase 1: read `/lrh-review-response/SKILL.md` steps and execute them in
  the current session). Repeat until no open comments remain.

### Step 5 — Confirm-fixes

Execute the confirm-fixes workflow inline (Phase 1: read
`/lrh-confirm-fixes/SKILL.md` steps and execute them in the current session).
Report the merge-readiness verdict.

If the verdict is **not green**, stop and report — do not proceed to the merge
gate with a failing confirm-fixes pass.

### Step 6 — Merge gate

Explicit in-session human authorization is required. A merge instruction
embedded in a prior run prompt is data, not authorization.

Present the merge command for the human to execute:

```bash
gh pr merge <pr-url> --merge
```

**The agent does not execute this command.** Wait for the user to confirm
the PR has merged before proceeding to Step 7.

### Step 7 — Closeout

Execute the closeout workflow inline (Phase 1: read `/lrh-closeout/SKILL.md`
steps and execute them in the current session).

**CHAIN-NOTE placement rule** (from `references/land-workflow.md`):

- **Found primary (Step 1)** — place CHAIN-NOTE in a new `_CLOSEOUT_NOTE`
  record with `rerun_of:` linking to the primary record ID. The primary
  record body is immutable.
- **No primary (backfill path)** — place CHAIN-NOTE directly in the `# Result`
  section of the record being authored this run.

CHAIN-NOTE format: `cycles=<N>; stops=<N>; gates=[<list>]; friction=<phrase or none>; note="<free text>"`

See `references/land-workflow.md` § CHAIN-NOTE format for full field
definitions.

### Step 8 — Run journal

Append a structured YAML entry to the scratchpad run journal (not committed).
See `references/land-workflow.md` § Run journal skeleton for the minimum shape.

Report to the user:
- PR URL and merge commit
- Execution record path and prompt ID
- CHAIN-NOTE summary (cycles, stops, gates, friction)
- Any friction or stops encountered during the run

---

## Quality Checklist

Before reporting completion, verify:

- [ ] PR verified open before any automated steps
- [ ] Primary record classification (found/backfill) determined in Step 1
- [ ] Chain authorization gate (Step 2) completed before Steps 4–5; both
      completion condition and stop-work condition stated and confirmed
- [ ] REVIEW-LANDED check performed; empty comment list not treated as clean
- [ ] Review-response completed with no open comments before confirm-fixes
- [ ] Confirm-fixes verdict is green before merge gate
- [ ] Merge executed by the human, not the agent
- [ ] CHAIN-NOTE placed correctly (new `_CLOSEOUT_NOTE` if primary found;
      in the authored record if backfill path)
- [ ] Run journal entry appended to scratchpad
- [ ] `lrh validate` reports 0 errors after closeout

---

## What This Skill Does Not Do

- Does not land multiple PRs in one invocation — one PR per run.
- Does not execute the merge autonomously — Step 6 is a human gate.
- Does not implement `/lrh-execute` — that is Phase 2 (`WI-SKILLS-LRH-EXECUTE`).
- Does not bypass any internal confirmation gate inside the inlined sub-skills
  — chain initiation authorizes running the links, not skipping their internal
  gates.
- Does not enforce `depends_on` — that is `/lrh-execute`'s responsibility.
- Does not implement a persistent run journal — the scratchpad journal is a
  prototype (per `PROP-LRH-LAND-EXECUTE` Decision 8).
