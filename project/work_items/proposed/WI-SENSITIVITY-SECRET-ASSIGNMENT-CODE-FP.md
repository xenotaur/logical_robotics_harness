---
id: WI-SENSITIVITY-SECRET-ASSIGNMENT-CODE-FP
title: "Stop the secret-assignment rule from flagging code-shaped values"
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
blocked: false
blocked_reason: null
resolution: null
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams: []
related_design:
  - project/design/proposals/proposed/local-agent-dogfood/00_proposal.md
  - project/design/proposals/adopted/lrh-pii-scan/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - merge_pr
  - force_push
  - delete_branch
acceptance:
  - "Code-shaped values after a secret keyword no longer produce a `secret.keyword_assignment` finding, including `token: Callable[[], str] = ...`, `secret: Optional[str]`, `secret: str)`, `secret = finding.get(...)`, and a block colon such as `if secret:` followed by code on the next line."
  - "Real secret assignments are still flagged at high severity, including `token: ghp_...`, `api_key = \"sk-...\"`, `password: hunter2abc`, `TOKEN=abc123def456`, and YAML and .env forms."
  - "Before-and-after counts over this repository's tracked text files, the conversation test fixtures, and the `lrh pii` layer-2 tests are recorded in the execution record, with every newly unflagged match reviewed."
  - "tests/shared_tests/sensitivity_rules_test.py, tests/conversations_tests, and the pii layer-2 tests cover both sides, and `scripts/test` and `lrh validate` pass."
required_evidence:
  - lrh_validate
  - test_output
  - manual_review
artifacts_expected:
  - src/lrh/shared/sensitivity_rules.py
  - tests/shared_tests/sensitivity_rules_test.py
---

# Stop the Secret-Assignment Rule from Flagging Code-Shaped Values

## Summary

Narrow `SECRET_ASSIGNMENT_PATTERN` in `src/lrh/shared/sensitivity_rules.py` so
that code-shaped values after a secret keyword are no longer reported as
high-severity secrets, while real secret assignments in transcripts and
configuration text are still caught. Code-shaped values include annotations,
call expressions, block colons, and prose arrows.

## Problem / Context

The rule matches a keyword (`password`, `secret`, `token`, `api_key`, and so
on), then `=`, `:`, or `:=`, then optional whitespace, then four or more
non-space characters. That fits `token: abc123...` in a pasted transcript. It
also fits code. Matches measured at commit `5a673821`:

| File | Matched code | Value read as a secret |
| --- | --- | --- |
| `experimental/local_agent/recorder.py:99` | `token: Callable[[], str] = ...` | `Callable[[],` |
| `src/lrh/secrets/scan.py:104` and `review.py:103` | `secret = finding.get(...)` | `finding.get(` |
| `src/lrh/secrets/purge.py:184` | `secret: str)` | `str)` |
| `src/lrh/secrets/purge.py:206` | `if secret:` | the next line's `secrets.append(secret)` |
| `src/lrh/secrets/purge.py` docstrings | `secret==>placeholder` | `=>placeholder` |

The block-colon case matches because `\s*` after the separator crosses a
newline.

Of 149 tracked `.py` files under `experimental/local_agent/` and `src/lrh/`, 9
have a high-severity finding:

- five test files that deliberately contain fake secrets, which is correct;
- the four source modules above.

Not every one of the nine comes from this rule. The local-agent prototype
(`WI-LOCAL-AGENT-001`) excluded `recorder.py` on 2026-10-07 for this reason.
`src/lrh/secrets/` is also excluded there by its credential-like directory
name, so the rule matters for those modules mainly in other consumers.
`PROP-LOCAL-AGENT-DOGFOOD` Decision 3 now offers an explicit, logged,
category-bound owner override, but that is a workaround; the rule itself is
the root cause.

The rule is shared through `lrh.conversations.sensitivity`. Consumers:

- every conversation export (Claude, Codex, Antigravity, and PDF import);
- `lrh pii` layer 2 (`src/lrh/pii/layer2.py`);
- the local-agent prototype (`experimental/local_agent/sources.py` and
  `export.py`).

A looser rule could miss a real secret in any of them. That is the main risk
this work item must manage.

## Scope

`src/lrh/shared/sensitivity_rules.py` (`SECRET_ASSIGNMENT_PATTERN`, or a small
post-match filter beside it) and its tests, plus measurement against
repository files, conversation fixtures, and pii tests. Changing severities,
categories, other rules, or the local-agent prototype is out of scope.

## Required Changes

1. **Measure the baseline.** Count `secret.keyword_assignment` findings over
   tracked text files, the conversation test fixtures, and the pii layer-2
   tests, and classify a sample as true or false positives.
2. **Change the rule so that code-shaped values do not match.** Candidates:
   - do not let the whitespace after the separator cross a newline;
   - skip values that start an annotation or expression, such as an
     identifier followed by `[`, `(`, `)`, `|`, or `.`;
   - skip a separator that is part of an arrow or comparison (`==`, `=>`).

   Quoted or opaque values (`"..."`, long alphanumeric runs, known token
   prefixes) must still match. Prefer the narrowest change that removes the
   measured false positives.
3. **Re-measure.** Review every newly unflagged match and record the before
   and after counts in the execution record.
4. **Add tests on both sides:** the code forms that must not match, and the
   transcript, config, and pii forms that still must.

## Non-Goals

- No severity or category changes, and no relaxation of other rules.
- No allowlist mechanism; `lrh pii` and `lrh secrets` have their own.
- No change to the local-agent override or its path exclusions.

## Acceptance Criteria

- The code-shaped values above no longer produce `secret.keyword_assignment`
  findings.
- Real secret assignments in transcript, YAML, `.env`, and inline forms still
  produce high-severity findings.
- Before and after counts are recorded across all consumers, with every newly
  unflagged match reviewed.
- Both-sides tests pass, and so do `scripts/test` and `lrh validate`.

## Validation

- `scripts/test --log`
- `scripts/lint`
- `lrh validate`
- The before and after measurement output, summarized in the execution record.

## Risk Notes

A regex can only approximate "this is code". The failure mode that matters is
a real secret in a transcript or a pii-scanned file no longer being flagged.
That would weaken every consumer. Keep the change narrow, and treat any newly
unflagged match that is not clearly code as a reason to tighten the change.
