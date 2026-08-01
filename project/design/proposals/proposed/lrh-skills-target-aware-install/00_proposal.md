---
id: PROP-LRH-SKILLS-TARGET-AWARE-INSTALL
type: design_proposal
title: Target-Aware `lrh skills install` — Codex as a First-Class Local Target
status: proposed
created_on: 2026-07-31
updated_on: 2026-07-31
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
  - src/lrh/skills/installer.py
  - docs/how-to/keep-skills-up-to-date.md
---

# Target-Aware `lrh skills install` — Codex as a First-Class Local Target

## Summary

This proposal extends `lrh skills install` from a Claude-only installer into a target-aware Agent Skills installer, treating `.claude/skills/` and `.agents/skills/` (Codex) as parallel first-class local install targets rendered from a shared canonical skill source, with ChatGPT Skills deferred to a later, separately-researched export path rather than a local install target.

## Background / Motivation

`src/lrh/skills/installer.py` currently copies package-bundled skills to exactly one destination shape: `~/.claude/skills/` or, with `--local`, `./.claude/skills/` (`install_skills()`, `src/lrh/skills/installer.py:183-216`). There is no `--target` flag anywhere in the CLI (`src/lrh/cli/main.py:130-160`) — `install_skills()` accepts only `skills_dir`, `dry_run`, and `force`.

Two independent platform developments make this single-target design a growing liability rather than a stable simplification:

1. **Codex CLI has its own, real, filesystem-based Agent Skills discovery mechanism.** Codex scans `.agents/skills/` from the current working directory up through the repository root, then `$HOME/.agents/skills/`, then admin/system locations, using the same `SKILL.md` file convention Claude Code uses ([Codex Agent Skills — Axiom Studio](https://axiomstudio.ai/learn/codex-agent-skills); confirmed independently via an OpenAI community report of a regression in exactly this discovery path: [Local skills in ~/.agents/skills are no longer discovered — OpenAI Developer Community](https://community.openai.com/t/local-skills-in-agents-skills-are-no-longer-discovered-in-new-codex-sessions/1379522)).
2. **ChatGPT Skills is a real, GA'd feature** (rolled out 2026-07-09 for Business/Enterprise/Edu accounts), using the same `SKILL.md` + YAML-frontmatter format and explicitly marketed as portable across tools ([Skills in ChatGPT — OpenAI Help Center](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)).

The coupling this proposal addresses is not hypothetical — it is already present at scale in this repository. Of the 14 skills currently shipped under `src/lrh/skills/`, 11 carry `disable-model-invocation: true` in frontmatter (e.g. `src/lrh/skills/lrh-closeout/SKILL.md:10`; the remaining three — `lrh-proposal`, `lrh-work-item`, `lrh-workstream` — use `when_to_use` instead, since they're designed to be composable from orchestrating skills), a field confirmed to be Claude Code–specific, controlling autonomous vs. slash-only invocation ([Extend Claude with skills — Claude Code Docs](https://code.claude.com/docs/en/skills)); Codex's own metadata extension point is a **separate sibling file**, `agents/openai.yaml`, which — as Decision 2 details — does carry a real equivalent for this specific field. Beyond metadata, all 14 skills reference "Claude Code" and/or `/lrh-*` slash-command invocation directly in `SKILL.md` **body prose**, not just frontmatter (e.g. `src/lrh/skills/lrh-land/SKILL.md`).

LRH already has working precedent for the canonical-source → per-target-rendered-output architecture this proposal needs: the `lrh request` template system renders the same underlying content differently per `--target-agent` (default `"Codex Cloud"`, `docs/reference/cli/request.md:114`). This proposal applies the same separation-of-concerns pattern to skill installation rather than prompt rendering.

## Prior Art Check

### Duplication search
- In-repo: No existing implementation found. `grep -rlE "target-aware|multi-target|codex.*skill|agents/skills"` (extended regex, so `|` is alternation, not a literal character) across `src/`, `project/design/proposals/`, `.claude/skills/` returned no matches at the time of this search, prior to this proposal's own file existing.
- Sibling repos: None identified (not asked interactively this session; no sibling repo previously named for skill distribution).
- External libraries: None identified — Codex's and ChatGPT's own skill directories are platform conventions to render for, not libraries to adopt.
- Recommendation: Proceed.

### Demand search
- Work items: None found matching this capability (`WI-TEMPLATE-AUDIT-WORK-ITEMS` matched the grep on an unrelated term but does not request this).
- Proposals: None found in `project/design/proposals/proposed/`.
- Backlog: No matching entries in `project/design/backlog.md` (Codex/ChatGPT mentions there are all incidental references to Codex-as-reviewer, not skill-target requests).
- Recommendation: No action.

## Design Decisions

### Decision 1: Conceptual model — source / scope / target / mode

Adopt a four-dimension resolution model for every install operation:

```
source:  lrh-package | current-repo | explicit-path
scope:   user | project
target:  claude | codex | all
mode:    install | dry-run | force | diff | check
```

`.claude/skills/` and `.agents/skills/` are **install targets, not canonical sources of truth** — the canonical skill tree (`src/lrh/skills/` for LRH itself, or a configured repo-local path such as `src/<package>/skills/`) is authoritative; installed target directories are generated/synchronized copies. This mirrors the `lrh request` system's existing template → rendered-prompt separation and is a natural generalization, not a new architectural style for this codebase.

Target directories:

| Target | Scope | Path |
|---|---|---|
| Claude | user | `~/.claude/skills/` |
| Claude | project | `./.claude/skills/` |
| Codex | user | `~/.agents/skills/` |
| Codex | project | `./.agents/skills/` |

**Chosen over:** a design where `.claude/skills/`/`.agents/skills/` are themselves authoritative (rejected — makes multi-target support impossible without hand-maintained divergent trees) or a design that bakes Claude-only assumptions permanently into `install_skills()` (rejected — this is the status quo the proposal exists to fix).

### Decision 2: Codex metadata mechanism — correct the sibling-file target

*(Refinement — corrects the source design session's proposed schema.)*

The source design session proposed a nested `metadata.lrh.targets.codex.*` key inside `SKILL.md` frontmatter for Codex-specific hints (invocation examples, tool dependencies). This does not match Codex's actual documented extension point: Codex reads **a separate sibling file**, `agents/openai.yaml`, alongside `SKILL.md`, for UI metadata, invocation policy, and MCP/tool dependencies — not a nested frontmatter block.

A renderer emitting the originally-proposed nested key would produce output Codex silently ignores — harmless, but non-functional, and the kind of mismatch that's expensive to discover only after implementation.

**Chosen:** the Codex render adapter (`CodexSkillRenderer`) targets the real mechanism — preserving or emitting `agents/openai.yaml` where a canonical skill supplies Codex-specific hints. Critically, `disable-model-invocation` is **not** simply stripped: `agents/openai.yaml` has a real equivalent, `policy.allow_implicit_invocation` (default `true`), which controls the same explicit-vs-automatic invocation distinction. Stripping `disable-model-invocation: true` without emitting `policy.allow_implicit_invocation: false` would silently change behavior for the 11 of 14 shipped skills that set it — Codex would default to implicit invocation and could inject a formerly manual-only skill (e.g. `lrh-land`, `lrh-implement`) into model context. The renderer must translate this field, not discard it. `argument-hint`, by contrast, has no documented Codex equivalent (it is Claude Code's slash-command UI hint) and is stripped rather than translated.

### Decision 3: Canonical source vs. installed copies

Canonical skill source directories (`src/lrh/skills/`, or a repo-configured path) are the authoritative editable versions. Installed target directories (`.claude/skills/`, `.agents/skills/`, and their user-global equivalents) are generated or synchronized copies, carrying a generated-notice comment where the target platform doesn't discourage it:

```
<!-- Generated by lrh skills install from src/lrh/skills/lrh-work-item. Do not
edit this copy directly unless intentionally customizing the installed target. -->
```

A target copy with local modifications is skipped by default (reported as a conflict, diffable with `--diff`), never silently overwritten — extending, not replacing, `_skill_differs_from_package()` (`src/lrh/skills/installer.py:94-105`) and the `SkillStatus.USER_MODIFIED` path (`installer.py:203-212`) that already exist and are already tested.

### Decision 4: Copy versus render — and the real cost of "start with copy"

*(Refinement — names a cost the source design left implicit.)*

The source design proposes starting with **direct copy** where a canonical skill is "fully compatible with the target," evolving to per-target **rendering** (stripping unsupported metadata, adding target-specific hints) only where needed, to avoid hand-maintained divergent skill trees.

That framing understates current coupling. Compatibility is not only a frontmatter question — it's a content question. Every one of the 14 shipped skills references "Claude Code" and/or `/lrh-*` slash-command invocation directly in `SKILL.md` body prose (confirmed by grep, not just frontmatter inspection). A direct copy of any current skill to `.agents/skills/` ships Claude-flavored instructional text unadapted into Codex's discovery path — Codex would technically discover the skill, but its body would tell the agent to behave like Claude Code.

This proposal names that cost explicitly rather than leaving it implicit in "copy where safe":

- **Interim state (accepted for the first implementation slice):** Codex-target copies of existing skills carry a known caveat — they are direct copies, may reference Claude Code/slash-command framing in body prose, and are provided for Codex's benefit on a best-effort basis pending body-prose neutralization.
- **Follow-on cost (explicitly scoped, not implicit):** rewriting skill bodies to be agent-neutral (referring to "the assigned agent" rather than "Claude Code," and to "this skill's invocation" rather than hardcoded `/lrh-*` slash syntax) is real authoring work across 14 files, tracked as its own follow-on work item rather than assumed to happen for free during the renderer build.

**Chosen:** support both copy and render from the start (architecturally), but explicitly scope the first implementation slice to copy-with-caveat for Codex, and file body-prose neutralization as separate follow-on work rather than a rendering-adapter responsibility.

### Decision 5: Repository configuration — parser choice is an implementation constraint

*(Refinement — flags a risk the source design didn't anticipate.)*

The source design proposes an optional `project/agent_skills.yaml` for repo-local source/target/scope/install-policy configuration, with CLI flags overriding config overriding conventional defaults. The shape (schema_version, sources[], targets[], scope, install.overwrite policy) is sound and is adopted as-is.

However, this repository has a **documented prior bug** in its home-grown YAML-subset parser: `_parse_simple_yaml` (`src/lrh/control/validator.py:568`) strips quotes from scalar values but not from list elements, which previously caused a real path/scheme-validation defect on list-valued frontmatter. `agent_skills.yaml`'s `sources:`/`targets:` fields are list-valued, which is exactly the shape that parser class has failed on before.

**Chosen:** whichever work item implements `agent_skills.yaml` parsing must either (a) use a real YAML library (e.g. `PyYAML`, already a reasonable dependency for this purpose) rather than extending `_parse_simple_yaml`, or (b) if reusing the existing simple parser for consistency with the rest of the control plane, add an explicit regression test for quoted list-element values before the config-parsing stage is considered done. This is stated as an implementation constraint on Stage 4 (repo config), not left to be discovered during code review.

### Decision 6: Installer architecture

Introduce these internal concepts, refactoring `installer.py` around them incrementally (not as a single rewrite):

```
SkillSource     — enumerates canonical skills from package resources, filesystem paths, or repo config
SkillManifest   — parsed SKILL.md metadata (name, description, license, compatibility, metadata, source_path, files)
SkillTarget     — a concrete output destination (target_name, scope, destination_root, supports_symlinks, requires_rendering)
InstallPlan     — a deterministic plan computed before writing (source skill, target, destination, action, reason, diff summary)
InstallResult   — report emitted after execution or dry run
SkillRenderer   — per-target rendering logic (ClaudeSkillRenderer, CodexSkillRenderer; future ChatGPTSkillExporter)
SkillInstaller  — applies install plans safely: compute plan → report in dry-run → skip modified copies unless --force → write atomically where practical → report exact actions
```

This generalizes, rather than discards, the existing `SkillStatus`/`SkillResult`/`InstallReport` dataclasses (`installer.py:17-34`) — `SkillStatus` becomes `InstallPlan.action`, `SkillResult` becomes one entry in `InstallResult`.

### Decision 7: Conflict handling and safety principles carry over unchanged

The existing safety behaviors are extended to the multi-target case, not replaced:

- Symlinked skill roots are never dereferenced (`_collect_fs_files`, `installer.py:60-73`; `_collect_fs_symlinks`, `installer.py:76-91`) — this policy applies per-target.
- A target copy with local modifications is skipped by default; `--force` is required to overwrite (`installer.py:203-212`).
- `--diff` shows a unified diff for modified copies (`diff_skill()`, `installer.py:108-159`).
- No bundled scripts are executed during install, for any target.
- Skills are installed only from explicit package or repo sources — no network download-on-demand.

### Decision 8: ChatGPT — deferred pending research, not a routine future stage

*(Refinement — sharpens the source design's deferral rationale.)*

ChatGPT Skills is correctly out of scope as a **local filesystem install target** — it is a hosted, enterprise-plan feature with its own upload/registration flow, not something `.claude/skills/`-style directory placement can satisfy. The source design already deferred this correctly to a future `lrh skills export --target chatgpt`.

This proposal sharpens that deferral: because ChatGPT Skills only reached GA on 2026-07-09, its actual upload/registration API contract is not yet publicly documented in enough depth to design against. Stage 7 (`lrh skills export --target chatgpt`) should be tracked as **blocked on research**, not as a routine "next stage" that simply hasn't been reached yet — the distinction matters for sequencing: don't schedule engineering time against it until the contract is confirmed.

## Non-Goals

- Does not make `lrh request` templates the canonical source for skills — they remain separate artifact types (a request template is a prompt rendered for a particular run; a skill is a reusable operational procedure selected or invoked by an agent).
- Does not require every LRH-managed repository to adopt skills or multi-target installation.
- Does not make `.claude/skills/` or `.agents/skills/` authoritative — canonical sources remain the source of truth.
- Does not build a marketplace, registry, or plugin-distribution system.
- Does not implement ChatGPT Skills export in the first implementation slice — see Decision 8.
- Does not rewrite all 14 existing skill bodies to be agent-neutral as part of this proposal — see Decision 4; that is scoped as explicit follow-on work.
- Does not automatically rewrite `AGENTS.md` to reference installed skills — a future `lrh skills suggest-agents-rules` could propose such changes without writing them automatically.

## Implementation Plan

*(Refinement — reconciles the source design's two implementation-scope sections.)*

The source design contained two implementation-scope descriptions that didn't quite agree: a 7-stage plan (Stage 1 = docs-only "preserve and name the current surface," Stage 2 = add `--target`) and a separate "Recommended First Work Item" section that scopes straight to `--target claude|codex|all` plus both Codex paths in a single work item, skipping a standalone Stage 1 slice.

**This proposal treats the "Recommended First Work Item" scope as authoritative for the first work item.** Stage 1's "preserve and name the current surface" intent is satisfied as acceptance criteria within that same work item (documenting `lrh skills install` as the canonical interface, confirming existing Claude behavior is unchanged) rather than as a separate prior work item — there is no independent value in a documentation-only PR that precedes the `--target` flag by itself, and splitting it out would add review overhead without a corresponding benefit.

Given the scope (Codex target support, repo config, render adapters, check/status commands, and a later ChatGPT export target researched separately), this is medium-to-large, multi-stage scope. Recommend `/lrh-workstream` to govern staged delivery, with individual work items filed against it:

1. **WI-SKILLS-TARGET-AWARE-INSTALL** (first work item): add `--target claude|codex|all`; preserve existing Claude default behavior; install Codex skills to `~/.agents/skills/` (user scope) and `./.agents/skills/` (project scope, via `--local`); keep `--dry-run`/`--force`/`--diff` behavior consistent across targets; direct-copy Codex output with the known body-prose caveat from Decision 4; add tests using temporary directories; update docs to describe both targets.
2. **Source abstraction** — add `--source` (`lrh-package`, `current-repo`, explicit path), matching Decision 1.
3. **Repo config** — `project/agent_skills.yaml` parsing, subject to the parser constraint in Decision 5.
4. **Render adapters** — `ClaudeSkillRenderer`/`CodexSkillRenderer` split, with the Codex adapter targeting `agents/openai.yaml` per Decision 2, plus canonical/target validation layers (`lrh skills check`).
5. **Status/check commands** — `lrh skills check`, `lrh skills status`.
6. **Body-prose neutralization** (follow-on, separately scoped per Decision 4) — rewrite existing skill bodies to be agent-neutral.
7. **ChatGPT export** — blocked on research per Decision 8; not scheduled until the upload/registration contract is confirmed.

## Cross-References

- Prior proposal establishing `src/lrh/skills/` and the current copy-only installer: `project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`
- Current implementation: `src/lrh/skills/installer.py`, `src/lrh/cli/main.py:130-160,1241-1262`
- Existing multi-target rendering precedent: `docs/reference/cli/request.md:114` (`--target-agent`, defaults to `"Codex Cloud"`)
- Existing tests to extend, not replace: `tests/skills_installer_test.py`, `tests/cli_tests/skills_test.py`
- Prior bug precedent motivating Decision 5: `src/lrh/control/validator.py:568` (`_parse_simple_yaml`)

## Open Questions

- ChatGPT Skills' actual upload/registration API contract — not yet researchable from public docs as of this proposal's drafting; blocks Stage 7 scoping (Decision 8).
- Whether Codex's `agents/openai.yaml` should be treated as canonical-source content (versioned alongside `SKILL.md`) or purely target-generated — deferred to the render-adapter work item (Decision 2 covers the mechanism, not the authoring workflow).
- Exact test budget per stage (unit/integration/regression counts) — the source design's Testing Strategy section is a reasonable checklist but wasn't sized against work-item scope; left for each implementing work item to size individually rather than fixed here.
