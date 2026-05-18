# CI Feasibility Assessment Request (Read-Only)

Assess whether this repository is a good candidate for CI work using the LRH CI setup and debugging playbook. In an LRH source checkout the full playbook lives at `docs/how-to/project-setup/ci.md`; this generated request also includes the execution-critical playbook guidance below so it remains usable from an installed LRH package or in target repositories that do not contain that path.

This is an assessment-only request.

- Do NOT edit files.
- Do NOT generate a patch.
- Do NOT open a PR.
- Do NOT propose speculative implementation details not grounded in repository evidence.
- Do NOT assume one universal workflow template before discovering project family, commands, and existing CI state.

==================================================
INPUT CONTEXT
==================================================

Optional background:
{{BACKGROUND_CONTEXT}}

==================================================
OBJECTIVE
==================================================

Inspect the repository and produce a conservative CI migration feasibility assessment.

The assessment must apply the CI playbook guidance in this request, use `docs/how-to/project-setup/ci.md` as the fuller source when that file is available, determine the project family before recommending workflows, discover canonical repository commands before proposing validation steps, and decide whether CI migration should proceed, adapt to repository conventions, or abort. Do not fail solely because the target repository lacks `docs/how-to/project-setup/ci.md`.


==================================================
PACKAGED CI PLAYBOOK SUMMARY
==================================================

Use this summary as the portable CI playbook when `docs/how-to/project-setup/ci.md` is not available in the target repository. If that file is available, read it as the fuller source and keep this summary as the execution-critical checklist.

- Discover the project family first: Python package/tool, Python scripts/tools collection, Unix command/tool repository, Rust/Cargo, Rust/WASM/WebGPU, JavaScript/TypeScript, game/simulation, documentation/static site, mixed repository, or other.
- Inventory existing commands and policy files before proposing CI: README/docs, `AGENTS.md`, `STYLE.md`, `PROMPTS.md`, `REVIEWS.md`, `scripts/`, `bin/`, `tools/`, `Makefile`, `justfile`, language package metadata, lockfiles, and existing workflow YAML.
- Prefer repository-owned wrapper commands in CI. For LRH-like repositories, the normal validation sequence is `scripts/version tools`, `scripts/check-workflows`, `scripts/format --check --diff`, `scripts/lint`, and `scripts/test`.
- Keep setup/bootstrap separate from validation. Setup may install dependencies or use caches/network; validation should be repeatable and evidence-producing. In Codex Cloud, run `scripts/develop` during environment setup/bootstrap, not routine task-phase validation.
- Make tool/runtime versions visible before validation. If formatter/linter/test tool versions are missing or mismatched, report a setup/cache issue before debugging validation failures.
- Design workflows so local and CI commands map clearly, use readable job/step names, and keep heavyweight smoke, packaging, release, GPU, browser, or simulation checks separate when practical.
- When workflows are touched, run `scripts/check-workflows` or the closest project-approved workflow YAML check if available.
- Debug with evidence: collect commit, working tree status, tool-version output, command logs, reports, screenshots, artifacts, or review notes before saying CI is flaky, fixed, unreproducible, or a pre-existing failure.
- Treat stronger tooling such as actionlint, pre-commit, tox/nox, dev containers, or lockfile/toolchain changes as deliberate follow-ups unless the task explicitly requests them or repository evidence shows they are already canonical.
- Use reusable workflow fragments only after repository family, commands, and existing CI state are understood; do not start with a universal template for an unfamiliar repository.

==================================================
REQUIRED INSPECTION CHECKLIST
==================================================

Inspect and summarize evidence for all of the following:

1. Project family and primary language(s)
   - Identify the repository family described by the packaged CI playbook summary: Python package/tool, Python scripts/tools collection, Unix command/tool repository, Rust/Cargo, Rust/WASM/WebGPU, JavaScript/TypeScript, game/simulation, documentation/static site, mixed repository, or other.
   - Identify dominant language(s) based on repository contents.
   - Note if repository is Python-first, mixed-language, or non-Python.

2. Build/package/dependency system
   - Examples: pyproject/pip/uv/poetry/hatch/tox/nox/Makefile/npm/cargo/etc.
   - Separate setup/bootstrap commands from validation commands.

3. Existing CI/workflow baseline
   - Inspect `.github/workflows/` (or equivalent CI if present).
   - Summarize workflows and what they enforce.
   - If workflows exist, identify whether the repository has `scripts/check-workflows` or a closest project-approved workflow YAML check.

4. Test framework and test layout
   - Determine current test framework(s): unittest / pytest / others / none.
   - Summarize test folder/file patterns and maturity.

5. Formatter/linter/tooling choices
   - Examples: black, ruff, flake8, mypy, isort, prettier, eslint, cargo fmt/clippy.
   - Treat stronger tooling such as actionlint, pre-commit, tox/nox, dev containers, or lockfile changes as deliberate follow-ups unless explicitly requested by the task or already established by the repository.

6. Dependency/install instructions and canonical commands
   - Inspect repository scripts, docs, and config before proposing commands.
   - Summarize documented local setup and test commands.
   - Identify canonical commands for setup/bootstrap, tool/version reporting, workflow YAML checks, format checks, lint checks, tests, smoke checks, and coverage where present.
   - Highlight gaps that block confident CI setup.

7. Repository shape classification
   - Classify as one of:
     - importable Python package
     - Python scripts/tools collection
     - notebook-heavy project
     - mixed-language repository
     - documentation/content-only repository
     - other (explain)

8. CI suitability judgment
   - Is LRH-style Python CI appropriate as-is?
   - Would adaptation be required?
   - Would native non-Python CI be more appropriate?
   - Would the existing CI be sufficient without migration?

9. Risks and unknowns
   - Explicitly list uncertainty and evidence gaps.
   - Do not say "cannot reproduce", "pre-existing failure", "flaky", or "fixed" without concrete evidence such as commit, working tree status, tool versions, command output, logs, reports, screenshots, or review notes.

10. Recommended next step
   - Recommend proceed/adapt/abort with rationale.
   - Keep recommendations repository-specific and tied to discovered commands and existing CI state.

==================================================
STATUS VOCABULARY (REQUIRED)
==================================================

End the assessment with exactly one final status from this set:

- PROCEED_PYTHON_LRH_STYLE
- PROCEED_WITH_ADAPTATION
- ABORT_NOT_PYTHON
- ABORT_DOCS_OR_CONTENT_ONLY
- ABORT_EXISTING_CI_IS_SUFFICIENT
- ABORT_INSUFFICIENT_EVIDENCE

==================================================
OUTPUT FORMAT (REQUIRED)
==================================================

# CI Feasibility Assessment

## Playbook Reference
- CI playbook: packaged summary in this generated request; fuller source `docs/how-to/project-setup/ci.md` when available

## Repository Signals
- Project family:
- Primary language(s):
- Package/build system:
- Existing workflows:
- Workflow YAML check:
- Test framework/layout:
- Formatter/linter choices:
- Setup/bootstrap instructions:
- Canonical validation commands:
- Repository shape classification:

## Suitability Analysis
- LRH-style Python CI fit:
- Native/non-Python CI fit:
- Existing CI sufficiency:
- Risks:
- Unknowns:

## Evidence Notes
- Commands inspected:
- Files inspected:
- Evidence gaps:

## Recommendation
- Next step recommendation:

If final status is `PROCEED_PYTHON_LRH_STYLE` or `PROCEED_WITH_ADAPTATION`, also include:
- Minimal likely implementation slice (scripts/workflows/docs):
- Expected local command entry points to add or align:
- Setup/bootstrap vs validation boundary:
- Workflow YAML validation command (`scripts/check-workflows` or closest approved equivalent):

## Final Status
`<ONE_REQUIRED_STATUS_TOKEN>`

==================================================
DECISION RULES
==================================================

- Follow the packaged CI playbook summary in this request, and read `docs/how-to/project-setup/ci.md` as the fuller source when available.
- Be conservative.
- Prefer abort status over speculative migration when evidence is weak.
- Do not recommend blindly copying LRH CI into non-Python, mixed-stack, or weak-fit repositories.
- Do not recommend actionlint, pre-commit, tox/nox, dev containers, or lockfile/toolchain changes unless the task explicitly calls for them or repository evidence shows they are already canonical.
- If the repository already has sufficient CI for its stack and maturity, prefer `ABORT_EXISTING_CI_IS_SUFFICIENT`.
