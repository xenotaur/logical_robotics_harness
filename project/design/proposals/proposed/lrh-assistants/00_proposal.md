---
id: PROP-LRH-ASSISTANTS
type: design_proposal
title: LRH Assistants — Unified Architecture for Backend-Neutral Assistant Roles
status: proposed
created_on: 2026-07-24
updated_on: 2026-07-24
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/proposed/constitutional-sandbox-envelope/00_proposal.md
  - project/design/proposals/proposed/lrh-serve-operational-triage-mvp/00_proposal.md
  - project/design/proposals/proposed/meta-operational-triage-semantics/00_proposal.md
  - project/design/proposals/proposed/workstream-execution-framework/00_proposal.md
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
  - project/design/execution_framework_mvp.md
  - project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
---

# LRH Assistants — Unified Architecture

## Summary

This proposal introduces **`project/assistants/`** as a new first-class LRH
artifact class. An LRH **assistant** is a persistent, backend-neutral
organizational *role* — a reusable package of charter, scope, policy,
preferences, communication/context/review policy, portable skill, reviewed
memory, and evaluations — that an arbitrary capable agent (Claude, Codex,
Jules, or a human) can instantiate. An assistant accepts a bounded
workstream-management assignment via a `managed_by` binding, maintains
planning artifacts, supervises run trees, handles routine review under
policy, communicates with its human supervisor, and accumulates reviewed
institutional knowledge. The assistant models **how an assigned manager
operates** — an axis orthogonal to the existing planning tree (what the
project is doing), run tree (execution), and contributor records (who acted).

## Background / Motivation

LRH today models **what the project is doing** (workstreams → work items →
runs) and **who acted** (`Contributor`). It has no model of **how an assigned
manager operates**: a reusable mandate with a permission ceiling, review
policy, communication contract, context strategy, and reviewed memory.
Verified against the current control plane, `src/lrh/control/models.py`
defines `Contributor` (an actor: identity, role, status, execution mode) and
`Workstream` (a planning node: lifecycle, parents/children, related designs,
child work items, evidence, exit criteria) — but nothing captures a persistent
role, permission ceiling, or communication/review policy. The gap is real and
orthogonal, not a re-skin of an existing artifact.

The motivation is the "graduate-student / managed-employee" pattern: the user
wants to delegate a bounded stream of work to a standing role, have that role
plan and supervise under explicit policy, report on a cadence, escalate the
right things, and build up reviewed knowledge — while the role remains
independent of any one backend and never becomes an unbounded autonomous
process. This proposal captures a full design that was developed externally
(the *Unified Assistant Architecture* document, 40 pp, reviewed and its code
and best-practice claims independently verified during the 2026-07-24
session).

Best-practice grounding (verified this session):

- **Least privilege & separation of duties** (NIST CSRC): privileges are held
  to the minimum needed, and no single role can both prepare and approve a
  consequential action. The assistant's `permission_ceiling`, "cannot approve
  its own work" rule, and independent-verification obligation map directly to
  AC-6 / AC-5.
- **Few durable abstractions / code-driven orchestration** (OpenAI Agents
  SDK): prefer specialized agents and deterministic code orchestration. This
  proposal introduces exactly **one** new artifact class and defers
  missions / engagements / teams / inboxes.
- **Separate agent reasoning from workflow state** (Microsoft Agent
  Framework): agents reason; deterministic, checkpointed workflows hold state
  and human-in-the-loop gates. The assistant directory holds role config; the
  run tree stays authoritative for execution.
- **Progressive disclosure / portable packages** (Anthropic Agent Skills):
  a directory package with `SKILL.md` and `references/`, loaded in tiers. The
  assistant is such a package — portable across backends.

## Prior Art Check

### Duplication search
- In-repo: No existing implementation of an assistant *role* artifact class.
  Grep hits for "assistant" resolve to `src/lrh/assist/` — the request /
  run-packet **tooling** layer ("assist"), which is a different concern from
  the `project/assistants/` **role artifacts** proposed here. The naming
  proximity is noted as an Open Question.
- Sibling repos: Taurcode has an LRH-like control plane but no known assistant
  role class; not inspected in depth for this proposal.
- External libraries: None adopted — the design deliberately owns *semantic*
  policy in LRH and delegates *enforcement* to backend adapters (OpenAI Agents
  SDK, MS Agent Framework, and Anthropic Agent Skills are used as
  best-practice references, not dependencies).
- Recommendation: **Proceed.**

### Demand search
- Work items: None found.
- Proposals: None define a persistent assistant role. Adjacent proposals
  cover the *enforcement* substrate (constitutional-sandbox-envelope), the
  *reporting* surface (lrh-serve-operational-triage-mvp,
  meta-operational-triage-semantics), and *run-tree* integration
  (workstream-execution-framework, lrh-execution-sessions,
  execution_framework_mvp) — related, not duplicative.
- Backlog: No matching entries.
- Recommendation: **No action** — cross-link the adjacent proposals (see
  Cross-References).

## Design Decisions

### Decision 1: A new first-class artifact class `project/assistants/`
The assistant is neither a contributor (actor), a planning node, a
workstream, nor a run. It is a reusable role. **Chosen:** add
`project/assistants/<slug>/` as a first-class artifact class with `ASST-` ID
prefix (avoids collision with the common software meaning of `AST`).
Discovery is exactly `project/assistants/*/assistant.md` — not every Markdown
file is an assistant.

### Decision 2: Directory package, not a monolithic prompt or lifecycle buckets
**Chosen:** a directory package (`README.md`, `assistant.md`, `scope.md`,
`policy.md`, `preferences.md`, `communication-policy.md`, `context-policy.md`,
`review-policy.md`, `SKILL.md`, `references/`, `memory/`, `evaluations/`).
This gives progressive disclosure, portable skill behavior, independently
reviewable policies, and separate memory governance. Lifecycle state stays in
`assistant.md` (`status: active|inactive|deprecated`) rather than in directory
buckets, so package paths remain stable and skill references never break.

### Decision 3: Flat frontmatter + namespaced string tokens
The LRH parser rejects nested frontmatter mappings (verified:
`src/lrh/control/parser.py` raises on indented sub-mappings). **Chosen:**
express all policy as flat scalar fields, block lists, and **namespaced string
tokens** (e.g. `planning:assess`, `review:fix_within_scope`,
`run:launch_approved`). No YAML-parser expansion is required for the MVP.

### Decision 4: Assistant roles carry capability, not authority
**Chosen:** the role package declares `capabilities` (what the role knows how
to do) and a `permission_ceiling` (the maximum authority that may *ever* be
granted). The **active** grant comes from a workstream binding and narrows
monotonically: `role ceiling ∩ binding grant ∩ work-item readiness ∩
run-packet authority ∩ backend capability`; hard denials win; with no run
packet, mutation-capable operations resolve as unavailable. Preferences rank
allowed alternatives and can never expand scope, grant tools, bypass a gate,
suppress an escalation, override a prohibition, or weaken validation.
Separation of duties is explicit: the assistant cannot approve its own work,
and independent verification after self-authored fixes is an **obligation**,
not a preference. Merge, release, publish, and closeout remain human- or
policy-gated. This aligns with LRH's existing safe-default resolution, where
missing human gates default to `True` (verified:
`src/lrh/control/execution_readiness.py`).

### Decision 5: One assistant binds one root workstream via `managed_by` (MVP)
**Chosen:** for the MVP, the binding lives on a single **root** workstream
through `managed_by` plus contract fields (`assistant_contract`,
`assistant_escalates_on`, `assistant_reports_on`, `assistant_cadence_mode`),
compiled into a typed `AssistantBinding`. Child workstreams inherit the
association for display/reporting but do not override it; `managed_by` is a
*management* relationship, not a parent-child planning edge. A future
first-class `project/engagements/` artifact is **deferred** until a
demonstrated need (multi-root delegation, reassignment, assistant teams,
cross-repo). Both the current and future source forms compile into the same
`AssistantBinding`, so downstream consumers depend on the binding, not on raw
workstream fields. *This decision adds fields to the `Workstream` schema and
is therefore a `schema_change` — it must go through schema-change escalation,
validation, and tests when implemented.*

### Decision 6: Semantic communication, separated from rendering
**Chosen:** communications are typed semantic messages with independent
dimensions (`intent`, `topic`, `urgency`, structured payload) rather than a
growing enum, rendered through profiles (`compact_chat`, `standard_markdown`,
`detailed_report`, …). Cadence is hybrid (baseline heartbeat + maximum
silence + phase/risk adjustment + immediate event triggers + on-demand
requests). Communication is **not** project truth: a status message may
describe or recommend a state change but never itself resolves a work item,
closes a workstream, approves a design, or merges a PR. Acknowledgment is
distinct from approval.

### Decision 7: Context is always derived, never hand-maintained
**Chosen:** the assistant directory must not store live work state
(`state.yaml`, `tasks/`, `current.md`, `blockers.md`). Context is composed
on demand into a typed `AssistantContextBundle` from the deterministic
read-only `CoreProjectState` plus the binding, workstream subtree, work-item
readiness, run state/events, communications, and accepted memory, via named
views (`orientation`, `current`, `status`, `blockers`, `changes`, `handoff`,
…). Every context item carries provenance, authority label, timestamp,
sensitivity, and inclusion rationale; incomplete event coverage is reported
honestly rather than fabricated.

### Decision 8: Reviewed memory governance, advisory only
**Chosen:** assistant memory uses `proposed → accepted → retired`; promotion
to `accepted` requires a human reviewer, timestamp, retained provenance, and
validation. The assistant may propose memory only with `memory:propose` and
may never accept its own memory, modify its policy, remove mandatory
escalations, alter its ceiling, rewrite acceptance criteria, or retire
inconvenient memory without review. Accepted assistant memory is **advisory**:
it may guide behavior but does not participate in LRH precedence and cannot
override principles, goals, roadmap, focus, approved design, workstream scope,
or work-item acceptance. Its relationship to `project/memory/decision_log.md`
and `project/memory/decisions/` is explicitly one of non-precedence advisory
guidance, not a competing decision record.

### Decision 9 (caution): Policy tokens require an authoritative catalog
The policy model is stringly-typed tokens. For validation to be real, an
**authoritative catalog** of legal capability / permission / obligation /
prohibition / escalation tokens must exist — otherwise typos and unknown
tokens pass silently. **Chosen:** the token catalog ships in the **same
increment** as the schema and validation (not deferred), mirroring the LRH
lesson that a template without its catalog entry is inert.

### Decision 10 (caution): Policy is advisory until the sandbox envelope enforces it
Enforcement of the permission ceiling and prohibitions belongs to the
**constitutional-sandbox-envelope** (currently `proposed / not_started`).
Until that lands, the assistant's ceiling and prohibitions are — in the
design's own adapter vocabulary — `prompt_enforced_only`, not hard runtime
guarantees. **Chosen:** the proposal and all assistant packages state this
plainly so the safety posture is not oversold; each vendor adapter must report
every hard policy as `enforced | prompt_enforced_only | unsupported |
requires_human_gate`, and an unsupported hard requirement must stop execution
or require an explicit human-approved fallback.

## Non-Goals

- **Does not implement runtime behavior.** This proposal is documentation
  only; no Python, launching, monitoring, scheduling, or run mutation.
- **Does not introduce `project/engagements/`, assistant teams, missions,
  initiatives, inboxes, or offices** — all deferred until a demonstrated need.
- **Does not add an autonomous scheduler, daemon, or webhook.** Cadence
  declarations describe intent; enforcement is sequenced behind durable run
  state and the sandbox envelope.
- **Does not grant the assistant merge, release, publish, force-push, or
  closeout authority** — these remain human- or policy-gated.
- **Does not supersede any existing proposal.** It is a peer that depends on
  the sandbox-envelope for enforcement and feeds the serve/triage reporting
  surface (see Cross-References).
- **Does not expand the frontmatter parser.** Flat fields + namespaced tokens
  only.
- **Does not make assistant memory authoritative.** It never participates in
  LRH precedence.

## Implementation Plan

Scope is **large / multi-stage**; delivery is staged and docs-first. The
first increment is documentation only. A governing workstream should own the
per-stage work items.

- **Stage 0 — Design adoption (this proposal).** Record the design, non-goals,
  and migration/deferral triggers.
- **Stage 1 — Documentation-only package convention (first PR).**
  `project/assistants/README.md`, one fully worked example package, the schema
  and **token vocabulary/catalog**, and the ID/status conventions. No Python.
- **Stage 2 — Typed models and loaders.** `Assistant`, modular profile
  objects, `AssistantProfile`, assistant fields on `Workstream`,
  `AssistantBinding`, project indexes. *(Deferred behind Stage 1.)*
- **Stage 3 — Validation.** Package, cross-file, policy-token (against the
  Stage 1 catalog), binding, memory-state, and path-safety validation.
- **Stage 4 — Core-state projection.** `AssistantState`,
  `AssistantBindingState`, `assistants_by_id`; assistants stay outside
  planning-tree parent-child relationships.
- **Stage 5 — Inspection & context rendering.** Safe-default read-only
  `lrh assistant list | inspect | context --view …` (Markdown + JSON); no
  dispatch or mutation.
- **Stage 6 — Communication semantics & rendering.** Typed messages, cadence
  resolution, render profiles, on-demand reports; no background scheduler.
- **Stage 7 — Memory & evaluations.** Memory validation, promotion helper,
  evaluation fixtures, portability tests.
- **Stage 8 — Dogfood pilot.** Bind one bounded real assistant (e.g. a
  `serve-interface-steward`) to one root workstream; evaluate the full flow
  manually.
- **Stage 9 — Durable run integration.** Prepare/launch/observe/classify
  against the run tree; surface awaited transitions; resume after human
  responses. *(Sequenced behind durable run state.)*
- **Stage 10 — Scheduled / event-driven supervision.** Only after durable
  state and adapters exist.

Migration to `project/engagements/` happens only after a demonstrated need for
independent-lifecycle delegation; both source forms compile to the same
`AssistantBinding`.

## Cross-References

- **Enforcement (dependency):**
  `project/design/proposals/proposed/constitutional-sandbox-envelope/00_proposal.md`
  — the capability policy-check / sandbox layer the assistant's
  `permission_ceiling` and `prohibitions` resolve against.
- **Reporting surface (feeds):**
  `project/design/proposals/proposed/lrh-serve-operational-triage-mvp/00_proposal.md`
  and `.../meta-operational-triage-semantics/00_proposal.md` — the dashboards /
  triage semantics the assistant's communication model renders into.
- **Run-tree integration (cross-links):**
  `project/design/proposals/proposed/workstream-execution-framework/00_proposal.md`,
  `.../lrh-execution-sessions/00_proposal.md`, and
  `project/design/execution_framework_mvp.md`.
- **Substrate:**
  `project/design/proposals/adopted/workstreams-and-recursive-planning-tree/00_proposal.md`
  (planning tree) and `.../lrh-project-local-skills/00_proposal.md` (Agent
  Skills package convention `SKILL.md` reuses).
- External best-practice references (not dependencies): NIST CSRC least
  privilege / separation of duties; OpenAI Agents SDK; Microsoft Agent
  Framework; Anthropic Agent Skills.

## Open Questions

- **Module naming.** The existing `src/lrh/assist/` package (request /
  run-packet tooling) is adjacent in name to the proposed `Assistant` role and
  `lrh assistant` CLI. Decide whether the CLI/loaders live under
  `src/lrh/assist/`, a new `src/lrh/assistants/` module, or elsewhere, to
  avoid "assist" vs "assistant" confusion. (Deferred to Stage 2.)
- **Execution-record linkage.** The design pairs `assistant_role: ASST-…`
  with `agent:` on execution records. Confirm whether this is an execution
  record schema addition in Stage 2 or a later increment.
- **Binding cardinality beyond MVP.** `managed_by` is singular on one root
  workstream. The trigger set for promoting to `project/engagements/` is
  listed; confirm it before any multi-root work.
