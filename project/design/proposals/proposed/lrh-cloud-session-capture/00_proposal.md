---
id: PROP-LRH-CLOUD-SESSION-CAPTURE
type: design_proposal
title: "Transcript capture from Claude Code cloud sessions"
status: proposed
created_on: 2026-11-06
updated_on: 2026-11-11
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/audits/2026-11-06-cloud-session-export-audit.md
  - project/design/proposals/adopted/lrh-claude-conversation-exporter/00_proposal.md
  - project/design/proposals/adopted/lrh-session-archive-sync/00_proposal.md
  - project/design/proposals/proposed/lrh-export-session-id-skill-families/00_proposal.md
  - project/work_items/resolved/WI-SKILLS-CLAUDE-PLUGIN-EXPORT.md
  - docs/how-to/use-lrh-with-agent-assistants.md
---

# Transcript capture from Claude Code cloud sessions

## Summary

Make `/lrh-export-claude` work in Claude Code cloud sessions
(claude.ai/code) without manual setup or repeated permission prompts:

- `lrh` is already present when the skill runs. It ships inside the plugin,
  with a setup-script install as the fallback.
- The export commands can be pre-approved by exact allow rules.
- The CLI reports whether the session is a cloud session.
- In a cloud session the skill writes the export straight to a location
  the session can deliver from, and offers it for download.
- A local `lrh conversation import-claude-export` command files the
  downloaded export into the private archive, replacing manual `mkdir`,
  `mv` and `chmod`.
- A re-export that only adds to an earlier export no longer needs
  `--force`.

## Background / Motivation

On 2026-11-06 a user in a cloud session on `xenotaur/taurworks` typed
`/lrh:lrh-export-claude`. The export eventually verified
(`match_source_grew`, exit 0, mode 0600), but it took manual recovery and
three permission round trips to get there:

- `lrh` wasn't installed. The plugin had synced the skills but not the CLI
  they call.
- The agent found and cloned `xenotaur/logical_robotics_harness` into the
  scratchpad itself. Auto mode's classifier denied the clone, then denied
  running the cloned CLI against the session's Claude data.
- The default archive was written inside the container, which is discarded
  when the session ends.
- The agent improvised a download through the scratchpad. The download lost
  the file's 0600 mode.

The findings, each tied to a repository file, CLI help text, or Claude Code
documentation, are in `project/audits/2026-11-06-cloud-session-export-audit.md`.
That note is the evidence base for this proposal and isn't repeated here.

This needs doing now because cloud sessions became a supported LRH surface
when the plugin marketplace shipped (`WI-SKILLS-CLAUDE-PLUGIN-EXPORT`,
`docs/how-to/use-lrh-with-agent-assistants.md` §5). Capturing transcripts
is how LRH keeps provenance (`session_transcript:` pointers, the private
archive), and today it silently fails to persist in the environment LRH
just started supporting.

The export skill's privacy and authority rules don't change:

- Never print transcript text.
- Never commit exports.
- Keep the confirmation gates for `--force` and for exports the model
  starts on its own.
- Never read Claude Code's internal storage directly; always go through the
  LRH exporter.

## Prior Art Check

### Duplication search
- In-repo: No existing implementation found. Nothing in `src/`, the
  proposals, workstreams, work items, or skill directories reads
  `CLAUDE_CODE_REMOTE` or ships a plugin `bin/`. Related, but not
  duplicates:
  - The setup-script note in `docs/how-to/use-lrh-with-agent-assistants.md` §5.
  - The checkout-only "Running `lrh`" fallback, copied into
    `src/lrh/skills/lrh-{export-claude,codex-export,antigravity-export}/SKILL.md`.
- Sibling repos: None identified.
- External libraries: None identified. The capability is LRH's own exporter
  plus Claude Code's documented plugin and settings surfaces.
- Recommendation: Proceed.

### Demand search
- Work items: None found that request this. These are adjacent, and the
  implementing items must coordinate with them:
  - `WI-LRH-EXPORT-DISPATCHER` (`/lrh-export` dispatcher).
  - `WI-EXPORT-SKILL-FAMILY-RENAME` (renames `lrh-codex-export` →
    `lrh-export-codex`).
  - `WI-CLOSEOUT-EXPORT-SCOPE` (wording of the closeout Step 8 `/export`
    offer).
- Proposals: `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` is adjacent. It
  governs skill naming and dispatch. This proposal governs runtime behavior
  in cloud environments, so they don't overlap.
- Backlog: No matching entries.
- Recommendation: No action. Cross-reference the adjacent items above.

## Design Decisions

### Decision 1: How `lrh` gets into a cloud container

Options considered:

- **Publish to PyPI.** LRH isn't published (`pypi.org/pypi/lrh/json` returns
  404), and `scripts/publish` says publishing is "not yet supported". Even
  once published, the CLI would drift from skills that auto-sync from
  `main`.
- **A setup script only.** It's documented, and the classifier never sees
  it: setup runs before Claude Code launches, and `github.com` and
  `pypi.org` are on the default allowlist. But every environment has to
  configure it. Its snapshot cache lasts about seven days, so the CLI can
  lag the skills by up to a week. And it does nothing for a user who hasn't
  set it up.
- **The skill clones and bootstraps LRH itself.** This triggers the
  classifier's "Code from External" denial. It also turns an export command
  into a hidden clone.
- **Bundle the CLI in the plugin.** The plugin exporter writes a launcher
  under `plugins/lrh/bin/`, plus a copy of `src/lrh` taken from the same
  commit as the skills. The plugin reference documents `bin/` as "on the
  Bash tool's PATH while the plugin is enabled". The copy is small: 3.3 MB
  and 269 files, against claude.ai's limits of 200 MB and 5,000 files.

**Chosen: bundle the CLI in the plugin, and keep a setup-script install as
the documented fallback.** Bundling removes version drift between skills and
CLI, the install step, and the clone, so the classifier has nothing to deny.
It is gated on a cloud probe (`WI-CLOUD-SESSION-PROBE`), because a synced
plugin's `bin/` in cloud sessions is undocumented. The setup-script docs
will pin a ref and state the snapshot-cache drift.

### Decision 2: What the skill does when it can't find `lrh`

Options considered:

- **Discover and clone the repository.** This is today's emergent behavior,
  rejected for the reasons in Decision 1.
- **Stop with an exact remedy.** This is chosen. One shared reference
  replaces the three copied "Running `lrh`" sections. It checks, in order:
  1. `PYTHONPATH=src python3 -m lrh.cli.main`, only inside an LRH checkout,
     which keeps the skills' existing advice to prefer the checkout's own
     code over a possibly different editable install;
  2. the plugin's bundled launcher, once it ships;
  3. `lrh` on PATH;
  4. otherwise, stop and print the setup-script line and the docs anchor.

  The launcher comes before `lrh` on PATH because it ships from the same
  commit as the plugin's skills, while a setup-script install can lag them
  by up to about seven days. Putting PATH first would let that stale
  install shadow the bundle and undo Decision 1. The cost: in a desktop
  session with the plugin enabled, the launcher also beats a newer local
  install. `WI-PLUGIN-BUNDLED-CLI` confirms or revises this order once it
  settles the launcher's name, and records that trade-off.

A one-time bootstrap clone stays possible, but only as its own step that
the user confirms, named for what it does ("clone LRH into the
scratchpad"). No command whose name sounds read-only may install, clone, or
overwrite anything.

### Decision 3: Permissions without classifier denials

Facts this decision rests on (sources in the audit, §1.2):

- Allow rules skip the classifier.
- Ask rules always prompt.
- Cloud sessions read only the repository's `.claude/settings.json`, and
  only in single-repo sessions.
- Plugins can't declare permissions.
- The classifier never reads `autoMode` configuration from project
  settings.

Options considered:

- **Plugin-declared permissions.** Not supported.
- **`autoMode.environment` trusted sources.** Not read from project
  settings, and user settings don't reach cloud sessions.
- **Exact allow rules in the client repository's `.claude/settings.json`.**
  This is chosen.

**Chosen: publish an exact-rule settings snippet, and change the commands so
the rules match.**

- **CLI:** create export and archive directories with mode 0700. Today
  `claude_export.py:144` uses a plain `mkdir`, and the skill relies on
  `( umask 077 … )` to protect the directories.
- **Skill:** drop the subshell and run plain `lrh conversation …` commands.
- **Snippet:** allow `lrh conversation current-claude-session-id *`,
  `lrh conversation export-claude-session *` and
  `lrh conversation inspect-export *`, plus an `ask` rule for `--force`.
  `/lrh-config-skills`, or a sibling command, may offer to write it, with
  confirmation. Exact rules match the command word, so if the bundled
  launcher (Decision 1) isn't named `lrh`, the snippet needs the same rules
  for the launcher's name. `WI-PLUGIN-BUNDLED-CLI` owns that update.
- **Docs:** state that multi-repo sessions still prompt.

### Decision 4: How the skill detects a cloud session

Options considered:

- Path or OS heuristics: rejected as guessing.
- The undocumented `CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE`: rejected.
- **The documented `CLAUDE_CODE_REMOTE=true`, read by the CLI**: chosen.

**Chosen:** `lrh conversation current-claude-session-id --format json` gains
two metadata-only fields:

- `cloud_session`: true when `CLAUDE_CODE_REMOTE == "true"`.
- `remote_session_id`: from `CLAUDE_CODE_REMOTE_SESSION_ID`, the documented
  `cse_`-prefixed cloud session ID.

The skill branches on these fields and never reads the environment itself,
so the detection logic is tested once, in Python.

### Decision 5: Where a cloud export goes

Facts this decision rests on:

- Each cloud session gets a fresh VM.
- git is the only documented way anything persists past the session, and
  exports must never be committed.
- No way to download a file from a cloud session is documented.

Options considered:

- **Write only to the in-container archive.** Rejected: the copy is lost
  silently.
- **Write to the archive, then copy to a delivery location.** This was the
  first draft of this decision. Rejected after the delivery flow used in
  two real cloud sessions was reviewed: the in-container archive is thrown
  away with the container, so it adds a second file and a second command to
  approve, and protects nothing.
- **Write straight to a delivery location with `--out`.** Chosen. It is the
  same exporter code path. The file is 0600 from its first byte
  (`claude_export.py:159-180`), and `inspect-export --source` works against
  it as it does against an archive file.
- **Commit to a private branch.** Rejected: it violates the
  never-commit-exports rule.

**Chosen:** in a cloud session, when the session offers a file-delivery tool
(checked at run time, never assumed):

- The skill exports with `--out <delivery-dir>/<source-id>.md`. The delivery
  directory is the session's scratchpad, or another location that tool can
  send from, and never a path inside the repository working tree.
- It verifies the file with `inspect-export`, then offers it for download.
- The report gives the one local command that files the download
  (`lrh conversation import-claude-export <file>`, Decision 7). The fallback
  when `lrh` isn't installed locally is `chmod 600 <file>`.

When there is no delivery tool, the skill exports to the default archive as
it does today, says plainly that the copy is lost when the session ends, and
does not improvise a delivery route.

### Decision 6: Snapshot timing and re-export

Options considered:

- **A SessionEnd hook that auto-exports.** Rejected. The hook budget is 1.5
  seconds by default and 60 at most. Whether a hook can finish before the
  VM is torn down is undocumented. And its output would land in the
  container, which is discarded.
- **Keep `--force` for every re-export.** Rejected: it asks every time, even
  when the only change is that the transcript grew.
- **A narrow `--refresh` mode, plus staleness flags.** Chosen.

**Chosen:**

- **Recorded render options.** The export manifest records
  `include_subagents` and `include_system_attachments`. Today it records
  neither (`claude_export.py:119-135`), so nothing could tell an export that
  included subagent transcripts from one that didn't.
- **`--refresh` on `export-claude-session`.** It overwrites only an existing
  export of the same source ID, with the same recorded render options,
  whose recorded source is a byte prefix of the current transcript — the
  case `inspect-export` already reports as `match_source_grew`. An export
  that already matches the transcript exactly (`match`) is a no-op. It
  refuses everything else, including exports that predate the recorded
  options.
  Because it can't destroy a different export, or quietly drop content an
  earlier export included, it doesn't trigger the `--force` gate, and its
  name promises exactly that.
- **Staleness flags.** In a cloud session, `/lrh-closeout` Step 8 and
  `/lrh-work-remains` item 11 flag "no export" or "export is N bytes stale"
  (from `inspect-export`'s grown-by count), and offer a refresh plus
  delivery. They find the export from the path `lrh-export-claude` reported
  earlier in the session, never by recomputing the archive path in skill
  text.
- **Closeout report.** It says when `lrh sessions closeout-sync` wrote to an
  archive that won't survive the session.

### Decision 7: How a downloaded export reaches the local archive

The download itself can't be automated: the browser does it, and Claude
Code documents no download, export, or API route for cloud transcripts.
Today the user files the download by hand, for example `mkdir -p` of
`~/.local/share/lrh/session-archive/claude/exports/YYYY/MM`, then `mv` from
`~/Downloads`, then `chmod 600`.

Options considered:

- **Manual commands, or the skill printing them pre-filled.** Rejected.
  - `mkdir -p` under a 022 umask creates the folders 0755.
  - The file stays readable by others until the `chmod`.
  - `LRH_SESSION_ARCHIVE_ROOT` is ignored.
  - Nothing checks the file.
  - Pre-filled commands would copy the exporter's path rule into skill
    text. That rule is the export's UTC year and month plus the sanitized
    source ID, at `claude_export.py:505-515`. The skill already refuses to
    copy it, and its line citation for that rule (`SKILL.md:296`, which
    cites `488-498`) has already gone stale.
- **A local import command.** Chosen.
- **Pick up exports from `~/Downloads` in `lrh sessions sync` or its weekly
  launchd schedule.** Deferred.
  - The file could sit unprotected for up to a week.
  - `sync` deliberately assumes no default exports location.
  - It would reuse the import command's filing code anyway.
- **A folder watcher that files downloads on arrival.** Rejected: a
  background process moving files silently, Mac-only, and unlike LRH's
  render-for-inspection `lrh sessions schedule`.
- **Teleport the cloud session (`claude --teleport`) and export locally.**
  This would skip the download entirely. Not chosen yet:
  - It needs a clean checkout of the same repository, a pushed branch, and
    the same account.
  - Compacted messages "aren't copied".
  - Whether it writes a local transcript file, and under which session ID,
    is undocumented.

  Added to `WI-CLOUD-SESSION-PROBE`.
- **The desktop app's session Export.** Not viable now. None of the 40 most
  recent sessions the desktop app listed on 2026-11-06 was a cloud session.

**Chosen:** add `lrh conversation import-claude-export <file>`. It:

- reads `exported_at` and `source_id` from the file's own frontmatter;
- computes the destination with a helper shared with the exporter, by
  factoring out `claude_export.py:505-515`. The exporter is changed to take
  its path's year and month and its manifest `exported_at` from one
  timestamp; today they come from two clock reads (`:109-110` and
  `:505-507`), which can disagree at a month boundary;
- resolves the root through `resolve_claude_archive_root`, so
  `LRH_SESSION_ARCHIVE_ROOT` and `--archive-root` apply;
- creates missing folders 0700 and writes the file 0600 from the first byte
  (not `copy2` then `chmod`, as `codex_archive.py:479-480` does);
- checks the manifest;
- treats an identical existing file as a no-op and refuses any other
  existing file by default;
- with an explicit `--replace-older`, replaces an older snapshot of the same
  session: same `source_id` and recorded render options, with a later
  `exported_at` and a larger `source_byte_count`. It can't use
  `--refresh`'s prefix check, which needs the original transcript, and that
  stayed in the cloud container. The flag's help says it is a manifest-only
  check;
- copies by default; deleting the download takes an explicit `--move`.

The precedent is `lrh conversation import-codex-exports`
(`codex_archive.py:224`).

## Non-Goals

- Does not add Codex Cloud transcript export. That needs a transport LRH
  doesn't have: `lrh-codex-export` depends on the local Codex app-server.
  It is recorded under Open Questions.
- Does not publish LRH to PyPI.
- Does not relax any privacy rule. Exports are never committed, transcript
  text is never printed, and the `--force` and model-initiated
  confirmation gates stay.
- Does not read Claude Code's internal transcript storage directly. All
  reads still go through `lrh conversation export-claude-session`.
- Does not solve permissions for multi-repo cloud sessions, which don't
  read project settings.
- Does not rename skills or add dispatchers. That is
  `PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES`.
- Does not decide whether `remote_session_id` becomes a new
  `session_transcript:` pointer scheme.

## Implementation Plan

Medium scope, seven work items. No workstream unless the user wants one; see
Open Questions.

1. **`WI-CLOUD-SESSION-PROBE`** — first. Run a real cloud session and check:
   - whether a synced plugin's `bin/` is on PATH;
   - whether `python3 >= 3.11` and PyYAML are present;
   - which of `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_HOST_SESSION_ID` and
     `CLAUDE_CODE_REMOTE_SESSION_ID` are set;
   - whether a narrow `lrh conversation …` allow rule actually skips the
     classifier, tested against a command the classifier denies without the
     rule;
   - whether teleporting the session writes a complete local transcript
     that `export-claude-session` can read, and under which session ID.

   Record the results as an execution record, and update the audit.
2. **`WI-LRH-CLI-RESOLUTION-REFERENCE`** — independent. One shared
   CLI-resolution reference for the three export skills, the stop-with-remedy
   path, and setup-script docs that state the cache drift.
3. **`WI-EXPORT-ALLOWLIST-READY`** — independent:
   - CLI creates directories with mode 0700;
   - the skill drops the subshell;
   - the allow/ask settings snippet, optionally offered by
     `/lrh-config-skills`.
4. **`WI-EXPORT-REFRESH-AND-STALENESS`** — independent. Recorded render
   options in the manifest, the `--refresh` mode, and the stale-export
   checks in closeout and work-remains. The checks read `cloud_session`
   from item 6's CLI output and stay dormant until it exists.
5. **`WI-PLUGIN-BUNDLED-CLI`** — after the probe and item 2. The exporter
   writes the `bin/` launcher and the copied `src/lrh`, with a packaging
   test. The launcher runs `python3 -I` and adds the copy to `sys.path`
   itself, since `-I` ignores `PYTHONPATH`. Settles the launcher's name and
   whether to copy in PyYAML, and extends item 3's snippet if the name
   isn't `lrh`.
6. **`WI-EXPORT-CLAUDE-CLOUD-BRANCH`** — after the probe, which settles the
   environment-variable facts. Adds the `cloud_session` and
   `remote_session_id` fields, and the skill's cloud branch: export with
   `--out` to the delivery location, offer the file, and report the local
   import command.
7. **`WI-CLAUDE-EXPORT-LOCAL-IMPORT`** — independent. Adds
   `lrh conversation import-claude-export` and the path helper it shares
   with the exporter, and fixes the stale `SKILL.md:296` line citation.

Coordination: if `WI-EXPORT-SKILL-FAMILY-RENAME` lands first, items 2 and 6
target the renamed skill paths.

## Cross-References

- Evidence: `project/audits/2026-11-06-cloud-session-export-audit.md`
- Exporter design: `project/design/proposals/adopted/lrh-claude-conversation-exporter/00_proposal.md`
- Archive design: `project/design/proposals/adopted/lrh-session-archive-sync/00_proposal.md`
- Naming and dispatch: `project/design/proposals/proposed/lrh-export-session-id-skill-families/00_proposal.md`
- Plugin delivery: `project/work_items/resolved/WI-SKILLS-CLAUDE-PLUGIN-EXPORT.md`
- User docs to update: `docs/how-to/use-lrh-with-agent-assistants.md` §5
- Claude Code docs relied on: `env-vars`, `cloud-environments`,
  `plugins-reference`, `permission-modes`, `auto-mode-config`, `settings`,
  and `hooks` at code.claude.com/docs (fetched 2026-11-06; quotes in the
  audit).

## Open Questions

- Is a synced plugin's `bin/` on PATH in cloud sessions? (The probe answers
  this; Decision 1 depends on it.)
- What should the bundled launcher be called? A plugin `lrh` would shadow a
  user's local `lrh` in desktop sessions where the plugin is enabled. A
  distinct name, such as `lrh-plugin`, needs a lookup rule in the shared
  reference.
- Should the bundle include PyYAML, or rely on the image? The one taurworks
  observation found it present.
- Should `remote_session_id` back a `claude-cloud:` `session_transcript:`
  pointer?
- Should `lrh sessions closeout-sync` skip mirroring, rather than only
  report, when `cloud_session` is true?
- Does teleporting a cloud session (`claude --teleport`) write a complete
  local transcript? If it does, exporting locally after teleport would skip
  the download entirely (the probe answers this; see Decision 7).
- Should `lrh sessions sync --exports-dir` later pick up LRH exports from a
  downloads folder, reusing the import command's filing code?
- How could Codex Cloud tasks be exported, given there is no local
  app-server? `/lrh-closeout` already names a `codex-cloud:` pointer that
  nothing produces.
- Should these seven items be grouped under a workstream?
