---
id: PROP-LRH-EXECUTION-SESSIONS
type: design_proposal
title: LRH Execution Sessions — Three-Phase Model and Claude.app Session Traceability
status: proposed
created_on: 2026-06-23
updated_on: 2026-06-28
implementation_status: partial
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - PROMPTS.md
  - project/executions/README.md
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
  - project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
---

# LRH Execution Sessions — Three-Phase Model and Claude.app Session
Traceability

## Summary

This proposal formalizes the **execution session model** for LRH. It
extends the existing prompt workflow to cover Claude.app sessions —
multi-turn conversations that do not fit the single-document Codex
Cloud submission model — while preserving the lightweight execution
record system. The proposal defines three components:

1. A **three-phase execution session model** (design → instruction →
   execution) that applies across Codex Cloud, Claude.app, and manual
   execution.
2. Optional new **execution record fields** that reference the
   instruction-phase artifact and the Claude.app session transcript as
   supporting observability artifacts.
3. **Taurcode meta-prompt placement** in LRH's distribution model and
   a path toward a future `lrh-execution-session` Claude Code skill.

This proposal is documentation-only. No CLI command, schema validator
change, or runtime behavior change is delivered in the proposal PR.

## Background and motivation

### The existing Codex Cloud workflow

LRH's current prompt workflow targets Codex Cloud. The user designs
a change, generates a structured prompt document with a unique prompt
ID, and submits the file to Codex Cloud. Codex Cloud implements the
work as a pull request. The resulting execution record links the
prompt ID to the PR and commit. The prompt file is the durable
instruction artifact and the natural audit trail.

```text
Design (conversation or docs)
  → prompt file with prompt ID
  → Codex Cloud
  → PR
  → execution record: prompt ID → PR → commit
```

This model maps cleanly to `PROMPTS.md`'s prompt ID format and to the
execution-record front-matter schema in `project/executions/README.md`.

### The Claude.app gap

Claude.app (Claude Code CLI/desktop) does not fit the single-document
submission model. A Claude.app session is a multi-turn conversation,
not a submitted file. The session may span design, clarification,
implementation, validation, and PR creation — but LRH has no way to
reference that session in an execution record.

Claude Code saves session transcripts as JSONL at:

```text
~/.claude/projects/<project-path-slug>/<session-id>.jsonl
```

where `<project-path-slug>` is the working directory path with `/`
replaced by `-` (e.g., for a project at
`/Users/centaur/Workspace/LogicalRoboticsHarness/logical_robotics_harness`
the slug is
`-Users-centaur-Workspace-LogicalRoboticsHarness-logical_robotics_harness`)
and `<session-id>` is a UUID-format filename stem. These JSONL files
are durable local artifacts that persist after the session ends.

The existing execution-record schema:

```yaml
execution_id: YYYY_MM_DD_HH_MM_SS_SLUG
prompt_id: PROMPT(...)[timestamp]
work_item: AD_HOC | WI-...
status: planned | in_progress | landed | ...
rerun_of: (optional)
pr: (optional URL)
commit: (optional SHA)
created_at: ISO8601
```

This schema has no field for the Claude.app session transcript, no
field for the instruction-phase artifact (meta-prompt or prompt file),
and no field to identify which execution backend was used.

### Evidence from the preceding session

A 2026-06 Claude.app session demonstrated the "E-via-C" dogfooding
approach — using the current best mechanism (a streamlined Claude.app
workflow, Option C) to produce the design that informs the general
model (the E-strategy execution sessions proposal, Option D). In that
session:

- A design was produced in conversation (design phase).
- The design was restated explicitly and a Taurcode meta-prompt was
  generated for future sessions (instruction phase).
- The work was implemented and landed as PR #313 (execution phase).
- Execution record created:
  `PROMPT(AD_HOC:REVIEW_RESPONSE_PROTOCOL_FIX)[2026-06-21T14:46:03-04:00]`

The execution record captures the prompt ID, PR, commit, and status
correctly. What it lacks: a machine-readable reference to the
Claude.app session where the design originated, and a reference to
the Taurcode meta-prompt that was generated as the instruction-phase
artifact.

## Problem statement

Without this proposal:

- Claude.app-driven execution records cannot reference the session
  transcript where the design and instruction phases happened.
- `lrh search` cannot distinguish Codex Cloud–driven from
  Claude.app–driven execution records.
- There is no canonical vocabulary for the three-phase model, so
  each session invents its own discipline or skips the instruction
  phase entirely.
- Taurcode meta-prompts generated in Claude.app sessions have no
  defined home in LRH's distribution model.
- The execution record for a Claude.app-driven PR looks identical
  to a Codex Cloud–driven PR, with no traceability back to the
  source session.

## Design

### 1. Three-phase execution session model

An execution session has three phases. Each phase produces artifacts
that LRH can reference in execution records or design documents.

```text
Phase 1: Design
  → the source of the design: a conversation, prior docs, review notes

Phase 2: Instruction
  → explicit task statement submitted to the execution backend:
    • Codex Cloud: a structured prompt file with prompt ID
    • Claude.app: a restated design + Taurcode meta-prompt
    • Manual: a work item or design proposal with acceptance criteria

Phase 3: Execution
  → implementation → validation → PR → execution record
```

#### Design phase

The design phase produces the reasoning behind the change. It may
span multiple conversations or documents. LRH does not require the
design phase to produce a formal artifact for every run; design
phase material may live in prior execution records, referenced
proposals, or linked GitHub issues.

When a Claude.app session produces a design, the session transcript
is a design-phase artifact. It is observability — what happened —
not a control-plane claim. It need not be committed to the
repository.

#### Instruction phase

The instruction phase makes the design actionable for a specific
execution backend:

- **Codex Cloud:** the user generates a structured prompt file with
  `lrh prompt label` and submits it to Codex Cloud. The prompt file
  is the instruction artifact.
- **Claude.app:** the user runs `lrh prompt label --slug <slug>` to
  mint a canonical prompt ID, then `lrh prompt check-execution
  --prompt-id "<id>"` for soft idempotence. They then restate the
  design explicitly in the session (the "instruction phase" marker)
  and optionally generate a Taurcode meta-prompt for future reuse.
  Minting the prompt ID before implementation begins ensures the
  resulting execution record has a `prompt_id` that `lrh search` and
  `lrh prompt check-execution` can find. The restatement is within
  the same session; the meta-prompt is a distributable artifact.
- **Manual:** the work item's acceptance criteria and validation
  commands serve as the instruction phase artifact.

The instruction phase produces the prompt ID that enters the
execution record `prompt_id` field.

#### Execution phase

The execution phase runs the change: branch creation, code or
documentation editing, validation, PR creation. The execution
record captures the outcome. This phase is already well-modeled by
LRH's current `project/executions/` schema.

### 2. Claude.app session transcript as a durable artifact

#### Session identification

A Claude.app session transcript is identified by:

- its **project-path slug**: the working directory path with `/`
  replaced by `-`
- its **session ID**: the UUID-format stem of the `.jsonl` filename

Together these form a unique session reference:

```text
~/.claude/projects/<project-path-slug>/<session-id>.jsonl
```

For display, a short form is sufficient:

```text
claude-app:<session-id>
```

#### New optional execution-record fields

This proposal adds three optional fields to the execution-record
front-matter schema. These fields are backward-compatible; existing
records remain valid without them.

```yaml
# New optional fields:
agent: claude_app | codex_cloud | manual | <other>
instruction_source: <path-or-description>
session_transcript: <path-to-jsonl>
```

`agent` identifies which execution backend performed the work. This
lets `lrh search` filter by backend without depending on other fields.

`instruction_source` references the instruction-phase artifact:
- For Codex Cloud: the path to the prompt file (e.g.,
  `/tmp/codex_prompt.md` or a Taurcode path)
- For Claude.app: a description or path to the Taurcode meta-prompt
  (e.g., `taurcode:lrh-review-response-protocol-fix`)
- For manual runs: the work item ID or design proposal reference

`session_transcript` references the Claude.app session by its session
ID using the short form:

```
claude-app:<session-id>
```

The short form is the only value that should appear in committed
execution records. Absolute paths such as
`~/.claude/projects/<project-slug>/<session-id>.jsonl` leak the
author's username and local workspace layout to anyone who clones the
repository. Absolute paths are appropriate only as local discovery
output (e.g., from a future `lrh sessions discover` command) and
should not be written into committed frontmatter.

If the session ID is not yet known when the record is created, use
the sentinel value `pending` and update the field before or when the
PR lands.

Stage 2 validator behavior: `lrh validate` should warn on any
`session_transcript` value that begins with `/`, `~`, or a Windows
drive letter, and suggest converting to the `claude-app:<session-id>`
short form.

These fields are observability references, not control-plane claims.
The session transcript is private by default and is not committed to
the repository. Referencing the session ID in the execution record
preserves traceability without leaking conversation content or local
path information.

#### Example: Claude.app-driven execution record

The execution record for PR #313 (the preceding session), with the
proposed new fields filled in:

```yaml
---
execution_id: 2026_06_22_12_30_37_REVIEW_RESPONSE_PROTOCOL_FIX
prompt_id: PROMPT(AD_HOC:REVIEW_RESPONSE_PROTOCOL_FIX)[2026-06-21T14:46:03-04:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/313
commit: 2300612
created_at: 2026-06-22T12:30:37-04:00
agent: claude_app
instruction_source: taurcode:lrh-review-response-protocol-fix
session_transcript: claude-app:<session-id>
---
```

The three new fields make visible what was invisible before: that a
Claude.app session drove this execution, that a Taurcode meta-prompt
was generated as the instruction-phase artifact, and where the
session transcript can be found.

#### `lrh search` discoverability

`lrh search executions` already performs full-text substring search
across execution-record frontmatter and body text. Adding `agent:
claude_app` to frontmatter makes Claude.app-driven records
immediately discoverable:

```bash
lrh search executions "claude_app" --project-root .
lrh search executions "session_transcript" --project-root .
```

No new CLI command is required for Stage 1. A future `lrh sessions
discover` command (Stage 3) could scan
`~/.claude/projects/<project-slug>/` to list all sessions associated
with the current project — but that is deferred.

### 3. LRH control plane integration

Execution sessions fit into LRH's existing hierarchy without adding
a new artifact type:

```text
Project → Workstream → Work Item
                       ↓
               Execution Session
               (three-phase process)
                       ↓
               Execution Record   ← primary control-plane artifact
               Branch / PR / Commit
               Session Transcript  ← observability artifact (local)
               Instruction Source  ← instruction artifact (local or stored)
```

The execution record remains the authoritative control-plane artifact.
The session transcript and instruction source are observability
artifacts in the sense defined by `workstream-execution-framework`:
they capture what happened during the run but do not replace
evidence or claims in the execution record.

This hierarchy is consistent with the
`workstreams-and-recursive-planning-tree` adopted proposal:

```text
Workstream = planning / aggregation / intent
Work item = executable task
Execution session = the process of executing a task (three phases)
Execution record = what happened during a session
Evidence = concrete validation output
```

The execution session concept clarifies where the prompt file (Codex
Cloud) and the restated design + meta-prompt (Claude.app) fit: they
are instruction-phase artifacts that sit between the work item and
the execution record. They do not require a new directory or artifact
type in Stage 1.

Future integration with `workstream-execution-framework` run packets:
when run packets are adopted, the instruction phase maps naturally
onto a run packet — the packet becomes the instruction-phase artifact
for both manual and backend-driven runs. This proposal does not
require run packets; it provides the vocabulary that makes run-packet
adoption smoother.

### 4. Taurcode meta-prompt as a distributable artifact

The "implement this design" meta-prompt generated in the preceding
Claude.app session is currently stored in Taurcode — a user-local
prompt library. This is a valid resting place for user-specific,
project-specific prompts. However, it creates a distribution problem:
the meta-prompt is not shareable with other users or installable by
other LRH instances without manual copying.

#### Distribution tiers

| Tier | Location | Audience | Mechanism |
|------|----------|----------|-----------|
| User-local | Taurcode | One user | Taurcode personal library |
| Project-local | `.claude/skills/<name>/` | Project contributors | Claude Code auto-discovery |
| Package-distributed | `src/lrh/skills/<name>/` | All LRH users | `lrh setup` (per PROP-LRH-PROJECT-LOCAL-SKILLS) |

A meta-prompt specific to one project (e.g., a review-response fix
for a particular repo) belongs at the user-local tier. A meta-prompt
encoding a generalizable LRH workflow (e.g., "run the three-phase
execution session model for any task") belongs at the package tier.

#### Future `lrh-execution-session` skill

When `PROP-LRH-PROJECT-LOCAL-SKILLS` is adopted and Stage 1 ships,
the three-phase execution session model should be encoded as a
Claude Code skill:

```text
src/lrh/skills/lrh-execution-session/
  SKILL.md
  references/
    execution-session-workflow.md   # three-phase model reference
    session-transcript-guide.md     # how to find and reference JSONL files
    taurcode-meta-prompt-guide.md   # instruction-phase artifact guidance
```

The skill would guide Claude through:

1. Performing the `lrh prompt label` + `check-execution` idempotence
   check.
2. Confirming the design phase is complete or explicitly captured.
3. Restating the design (instruction phase marker).
4. Optionally generating a Taurcode meta-prompt for future reuse.
5. Implementing the work (execution phase).
6. Running validation.
7. Creating the PR and the execution record with the new optional
   fields filled in.

This skill is deferred until `PROP-LRH-PROJECT-LOCAL-SKILLS` ships.
In the interim, the three-phase model in `PROMPTS.md` and this
proposal serves as the reference for Claude.app sessions.

#### Independence from `lrh-project-local-skills`

The schema additions (new optional fields in execution records) in
Stage 1 do not depend on `PROP-LRH-PROJECT-LOCAL-SKILLS`. Users can
populate the new fields manually in execution records even before the
`lrh-execution-session` skill exists.

## Staged implementation plan

This proposal is documentation-only. Implementation proceeds in
stages, each backed by a separate work item.

### Stage 0 — This proposal (done)

- `project/design/proposals/proposed/lrh-execution-sessions/` with
  this umbrella document and README.
- Index entry in `project/design/proposals/README.md`.

Deliverable: a written design with a specific vocabulary for future
implementation work.

### Stage 1 — Documentation additions (`WI-EXEC-SESSIONS-DOCS`) — not_started

- Update `project/executions/README.md` to document the new optional
  fields: `agent`, `instruction_source`, `session_transcript`.
- Update `PROMPTS.md` to describe the three-phase model for
  Claude.app sessions and the optional new fields.
- No validator changes; existing validators should pass through
  unknown frontmatter fields without error. If they do not, a
  targeted fix belongs here.

Stage 1 is documentation-only and can land quickly. As of 2026-06-28,
163 execution records already use the new fields organically (populated
by `/lrh-implement`), but neither README.md nor PROMPTS.md documents
them. The fields are documented in `.claude/skills/lrh-implement/
references/execution-session-reference.md`, but that is skill-internal,
not the canonical location.

### Stage 2 — Schema validation (`WI-EXEC-SESSIONS-SCHEMA`) — not_started

- Update `lrh validate` to recognize and validate the optional new
  fields: `agent` value set, `session_transcript` path or short-form,
  `instruction_source` format.
- Add tests for valid and invalid values.
- Add `lrh snapshot project` reporting: counts by `agent` value if
  the field is present; flag records with `session_transcript` that
  reference missing local files (advisory, not error).

As of 2026-06-28, `lrh validate` has no execution-record validation
logic; the new fields pass through silently without enum checking or
path-format warnings.

### Stage 3 — Session discovery (`WI-EXEC-SESSIONS-DISCOVERY`) — not_started

- `lrh sessions discover [--project-root .]` — scan
  `~/.claude/projects/<project-slug>/` for JSONL files and list
  sessions with timestamps, approximate sizes, and any linked
  execution records.
- `lrh sessions link --session <id> --execution <execution-id>` —
  add `session_transcript` to an existing execution record.

This stage requires local filesystem access to `~/.claude/projects/`
and is a new CLI command surface.

### Stage 4 — Skill — done (subsumed by /lrh-implement)

The proposed `lrh-execution-session` skill's 7 steps are fully
covered by `/lrh-implement`, which shipped in WS-SKILLS (resolved).
`/lrh-implement` covers all seven steps and adds readiness checking,
a human plan-confirm gate, and branch creation. It populates `agent`,
`instruction_source`, and `session_transcript` in every execution
record it creates.

A separate `lrh-execution-session` skill is not warranted.
`PROP-LRH-PROJECT-LOCAL-SKILLS` is already adopted; the project-local
skill mechanism is in place.

## Non-goals

- Do not require a `session_transcript` field for every execution
  record. The field is always optional and backward-compatible.
- Do not commit Claude.app session JSONL files to the repository.
  They are local-only, private-by-default, and may contain sensitive
  conversation content.
- Do not build a conversation storage or replay system. That belongs
  in `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP`.
- Do not change the prompt ID format. The existing
  `PROMPT(<WORK_ITEM>:<SLUG>)[<TIMESTAMP>]` format remains the
  canonical prompt identifier.
- Do not add a new first-class artifact directory (e.g.,
  `project/sessions/`). The execution record with optional new fields
  is sufficient in Stage 1.
- Do not automate the three-phase workflow. Claude.app sessions are
  human-driven; the skill (Stage 4) guides but does not automate.
- Do not import or ingest session JSONL content into the repository.
  The transcript path is a reference, not a copy.

## Risks and mitigations

### Risk 1 — Session JSONL path instability

The `~/.claude/projects/<project-slug>/` layout is not a documented
Claude Code API. It may change across Claude Code versions or
differ on Windows.

Mitigation: the `session_transcript` field is optional and advisory.
The short form `claude-app:<session-id>` is more stable than an
absolute path. Stage 3 discovery tooling should handle path variation
gracefully.

### Risk 2 — Privacy leakage via transcript references

An execution record with `session_transcript: ~/.claude/projects/...`
is committed to the repository. If another contributor clones the
repo and sees this field, they will not be able to access the file —
it is local to the original author's machine — but they may not
realize that the reference is intentionally local.

Mitigation: `project/executions/README.md` should document that
`session_transcript` references are local and private by default. The
short form `claude-app:<session-id>` makes the locality explicit.
`lrh validate` (Stage 2) can emit an advisory if an absolute path
starting with `~` or the filesystem root is found.

### Risk 3 — Multiple backends per execution

A single execution may use both Claude.app (design phase) and Codex
Cloud (execution phase). The `agent` field would accurately reflect
only the execution-phase backend.

Mitigation: the `instruction_source` field captures the design-phase
tool when relevant. If multi-backend runs become common, a future
`design_session_transcript` field or an array `agents:` field can be
added. Stage 1 uses a single `agent` value for simplicity.

### Risk 4 — Field proliferation

Adding optional fields to execution records risks accumulating unused
or inconsistently populated fields over time.

Mitigation: Stage 1 adds only three fields, all optional. Stage 2
adds validation that encourages consistent use. If fields prove
unused after a reasonable trial period, they can be deprecated through
the normal proposal process.

## Acceptance criteria

This proposal can be considered effectively implemented when:

- `project/executions/README.md` documents the `agent`,
  `instruction_source`, and `session_transcript` optional fields;
- `lrh validate` accepts execution records with those fields without
  error and validates their values where possible;
- at least one real Claude.app-driven execution record includes all
  three fields and `lrh search executions "claude_app"` finds it; and
- dogfooding confirms that the three-phase model in `PROMPTS.md` is
  sufficient to guide a new Claude.app execution session without
  additional tooling.

## Work items

Status as of 2026-06-28:

- `WI-EXEC-SESSIONS-DOCS` — update `project/executions/README.md`
  and `PROMPTS.md` to document the three-phase model and optional
  new fields — **not started**
- `WI-EXEC-SESSIONS-SCHEMA` — update `lrh validate` for the new
  optional fields; add tests — **not started**
- `WI-EXEC-SESSIONS-DISCOVERY` — implement `lrh sessions discover`
  and `lrh sessions link` commands — **deferred**
- `WI-EXEC-SESSIONS-SKILL` — **superseded** by `/lrh-implement`
  (WS-SKILLS); no separate skill needed

## References

- `PROMPTS.md` — prompt workflow, prompt ID format, execution-record
  lifecycle.
- `project/executions/README.md` — canonical execution-record schema.
- `project/executions/AD_HOC/2026_06_22_12_30_37_REVIEW_RESPONSE_PROTOCOL_FIX.md`
  — the motivating execution record; shows the gap (no `agent`,
  `instruction_source`, or `session_transcript` fields).
- `PROP-LRH-PROJECT-LOCAL-SKILLS` — proposed skill distribution
  infrastructure that Stage 4 of this proposal builds on.
- `PROP-WORKSTREAM-EXECUTION-FRAMEWORK` — deferred runtime
  architecture; the observability-vs-evidence distinction used in
  this proposal derives from that framework.
- `PROP-WORKSTREAMS-RECURSIVE-PLANNING-TREE` (adopted) — defines the
  Project → Workstream → Work Item hierarchy that execution sessions
  sit beneath.
- `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP` — complementary proposal
  on raw conversation capture; that proposal addresses general
  conversation storage semantics whereas this proposal addresses the
  narrower execution-record linkage for Claude.app-driven sessions.
- Claude Code documentation — Claude Code stores session transcripts
  as JSONL at `~/.claude/projects/<project-path-slug>/`. Confirmed
  in practice during 2026-06 sessions.
