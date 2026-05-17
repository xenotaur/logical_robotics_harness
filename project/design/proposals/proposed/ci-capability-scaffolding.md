---
id: PROP-CI-CAPABILITY-SCAFFOLDING
type: design_proposal
title: CI Capability Scaffolding
status: proposed
created_on: 2026-05-14
updated_on: 2026-05-14
implementation_status: partial
implemented_by:
  - WI-CI-PLAYBOOK
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-CI-CAPABILITY-SCAFFOLDING
supersedes: []
superseded_by: null
---

# CI Capability Scaffolding Design Proposal

## Summary

LRH should turn recent CI and development-toolchain reconciliation lessons into reusable CI
capability scaffolding for humans and agents. The target capability is not a universal workflow
file. It is a staged set of project-control guidance, request-template behavior, and possible skill
support that helps different repository families assess, design, implement, debug, and harden CI
without erasing repository-specific conventions.

This proposal began as design/control-plane alignment only. The first implementation phase now adds
the human CI playbook at `docs/how-to/project-setup/ci.md`; request-template updates, Agent Skill design,
CI templates, and repository workflow changes remain out of scope for that playbook PR.

## Problem statement

CI setup and debugging failures recur across multiple repositories. Recent LRH toolchain work showed
that several failure classes are common enough to deserve reusable guidance:

- local, CI, and agent environments drift over time;
- setup/bootstrap phases are often confused with task-phase validation;
- formatter and linter versions need explicit guardrails where reproducibility matters;
- workflow YAML validity needs a quick canonical check before deeper CI debugging;
- agent claims such as "cannot reproduce" are weak unless backed by command output, versions,
  commit state, and other reviewable evidence; and
- LRH-supported repositories differ enough that one workflow template would likely be brittle.

The capability must work across heterogeneous project families, including Python package/tool
projects, Unix command/tool projects, Rust/WebGPU/WASM projects, and game or simulation projects.

## Design goal

Create reusable LRH CI capability scaffolding that helps humans and agents assess, design,
implement, debug, and harden CI for heterogeneous repositories while preserving each repository's
canonical scripts, setup model, validation expectations, and review process.

## Proposed staged approach

1. **Human playbook** — add a concise CI setup and debugging playbook at
   `docs/how-to/project-setup/ci.md` that captures environment parity, setup/validation separation,
   canonical-command use, tool-version guardrails, workflow YAML checks, and evidence expectations.
   This phase is implemented by `WI-CI-PLAYBOOK`.
2. **Request-template refresh** — update existing LRH CI request templates, including
   `src/lrh/assist/templates/request/ci_assess_status.md` and
   `src/lrh/assist/templates/request/ci_implement_workflow.md`, so CI assessment and implementation
   prompts apply the playbook rather than rediscovering the same guidance.
3. **CI Agent Skill prototype design** — after playbook and prompt behavior stabilize, design a CI
   setup/assessment Agent Skill as a possible LRH skill prototype. The first step should be design,
   not immediate automation.
4. **Template or reusable-fragment reassessment** — after dogfooding the playbook and prompts,
   reassess whether reusable workflow templates or smaller fragments are useful. Prefer evidence from
   real repositories before committing to shared CI YAML.

## Best-practice principles

- Prefer repository canonical scripts over raw ad hoc tool commands.
- Separate setup/bootstrap from validation, especially in agent prompts and CI diagnostics.
- Constrain or pin formatter, linter, runtime, and build-tool versions where reproducibility matters.
- Validate workflow YAML before treating CI failures as runtime or package failures; consider deeper
  semantic linting later when a repository has opted into that tooling.
- Require evidence before claims such as "cannot reproduce" or "CI is flaky".
- Preserve repository-specific setup and validation conventions instead of forcing all projects onto
  one template.
- Keep the first pass documentation- and prompt-oriented until dogfooding shows where automation is
  genuinely reusable.

## Non-goals

- Do not force all projects onto one CI template.
- Do not introduce a universal project generator.
- Do not require Docker or dev containers.
- Do not require pre-commit, tox, nox, Poetry, uv, pip-tools, or actionlint in the first pass.
- Do not fully automate CI setup without human review.
- Do not replace repository-specific scripts and conventions.
- Do not modify LRH's existing CI workflows as part of this design proposal.

## Risks and mitigations

### Too generic to be useful

Mitigation: start from concrete LRH toolchain-reconciliation lessons and dogfood the playbook across
several repository families before declaring it stable.

### Prompt sprawl

Mitigation: refresh existing CI assessment and implementation request templates first. Add new
prompt surfaces only when existing templates cannot express a repeated need.

### Premature skill abstraction

Mitigation: require a stable playbook and prompt behavior before designing a CI Agent Skill
prototype. Treat the skill as a later design artifact, not as the first implementation step.

### Stale templates

Mitigation: make request templates reference durable playbook concepts rather than duplicating long
CI guidance. Reassess templates after dogfooding.

### Overengineering

Mitigation: avoid a universal generator, required container stack, or mandatory CI-linting tool in
the first pass. Prefer lightweight documentation, canonical-command discipline, and evidence
requirements.

## Acceptance criteria for the overall design

The design can be considered effective when:

- a usable human CI setup and debugging playbook exists at `docs/how-to/project-setup/ci.md`;
- CI assessment and implementation requests apply that playbook;
- any CI Agent Skill prototype is designed only after playbook and prompt stabilization; and
- reusable templates or fragments are reassessed based on dogfooding evidence rather than assumed up
  front.

## Work items and follow-up seeds

`WI-CI-PLAYBOOK` is the first implementation leaf and creates the human CI setup and debugging
playbook at `docs/how-to/project-setup/ci.md`.

Likely follow-up work items, if adopted, are:

- `WI-CI-REQUEST-TEMPLATES` — refresh CI request templates to apply the playbook;
- `WI-CI-SKILL-PROTOTYPE` — design a CI setup/assessment Agent Skill prototype after prompt
  stabilization; and
- `WI-CI-TEMPLATE-FRAGMENTS-ASSESSMENT` — reassess reusable templates or fragments using dogfooding
  evidence.
