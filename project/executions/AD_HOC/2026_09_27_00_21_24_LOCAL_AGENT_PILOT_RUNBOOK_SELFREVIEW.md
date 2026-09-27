---
execution_id: 2026_09_27_00_21_24_LOCAL_AGENT_PILOT_RUNBOOK_SELFREVIEW
prompt_id: PROMPT(AD_HOC:LOCAL_AGENT_PILOT_RUNBOOK_SELFREVIEW)[2026-09-27T00:21:24+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/745
commit: 744c0e5ae0c77332bad3dfc84aaecf6538058822
created_at: 2026-09-27T00:21:24+00:00
agent: claude_app
instruction_source: lrh-implement Step 7.5 diff-mode self-review for PROMPT(WI-LOCAL-AGENT-001:LOCAL_AGENT_PILOT_RUNBOOK)[2026-09-26T22:07:47+00:00]
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Diff-mode `/lrh-self-review` of the local-agent pilot runbook change before its
first push. The change adds `run --prompt-version`, the `task` and `b0`
subcommands, a scores template, and a numbered Runbook, with no pre-registered
criteria changed. `rerun_of` is empty by design. The diff was taken against the
branch base `3c76b49d`.

# Result

A cold subagent confirmed that no pre-registered content changed:

- `tasks.yaml`, `settings.py`, and `prompts/` have no diff;
- the only README hunk starts at the old Commands section;
- the order table correctly applies the B0/B1/B1/B0 pattern;
- the runbook commands work with the fake backend.

It reported seven findings, none blocking:

1. **Medium: the scores template shipped real values** (`usefulness: 2`, zero
   minutes), so an unedited template scored as a useful, zero-effort result.
   The main session re-verified this against the file it had written.
   **Fixed:** every placeholder is now `null`, and `evaluate` rejects nulls and
   negative counts. Test added.
2. **Medium: wrong runbook claim.** It said committing prompt versions keeps
   `lrh_code_dirty` clean, but that flag is captured at packet build.
   **Fixed:** the wording now says to build each task's packet once and reuse
   the sha for B0 and all B1 runs, with prompt traceability via
   `prompt_version` and `prompt_template_sha256`.
3. **Low-medium: tuning-text privacy was enforced only by prose.** **Fixed:**
   step 7 now has separate export commands for frozen-prompt B1 runs and B0
   records versus tuning-iteration B1 runs.
4. **Low: B0 `manual` outcomes could skew a naive non-completed count.**
   **Fixed:** the runbook says to count over `condition: B1` only.
5. **Low: B0 minutes were recorded in two places.** **Fixed:** the runbook
   says to set `total_human_minutes` equal to `b0 --minutes`.
6. **Low: tracebacks on bad input.** A missing briefing file and malformed
   tasks entries raised tracebacks. **Fixed:** they now produce `error:` and
   exit 2, or raise `TaskError`. Tests added.
7. **Nit: B1-first wording.** **Fixed:** the redundant `notes` instruction was
   dropped; the order table records the order.

# Validation

- `experimental/local_agent/test`: Ran 78 tests, OK.
- `scripts/test --log`: Ran 1806 tests, OK.
- `scripts/format --check --diff` and `scripts/lint`, both default and on
  `experimental/local_agent`: clean.
- `lrh validate`: 0 errors, 0 warnings.
- A `task` dry run built packets for all 12 tasks.

# Follow-up

None. The hosted review round still runs as usual.
