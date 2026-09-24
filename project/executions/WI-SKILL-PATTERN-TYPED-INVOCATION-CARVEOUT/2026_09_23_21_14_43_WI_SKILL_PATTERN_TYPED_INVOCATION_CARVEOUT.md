---
execution_id: 2026_09_23_21_14_43_WI_SKILL_PATTERN_TYPED_INVOCATION_CARVEOUT
prompt_id: PROMPT(WI-SKILL-PATTERN-TYPED-INVOCATION-CARVEOUT:WI_SKILL_PATTERN_TYPED_INVOCATION_CARVEOUT)[2026-09-23T21:07:32+00:00]
work_item: WI-SKILL-PATTERN-TYPED-INVOCATION-CARVEOUT
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/718
commit: a0f954a8823578e6741c215b58832cc2c15e6e94
created_at: 2026-09-23T21:14:43+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-SKILL-PATTERN-TYPED-INVOCATION-CARVEOUT.md
session_transcript: claude-app:3278dd49-9852-4955-b978-00367552dc27
---

# Summary

Implemented `WI-SKILL-PATTERN-TYPED-INVOCATION-CARVEOUT` via `/lrh-execute`:
added a new "## Typed-invocation carve-out (opt-in, not a default)"
section to `lrh-skill-pattern.md`'s confirm-before-write gate area,
documenting the exception `WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT`
(PR #703) already implemented in practice for `/lrh-export-claude`, per
the deferred `km9-g` review finding this WI exists to track.

# Result

Edited `src/lrh/skills/lrh-create-skill/references/lrh-skill-pattern.md`,
adding the new section covering all 5 Required Changes: the carve-out
itself, its opt-in scoping with `lrh-export-claude/SKILL.md` Step 3 cited
as the worked reference implementation, the `<command-message>`/
`<command-name>` detection signal with the ambiguous-defaults-to-model
fallback, and the dangerous-flag exception pattern (a static named list,
citing `--force`, with the duplication-avoidance rationale). Re-rendered
the three installed copies (`.claude/skills`, `.agents/skills`,
`.gemini/plugins/lrh/skills`) for `lrh-create-skill` only, using the
established `installer.resolve_skill_source`/`_copy_skill_from_source`
workaround (`lrh skills install --force` is target-wide and other
targets carry unrelated pre-existing local modifications from other
in-flight work). Verified `git status` showed only the expected 4 files
changed, and diffed all three installs byte-identical to source.

**Diff-mode `/lrh-self-review` pass** (cold subagent, before first push):
verified the new text's factual accuracy line-by-line against the actual
`lrh-export-claude/SKILL.md` Step 3 it cites, confirmed all 5 Required
Changes and Acceptance Criteria satisfied, confirmed the 4-file scope,
and confirmed the three installs byte-identical. **One should-fix
finding**: the new subsection was nested as `### Typed-invocation
carve-out` under `## The confirm-before-write gate`, but that heading
level is the *only* real `###` anywhere in the document outside an
illustrative fenced-code example — breaking the file's own established
flat `##`-section convention. **Independently re-verified** by this
session directly (`grep -n "^##\|^###"` against the file) — confirmed
accurate. Fixed: promoted to a flat `## Typed-invocation carve-out
(opt-in, not a default)` section, matching the file's existing structure
exactly. Re-rendered all three installs and re-ran full validation after
the fix; no regression.

Confirmed the pre-existing, repo-wide Codex `argument-hint has no Codex
metadata equivalent` finding on `lrh-create-skill` (its own `SKILL.md`
frontmatter, unaffected by this diff since only a `references/` file was
touched) is unrelated to this change — same finding documented in
`WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT`'s own execution record
from earlier this session.

Opened https://github.com/xenotaur/logical_robotics_harness/pull/718.

**Branch-naming note:** `xenotaur/feat/wi-skill-pattern-typed-invocation-carveout`
was already used by PR #713 (the planning PR). Its tip (`7053ecba`) was
confirmed a genuine ancestor of `origin/main` before reset — safely reset
via `git checkout -B` from fresh `origin/main`, same pattern as
`WI-CLAUDE-EXPORT-MARKDOWN-USER-TURN-MISLABEL`'s implementation PR.

# Validation

- `scripts/version tools` — ruff 0.15.12, black 26.3.1, versions as
  pinned.
- `PYTHONPATH=src scripts/format --check --diff` — clean.
- `PYTHONPATH=src scripts/lint` — clean.
- `PYTHONPATH=src scripts/test` — full suite + smoke, exit 0.
- `lrh validate` — 0 errors, 0 warnings.
- `lrh skills check --target claude --local --source current-repo`,
  `--target codex`, `--target antigravity` — all report `lrh-create-skill`
  up to date.

# Follow-up

- Proceed to `/lrh-land` for PR #718.
