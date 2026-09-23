---
title: "Session Sync / Transcript Mirror / Export Ecosystem Audit"
date: 2026-09-22
status: completed
type: audit
scope: session-archive
---

# Session Sync / Transcript Mirror / Export Ecosystem Audit (2026-09-22)

Prompt ID: `PROMPT(AD_HOC:SESSION_SYNC_EXPORT_ECOSYSTEM_AUDIT)[2026-09-22]`
Trigger: downstream handoff from a consumer-repo (LCATS) session. It asked
"does the session archive capture everything the export does?" and reported
six findings. This audit confirms, corrects, or dismisses each one against
current source (`main` @ `24909604`) and one real machine's state. It then
recommends a design.

**Revision (same day).** The first version of this audit said the desktop
app's "per-session Export menu still exists". That was based on a tool
description, not on the app. The user, who did the exporting, reported
three things: in-session `/export` no longer resolves, View > Copy URL is
gone, and no Export menu can be found. A read-only inspection of the
installed app bundle (Claude.app 2.7032.0, `app.asar`) confirmed this and
refined the picture. Finding 1 and §6.2 have been rewritten. New findings
A8 and A9 are added. The View > Copy URL fallback in the skills has been
replaced (§8).

## 1) Summary

- The ecosystem has **two artifact families** and **one identity index**:
  1. the verbatim raw mirror (`lrh sessions sync`);
  2. per-backend human-readable Markdown exports (`/lrh-export-claude`,
     `/lrh-antigravity-export`, `/lrh-codex-export`);
  3. `project/sessions/index.jsonl`, which records host↔child↔PR identity.

  Keeping the two artifact families separate is correct. The real gap is in
  the index: **it is fed almost only by `/lrh-closeout`'s
  `record-session-alias`, which never passes `--title` or `--branch`.** On
  this machine, 0 of 30 index rows have a title.
- The downstream report assumed that title, branch, and PR data "aren't in
  the transcript content". **That is wrong.** Current Claude Code JSONL
  transcripts carry `pr-link` (`prNumber`, `prUrl`, `prRepository`),
  `custom-title`, `ai-title`, and `agent-name` records, plus `gitBranch` and
  `cwd` on every message line. The raw mirror already *copies* this data.
  Nothing *extracts* it. The one thing raw JSONL really lacks is a structured
  **host** id. The live desktop app exposes the host id through the
  `CLAUDE_CODE_HOST_SESSION_ID` env var and the session-management
  `get_session`/`list_sessions` tools.
- The `session-export-*.zip` harvest **has lost its only human trigger**:
  - The zip was always built by the desktop app, not the CLI. Its
    `metadata.json` is the app's own session record: the `local_` host id,
    `prs[]`, and `writtenBranches`, which the CLI never has.
  - Users produced it by typing `/export` in a Code-tab session. As of
    Claude.app 2.7032.0, that command reports "not available for this
    session". No visible menu item replaces it.
  - The zip builder itself survives. The only remaining way to invoke it is
    the agent-side session-management `export_transcript` tool.
  - On this machine, no zip has ever been harvested: the archive has no
    `exports/` directory and there are no zips in Downloads.
  - The harvest was always meant to be the *retroactive* path. Per
    `PROP-LRH-SESSION-ARCHIVE-SYNC` Decision 1, forward env-var capture is the
    primary path.
- **View > Copy URL is gone.** It now sits in a hidden `Debug` submenu. That
  breaks `/lrh-closeout` Step 3's manual fallback and its "browser URL wins"
  confirmation rule, which are fixed in this change (A8). The natural
  replacement, a `/lrh-claude-session` skill parallel to
  `/lrh-codex-session`, is not tracked anywhere yet, although its CLI
  already exists (A9).
- Skill drift is real, and it has **two dimensions no current check covers**:
  - The installer cannot tell "stale because the package moved ahead" apart
    from "the user edited it". Both are reported as "local modifications" and
    need `--force`. This explains downstream finding 6.
  - **Skill↔CLI version skew**: on this machine, the `lrh` on `PATH` is an
    editable install pinned to a worktree frozen at 2026-08-21. That CLI has
    no `closeout-sync`, `report`, or `schedule`, but the installed
    `/lrh-closeout` calls `closeout-sync` unconditionally.
- Confirmed stale documentation has been fixed in this change:
  - the `lrh sessions list` reference in `lrh-land`;
  - the View > Copy URL fallback in `lrh-closeout`, `lrh-land`, and
    `lrh-implement` (all four copies of each);
  - `docs/reference/cli/sessions.md`'s missing scan-scope disclosure and
    its account of where the zip comes from.

## 2) Scope and method

In scope:
- `src/lrh/sessions_workflow.py`, `src/lrh/prompt_workflow_sessions.py`
- `src/lrh/prompt_workflow.py` (`record-session-alias`)
- `src/lrh/conversations/` (the Claude, Antigravity, and Codex exporters and
  `claude_session.py`)
- `src/lrh/skills/installer.py`
- The skills `lrh-closeout`, `lrh-land`, `lrh-implement`,
  `lrh-export-claude`, `lrh-antigravity-export`, `lrh-codex-export`, and
  `lrh-codex-session`
- The adopted proposals `PROP-LRH-SESSION-ARCHIVE-SYNC` and
  `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER`
- The open work items `WI-SESSION-ARCHIVE-CLOSEOUT-SAFETY` and
  `WI-SESSION-ARCHIVE-ROOT-DEFAULT`

Evidence sources (all read-only except the fixes in §8):
- Source reading at the lines cited below.
- A key census of the 60 most recent real transcripts under
  `~/.claude/projects/`. Only record `type`s and top-level key names were
  counted; no message bodies were read.
- The desktop app's `get_session("self")` output, and the
  `export_transcript` / `list_sessions` tool contracts.
- A read-only string/code inspection of the installed desktop app bundle
  (`/Applications/Claude.app`, version 2.7032.0: `en-US.json` and
  `app.asar`), covering its menus, the `shareSession` / `transcriptExport`
  zip builder, and the `export_transcript` tool handler.
- `list_sessions` and `search_session_transcripts` across local sessions,
  plus `gh pr list`, to look for in-flight `/lrh-claude-session` work.
- On-disk state of `~/.local/share/lrh/session-archive/` (directory names
  and counts only) and of `project/sessions/index.jsonl` (field-population
  counts).
- `lrh skills status`, `lrh skills install --dry-run --diff`, and
  `lrh skills check` run against both the package source and
  `--source current-repo`.

Not done:
- **No export zip was generated.** Calling `export_transcript` would write
  a full transcript into the user's Downloads. The `metadata.json` content is
  therefore inferred from code, not observed in a zip. The zip builder
  copies the app's per-session record file verbatim (see §6.2).
- The app's Code-tab UI is loaded from claude.ai, not shipped in the bundle.
  "No visible Export menu" therefore rests on the user's report plus the
  absence of any menu label in the bundle; it is not a complete UI survey.
- The Codex and Antigravity exporters were inventoried, not audited
  line-by-line.

## 3) Inventory

### 3.1 CLI commands

| Command | Reads | Writes | Notes |
|---|---|---|---|
| `lrh sessions sync` (`sessions_workflow.py:254`) | Every `~/.claude/projects/*/*.jsonl` plus the nested `<session-id>/**` files (`discover_transcripts`, `prompt_workflow_sessions.py:667`). If `--exports-dir` is given, also `session-export-*.zip` → `metadata.json` only. | `<archive>/raw/<slug>/…` (atomic, never-shrink; `mirror_transcript` `:721`). `project/sessions/index.jsonl` (child aliases for already-known hosts; harvested identity). `<archive>/exports/<host>/metadata.json` (sanitized copy). | Machine-wide scan. `--project-root` does not scope the scan; it only picks which index gets written. |
| `lrh sessions closeout-sync` (`:338`) | same as `sync` | same as `sync` | A thin wrapper around `_run_sync` that adds a heading/footer and catches `OSError`/`ValueError`. |
| `lrh sessions schedule` (`:350`) | nothing | stdout, or the `--output` plist | Renders a weekly launchd job that runs `lrh sessions sync --project-root <abs>`. |
| `lrh sessions discover` (`:430`) | `~/.claude/projects/<slug-of-project>/*.jsonl` (top-level only) and the index | stdout | The only project-scoped command. Returns **child** ids from filenames, plus a host id only if the index already has it. |
| `lrh sessions link` (`:469`) | index, execution records | one execution record's `session_transcript` | Explicit child→host promotion. |
| `lrh sessions report` (`:505`) | Execution-record frontmatter; index; `<archive>/raw/*/*.jsonl` **filenames**; `<archive>/codex/**/attempt.json` | stdout | Claude coverage = "any indexed child id has a raw top-level JSONL". It does not recognize `claude/exports/*.md` or `antigravity/exports/*.md`. |
| `lrh prompt record-session-alias` (`prompt_workflow.py:418`) | index | index (`record_session_observation`) | Accepts `--host-id --child-id --title --pr --branch --written-branch`. |
| `lrh conversation current-claude-session-id` (`claude_session.py:130`) | env `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_HOST_SESSION_ID`; globs the transcript path | stdout | Metadata only. Already yields the host pointer. |
| `lrh conversation export-claude-session` (`claude_export.py`) | one raw JSONL (+ subagents) | `<archive>/claude/exports/YYYY/MM/<child-id>.md` | Markdown plus privacy/sensitivity frontmatter. Frontmatter has `source_id` (the **child** id) but no host id, title, branch, or PR. |
| `lrh conversation export-antigravity-session` | Antigravity `transcript.jsonl` | `<archive>/antigravity/exports/YYYY/MM/<id>.md` | Parallel design. Nothing downstream reads it. |
| `lrh conversation archive-codex-thread` / `export-codex-thread` / `import-codex-exports` / `current-codex-thread-id` | Codex app-server RPC / files | `<archive>/codex/…` including `attempt.json` | `report` reads `attempt.json` for Codex coverage. |
| `lrh conversation inspect-export` | an export `.md` | stdout | Used by all three export skills for verification. |
| `lrh memory sync` | `~/.claude/projects/*/memory/` | `<archive>/raw/<slug>/memory/` and `<archive>/history/` | Shares the archive root and `mirror_file_with_snapshot`. Adjacent, not audited. |

### 3.2 Skills and which commands they invoke

| Skill | Invokes | When |
|---|---|---|
| `/lrh-implement` | `lrh prompt record-session-alias` (host + child, at record creation) | Every execution-record creation on Claude.app |
| `/lrh-closeout` | Step 3: env var (confirmed with `get_session("self")`), `list_sessions` by PR, or a session picked from `list_sessions` (the Copy URL path is replaced; see A8). Step 5: `lrh prompt update-execution`, `lrh prompt record-session-alias --host-id --child-id --pr` (**no `--title`/`--branch`**), then **always** `lrh sessions closeout-sync --project-root .` | Every closeout |
| `/lrh-land` | Step 3: same resolution as closeout (was a phantom `lrh sessions list`, now fixed). The Step 6 preview shows the `closeout-sync` command. Inlines `/lrh-closeout`. | Every land |
| `/lrh-execute` | inlines `/lrh-implement` → `/lrh-land` | — |
| `/lrh-export-claude` | `lrh conversation current-claude-session-id`, `export-claude-session`, `inspect-export` | On explicit request only |
| `/lrh-antigravity-export` | `export-antigravity-session`, `inspect-export` | On explicit request only |
| `/lrh-codex-export` | `current-codex-thread-id`, `archive-codex-thread`, `inspect-export` | On explicit request only |
| `/lrh-codex-session` | `current-codex-thread-id` | Pointer only; no export |

### 3.3 Data-flow graph

```text
 live desktop session ──env CLAUDE_CODE_{HOST_,}SESSION_ID──┐
 desktop list_sessions/get_session (host id, title, branch, │
                                   prNumber)                ├─► record-session-alias ─┐
   (/lrh-implement, /lrh-closeout Step 3→5)  ───────────────┘   (title/branch never    │
                                                                 passed today)         ▼
 ~/.claude/projects/**/*.jsonl ──► sessions sync ──► <archive>/raw/<slug>/…   project/sessions/index.jsonl
   (pr-link, ai-title,             │  (all projects)        │                          ▲   │
    gitBranch… present             ├─ reconcile_child_id_aliases (sessionId only) ────┘   │
    but NOT extracted)             └─ --exports-dir: session-export-*.zip ─► sync_export ─┘
                                        (desktop zip builder → ~/Downloads;     └─► <archive>/exports/<host>/metadata.json
                                         in-app /export removed; agent-only
                                         export_transcript remains; never
                                         harvested on this machine)
 raw JSONL ──► export-claude-session ──► <archive>/claude/exports/YYYY/MM/<child>.md   (read by: inspect-export only)
 Antigravity log ──► export-antigravity-session ──► <archive>/antigravity/exports/…     (read by: inspect-export only)
 Codex RPC ──► archive-codex-thread ──► <archive>/codex/…/attempt.json ──► sessions report
 execution records + index + raw filenames ──► sessions report
 index ──► sessions discover / link ──► execution-record session_transcript
```

## 4) Downstream findings

### Finding 1: "The `--exports-dir` harvest path may be unreachable for Claude sessions"

**Verdict: confirmed for human use. The harvest's feeder is gone, and the
only surviving trigger is agent-side.** (This is revised; the first version
wrongly said a per-session Export menu still existed.)

- **Confirmed:** in-session `/export` no longer works in the desktop app's
  Code tab. It reports "not available for this session".
  `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` Background records the same
  butterbar text. The user confirms there is no replacement menu item.
- **Refined: the zip was always an app artifact.** When users typed
  `/export` in the desktop app, the result was a `session-export-*.zip`
  whose `metadata.json` carries the `local_` host id, `prs[]`, and
  `writtenBranches`. Only the desktop app's own session record has those
  fields. The bundle shows how the zip is built:
  - The `LocalSessions.shareSession(sessionId)` entry point is gated by the
    org policy `share_session_export`.
  - It calls a `transcriptExport` worker that zips the child JSONL and
    subagent transcripts, adds the session's record file as
    `metadata.json`, and writes to Downloads.
  - The in-app `/export` was very likely a desktop-side handler for this
    same function. That part is an inference from the code.
- **What remains:** the builder is still shipped, and the agent-side
  session-management `export_transcript` tool calls it. That tool calls
  `shareSession(…, {includeAppLogs: false})`, is refused after six exports
  an hour, and is refused once the transcript is pruned. No human UI path
  was found. The path is therefore reachable only by an agent, and in
  practice it goes unused: `~/.local/share/lrh/session-archive/exports/`
  does not exist on this machine, and `~/Downloads` holds no
  `session-export-*.zip`.
- **Related loss (A8):** View > Copy URL, the other human way to get a
  session's host id, is also gone from view.
- **Corrected:** the harvest is not "the identity-capture path this system
  was designed around." `PROP-LRH-SESSION-ARCHIVE-SYNC` Decision 1 makes
  **forward env-var capture primary**. The zip harvest is labelled
  "Retroactive mapping … for pointers that already dangle."
- **Existing mitigations the downstream session missed:**
  - `/lrh-closeout` Step 3 path 1 (env var) and path 2 (`list_sessions`
    matched by `prNumber`), plus Step 5's `record-session-alias`. Together
    these capture host id, child id, and PR on every closeout.
  - `lrh conversation current-claude-session-id` (PR #698) also resolves
    the host pointer.
  - `get_session("self")` and `list_sessions` return the host id, title,
    branch, and PR number: the same identity the zip's `metadata.json`
    carried, without writing a transcript anywhere.
- **Residual gap, which is real:** title and branch are never captured on
  the forward path, because closeout does not pass `--title` or `--branch`.
  `written_branches` is captured by nothing. Index census on this machine:
  30 rows; `prs` 30, `child_ids` 30, `branch` 20, `title` **0**,
  `written_branches` **0**. The 20 populated `branch` values date from the
  index's early history (the `branch` field first appears with
  `bc4994c0`/#498). The current closeout skill text has no step that
  populates `branch`.

### Finding 2: "`/lrh-export-claude` was meant to replace native `/export` but produces an incompatible artifact"

**Verdict: the split is deliberate. The *identity* integration gap is real,
but the proposed fixes would not close it.**

- It is deliberate. `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` Non-Goals says
  it "Does not attempt to replicate the Claude Desktop app's
  `session-export-<timestamp>.zip` … mechanism." Its phrase "parallel to
  Claude's own `/export` habit" refers to the CLI's *human-readable*
  `/export`, not to the zip.
- The two adopted proposals **contradict each other about the zip**:
  - The archive-sync proposal treats it as the host↔child↔PR identity
    carrier.
  - The exporter proposal calls it "an unrelated Cowork-diagnostics feature
    (bundling … `cowork_vm_*`/`coworkd`/`vzgvisor` application logs)".
  - The bundle supports the archive-sync reading. The per-session path is
    `shareSession`, which zips the transcript plus the session record and
    passes no logs directory. A separate code path in the same builder
    accepts a logs directory and `other-mode-*` log names (the Cowork
    diagnostic bundle), which may be what the exporter proposal's
    investigation actually saw. The exporter proposal needs a correction
    note (§6.5, R6).
- Proposed fix (a), "`sync_export` reads `/lrh-export-claude` frontmatter",
  **would not work**. That frontmatter carries `source_id` (the child id)
  and transcript statistics, but no host id, title, branch, or PR. Without
  a host id there is nothing to key an index row on.
- Proposed fix (b), "`/lrh-export-claude` upserts into the index", would
  work, but it is the wrong place:
  - The exporter only runs on explicit request.
  - It is deliberately free of project-state side effects: it "does not
    promote private transcript text into LRH project state".
  - Closeout and sync already run on every PR, so identity capture belongs
    there (§6).

### Finding 3: "A newly shipped skill sat uninstalled indefinitely"

**Verdict: confirmed, and the problem is broader than reported.**

- `lrh skills status`/`check`/`install --dry-run` detect `missing` and
  `modified` correctly, but only when someone runs them. Nothing in
  `closeout-sync`, `sync`, `lrh version`, or any skill runs them.
- **New dimension: skill↔CLI version skew.** On this machine, the `lrh` on
  `PATH` (`anaconda3/bin/lrh`) is an **editable install whose source is a
  different worktree**
  (`…/SecretsHygiene/…/lrh-secrets-scope-discussion-85e353`). That worktree
  is checked out at `93d0a96a` (2026-08-21, PR #584).
  - `lrh sessions --help` there lists only `{sync,discover,link}`. There is
    no `closeout-sync`, `report`, or `schedule`.
  - `lrh conversation export-claude-session` there has no `--current`.
  - The package-sourced skill set has no `lrh-export-claude`,
    `lrh-antigravity-export`, `lrh-codex-session`, or `lrh-config-*`.
  - Yet `~/.claude/skills/lrh-closeout` (installed from a newer repo) calls
    `lrh sessions closeout-sync` in its "always run" step, which would fail
    with an argparse error on this machine.
  - `lrh version` reports `0.2.5.dev2656+g1bffa0995` (09-22). That comes
    from `importlib.metadata` dist-info written at install time, not from
    the code that actually runs, so the version string hides the skew.
- The downstream machine's "installed only when someone asked" symptom is
  the `missing` case of the same problem.

### Finding 4: "`lrh-land` references nonexistent `lrh sessions list`"

**Verdict: confirmed in canonical source. It has been present since the
skill was created (`5f5d2bcb`, PR #434). Fixed in this change. The proposed
replacement is corrected.**

- It was present in `src/lrh/skills/lrh-land/SKILL.md:160` and the three
  generated copies (`.claude/`, `.agents/`, `.gemini/plugins/lrh/`).
- `discover` is **not** the right substitute. It returns **child** ids from
  JSONL filenames, and `/lrh-closeout` Step 3 explicitly forbids using
  filename auto-detection to produce a `claude-app:` pointer. The intended
  tool is plainly the desktop session-management `list_sessions`, matched
  by `prNumber`, which is closeout's path 2. The text now says so and warns
  against `discover`.

### Finding 5: "sync scans the entire machine with no scoping disclosure"

**Verdict: confirmed. The behavior is intentional; the disclosure gap is
real.**

- `_run_sync` defaults to `~/.claude/projects`. `discover_transcripts`
  iterates every bucket. On this machine there are 124 buckets and 109
  archived slug directories.
- It is intentional in the sense that the archive is a machine-local,
  cross-project store keyed `raw/<project-slug>/`, and its invariant ("no
  agent session that changed this repository is ever lost") is best served
  by over-capturing.
- Cross-project transcripts are **copied but never indexed** into the wrong
  repo: `reconcile_child_id_aliases` only extends hosts already in *this*
  project's index (`prompt_workflow_sessions.py:897`). The privacy boundary
  therefore holds.
- The disclosure gaps:
  - Nowhere a human approves the run (`/lrh-closeout` Step 4 gate, the
    `/lrh-land` Step 6 preview, `docs/reference/cli/sessions.md`) was it
    stated that the scan covers every project. `discover`'s own help text
    ("for the current project") makes the contrast easy to miss.
  - The docs are fixed in this change. The gate text is left to a work item
    (R5), because gate definitions are tracked by `lrh chain-defaults
    check-staleness`.
- **Cost note:** every sync JSON-parses every top-level transcript on the
  machine to collect aliases, and loads the index twice per transcript
  (`:924`, `:935`). That is O(all transcripts) on every closeout, regardless
  of project.

### Finding 6: "General skill drift across eight skills"

**Verdict: confirmed and reproduced exactly on this machine. Only
`lrh-export-claude`'s drift is session-related. The root cause is found.**

- Running `lrh skills install --dry-run --diff --source current-repo`
  against `~/.claude/skills` reports the same eight skills (`lrh-closeout`,
  `lrh-execute`, `lrh-implement`, `lrh-land`, `lrh-proposal`,
  `lrh-self-review`, `lrh-work-item`, `lrh-workstream`) plus
  `lrh-export-claude`.
- Diff classification:
  - `lrh-closeout`: 9 lines, frontmatter-quoting guidance only.
  - `lrh-execute`/`lrh-land`: creation-PR check and land-workflow updates.
  - `lrh-export-claude`: 269 lines. The installed copy predates the
    current-session default (the PR #703 era). This is the only
    session-export-related drift.
  - None of the drift in closeout, land, or implement touches `sessions`,
    `record-session-alias`, `closeout-sync`, or `session_transcript` text.
- **Root cause:** `install_skills` (`installer.py:933`) marks *any*
  difference as `USER_MODIFIED` ("has local modifications — skipped (use
  --force …)"). There is no record of what was last installed, so an
  ordinary upgrade looks exactly like a user edit and is refused. Drift
  therefore accumulates on every machine that upgrades without `--force`.
- The repo's own checked-in Codex and Antigravity targets are also drifted.
  `lrh skills check --local --source current-repo` reports, for example,
  `lrh-closeout`/`lrh-land`/`lrh-implement` modified, and
  `lrh-antigravity-export` missing from the Antigravity target. This is
  already in `WI-SESSION-ARCHIVE-CLOSEOUT-SAFETY`'s acceptance criteria.
  The `.claude/` target is clean.

## 5) Additional findings (not in the handoff)

| # | Finding | Evidence | Severity |
|---|---|---|---|
| A1 | **The raw transcripts already contain PR, title, and branch; only extraction is missing.** Record types: `pr-link` (`prNumber`, `prUrl`, `prRepository`), `custom-title`, `ai-title`, `agent-name`, `worktree-state`. Every message line carries `gitBranch`/`cwd`. There is no structured host id: the host id appears only where a human or agent echoed the env var. | Census of 60 transcripts: 8,928 `pr-link` records, 7,655 `custom-title`, 6,094 `ai-title`; `gitBranch` on 150,888 lines. | High (design-shaping) |
| A2 | The harvest's field whitelist omits `writtenBranches` and `cwd`, even though the proposal (Motivation, Decision 4) names them as the fork-stitching keys and `persist_export_metadata`'s docstring claims the persisted copy lets "Stage 3 … recover `written_branches`/`cwd`". Those fields are never harvested, so they can never be recovered. `prNumber` *is* harvested but never indexed; only `prs[].url` is. | `EXPORT_IDENTITY_FIELDS` `:955`; `sync_export` `:1030`. | Medium |
| A3 | `report` measures Claude coverage only by raw JSONL filenames. A Markdown export in `claude/exports/` does not count, and the Antigravity scheme is reported as `unsupported`. | `_archived_claude_child_ids` `:414`. | Low |
| A4 | Parts of proposal Decision 2/3 were never built: the per-session `sessions/<key>.json`, the archive-level `index.jsonl`, era-general keys, `lost` rows, fork stitching, the recovery heuristic, and the `SessionEnd` hook. The proposal nonetheless says `implementation_status: implemented`. Its "Implementation Closeout Baseline" discloses the coverage gaps but not these unbuilt pieces. | Proposal text vs. source. | Medium (doc honesty) |
| A5 | `sessions sync` lacks the "archive root inside a git worktree" guard that all three exporters have (`_reject_archive_root_inside_current_git_worktree`). | `claude_export.py:218`, `codex_archive.py:75`, `antigravity_export.py:217`. | Medium; already tracked by `WI-SESSION-ARCHIVE-CLOSEOUT-SAFETY` |
| A6 | `WI-SESSION-ARCHIVE-ROOT-DEFAULT` plans to default `--exports-dir` from `resolve_archive_root()`. Zips land in `~/Downloads`, so a default derived from the archive root would never find one. The WI's `related_design` also points at `proposed/lrh-session-archive-sync`, which is now `adopted/`. | WI frontmatter/body; `export_transcript` contract. | Medium; the WI needs rescoping |
| A8 | **View > Copy URL is no longer visible.** In Claude.app 2.7032.0 the "Copy URL" menu item is defined only inside a `Debug` submenu declared `visible: false`, so users cannot reach it. `/lrh-closeout` Step 3 path 3 ("Paste View > Copy URL") and its path-1 rule ("if View > Copy URL disagrees with the env var, the browser URL wins") were therefore dead instructions. The same references appeared in `closeout-workflow.md`, `execution-session-reference.md`, and `lrh-land`. | `app.asar` menu definition; user report. | High for closeout correctness; **fixed in this change** (§8) |
| A9 | **The `/lrh-claude-session` gap is untracked.** The CLI half already exists: `lrh conversation current-claude-session-id` (`WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER`, PR #698, resolved), modelled on the Codex resolver. That WI's Non-Goals explicitly left "migrate `/lrh-closeout` Step 3 to use the new resolver" as "a natural follow-up", but no WI, proposal, backlog entry, open PR, branch, or local session transcript mentions `lrh-claude-session` or picks up that follow-up. Unlike `/lrh-codex-session`, there is no skill wrapper. | `grep` over `project/`, `src/`, `docs/`; `gh pr list`; `search_session_transcripts` (no hits for `lrh-claude-session`). | Medium; see R7 |
| A7 | The weekly `schedule` job runs `sync --project-root <checkout>` unattended. Any alias it reconciles is written into that checkout's `project/sessions/index.jsonl` as an **uncommitted change**, possibly on whatever branch that checkout has checked out. | `build_launchd_plist` `:373`; `reconcile_child_id_aliases`. | Medium; intersects the `lrh-land` main-worktree-lock work (§9) |

## 6) Recommendations

### 6.1 Unify the raw mirror and human-readable exports? Keep the artifacts separate; unify identity.

The two artifacts serve different contracts:
- The **raw mirror** is automatic, verbatim, and never-shrink. It is the
  durability guarantee against the roughly 30-day `~/.claude/projects`
  pruning.
- The **Markdown export** is explicit, rendered, and privacy-scanned. It is
  for human review.

Merging them would either make exports automatic, violating the
explicit-request contract, or make the mirror lossy. Keep them separate, and
document the rationale in `docs/reference/cli/sessions.md` and in the
exporter proposal.

Unify what they *mean* to the control plane instead:

- **R1: one identity pipeline, three sources in priority order**, all
  writing through `record_session_observation`:
  1. **Live desktop metadata** at `/lrh-implement` record creation and at
     `/lrh-closeout` Step 5. On path 1, pass `--title`/`--branch` from
     `get_session("self")` or the current transcript. On path 2, pass them
     from the `list_sessions` row. This is a skill-text change plus nothing
     new in the CLI.
  2. **Raw-JSONL extraction inside `sync`.** `reconcile_child_id_aliases`
     already parses every line. Extend it to collect `pr-link.prUrl`, the
     latest `custom-title`/`ai-title`, and the set of `gitBranch` values
     (→ `written_branches`). Upsert only for hosts already known, under the
     same no-new-host rule. This alone back-fills title, branch, PRs, and
     `written_branches` for every indexed session still on disk or in the
     raw archive. It should also read from `<archive>/raw/` so that pruned
     sessions are covered.
  3. **Zip harvest** stays as the retroactive and bootstrap path for host
     ids that no forward capture saw. Fix its field list (A2).
- **R2:** add `session_host_id` (when the env var or `--session-id` resolves
  it), `title`, `branch`, and `prs` to `/lrh-export-claude`'s frontmatter,
  so each export describes itself. Do **not** make the exporter write the
  index.
- **R3:** have `report` count `claude/exports/*.md` as coverage, as a
  weaker "rendered-only" class, and add an `antigravity-app` scheme (A3).

### 6.2 Close the `metadata.json` gap for Claude?

Yes, and through R1 sources 1 and 2, not through the zip. With in-app
`/export` removed, the zip can only be made by an agent calling
`export_transcript`. That writes a full, unredacted transcript into
`~/Downloads` in order to harvest about 6 identity fields. The same fields
come straight from `get_session`/`list_sessions` and the env vars with no
transcript copy at all. Rebuilding the harvest around an agent-triggered
zip would be strictly worse on privacy and no better on coverage.

Concrete follow-ups:
- **Keep the harvest code**, as a retroactive import for any old zips a user
  still has. Fix its field list (A2). Stop treating it as a live capture
  path in docs and proposals.
- **Optional one-time verification:** with the user's consent, call
  `export_transcript("self")` once, list the zip's members and
  `metadata.json` keys (not bodies), then delete it. This would confirm the
  schema that A2's fixes target.
- **Rescope `WI-SESSION-ARCHIVE-ROOT-DEFAULT` (A6).** Drop the
  "`--exports-dir` default" half. With no human trigger left, there is no
  steady stream of zips to discover. Keep only the archive-root decision,
  and fix its `related_design` path.

### 6.3 Surface skill drift proactively?

Yes, as three coordinated changes, in this order:

- **R4a: fix the classification first.** Write an install manifest when
  installing (for example `<skills_dir>/<skill>/.lrh-install.json` with the
  installed content hash and package version). Then `status` can report
  `stale` (installed == the last LRH-installed content, safe to upgrade
  without `--force`) separately from `modified` (the user edited it). Let
  `install` upgrade `stale` skills by default. Without this, any proactive
  warning just nags people toward `--force`.
- **R4b: detect CLI↔skill skew.** Give skills a declared minimum capability.
  For example, frontmatter `requires_lrh_commands: [sessions closeout-sync]`
  checked by `lrh skills check`, or a cheap `lrh capabilities` listing that
  skills probe before an "always run" step. Also make `lrh version` report
  the editable-install source path and its git HEAD when the distribution is
  editable, so skew is visible.
- **R4c: where to surface it.** Add a one-line, non-fatal footer to
  `lrh sessions closeout-sync`, for example
  `skills: 3 stale, 1 missing (lrh skills install --dry-run --diff)`.
  - It already runs on every closeout on the user's machine, and it is the
    natural place for a machine-state health line.
  - Keep it out of the schedule path's stdout noise by using the same
    function but only when stdout is a TTY or `--check-skills` is passed.
  - Also add it to `lrh project doctor`.
  - Do **not** hook it into `pip install`/version bumps. Editable installs
    never re-run install hooks, which is exactly the failure seen here.

### 6.4 Scope disclosure (Finding 5)

- **R5:** update the `/lrh-closeout` Step 4 gate bullet and the `/lrh-land`
  Step 6 preview so the sync line reads something like "`lrh sessions
  closeout-sync --project-root .`: mirrors **all** local Claude Code
  projects' transcripts into the private archive at `<resolved root>`;
  indexes only this repo's known sessions". Do this through a work item,
  with a gate-definition staleness refresh.
- Also add a summary line to sync's own output, for example
  `scanned 124 project buckets, 3,410 files`. This costs nothing.

### 6.5 Proposal hygiene

- **R6:** add a correction note to `PROP-LRH-SESSION-ARCHIVE-SYNC`:
  - the zip's actual producer and location;
  - forward capture omits title and branch;
  - the unbuilt Decision 2/3 pieces (A4), moved to explicit follow-ups;
  - JSONL now carries PR, title, and branch, which updates the Motivation's
    "the session-listing tools return the host id but not the child id"
    analysis.

  Add a matching note to `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` about its
  "Cowork-diagnostics" characterization.

  Also record in the archive-sync proposal that the zip's human trigger
  (in-app `/export`) and the Copy URL fallback are gone as of Claude.app
  2.7032.0.

### 6.6 A `/lrh-claude-session` skill (A9)

- **R7:** file the follow-up that `WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER`
  deferred. Add a `/lrh-claude-session` skill parallel to
  `/lrh-codex-session`: metadata-only, never exports. It would:
  - wrap `lrh conversation current-claude-session-id` for the current
    window;
  - enrich the result with title and branch from the session-management
    `get_session("self")` tool where that tool exists;
  - for another session, resolve through `list_sessions` (by PR, branch, or
    title), falling back to asking the user to pick from the list;
  - report `session_transcript: claude-app:<host-uuid-stem>` plus the
    identity fields R1 source 1 needs (`--title`, `--branch`, `--pr`).

  `/lrh-closeout` Step 3, `/lrh-land` Step 3, and `/lrh-implement` would
  then call the skill instead of repeating the resolution order in three
  places. The skill should tolerate an installed CLI that lacks the
  resolver (Finding 3's skew) by falling back to reading the env var
  directly.

## 7) Proposed follow-up work items (not created by this audit)

| Proposed ID | Covers | Depends on |
|---|---|---|
| `WI-SESSION-INDEX-JSONL-IDENTITY-EXTRACTION` | R1 source 2: extract `pr-link`, title, and `gitBranch` from raw JSONL in `sync` for known hosts, including archived raw copies | — |
| `WI-CLOSEOUT-SESSION-IDENTITY-TITLE-BRANCH` | R1 source 1: pass `--title`/`--branch` in `/lrh-closeout` and `/lrh-implement` | — |
| `WI-SESSION-EXPORT-HARVEST-FIELDS` | A2: harvest `writtenBranches`/`cwd`; index `prNumber` as a fallback; optionally verify the current zip schema (§6.2) | — |
| `WI-SKILLS-INSTALL-MANIFEST` | R4a: separate `stale` from `modified`; upgrade without `--force` | — |
| `WI-SKILLS-CLI-CAPABILITY-SKEW` | R4b + R4c: capability declaration, editable-install-aware `lrh version`, closeout-sync footer, `project doctor` | `WI-SKILLS-INSTALL-MANIFEST` |
| `WI-CLOSEOUT-ARCHIVE-SCOPE-DISCLOSURE` | R5: gate/preview text, plus the sync summary line | — |
| `WI-SESSION-REPORT-EXPORT-COVERAGE` | R2 + R3 | — |
| Rescope `WI-SESSION-ARCHIVE-ROOT-DEFAULT` | A6: drop the `--exports-dir` default half; fix its `related_design` path | — |
| `WI-SKILLS-LRH-CLAUDE-SESSION` | R7 / A9: `/lrh-claude-session` skill; migrate closeout/land/implement Step 3 to call it | — (the CLI resolver is already landed) |

`WI-SESSION-ARCHIVE-CLOSEOUT-SAFETY` (existing) already covers A5 and the
regeneration of the Codex/Antigravity generated targets.

## 8) Changes made with this audit

- `src/lrh/skills/lrh-land/SKILL.md` Step 3, and the identical edits in
  `.claude/skills/`, `.agents/skills/`, and `.gemini/plugins/lrh/skills/`:
  replaced the phantom `lrh sessions list` with the `list_sessions` tool
  matched by `prNumber`, and added a warning against substituting
  `discover`. `lrh skills check --target claude --local --source
  current-repo` reports the `.claude/` target clean afterwards.
- `docs/reference/cli/sessions.md` (`sync` section):
  - disclosed the machine-wide scan scope, and what `--project-root` does
    and does not scope;
  - described `session-export-*.zip` as a desktop-app artifact whose
    in-app `/export` trigger is gone as of 2.7032.0, reachable now only
    through the agent-side `export_transcript` tool, and therefore a
    retroactive-only path;
  - distinguished it from `/lrh-export-claude` output.
- **View > Copy URL removal (A8)**, in `lrh-closeout/SKILL.md`,
  `lrh-closeout/references/closeout-workflow.md`,
  `lrh-implement/references/execution-session-reference.md`, and
  `lrh-land/SKILL.md`, canonical plus all three generated copies:
  - Path 1 confirmation now shows the session's title and branch from
    `get_session("self")`, and falls through to path 2 or 3 if the user
    says it is the wrong session. It replaces "the browser URL wins".
  - Path 3 is now "pick from the session list" (`list_sessions`, optionally
    including archived sessions), with a pasted `local_<uuid>` from another
    source still accepted.
  - The Step 5 alias-capture and Step 8 reminder wording now match.
  - None of these edits are inside the `/lrh-closeout` gate-definition
    block; `lrh chain-defaults status` reports `stale: False` afterwards.
  - The Codex/Antigravity generated targets' pre-existing drift sets are
    unchanged.

## 9) Intersection with the `lrh-land` main-worktree-lock redesign

These are separate concerns, with one real point of contact.

`closeout-sync --project-root .` writes the committed
`project/sessions/index.jsonl` in whichever checkout it runs in. The weekly
`schedule` job does the same thing unattended (A7). Whatever the
detached-HEAD redesign decides about *where* closeout runs also determines:
- which branch the index change lands on;
- whether a scheduled sync can leave a dirty tree in the main worktree that
  the redesign's lock or cleanliness checks then trip over.

Archive-root resolution itself is independent of worktree choice, because
it is a home-relative path.
