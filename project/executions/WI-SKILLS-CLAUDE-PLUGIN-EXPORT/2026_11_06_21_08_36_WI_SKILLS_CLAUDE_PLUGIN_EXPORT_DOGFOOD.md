---
execution_id: 2026_11_06_21_08_36_WI_SKILLS_CLAUDE_PLUGIN_EXPORT_DOGFOOD
prompt_id: PROMPT(WI-SKILLS-CLAUDE-PLUGIN-EXPORT:WI_SKILLS_CLAUDE_PLUGIN_EXPORT_DOGFOOD)[2026-11-06T21:08:36+00:00]
work_item: WI-SKILLS-CLAUDE-PLUGIN-EXPORT
status: landed
rerun_of: 2026_10_29_01_13_43_WI_SKILLS_CLAUDE_PLUGIN_EXPORT
pr: https://github.com/xenotaur/logical_robotics_harness/pull/859
commit: 216c451b4dac1b775c8f245734dfb51423ad172c
created_at: 2026-11-06T21:08:36+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/859
session_transcript: claude-app:b45207bd-f56d-4b2d-a182-23126acc88a6
---

# Summary

Cloud-session dogfood for `WI-SKILLS-CLAUDE-PLUGIN-EXPORT`, run by the human
on 2026-11-06 after PR #859 merged as `216c451b`. It was deferred by agreement
at the `/lrh-execute` chain gate to after merge, because claude.ai can only
sync the marketplace from the default branch. The agent turned the pasted
results into this record and checked the cited docs against the raw pages.
The primary record's body is untouched.

Verdict: the dogfood succeeds. The `lrh` plugin loads in claude.ai/code cloud
sessions, with and without a repository attached, and `/lrh:lrh-design` ran
end to end in a session with no repository.

# Result

## Setup on claude.ai (personal account)

- The marketplace `xenotaur/logical_robotics_harness` was added under
  Customize > Plugins. It took a couple of passes through the add flow.
  "Sync automatically" was part of that flow, the flow then asked for the
  marketplace again, and there is no separate sync button afterward.
- The plugin shows under "From marketplaces you added" as `Lrh`, "v1 · 27
  skills", "Synced from a repository · read-only", with 66 files under
  Contents. claude.ai labels it `v1` although `plugin.json` has no `version`.
- In claude.ai chat (claude.ai/new) the `lrh-*` skills autocomplete, labelled
  "Lrh plugin".

## claude.ai/code, before the first message

- The composer's `/lrh:` autocomplete is empty, with or without a repository
  selected. The `/skills` dialog does list all 27 skills under "From
  marketplaces you added". This is the composer not having loaded plugin
  skills yet, not a load failure.

## claude.ai/code, started session with the LRH repository attached

- `claude plugin list` (Claude Code 2.1.319): `lrh@synced`,
  `lrh-cloud-probe@synced`, and `lrh-cloud-probe-strict@synced`, all
  "√ loaded", "Version: unknown". Files are under
  `/root/.claude/plugins/synced/<account-id>/lrh`, next to `lrh.meta.json` and
  `manifest.json`, dated after the merge.
- The skill listing has both the repo's 26 unprefixed `lrh-*` skills and the
  plugin's 26 `lrh:lrh-*` skills.
- Once the session is running, the composer autocompletes `/lrh:` skills with
  their descriptions.
- `/reload-plugins` is refused ("isn't available over a remote connection in
  this session"). `/reload-skills` works: "84 skills available".

## claude.ai/code, started session with no repository

- The listing has the plugin's 26 `lrh:lrh-*` skills, the probe plugin, the
  `anthropic-skills:` account skills, and the built-in skills.
- `/lrh:lrh-design <idea>` ran the whole skill on a real request (a design for
  a novel-writing tracker app, from two attached spreadsheets). It ran the
  prior-art and demand checks, noted that `/home/user` is not a git
  repository and that there is no LRH repository to search, produced the full
  design, and stopped at the Step 4 handoff without invoking anything.
- Plain `/lrh-design <idea>` did not run the skill. The composer offered
  `lrh:lrh-design` as the completion, but the sent message was handled as
  ordinary text, and the session replied "/lrh-design isn't a command here".

## Open Question answers

1. **Does the short form resolve in a cloud session?** No. In a session with
   no repository, `/lrh-design` is not a command; the plugin skill answers
   only to `/lrh:lrh-design`. Users must type or pick the prefixed name. How
   in-skill cross-references such as "inline `/lrh-implement`" behave inside
   the plugin is untested; the model reads sibling skills by path, which the
   plugin layout keeps.
2. **Do the `_shared/` citations matter?** No, resolved by inspection. All 17
   plugin skills that cite `src/lrh/skills/_shared/` do so as a provenance
   pointer next to an inlined copy: 17 cite `github-network-execution.md`
   beside a section marked self-contained for installed client skills, and
   `lrh-execute` and `lrh-land` cite `chain-defaults.md`, whose flow is
   inlined in `lrh-land/references/land-workflow.md`. No skill needs the
   file to run, so neither bundling `_shared/` nor rewording is needed.
3. **Is the duplication in LRH-repo sessions harmful?** Not for typed
   commands: both copies load under different names. It does cost listing
   space. Claude Code drops skill descriptions when the listing exceeds its
   budget (skills.md, "Skill descriptions are cut short": "if you have many
   skills, Claude Code drops some descriptions to fit the listing's character
   budget"), and in that session most `lrh:` entries were listed without a
   description. That weakens Claude choosing a skill on its own, mainly in
   the LRH repository itself.
4. **Does a personal marketplace re-sync on push?** Still untested. The first
   sync after the merge worked; a later push was not tried.
5. **Same behavior with a repository attached?** Yes: `lrh@synced` loaded and
   its skills were listed in the repository-attached session.

## Other observations

- Manual-only is honored: the listing shows 26 of the 27 plugin skills, and
  the missing one is `lrh-codex-session`, the only skill with
  `disable-model-invocation: true`. `lrh-cloud-probe-strict` shows no skills
  for the same reason.
- `lrh-session-id`, `lrh-session-id-claude`, `lrh-session-id-codex`, and
  `lrh-codex-session` have no `when_to_use` in their canonical frontmatter,
  so they list without a "when to invoke" note. This is existing source
  frontmatter, not something the export dropped.

# Validation

- Evidence: the human's pasted session output and screenshots, 2026-11-06.
- Docs checked against the raw pages downloaded the same day:
  `code.claude.com/docs/en/plugins/loading.md` ("Synced plugins load in Cowork
  sessions and in terminal sessions" — claude.ai/code is not named),
  `plugins/install.md` (the cloud-session tab does not mention account
  plugins), `cloud-environments.md` (repo `.claude/skills/` load as part of
  the clone), `skills.md` (listing budget), and
  `claude.com/docs/plugins/overview` (`/reload-plugins` advice for Claude
  Code). Loading account plugins in claude.ai/code remains observed but
  undocumented.
- `grep` over `plugins/lrh/skills/*/SKILL.md` for the `_shared` citations and
  for missing `when_to_use`.

# Follow-up

- Update `docs/how-to/use-lrh-with-agent-assistants.md` §5 with these
  results:
  - repository-attached sessions are tested;
  - plugin skills appear in the composer only after the session starts, so
    check `/skills` instead;
  - only the prefixed `/lrh:lrh-*` form works;
  - start a new session to pick up a plugin change, since `/reload-plugins`
    is unavailable in cloud sessions;
  - the add flow includes Sync automatically, and there is no separate sync
    button afterward.
- Optional: decide whether the description-budget cost of loading both copies
  in LRH-repo sessions is worth addressing.
- Test re-sync on push the next time a skill change merges.
