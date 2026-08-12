---
id: BACKLOG-LRH-SKILLS-TARGET-AWARE-INSTALL
type: design_backlog
title: Codex Skills Compatibility Backlog
status: closed
created_on: 2026-08-02
updated_on: 2026-08-09
related_design:
  - project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md
  - project/workstreams/proposed/WS-SKILLS-TARGET-AWARE-INSTALL.md
---

# Codex Skills Compatibility Backlog

Lightweight list of Claude-to-Codex skill compatibility issues discovered while
dogfooding LRH skills in Codex. Each entry should record what was observed, why
it matters for Codex, and where it came from so a future burn-down pass can
decide whether to fix it in a render adapter, canonical skill prose, or
supporting LRH tooling.

---

## Planning skills hard-code Claude execution-record provenance

**Noted:** 2026-08-02, while running `/lrh-workstream` from a Codex app
session for `PROP-LRH-SKILLS-TARGET-AWARE-INSTALL`.

**Issue:** The planning skills instruct the operator to create execution
records with Claude-specific provenance, including `agent: claude_app`,
`session_transcript: claude-app:<host-uuid-stem>`, and references to
`CLAUDE_CODE_HOST_SESSION_ID`. That is appropriate for Claude Code sessions but
not for Codex app sessions, where the durable transcript identifier and agent
label are different.

**Idea:** Define Codex execution-record provenance values, such as
`agent: codex_app` and a Codex task/thread transcript reference, then update the
skill instructions or target renderer so Codex-installed skills do not tell
Codex to record itself as Claude.

**Disposition:** Fixed in canonical prose by
`WI-SKILLS-BODY-PROSE-NEUTRALIZATION`. Execution-record templates now use
`agent: <agent-backend>` and describe `claude_app`, `codex_app`,
`codex_cloud`, and `manual` options. Session transcript guidance now branches
by backend and does not tell Codex-installed skills to record themselves as
Claude.

**Related:** `src/lrh/skills/lrh-workstream/SKILL.md`;
`src/lrh/skills/lrh-workstream/references/execution-record.md`;
`src/lrh/skills/lrh-work-item/SKILL.md`;
`src/lrh/skills/lrh-work-item/references/execution-record.md`;
`src/lrh/skills/lrh-proposal/SKILL.md`;
`src/lrh/skills/lrh-proposal/references/execution-record.md`;
`src/lrh/skills/lrh-implement/SKILL.md`;
`src/lrh/skills/lrh-land/SKILL.md`.

---

## Slash-command and argument-hint framing leaks into Codex installs

**Noted:** 2026-08-02, while applying a Claude-authored `/lrh-workstream`
skill manually in Codex.

**Issue:** LRH skill bodies and frontmatter frequently describe invocation as
Claude slash commands (`/lrh-workstream`, `/lrh-work-item`, `/lrh-land`) and use
Claude UI metadata such as `argument-hint`. Codex can still process the
procedural content when the user names the skill, but the installed Codex copy
would present Claude-specific command syntax and unsupported UI hints.

**Idea:** Make canonical skill prose more agent-neutral, or have the Codex
renderer remove/translate Claude-only invocation metadata and examples where
that can be done mechanically. Keep concrete command names only where the LRH
workflow itself requires them as historical or user-facing identifiers.

**Disposition:** Partly fixed in the Codex renderer and partly retained with
rationale. The render adapter strips Claude-only frontmatter metadata such as
`argument-hint` from Codex installs. Body prose was neutralized where the
wording described the executing backend or installed target. Literal
`/lrh-*` names remain where they identify LRH workflow names or user-facing
skill invocations; removing them would make the procedural references less
clear without improving Codex behavior.

**Related:** `src/lrh/skills/lrh-workstream/SKILL.md`;
`src/lrh/skills/lrh-work-item/SKILL.md`;
`src/lrh/skills/lrh-proposal/SKILL.md`;
`src/lrh/skills/lrh-implement/SKILL.md`;
`src/lrh/skills/lrh-land/SKILL.md`;
`project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md`
Decision 2 and Decision 4.

---

## Manual-only invocation metadata needs Codex policy translation

**Noted:** 2026-08-02, while reviewing which Claude skill metadata would behave
incorrectly if copied directly into `.agents/skills/`.

**Issue:** Several LRH skills rely on Claude's `disable-model-invocation: true`
metadata to prevent implicit use of manual-only workflows. Codex does not use
that frontmatter field directly; the proposal identifies `agents/openai.yaml`
as the Codex-side policy location. Direct copying without translation can make
the Codex skill discoverable while failing to preserve the intended invocation
policy.

**Idea:** Treat this as a renderer acceptance criterion: Claude
`disable-model-invocation: true` must become Codex
`policy.allow_implicit_invocation: false` in `agents/openai.yaml`, or an
equivalent Codex-supported policy mechanism if the platform contract changes.

**Disposition:** Fixed by `WI-SKILLS-RENDER-ADAPTERS`. The Codex renderer
strips `disable-model-invocation` from rendered `SKILL.md` and writes or
preserves `agents/openai.yaml` with
`policy.allow_implicit_invocation: false` when the canonical Claude metadata
requests manual-only invocation.

**Related:** `src/lrh/skills/lrh-implement/SKILL.md`;
`src/lrh/skills/lrh-land/SKILL.md`;
`project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md`
Decision 2.

---

## Skill references assume `.claude/skills/` mirrors as the installed target

**Noted:** 2026-08-02, while reading LRH skill authoring and validation
guidance before creating this workstream.

**Issue:** Some skill instructions and references describe installation,
mirroring, or validation in terms of `src/lrh/skills/` and `.claude/skills/`.
That was correct when Claude was the only local target, but it is incomplete
once `.agents/skills/` becomes a first-class Codex install target.

**Idea:** Update skill authoring and closeout guidance to talk about canonical
sources and selected install targets, then make validation or status tooling
show both Claude and Codex mirror state when relevant.

**Disposition:** Fixed in canonical prose. Skill references now describe
canonical source plus selected install targets, and validation guidance uses
`lrh skills check --target claude --local` and
`lrh skills status --target codex --local` instead of treating a raw
`.claude/skills/` byte mirror as the universal test. Claude project installs
remain available and intentional; Codex installs are validated as rendered
target output.

**Related:** `src/lrh/skills/lrh-work-item/references/work-item-body-guide.md`;
`src/lrh/skills/lrh-workstream/SKILL.md`;
`project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md`
Decision 1, Decision 3, and Decision 4.

---

## `/lrh-land` assumes Claude session surfaces and installed slash skills

**Noted:** 2026-08-02, while running the `/lrh-land` workflow from Codex on
PR #468.

**Issue:** The `/lrh-land` workflow was usable from the repository copy, but it
was not installed as a Codex-discoverable skill in this session. Its transcript
discovery step also starts with `CLAUDE_CODE_HOST_SESSION_ID` and
`claude-app:<host-uuid-stem>`, which do not resolve in Codex. The inlined
sub-skills carry the same Claude provenance examples in their execution-record
templates.

**Idea:** Add target-aware transcript discovery and execution-record
provenance guidance for Codex. Codex-installed lifecycle skills should refer to
Codex task/thread identifiers where available and should not require the user
to know that the canonical source lives under `src/lrh/skills/`.

**Disposition:** Fixed in canonical prose for the lifecycle skills. `/lrh-land`
and `/lrh-closeout` now branch transcript resolution by execution-record
backend, explicitly covering `codex_app`, `codex_cloud`, Claude.app, manual,
and other non-Claude backends. Claude env vars and `claude-app:` URLs are
retained only for Claude.app records.

**Related:** `src/lrh/skills/lrh-land/SKILL.md`;
`src/lrh/skills/lrh-land/references/land-workflow.md`;
`src/lrh/skills/lrh-confirm-fixes/SKILL.md`;
`src/lrh/skills/lrh-review-response/SKILL.md`.

---

## Local sub-agent self-review is available in Codex but under-modeled in `/lrh-land`

**Noted:** 2026-08-02, while landing PR #468 from Codex after the user noted
that GitHub code reviews are an expensive resource and Claude sessions now
prefer fresh independent sub-agent self-review when possible.

**Issue:** Codex can emulate the desired fresh independent self-review pattern
with a spawned sub-agent that does not post GitHub reviews, request reviewers,
edit files, or push commits. `/lrh-confirm-fixes` already documents a
`--subagent` verification mode, but `/lrh-land` still frames REVIEW-LANDED
mostly around GitHub review-response and reviewer retrigger mechanics. That is
appropriate when GitHub reviewers are the authoritative signal, but it does not
clearly model the cheaper local self-review path as an intentional review
signal for Codex dogfooding.

**Idea:** Decide how LRH should represent local independent self-review in the
land/confirm workflow: as a Codex target adaptation, a repo policy override, or
an explicit workflow option. The guidance should distinguish local self-review
from GitHub review objects so it does not accidentally imply branch-protection
approval or consume reviewer resources.

**Disposition:** Deliberately retained as a workflow-policy concern for now.
The repository chain defaults already encode
`self_review_preference: substitute_self_review`, and this LRH run uses that
preference. The `/lrh-land`/`/lrh-confirm-fixes` prose still distinguishes
local self-review from GitHub review objects so it does not imply branch
protection approval or consume reviewer resources. No renderer change is
needed for this entry in this work item.

**Related:** `src/lrh/skills/lrh-land/SKILL.md`;
`src/lrh/skills/lrh-confirm-fixes/SKILL.md`;
`src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md`;
`project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md`
Decision 4.
