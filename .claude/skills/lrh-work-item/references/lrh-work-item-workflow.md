# LRH Work Item — Lifecycle and Workflow Context

This document describes where `/lrh-work-item` fits in the LRH workflow,
how it relates to adjacent tools, and what the user should do after the
skill completes.

---

## Where this skill sits in the lifecycle

```
Identify need
    │
    ▼
/lrh-work-item WI-<ID>            ← this skill
    │  Creates project/work_items/proposed/<ID>.md
    │  Runs lrh validate
    │
    ▼
lrh work-items validate            ← verify hygiene
lrh work-items readiness           ← check prompt-readiness
    │
    ▼
lrh request ready-work-item <ID>   ← refine if thin
    │  (assistive; proposes a patch for human review)
    │
    ▼
lrh request prompt-from-work-item  ← render implementation prompt
    │
    ▼
Implementation (human or agent)
    │
    ▼
project/executions/<ID>/           ← execution record
    │
    ▼
lrh work-items validate + audit    ← closeout evidence
    │
    ▼
Move to resolved/                  ← human decision
```

---

## Relationship to `lrh request ready-work-item`

`ready-work-item` and `/lrh-work-item` are complementary, not competing.

| Tool | Purpose |
|---|---|
| `/lrh-work-item` | Create a new work item from scratch |
| `lrh request ready-work-item` | Refine an existing thin item toward prompt-readiness |

After using `/lrh-work-item`, the created item may still be thin — it has
structure but may lack the depth of `Required Changes` or `Acceptance
Criteria` needed to drive a bounded implementation prompt. In that case, run:

```bash
lrh request ready-work-item WI-<ID>
```

This renders an assistive refinement proposal for human review. It does not
edit files automatically.

---

## Relationship to `lrh request prompt-from-work-item`

`prompt-from-work-item` renders an implementation prompt from a work item
that has passed readiness checks. It requires:

- All required body sections (Summary, Problem/Context, Required Changes,
  Non-Goals, Acceptance Criteria, Validation).
- No blocking issues flagged by `lrh work-items readiness`.
- `status: proposed` or `status: active`.

If `lrh work-items readiness` flags the item as not prompt-ready, run
`lrh request ready-work-item` first to fill the gaps.

---

## Workstream integration

After creating a work item with this skill:

1. The skill offers (in Step 7) to add the new ID to the parent workstream's
   `work_items:` YAML list.
2. If you accept, the skill edits the workstream file and re-runs
   `lrh validate`.
3. If you decline, add it manually when you are ready.

The workstream file lives at `project/workstreams/<status>/<WS-ID>.md`.
After editing, run `lrh validate` to confirm the reference is valid.

---

## Suggested next steps after skill completes

There are two independent next-step paths, on different axes. They are not
alternatives — a work item usually needs both.

### Path 1 — PR lifecycle (the branch Step 8 just pushed)

Step 8 opens a PR containing the new work item file, so the PR needs review
like any other:

1. `/lrh-review-response <pr-url>` — address reviewer comments. Repeat as
   needed until no comments remain outstanding.
2. `/lrh-confirm-fixes <pr-url>` — verify the fixes against the current diff
   and resolve the review threads before merge.
3. Merge the PR.
4. `/lrh-closeout <pr-url>` — this skill files a *planning artifact* and
   creates no execution record itself, but `/lrh-review-response` and
   `/lrh-confirm-fixes` each create one when the PR gets review activity, so
   closeout lands those records after merge. Only a PR merged with no review
   activity has nothing to land and can skip this step.

Merging does not resolve the work item — it stays `proposed` until the work
it describes is implemented. Resolving the item is a *separate* closeout, run
later against the *implementation* PR — see "Evidence and closeout" below.

### Path 2 — item refinement (making the item prompt-ready)

Independent of the PR. Use when the item is not yet ready to drive execution:

```bash
# 1. Verify hygiene
lrh work-items validate

# 2. Check prompt-readiness
lrh work-items readiness --status proposed --format md

# 3. Refine if needed
lrh request ready-work-item WI-<ID>
# review the proposed patch; apply manually if approved

# 4. When ready to execute
lrh request prompt-from-work-item WI-<ID>
```

---

## Evidence and closeout

Once implementation is complete and its PR is merged, run
`/lrh-closeout <pr-url>`. It creates or lands the execution record under
`project/executions/<WI-ID>/`, moves the file to
`project/work_items/resolved/` with `status: resolved` and a non-null
`resolution`, and re-validates.

Do not hand-roll these steps. The status change and file move must happen
together — `lrh validate` fails if the file is in the wrong bucket — and
`/lrh-closeout` is the single place that sequencing is maintained.

---

## Orchestration: invoking this skill from other skills

`/lrh-work-item` can be invoked by orchestrating skills (`/lrh-design`,
`/lrh-proposal`, `/lrh-workstream`) when they need to create companion work
items as part of a design-capture workflow. This is enabled by removing
`disable-model-invocation: true`; the `when_to_use` field was added in its
place to provide guidance that reduces accidental auto-invocations.

### Why the confirm gate is sufficient write protection

The former `disable-model-invocation: true` flag conflated two concerns:

1. Preventing accidental keyword auto-triggering.
2. Blocking explicit model invocation via the Skill tool.

The first concern is desirable. The second prevents composition — orchestrating
skills cannot call `/lrh-work-item` as a sub-task without requiring the user to
manually type the slash command, defeating the purpose of skill composition.

The Step 4 confirm gate shows the complete proposed work item and requires
explicit user approval before any file is written. This satisfies OWASP LLM08
("Require human approval for high-impact actions") without blocking programmatic
invocation. The confirm gate fires in any invocation context — direct user call
or orchestrated call — so write protection is preserved regardless of how the
skill is triggered.

The `when_to_use` field narrows the auto-trigger surface — Claude is less likely
to invoke this skill when the user is simply asking about work items — while
still allowing explicit invocation from both users and orchestrating skills.
`when_to_use` is guidance, not a hard platform guarantee.

### Preloading into forked subagents

Removing `disable-model-invocation` also allows this skill to be preloaded into
forked subagents (`context: fork`). This is low-risk because the confirm gate
fires in any context, but skill authors building agents that fork should be aware
that the skill will be available in sub-contexts and that the gate remains the
last line of defense.

---

## LRH-specific constraints this skill enforces

- Work items are always created in `proposed/` — they are never created
  directly as `active` or `resolved`.
- `blocked: false` and `blocked_reason: null` are set for all new items.
- `resolution: null` is set for all new items.
- `status` always matches the directory bucket.
- `lrh validate` is run before reporting completion.
- The user confirms the full proposed content before any file is written.
