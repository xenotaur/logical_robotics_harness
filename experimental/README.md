# Experimental LRH Work

This directory contains temporary investigation code and notes for LRH
maintainers. It is intentionally outside `src/`, `tests/`, and `project/` so
early spikes do not become package API, normal test surface, or authoritative
control-plane state by accident.

Guidelines:

- Treat everything here as provisional.
- Do not import files from this directory into `src/lrh/`.
- Do not add this directory to normal package builds or test discovery.
- Keep raw private transcript captures out of Git.
- Prefer writing raw captures to `/private/tmp` and committing only sanitized
  findings or plans.
- Promote useful code into `src/lrh/` only through a separate reviewed work item
  or proposal.

