---
execution_id: 2026_09_26_05_18_25_WI_LOCAL_AGENT_001_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_LOCAL_AGENT_001_SELFREVIEW)[2026-09-26T05:18:25+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-09-26T05:18:25+00:00
agent: claude_app
instruction_source: lrh-implement Step 7.5 diff-mode self-review for PROMPT(WI-LOCAL-AGENT-001:WI_LOCAL_AGENT_001)[2026-09-26T02:47:36+00:00]
session_transcript: pending
---

# Summary

Diff-mode `/lrh-self-review` of PR B for `WI-LOCAL-AGENT-001`: pre-registration
(`experiments/`) and the stage-0 prototype (`experimental/local_agent/`). The
pass ran before the first push. `rerun_of` is empty by design, because no
primary record exists before the PR opens. The diff was taken against the
branch base `9919582b`, since `origin/main` had advanced.

# Result

The first dispatch was interrupted by the user and produced no report. It was
rerun at the user's request.

A cold subagent verified the pins, digests, dry runs, and proxy/redirect
handling. It reported nine findings, none blocking except finding 1 for live
runs:

1. **Medium: stored packet not re-hashed.** The runner compared only the two
   CLI hash strings. The main session re-verified this by code inspection
   (`runner.run_briefing` never recomputed `context.packet_sha256`).
   **Fixed:** the runner re-hashes and refuses tampered packets, and the store
   validates packet ids.
2. **Low-medium: raw model text in citation stats.** Unresolved citation
   strings copied model text into `run.json`, and therefore into default
   exports. **Fixed:** only pattern-valid refs are listed; free-form refs are
   counted as `malformed_citations`.
3. **Low: byte budget wording.** The README described the byte budget as
   covering the whole packet, but it counts source content only. **Fixed:**
   `source_bytes` and `rendered_bytes` are both recorded, and the README is
   reworded.
4. **Low: `--include-output` did not require scores, and evaluation notes were
   unscanned.** **Fixed:** an evaluation is now required, and evaluations are
   scanned.
5. **Low: unknown packet raised a traceback.** **Fixed:** the CLI reports
   `error:` and exits 2. Config errors before a run stays a deliberate
   pre-attempt error.
6. **Low: `urllib_transport` untested.** **Fixed:** a new behavioural test
   shows the opener ignores `http_proxy` (against a default-opener control)
   and refuses redirects. The test also corrected an inaccurate assumption:
   the empty `ProxyHandler` is not registered; it works by replacing the
   default env-reading handler.
7. **Nit: line numbering.** `str.splitlines` split on form feeds and similar
   characters. **Fixed:** splitting is on newlines only.
8. **Nit: label.** LCATS #400 was labelled a merge. **Fixed:** relabelled as a
   squash.
9. **Nit: dirty flag.** `lrh_commit` had no dirty flag. **Fixed:**
   `lrh_code_dirty` is recorded.

Earlier in the same implementation, a packet dry run caught a fabricated
full-length SHA expansion for LRH pin `9919582b` in `tasks.yaml`. It was
corrected to `9919582ba0dab29407198d54e381fe433b93ff46`, and all 12 pins now
resolve exactly.

# Validation

- `experimental/local_agent/test`: Ran 58 tests, OK.
- `scripts/test --log`: Ran 1795 tests, OK. The prototype is not discovered.
- `scripts/format --check --diff` and `scripts/lint`, both default and on
  `experimental/local_agent`: clean.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

None for this PR. The hosted review round still runs as usual.
