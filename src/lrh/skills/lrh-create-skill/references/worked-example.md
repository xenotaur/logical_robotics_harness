# Worked Example: new-scenario (prosoc project)

This document annotates the `new-scenario` skill from the prosoc social
navigation project as a reference implementation of the LRH skill pattern.
The skill lives at `.claude/skills/new-scenario/SKILL.md` in the prosoc
repository. Key excerpts are reproduced here with annotations.

---

## Frontmatter

```yaml
---
name: new-scenario
description: >
  Draft a new prosoc social navigation scenario card from a paper or description.
  Use this skill whenever the user asks to implement, add, create, author, or draft
  a social navigation scenario — especially when they name a scenario (e.g. "blind
  corner", "entering room", "following", "crowd navigation"), reference the P&G paper,
  or provide a new paper and ask for a scenario from it. Produces a DRAFTED scenario.md
  and scenario.yml under prosoc/scenarios/<name>/. Also use when the user asks to
  "fill in" missing scenarios or "implement scenarios from the paper".
---
```

**Annotations:**

- **No `disable-model-invocation`** — this is a domain-specific skill.
  Auto-triggering on scenario keywords is desirable. Contrast with
  `lrh-create-skill`, where `disable-model-invocation: true` is required because
  the skill writes files and should only run on explicit user intent.

- **Specific trigger phrases** in the description ("implement", "add",
  "create", "draft", named scenarios, "fill in", "implement scenarios from
  the paper"). Being specific reduces false positives.

- **Output described in the description** ("Produces a DRAFTED scenario.md
  and scenario.yml"). This helps Claude confirm the skill is the right tool
  before invoking it.

---

## Reference Knowledge section

```markdown
## Reference Knowledge

Load these before generating the scenario card:

1. **`references/pg_scenarios.md`** — Table 3 data for all 18 P&G scenarios,
   plus notes on which are already implemented. Always read this first to
   check if the scenario is already implemented and to get canonical metadata.

2. **`references/principles.md`** — The P1–P8 principle definitions and
   common metric IDs. Read this to correctly populate `relevant_principles`
   and `scenario_usage_guide`.

3. **`references/schema_guide.md`** — Field-by-field guidance for the
   scenario schema. Read this to understand what goes in each YAML field
   and what to leave blank.
```

**Annotations:**

- **Three reference files**, each with a clear purpose statement. This is
  the right number for a skill of this complexity. More than five reference
  files suggests the skill is too broad.

- **"Always read this first"** on the first file — explicit load ordering
  when order matters.

- **Each file is described by what it enables**, not just what it contains.
  "Read this to correctly populate `relevant_principles`" is more useful
  than "Contains principles data."

---

## Execution Steps

```markdown
### 1. Check for existing implementation

List `prosoc/scenarios/` and check whether a directory for this scenario
already exists. If it does, report this to the user and ask whether to
overwrite or extend. Do not silently overwrite existing work.
```

**Annotation:** The first step is always a guard check. For `new-scenario`
it checks the scenarios directory. For `lrh-create-skill` it checks
`.claude/skills/<name>/`. This prevents accidental overwrites.

```markdown
### 3. Extract scenario metadata

Map the source material to these fields (refer to `references/schema_guide.md`):

- scenario name, id (snake_case_01), summary
- scientific_purpose, geometric_layout
...

**Leave fields blank rather than guessing.** A sparse but accurate card is
better than a complete but fabricated one.
```

**Annotation:** "Leave fields blank rather than guessing" is the key
conservative discipline for LRH skills. Apply this principle broadly: when
context is insufficient, prefer explicit gaps over invented content.

```markdown
### 6. Run the distiller

After writing the file, run:

    cd prosoc && python -m prosoc.scenarios.distill

If the distiller reports a schema validation error, fix the YAML before
reporting completion.
```

**Annotation:** Step 6 is the validation step. For `new-scenario` it runs
a domain-specific distiller. For LRH skills that produce control-plane
artifacts, the equivalent step is `lrh validate`. Always include a
validation step that produces machine-readable evidence.

---

## Quality Checklist

```markdown
## Quality Checklist

Before reporting completion, verify:

- [ ] The scenario directory exists and contains both `scenario.md` and `scenario.yml`
- [ ] The STATUS block is present and says DRAFTED
- [ ] The fenced YAML block is valid and passes the distiller
- [ ] `relevant_principles` contains only P1–P8 identifiers
- [ ] `expected_behaviors` is flexible, not over-specified
- [ ] The Scenario Overview is readable without the YAML
- [ ] The source is cited in the STATUS block
```

**Annotation:** The checklist is concrete and verifiable, not vague. Each
item has a clear pass/fail condition. Avoid items like "quality is good" or
"the output looks right" — these are not checkable.

---

## What This Skill Does Not Do

```markdown
## What This Skill Does Not Do

- Does not promote scenarios to EDITED or AUDITED (human responsibility)
- Does not modify `schema.json`, the template, or the distiller
- Does not decide whether a scenario is redundant — flags it and asks
- Does not invent scenarios without a source
- Does not guarantee correctness of scientific or normative claims — that
  is what the AUDITED stage is for
```

**Annotation:** Each non-goal is stated as a negative imperative. The
section prevents scope creep during execution — both by the model and by
users who might try to extend the skill's scope mid-run.

---

## Key design contrasts: new-scenario vs. lrh-create-skill

| Aspect | new-scenario | create-skill |
|---|---|---|
| `disable-model-invocation` | absent (auto-triggers) | `true` (explicit only) |
| Validation step | domain distiller | frontmatter checklist |
| Confirm-before-write gate | no (domain skill, lower risk) | yes (mandatory LRH gate) |
| Target audience | prosoc contributors | LRH project developers |
| Output | `scenario.md` + `scenario.yml` | `SKILL.md` + `references/` + `CLAUDE.md` entry |

The confirm-before-write gate in `lrh-create-skill` is the primary LRH addition.
`new-scenario` omits it because the risk of a bad scenario draft is low
(it is marked DRAFTED and requires human promotion). `lrh-create-skill` includes
it because writing a poorly-scoped skill to disk has higher correction cost.
