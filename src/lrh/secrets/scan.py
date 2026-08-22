"""Read-only secrets scanning for `lrh secrets scan`.

Wraps `gitleaks` (https://github.com/gitleaks/gitleaks) to scan a target
repository's full git history for leaked secrets. Writes two files into
`--out-dir` for later review by `lrh secrets review`:

  findings.json     - raw gitleaks report (rule, file, commit, line, secret)
  replacements.txt  - draft `git-filter-repo --replace-text` input, one
                       `<secret>==>***REMOVED-<RuleID>***` line per unique
                       secret found

Nothing here rewrites history or touches the repository under scan - this
command only reads and reports. The draft `replacements.txt` must go
through `lrh secrets review --apply` before `lrh secrets purge` will
accept it (see that command's own module docstring for the
runtime-enforced reviewed-replacements gate).

**Provider coverage is uneven, not uniform.** OpenAI/Anthropic/Gemini keys
have structural prefixes (`sk-proj-...`, `sk-ant-api03-...`, `AIza...`)
that gitleaks' default rules catch reliably regardless of surrounding
code. Azure-family keys (Azure OpenAI / Cognitive Services) have no
distinguishing prefix at all - they are only caught via contextual rules
(gitleaks' default `generic-api-key` rule, or a target repo's own
`.gitleaks.toml` extension), and are invisible entirely if assigned to a
variable name with no azure/aoai/key/secret hint. Separately, `.ipynb`
files store source as JSON-escaped strings on disk (`KEY = \"value\"`),
which can defeat delimiter-based detection regexes that don't account for
the escaping, regardless of provider - this is the exact bug that let a
live Azure key sit undetected in a real notebook (see
https://github.com/xenotaur/LCATS/pull/315, commit `fa308bb18`). This
command does not attempt to close either gap; scan coverage depends
entirely on gitleaks' own ruleset plus whatever a target repo's own
`.gitleaks.toml` adds via auto-discovery.

**This command must never suppress that auto-discovery.** `gitleaks
detect --source <path>` auto-discovers a `.gitleaks.toml` at the scanned
path's root with no extra flag - a target repo (e.g. one that added a
custom rule after its own real-secret incident) may depend on that for
correct scan coverage. This module never passes `--config`, `--no-config`,
`--no-git`, or any other flag that would override or suppress it.

Requires the `gitleaks` binary on PATH:
https://github.com/gitleaks/gitleaks#installing
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import shutil
import subprocess
import sys


def check_gitleaks_available() -> None:
    if shutil.which("gitleaks") is None:
        print(
            "FAIL: `gitleaks` not found on PATH. Install it first, e.g.:\n"
            "  brew install gitleaks\n"
            "See https://github.com/gitleaks/gitleaks#installing for other platforms.",
            file=sys.stderr,
        )
        raise SystemExit(1)


def _restrict_permissions(path: pathlib.Path) -> None:
    """Best-effort chmod 0600 - these files contain real secret values."""
    try:
        path.chmod(0o600)
    except OSError:
        pass


def run_gitleaks(project_root: pathlib.Path, report_path: pathlib.Path) -> None:
    cmd = [
        "gitleaks",
        "detect",
        "--source",
        str(project_root),
        "--log-opts=--all",
        "--report-format",
        "json",
        "--report-path",
        str(report_path),
        "--no-banner",
        "--exit-code",
        "0",
    ]
    subprocess.run(cmd, check=True)


def load_findings(report_path: pathlib.Path) -> list[dict]:
    if not report_path.exists() or report_path.stat().st_size == 0:
        return []
    with report_path.open() as f:
        return json.load(f)


def draft_replacements(findings: list[dict]) -> list[tuple[str, str]]:
    """Dedupe findings by secret value, return [(secret, placeholder), ...]."""
    by_secret: dict[str, str] = {}
    for finding in findings:
        secret = finding.get("Secret", "")
        rule_id = finding.get("RuleID", "unknown-rule")
        if not secret or secret in by_secret:
            continue
        by_secret[secret] = f"***REMOVED-{rule_id}***"
    return sorted(by_secret.items())


@dataclasses.dataclass(frozen=True)
class ScanResult:
    findings_count: int
    replacements_count: int
    findings_path: pathlib.Path
    replacements_path: pathlib.Path | None


def run_scan(project_root: pathlib.Path, out_dir: pathlib.Path) -> ScanResult:
    check_gitleaks_available()
    out_dir.mkdir(parents=True, exist_ok=True)
    findings_path = out_dir / "findings.json"
    replacements_path = out_dir / "replacements.txt"

    run_gitleaks(project_root, findings_path)
    _restrict_permissions(findings_path)
    findings = load_findings(findings_path)

    if not findings:
        # A stale replacements.txt from an earlier, dirtier scan of this
        # same --out-dir would otherwise sit here holding old live secrets
        # while this clean result reports replacements_path: null - remove
        # it so it can't be mistaken for the current scan's output.
        if replacements_path.exists():
            replacements_path.unlink()
        return ScanResult(0, 0, findings_path, None)

    replacements = draft_replacements(findings)
    with replacements_path.open("w") as f:
        for secret, placeholder in replacements:
            f.write(f"{secret}==>{placeholder}\n")
    _restrict_permissions(replacements_path)

    return ScanResult(
        len(findings), len(replacements), findings_path, replacements_path
    )


def format_text(result: ScanResult) -> str:
    lines = [f"gitleaks found {result.findings_count} finding(s) across all history."]
    if result.replacements_path is None:
        lines.append("Nothing to review. Not writing replacements.txt.")
    else:
        lines.append(
            f"Wrote {result.findings_count} raw finding(s) to {result.findings_path}"
        )
        lines.append(
            f"Wrote {result.replacements_count} unique secret(s) to "
            f"{result.replacements_path}"
        )
        lines.append(
            "\nSTOP: do not hand replacements.txt to `lrh secrets purge` "
            "directly.\nRun `lrh secrets review` to triage findings.json "
            "and produce a\nreviewed, purge-accepted replacements.reviewed.txt."
        )
    return "\n".join(lines)


def format_json(result: ScanResult) -> str:
    return json.dumps(
        {
            "findings_count": result.findings_count,
            "replacements_count": result.replacements_count,
            "findings_path": str(result.findings_path),
            "replacements_path": (
                str(result.replacements_path) if result.replacements_path else None
            ),
        },
        indent=2,
    )
