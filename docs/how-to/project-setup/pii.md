# PII and Sensitive-Content Philosophy

## Purpose

Use this guide when deciding whether and how to check an LRH-managed repository for personally identifiable information (PII) or other content that shouldn't be in a source repository — a hardcoded personal hostname, an embedded email address outside its expected context, or an entire misplaced document such as a bank statement PDF or ID scan swept in during a file move. It is meant for humans and agents working together, across repositories with very different owners and risk profiles: a personal dotfiles repo, a shared team project, and a repo that may someday hold real customer data all warrant different judgment calls, and this guide is written to support that judgment rather than replace it.

This is a how-to and philosophy guide, not a mandate. LRH does not turn PII scanning on by default for any repository, and this document explains why, not just what.

## How this differs from `lrh secrets`

`lrh secrets scan` finds credential-shaped strings (API keys, tokens, private-key blocks) by wrapping `gitleaks`. It is a different tool for a different problem than PII detection, and the difference matters for how you use each one:

| | `lrh secrets` | PII detection |
| --- | --- | --- |
| What it looks for | Structurally identifiable secrets (key prefixes, high entropy) | Content that's sensitive because of what it is or where it appears |
| False-positive profile | Low — a key either matches or it doesn't | Higher by nature — the same email address can be a legitimate contributor listing or a real leak, depending entirely on context |
| Remediation | Rotate the credential, then purge it from history | Rarely the same move — see "Why remediation looks different" below |

If you're looking for leaked API keys or tokens, use `lrh secrets scan`. This guide and the `lrh pii scan` command it describes are for the adjacent, differently-shaped problem: content that is sensitive independent of any credential pattern.

## Core philosophy

1. **Opt-in, never mandated.** No LRH default wires PII scanning into any repository's pre-commit hooks or CI. You choose to run this, the same way you choose to run `lrh secrets scan`.

2. **Audit-first, prevention-second.** LRH does not require a CI or pre-commit setup before this capability is useful — it works standalone, on demand, against a repository's existing history. This isn't a placeholder for a prevention layer that hasn't been built yet; it's a deliberate ordering. Even LCATS — a repository that had a real, live credential leak reach production history — chose not to add secret- or PII-pattern scanning to its pre-commit hooks after the incident. Its fix was a structural one (stripping notebook cell outputs, the specific vector that leaked) plus a retroactive audit tool, not a content-pattern gate on every commit. Follow that precedent: reach for prevention only where a structural fix is available and cheap, and don't treat "we don't gate commits on this" as an unfinished state.

3. **Precision requirements scale with consequence.** A finding that only a human will review can tolerate more false positives than a finding that blocks a commit or a merge. This isn't a hypothetical concern — a real attempt to widen a credential-detection rule in LCATS inflated its findings from 7 to 59, almost all false positives, and was rejected for exactly this reason. Anything advisory-only can use heuristics that anything gating a workflow cannot. Keep that distinction in mind if you're deciding whether to wire a scan into a required check: the bar is higher there than it is for an on-demand audit.

4. **Prefer structural prevention over content classification, where available.** Before reaching for "detect whether this file's content is sensitive," ask whether the whole category of risk can be closed mechanically instead — the way stripping notebook outputs removes an entire leak vector without needing to judge any specific output's content. A `.gitignore` rule or a file-type check that keeps a whole class of document out of a repository is cheaper and more reliable than trying to classify what's inside one.

5. **Disclose limitations in the tool's own output, not only in documentation.** A scan result should say plainly what it did and did not check — no OCR, no ML-based content classification, heuristic and local only — not imply completeness it doesn't have.

6. **Human-in-the-loop remediation, always.** No tool in this space should auto-remove or auto-rewrite anything. A finding is a prompt for a person to decide what it means and what, if anything, to do about it.

## Why remediation looks different for PII than for credentials

A leaked credential has one clear fix: rotate it, then purge the old value from history so a stale clone can't resurrect it via merge. PII rarely works the same way. A stray hostname or personal path usually isn't dangerous enough to justify a disruptive history rewrite. An entire misplaced document — a bank statement, an ID scan — is a closer analogue to a credential purge (the whole file arguably shouldn't have existed in history at all), but even there, if the exposed content belongs to someone else, the fix may not be purely technical: some jurisdictions attach notification obligations to a real personal-data exposure that a `git-filter-repo` rewrite doesn't address on its own. Treat a PII finding as a prompt to think through the right response, not as something a purge command can close out by itself.

## Repo-configurability

LRH ships detectors and sensible defaults, not a fixed judgment about what's acceptable in your repository. A personal dotfiles repo and a repo destined to hold real customer records will reasonably disagree about what counts as noise versus a real problem. Configure and suppress findings at the repository level (an `.lrh-pii.toml`-style rule-extension file and a fingerprint-keyed allowlist, modeled on the `.gitleaks.toml`/`.gitleaksignore` conventions `lrh secrets` already follows) rather than expecting one global policy to fit every repository LRH manages.

## Where this applies across LRH's user tiers

LRH supports users ranging from someone who only wants generated prompts, to skill users, to people actively extending LRH itself. This guide's philosophy applies at every tier — none of them get PII scanning turned on for them — but how much of the tooling itself is relevant will differ: prompt- and skill-tier users mostly need to know this capability exists and what it does and doesn't check, while engineering-tier users are the ones actually running `lrh pii scan` and tuning its configuration. See `src/lrh/project/bootstrap.py` and the `project_bootstrap` templates for how LRH already delivers different guidance to different tiers — this document is expected to propagate through that same mechanism rather than a new one.

## What this does not do

- Does not classify document content using OCR or machine learning — detection is local, deterministic, and heuristic.
- Does not call any cloud service to inspect repository content.
- Does not remove, rewrite, or purge anything — findings are reported, never acted on automatically.
- Does not replace judgment about what's acceptable in a given repository — that stays with the repository's owner.

## Related reference

- [`lrh pii`](../../reference/cli/pii.md) — exact `lrh pii scan` command syntax, flags, output schema, and the allowlist fingerprint format.
