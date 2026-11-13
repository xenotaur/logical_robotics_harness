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
- **A plugin `bin/` can't reach claude.ai.** The plugin reference's
  Executables row says files in `bin/` "are on the Bash tool's `PATH` while
  the plugin is enabled", and continues: "claude.ai and Cowork don't
  install a plugin that has this directory"
  (<https://code.claude.com/docs/en/plugins-reference.md#standard-layout>).
  - claude.ai's org-sync page says it "rejects a plugin that has one,
    whether the plugin arrives by marketplace sync or by direct upload",
    with an error starting `Plugin contains a top-level bin/ directory`
    (<https://claude.com/docs/plugins/org-sync#keep-executables-out-of-the-top-level-bin-directory>).
  - The support table lists `bin/` as "Can't be installed" on claude.ai
    and Cowork, while other unsupported components are only ignored
    (<https://claude.com/docs/plugins/platform-support>).
  - The repo already enforces this. `src/lrh/skills/exporter.py:596-597`
    refuses a top-level `bin/`, `tests/skills_exporter_test.py:1377` tests
    it, and `docs/reference/cli/skills.md:258` documents it.
  - No doc gives the reason. The likely one (inference): a synced plugin
    also loads into members' Claude Code sessions, and a `bin/` would add
    commands that run by bare name, even when no skill mentions them.
  - An earlier draft of this audit quoted only the first sentence of the
    row and called the cloud behavior undocumented. A substitute review on
    2026-11-13 caught the omission.
- **The documented alternative is a script called by path.** The org-sync
  page says: "Keep executables in another directory, such as `scripts/`,
  and reference them as `${CLAUDE_PLUGIN_ROOT}/scripts/<name>`".
  - Claude Code substitutes `${CLAUDE_PLUGIN_ROOT}` inline in skill,
    command and agent content. It isn't in the Bash tool's environment
    (`plugins-reference.md`, Environment variables).
  - A 2026-10-26 probe saw it resolve to
    `/root/.claude/plugins/synced/<account-id>/lrh-cloud-probe` for a synced
    plugin in a cloud session
    (`project/executions/AD_HOC/2026_10_27_00_12_53_WI_SKILLS_CLAUDE_PLUGIN_EXPORT.md`).
  - claude.ai's skills guide documents the per-skill variant,
    `${CLAUDE_SKILL_DIR}/scripts/…`. It adds that `Bash()` rules "match the
    whole command line", and that "a wildcard before the path would approve
    more than you intend"
    (<https://claude.com/docs/skills/how-to#add-scripts>).
  - The synced plugin loading in cloud sessions at all is still
    undocumented but observed (`docs/how-to/use-lrh-with-agent-assistants.md`
    §5).
  - Directory submission, which LRH doesn't use, would add a 512-file and
    256 KiB-per-file review threshold
    (<https://claude.com/docs/plugins/pre-submission-checklist>). A bundled
    plugin would be about 256 files: the 66 it has today, about 187 from
  `src/lrh` outside `src/lrh/skills`, and the three Python modules in
  `src/lrh/skills` (`__init__.py`, `exporter.py`, `installer.py`). The
  copy needs those three: `lrh.cli.main` imports `lrh.agent_skills_status` at top level, and that imports `lrh.skills.installer`.
  It can leave out the rest of `src/lrh/skills`, the skill sources the
  plugin already carries. No `src/lrh` file exceeds 256 KiB.
- **Bundling is small.** `src/lrh` is 3.3 MB and 269 files. claude.ai's plugin
  limit is 5,000 files and 200 MB (same doc §5). The only runtime dependency is
  `PyYAML` (`pyproject.toml`), and every CLI command needs it.
  `lrh.cli.main` imports `lrh.agent_skills_status` at top level, and that
  module imports `yaml` (`src/lrh/agent_skills_status.py:29`). So a
  bundled launcher without PyYAML in the image fails on any command,
  including `current-claude-session-id`, not just `inspect-export`. In
  the taurworks session
  `PYTHONPATH=src python3 -m lrh.cli.main conversation inspect-export`
  succeeded, so that image had PyYAML. That is one observation, not a
  guarantee.
- **No published package.** `pip index versions lrh` finds nothing, and
  `https://pypi.org/pypi/lrh/json` returns 404. `scripts/publish` says
  "Publishing not yet supported".
- **Setup scripts run before Claude Code launches**, as root. A new
  environment starts at the **Limited** network level with **Allow package
  managers** checked; an environment saved as "Trusted" opens that way too.
  The default allowlist then includes `github.com`, `codeload.github.com`,
  `pypi.org`, and `files.pythonhosted.org`
  (<https://code.claude.com/docs/en/cloud-environments.md#setup-scripts>,
  `#access-levels`, `#default-allowed-domains`, re-read 2026-11-13). An
  install run there never goes through the permission classifier.
  - The session's GitHub proxy serves only the repositories attached to
    the session, and archive fetches for any other repository get a 403
    (same page, GitHub proxy).
  - A setup-script install of LRH should therefore use the
    `pip install "git+https://…"` form, which the taurworks session showed
    can clone LRH, and not a source-archive URL.
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

- **Allow rules skip the classifier, with listed exceptions.** In the
  classifier's decision order, actions matching allow, ask, or deny rules
  "resolve immediately, with these exceptions". None of the exceptions
  applies to an `lrh conversation` command: protected-path writes,
  critical-path removals, `requiresUserInteraction` MCP tools, shell
  commands with per-command allowed domains, content-matching ask rules
  (which prompt), symlinked protected writes, and network-path reads
  (<https://code.claude.com/docs/en/permission-modes.md#how-the-classifier-evaluates-actions>,
  re-read 2026-11-13; an earlier draft quoted wording the page no longer
  has).
  Ask rules always prompt, even in auto mode
  (<https://code.claude.com/docs/en/auto-mode-config.md#add-a-human-checkpoint>).
- **Only one settings file reaches a cloud session.** User
  `~/.claude/settings.json` and `.claude/settings.local.json` are not read
  there. The repo's shared `.claude/settings.json` is read only in
  single-repo sessions, and cloud threads in a project apply none of its
  permission rules, "however many repositories the project has"
  (<https://code.claude.com/docs/en/settings.md#settings-in-cloud-sessions>).
- **A plugin's `settings.json` can't grant permissions, but its skills can.**
  The plugins reference fetched on 2026-11-12 said that in a plugin's
  `settings.json`, "Only `agent` and `subagentStatusLine` take effect". The
  pages fetched on 2026-11-13 no longer document plugin settings, and none
  lets them grant permissions. A skill's `allowed-tools` frontmatter is a
  separate channel.
  - It grants the listed tools "during the turn that invokes this skill.
    The grant clears when you send your next message"; "invoking the skill
    again re-applies it for that turn" (`skills.md`).
  - Consequence for `lrh-export-claude`: it waits for confirmation on
    model-initiated invocations and on every `--force`
    (`src/lrh/skills/lrh-export-claude/SKILL.md:20-22,291`), and the
    confirming reply clears the grant. So the grant covers only a
    user-typed invocation without `--force`.
  - In a plugin skill, `${CLAUDE_PLUGIN_ROOT}` is substituted in its Bash
    rules. "Using the same variable in both places lets a skill run a
    bundled script without a permission prompt"
    (<https://code.claude.com/docs/en/skills.md#available-string-substitutions>).
  - A synced skill's grant "goes through the normal permission flow"
    (same page, "How Claude Code handles the frontmatter of a synced
    skill"). There, "synced skill" means a skill enabled on the claude.ai
    account. The page doesn't say whether the rule covers skills inside a
    synced plugin, so the probe tests it.
  - A `*` in a Bash rule "matches any text, including spaces"
    (`permissions.md`). No rule can wildcard a single path segment.
  - Auto mode drops only broad allow rules: blanket `Bash(*)`, wildcarded
    interpreters, package-manager runs, and Agent and Monitor rules
    (`permission-modes.md`).
  - Rules evaluate deny, then ask, then allow (`permissions.md`), so a
    repository's ask rule still prompts.
  - An earlier draft of this audit said there was no documented way for a
    plugin to declare permissions. A substitute review on 2026-11-13
    corrected that.
- **Substitution reaches SKILL.md, not supporting files.** "Claude Code
  substitutes `${CLAUDE_SKILL_DIR}` and `${CLAUDE_PROJECT_DIR}` in two
  places: the skill's markdown content, and Bash rules in the
  `allowed-tools` frontmatter", and `${CLAUDE_PLUGIN_ROOT}` "in the same two
  places" (`skills.md`). A path placeholder in a `references/` file reaches
  Claude as literal text.
- **`autoMode` config can't come from the repo.** The classifier reads
  `autoMode` only from user, managed, and `--settings` scopes, never from
  project settings (`auto-mode-config.md#where-the-classifier-reads-configuration`).
  User settings aren't read in cloud sessions, so in practice only managed
  settings could tune it there. (Inference from the two documented facts.)
- **The "Code from External" denial came from the mid-session clone.** By
  default auto mode trusts "only the working directory and the current repo's
  configured remotes" (`auto-mode-config.md`), and the LRH repo is neither for
  a taurworks session. Installing in setup, or shipping a copy in the
  plugin, removes the clone. The second denial was for running the cloned CLI
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

**Make `lrh` already present (CLI bundled in the plugin's `scripts/` and
called by path, with a setup-script route as well). Make the export
commands pre-approved: the launcher by the skill's own `allowed-tools`, and
the setup-script route by exact repository rules. Make the
skill detect cloud and deliver the export instead of trusting the archive.
Make re-export safe without `--force`.**

1. **CLI availability: bundle the CLI in the plugin's `scripts/`, behind a
   probe.** (Revised 2026-11-13: an earlier draft used `bin/`, which
   claude.ai won't install. See §1.1.)
   - The plugin exporter writes a bootstrap, `plugins/lrh/scripts/lrh_cli.py`,
     plus a vendored copy of `src/lrh` under `plugins/lrh/scripts/`, from the
     same commit as the skills. That gives zero drift, no install step, and
     no clone.
   - Skills run it by path from SKILL.md text, where the placeholder is
     substituted:
     `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/lrh_cli.py conversation …`.
     Running it through `python3` avoids depending on the executable bit,
     whose survival through claude.ai upload or sync isn't documented.
   - First confirm in a real cloud session three things:
     - `${CLAUDE_PLUGIN_ROOT}` is substituted in a synced plugin's skill
       text;
     - a script under the plugin's `scripts/` runs with `python3 -I`;
     - `python3` and PyYAML are present.
   - Still to settle: the exact file names, and whether to vendor PyYAML.
   - A repository's exact allow rule can't name the launcher, because its
     absolute path contains the account ID in cloud. The skill's own
     `allowed-tools`, using `${CLAUDE_PLUGIN_ROOT}`, can (§1.2, §2.3).
   - Document a setup-script install pinned to a ref, with the roughly
     seven-day cache drift stated. It is the route whose commands can be
     pre-approved, and the fallback if the probe fails.
2. **Missing-CLI recovery never discovers or clones on its own.** Replace the
   three copied "Running `lrh`" sections with one shared reference:
   - Inside an LRH checkout, use `PYTHONPATH=src`.
   - Else use the bundled launcher, once it ships, when the launcher path
     written in the SKILL.md body exists. The path has to live in each
     SKILL.md, because `references/` files aren't substituted. Outside the
     plugin the placeholder isn't substituted either, so the test fails and
     the order falls through. It comes before PATH because a setup-script install can lag
     the plugin by about seven days, and should not shadow the bundle.
   - Else use `lrh` when it is on PATH.
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
   - For the plugin launcher, `lrh-export-claude` declares matching
     `allowed-tools` rules instead, pending the probe.
   - Known limits, stated in the docs:
     - Multi-repo cloud sessions and cloud threads in a project don't
       apply the repo's permission rules.
     - A plugin's `settings.json` can't declare permissions.
     - The rules cover only the `lrh conversation …` form. They don't match
       the `PYTHONPATH=src python3 -m lrh.cli.main` checkout form, or the
       plugin launcher's absolute, account-specific path.
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
| Permissions in plugin `settings.json` | Not documented as possible (2026-11-12 docs: only `agent` and `subagentStatusLine`; 2026-11-13 docs no longer cover plugin settings). The plugin skill's `allowed-tools` is the supported channel, and is chosen for the launcher. |
| A repository allow rule for the launcher path with a wildcard for the account segment | A `*` matches any text, including `../..`, so it would approve any file with the launcher's name, including one in the working tree. Auto mode may also drop an interpreter rule with a wildcard. |
| Detect cloud by path heuristics (`/home/user`, no `~/Library`) | Guessing, when a documented variable exists. |
| Export to the in-container archive, then copy for delivery | The archive copy is thrown away with the container. It adds a file and a command to approve, and protects nothing. |
| File downloads by hand, or have the skill print pre-filled `mkdir`/`mv`/`chmod` | Folders come out 0755, the file is exposed until the `chmod`, `LRH_SESSION_ARCHIVE_ROOT` is ignored, and nothing checks the file. Pre-filling copies the exporter's path rule into skill text, which has already drifted (`SKILL.md:296`). |
| Pick up downloads in `lrh sessions sync` or its weekly launchd schedule | Exposure for up to a week, and `sync` deliberately assumes no default exports location. A possible later add-on that reuses the import command's code. |
| A folder watcher that files downloads on arrival | A background process moving files silently, and Mac-only. |
| Ship the CLI in the plugin's top-level `bin/`, on PATH | claude.ai and Cowork won't install a plugin with a top-level `bin/` (§1.1), so the whole plugin would stop reaching cloud sessions. The repo's exporter already refuses one. |
| Desktop app session Export of the cloud session | None of the 40 most recent sessions the desktop app listed was a cloud session. |
| Teleport, then export locally | Would skip the download, but compacted messages aren't copied, there are checkout prerequisites, and local transcript storage is undocumented. Probe it. |

### Open questions for the probe

- Is `${CLAUDE_PLUGIN_ROOT}` substituted in a synced plugin's skill text in
  a cloud session, and does `python3 -I` run a script under the plugin's
  `scripts/`?
- Does a plugin skill's `allowed-tools` rule, written with
  `${CLAUDE_PLUGIN_ROOT}`, run the bundled script without a prompt or
  classifier check in cloud auto mode? Does the quoting of the path in the
  SKILL.md command matter for the match?
- Is `${CLAUDE_PLUGIN_ROOT}` left literal in a `references/` file, as the
  docs imply?
- Does the `allowed-tools` grant hold for a skill inside a synced plugin,
  and is it gone in the turn after a confirming reply?
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
