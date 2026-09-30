---
execution_id: 2026_10_06_03_57_08_WI_LOCAL_AGENT_001_T0_ASK_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_LOCAL_AGENT_001_T0_ASK_SELFREVIEW)[2026-10-06T03:57:08+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
created_at: 2026-10-06T03:57:08+00:00
agent: claude_app
instruction_source: lrh-implement Step 7.5 diff-mode self-review for PROMPT(WI-LOCAL-AGENT-001:WI_LOCAL_AGENT_001_T0_ASK)[2026-09-30T21:57:20+00:00]
session_transcript: claude-app:ae03b82e-f234-4666-ab7a-2c5a12a5f340
---

# Summary

Diff-mode `/lrh-self-review` of the T0 `ask` prototype
(`experimental/local_agent/`), before the first push. `rerun_of` is empty by
design. It was report-only; the implementing session applied the fixes.

# Result

A cold subagent verified the following:

- errors and logs name categories only;
- the stream uses the no-proxy, no-redirect opener with `think: False`;
- budgets, `delete`/`prune` validation, and store placement are correct;
- 115 tests, lint, and format pass.

It reported 14 findings:

1. **Medium: `.env*` was implemented as `.env` and `.env.*`.** `.envrc` and
   `.env_prod` were admitted. The main session re-verified this against
   `settings.py`. **Fixed:** the pattern is now `.env*`, with tests.
2. **Medium: failures before the call were not logged.** This covered an
   unknown `--wi`, a refused endpoint or model, and declining at confirmation.
   **Fixed:** `ask.record_failure` logs `missing_prerequisite`,
   `backend_error`, or `cancelled`, with CLI tests.
3. **Low:** `secret`/`credential` directory names were not matched.
   **Fixed:** directory components are checked too.
4. **Low:** the partial streamed answer was lost on failure. **Fixed:** it is
   kept with `partial: true`.
5. **Low:** an output error such as a broken pipe was reported as Ollama
   unreachable. **Fixed:** only transport reads are classified.
6. **Low:** wall time could overshoot by up to one read timeout. **Deferred:** a
   short per-read timeout would misfire during long prompt evaluation.
7. **Low:** test gaps. **Fixed:** tests now cover "never sent or logged" for
   excluded content, medium findings in the question at export, and a
   preflight failure making no call.
8. **Low:** an Ollama stream `error` chunk lost its message. **Fixed.**
9. **Nit:** test classes after the `__main__` guard. **Fixed.**
10. **Nit:** placeholder text in the question was expanded. **Fixed:**
    substitution is now a single pass.
11. **Nit:** prose such as "S3 bucket" counts as a citation. **Deferred.**
12. **Nit:** `log` token statistics are median output tokens only.
    **Deferred.**
13. **Nit:** Ctrl-C at the prompts printed a traceback. **Fixed.**
14. **Nit:** a misnamed CLI test. **Fixed.**

# Validation

- `experimental/local_agent/test`: 123 tests OK.
- Format and lint clean.
- `scripts/test --log`: PASS.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

Deferred items 6, 11, and 12 are carried to the T0 PR's merge gate.
