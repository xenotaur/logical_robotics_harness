# How-To Guides

How-to guides give task-specific operational instructions for people applying LRH to real work.

## What belongs here

- Recipes for accomplishing a specific maintenance, validation, setup, or workflow task.
- Step-by-step operational guidance that assumes the reader has a goal already.
- Troubleshooting procedures with evidence to collect and decisions to make.
- Reusable playbooks that apply across LRH and downstream project repositories.

## What does not belong here

- First-time guided lessons whose purpose is teaching concepts from scratch.
- Exhaustive command, schema, or format definitions.
- Historical rationale or design discussion that is not task-oriented.
- Duplicated current project state from [`../../project/`](../../project/).

## How to decide whether to add content here

Add content here when the title can naturally start with “How to ...” and the reader should finish with a completed task. If the document mainly teaches a complete learning path, use [tutorials](../tutorials/README.md). If it defines exact stable behavior, use [reference](../reference/README.md). If it explains rationale, use [explanations](../explanations/README.md).

## Guides

- [Validate a project control directory](validate-a-project.md) — run current `lrh validate` checks against an LRH `project/` directory.
- [Generate a context snapshot](generate-a-snapshot.md) — render current `lrh snapshot` context packets.
- [Survey a source tree](survey-a-source-tree.md) — inventory a Python source tree with `lrh survey`.
- [Use request templates](use-request-templates.md) — discover and render current `lrh request` prompts and template diagnostics.
- [Manage the work-item lifecycle](manage-work-item-lifecycle.md) — audit, ready, prompt, execute, and evidence-close work items conservatively.
- [Register a project with an LRH meta workspace](register-a-project-with-meta.md) — initialize meta state and register project records.
- [Inspect workspace state](inspect-workspace-state.md) — inspect active meta workspace paths and registered projects.
- [Use the developer sandbox](use-the-developer-sandbox.md) — run LRH commands against isolated developer state.
- [How to run a release](run-a-release.md) — validate, tag, smoke-test, and publish LRH releases.
- [Project setup playbooks](project-setup/README.md) — reusable setup and hardening guidance for heterogeneous project repositories.
