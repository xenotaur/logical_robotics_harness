## Skills

- `/lrh-create-skill` — Create a new project-local Claude Code skill following the LRH pattern
- `/lrh-work-item` — Create a new LRH work item in project/work_items/proposed/
- `/lrh-implement` — Implement an LRH work item or ad-hoc task using the three-phase execution session model
- `/lrh-land` — Land an open PR end-to-end: chain auth gate, review, confirm, merge gate, closeout
- `/lrh-execute` — Implement one work item end-to-end and land it: resolve the target (WI-ID or next-ready WI under a WS-ID), enforce depends_on, chain auth gate, inline /lrh-implement then /lrh-land
- `/lrh-review-response` — Address open PR review comments using lrh request review_response, with confirmation gate and execution record
- `/lrh-confirm-fixes` — Pre-merge verification: fresh-eyes check pushed fixes against the current diff, resolve satisfied review threads, surface exceptions, and report a merge-readiness verdict without merging
- `/lrh-self-review` — Dispatch a cold-context subagent to independently review a diff (before a PR's first push) or a PR (as round-cap-gate.md's post-ceiling substitute for a bot retrigger)
- `/lrh-design` — Generate a structured design for a feature, improvement, or system
- `/lrh-proposal` — Create a new LRH design proposal in project/design/proposals/proposed/
- `/lrh-workstream` — Create a new LRH workstream planning node in project/workstreams/proposed/
- `/lrh-doc-audit` — Audit a repository's documentation against the Diataxis framework and write a structured audit artifact
- `/lrh-doc-organize` — Implement one scoped phase of Diataxis-informed documentation reorganization as a reviewable PR
- `/lrh-doc-work` — Update a repository's documentation to reflect recently completed work (merged PR, resolved WI, or closed WS)
- `/lrh-closeout` — Automate the post-execution closeout workflow: land execution records, resolve work items, close workstreams, and adopt proposals
- `/lrh-readiness` — Close the ready-work-item apply loop: draft and apply a confirmed patch for a thin work item, then re-validate
- `/lrh-work-remains` — Summarize session accomplishments and report what work remains, grounded in tracked repo state rather than conversational recall
