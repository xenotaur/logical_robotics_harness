---
id: WS-CI-CAPABILITY-SCAFFOLDING
kind: planning_node
title: CI Capability Scaffolding
status: proposed
stage: designed
origin: ad_hoc
summary: Turn LRH's CI and toolchain reconciliation lessons into reusable CI setup, assessment, and implementation capability for heterogeneous repositories.
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_design:
  - project/design/proposals/proposed/ci-capability-scaffolding.md
work_items:
  - WI-CI-PLAYBOOK
exit_criteria:
  - design proposal and control-plane links exist
  - human CI setup and debugging playbook exists at `docs/how-to/project-setup/ci.md`
  - CI assessment and implementation request templates apply the playbook
  - CI Agent Skill prototype is considered only after playbook and prompt stabilization
  - reusable templates or fragments are reassessed using dogfooding evidence
---

# CI Capability Scaffolding

## Purpose

Turn LRH's CI and toolchain reconciliation lessons into reusable CI setup, assessment, and
implementation capability. The workstream should help humans and agents reason about CI across
heterogeneous repositories without forcing every project onto the same workflow template, package
manager, container model, or validation stack.

## Rationale

Recent LRH development-toolchain reconciliation work reduced recurring local, CI, and Codex lint and
formatting mismatch noise. Those lessons are useful beyond LRH itself. A focused workstream keeps the
next steps visible while preserving a design/control-plane boundary: the playbook phase is now
resolved, while request-template changes, skill design, and reusable template experiments remain
future phases.

## Phases

1. **Design proposal and control-plane alignment** — add the CI capability scaffolding proposal,
   create this workstream, and link relevant roadmap, focus, README, and work-item planning notes.
2. **Human playbook** — create a concise CI setup and debugging playbook at
   `docs/how-to/project-setup/ci.md`, covering canonical scripts, setup/validation separation, version
   guardrails, workflow YAML checks, and evidence expectations. This phase is implemented by
   `WI-CI-PLAYBOOK`.
3. **CI request-template refresh** — update CI assessment and implementation request templates to
   apply the playbook and avoid ad hoc rediscovery.
4. **CI Agent Skill prototype design** — design a CI setup/assessment Agent Skill prototype only
   after playbook and prompt behavior stabilize.
5. **Template/fragments reassessment** — decide, based on dogfooding evidence, whether reusable CI
   templates or smaller fragments are worth maintaining.

## Work-item leaves

- `WI-CI-PLAYBOOK` — resolved first implementation leaf that created the human CI setup and
  debugging playbook at `docs/how-to/project-setup/ci.md`.

The remaining seeds are future planning leaves, not active work items yet:

- `WI-CI-REQUEST-TEMPLATES` — refresh `ci_assess_status` and `ci_implement_workflow` request
  templates so they apply the playbook.
- `WI-CI-SKILL-PROTOTYPE` — design a CI setup/assessment Agent Skill prototype after playbook and
  prompt stabilization. LRH-only dogfooding evidence in `project/evidence/EV-0009.md` recommends
  one additional non-LRH dogfood pass before skill design proceeds.
- `WI-CI-TEMPLATE-FRAGMENTS-ASSESSMENT` — reassess reusable CI templates or fragments using
  dogfooding evidence.

## Non-goals for the playbook PR

- Do not update CI request templates beyond links if needed.
- Do not implement an Agent Skill.
- Do not add CI templates or reusable workflow fragments.
- Do not modify existing CI workflows.
- Do not introduce new tooling.

## Exit criteria

This workstream can move toward resolution when the playbook at `docs/how-to/project-setup/ci.md` exists,
CI request templates apply it, skill-prototype design has been considered after stabilization, and
any template or fragment decision
is grounded in dogfooding evidence.
