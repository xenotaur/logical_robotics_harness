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

Fifth review fixes, 2026-11-13: a fourth `/lrh-confirm-fixes` run found no
open threads and green CI at `c66df640`. Its substitute self-review
(record `2026_11_13_01_25_04_LRH_CLOUD_SESSION_CAPTURE_SELFREVIEW`) found
six issues, one blocking. The user chose to fix all six:

- **Launcher path placement (blocking).** Claude Code substitutes
  `${CLAUDE_PLUGIN_ROOT}` only in SKILL.md content and `allowed-tools`
  rules, so the launcher path now lives in each consuming SKILL.md body,
  never only in the shared reference. This changes Decision 2, audit
  §2.2, `WI-LRH-CLI-RESOLUTION-REFERENCE` and `WI-PLUGIN-BUNDLED-CLI`.
- **Plugin-skill `allowed-tools`.** Decision 3 now has two channels: the
  plugin launcher is pre-approved by `lrh-export-claude`'s own
  `allowed-tools` (pending the probe), and the setup-script route by
  repository rules. The audit's "plugins can't declare permissions" claim
  is corrected.
- **Probe.** It tests the `allowed-tools` grant, quoted and unquoted, with
  a control, and confirms that a `references/` file stays literal. Its
  launcher-path repository rule drops the trailing wildcard that couldn't
  match.
- **Audit quote.** The "generally skip the classifier" text, which the
  page no longer has, is replaced with the current decision-order
  exceptions.
- **Limits.** Cloud threads in a project are added to Decision 3's limits,
  the audit and `WI-EXPORT-ALLOWLIST-READY`.
- **Metadata.** The proposal's `updated_on` is now 2026-11-13. The audit's
  253-file estimate now says it excludes `src/lrh/skills`.

Sixth review fixes, 2026-11-13: a fifth `/lrh-confirm-fixes` run found no
open threads and green CI at `bfa44896`. Its substitute self-review
(record `2026_11_13_17_56_25_LRH_CLOUD_SESSION_CAPTURE_SELFREVIEW`) found
nothing blocking, with two should-fix findings and five nits. The user
chose to fix all seven:

- **Grant scope.** The `allowed-tools` grant clears at the user's next
  message, so it covers only a user-typed invocation without `--force`.
  Runs that wait for confirmation, including the closeout refresh offer,
  go to the classifier. Decisions 1 and 3, audit §1.2 and
  `WI-PLUGIN-BUNDLED-CLI` now say so, and the false "later turn gets the
  grant again" note is gone.
  - Re-invoking the skill after a confirmation is now an open question.
  - The probe adds a confirm-then-run turn.
- **Account-segment wildcard.** A `*` matches any text, so a repository
  rule can't wildcard just the account segment. It is now a rejected
  alternative, and its probe step and open question are removed.
- **Bundle contents.** The copy keeps `src/lrh/skills/{__init__,exporter,installer}.py`,
  which the CLI imports, and the estimate is now about 256 files.
- **Doc currency.**
  - The probe's question count is fixed.
  - The plugin-settings citation and the cloud network level are updated
    to the 2026-11-13 docs.
  - The synced-skill grant rule is marked as unconfirmed for plugin
    skills.
  - Setup installs are to use the `git+https` form, since the proxy
    blocks archive fetches of unattached repositories.

Seventh review fixes, 2026-11-13: a sixth `/lrh-confirm-fixes` run found
no open threads and green CI at `f537e2e3`. Its substitute self-review
(record `2026_11_13_19_14_52_LRH_CLOUD_SESSION_CAPTURE_SELFREVIEW`) found
nothing blocking: two should-fix findings in the probe and one nit. The
user chose to fix all three:

- **Probe skill D.** Its own text waits for "yes", it is invoked in one
  turn, and the reply comes in the next turn without invoking it again.
  The old confirm-then-run step invoked the skill after the reply, which
  re-applies the grant.
- **Probe skill E.** It tests the shipped rule shape: an interpreter, an
  absolute path and a trailing ` *`. `WI-PLUGIN-BUNDLED-CLI` and Decision
  3 now add the `allowed-tools` rules only if E passes.
- **PyYAML.** Every CLI command needs it, through `lrh.agent_skills_status`,
  not just `inspect-export`. A launcher without it would crash instead of
  falling through. The audit, the proposal's open question and
  `WI-PLUGIN-BUNDLED-CLI` say so.

No code, skill, or documentation behavior changed.

Eighth review fixes, 2026-11-13: a seventh `/lrh-confirm-fixes` run found
no open threads and green CI at `20069ab7`. Its substitute self-review
(record `2026_11_13_21_34_40_LRH_CLOUD_SESSION_CAPTURE_SELFREVIEW`) found
nothing blocking: three cross-item gaps and one nit. The user chose to fix
all four:

- **Subshell on both routes.** Claude Code splits compound commands on
  newlines and requires every subcommand to be allowed, so the launcher's
  `allowed-tools` rule wouldn't cover today's `( umask 077 … )` Step 4
  either. Decision 3 now applies the 0700 directories and plain commands
  to both routes. `WI-PLUGIN-BUNDLED-CLI` depends on
  `WI-EXPORT-ALLOWLIST-READY`, and the audit's "not documented" wording
  now cites `permissions.md`.
- **Second order trade-off.** Once the launcher comes before PATH,
  repository rules for `lrh conversation …` stop matching, so confirmed
  runs lose pre-approval for teams that relied on them. Decision 2, the
  audit and `WI-PLUGIN-BUNDLED-CLI` record it.
- **Other targets.** The Codex and Antigravity renderers copy frontmatter
  unchanged, so `WI-PLUGIN-BUNDLED-CLI` now keeps the Claude-only
  `allowed-tools` rules out of those copies, or records why they're
  harmless.
- **Size.** `src/lrh` is about 2.7 MiB of tracked files, not 3.3 MB.

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
