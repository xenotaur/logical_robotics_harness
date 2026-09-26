"""Build an immutable, approved-before-use context packet for one work item.

The packet reuses existing LRH semantics instead of re-implementing them:
prompt readiness (``lrh.work_items.readiness``), execution-readiness
diagnostics (``lrh.assist.run_packet``), and related-context resolution
(``lrh.assist.ready_work_item``). Their diagnostics are preserved verbatim; an
unready item can be briefed but is never presented as ready.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import tempfile

from local_agent import settings, sources
from lrh.assist import ready_work_item, run_packet
from lrh.work_items import readiness

# Related-context relations in the order they are admitted under the budget.
_RELATION_PRIORITY = (
    "Dependency",
    "Workstream",
    "Design",
    "Focus",
    "Roadmap",
    "Status",
    "Evidence",
)


@dataclasses.dataclass(frozen=True)
class ContextPacket:
    """A materialized packet plus its manifest; hashed for explicit approval."""

    manifest: dict[str, object]
    text: str

    @property
    def sha256(self) -> str:
        return packet_sha256(self.manifest, self.text)


def packet_sha256(manifest: dict[str, object], text: str) -> str:
    """Hash the manifest and packet text together."""
    digest = hashlib.sha256()
    digest.update(json.dumps(manifest, sort_keys=True).encode("utf-8"))
    digest.update(b"\n\x00\n")
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()


def _relative(path: str | pathlib.Path, project_root: pathlib.Path) -> str:
    candidate = pathlib.Path(path)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(project_root.resolve()).as_posix()
        except ValueError:
            return candidate.name
    return candidate.as_posix()


def _collect_diagnostics(
    project_root: pathlib.Path, work_item_id: str
) -> tuple[dict[str, object], str, list[tuple[str, str, str]]]:
    """Return diagnostics, the work item path, and related-context candidates."""
    report = readiness.evaluate_readiness(
        project_root=project_root, work_item_id=work_item_id
    )
    item = report.items[0]
    work_item_path = project_root / item.path

    packet_result = run_packet.render_run_packet_from_work_item(
        work_item_path, project_root=project_root
    )
    execution_issues = [
        {"severity": issue.severity, "code": issue.code, "message": issue.message}
        for issue in packet_result.diagnostics
    ]

    candidates: list[tuple[str, str, str]] = []
    unresolved: list[dict[str, object]] = []
    context_error: str | None = None
    try:
        request = ready_work_item.render_ready_work_item_request(
            work_item_path, project_root=project_root
        )
    except (OSError, ValueError, KeyError) as error:
        context_error = f"{type(error).__name__}: {error}"
    else:
        for resolved in request.resolved_context:
            candidates.append(
                (
                    resolved.relation,
                    _relative(resolved.path, project_root),
                    "lrh.ready_work_item",
                )
            )
        for missing in request.unresolved_context:
            unresolved.append(
                {"relation": missing.relation, "reference": missing.reference}
            )

    diagnostics: dict[str, object] = {
        "work_item_id": item.work_item_id,
        "status": item.status,
        "prompt_readiness": {
            "prompt_ready": item.prompt_ready,
            "blocking_reasons": list(item.blocking_reasons),
            "warnings": list(item.warnings),
            "recommended_next": item.recommended_next,
        },
        "execution_readiness": {
            "execution_ready": not execution_issues,
            "issues": execution_issues,
        },
        "unresolved_references": unresolved,
        "context_resolution_error": context_error,
    }
    return diagnostics, item.path, candidates


def _prefix_fallback(
    unresolved: list[dict[str, object]],
    project_dir: str,
    project_root: pathlib.Path,
) -> list[tuple[str, str, str]]:
    """Resolve references written relative to the repository, not the project.

    Some repositories write ``related_design`` paths with the project
    subdirectory prefix (for example ``lcats/project/...``). LRH reports those
    as unresolved; that diagnostic is kept, and this fallback is labelled.
    """
    if project_dir in ("", "."):
        return []
    prefix = f"{project_dir.rstrip('/')}/"
    found: list[tuple[str, str, str]] = []
    for entry in unresolved:
        reference = str(entry["reference"])
        if reference.startswith(prefix):
            stripped = reference[len(prefix) :]
            if (project_root / stripped).is_file():
                found.append((str(entry["relation"]), stripped, "prefix_fallback"))
    return found


def build_packet(
    *,
    repo: pathlib.Path,
    repo_label: str,
    revision: str,
    project_dir: str,
    work_item_id: str,
    budgets: settings.Budgets,
    lrh_commit: str | None = None,
    lrh_code_dirty: bool | None = None,
) -> ContextPacket:
    """Build a packet for ``work_item_id`` from tracked content at ``revision``."""
    commit = sources.resolve_commit(repo, revision)
    with tempfile.TemporaryDirectory(prefix="lrh-local-agent-") as scratch:
        project_root = sources.materialize_project_tree(
            repo, commit, project_dir, pathlib.Path(scratch)
        )
        diagnostics, work_item_rel, candidates = _collect_diagnostics(
            project_root, work_item_id
        )
        unresolved = diagnostics["unresolved_references"]
        assert isinstance(unresolved, list)
        candidates.extend(_prefix_fallback(unresolved, project_dir, project_root))

    ordered = sorted(
        {(rel, path, how) for rel, path, how in candidates},
        key=lambda entry: (
            (
                _RELATION_PRIORITY.index(entry[0])
                if entry[0] in _RELATION_PRIORITY
                else len(_RELATION_PRIORITY)
            ),
            entry[1],
        ),
    )

    source_refs: list[dict[str, object]] = []
    omitted: list[dict[str, object]] = []
    sections: list[str] = []
    used = 0
    planned = [("WorkItem", work_item_rel, "lrh.readiness")] + [
        entry for entry in ordered if entry[1] != work_item_rel
    ]
    seen_paths: set[str] = set()
    for relation, rel_path, resolved_by in planned:
        if rel_path in seen_paths:
            continue
        seen_paths.add(rel_path)
        source_id = f"S{len(source_refs) + 1}"
        remaining = budgets.max_packet_bytes - used
        # The target work item may use the whole budget; context is capped.
        cap = remaining
        if relation != "WorkItem":
            cap = min(budgets.max_source_bytes, remaining)
        if cap <= 0:
            omitted.append({"path": rel_path, "relation": relation, "reason": "budget"})
            continue
        try:
            ref, text = sources.make_source(
                repo=repo,
                repo_label=repo_label,
                commit=commit,
                project_dir=project_dir,
                project_relative_path=rel_path,
                source_id=source_id,
                relation=relation,
                max_bytes=cap,
            )
        except sources.SourceError as error:
            omitted.append(
                {"path": rel_path, "relation": relation, "reason": str(error)}
            )
            continue
        if ref.included_bytes == 0:
            omitted.append({"path": rel_path, "relation": relation, "reason": "budget"})
            continue
        used += ref.included_bytes
        entry = ref.as_dict()
        entry["resolved_by"] = resolved_by
        source_refs.append(entry)
        sections.append(_render_source(ref, text))

    manifest: dict[str, object] = {
        "record_schema_version": settings.RECORD_SCHEMA_VERSION,
        "prototype_version": settings.PROTOTYPE_VERSION,
        "policy_version": settings.POLICY_VERSION,
        "repo_label": repo_label,
        "project_dir": project_dir,
        "source_commit": commit,
        "lrh_commit": lrh_commit,
        "lrh_code_dirty": lrh_code_dirty,
        "work_item_id": work_item_id,
        "diagnostics": diagnostics,
        "sources": source_refs,
        "omitted_sources": omitted,
        "source_bytes": used,
        "budgets": budgets.as_dict(),
    }
    text = _render_packet(manifest, sections)
    # Recorded after rendering: the size of the full text the model will see,
    # including diagnostics, headers, and line prefixes.
    manifest["rendered_bytes"] = len(text.encode("utf-8"))
    return ContextPacket(manifest=manifest, text=text)


def _render_source(ref: sources.SourceRef, text: str) -> str:
    header = (
        f"### [{ref.source_id}] {ref.path} ({ref.relation}; "
        f"lines {ref.line_start}-{ref.line_end} of {ref.total_lines})"
    )
    numbered = "".join(
        f"L{index}: {line if line.endswith(chr(10)) else line + chr(10)}"
        for index, line in enumerate(sources.split_lines(text), start=1)
    )
    marker = ""
    if ref.truncated:
        marker = (
            f"[TRUNCATED: {ref.total_lines - ref.line_end} more lines omitted by "
            "budget]\n"
        )
    return f"{header}\n{numbered}{marker}"


def _render_packet(manifest: dict[str, object], sections: list[str]) -> str:
    diagnostics = manifest["diagnostics"]
    lines = [
        f"# Context packet for {manifest['work_item_id']}",
        "",
        f"Repository: {manifest['repo_label']} at commit {manifest['source_commit']}",
        "",
        "## LRH diagnostics (authoritative; do not contradict)",
        "",
        "```json",
        json.dumps(diagnostics, indent=2, sort_keys=True),
        "```",
        "",
    ]
    omitted = manifest["omitted_sources"]
    if omitted:
        lines.append("## Sources omitted from this packet")
        lines.append("")
        for entry in omitted:  # type: ignore[union-attr]
            lines.append(f"- {entry['path']} ({entry['relation']}): {entry['reason']}")
        lines.append("")
    lines.append("## Sources (line-numbered; cite as S<n>:L<a>-L<b>)")
    lines.append("")
    return "\n".join(lines) + "\n" + "\n".join(sections)
