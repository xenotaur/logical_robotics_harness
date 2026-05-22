# LRH Human-Facing Documentation

This directory is the landing page for human-facing Logical Robotics Harness (LRH) documentation. It is for maintainers and users who need to learn LRH, operate it in real repositories, look up stable behavior, or understand design rationale.

The authoritative LRH project control plane remains in [`../project/`](../project/). Documentation here should teach, explain, and guide. When project state, active plans, design authority, or evidence matters, link to the relevant artifact under `project/` instead of duplicating it here.

## Documentation sections

LRH uses a lightweight, GitHub-rendered, Diátaxis-inspired structure:

- [Tutorials](tutorials/README.md) — guided learning paths that teach LRH through complete examples.
- [How-to guides](how-to/README.md) — task-specific operational instructions for real work.
- [Reference](reference/README.md) — exact commands, schemas, file formats, and stable behavior.
- [Explanations](explanations/README.md) — rationale, concepts, and design background.
- [Conversations](conversations/README.md) — user-facing workflows for conversation capture, import, and promotion into durable LRH artifacts.

Use [Documentation structure](reference/documentation-structure.md) when deciding where future documentation belongs.

## Current how-to guides

- [Validate a project control directory](how-to/validate-a-project.md) — run current `lrh validate` checks against an LRH `project/` directory.
- [Generate a context snapshot](how-to/generate-a-snapshot.md) — render current `lrh snapshot` context packets.
- [Survey a source tree](how-to/survey-a-source-tree.md) — inventory a Python source tree with `lrh survey`.
- [Use request templates](how-to/use-request-templates.md) — discover and render current `lrh request` prompts and template diagnostics.
- [Manage the work-item lifecycle](how-to/manage-work-item-lifecycle.md) — audit, ready, prompt, execute, and evidence-close work items conservatively.
- [Register a project with an LRH meta workspace](how-to/register-a-project-with-meta.md) — initialize meta state and register project records.
- [Inspect workspace state](how-to/inspect-workspace-state.md) — inspect active meta workspace paths and registered projects.
- [Use the developer sandbox](how-to/use-the-developer-sandbox.md) — run LRH commands against isolated developer state.
- [How to run a release](how-to/run-a-release.md) — maintainer release, TestPyPI, PyPI, and tag-push validation guidance.
- [Project setup playbooks](how-to/project-setup/README.md) — reusable setup and hardening guidance for heterogeneous project repositories.

## Current CLI reference

- [`lrh validate`](reference/cli/validate.md)
- [`lrh snapshot`](reference/cli/snapshot.md)
- [`lrh survey`](reference/cli/survey.md)
- [`lrh request`](reference/cli/request.md)
- [`lrh work-items`](reference/cli/work-items.md)
- [`lrh meta`](reference/cli/meta.md)
- [`lrh conversation`](reference/cli/conversation.md)
- [`lrh serve`](reference/cli/serve.md)
- Prompt workflow commands (`lrh prompt`, `lrh match`, `lrh search`) are currently documented in [Prompt workflow](tutorials/first-prompt-driven-change.md) and [PROMPTS.md](../PROMPTS.md).

Future content migration should prefer link-only compatibility updates and small, reviewable moves over broad rewrites.
