# LRH Project-Local Skills proposal set

This proposal set records the proposed design for first-class Claude Code
project-local skill support in LRH: the `create-skill` skill, the
`src/lrh/skills/` distributable skill directory, and the `lrh setup`
per-machine installation command.

## Status

`adopted` / `partial`

`lrh-create-skill` and `lrh-work-item` are shipped. `lrh setup` and
`lrh-implement` remain to be implemented.

## Documents

1. [`00_proposal.md`](00_proposal.md)
   — umbrella proposal covering motivation, problem statement, the three
   coupled component designs (`create-skill`, `src/lrh/skills/`, `lrh setup`),
   design choice rationale, staged implementation plan, non-goals, risks,
   acceptance criteria, and work item seeds.

2. [`01_lrh_implement_skill.md`](01_lrh_implement_skill.md)
   — sub-proposal for `/lrh-implement`, a Claude Code skill encoding the
   instruction and execution phases of the three-phase execution session
   model. Covers lifecycle placement, 10-step execution design, three
   reference files, key design decisions, and acceptance criteria.

## Reading order

1. `README.md` (this file)
2. `00_proposal.md`
3. `01_lrh_implement_skill.md`

## Canonical-document touchpoints

If adopted, this proposal would inform future updates to:

- `project/design/architecture.md` — skill distribution as a new harness
  distribution surface alongside `src/lrh/assist/templates/`
- `project/design/repository_spec.md` — `src/lrh/skills/` and
  `.claude/skills/` as defined repository locations
- `docs/how-to/` — a future how-to guide for adding and using LRH skills
- `pyproject.toml` — package data declaration for `src/lrh/skills/`
