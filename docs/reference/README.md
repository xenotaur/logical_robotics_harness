# Reference

Reference documentation records exact, stable LRH behavior that readers need to look up.

## What belongs here

- CLI command behavior, options, inputs, outputs, and exit expectations.
- Schemas, frontmatter fields, file formats, and validation rules.
- Stable repository conventions and documentation placement rules.
- Precise compatibility notes that should be maintained as behavior changes.

## What does not belong here

- Guided lessons that teach by walking through an example.
- Task recipes that combine multiple reference facts into an operational procedure.
- Design rationale without normative behavior.
- Duplicated project status, active work, or evidence from [`../../project/`](../../project/).

## How to decide whether to add content here

Add content here when the reader needs to look up exact behavior and expects the answer to stay synchronized with implementation or accepted project conventions. If content becomes a task procedure, put it in [how-to guides](../how-to/README.md) and link back to reference facts. If it becomes conceptual background, put it in [explanations](../explanations/README.md).

## Reference subsections

- [CLI reference](cli/README.md) — command-oriented reference material.
- [Schema reference](schemas/README.md) — project-control and file-format reference material.
- [Documentation structure](documentation-structure.md) — placement guide for future human-facing docs.

## Related operational guides

- [How to run a release](../how-to/run-a-release.md) contains command and release-process details for maintainers.
