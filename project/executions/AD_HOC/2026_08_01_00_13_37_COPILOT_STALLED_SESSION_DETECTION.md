---
execution_id: 2026_08_01_00_13_37_COPILOT_STALLED_SESSION_DETECTION
prompt_id: PROMPT(AD_HOC:COPILOT_STALLED_SESSION_DETECTION)[2026-08-01T00:13:37+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-08-01T00:13:37+00:00
agent: claude_app
instruction_source: ad_hoc conversation — user reported a GitHub Copilot coding-agent session on an external PR (xenotaur/LCATS#202) stopping with "you've run out of your included AI credits for the month," asked whether this is API-detectable, then asked for options to signal the condition to a human or agent so a fallback (top up credits, or a self-review fallback under separate development) can be chosen
session_transcript: claude-app:local_23a15fdd-6d6c-4d84-a7be-960a54769157
---

# Summary

Investigate whether GitHub Copilot's "out of included AI credits" stop
condition (observed live on `xenotaur/LCATS#202`) is detectable via the
GitHub API, evaluate options for signaling that condition to a human or
agent, and implement the recommended near-term option:
`/lrh-confirm-fixes` Step 8.3's existing "no response after a reasonable
wait" check now distinguishes a reviewer that was never invoked from one
whose session started and stalled, before asking the human.

# Result

**Investigation** (against the live incident, `xenotaur/LCATS#202`):
grepped every PR comment, issue comment, and timeline event body for
"credit" — no match anywhere. The literal exhaustion message is not
exposed on any REST-accessible surface; it renders only in the GitHub web
UI's Copilot session panel. What *is* detectable: the issue Timeline API
(`copilot_work_started` with no later `copilot_work_finished`/
`_finished_failure`) and the `copilot-pull-request-reviewer` check-run on
the head commit, stuck `status: in_progress`, `conclusion: null`,
`completed_at: null`. Confirmed via `gh api .../check-runs` and
`gh api .../timeline` directly against the PR. Also confirmed against
GitHub's own webhook docs that `check_run` only fires
`created`/`rerequested`/`completed`/`requested_action` — no periodic
"still in progress" event — so this condition can only be polled, never
subscribed to.

**Options evaluated** (grounded in this repo's existing bot-retrigger
mechanism, `round-cap-gate.md`, and `WI-BOUNDED-STABILIZATION-LOOP-DESIGN.md`):

- **A — extend the existing Step 8.3 wait-for-reviewer check** with the
  stall heuristic above. Zero new infrastructure; reactive/session-scoped
  only.
- **B — scheduled poller** (GH Actions `schedule:` in the monitored repo,
  or `/loop`/`CronCreate`), for overnight/unattended coverage. New infra
  to build and maintain; deferred, not built here.
- **C — GitHub App/webhook receiver** — disqualified: `check_run`'s
  documented actions never include a "still stalled" event, so a webhook
  receiver still needs a polling backstop, buying no capability over B at
  meaningfully higher setup cost.
- **D — promote to a real, unit-tested LRH primitive** (e.g.
  `lrh pr-health check`), per `WI-BOUNDED-STABILIZATION-LOOP-DESIGN.md`'s
  own recommendation to move this class of logic out of skill-prose bash.
  Correct eventual home, but explicitly gated behind that WI's
  `depends_on` chain — not buildable today. Captured in
  `project/design/backlog.md` rather than implemented.

**Implemented (Option A):**

- `.claude/skills/lrh-confirm-fixes/SKILL.md` Step 8.3 (+ `src/lrh/...`
  mirror) — before asking the generic "no response yet" question, checks
  whether the reviewer's own session started and stalled, and asks a
  distinguishing question naming the specific case (not-configured vs.
  stalled, with credit exhaustion named as one known cause and the
  self-review-fallback option offered generically, without assuming it
  exists in this repo).
- `.claude/skills/lrh-confirm-fixes/references/round-cap-gate.md` (+
  mirror) — new "Detecting a stalled reviewer session" section
  documenting the exact `gh api` check-run and timeline queries, the
  15-minute threshold (reusing the skill's existing `STALE_AGE_SECONDS`
  constant), the `xenotaur/LCATS#202` grounding, and explicit caveats that
  this is a heuristic (identifies *that* a session stalled, not *why*) and
  does not measure aggregate Copilot spend — cross-linked from the
  pre-existing "no billing API" bullet in "What this bounds."
- `project/design/backlog.md` — new entry capturing Option D, deferred
  behind `WI-BOUNDED-STABILIZATION-LOOP-DESIGN`, with an explicit revisit
  trigger (an observed false positive/negative in practice).

**Prior-art check:** no duplication — `round-cap-gate.md`'s own "What this
bounds" section already named the "no automated source for billing
context" gap this closes; no other file implements a stall/credit
heuristic.

# Validation

```
lrh validate   — 0 errors, 1 pre-existing unrelated warning
                 (PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF on
                 WS-LRH-ASSISTANTS, unrelated to this change)
diff .claude/skills/lrh-confirm-fixes/SKILL.md src/lrh/skills/lrh-confirm-fixes/SKILL.md — identical
diff .claude/skills/lrh-confirm-fixes/references/round-cap-gate.md src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md — identical
```

Doc/skill-prose-only change; no source code touched, so `scripts/test`
does not apply.

# Follow-up

- Land via `/lrh-land` once the PR is open.
- `project/design/backlog.md`'s new entry: revisit Option D once
  `WI-BOUNDED-STABILIZATION-LOOP-DESIGN` is implemented, or sooner if the
  Step 8.3 heuristic produces an observed false positive/negative.
