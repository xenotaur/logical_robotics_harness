"""Top-level orchestration for `lrh pii scan`.

Wires together every prior `lrh.pii` module into one end-to-end pass,
mirroring `lrh.secrets.scan`'s own `run_scan`/`format_text`/`format_json`
shape: enumerate every path ever added (`lrh.pii.enumerate`), flag
suspicious ones by type/name (`lrh.pii.layer1`), scan content per
`content_scan_scope` (`lrh.pii.layer2`), assemble the unified schema and
drop allowlisted findings (`lrh.pii.output`, `lrh.pii.allowlist`), and
write `pii_findings.json` to `--out-dir`.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib

from lrh.pii import allowlist as pii_allowlist
from lrh.pii import config as pii_config
from lrh.pii import enumerate as pii_enumerate
from lrh.pii import layer1 as pii_layer1
from lrh.pii import layer2 as pii_layer2
from lrh.pii import output as pii_output


@dataclasses.dataclass(frozen=True)
class ScanResult:
    findings_count: int
    allowlisted_count: int
    findings_path: pathlib.Path
    findings: tuple[pii_output.Finding, ...]


def run_scan(
    project_root: pathlib.Path,
    out_dir: pathlib.Path,
    config_path: pathlib.Path | None = None,
) -> ScanResult:
    config = pii_config.load_config(project_root, config_path=config_path)

    all_paths = pii_enumerate.enumerate_added_paths(project_root)
    layer1_findings = pii_layer1.flag_paths(all_paths, config)
    flagged_paths = [finding.path for finding in layer1_findings]
    layer2_findings = pii_layer2.content_findings_for_paths(
        project_root,
        flagged_paths=flagged_paths,
        all_paths=all_paths,
        config=config,
    )

    findings = pii_output.build_findings(project_root, layer1_findings, layer2_findings)
    allowlist = pii_allowlist.load_allowlist(project_root)
    remaining = pii_output.filter_allowlisted(findings, allowlist)

    out_dir.mkdir(parents=True, exist_ok=True)
    findings_path = out_dir / "pii_findings.json"
    findings_path.write_text(pii_output.render_json(remaining) + "\n", encoding="utf-8")

    return ScanResult(
        findings_count=len(remaining),
        allowlisted_count=len(findings) - len(remaining),
        findings_path=findings_path,
        findings=tuple(remaining),
    )


def format_text(result: ScanResult) -> str:
    """Full text report: written-to location, allowlist suppression
    count, then the per-finding detail `pii_output.render_text_summary`
    already knows how to render - not just the bare count, which forced
    users to open the JSON to see what was actually found (PR #654
    review, `chatgpt-codex-connector`)."""
    lines = [f"Findings written to {result.findings_path}."]
    if result.allowlisted_count:
        lines.append(f"{result.allowlisted_count} allowlisted finding(s) suppressed.")
    lines.append("")
    lines.append(pii_output.render_text_summary(list(result.findings)))
    return "\n".join(lines)


def format_json(result: ScanResult) -> str:
    return json.dumps(
        {
            "findings_count": result.findings_count,
            "allowlisted_count": result.allowlisted_count,
            "findings_path": str(result.findings_path),
        }
    )
