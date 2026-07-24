---
kind: assistant_scope
assistant: ASST-SERVE-INTERFACE-STEWARD
domain_scope:
  - lrh-serve
  - interface-design
  - accessibility
repository_scope:
  - self
managed_paths:
  - self:src/lrh/serve.py
  - self:src/lrh/serve_triage.py
  - self:src/lrh/ux/**
  - self:tests/ux_tests/**
context_paths:
  - self:src/lrh/core_state.py
  - self:project/design/**
  - self:project/workstreams/**
  - self:project/work_items/**
  - self:project/runs/**
excluded_paths:
  - self:.github/workflows/**
  - self:src/lrh/meta/**
managed_artifact_kinds:
  - design_proposal
  - workstream
  - work_item
  - run_report
lifecycle_scope:
  - assessed
  - designed
  - planned
  - executing
  - reviewing
output_surfaces:
  - cli
  - local_web_ui
  - markdown_report
---

# Serve Interface Steward — Scope

Scope distinguishes what this assistant **manages** from what it may only
**inspect** for context.

- **Domain scope** — the subject-matter domains it is responsible for: the
  `lrh serve` surface, interface design, and accessibility.
- **Managed paths** — the code and tests it may propose changes to (through
  work items and runs, never by direct autonomous mutation).
- **Context paths** — read-only material it may inspect to build context
  (core state, designs, planning artifacts, run records) but must not manage.
- **Excluded paths** — explicitly out of bounds even for inspection-driven
  change (CI workflows, the meta control plane).
- **Managed artifact kinds** — the planning/reporting artifacts it may create
  within its lifecycle scope.
- **Lifecycle scope** — the stages it operates in; it does not, for example,
  perform closeout.
- **Output surfaces** — where its work is expected to surface.

The `self:` locator scopes every path to this repository. It leaves room for
future cross-repository forms (for example `repo:<owner>/<name>/**` or
`workspace:<name>/**`) before cross-repository execution is enabled; those are
out of scope for the MVP.
