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

## Existing guides awaiting placement

This PR establishes the destination structure; it does not migrate all existing content. Until follow-up PRs move or split them, these existing guides remain in place:

- [Release runbook](release.md) — maintainer release, TestPyPI, PyPI, and tag-push validation guidance.
- [Project setup playbooks](project-setup/README.md) — reusable setup and hardening guidance for heterogeneous project repositories.

Future content migration should prefer link-only compatibility updates and small, reviewable moves over broad rewrites.
