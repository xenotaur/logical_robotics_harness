---
execution_id: 2026_08_09_03_54_23_LRH_FRONTMATTER_PARSER
prompt_id: PROMPT(AD_HOC:LRH_FRONTMATTER_PARSER)[2026-08-09T03:54:05+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 531
commit: 
created_at: 2026-08-09T03:54:23+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/lrh-frontmatter-parser/00_proposal.md
session_transcript: "claude-app:494c3b1f-14c8-46bf-a4e3-0b6e8df119e8"
---

# Summary

Investigated a reported bug where a `#` comment line interleaved in a
YAML frontmatter list crashes `control/parser.py`'s hand-rolled parser
but is invisible to `lrh validate` (which uses a second, independent
hand-rolled parser in `validator.py` that happens to tolerate it). Ran a
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
(scoped only to `validator.py`); closed it as superseded
(`status: abandoned`, moved to `project/work_items/abandoned/`,
`resolution:` records the supersession) rather than duplicating it. Wrote
`PROP-LRH-FRONTMATTER-PARSER` (design decisions: PyYAML as the engine,
accept real datetime objects and patch 3 consumers rather than disabling
PyYAML's implicit resolver, a schema-level check for the colon-collapse
case, a diff-based one-time content migration tool exposed via
`lrh project doctor --fix-frontmatter`, and a raw-text lint guard plus
authoring guidance to prevent recurrence) and its governing workstream
`WS-LRH-FRONTMATTER-PARSER`. No implementation code was changed in this
PR — this PR is planning-artifact-only, filing the design for the
workstream's work items to implement.

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
