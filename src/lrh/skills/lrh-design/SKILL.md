---
name: lrh-design
description: >
  Generate a structured design for a feature, improvement, or system. Given
  an idea or topic as the argument, reviews the idea, surveys best practices,
  produces a high-level design, identifies low-level choices, evaluates pros
  and cons, and recommends an approach—stopping to clarify or raise blockers
  when needed. After the design, offers to capture findings as an LRH work
  item. Invoke with /lrh-design followed by the idea to design; typically
  used before /lrh-work-item and /lrh-implement to front-load design thinking.
disable-model-invocation: true
argument-hint: "<feature, improvement, or system to design>"
---

# lrh-design Skill

This skill applies a structured design framework to a feature, improvement,
or system the user wants to build. It reviews the idea, surveys best
practices, produces a high-level design, identifies low-level choices,
evaluates pros and cons, and recommends an approach. After the design, it
offers to capture the output as an LRH work item.

Use before `/lrh-work-item` and `/lrh-implement` to front-load design
thinking and catch problems before implementation begins.

---

## Inputs

Provide the idea, feature, or system to design as the argument:

```
/lrh-design Please flesh out a design to implement Option C-1 for /lrh-doc-audit, /lrh-doc-organize, and /lrh-doc-work.
/lrh-design A skill that generates structured designs from a topic
```

The argument may be a short label or a full paragraph of context. More
context produces a more grounded design; less context may trigger a
clarification request at Step 1.

---

## Reference Knowledge

No references are needed. The design framework is embedded in the execution
steps below.

---

## Execution Steps

### Step 1 — Parse and clarify

Restate the topic in one sentence to confirm understanding.

If key information is missing — intent, scope, constraints, or target
system — ask for clarification before proceeding. Do not produce a design
based on an ambiguous brief.

### Step 2 — Check for blockers

If there is a serious issue that makes the idea unsafe, unethical,
architecturally unsound, or otherwise inadvisable, stop and alert the user
with a clear explanation. Do not produce a design that would validate a
fundamentally bad idea without naming the problem.

### Step 3 — Apply design framework

Work through these phases in order. Think step by step. Cite or quote
reputable sources where applicable.

**a. Review the idea**
Understand the goal, context, constraints, and any prior art or related
work in the project. For LRH projects: note how the idea fits the
three-phase model, skill pattern, or control-plane conventions.

**b. Review best practices**
Identify the relevant engineering, architectural, or documentation domain.
Survey applicable best practices, patterns, and known trade-offs. Cite
sources (RFCs, recognized frameworks, canonical texts, prior LRH decisions).

**c. High-level design**
Lay out the approach at a system or architecture level. Describe the major
components, their responsibilities, and how they interact. Diagrams in prose
or structured lists are sufficient.

**d. Low-level choices**
Enumerate the specific implementation decisions the design requires: data
structures, algorithms, file layouts, naming conventions, integration points,
edge cases. These become the "Required Changes" in a work item.

**e. Evaluate pros and cons**
For each major choice identified in (d), assess the options against the best
practices from (b) and the project's constraints. Be explicit about
trade-offs.

**f. Recommend**
State clearly which approach is recommended and why. Note any choices where
the best answer depends on information only the user can supply.

Use best judgment on scope: do not cut corners or incur avoidable technical
debt, and do not over-engineer or introduce premature abstractions.

When citing sources: only cite sources you are confident are real. If no
credible source is available for a claim, say so explicitly rather than
inventing a citation. Prefer explicit gaps over fabricated references.

### Step 4 — Assess scope and offer follow-on

After delivering the design, assess the scope of the resulting work and offer
the appropriate LRH artifact(s). Do not automatically invoke any skill — assess
and offer; wait for the user to decide.

**Scope assessment — apply this matrix:**

| Scope signal | Offer |
|---|---|
| Single PR, well-bounded, no novel architectural decisions | `/lrh-work-item` only |
| Multiple PRs, novel decisions, or uncertain scope | `/lrh-proposal` ± `/lrh-workstream` ± `/lrh-work-item` |
| Complex multi-stage work, deferred scope, or multiple contributors | `/lrh-proposal` + `/lrh-workstream` first; work items later |

**Guidance:**

- **`/lrh-proposal`** — captures the design decision and its rationale as a
  durable record. Offer when the design involves a significant architectural
  choice, affects multiple areas of the codebase, or needs to be referenced
  by future work.
- **`/lrh-workstream`** — groups related work under a planning node. Offer
  when implementation will span multiple PRs or involve multiple contributors.
- **`/lrh-work-item`** — captures a single bounded task. Offer when the design
  maps cleanly to one deliverable, operation, investigation, or evaluation.
  Include a suggested title and type when offering this.

State which combination you are recommending and why, then wait for the user
to confirm before invoking anything.

---

## Quality Checklist

Before reporting the design complete, verify:

- [ ] Topic was restated to confirm understanding
- [ ] Any blockers were surfaced before the design was produced
- [ ] Best practices were surveyed; any citations given are real, not invented
- [ ] High-level design is present
- [ ] Low-level choices are enumerated
- [ ] Pros/cons are evaluated against best practices
- [ ] A clear recommendation is made
- [ ] Any choices that depend on user-supplied information are flagged
- [ ] Scope assessed and appropriate artifact(s) offered (work item, proposal, and/or workstream)

---

## What This Skill Does Not Do

- Does not implement — use `/lrh-work-item` + `/lrh-implement` for that.
- Does not automatically create work items — offers and waits for user decision.
- Does not write files — the design lives in the conversation unless captured.
- Does not run validation, tests, or code analysis — those belong in
  implementation skills.
- Does not replace the Taurcode `:design` Espanso snippet for non-Claude-Code
  contexts.
