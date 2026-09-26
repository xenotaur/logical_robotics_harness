"""Human-readable inspection, sanitized export, and evaluation records.

Export includes provenance and metrics but excludes raw packet text, the
rendered prompt, and the raw model response. Briefing text is included only on
explicit request, and only when the local sensitivity scan finds nothing.
Every export lists what it excluded.
"""

from __future__ import annotations

import json
import pathlib

from local_agent import briefing, recorder
from lrh.conversations import sensitivity

EXPORT_SCHEMA_VERSION = "1"

ALWAYS_EXCLUDED = (
    "context packet text (reconstructible from the listed commit, paths, "
    "line ranges, and hashes)",
    "rendered prompt text (template recorded by version and sha256)",
    "raw model response text",
    "absolute local paths (home directory rewritten as ~)",
    "environment variables and credentials (never recorded)",
)

# Rubric fields a human records for each attempt. Values are validated loosely
# so the experiment report owns the scoring definitions.
EVALUATION_FIELDS = {
    "usefulness": (0, 1, 2),
    "correction_minutes": None,
    "review_minutes": None,
    "total_human_minutes": None,
    "cited_claims_checked": None,
    "cited_claims_supported": None,
    "unsupported_assertions": None,
    "critical_fabricated_status": None,
    "diagnostics_surfaced": (True, False),
    "miss_cause": (None, "context", "model", "task"),
    "notes": None,
}


class ExportError(ValueError):
    """Raised for an invalid evaluation or unsafe export request."""


def _home_relative(value: object, home: str) -> object:
    if isinstance(value, str):
        return value.replace(home, "~")
    if isinstance(value, dict):
        return {key: _home_relative(item, home) for key, item in value.items()}
    if isinstance(value, list):
        return [_home_relative(item, home) for item in value]
    return value


def inspect_run(store: recorder.Store, run_id: str) -> str:
    """Render a readable summary of one run without printing raw content."""
    run = store.load_run(run_id)
    events, truncated = store.events(run_id)
    packet_manifest, _ = store.load_packet(str(run["packet_sha256"]))
    lines = [
        f"run {run_id}",
        f"  work item: {run.get('work_item_id')}  task: {run.get('task_id')}",
        f"  source commit: {run.get('source_commit')}",
        f"  outcome: {run.get('outcome')} ({run.get('outcome_detail')})",
        f"  model: {json.dumps(run.get('model'), sort_keys=True)}",
        f"  usage: {json.dumps(run.get('usage'), sort_keys=True)}",
        f"  citations: {json.dumps(run.get('citations'), sort_keys=True)}",
        "  sources:",
    ]
    for source in packet_manifest.get("sources", []):  # type: ignore[union-attr]
        lines.append(
            f"    {source['source_id']} {source['path']} "
            f"L{source['line_start']}-{source['line_end']}/{source['total_lines']}"
            f"{' TRUNCATED' if source['truncated'] else ''} ({source['relation']})"
        )
    for omitted in packet_manifest.get("omitted_sources", []):  # type: ignore[union-attr]
        lines.append(f"    omitted {omitted['path']}: {omitted['reason']}")
    lines.append(f"  events: {len(events)}{' (truncated tail)' if truncated else ''}")
    for event in events:
        lines.append(f"    #{event['seq']} {event['type']}")
    return "\n".join(lines) + "\n"


def record_evaluation(
    store: recorder.Store, run_id: str, scores: dict[str, object]
) -> dict[str, object]:
    """Validate and store a human evaluation for one run."""
    unknown = sorted(set(scores) - set(EVALUATION_FIELDS))
    if unknown:
        raise ExportError(f"unknown evaluation fields: {unknown}")
    for field, allowed in EVALUATION_FIELDS.items():
        if allowed is not None and field in scores and scores[field] not in allowed:
            raise ExportError(f"{field} must be one of {allowed}")
    store.load_run(run_id)
    store.write_json(run_id, "evaluation.json", scores)
    store.append_event(run_id, "evaluation_recorded", fields=sorted(scores))
    return scores


def export_run(
    store: recorder.Store,
    run_id: str,
    out_dir: pathlib.Path,
    *,
    include_output: bool = False,
    home: str | None = None,
) -> pathlib.Path:
    """Write ``<out_dir>/<run_id>.json`` and return its path."""
    home_dir = home if home is not None else str(pathlib.Path.home())
    run = store.load_run(run_id)
    events, truncated = store.events(run_id)
    packet_manifest, _ = store.load_packet(str(run["packet_sha256"]))
    evaluation = store.read_json(run_id, "evaluation.json")
    if evaluation is not None:
        evaluation_scan = sensitivity.scan_text_for_sensitive_findings(
            json.dumps(evaluation, sort_keys=True)
        )
        if evaluation_scan.status != sensitivity.STATUS_NONE_DETECTED:
            raise ExportError(
                "evaluation withheld: sensitivity scan flagged its free text; "
                "edit the notes and re-record the evaluation"
            )

    excluded = list(ALWAYS_EXCLUDED)
    exported: dict[str, object] = {
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "run": run,
        "packet_manifest": packet_manifest,
        "events": events,
        "events_truncated_tail": truncated,
        "evaluation": evaluation,
        "excluded": excluded,
    }

    output = store.read_json(run_id, "output.json")
    parsed = output.get("briefing") if isinstance(output, dict) else None
    if include_output and parsed is not None:
        if not isinstance(evaluation, dict) or "usefulness" not in evaluation:
            raise ExportError(
                "briefing text is exported only for scored runs; record an "
                "evaluation with at least `usefulness` first"
            )
        scan = sensitivity.scan_text_for_sensitive_findings(
            json.dumps(parsed, indent=2, sort_keys=True)
        )
        if scan.status != sensitivity.STATUS_NONE_DETECTED:
            raise ExportError(
                f"briefing text withheld: sensitivity scan reported "
                f"{scan.finding_count} potential finding(s) in {scan.categories}"
            )
        exported["briefing"] = parsed
        exported["briefing_sensitivity_scan"] = scan.status
        exported["briefing_label"] = (
            "Model output record, scored separately; not project state."
        )
    else:
        excluded.append("parsed briefing text (use --include-output after review)")
        if parsed is not None:
            exported["briefing_claim_counts"] = {
                name: len(parsed.get(name, [])) for name in briefing.CLAIM_LISTS
            }

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{run_id}.json"
    path.write_text(
        json.dumps(_home_relative(exported, home_dir), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
