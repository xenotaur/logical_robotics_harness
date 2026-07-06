---
title: "Security Audit Report - Subprocess, XSS, and Secrets Scanning"
date: 2026-07-05
status: completed
type: audit
scope: security
---

# Security Audit Report: 2026-07-05

This document captures a lightweight security audit performed across the repository to identify potential vulnerabilities or defense-in-depth enhancements, focusing specifically on subprocess execution, cross-site scripting (XSS) vectors in local UI components, and secret scanning heuristics.

## Findings

### 1. Subprocess Execution and Timeouts

The codebase uses `subprocess.run` across development scripts and integrations, including:
- `src/lrh/dev/versioning.py`
- `src/lrh/dev/release_smoke.py`
- `src/lrh/integrations/github/gh_client.py`

**Observation:**
These calls correctly avoid `shell=True` (using `shell=False` implicitly by passing lists of arguments), successfully mitigating the most critical command injection vectors. However, the `subprocess.run` invocations do not define a `timeout`.

**Recommendation:**
While these are developer-facing tools, a lack of timeout could lead to hanging processes or local denial of service if an underlying command (like git or a pip install) stalls indefinitely. It is recommended to implement a sensible `timeout` parameter for all `subprocess.run` calls, or wrap them in a helper that enforces bounded execution time.

### 2. HTML Escaping and XSS Prevention

The local viewer implemented in `src/lrh/serve.py` manually renders HTML for a read-only HTTP interface.

**Observation:**
The module consistently and correctly uses `html.escape()` for user-provided or project-derived data (e.g., project names, IDs, paths). This effectively neutralizes XSS risks in the local viewer. The default behavior of Python's `html.escape` sets `quote=True`, which correctly escapes quotes (`"` to `&quot;`). In some places, `quote=True` is explicitly passed, while in others it relies on the default.

**Recommendation:**
The implementation is safe and secure. For code consistency and readability, it may be beneficial to standardize the usage of `html.escape(..., quote=True)` throughout `src/lrh/serve.py` so the intent is always explicit, though this is purely stylistic and not a security flaw.

### 3. Sensitivity Scanner Enhancements

The sensitivity scanner located at `src/lrh/conversations/sensitivity.py` uses heuristic regular expressions to detect secrets in conversation transcripts (e.g., PDFs exported from ChatGPT).

**Observation:**
The current rule set detects basic PII (SSN, Phone, Email) and some generic secrets (PEM blocks, generic token prefixes like `sk-` or `ghp_`, and keyword-based assignments like `password=xyz`).

**Recommendation:**
The scanner is functioning as designed as a heuristic safety rail. To improve defense-in-depth, we should consider expanding the `_BASIC_RULES` to include distinct patterns for high-value third-party credentials that are commonly leaked, such as:
- AWS Access Key IDs (`AKIA[0-9A-Z]{16}`)
- Slack API Tokens (`xox[baprs]-[0-9a-zA-Z]{10,48}`)
- Additional cloud provider specific token prefixes.

## Conclusion

No critical vulnerabilities were found during this audit. The current security posture relies heavily on the fact that LRH is designed to be a local harness operating on trusted repository data. Adding bounded execution times to subprocesses and expanding the sensitivity scanner represent the best immediate steps for defense-in-depth.