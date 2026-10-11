---
name: lrh-session-id
description: 'Report the current or specified agent session''s LRH `session_transcript:`
  pointer by detecting the vendor (Claude, Codex, or Antigravity) and running the
  matching lrh-session-id-<vendor> skill inline, without exporting or reading transcript
  content. Use when a closeout or execution record needs the session pointer and the
  caller does not want to pick the vendor skill itself.

  '
---

# lrh-session-id Skill

This skill is the delegating dispatcher for the session-ID skill family
(`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` Decision 2). It works out which
agent environment the session belongs to, then carries out the matching
`lrh-session-id-<vendor>` skill's steps inline. The variant owns the
resolution order, the pointer format, and the report; the dispatcher only
chooses the variant.

It is metadata-only and writes nothing, so it may be invoked directly by the
user or from `/lrh-closeout`, `/lrh-land`, and `/lrh-implement`. It never
exports, reads, or prints transcript content.

---

## Inputs

All arguments are optional:

```text
/lrh-session-id
/lrh-session-id claude
/lrh-session-id claude 716
/lrh-session-id codex 019fc43f-e2d9-7503-88cb-9d9a8136c111
/lrh-session-id antigravity
```

- If the **first** argument is exactly `claude`, `codex`, or `antigravity`
  (case-insensitive), it selects the vendor and is removed. Every remaining
  argument passes through to the variant unchanged.
- Any other first argument is not a vendor name. The vendor is then chosen
  from the environment (Step 1), and **all** arguments pass through to the
  variant unchanged — for example a Claude host id, PR number, or branch, or
  a Codex thread id.

---

## Reference Knowledge

The variants are installed sibling skills: `/lrh-session-id-claude`,
`/lrh-session-id-codex`, and, once it ships, `/lrh-session-id-antigravity`.
Resolve each one the way this skill itself was loaded — as a sibling in the
selected agent skills directory — not through a hardcoded
`src/lrh/skills/...` path, which does not exist in a client repository.

Each variant documents its own CLI contract (`lrh conversation --help` and
the variant's resolver subcommand). The LRH checkout's
`docs/reference/cli/conversation.md` is an optional maintainer reference, not
a client-repository prerequisite; a missing LRH-owned documentation file is
not evidence that session-id resolution is unavailable.

The environment signals, one per vendor:

| Vendor | Signal | Variant | Pointer |
|---|---|---|---|
| Claude | `CLAUDE_CODE_SESSION_ID` | `lrh-session-id-claude` | `claude-app:<host-uuid-stem>` |
| Codex | `CODEX_THREAD_ID` | `lrh-session-id-codex` | `codex-app:<thread-id>` |
| Antigravity | `ANTIGRAVITY_CONVERSATION_ID` | `lrh-session-id-antigravity` | `antigravity-app:<conversation-id>` |

---

## Safety Rules

Follow these rules for every run:

1. Do not export, archive, or read transcripts, and never call the
   session-management `export_transcript` tool. The export skills are the
   explicit, user-requested capture path.
2. Never guess the vendor. When no signal is present, or more than one is,
   ask (Step 1).
3. Never guess a pointer. If the selected variant is not installed, report
   the vendor as unsupported and `session_transcript: pending` (Step 2).
4. Do not route through a deprecated stub (for example `/lrh-codex-session`)
   as a fallback for a missing variant.
5. Do not print environment variable values while detecting the vendor;
   check only whether each one is set.
6. Add no gate, write step, or report field of its own, other than the
   vendor line in Step 3. The variant's own safety rules apply in full.

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
   and ask the user to name the vendor, or to accept
   `session_transcript: pending`. Do not pick one yourself.

### Step 2 -- Check the variant is installed

Look for the installed sibling skill `lrh-session-id-<vendor>` (its
`SKILL.md`). This is checked at run time, so a variant that ships later
is picked up without editing this dispatcher.

If it is not installed, stop and report:

```text
Vendor: <vendor> (selected via <argument | environment | user>)
Status: unsupported -- lrh-session-id-<vendor> is not installed
session_transcript: pending
```

If the vendor should be supported, suggest updating the installed skills
(`lrh skills install`). Do not derive a pointer by any other means.

### Step 3 -- Run the variant inline

Read the variant's `SKILL.md` and carry out its Execution Steps directly in
this session, with the passed-through arguments as its arguments. Follow its
inputs, safety rules, confirmation behaviour, and report format exactly.

Prefix the variant's report with one line:

```text
Vendor: <vendor> (selected via <argument | environment | user>)
```

Callers read the remaining fields — at least `session_transcript:`, plus any
alias fields the variant reports — exactly as they would from the variant
itself.

### Step 4 -- Close out

Tell the user that no transcript was exported or read. If they need a
private archive capture, the vendor's export skill must be requested
explicitly.
