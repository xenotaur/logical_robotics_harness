# LRH Project-Local Skills proposal set

This proposal set records the proposed design for first-class Claude Code
project-local skill support in LRH: the `create-skill` skill, the
`src/lrh/skills/` distributable skill directory, and the `lrh setup`
per-machine installation command.

## Status

`proposed` / `not_started`

This is a documentation-only design proposal. It does not implement any
CLI command, packaging change, or skill file.

## Documents

1. [`00_proposal.md`](00_proposal.md)
   — umbrella proposal covering motivation, problem statement, the three
   coupled component designs, design choice rationale, a staged
   implementation plan, non-goals, risks, acceptance criteria, and work
   item seeds.

## Reading order

1. `README.md` (this file)
2. `00_proposal.md`

## Canonical-document touchpoints

If adopted, this proposal would inform future updates to:

- `project/design/architecture.md` — skill distribution as a new harness
  distribution surface alongside `src/lrh/assist/templates/`
- `project/design/repository_spec.md` — `src/lrh/skills/` and
  `.claude/skills/` as defined repository locations
- `docs/how-to/` — a future how-to guide for adding and using LRH skills
- `pyproject.toml` — package data declaration for `src/lrh/skills/`
