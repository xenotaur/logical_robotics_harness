---
execution_id: 2026_08_09_03_54_23_LRH_FRONTMATTER_PARSER
prompt_id: PROMPT(AD_HOC:LRH_FRONTMATTER_PARSER)[2026-08-09T03:54:05+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/531
commit: 
created_at: 2026-08-09T03:54:23+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/lrh-frontmatter-parser/00_proposal.md
session_transcript: "claude-app:494c3b1f-14c8-46bf-a4e3-0b6e8df119e8"
---

# Summary

Investigated a reported bug where a `#` comment line interleaved in a
YAML frontmatter list crashes `src/lrh/control/parser.py`'s hand-rolled parser
but is invisible to `lrh validate` (which uses a second, independent
hand-rolled parser in `src/lrh/control/validator.py` that happens to tolerate it). Ran a
full design (`/lrh-design`) evaluating whether to patch the two
hand-rolled parsers or consolidate onto a standard YAML engine, and
created `PROP-LRH-FRONTMATTER-PARSER` and `WS-LRH-FRONTMATTER-PARSER` to
capture the resulting design.

# Result

Chose to consolidate onto PyYAML (`yaml.safe_load`) rather than patch the
two hand-rolled parsers, after empirically confirming (via direct testing
against the real PyYAML install, and a systematic old-parser-vs-PyYAML
diff run across every file in this repo's `project/` tree) that a naive
swap would silently mishandle real existing content in three distinct
ways: unquoted `key: value`-shaped list items collapsing into one-entry
mappings (9 files), plain scalars starting with a reserved indicator or
containing a second colon raising hard syntax errors (18 files), and a
space-then-`#` sequence anywhere in a plain scalar silently truncating
the value with no parse error (45 files / 50 fields, mostly
`instruction_source` values referencing "PR #NNN"). A fourth issue —
PyYAML's implicit timestamp resolver converting unquoted ISO-8601-shaped
scalars into `datetime` objects — was traced to exactly 3 downstream
consumers rather than the naive 723-file estimate. Verified that these
lexical-grammar issues are properties of YAML's plain-scalar style
specifically (quoted and block-scalar forms are immune), not fixable by
switching to a different YAML library (ruamel.yaml, strictyaml both
evaluated and ruled out). During the prior-art check for the design, found
`WI-VALIDATOR-YAML-PARSER` already proposed a narrower version of this fix
(scoped only to `src/lrh/control/validator.py`); closed it as superseded
(`status: abandoned`, moved to `project/work_items/abandoned/`,
`resolution:` records the supersession) rather than duplicating it. Wrote
`PROP-LRH-FRONTMATTER-PARSER` (design decisions: PyYAML as the engine,
accept real datetime objects and patch 3 consumers rather than disabling
PyYAML's implicit resolver, a schema-level check for the colon-collapse
case, a raw-text lexical detector shared between a one-time content
migration tool (`lrh project doctor --fix-frontmatter`) and a permanent
`lrh validate` lint guard, plus authoring guidance to prevent recurrence)
and its governing workstream `WS-LRH-FRONTMATTER-PARSER`. No
implementation code was changed in this PR — this PR is
planning-artifact-only, filing the design for the workstream's work items
to implement.

**Review round:** `chatgpt-codex-connector` (P1) found the migration
tool's originally-drafted detection logic (diff the old lenient parser's
output against `yaml.safe_load`'s output, rewrite every divergence) was
unsound — verified directly that it would corrupt already-correctly-quoted
list items (the old parser retains literal quote characters that
`safe_load` strips) and would contradict Decision 2 by flagging the
accepted date/datetime divergence as unsafe. Revised Decision 4 to share
its detector with Decision 5's raw-text lint guard instead, so a rewrite
only fires on a proven-unsafe lexical pattern in the raw text, never on a
bare difference in what the two parsers return.
`copilot-pull-request-reviewer` found this record's own `pr:` field used
an unquoted integer, inconsistent with every other execution record's
convention; corrected to the full PR URL.

**Review round 2:** `chatgpt-codex-connector` found two P2 inconsistencies
in the round-1 fix: Decision 4's shared-detector list omitted the
implicit-resolution check Decision 5 had, contradicting the "can never
disagree" claim; and Decision 5's `bool/null/date/int` enumeration missed
`float`. Fixed both — Decision 4 now lists the implicit-resolution check
explicitly, and Decision 5's language covers any non-string implicit
resolution rather than a closed, re-forgettable list. Also independently
caught, via `copilot-pull-request-reviewer`'s suppressed-comments section,
that this proposal/workstream/WI used the shorthand `control/parser.py`/
`control/validator.py` throughout instead of the real repo path
`src/lrh/control/...` — fixed across all four touched files.

# Validation

- `lrh validate` — 0 errors, 1 pre-existing warning unrelated to this
  change (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on
  `WS-SESSION-ARCHIVE-SYNC`, present on `main` before this PR).

# Follow-up

- File work items under `WS-LRH-FRONTMATTER-PARSER` for: parser
  consolidation + tests, the 3 datetime-consumer patches, the 27-file
  manual content fixes, the `lrh project doctor --fix-frontmatter`
  migration tool, and the `lrh validate` lint guard + skill guidance
  updates.
- Run the migration tool dry-run against this repo's own `project/` tree
  and manually review the diff before any `--apply`, per the proposal's
  Decision 4 rollout note.
