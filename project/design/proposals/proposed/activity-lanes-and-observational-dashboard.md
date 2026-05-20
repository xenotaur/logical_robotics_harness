---
id: PROP-ACTIVITY-LANES-OBSERVATIONAL-DASHBOARD
type: design_proposal
status: proposed
implementation_status: not_started
---

# Activity Lanes and Observational Dashboard Proposal

## 1) Problem statement

LRH currently has strong project-control artifacts (`project/`) and emerging operational
interfaces, but teams executing work across ChatGPT, Codex Cloud, Codex App, Claude,
VS Code/manual editing, and GitHub PR review can fragment status narratives across tools.

If LRH requires all meaningful work to pass through `lrh run`, then it fails practical
adoption in heterogeneous environments. Most real projects are mixed-mode and must retain
manual + tool-specific workflows while still producing interpretable, evidence-backed
project status.

The core problem: **how to coordinate and summarize heterogeneous workflows without making
centralized execution mediation mandatory**.

## 2) Goals and non-goals

### Goals

- Define a lightweight, tool-agnostic activity-lane model for ongoing work coordination.
- Treat external systems (GitHub, local tools, AI assistants) as observational telemetry
  sources, not authoritative control-plane truth.
- Produce recomputable, cacheable derived snapshots that combine declared project intent
  with observations.
- Support read-only, local-first MVP behavior.
- Enable both CLI and `lrh serve` to consume the same interpreted snapshot contract.

### Non-goals

- Do not introduce mandatory centralized execution (`lrh run` remains optional).
- Do not require database-first architecture for MVP.
- Do not implement autonomous orchestration in this proposal slice.
- Do not bind LRH semantics to a single vendor/tool runtime.

## 3) Design principles

1. **Tool-agnostic control plane**: project declarations remain canonical regardless of tool.
2. **Declared > observed for authority**: project Markdown is authoritative; observations are
   supportive context.
3. **Observation is replayable**: adapters should be recomputable from local artifacts/APIs.
4. **Interpretation is explicit**: dashboard state is derived via deterministic projection rules.
5. **MVP minimalism**: begin read-only, local-first, no mandatory daemon/database.
6. **Evidence linkage**: derived status should always be explainable back to inputs.

## 4) Activity-lane architecture

Introduce lightweight lane records under:

- `project/activity/ACT-*.md`

Each activity lane captures coordination metadata (intent, participants, scope, related work
items, expected evidence signals) without claiming that lane records are raw execution logs.

Conceptually:

- Work items define planned unit(s) of accountable project work.
- Activity lanes define active coordination tracks where work may occur through many tools.
- Evidence artifacts ground completion/health claims.

Lane states should be declaration-oriented (e.g., active/paused/closed) and may include
references to known observational handles (branch names, PR URLs, conversation artifact IDs),
but those handles are not themselves authoritative state.

## 5) Observational telemetry architecture

Define observational adapters as bounded readers:

- local filesystem/worktree signals
- Git metadata signals
- GitHub pull-request/review signals
- optional conversation artifact signals (ChatGPT/Codex/Claude exports when available)

Adapter contract (conceptual):

- input: lane declarations + adapter config + current project root
- output: timestamped observation records (normalized shape + provenance)
- guarantees: read-only, deterministic per fetch point, source-attributed

Observations should include freshness metadata and adapter provenance so interpretation can
surface stale/partial telemetry instead of fabricating certainty.

## 6) Derived dashboard/snapshot architecture

Add a projection layer that interprets:

1. authoritative declarations (`project/`)
2. observational telemetry (adapters)
3. precedence/validation rules

Into snapshot-oriented views:

- per-lane health summary
- portfolio-level rollup
- work-item adjacency summary
- evidence-confidence indicators

Snapshots are **derived artifacts**, not editable source of truth.

## 7) Repository structure changes

Proposed structure additions:

- `project/activity/` for lane declarations (`ACT-*.md`)
- `src/lrh/activity/` for lane model + loader + validator
- `src/lrh/observations/` for observational adapter interfaces and normalization
- `src/lrh/dashboard/` for interpretation/projection into snapshots

MVP may stage this across multiple PRs; this proposal only defines design direction.

## 8) Proposed schemas and example frontmatter

Example activity-lane declaration (`project/activity/ACT-UI-STABILITY.md`):

```yaml
---
id: ACT-UI-STABILITY
type: activity_lane
title: UI stability and review stabilization
status: active
owners:
  - maintainer-team
related_work_items:
  - WI-UI-TRIAGE-MVP
focus:
  - reproducible failures
  - PR review convergence
observational_handles:
  github_prs:
    - 123
  branches:
    - feat/ui-triage
  conversations:
    - CONV-2026-05-UX-TRIAGE
created_at: 2026-05-17T00:00:00+00:00
updated_at: 2026-05-17T00:00:00+00:00
---
```

Observation record schema (conceptual normalized shape):

```yaml
observation_id: OBS-...
observed_at: 2026-05-17T12:34:56+00:00
adapter: github_pull_request
subject:
  type: activity_lane
  id: ACT-UI-STABILITY
signal_type: pr_review_state
payload:
  pr_number: 123
  review_state: changes_requested
provenance:
  source: github_api
  fetch_ref: repo@sha-or-etag
```

## 9) Command-surface proposals

Potential command family:

- `lrh activity list`
- `lrh activity show ACT-...`
- `lrh observe refresh [--adapter ...]`
- `lrh snapshot dashboard [--format json|md]`
- `lrh snapshot lane ACT-...`

Design intent:

- keep `lrh validate` focused on control-plane correctness
- treat observation refresh as optional enrichment
- allow snapshot generation from cached observations when offline

## 10) Storage-boundary design

Authoritative data remains in `project/` Markdown.

Observations and snapshots should be stored separately from authoritative declarations,
for example under `.lrh/runtime/` or an equivalent ignored runtime directory.

Properties:

- safe to delete/recompute
- not required to commit
- optionally materialized for debugging/evidence export

## 11) CLI and `lrh serve` integration strategy

`lrh serve` should not invent a separate state model.

Both CLI snapshot commands and server endpoints should consume one shared interpreted
snapshot contract produced by the same projection code path.

This prevents drift between terminal and dashboard views and preserves deterministic,
inspectable behavior.

## 12) Separation of authoritative state vs derived observations

Authoritative:

- principles, goal, roadmap, focus, work items, evidence, activity-lane declarations

Derived/non-authoritative:

- GitHub status, review chatter, branch recency, conversation artifact metadata,
  inferred lane health labels

Rule: derived labels must be explainable via trace links to observations + declarations.
No silent state mutation of authoritative project files from observational adapters.

## 13) Local-first MVP scope

MVP scope:

- lane declaration model + validation
- one or two read-only adapters (likely Git + local filesystem first)
- snapshot interpreter with explicit freshness/confidence markers
- CLI rendering and `lrh serve` read-only display integration

Out of MVP:

- writeback automation
- autonomous task dispatch
- cross-repo centralized service requirements

## 14) GitHub observational enrichment strategy

GitHub enrichment should be additive and optional:

- PR open/closed/draft state
- review decision distribution
- check-run summaries
- mergeability/conflict indicators

Design constraints:

- graceful degradation without GitHub token/network
- explicit stale-state presentation
- no authoritative status derived solely from GitHub events

GitHub helps interpretation but cannot override declared project-control state.

## 15) Rollout and phased implementation plan

Phase 0 (this proposal):

- adopt architecture direction and contracts

Phase 1:

- add `activity_lane` schema + loader/validator + docs

Phase 2:

- add observational adapter interface + local adapters

Phase 3:

- add snapshot interpreter and CLI snapshot commands

Phase 4:

- wire `lrh serve` to shared snapshot contract

Phase 5:

- add optional GitHub adapter and enrichment policies

Each phase should ship with tests, clear docs, and evidence-backed validation notes.

## 16) Tradeoff analysis and alternatives considered

Alternative A: require all work through `lrh run`.

- Rejected for MVP because it conflicts with heterogeneous real-world workflows and would
  suppress adoption.

Alternative B: vendor-specific deep integration first.

- Rejected because it creates lock-in and delays core tool-agnostic coordination value.

Alternative C: database-first architecture.

- Deferred; can be revisited after proven local-first snapshot workflows.

Chosen approach: declaration-first + observational adapters + derived snapshots.

## 17) Risks and mitigations

Risk: telemetry noise or contradictory signals.

- Mitigation: provenance, freshness, confidence scoring, and explicit unresolved states.

Risk: users misread derived dashboard labels as authoritative truth.

- Mitigation: UX labeling (`derived`, `observed_at`, `source`) and trace drill-down.

Risk: scope creep into orchestration automation.

- Mitigation: strict MVP boundaries and phase gates tied to evidence.

Risk: adapter brittleness across tool changes.

- Mitigation: narrow adapter contracts, graceful degradation, and test fixtures.

## 18) Future directions

- optional adapter packs for ChatGPT/Codex/Claude transcript metadata ingestion
- multi-project portfolio dashboard overlays
- policy packs for org-specific lane health interpretation
- controlled writeback proposals (future design proposals only)

Future evolution should preserve the central LRH boundary:

**authoritative project declarations stay human-readable and tool-agnostic, while
observational telemetry remains derived, recomputable, and non-authoritative.**
