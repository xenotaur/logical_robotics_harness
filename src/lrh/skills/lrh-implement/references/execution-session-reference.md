# Execution Session Reference

Practical facts from `PROP-LRH-EXECUTION-SESSIONS` needed when running
`/lrh-implement`. Read this before Step 3 (instruction phase) and Step 9
(execution record).

---

## Prompt workflow commands

### Mint a prompt ID

```bash
# For a work item:
lrh prompt label --slug <slug> --work-item <WI-ID>

# For an ad-hoc task:
lrh prompt label --slug <slug>
```

The `--slug` value is lower-kebab-case, derived from the work item ID:
`WI-SKILLS-LRH-SETUP` → `wi-skills-lrh-setup`. For ad-hoc tasks, ask the
user for a short descriptive slug if one is not obvious.

The command outputs a `prompt_id` in the form:

```
PROMPT(<WI-ID-OR-AD_HOC>:<SLUG_UPPER_UNDERSCORE>)[<ISO8601-TIMESTAMP>]
```

`<SLUG_UPPER_UNDERSCORE>` is the slug with `-` replaced by `_` then
uppercased: `wi-skills-lrh-setup` → `WI_SKILLS_LRH_SETUP`.

### Check for prior execution

```bash
lrh prompt check-execution --prompt-id "<id>" --project-root .
```

### Update execution record to landed

Use this after a PR merges, typically from `/lrh-closeout` Step 5:

```bash
/Users/centaur/anaconda3/envs/LRH/bin/lrh prompt update-execution \
  --execution-id <execution-id> \
  --status landed \
  --pr <pr-url> \
  --commit <merge-commit-sha> \
  --session-transcript <claude-app:uuid-or-pending> \
  --project-root .
```

- `--execution-id`: the `execution_id:` field value from the record
  (e.g. `2026_06_28_11_30_26_WI_PROMPT_CLI_CLOSEOUT`)
- `--commit`: required when `--status landed`; use the merge commit SHA
- `--session-transcript`: optional; if absent when the record was created,
  the command inserts it after the `commit:` line
- Only `in_progress → landed` is a valid status transition

If this returns a `landed` or `in_progress` record, stop and report to the
user — do not proceed without explicit instruction to rerun.

### Create execution record

```bash
lrh prompt record-execution \
  --prompt-id "<id>" \
  --work-item <WI-ID or AD_HOC> \
  --slug <slug> \
  --status in_progress \
  --project-root .
```

This creates a new file at:
`project/executions/<WI-ID-OR-AD_HOC>/<timestamp>_<SLUG_UPPER_UNDERSCORE>.md`

Immediately edit the generated file to add the three optional fields (below).

---

## Branch naming convention

Format: `<username>/<type>/<slug>`

Get the GitHub login for `<username>`:

```bash
gh api user --jq .login
```

Map the work item `type` field to `<type>`:

| Work item type | Branch type |
|---|---|
| `deliverable` | `feat` |
| `operation` | `chore` |
| `investigation` | `spike` |
| `evaluation` | `audit` |
| ad-hoc / unknown | `chore` |

`<slug>` is the same lower-kebab slug used for the prompt label.

Example: `xenotaur/feat/wi-skills-lrh-setup`

Do not use the `agents/<backend>/<id>` namespace — reserved for future
autonomous backends.

---

## Execution record optional fields

These three fields are defined by `PROP-LRH-EXECUTION-SESSIONS`. Add them
immediately after running `lrh prompt record-execution`:

```yaml
agent: claude_app
instruction_source: <path-or-description>
session_transcript: pending
```

### `agent`

Identifies the execution backend:

| Value | Use when |
|---|---|
| `claude_app` | Implemented in a Claude Code (Claude.app) session |
| `codex_cloud` | Submitted to and executed by Codex Cloud |
| `manual` | Implemented manually without an AI backend |

### `instruction_source`

References the instruction-phase artifact:

- Work item: path to the work item file (e.g.
  `project/work_items/proposed/WI-SKILLS-LRH-SETUP.md`)
- Ad-hoc: brief description of the task origin (e.g.
  `ad_hoc conversation — design session for /lrh-implement skill`)
- Codex Cloud: path or Taurcode reference to the prompt file

### `session_transcript`

References the Claude.app session. Use the short form only:

```
claude-app:<session-id>
```

The `<session-id>` is the UUID stem of the `.jsonl` file at:
`~/.claude/projects/<project-slug>/<session-id>.jsonl`

**Use `pending` when the session ID is not yet known.** Update the field
before or when the PR lands. Never commit an absolute path (`~/.claude/...`
or `/Users/...`) — it leaks your local workspace layout to everyone who
clones the repository.
