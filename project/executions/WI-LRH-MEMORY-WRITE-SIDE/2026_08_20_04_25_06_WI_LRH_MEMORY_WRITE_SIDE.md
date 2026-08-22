---
execution_id: 2026_08_20_04_25_06_WI_LRH_MEMORY_WRITE_SIDE
prompt_id: PROMPT(WI-LRH-MEMORY-WRITE-SIDE:WI_LRH_MEMORY_WRITE_SIDE)[2026-08-20T01:29:37+00:00]
work_item: WI-LRH-MEMORY-WRITE-SIDE
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/570
commit: 84bd10ae8e531f3d02311e0ec49a2804005392a3
created_at: 2026-08-20T04:25:06+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-MEMORY-WRITE-SIDE.md
session_transcript: claude-app:3bfe1290-c27a-4ffe-82f5-e718adbd8319
---

# Summary

Implemented `WI-LRH-MEMORY-WRITE-SIDE`: the write-side `lrh memory`
command surface (`write`/`list`/`validate`/`repair`) per
`PROP-LRH-MEMORY-COMMAND`, now that the proposal is adopted (PR #568).

# Result

Created `src/lrh/atomic_write.py` (extracted `_atomic_write`/
`_atomic_write_bytes` from `prompt_workflow_sessions.py`, all three call
sites there updated to the shared module, no leftover duplicates) and
`src/lrh/prompt_workflow_memory.py` (core logic: `write_memory`,
`list_memories`, `validate_corpus`, `repair_memory`, plus
`read_frontmatter_and_body` using `yaml.safe_load` rather than the
constrained `lrh.control.parser`, which cannot parse the nested
`metadata:` mapping this schema requires). Added `src/lrh/memory_workflow.py`
(thin CLI wiring, mirroring `sessions_workflow.py`'s pattern) and
registered `memory` in `src/lrh/cli/main.py`. Migrated
`src/lrh/skills/lrh-closeout/SKILL.md`'s Step 7 direct-write instruction
to call `lrh memory write`, and regenerated the rendered `.claude`/
`.agents`/`.gemini` installs via `lrh skills install --local --target all
--source current-repo --force` (only `lrh-closeout` changed; verified via
`git status`). Added `project/memory/decisions/DEC-LRH-MEMORY-AUTHORED-BY.md`
recording the schema decision, per the work item's own Required Changes.

Implements the crash-consistency ordering from Decision 4's addendum
(memory-file rename strictly before the `MEMORY.md` rename — verified by
reading the code, not just trusting the docstring) and the malformed/
legacy two-tier `validate` split from Decision 3's grandfathering clause.
`repair` routes through `write`'s own validated path (`force=True`) and
preserves the existing `authored_by` unless the caller's `--set`
explicitly overrides it.

**A pre-push diff-mode self-review (`/lrh-self-review`, no `--pr` — no PR
existed yet) found and this record's own commit fixes a real,
exploit-confirmed security issue**: `repair_memory` did not validate its
`name` argument before resolving a filesystem path, unlike
`write_memory`. A `../`-laden `name` (e.g.
`../../../outside/secret.md`) could read an arbitrary accessible `.md`
file's frontmatter and body into the memory corpus. Independently
re-verified the finding directly (reproduced the exploit) before
fixing — mandatory discipline, not accepted on the subagent's report
alone. Fixed by validating `name` the same way `write_memory` already
did, before any path resolution; added a regression test
(`test_repair_rejects_path_traversal_name`) reproducing the original
exploit and confirming it now raises `MemoryValidationError`.

Manually smoke-tested end-to-end beyond the automated suite: write → list
→ validate → repair round trip; cross-agent overwrite refusal without
`--force` and success with it; legacy vs. malformed detection against
hand-crafted fixture files; the path-traversal exploit repro before and
after the fix.

# Validation

- `lrh validate` — 0 errors, 0 warnings.
- Full suite: `PYTHONPATH=src python3 -m unittest discover -s tests -p
  "*_test.py"` — 1129/1129 tests pass (1128 pre-existing + this work
  item's 25 new tests, including the path-traversal regression test).
- `black`/`ruff` clean on all new/changed files. This dev environment's
  installed tool versions (`black` 25.11.0, `ruff` 0.15.0) are older than
  this repo's pinned `required-version` (`26.3.1`/`0.15.12`), so
  `scripts/format`/`scripts/lint` themselves refuse to run here — a
  pre-existing environment gap, not something this change caused. Ran
  the underlying tools directly (`black --config <local-override>`,
  `ruff check --isolated`) against every new/changed file for a real
  signal instead: both clean, 0 findings.
- `lrh memory write --help` / `lrh memory validate --help` — both exit 0.

# Follow-up

- `WI-LRH-MEMORY-ARCHIVE-SIDE` (depends on this item, for the extracted
  atomic-write helper) and `WI-LRH-MEMORY-PORTABILITY` (depends on this
  item's `write` validation path) are now unblocked on this dependency.
- `lrh memory repair` against the 19 already-known non-conforming memory
  files from the original findings audit is still out of scope — this
  item delivers the tool, not the retroactive cleanup operation.
- This dev environment's `black`/`ruff` pinned-version mismatch is worth
  fixing at the environment level (not this WI's scope) so future
  sessions don't need the same local-override workaround.
