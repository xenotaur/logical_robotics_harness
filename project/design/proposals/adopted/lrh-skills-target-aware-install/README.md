# Target-Aware `lrh skills install` — Proposal Set

## Status summary

- `00_proposal.md` — umbrella proposal. Status: `proposed` / `not_started`
  (documentation-only; no CLI, installer, or renderer code changes in this PR)

## What this proposal set covers

This proposal set extends `lrh skills install` from a Claude-only installer
into a target-aware Agent Skills installer, treating `.claude/skills/` and
`.agents/skills/` (Codex) as parallel first-class local install targets
rendered from a shared canonical skill source, with ChatGPT Skills deferred
to a later, separately-researched export path.

The umbrella proposal defines:

1. A four-dimension resolution model (`source` / `scope` / `target` / `mode`)
   for every install operation.
2. The canonical-source-vs-installed-copy separation, generalizing the
   existing `lrh request` template-rendering precedent to skill installation.
3. The corrected Codex metadata mechanism — `agents/openai.yaml` as a sibling
   file, including translation of `disable-model-invocation` to
   `policy.allow_implicit_invocation` rather than silent field-stripping.
4. The real cost of "copy where safe" given current Claude Code-specific
   coupling in shipped skill body prose, and how that cost is scoped as
   explicit follow-on work rather than left implicit.
5. A staged implementation plan, reconciling a scope mismatch in the source
   design between its staged plan and its recommended first work item.

## Canonical documents touched

- `src/lrh/skills/installer.py` — current single-target installer this
  proposal extends.
- `docs/reference/cli/request.md` — prior art for the canonical-source →
  per-target-rendered-output pattern this proposal generalizes.
- `project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`
  — prior proposal establishing `src/lrh/skills/` and the current installer.

No canonical document (`design.md`, `architecture.md`,
`repository_spec.md`) is edited by this proposal; adoption may later fold
its decisions into one of those documents.
