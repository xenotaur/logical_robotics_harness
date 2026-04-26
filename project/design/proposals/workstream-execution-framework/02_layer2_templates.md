---
id: PROP-WORKSTREAM-LAYER2-TEMPLATES
title: Layer 2 — First-party LRH Templates for Workstream Stages
status: proposed
type: design_proposal
created_on: 2026-04-26
updated_on: 2026-04-26
parent: PROP-WORKSTREAM-EXECUTION-FRAMEWORK
---

# Layer 2 — First-party LRH Templates for Workstream Stages

## Summary

This sub-proposal ships the **first-party Markdown templates** for the
per-stage artifacts a workstream emits as it advances. Each template
is a thin Markdown skeleton with prompts that guide a contributor (or
an agent) to fill in the right sections, plus YAML frontmatter that
matches LRH's existing schema dialect. Templates live as **package
resources** under `src/lrh/assist/templates/workstream/` so that
installed-package usage works without repository-relative paths,
matching the package-owned template direction documented in the
repo-root README.

The deliverable boundary for Layer 2 is small: after this layer ships,
`lrh workstream new` and the per-stage advance commands (Layer 3) can
materialize the right template into the right file at the right time.
The templates are deliberately **not** spec-kit's templates: LRH's
schema dialect, conventions, and audience differ enough that adopting
spec-kit's would force a translation layer for marginal benefit. We
*do* embrace spec-kit's "specification as the center of the
engineering process" framing ([github/spec-kit][spec-kit]) — that's
exactly what a workstream's `design.md` is.

## Table of contents

1. [Goals and non-goals](#1-goals-and-non-goals)
2. [Why first-party rather than borrowed](#2-why-first-party-rather-than-borrowed)
3. [Template inventory](#3-template-inventory)
4. [Template loading and discovery](#4-template-loading-and-discovery)
5. [Per-template content guides](#5-per-template-content-guides)
6. [Worked examples](#6-worked-examples)
7. [Tests](#7-tests)
8. [Risks](#8-risks)
9. [References](#9-references)

## 1. Goals and non-goals

### Summary

Layer 2 ships templates and only templates. The CLI hooks that *use*
the templates (`lrh workstream new`, the per-stage advance commands)
ship in Layer 1 and Layer 3. We're separating "what the template
contains" from "when it gets stamped out" because the templates are
re-usable in manual mode (a human just cat's the template and edits)
and in agent mode (an agent receives the template as context and
fills it in).

### Goals

A complete inventory of templates for every artifact a workstream
emits (`workstream.md`, `conception.md`, `assessment.md`, `design.md`,
`plan.md`, prompt, decision-record, evidence-stub). Package-resource
loading so that templates work in installed-package contexts. A
template-loader API (`lrh.assist.templates.workstream.load(name)`)
that returns a Markdown string suitable for stamping out. A template
linter that catches drift between templates and schema (e.g. a
template referencing a frontmatter field that the schema doesn't
recognize).

### Non-goals

We do not ship a template-rendering engine — templates are static
Markdown with placeholder text, not Jinja2. We do not ship a CLI for
listing or editing templates beyond what's needed for the workstream
commands. We do not ship templates for layers other than the
workstream lifecycle (work-item templates, focus templates, etc. are
out of scope for this proposal).

## 2. Why first-party rather than borrowed

### Summary

We considered adopting spec-kit ([github/spec-kit][spec-kit]) or
OpenSpec ([Fission-AI/OpenSpec][openspec]) templates wholesale. Both
are good projects. Both are wrong for LRH's specific needs. This
section names the reasoning so the decision is reversible later.

### What spec-kit and OpenSpec are good at

spec-kit is a comprehensive Spec-Driven Development toolkit that uses
a "constitution document that establishes a set of non-negotiable
principles" and a specification "where instead of writing a spec and
setting it aside, the spec drives the implementation, checklists, and
task breakdowns" ([github/spec-kit][spec-kit]). It works with 30+ AI
coding agents.

OpenSpec is a lighter-weight alternative that "adds a lightweight
spec layer so you agree on what to build before any code is written"
and gives "each change its own folder with proposal, specs, design,
and tasks" ([Fission-AI/OpenSpec][openspec]).

Both are doing real work in the SDD space and are worth tracking.

### Why we don't adopt their templates

LRH's schema dialect is already established (`project/design/design.md`
§15 lays it out). Existing artifacts — focus, work items, evidence,
executions — use frontmatter fields that are LRH-specific (`status`
buckets, `acceptance`, `required_evidence`, `expected_actions`,
`forbidden_actions`). Adopting spec-kit's templates would force every
template to either drop these fields (lose information) or duplicate
them in spec-kit's vocabulary (translation layer). Neither is good.

LRH's audience is multi-modal — humans editing in IDEs, agents
filling templates from prompts, and validators reading frontmatter.
spec-kit's templates are tuned for AI coding agents specifically; they
include a lot of agent-directed prose ("now generate...") that is
noisy for human contributors and orthogonal to LRH's evidence-grounded
philosophy. We want templates that read well to a human first and
work well for an agent second.

LRH's lifecycle is different. spec-kit and OpenSpec model a single
linear flow (spec → plan → tasks → implement). LRH's workstream
lifecycle has eight stages with manual-mode parity and explicit gates,
plus closure with structural evidence checks. Trying to fit that into
spec-kit's templates would lose the gating and parity structure.

### What we borrow conceptually

The "constitution as principles" framing is good — LRH already has
`principles/` and the connection is now explicit. The "spec drives
implementation" framing is good — that's exactly what `design.md`
plus `plan.md` plus `prompts/` does in our model. The "each change
gets its own folder" pattern is good — that's exactly what
`project/workstreams/{bucket}/WS-{SLUG}/` is.

So: borrow the ideas, ship our own templates. The decision is
documented; if a future LRH version wants to adopt spec-kit-compatible
templates as an alternative, that's an orthogonal addition and not a
breaking change.

## 3. Template inventory

### Summary

Eight templates, each corresponding to an artifact a workstream
emits. The naming matches the on-disk filename so that loading a
template by filename is unambiguous.

### Templates

```text
src/lrh/assist/templates/workstream/
  workstream.md.tmpl        # the manifest (used by `lrh workstream new`)
  conception.md.tmpl        # written at conceived stage
  assessment.md.tmpl        # written at assessed stage
  design.md.tmpl            # written at designed stage
  plan.md.tmpl              # written at planned stage
  prompt.md.tmpl            # one per prompt under prompts/
  decision.md.tmpl          # one per decision under decisions/
  evidence_stub.md.tmpl     # used by Layer 5b's stub-and-fill flow
```

The `.tmpl` suffix is a minor convention to distinguish "template" from
"stamped-out file." When a template is materialized, the suffix is
dropped (`workstream.md.tmpl` → `workstream.md`).

### Coverage

These eight templates cover every Markdown file a workstream produces
in the lifecycle. The `prompts/PROMPT-XXX.md` and
`decisions/DEC-XXX.md` files are stamped from `prompt.md.tmpl` and
`decision.md.tmpl` with a numeric suffix. Per-stage artifacts are
stamped 1:1.

Layer 5b's stub-and-fill manual evidence flow uses
`evidence_stub.md.tmpl` to scaffold a `project/evidence/staging/`
file that a human contributor fills in by hand. The template is
shared with the agent path so manual-mode parity is preserved (same
shape, different author).

## 4. Template loading and discovery

### Summary

Templates load via `importlib.resources` so installed-package usage
works without repository-relative paths. The loader API is small and
deliberately read-only.

### Loader API

```python
# src/lrh/assist/templates/workstream/__init__.py
from importlib.resources import files


def load(template_name: str) -> str:
    """Load a workstream template by short name.

    Args:
        template_name: One of "workstream", "conception", "assessment",
            "design", "plan", "prompt", "decision", "evidence_stub".

    Returns:
        The template's Markdown content as a string.

    Raises:
        ValueError: If template_name is not a known template.
    """
    valid = {
        "workstream",
        "conception",
        "assessment",
        "design",
        "plan",
        "prompt",
        "decision",
        "evidence_stub",
    }
    if template_name not in valid:
        raise ValueError(
            f"unknown workstream template: {template_name!r}"
        )
    resource = files("lrh.assist.templates.workstream").joinpath(
        f"{template_name}.md.tmpl"
    )
    return resource.read_text(encoding="utf-8")
```

UTF-8 is explicit (per STYLE.md §"Encoding"). The loader does no
substitution — callers are responsible for any string-replacement
they need (Layer 3's writer handles this for new workstreams).

### Stamping conventions

The single placeholder convention is `{{FIELD_NAME}}` for fields the
caller will substitute. Anything else in a template is literal
content. Examples:

```text
id: {{WS_ID}}
title: {{WS_TITLE}}
created_on: {{TODAY_ISO}}
```

The caller (Layer 3's `writer.py`) builds a substitution dict from
the workstream-creation context and does a literal `str.replace` for
each placeholder. We deliberately avoid Jinja2 or any other
template engine — the placeholders are simple enough that
`str.replace` is correct and the dependency surface stays minimal.
This matches the LRH preference for "simple > clever"
(STYLE.md §"Philosophy").

## 5. Per-template content guides

### Summary

Each template has a recognizable structure: frontmatter at the top,
a one-paragraph summary, then numbered sections with **inline
guidance** in italics that disappears once the contributor edits.
This section walks each template's structure and shows the inline
guidance in action.

### `workstream.md.tmpl`

Materialized as `WS-{ID}/workstream.md` by `lrh workstream new`.

```markdown
---
id: {{WS_ID}}
title: {{WS_TITLE}}
stage: conceived
mode_default: {{MODE_DEFAULT}}
created_on: {{TODAY_ISO}}
updated_on: {{TODAY_ISO}}
related_focus:
  - {{FOCUS_ID}}
sibling_workstreams: []
gates:
  designed_to_planned: auto
  planned_to_executing: confirm
  executing_to_reviewing: auto
  reviewing_to_closed: confirm
expected_evidence_at_close: {}
budget:
  per_workstream_usd: 10.00
  per_call_usd: 2.00
owner: {{OWNER}}
contributors: []
assigned_agents: []
transitions: []
---

# {{WS_TITLE}}

*One-paragraph description of what this workstream is for. Replace
this italicized text with prose that names the problem, the desired
outcome, and the rough scope.*

## Notes

*Add any notes that don't yet rise to the level of `conception.md`.
Once you advance to `assessed`, this section is informational only.*
```

### `conception.md.tmpl`

Written at the `conceived` stage. The conception is the deliberately
unstructured "what is this work?" stage — like a tech-design "back of
the envelope" sketch.

```markdown
---
workstream: {{WS_ID}}
stage: conceived
written_at: {{TODAY_ISO}}
written_by: {{AUTHOR}}
---

# Conception — {{WS_TITLE}}

## What we want

*Describe the desired outcome in plain language. What does the world
look like when this workstream is done?*

## Why now

*Why does this matter to the project right now? What changes if we
don't do it?*

## Rough shape

*A loose paragraph or two on how you imagine the work decomposing.
This is not a design — it's a sketch. Specifics belong in
`design.md`.*

## Adjacent threads

*Are there sibling workstreams or related work items? Name them. The
`sibling_workstreams` frontmatter field on `workstream.md` is the
authoritative list; this section is the human-readable explanation.*
```

### `assessment.md.tmpl`

Written at the `assessed` stage. Assessment is where scope, risk, and
mode get nailed down before design begins.

```markdown
---
workstream: {{WS_ID}}
stage: assessed
written_at: {{TODAY_ISO}}
written_by: {{AUTHOR}}
---

# Assessment — {{WS_TITLE}}

## Scope

*What is in scope? What is out of scope? Be specific. If the conception
mentioned five things, name which five and which are deferred.*

## Constraints

*Time, cost, tooling, data, contributor availability, guardrails. The
`forbidden_actions` mechanism applies here.*

## Risks

*Top three risks. For each, what makes you confident the workstream
can complete despite the risk?*

## Mode choice

*Why is this workstream `manual`, `agent`, or `hybrid`? If hybrid,
which stages are which? If agent, what's the rationale and what's
the budget?*

## Success criteria

*How will we know we're done? These should map to entries in
`expected_evidence_at_close`.*
```

### `design.md.tmpl`

Written at the `designed` stage. This is where the workstream meets
LRH's existing `design/` directory style — it's a *technical design
document* for the work.

```markdown
---
workstream: {{WS_ID}}
stage: designed
written_at: {{TODAY_ISO}}
written_by: {{AUTHOR}}
---

# Design — {{WS_TITLE}}

## Summary

*One-paragraph technical summary.*

## Approach

*The technical approach. Tools, data, intermediate artifacts.*

## Schema additions

*Does this workstream introduce new evidence kinds? New frontmatter
fields? List them here so they get registered in
`project/evidence/schemas/` per Layer 5b.*

## Open questions

*Anything that should be resolved before planning.*

## References

*Existing LRH artifacts (focus, work items, prior workstreams,
decisions) this design builds on.*
```

### `plan.md.tmpl`

Written at the `planned` stage. The plan is the bridge from design to
execution — it lists the prompts that will run.

```markdown
---
workstream: {{WS_ID}}
stage: planned
written_at: {{TODAY_ISO}}
written_by: {{AUTHOR}}
---

# Plan — {{WS_TITLE}}

## Prompts

*A numbered list of `PROMPT-XXX` entries that will produce the
workstream's evidence. Each prompt should produce at least one
evidence record. Reference the prompt files under `prompts/`.*

| Prompt   | Purpose                                  | Mode    | Budget  |
|----------|------------------------------------------|---------|---------|
| P-001    | *…*                                      | agent   | $0.50   |
| P-002    | *…*                                      | manual  | $0.00   |

## Sequencing

*Does any prompt depend on a prior prompt's evidence? Note it here.*

## Closure criteria

*Map prompt outputs to the `expected_evidence_at_close` entries.*
```

### `prompt.md.tmpl`

Materialized as `prompts/PROMPT-XXX.md`. This is LRH's existing
prompt-record schema — see `PROMPTS.md` — extended with workstream
context.

```markdown
---
prompt_id: {{PROMPT_ID}}
workstream: {{WS_ID}}
work_item: {{WORK_ITEM_ID_OR_NULL}}
mode: {{MODE}}
budget_usd: {{BUDGET}}
permission_mode: {{PERMISSION_MODE}}
allowed_tools:
  - Read
  - Write
forbidden_actions:
  - production_write
created_on: {{TODAY_ISO}}
---

# {{PROMPT_TITLE}}

## Purpose

*What evidence is this prompt designed to produce?*

## Inputs

*Which files or artifacts the prompt should read.*

## Expected output

*What evidence kind(s) should result. Reference Layer 5b's evidence
kinds.*

## Prompt body

```text
*The actual prompt text the agent (or human) executes.*
```

## Constraints

*Anything the prompt explicitly should NOT do.*
```

### `decision.md.tmpl`

Materialized as `decisions/DEC-XXX-{slug}.md`. Captures a decision
made during the workstream that future readers might want to find.

```markdown
---
decision_id: {{DEC_ID}}
workstream: {{WS_ID}}
written_at: {{TODAY_ISO}}
written_by: {{AUTHOR}}
status: accepted
---

# {{DEC_TITLE}}

## Context

*What was the question or tension?*

## Options considered

*1. Option A — pros and cons*
*2. Option B — pros and cons*

## Decision

*What did we pick and why?*

## Consequences

*What follows from this decision? What did we close off?*
```

### `evidence_stub.md.tmpl`

Used by Layer 5b's stub-and-fill flow to scaffold a manual evidence
record. Same shape an agent would produce.

```markdown
---
id: {{EV_ID}}
kind: {{EVIDENCE_KIND}}
workstream: {{WS_ID}}
work_item: {{WORK_ITEM_ID_OR_NULL}}
stage: {{STAGE}}
source: human
captured_by: {{AUTHOR}}
captured_at: {{TODAY_ISO}}
references: []
data: {}
---

# {{EVIDENCE_TITLE}}

*Fill in the body. This evidence record is in
`project/evidence/staging/`; promote to `project/evidence/` once
complete.*
```

## 6. Worked examples

### Summary

Two short examples: stamping a workstream on creation, stamping a
prompt as part of planning.

### Example A — `lrh workstream new`

```bash
$ lrh workstream new --id WS-LCATS-CORPORA-ANALYSIS \
                     --title "Analyze the LCATS corpora" \
                     --focus FOCUS-LCATS-CORPORA \
                     --mode-default hybrid \
                     --owner anthony
```

The CLI calls `lrh.assist.templates.workstream.load("workstream")`,
substitutes `{{WS_ID}}`, `{{WS_TITLE}}`, `{{MODE_DEFAULT}}`,
`{{TODAY_ISO}}`, `{{FOCUS_ID}}`, `{{OWNER}}`, and writes
`project/workstreams/proposed/WS-LCATS-CORPORA-ANALYSIS/workstream.md`.

### Example B — Plan adds a prompt

A contributor at the `planned` stage runs `lrh workstream prompt new`
(this command is detailed in Layer 3 but the template loading is here).
The CLI calls `load("prompt")`, substitutes `{{PROMPT_ID}}` (auto-
generated from a counter), `{{WS_ID}}`, `{{MODE}}`, etc., and writes
`project/workstreams/proposed/WS-LCATS-CORPORA-ANALYSIS/prompts/PROMPT-001.md`.

The contributor then edits the prompt body. The template's `prompts:`
table in `plan.md` doesn't auto-update — the contributor edits it,
which is intentional: the plan is human-curated, the prompts are
file-system records.

## 7. Tests

### Summary

Tests live under `tests/assist_tests/templates/workstream_test.py`.

### Test plan

`load_known_template_returns_string` — every name in the valid set
loads.

`load_unknown_template_raises_value_error` — covers the negative
path.

`installed_package_smoke_test` — install LRH into a clean venv, run
`python -c 'from lrh.assist.templates.workstream import load;
print(load("workstream"))'`. This catches the package-resource
gotcha that `setup.py` or `pyproject.toml` packaging changes can
introduce.

`every_template_parses_as_yaml_frontmatter_plus_markdown` — load each
template, split on the first `---` block, parse the YAML, confirm
required-field placeholders are all present. This is a drift-prevention
test: if a template loses a placeholder by accident, the test fails.

`schema_drift_test` — for each template, list the placeholder names
(`{{FOO}}`); compare to the substitution dict the writer in Layer 3
builds; assert that every placeholder has a corresponding writer
field. (This test ships with Layer 3 since the writer is there.)

`utf8_encoding_smoke_test` — assert all templates are UTF-8
(STYLE.md §"Encoding").

## 8. Risks

### Summary

Layer 2's risks are about drift, not architecture.

Template-schema drift is the dominant risk — a template can name a
field that the schema doesn't recognize, or vice versa. Mitigation:
the schema-drift test in §7 plus a CI check that runs it.

Placeholder convention drift (`{{FOO}}` vs `${FOO}` vs `<<FOO>>`)
across templates would confuse contributors. Mitigation: the
test-suite linter enforces a single convention.

Future LRH versions might want a more sophisticated template engine
(conditionals, loops). Mitigation: keep the API surface — `load(name)
-> str` — narrow enough that we can swap the implementation later
without changing callers.

## 9. References

`project/design/design.md` — LRH design document; templates align with
the existing schema dialect documented there.

`PROMPTS.md` — existing prompt-record schema; the prompt template
extends it with workstream context but doesn't change the existing
fields.

`README.md` (repo root) §"Near-term priorities" — documents the
package-owned-templates direction. This proposal aligns with it.

`STYLE.md` §"Encoding" and §"Philosophy" — UTF-8, simple-over-clever
informed the no-Jinja decision.

[github/spec-kit][spec-kit] — for the SDD framing and the
"constitution" → `principles/` mapping.

[Fission-AI/OpenSpec][openspec] — for the lighter-weight per-change
folder pattern that LRH's workstream directory mirrors.

[spec-kit]: https://github.com/github/spec-kit
"github/spec-kit — Spec-Driven Development toolkit"

[openspec]: https://github.com/Fission-AI/OpenSpec
"Fission-AI/OpenSpec — lightweight spec-driven framework"
