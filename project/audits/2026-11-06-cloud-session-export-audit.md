# Cloud-session transcript export audit (2026-11-06)

Investigation only. Nothing here is implemented yet. Trigger: a claude.ai/code
cloud session on `xenotaur/taurworks` needed many manual steps, and three
permission round trips, to run `/lrh:lrh-export-claude`.

Sources: repository files (cited by path), `lrh conversation ... --help`
output from this checkout, and Claude Code documentation fetched 2026-11-06
(cited by URL). Where the docs are silent, this note says "undocumented" and
does not guess.

---

## 1. Findings

### 1.1 Making the CLI available

- **The plugin ships skills only.** `plugins/lrh/` has `.claude-plugin/` and
  `skills/`, and nothing else: no `bin/`, no `hooks/`.
- **Plugins can ship executables.** The plugin reference says of `bin/`:
  "Files here are on the Bash tool's PATH while the plugin is enabled"
  (<https://code.claude.com/docs/en/plugins-reference.md#standard-layout>).
  Whether that also holds for an account-synced plugin in a cloud session is
  undocumented. The synced plugin itself loading in cloud sessions is already
  undocumented-but-observed (`docs/how-to/use-lrh-with-agent-assistants.md`
  §5).
- **Bundling is small.** `src/lrh` is 3.3 MB and 269 files. claude.ai's plugin
  limit is 5,000 files and 200 MB (same doc §5). The only runtime dependency is
  `PyYAML` (`pyproject.toml`). `inspect-export` imports it
  (`src/lrh/conversations/export_inspector.py`). In the taurworks session
  `PYTHONPATH=src python3 -m lrh.cli.main conversation inspect-export`
  succeeded, so that image had PyYAML. That is one observation, not a
  guarantee.
- **No published package.** `pip index versions lrh` finds nothing, and
  `https://pypi.org/pypi/lrh/json` returns 404. `scripts/publish` says
  "Publishing not yet supported".
- **Setup scripts run before Claude Code launches**, as root, with the default
  "Trusted" network level. That level's allowlist includes `github.com`,
  `codeload.github.com`, `pypi.org`, and `files.pythonhosted.org`
  (<https://code.claude.com/docs/en/cloud-environments.md#setup-scripts>,
  `#default-allowed-domains`). An install run there never goes through the
  permission classifier.
- **The setup-script route drifts.** Setup results under about five minutes
  are snapshotted and reused until the script changes or about seven days
  pass (`cloud-environments.md#environment-caching`). The plugin syncs from
  `main` on every merge (doc §5, "Updating"). So a `pip install git+...@main`
  done by setup can be up to about a week older than the skills that call it.
- **The skill's fallback assumes a checkout.** The "Running `lrh`" section,
  repeated in `lrh-export-claude`, `lrh-codex-export` and
  `lrh-antigravity-export`, says to run `PYTHONPATH=src python3 -m
  lrh.cli.main` "from an LRH checkout". In a client repo there is none. That
  pushed the agent to find and clone the repo itself.
- **The docs already recommend a setup-script install**
  (`docs/how-to/use-lrh-with-agent-assistants.md`, "Install the `lrh` CLI in
  the cloud environment"). The skill doesn't point to it.

### 1.2 Permissions

- **Allow rules skip the classifier.** "Allow rules generally skip the
  classifier. The exceptions are protected-path writes, critical-path
  removals, and shell commands with per-command allowed domains"
  (<https://code.claude.com/docs/en/permission-modes.md#how-the-classifier-evaluates-actions>).
  Ask rules always prompt, even in auto mode
  (<https://code.claude.com/docs/en/auto-mode-config.md#add-a-human-checkpoint>).
- **Only one settings file reaches a cloud session.** User
  `~/.claude/settings.json` and `.claude/settings.local.json` are not read
  there. The repo's shared `.claude/settings.json` is read only in
  single-repo sessions
  (<https://code.claude.com/docs/en/settings.md#settings-in-cloud-sessions>).
- **Plugins can't grant permissions.** In a plugin's `settings.json`, "Only
  `agent` and `subagentStatusLine` take effect" (`plugins-reference.md#settings`),
  and there is no documented way for a plugin to declare permissions.
- **`autoMode` config can't come from the repo.** The classifier reads
  `autoMode` only from user, managed, and `--settings` scopes, never from
  project settings (`auto-mode-config.md#where-the-classifier-reads-configuration`).
  User settings aren't read in cloud sessions, so in practice only managed
  settings could tune it there. (Inference from the two documented facts.)
- **The "Code from External" denial came from the mid-session clone.** By
  default auto mode trusts "only the working directory and the current repo's
  configured remotes" (`auto-mode-config.md`), and the LRH repo is neither for
  a taurworks session. Installing in setup, or shipping in the plugin's
  `bin/`, removes the clone. The second denial was for running the cloned CLI
  against `~/.claude` session data. An exact allow rule for the three
  commands would skip the classifier for that.
- **The skill's command shape defeats narrow allow rules.** Step 4 wraps the
  export in `( umask 077 \n lrh conversation export-claude-session ... )`. A
  rule like `Bash(lrh conversation export-claude-session *)` is written for a
  plain command, and whether a multi-line subshell matches it is not
  documented. The wrapper exists for directories only: the export file is
  already opened `0o600` (`src/lrh/conversations/claude_export.py:180`), but
  parent directories come from a plain `out.parent.mkdir(parents=True,
  exist_ok=True)` (`claude_export.py:144`) and follow the umask.
- **The client repo has no LRH allow rules.** This repo's
  `.claude/settings.json` allows `lrh prompt *`, `lrh request *` and others,
  but no `lrh conversation ...`. Client repos get none from LRH.

### 1.3 Detecting a cloud session

- **`CLAUDE_CODE_REMOTE` is the documented signal**: "Set automatically to
  `true` when Claude Code is running as a cloud session. Read this from a hook
  or setup script to detect whether you are in a cloud session"
  (<https://code.claude.com/docs/en/env-vars.md>).
- **`CLAUDE_CODE_REMOTE_SESSION_ID` holds the cloud session ID**, with a
  `cse_` prefix (`cloud-environments.md#link-output-back-to-the-session`).
  LRH's pointer code reads `CLAUDE_CODE_SESSION_ID` and
  `CLAUDE_CODE_HOST_SESSION_ID` only (`src/lrh/conversations/claude_session.py:14,55-56`),
  so a cloud session has no `claude-cloud:`-style pointer.
- **`CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE` is undocumented.** Don't use it.
- **A cloud session gets a fresh VM, and git is the only documented
  persistence**: "each session gets a fresh virtual machine", and "Anything
  you commit to the repo is available"
  (`cloud-environments.md#whats-available-in-cloud-sessions`,
  `#what-carries-over-from-your-setup`). Whether files survive after the VM
  is reclaimed is undocumented. The default archive
  (`~/.local/share/lrh/session-archive`, `prompt_workflow_sessions.py:571`)
  should be treated as lost when the session ends.

### 1.4 Delivery

- **No documented download path.** Claude Code's docs don't describe getting a
  file out of a cloud session, and the session scratchpad is documented only
  for local sessions (`claude-directory.md#session-scratchpad-directory`).
  The scratchpad copy plus file-delivery tool used in the taurworks session
  is a harness capability, not a documented contract. The skill should check
  for it at run time, not assume it.
- **Lost permissions are expected.** A browser download doesn't keep `0600`.
  `inspect-export` with no `--source` still checks the manifest, so a
  delivered copy can be re-verified locally.
- **There is no local import step.** `lrh conversation import-codex-exports`
  exists for Codex (`src/lrh/conversations/codex_archive.py:224`). No
  equivalent puts a downloaded Claude export into the local archive with
  `0600`. In two cloud sessions the user filed the download by hand:
  `mkdir -p ~/.local/share/lrh/session-archive/claude/exports/2026/11`,
  then `mv` from `~/Downloads`, then `chmod 600`.
  - Under a 022 umask the `mkdir -p` folders come out 0755.
  - The file stays readable by others until the `chmod`.
  - `LRH_SESSION_ARCHIVE_ROOT` is ignored.
  - The destination follows the exporter's path rule: the export's UTC
    year and month plus the sanitized source ID
    (`src/lrh/conversations/claude_export.py:505-515`). That rule lives
    inline in the CLI function, not in a reusable helper.
    `lrh-export-claude/SKILL.md:296` cites it as `claude_export.py:488-498`,
    a citation that has already gone stale.
  - The export's frontmatter carries `exported_at` and `source_id`
    (`claude_export.py:122,132`), so an import command can recompute the
    destination without looking at the filename.
- **The Codex import widens permissions briefly.** It copies with `copy2`,
  then `chmod`s (`codex_archive.py:479-480`), so the copy briefly carries
  the source's mode. The Claude exporter's `os.open(..., 0o600)` pattern
  (`claude_export.py:159-180`) avoids that window.
- **The in-container archive copy is pointless when delivery works.** It is
  thrown away with the container. Exporting with `--out` straight to the
  delivery location uses the same code path, writes the file 0600 from the
  first byte, and saves a copy step.
- **Teleport might skip the download, but it's unproven.** `claude
  --teleport` "loads the conversation into your terminal"
  (<https://code.claude.com/docs/en/claude-code-on-the-web.md#continue-a-cloud-session-in-your-terminal>).
  - Requirements: clean git state, a checkout of the same repository, a
    pushed branch, and the same account.
  - Compacted messages "aren't copied".
  - Whether teleport writes a local transcript file, and under which
    session ID, is undocumented.
- **The desktop app's session Export can't reach cloud sessions today.**
  Export writes a zip with the transcript and metadata, which
  `lrh sessions sync --exports-dir` already harvests for identity fields
  (`src/lrh/prompt_workflow_sessions.py:970`). But none of the 40 most
  recent sessions the desktop app listed on 2026-11-06 was a cloud session.

### 1.5 Snapshot timing

- **A SessionEnd hook can't be relied on.** "SessionEnd hooks share a
  1.5-second budget", raisable "up to 60 seconds" (<https://code.claude.com/docs/en/hooks.md>).
  Whether a SessionEnd hook can finish writing before a cloud VM is torn down
  is undocumented. Even if it could, a file left in the container is lost
  (1.3).
- **Re-exporting needs `--force`, which always asks.** `--force` overwrites
  any destination, so it always triggers the gate. A same-session re-export
  where the source has only grown is not a risky overwrite, but the CLI can't
  tell the two cases apart today.
- **Closeout already has an export offer** ("Offer the backend-appropriate
  local transcript archival/export workflow", `lrh-closeout/SKILL.md` Step
  8), and `lrh-work-remains` checks that it was made
  (`references/grounding-sources.md` item 11). Neither knows about cloud
  sessions, and neither checks whether an existing export is stale.
  `inspect-export --source` already reports `match_source_grew` with a byte
  delta, which is enough to detect a stale export without new reading code.
- **Closeout's archive sync is pointless in cloud.** `/lrh-closeout` always
  runs `lrh sessions closeout-sync` (Step 5). In a cloud session that mirrors
  transcripts into the ephemeral archive. It does no harm, but it achieves
  nothing durable, and the report doesn't say so.

### 1.6 Other vendors

- **Codex.** `lrh-codex-export` exports through the local Codex app-server's
  `thread/read` (SKILL.md ~line 96). The repo has nothing that exports a
  Codex Cloud task. `/lrh-closeout` mentions a `codex-cloud:` pointer, but no
  resolver or exporter produces one (`grep codex-cloud: src/lrh` finds
  nothing in code). This is a bigger gap than Claude's: the transport itself
  is missing, not just the setup. The repo already sets the Codex Cloud setup
  convention: run `scripts/develop` at environment setup
  (`src/lrh/assist/templates/request/ci_implement_workflow.md:27`).
- **Antigravity** is a local IDE flow. The repo references no remote mode.
  It does share the checkout-assuming "Running `lrh`" fallback.
- **The three "Running `lrh`" sections are copies of one another.** One fix
  belongs in one shared place.

---

## 2. Recommended approach

**Make `lrh` already present (CLI bundled in the plugin, with a setup-script
fallback). Make the export commands pre-approved by exact rule. Make the
skill detect cloud and deliver the export instead of trusting the archive.
Make re-export safe without `--force`.**

1. **CLI availability: bundle the CLI in the plugin, behind a probe.**
   - The plugin exporter writes `plugins/lrh/bin/<shim>` plus a vendored copy
     of `src/lrh` from the same commit as the skills. That gives zero drift,
     no install step, and no clone, so nothing for the classifier to flag.
   - First confirm in a real cloud session that a synced plugin's `bin/` is on
     PATH, and that `python3` and PyYAML are present.
   - Design decisions to settle:
     - The shim's name. A plugin `lrh` on PATH would shadow a user's local
       `lrh` in desktop sessions. A distinct name such as `lrh-plugin` avoids
       that, but every skill would need a lookup rule.
     - Whether to vendor PyYAML.
   - Until the probe passes, or if it fails: document a setup-script install
     pinned to a ref, with the roughly seven-day cache drift stated.
2. **Missing-CLI recovery never discovers or clones on its own.** Replace the
   three copied "Running `lrh`" sections with one shared reference:
   - Use `lrh` when it is on PATH.
   - Else use the bundled shim, once that ships.
   - Else use `PYTHONPATH=src` only inside an LRH checkout.
   - Else stop, and print the exact setup-script line and the docs anchor. A
     one-time bootstrap clone is allowed only as an explicit, separately
     confirmed step, named for what it does (for example "clone LRH into the
     scratchpad"), never hidden behind a read-only-sounding command.
3. **Permissions: exact allow rules, an ask rule for `--force`, and no
   subshell.**
   - CLI: create export and archive directories `0700` itself, so the skill
     can drop the `( umask 077 ... )` wrapper and run plain commands.
   - Publish a settings snippet for client repos' `.claude/settings.json`:
     allow `lrh conversation current-claude-session-id *`,
     `lrh conversation export-claude-session *` and
     `lrh conversation inspect-export *`, plus an `ask` rule matching
     `--force`.
   - `/lrh-config-skills`, or a sibling command, can offer to write the
     snippet, with confirmation.
   - Known limits: multi-repo cloud sessions don't read project settings,
     and plugins can't declare permissions. Say both in the docs.
4. **Cloud detection lives in the CLI, not the skill.**
   `current-claude-session-id --format json` gains two metadata-only fields:
   - `cloud_session` (from `CLAUDE_CODE_REMOTE == "true"`)
   - `remote_session_id` (from `CLAUDE_CODE_REMOTE_SESSION_ID`)

   The skill branches on that output. Whether `remote_session_id` becomes a
   `claude-cloud:` `session_transcript` pointer is a separate, small decision.
5. **Cloud branch of the skill.** When `cloud_session` is true and the
   session offers a file-delivery tool:
   - Export with `--out` straight to the delivery location (the scratchpad,
     never the repository working tree).
   - Verify the file, then offer it for download.
   - Report the one local command that files the download,
     `lrh conversation import-claude-export <file>`. Fall back to
     `chmod 600 <file>` when `lrh` isn't installed locally.

   Without a delivery tool, export to the archive and say plainly that the
   copy disappears with the container. (Revised 2026-11-06: an earlier draft
   exported to the archive and then copied. See §1.4.)
6. **Local import command.** `lrh conversation import-claude-export <file>`:
   - Computes the destination from the file's own frontmatter, using a path
     helper shared with the exporter.
   - Honors `LRH_SESSION_ARCHIVE_ROOT`.
   - Creates missing folders 0700 and writes the file 0600 from the first
     byte.
   - Checks the manifest. An identical existing file is a no-op; any other
     existing file is refused by default.
   - An explicit `--replace-older` replaces an older snapshot of the same
     session, judged from the two manifests only. `--refresh`'s prefix
     check can't run here: it needs the original transcript, which stayed
     in the container.
   - Copies by default; deleting the download takes an explicit `--move`.

   This replaces the manual `mkdir`/`mv`/`chmod`. The download itself stays
   manual unless teleport proves out.
7. **Snapshot timing: refresh without overwrite risk, and flag staleness.**
   - Record the render options (`include_subagents`,
     `include_system_attachments`) in the export manifest, which today
     records neither (`claude_export.py:119-135`).
   - Add a `--refresh` mode to the exporter. It overwrites only an existing
     export of the same source ID, with the same recorded render options,
     whose recorded source is a byte-prefix of the current transcript (the
     `match_source_grew` case), and refuses anything else. Because it can't
     destroy a different export, or drop subagent or attachment content an
     earlier export included, it doesn't need the `--force` gate. The name
     promises exactly that.
   - `/lrh-closeout` Step 8 and `/lrh-work-remains` item 11 learn one cloud
     rule: in a cloud session, flag "no export" or "export is N bytes stale"
     (from `inspect-export`), and offer a refresh plus delivery. Don't use a
     SessionEnd hook.
   - Closeout's report notes when `closeout-sync` ran against an ephemeral
     archive.

### Alternatives considered

| Option | Why not (or not alone) |
|---|---|
| Publish to PyPI | Not published, and publishing is explicitly unsupported (`scripts/publish`). It still drifts from auto-synced skills. Revisit when LRH is published. |
| Setup script only | Documented and classifier-free. But each environment must configure it, it drifts up to about 7 days behind the snapshot, and nothing helps a user who hasn't set it up. Keep it as the fallback. |
| Skill does a one-time scratchpad clone and bootstrap | Triggers "Code from External". A read-only-sounding export step would be quietly cloning. Allowed only as an explicit, confirmed, honestly named step. |
| SessionEnd hook auto-export | 1.5 s default budget, teardown behavior undocumented, and the output would land in the ephemeral container. |
| Commit exports to a private branch for durability | Violates "never commit exports". |
| `autoMode.environment` trusted sources | Not read from project settings, and user settings aren't read in cloud sessions. |
| Plugin-declared permissions | Not supported (plugin `settings.json` honors only `agent` and `subagentStatusLine`). |
| Detect cloud by path heuristics (`/home/user`, no `~/Library`) | Guessing, when a documented variable exists. |
| Export to the in-container archive, then copy for delivery | The archive copy is thrown away with the container. It adds a file and a command to approve, and protects nothing. |
| File downloads by hand, or have the skill print pre-filled `mkdir`/`mv`/`chmod` | Folders come out 0755, the file is exposed until the `chmod`, `LRH_SESSION_ARCHIVE_ROOT` is ignored, and nothing checks the file. Pre-filling copies the exporter's path rule into skill text, which has already drifted (`SKILL.md:296`). |
| Pick up downloads in `lrh sessions sync` or its weekly launchd schedule | Exposure for up to a week, and `sync` deliberately assumes no default exports location. A possible later add-on that reuses the import command's code. |
| A folder watcher that files downloads on arrival | A background process moving files silently, and Mac-only. |
| Desktop app session Export of the cloud session | None of the 40 most recent sessions the desktop app listed was a cloud session. |
| Teleport, then export locally | Would skip the download, but compacted messages aren't copied, there are checkout prerequisites, and local transcript storage is undocumented. Probe it. |

### Open questions for the probe

- Is a synced plugin's `bin/` on PATH in a cloud session?
- Are `python3 >= 3.11` and PyYAML always present in the default image?
- Which of `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_HOST_SESSION_ID`, and
  `CLAUDE_CODE_REMOTE_SESSION_ID` are set in a cloud session? The taurworks
  session showed that `CLAUDE_CODE_SESSION_ID` resolved.
- Does a narrow `Bash(lrh conversation export-claude-session *)` allow rule
  actually suppress the classifier there? The test needs a control: the
  same command run in auto mode without the rule must be denied first, or
  a pass shows nothing.
- Does `claude --teleport` write a complete local transcript under
  `~/.claude/projects/`, and under which session ID? If it does, exporting
  locally after teleport skips the download.
