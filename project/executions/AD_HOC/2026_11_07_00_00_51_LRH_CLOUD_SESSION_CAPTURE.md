---
execution_id: 2026_11_07_00_00_51_LRH_CLOUD_SESSION_CAPTURE
prompt_id: PROMPT(AD_HOC:LRH_CLOUD_SESSION_CAPTURE)[2026-11-06T23:42:59+00:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/863
commit:
created_at: 2026-11-07T00:00:51+00:00
agent: claude-code
instruction_source: project/design/proposals/proposed/lrh-cloud-session-capture/00_proposal.md
session_transcript: pending
---

# Summary

Investigated why `/lrh:lrh-export-claude` needed manual recovery and three
permission round trips in a Claude Code cloud session on `xenotaur/taurworks`
(2026-11-06). Captured the result as three kinds of planning artifact:

- an evidence audit;
- the design proposal `PROP-LRH-CLOUD-SESSION-CAPTURE`;
- seven companion work items: six in the first commit, and a seventh added
  in the revision described under Result.

The user confirmed the proposal and the first six work items before anything
was written, and chose a single PR for the set. That's why one execution record
covers the whole set, instead of one per `/lrh-proposal` and
`/lrh-work-item` run.

# Result

- `project/audits/2026-11-06-cloud-session-export-audit.md`: findings for
  each investigation question, cited to repo files, `lrh conversation ...
  --help` output, and Claude Code docs fetched 2026-11-06.
- `project/design/proposals/proposed/lrh-cloud-session-capture/00_proposal.md`
  (`PROP-LRH-CLOUD-SESSION-CAPTURE`): seven decisions (six at first, plus
  Decision 7 from the revision), the non-goals, an implementation plan, and
  open questions.
- `project/work_items/proposed/`, six items at first:
  - `WI-CLOUD-SESSION-PROBE`
  - `WI-LRH-CLI-RESOLUTION-REFERENCE`
  - `WI-EXPORT-ALLOWLIST-READY`
  - `WI-EXPORT-REFRESH-AND-STALENESS`
  - `WI-PLUGIN-BUNDLED-CLI` (depends on the probe)
  - `WI-EXPORT-CLAUDE-CLOUD-BRANCH` (depends on the probe)
- PR: https://github.com/xenotaur/logical_robotics_harness/pull/863

Revision, same session: the user described the delivery flow two real
cloud sessions used (copy to the scratchpad, offer download, download, then
a manual local `mkdir -p` / `mv` / `chmod 600` into the archive) and asked
which steps could be automated. The user approved revising the PR:

- **Decision 5 revised.** In a cloud session with a file-delivery tool, the
  skill exports with `--out` straight to the delivery location instead of
  writing to the in-container archive and then copying.
- **Decision 7 added.** A local `lrh conversation import-claude-export`
  command files the download. The alternatives recorded with it: manual
  commands, picking downloads up in `lrh sessions sync`, a folder watcher,
  teleport, and the desktop app's Export.
- **Seventh work item added:** `WI-CLAUDE-EXPORT-LOCAL-IMPORT`.
- **Teleport added to `WI-CLOUD-SESSION-PROBE`**, as the only candidate for
  skipping the download.
- **`WI-EXPORT-CLAUDE-CLOUD-BRANCH` revised** to match Decision 5, with the
  import command in its report.
- **Audit §1.4, §2 and the alternatives table updated.** The update records
  two findings: `SKILL.md:296` cites a stale line range for the exporter's
  path rule, and the desktop app listed no cloud sessions among its 40 most
  recent.

Review fixes, same session: the hosted reviewers' four threads and a
substitute self-review of `6c15011a` (record
`2026_11_07_06_32_39_LRH_CLOUD_SESSION_CAPTURE_SELFREVIEW`) found nothing
blocking. The user chose to fix all nine findings in one push:

- **Bundled launcher.** `WI-PLUGIN-BUNDLED-CLI` no longer passes the copy
  through `PYTHONPATH`, which `python3 -I` ignores. A bootstrap adds the
  copy to `sys.path` itself, with tests against a shadowing working
  directory and `PYTHONPATH`. The item now depends on
  `WI-LRH-CLI-RESOLUTION-REFERENCE`.
- **Refresh.** The manifest records the render options, and `--refresh`
  requires them to match (Decision 6, audit §2.7,
  `WI-EXPORT-REFRESH-AND-STALENESS`). Closeout and work-remains read cloud
  status only from the CLI's `cloud_session` field.
- **Import.** The "grown same-source" rule couldn't be checked without the
  original transcript. It is replaced by "identical is a no-op, refuse
  otherwise", plus an explicit, manifest-only `--replace-older` (Decision
  7, audit §2.6, `WI-CLAUDE-EXPORT-LOCAL-IMPORT`).
- **Probe.** The allow-rule test gains a control run without the rule.
- **Allowlist.** The settings snippet is tied to the launcher name, in
  Decision 3, `WI-EXPORT-ALLOWLIST-READY` and `WI-PLUGIN-BUNDLED-CLI`.
- **This record** now reflects seven decisions and seven items.

Second review fixes, 2026-11-11: `/lrh-confirm-fixes` resolved the three
remaining threads at `1293bed1`. Its substitute self-review of `26d7f5de`
(record `2026_11_09_05_07_28_LRH_CLOUD_SESSION_CAPTURE_SELFREVIEW`) found
seven non-blocking issues, and the user chose to fix all of them:

- **Probe.** The control command gains `--current`; without it the CLI
  exits 2. The teleport step runs `current-claude-session-id` inside the
  teleported session and records compaction status in place of an
  unmeasurable completeness check.
- **Resolution order (Decision 2, audit §2.2,
  `WI-LRH-CLI-RESOLUTION-REFERENCE`).** The order is now: an LRH
  checkout, then the bundled launcher, then `lrh` on PATH, so a lagging
  setup-script install can't shadow the bundle. `WI-PLUGIN-BUNDLED-CLI`
  confirms or revises it.
- **Stale-export check.** It takes the export's path from the export
  skill's own report in the session (Decision 6,
  `WI-EXPORT-REFRESH-AND-STALENESS`).
- **`--refresh`.** It treats an unchanged export as a no-op.
- **One timestamp.** The exporter uses a single timestamp for the archive
  month and for `exported_at` (Decision 7,
  `WI-CLAUDE-EXPORT-LOCAL-IMPORT`).
- **Metadata.** The proposal's `updated_on`, the cloud-branch item's
  decision list, and the PR description are updated.
- **Allowlist.** `WI-EXPORT-ALLOWLIST-READY` now says an allowed `--out`
  can point inside the working tree.

Third review fixes, 2026-11-12: a second `/lrh-confirm-fixes` run found
no open threads and green CI at `6120e073`. Its substitute self-review
(record `2026_11_12_06_03_03_LRH_CLOUD_SESSION_CAPTURE_SELFREVIEW`) found
four non-blocking issues, and the user chose to fix all of them:

- **Import dependency.** `WI-CLAUDE-EXPORT-LOCAL-IMPORT` now depends on
  `WI-EXPORT-REFRESH-AND-STALENESS`, so `--replace-older` doesn't ship
  before the render-option fields it compares. The proposal's plan item
  7 now says so.
- **Refresh path.** The offered stale-export refresh passes the reported
  path with `--out`, so a month rollover can't create a second export.
- **Probe.** The PyYAML check runs `python3 -I`, like the launcher.
- **Directory helper.** `WI-EXPORT-ALLOWLIST-READY` and
  `WI-CLAUDE-EXPORT-LOCAL-IMPORT` cross-reference one shared 0700
  directory helper.

Fourth review fix, 2026-11-13: a third `/lrh-confirm-fixes` run found no
open threads and green CI at `c54374d0`. Its substitute self-review
(record `2026_11_13_00_21_41_LRH_CLOUD_SESSION_CAPTURE_SELFREVIEW`) found a
blocking flaw: Decision 1 put the launcher in the plugin's top-level `bin/`,
and claude.ai and Cowork don't install a plugin that has one. The audit
had quoted only the first sentence of the doc row that says so, and the
repo's exporter already refuses a `bin/`.

The user asked for an investigation first. No doc gives a reason for the
rule. claude.ai's org-sync page names `scripts/` called as
`${CLAUDE_PLUGIN_ROOT}/scripts/<name>` as the alternative, so a later
rejection of that route looks unlikely. The user chose to revise to it:

- **Decision 1, audit §1.1 and §2.1.** The CLI is bundled under
  `plugins/lrh/scripts/`, and skills run
  `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py"`. A top-level
  `bin/` is recorded as rejected, the audit quote is corrected, and the
  sources are listed.
- **Decision 2 and `WI-LRH-CLI-RESOLUTION-REFERENCE`.** The launcher slot
  is the bootstrap path. It falls through when the placeholder isn't
  substituted.
- **Decision 3, audit §2.3 and `WI-EXPORT-ALLOWLIST-READY`.** The snippet
  covers only the `lrh conversation …` form. It covers neither the
  checkout form nor the launcher's absolute, account-specific path.
- **`WI-CLOUD-SESSION-PROBE`.** It tests path substitution and a bundled
  script instead of `bin/` on PATH, plus a wildcard rule for the launcher
  path.
- **`WI-PLUGIN-BUNDLED-CLI`.** Rewritten for the `scripts/` route. It
  keeps the exporter's `bin/` refusal.

No code, skill, or documentation behavior changed.

# Validation

- `lrh validate`: 0 errors, 0 warnings, after the proposal and again after
  the work items.
- `lrh work-items readiness <ID>`: `prompt_ready: yes` for all six, and
  again after the revision for the new and changed items
  (`WI-CLAUDE-EXPORT-LOCAL-IMPORT`, `WI-CLOUD-SESSION-PROBE`,
  `WI-EXPORT-CLAUDE-CLOUD-BRANCH`).
- `lrh validate`: 0 errors, 0 warnings after the revision.
- `lrh prompt check-execution --slug <slug> --work-item AD_HOC`: no prior
  record for `lrh-cloud-session-capture` or any of the six WI slugs.
- After the review fixes: `lrh validate` and `lrh work-items readiness` for
  the five changed items (results in the self-review record).

# Follow-up

- Start with `WI-CLOUD-SESSION-PROBE`. It decides whether
  `WI-PLUGIN-BUNDLED-CLI` goes ahead and confirms the environment-variable
  facts behind `WI-EXPORT-CLAUDE-CLOUD-BRANCH`.
- The proposal's open questions are unresolved:
  - the bundled launcher's name;
  - whether to bundle PyYAML;
  - a `claude-cloud:` pointer;
  - whether `closeout-sync` should skip mirroring in cloud sessions;
  - whether teleport writes a complete local transcript (the probe answers
    this);
  - whether `lrh sessions sync --exports-dir` should later pick up
    downloads;
  - Codex Cloud export;
  - whether to group the seven items under a workstream.
- Coordinate with `WI-EXPORT-SKILL-FAMILY-RENAME` (skill paths) and
  `WI-CLOSEOUT-EXPORT-SCOPE` (the closeout Step 8 offer).
- `session_transcript: pending`: update to this session's `claude-app:`
  pointer at closeout.
