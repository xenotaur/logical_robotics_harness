---
id: PROP-LRH-CLOSEOUT
type: design_proposal
title: LRH Session Closeout — /lrh-closeout Skill and lrh prompt update-execution CLI
status: adopted
created_on: 2026-06-27
updated_on: 2026-06-28
implementation_status: implemented
implemented_by:
  - WI-SKILLS-LRH-CLOSEOUT
  - WI-SKILLS-CLOSEOUT-GATE-FIX
  - WI-SKILLS-CLOSEOUT-UX-FIX
  - WI-PROMPT-CLI-CLOSEOUT
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
  - project/workstreams/resolved/WS-SKILLS.md
  - project/workstreams/resolved/WS-SKILLS-DOC.md
  - src/lrh/skills/lrh-implement/references/lrh-implement-workflow.md
  - src/lrh/skills/lrh-implement/references/execution-session-reference.md
---

# LRH Session Closeout — `/lrh-closeout` Skill and `lrh prompt update-execution` CLI

## Summary

This proposal introduces a `/lrh-closeout` Claude Code skill that automates
the post-execution closeout workflow for LRH sessions: updating execution
records to `landed`, resolving work items, closing workstreams, and adopting
governing proposals. It also specifies a `lrh prompt update-execution` CLI
command as a forward requirement to replace the skill's initial edit-in-place
mechanism once the CLI is implemented.

## Background / Motivation

The three-phase execution session model (documented in
`project/design/proposals/proposed/lrh-execution-sessions/`) ends at
execution — no closeout phase is defined, and no tooling exists for
post-execution closeout. In practice, closeout has been performed manually
in every LRH session:

- editing execution record frontmatter (`status: in_progress → landed`,
  `pr:`, `commit:`, `session_transcript:`)
- moving work items from `proposed/` to `resolved/` with a `resolution:` note
- closing workstreams (`stage: closed`, `status: resolved`)
- moving proposals from `proposed/` to `adopted/`

This is error-prone and inconsistent. In the `WS-SKILLS-DOC` workstream
(resolved 2026-06-27), the workstream and proposal closeout steps were
forgotten until the user explicitly prompted for them, despite occurring
within the same session that completed all three work items.

The gap is structural: no single command or skill has responsibility for the
full closeout sequence. The execution record is updated manually; the work
item move is a separate manual operation; workstream and proposal closeout
are ad hoc. A skill that assesses current state and executes all confirmed
closeout actions closes this gap.

Two prior proposals establish the context:

- `PROP-LRH-PROJECT-LOCAL-SKILLS` introduced the skill pattern
  (`src/lrh/skills/<name>/`, `lrh setup`) and the confirm-gate convention.
- `PROP-LRH-EXECUTION-SESSIONS` (proposed) defines the three-phase model,
  execution record fields, and the `session_transcript` convention.

`/lrh-closeout` is the missing post-execution complement to `/lrh-implement`
and `/lrh-review-response`.

## Design Decisions

### Decision 1: Skill-first sequencing

**Question:** Should the skill be built before or after a dedicated
`lrh prompt update-execution` CLI command?

**Options considered:**
- A: Skill first (edit-in-place), CLI spec concurrent, CLI implementation
  deferred
- B: CLI first, then clean skill implementation
- C: Parallel (skill and CLI simultaneously)

**Chosen: A — skill first.** The edit-in-place approach has been used in
every LRH closeout to date and is proven to work. Building the skill first
reveals the exact field set and validation requirements the CLI must handle
(applying "parse, don't validate" — King 2019: design from observed usage,
not speculation). The CLI interface specified in Decision 3 is a forward
requirement: specified here based on the design session analysis, but
implementation is explicitly deferred to WI-2. The skill's internal mechanism
(Edit calls → CLI call) can be swapped without changing the skill's external
interface, following the strangler-fig pattern (Fowler, *Patterns of
Enterprise Application Architecture*, 2002).

### Decision 2: Assessment-first execution (decision matrix)

**Question:** Should the skill follow a fixed sequence, or assess all
artifact states before acting?

**Options considered:**
- Fixed sequence: update record, resolve WI, offer WS closeout — always in
  that order
- Assessment-first: read all state, build a closeout plan, confirm, then
  execute

**Chosen: assessment-first.** A fixed sequence fails silently on
already-closed artifacts (no idempotence) and provides no early warning when
the PR is still open or state is ambiguous. The decision matrix (Step 2 of
the skill) assesses each artifact independently before any file is touched,
producing an explicit plan shown at the confirm gate. This applies
command-query separation (Meyer, *Object-Oriented Software Construction*,
1988): Step 2 is purely read-only; Step 5 is purely write.

The decision matrix:

| Artifact | Condition | Action |
|---|---|---|
| PR | `state: MERGED` | proceed |
| PR | `state: OPEN` or `CLOSED` without merge | **abort** |
| Execution record | `status: in_progress` | update to `landed` |
| Execution record | `status: landed` | skip (already done) |
| Execution record | missing | warn and ask |
| WI | in `proposed/` | resolve (move + set `resolution:`) |
| WI | in `resolved/` | skip |
| WI | not found | warn and ask |
| WS | all WIs resolved AND WS in `proposed/` | offer closeout |
| WS | any WI still in `proposed/` | skip — not ready |
| Proposal | WS closed AND proposal in `proposed/` | offer adoption |
| Proposal | already in `adopted/` | skip |

This mirrors the triage step in `/lrh-review-response` (presence check →
validity check → feasibility check per comment), applied to closeout
artifacts instead of review comments.

### Decision 3: CLI command name and interface

**Question:** What is the right CLI interface for atomically updating an
execution record to `landed`?

**Options considered:**
- A: `lrh prompt update-execution` (new subcommand in `lrh prompt` group)
- B: `lrh closeout` (new top-level command)
- C: Overload `lrh prompt record-execution --status landed`

**Chosen: A — `lrh prompt update-execution`.** Consistent with the
`lrh prompt` subgroup naming (`record-execution`, `label`,
`check-execution`). `update` is semantically distinct from `record`
(mutation vs. creation), avoiding dual-mode command semantics (Fowler,
*Refactoring*, 1999: avoid dual-purpose methods). Option B (`lrh closeout`)
implies broader scope than execution record mutation — if it does only the
record update, the name misleads; if it does the full closeout (WI, WS,
proposal), it duplicates the skill. Option C overloads `record-execution`
with two lifecycle events, making it harder to reason about.

**Specified interface (forward requirement for WI-2):**

```bash
lrh prompt update-execution \
  --execution-id <ID> \
  --status landed \
  --pr <URL> \
  --commit <SHA> \
  --session-transcript <ID-or-pending>
```

**Required validation:**
- Execution record must exist at the path implied by `--execution-id`
- Status transition must be valid; `in_progress → landed` is the only
  documented forward transition; backwards transitions are rejected
- If `--status landed`, `--commit` is required (a landed record without
  a commit SHA is incoherent)

**Minimum updatable field set (4 fields):**
- `--status` — lifecycle transition
- `--pr` — PR URL
- `--commit` — merge commit SHA
- `--session-transcript` — session ID or the literal string `pending`

The record body (Summary, Result, Validation, Follow-up sections) is
human-authored prose and is not updated by the CLI.

### Decision 4: Session transcript resolution (3-way confirm)

**Question:** How should the skill handle `session_transcript` when the
session ID is not known?

**Context:** `execution-session-reference.md` documents one session ID
format: the UUID stem of the JSONL file at
`~/.claude/projects/<slug>/*.jsonl`, stored as `claude-app:<uuid>`.
JSONL auto-detection is reliable in CLI-backed sessions but may not
locate the correct file in web-backed sessions.

**Chosen: 3-way resolution at Step 3, surfaced at the confirm gate:**

1. **Found via JSONL:** "Detected session ID `<uuid>`. Is this correct?"
2. **Not found / wrong format:** "Could not auto-detect. Provide it, or
   confirm `pending` is acceptable."
3. **User confirms `pending`:** set `session_transcript: pending`; include
   a reminder in the Step 8 report to update before archiving.

`session_transcript: pending` is explicitly first-class per
`execution-session-reference.md` ("Use `pending` when the session ID is
not yet known"). This field must never block the closeout workflow.

### Decision 5: Skill step structure

**Chosen: 8 steps.**

```
Step 1 — Parse input
         Accept: PR URL, WI ID, WS ID, or auto-detect from in_progress records
         Auto-detect: grep -rl '^status: in_progress' project/executions/ --include='*.md'
         Read pr: field from candidates; if ambiguous, list and ask

Step 2 — Assess state → build closeout plan
         Apply decision matrix to all discovered artifacts
         Produce plan as list of (artifact, current-state, intended-action)

Step 3 — Resolve session transcript
         Attempt JSONL auto-detection; 3-way confirm (Decision 4)

Step 4 — Confirm gate (human gate)
         Show full closeout plan + resolved session transcript value
         Wait for explicit confirmation before touching any files

Step 5 — Execute confirmed actions
         Phase 1 (WI-1): edit-in-place on execution record YAML
         Phase 2 (WI-2): lrh prompt update-execution call

Step 6 — Validate
         lrh validate; abort and report if errors

Step 7 — Session reflection
         Ask: "Is there anything from this session worth persisting to memory?"
         If yes: prompt for memory content and write; if no: proceed

Step 8 — Report
         Summarize actions taken; remind about /export to archive session;
         remind to update session_transcript if still pending
```

### Decision 6: Reference file structure

**Chosen: one reference file — `references/closeout-workflow.md`.**

Contains: the decision matrix (Decision 2), execution record update
protocol (field values, valid transitions, `pending` convention), WI
resolution protocol (frontmatter fields, `mv` to `resolved/`), WS
closeout protocol (`stage: closed`, `status: resolved`), proposal
adoption protocol (`status: adopted`, `implementation_status: implemented`,
`implemented_by: [WI IDs]`), and session transcript auto-detection
(JSONL path pattern, `claude-app:<uuid>` format, `pending` sentinel).

No `diataxis-criteria.md` is needed — this skill performs no documentation
classification. Per-skill reference files follow the convention established
by `PROP-LRH-PROJECT-LOCAL-SKILLS` and `PROP-LRH-DOC-SKILLS`.

## Non-Goals

- Does not implement `lrh prompt update-execution` in WI-1 — the CLI is a
  forward requirement specified here and implemented in WI-2.
- Does not automate the `resolution:` prose in work items — the one-line
  summary is human-authored and provided at the confirm gate or inferred
  from the PR title.
- Does not close GitHub PRs via `gh pr close` — the skill only records an
  already-merged PR's state; PR closing is a human action.
- Does not replace human judgment about whether WS exit criteria are met
  — the skill checks structural completeness (all WIs resolved), not
  semantic completeness.
- Does not write memories automatically — Step 7 prompts the user; writing
  is always opt-in.
- Does not implement `lrh design organize --apply` for proposal bucket moves
  — the skill uses `mv` directly because it knows exactly which files to move.
- Does not cover the design or instruction phases of the three-phase
  execution session model — those remain the `/lrh-design`, `/lrh-proposal`,
  and `/lrh-implement` skills.
- Does not handle abandoned work items (WI with no PR ever opened) — that
  edge case is flagged with a warning and left for human resolution.

## Implementation Plan

Implementation is governed by workstream `WS-SKILLS-CLOSEOUT` and two work
items:

| Work item | Deliverable | Depends on |
|---|---|---|
| `WI-SKILLS-LRH-CLOSEOUT` | `/lrh-closeout` skill (edit-in-place, Phase 1) | This proposal adopted |
| `WI-PROMPT-CLI-CLOSEOUT` | `lrh prompt update-execution` CLI + skill upgrade (Phase 2) | `WI-SKILLS-LRH-CLOSEOUT` landed |

**WI-SKILLS-LRH-CLOSEOUT** produces:
- `src/lrh/skills/lrh-closeout/SKILL.md` (8-step flow per Decision 5)
- `src/lrh/skills/lrh-closeout/references/closeout-workflow.md` (per
  Decision 6)
- `.claude/skills/lrh-closeout/` mirror (byte-for-byte, `diff -r`
  verified)
- `CLAUDE.md ## Skills` entry: `/lrh-closeout`

**WI-PROMPT-CLI-CLOSEOUT** produces:
- `lrh prompt update-execution` CLI implementation (per Decision 3 spec)
- Updated `src/lrh/skills/lrh-closeout/SKILL.md` Step 5: Edit calls
  replaced by `lrh prompt update-execution` call
- Updated `src/lrh/skills/lrh-implement/references/execution-session-reference.md`
  with the new command syntax

The skill upgrade in WI-2 is a local Step 5 change only — the skill's
external interface, step structure, and reference files are stable across
both phases.

## Cross-References

- Three-phase execution session model (design → instruction → execution;
  closeout workflow extends it):
  `project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md`
- Skill distribution pattern:
  `project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`
- Execution record fields and session transcript format reference:
  `src/lrh/skills/lrh-implement/references/lrh-implement-workflow.md`
  `src/lrh/skills/lrh-implement/references/execution-session-reference.md`
- Prior skills workstreams (structural precedents):
  `project/workstreams/resolved/WS-SKILLS.md`
  `project/workstreams/resolved/WS-SKILLS-DOC.md`
