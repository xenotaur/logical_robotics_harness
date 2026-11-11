# Diataxis Classification Criteria

Reference material for classifying documentation against the Diataxis
four-quadrant framework. Apply at Step 5 of `/lrh-doc-organize` when
evaluating whether candidate scope items respect Diataxis quadrant boundaries.

Source: https://diataxis.fr/ (Daniele Procida)

<!-- Template counterpart: src/lrh/assist/templates/request/organize_docs.md -->

---

## The Four Quadrants

Diataxis organizes documentation along two axes:

- **Action ↔ Cognition**: does the content support doing or understanding?
- **Acquisition ↔ Application**: is the user learning something new or
  applying existing knowledge?

This yields four distinct modes:

```
                  Action
                    │
       Tutorial     │     How-to
    (acquisition)   │   (application)
─────────────────── ┼ ───────────────────
     Explanation    │     Reference
    (acquisition)   │   (application)
                    │
                 Cognition
```

---

## Quadrant Definitions

### Tutorial

**Purpose:** Learning-oriented. Guides a newcomer through a complete, working
exercise. The outcome is that the learner has *done something* and gained
confidence.

**Characteristics:**
- Written in imperative mood ("create", "run", "type")
- Step-by-step, concrete, and reproducible
- Assumes no prior knowledge beyond prerequisites stated at the top
- Reaches a working outcome by the end
- Does not explain *why* at length — that belongs in Explanation

**Examples:** Getting-started guides, "Your first X" walkthroughs, quickstarts
that produce a real running result.

**Classification question:** "Does this help a complete beginner get started
by doing something, step by step, with a concrete result?"

---

### How-to Guide

**Purpose:** Problem-oriented. Gives a recipe for achieving a specific goal.
Assumes the reader already has baseline knowledge and wants to accomplish
something practical.

**Characteristics:**
- Title is task-focused ("How to configure X", "Setting up Y for Z")
- Assumes prerequisite knowledge; does not explain basics
- Goal-oriented: each step serves the goal directly
- May omit explanation of *why* — links to Explanation instead
- Scope is narrower and more specific than a tutorial

**Examples:** How to deploy to production, how to configure TLS, how to
migrate from v1 to v2, how to set up linting.

**Classification question:** "Does this help a practitioner who already knows
the basics solve a specific, named problem?"

---

### Reference

**Purpose:** Information-oriented. Describes the machinery accurately and
completely. Corresponds to the code.

**Characteristics:**
- Consistent, regular structure (API docs, config options, CLI flags, schemas)
- Present tense, declarative ("The `timeout` field specifies…")
- Does not explain motivation or teach — just describes
- Must stay accurate as code changes
- Dense; users scan it, they do not read it linearly

**Examples:** API documentation, CLI `--help` output, config file schema,
list of environment variables, class/method docstrings.

**Classification question:** "Does this accurately describe what something is
or does, so a practitioner can look up a specific fact?"

---

### Explanation

**Purpose:** Understanding-oriented. Illuminates a concept, decision, or
design rationale. Helps readers build a mental model.

**Characteristics:**
- Discursive, essay-like — not step-by-step
- Discusses *why*, not *how*
- May contrast alternatives or discuss trade-offs
- Not action-oriented; no instructions
- Background reading, not a task reference

**Examples:** Architecture overview, rationale for a design decision,
explanation of a core concept, "how does X work under the hood".

**Classification question:** "Does this help readers understand a concept,
decision, or design rather than how to use or do something?"

---

## Mixed and Meta Content

### Mixed (flag for splitting)

A file that serves multiple quadrants simultaneously is a sign of
documentation drift. Common cases:

- **README that does everything** — typically mixes tutorial (quickstart),
  how-to (common tasks), reference (config table), and explanation (rationale).
  Flag each section with its quadrant; recommend splitting.
- **CONTRIBUTING.md** — usually mixes how-to (how to submit a PR) with
  reference (code style rules) and sometimes explanation (project philosophy).
- **Inline code comments** — short-form reference and explanation; not
  standalone docs.

### Meta (project management content)

Some files are not documentation in the Diataxis sense — they manage the
project rather than explain the software:

- `CHANGELOG.md` — change log (meta/reference hybrid)
- `AGENTS.md`, `STYLE.md`, `PROMPTS.md` — contributor guidelines (meta)
- `SECURITY.md` — security disclosure policy (meta/how-to)
- `CODE_OF_CONDUCT.md` — community governance (meta)
- LRH `project/` files — control-plane artifacts (meta)

Classify these as **Meta** and note them in the inventory; do not try to
force them into the four quadrants.

---

## Classification Heuristics

When classification is unclear, apply these questions in order:

1. **Who is this for?** A complete beginner → Tutorial. A practitioner →
   How-to or Reference. Someone building understanding → Explanation.

2. **What action does the reader take?** They follow steps → Tutorial or
   How-to. They look up a fact → Reference. They read to understand → Explanation.

3. **Does it teach or describe?** Teaching (even if advanced) → Tutorial or
   How-to. Accurate description → Reference. Conceptual illumination → Explanation.

4. **Is there a concrete outcome?** A working result → Tutorial. A completed
   task → How-to. A lookup answer → Reference. A mental model → Explanation.

5. **Beginner or expert?** No assumed knowledge → Tutorial. Assumed knowledge,
   specific goal → How-to. Assumed knowledge, lookup → Reference. Any level,
   conceptual → Explanation.

When a file clearly spans multiple quadrants, classify it as **Mixed** and
identify the dominant quadrant and secondary quadrants separately.
