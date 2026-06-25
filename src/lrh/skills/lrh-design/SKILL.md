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

### Step 4 — Offer follow-on

After delivering the design, offer:

- To capture the design as an LRH work item via `/lrh-work-item` (include a
  suggested work item title if the design is well-scoped).
- To produce a proposal document in `project/design/proposals/` if the idea
  is significant enough to warrant one.

Do not automatically do either — always offer and wait for the user to decide.

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
- [ ] Follow-on offer (work item or proposal) was made

---

## What This Skill Does Not Do

- Does not implement — use `/lrh-work-item` + `/lrh-implement` for that.
- Does not automatically create work items — offers and waits for user decision.
- Does not write files — the design lives in the conversation unless captured.
- Does not run validation, tests, or code analysis — those belong in
  implementation skills.
- Does not replace the Taurcode `:design` Espanso snippet for non-Claude-Code
  contexts.
