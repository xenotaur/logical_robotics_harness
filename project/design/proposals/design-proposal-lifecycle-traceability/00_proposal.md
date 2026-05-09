---
id: PROP-DESIGN-PROPOSAL-LIFECYCLE-TRACEABILITY
type: design_proposal
title: Design Proposal Lifecycle and Implementation Traceability
status: proposed
created_on: 2026-05-08
updated_on: 2026-05-08
---

## 1) Purpose

Define a future LRH design direction for treating design proposals as
first-class decision artifacts with explicit decision lifecycle metadata,
separate implementation lifecycle metadata, and traceability to work
items and evidence.

This proposal is documentation/design only. It does not implement
parser behavior, validation checks, organizer commands, CLI behavior, or
snapshot reporting.

## 2) Motivation

Design proposals often answer more than one question. A project needs to
know whether a decision governs the work, but it also needs to know
whether the governed design has actually been delivered. Combining those
questions in a single `status` field creates ambiguous project state:
accepted ideas can look complete before implementation exists, and
implemented claims can drift away from the work items or evidence that
would justify them.

LRH should make those states explicit because its project-control model
is meant to be human-auditable, machine-interpretable, deterministic,
and evidence-backed.

## 3) Core principle

Design proposals are decision artifacts with their own lifecycle. Their
adoption state is separate from their implementation state.
Implementation claims must be traceable to work items and evidence.

Central invariant:

```text
status answers whether the design decision governs the project.
implementation_status answers whether the governed design has been delivered.
implemented_by and evidence answer why LRH should believe that claim.
```

This follows established Architecture Decision Record practice in which
decision records carry explicit lifecycle states and supersession
history, while adding LRH-specific traceability from decisions to
implementation work and evidence-backed completion claims.

## 4) Proposed canonical layout

A future organized project should use lifecycle buckets for design
proposal files:

```text
project/design/
  design.md
  proposals/
    README.md
    proposed/
      DP-0002-...
    adopted/
      DP-0001-...
    rejected/
    superseded/
```

Rules:

- Frontmatter `status` is authoritative.
- The directory bucket is derived from `status` for human readability.
- New organized projects should use lifecycle buckets.
- Existing unbucketed proposal files may be supported during migration.
- A future organizer command may move files to their derived buckets.

LRH currently has proposal-set directories under
`project/design/proposals/`. This proposal does not move them. It
records the target convention for future parser, validator, organizer,
and dogfooding work.

## 5) Decision lifecycle metadata

Intended decision lifecycle values:

```yaml
status: proposed | adopted | rejected | superseded
```

Meanings:

- `proposed`: under consideration; not governing yet.
- `adopted`: accepted as project direction; governs implementation.
- `rejected`: considered and not chosen.
- `superseded`: once governed, but replaced by another design proposal.

LRH should use `adopted` as the canonical term for a governing design
proposal. This corresponds to the common ADR concept of an accepted
decision while avoiding ambiguity with implementation completion.

## 6) Implementation lifecycle metadata

Intended implementation lifecycle values:

```yaml
implementation_status: not_started | partial | implemented | deferred | obsolete
```

Meanings:

- `not_started`: adopted design exists, but no implementation work has
  landed.
- `partial`: some linked work or evidence exists, but the design is not
  fully delivered.
- `implemented`: implementation is complete and evidence-backed.
- `deferred`: implementation is intentionally postponed.
- `obsolete`: no further implementation is expected, usually because
  the design was superseded or rejected.

`implementation_status` should eventually be required or strongly
recommended for adopted proposals. Early migration should be tolerant of
older documents and should prefer warnings before hard errors where
reasonable.

## 7) Traceability fields

Core implementation traceability fields:

```yaml
implemented_by:
  - WI-...
evidence:
  - EV-...
```

Supersession fields:

```yaml
supersedes:
  - DP-...
superseded_by: DP-...
```

Future optional fields may include `decided_on`, `decision_owner`, or
`related_work_items`, but this initial design should not make those
fields required.

## 8) Example frontmatter

### Adopted and implemented

```yaml
---
id: DP-0001
kind: design_proposal
status: adopted
implementation_status: implemented
implemented_by:
  - WI-RENDER-0001
  - WI-RENDER-0002
evidence:
  - EV-0002
  - EV-0003
supersedes: []
superseded_by: null
---
```

This means the design governs the project and LRH has linked work items
and evidence supporting the implementation claim.

### Adopted but not started

```yaml
---
id: DP-0002
kind: design_proposal
status: adopted
implementation_status: not_started
implemented_by: []
evidence: []
supersedes: []
superseded_by: null
---
```

This means the design governs the project, but no implementation work
has landed yet.

### Superseded and obsolete

```yaml
---
id: DP-0003
kind: design_proposal
status: superseded
implementation_status: obsolete
implemented_by:
  - WI-OLD-0001
evidence:
  - EV-0010
supersedes: []
superseded_by: DP-0004
---
```

This means the design once governed the project, but another design now
replaces it and no further implementation is expected for the old
decision.

### Implemented but missing evidence warning

```yaml
---
id: DP-0005
kind: design_proposal
status: adopted
implementation_status: implemented
implemented_by: []
evidence: []
supersedes: []
superseded_by: null
---
```

This should be treated as a warning case in early validation: the file
claims implementation is complete, but provides no linked work item or
evidence explaining why LRH should believe that claim.

## 9) Future validation design

Future structural checks should include:

- proposal Markdown files parse successfully;
- frontmatter parses successfully;
- each proposal has an `id`;
- `id` follows the project DP convention;
- the filename includes or starts with the ID.

Future schema checks should include:

- `status` is one of the allowed decision lifecycle values;
- `implementation_status` is one of the allowed implementation lifecycle
  values;
- `implemented_by`, `evidence`, and `supersedes` are lists when present;
- `superseded_by` is a string or null when present.

Future semantic checks should include:

- `implemented_by` values resolve to known work-item IDs;
- `evidence` values resolve to known evidence IDs;
- `supersedes` and `superseded_by` values resolve to known design
  proposal IDs;
- the status bucket matches the directory bucket;
- `status: superseded` normally has `superseded_by`;
- `status: adopted` plus `implementation_status: implemented` has
  evidence and/or implemented work-item links;
- `implementation_status: implemented` is not treated as an
  evidence-free assertion.

Early migration should prefer warnings before hard errors where
reasonable, especially for existing unbucketed proposal files and
proposal files that predate these fields.

## 10) Future tooling design

Implementation should be staged in later PRs:

1. Add a parser and validation model for design proposals.
2. Add `lrh design organize` and `lrh design organize --apply`, modeled
   after `lrh work-items organize --apply`.
3. Extend `lrh snapshot` to report adopted-but-unimplemented, partially
   implemented, implemented, and superseded design proposals.
4. Dogfood the convention in LRH's own `project/design/proposals`.
5. Consider a more generic typed artifact lifecycle framework only after
   this narrower design-proposal feature proves useful.

## 11) Relationship to LRH philosophy

This design reinforces existing LRH project-control principles:

- Markdown-first, human-readable artifacts remain the source of truth.
- YAML frontmatter provides machine interpretation without hiding state.
- Validation and deterministic interpretation reconcile source documents
  with runtime models.
- Completion claims remain evidence-backed rather than optimistic.
- Intent/design, execution/work items, and truth/evidence/status stay
  separate but traceable.

## 12) Scope and non-goals

This proposal does not:

- implement code;
- add CLI commands;
- add validators;
- move existing design proposals;
- broadly refactor existing design documents.

Follow-up PRs may update canonical design documents once this proposal
is adopted and implementation work begins.
