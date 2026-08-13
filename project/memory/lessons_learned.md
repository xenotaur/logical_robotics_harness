# Lessons Learned

- The project schema needs to be readable without the harness.
- "Task" is too vague; typed work items are better.
- Evidence must be first-class rather than an afterthought.
- Current focus is a better general abstraction than a sprint-only model.
- In Codex `/lrh-land`, a fresh independent subagent self-review can find the
  same issue that later appears as a GitHub review thread; fix it once, then
  still resolve the GitHub thread through normal confirm-fixes so PR archaeology
  stays complete.
- In Codex LRH validation, prefer `conda run -n LRH ...` for repository scripts
  so Black/Ruff versions match the project environment; format, lint, and tests
  may still need unsandboxed execution when Black multiprocessing or serve tests
  bind local sockets.
- In Codex `/lrh-land`, `lrh prompt record-execution` can generate blank
  frontmatter fields with trailing spaces; `lrh validate` accepts them, but
  `git diff --check origin/main...HEAD` catches them and fresh self-review may
  flag them before merge.
- In execution records, do not start `instruction_source` with `/`; even a
  slash-command phrase such as `/lrh-land PR 487` is treated by validation as
  an absolute path leak. Use a scheme-style value such as
  `lrh-skill:lrh-land PR 487`.
