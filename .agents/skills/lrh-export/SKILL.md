---
name: lrh-export
description: 'Export the current or specified agent session transcript into LRH''s
  private session archive by detecting the vendor (Claude, Codex, or Antigravity)
  and running the matching lrh-export-<vendor> skill inline. The variant keeps its
  own transcript resolution, confirm-before-write gate, archive defaults, and metadata-only
  reporting.

  '
---

# lrh-export Skill

This skill is the delegating dispatcher for the export skill family
(`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decision 2). It works out which
agent environment the session belongs to, then carries out the matching
`lrh-export-<vendor>` skill's steps inline. The variant owns transcript
resolution, its confirm-before-write gate, the archive destination, and the
metadata-only report; the dispatcher only chooses the variant.

Unlike `/lrh-session-id`, this skill writes a durable archive copy (through
the variant), so it runs only on an explicit user request and is never
invoked proactively or chained from another skill on the agent's own
initiative.

---

## Inputs

All arguments are optional:

```text
/lrh-export
/lrh-export claude
/lrh-export claude --latest
/lrh-export codex 019fc43f-e2d9-7503-88cb-9d9a8136c111
/lrh-export antigravity --conversation-id <conversation-id>
```

- If the **first** argument is exactly `claude`, `codex`, or `antigravity`
  (case-insensitive), it selects the vendor and is removed. Every remaining
  argument passes through to the variant unchanged.
- Any other first argument is not a vendor name. The vendor is then chosen
  from the environment (Step 1), and **all** arguments pass through to the
  variant unchanged.
- Each variant interprets its arguments by its own Inputs section:
  `/lrh-export-claude` and `/lrh-export-antigravity` take discovery flags
  such as `--transcript-path`, `--latest`, and `--out`; `/lrh-export-codex`
  takes an optional thread id. Pass flags that the selected variant accepts.

---

## Reference Knowledge

The variants are installed skills: `/lrh-export-claude`, `/lrh-export-codex`,
and `/lrh-export-antigravity`. Resolve each one as an installed skill — in
any skills directory or scope the host loads (project or user), typically as
a sibling of this skill — not through a hardcoded `src/lrh/skills/...` path,
which does not exist in a client repository.

Each variant documents its own CLI contract (`lrh conversation --help` and
the variant's export subcommand). The LRH checkout's
`docs/reference/cli/conversation.md` is an optional maintainer reference, not
a client-repository prerequisite; a missing LRH-owned documentation file is
not evidence that export is unavailable.

The environment signals, one per vendor:

| Vendor | Signal | Variant |
|---|---|---|
| Claude | `CLAUDE_CODE_SESSION_ID` | `lrh-export-claude` |
| Codex | `CODEX_THREAD_ID` | `lrh-export-codex` |
| Antigravity | `ANTIGRAVITY_CONVERSATION_ID` | `lrh-export-antigravity` |

---

## Safety Rules

Follow these rules for every run:

1. Never guess the vendor. When no signal is present, or more than one is,
   ask (Step 1). A wrong guess writes a permanent archive copy of the wrong
   session.
2. Add no write step, archive default, or confirm gate of its own, and never
   skip or weaken the variant's. Its confirm-before-write gate, `--force`
   rule, and safety rules apply in full.
3. If the selected variant is not installed, stop and report it (Step 2). Do
   not export by any other means, and do not route through a deprecated stub
   (for example `/lrh-codex-export` or `/lrh-antigravity-export`).
4. Do not print environment variable values while detecting the vendor;
   check only whether each one is set.
5. Do not print, read for display, or commit transcript text. Report only
   what the variant's metadata-only report contains.

---

## Execution Steps

Work through these steps in order.

### Step 1 -- Select the vendor

1. **Explicit argument.** If the first argument names a vendor, use it, and
   drop it from the arguments passed through. Skip the rest of this step.
2. **Environment.** Otherwise check which signals are set, without printing
   their values:

   ```bash
   for v in CLAUDE_CODE_SESSION_ID CODEX_THREAD_ID ANTIGRAVITY_CONVERSATION_ID; do
     if [ -n "$(printenv "$v" | tr -d '[:space:]')" ]; then
       echo "$v=set"
     else
       echo "$v=unset"
     fi
   done
   ```

   Exactly one set: that is the vendor.
3. **Ask.** If none is set, or more than one is (for example Claude Code
   running inside a Codex-hosted terminal), list which signals were found
   and ask the user to name the vendor, or to stop. Do not pick one
   yourself. If the user stops, report that nothing was exported.

### Step 2 -- Check the variant is installed

Check whether the skill `lrh-export-<vendor>` is available: listed in this
session's available skills, or present (its `SKILL.md`) in any skills
directory or scope the host loads, project or user.

If it is not installed, stop and report:

```text
Vendor: <vendor> (selected via <argument | environment | user>; unsupported: lrh-export-<vendor> is not installed)
Nothing was exported.
```

If the vendor should be supported, suggest updating the installed skills
(`lrh skills install`).

### Step 3 -- Run the variant inline

State the selected vendor in one line:

```text
Vendor: <vendor> (selected via <argument | environment | user>)
```

Then read the variant's `SKILL.md` and carry out its Execution Steps
directly in this session, with the passed-through arguments as its
arguments. Follow its inputs, confirm-before-write gate, safety rules, and
report format exactly.

**How the variant's gate classifies this invocation.** The Claude and
Antigravity variants treat a user-typed invocation of the variant itself as
the explicit request; the Codex variant skips asking only when the user's
own message this turn explicitly requested the export. When the current
turn is the user's literal, typed `/lrh-export` command (with or without a
vendor argument) — it arrives as `<command-message>`/`<command-name>` tags
naming `/lrh-export`, or the equivalent explicit textual invocation the
platform surfaces — treat it exactly as a typed invocation of the selected
variant, which also satisfies the Codex condition: the dispatcher only
chose which skill the user's own command runs. Every other route —
`/lrh-export` offered proactively or chained from another skill or
workflow — is model-initiated for the variant's gate, and an unclear signal
is ambiguous, so the variant waits for confirmation. The Claude and
Antigravity dangerous-flag rule is unchanged: `--force` always waits for
confirmation, however the command arrived. (The Codex variant has no
`--force`.)

### Step 4 -- Close out

Report the variant's metadata-only result, prefixed by the `Vendor:` line
from Step 3. Do not add transcript content.
