"""T0 ask: answer a free-form question about a checkout from tracked files.

One tool-less model call per question. Every run is recorded automatically in
the private store, including failures, so the owner judges the toy from its
log rather than from manual bookkeeping.
"""

from __future__ import annotations

import collections
import dataclasses
import hashlib
import math
import pathlib
import re
import statistics
from collections.abc import Callable

from local_agent import briefing, context, model, recorder, settings, sources

PROMPT_VERSION = "ask_v1"
KIND_ASK = "ask"
MODE_WORK_ITEM = "work_item"
MODE_FILES = "files"
MODE_OVERVIEW = "overview"
RATINGS = {"g": "good", "o": "ok", "b": "bad"}
_LISTING_LIMIT = 400
_README_NAMES = ("README.md", "README.rst", "README.txt", "README")


@dataclasses.dataclass(frozen=True)
class AskContext:
    """Sources assembled for one question, plus what was excluded and why."""

    mode: str
    repo: str
    source_commit: str
    text: str
    source_refs: list[dict[str, object]]
    excluded: list[dict[str, str]]
    diagnostics: dict[str, object] | None = None
    # Medium-severity categories found anywhere in the rendered context,
    # including diagnostics and the listing (names only, never values).
    context_warnings: tuple[str, ...] = ()


def _repo_relative(repo: pathlib.Path, path: str) -> str:
    candidate = pathlib.Path(path)
    if not candidate.is_absolute():
        candidate = (pathlib.Path.cwd() / candidate).resolve()
    try:
        return candidate.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path


def build_context(
    *,
    repo: pathlib.Path,
    revision: str = "HEAD",
    work_item: str | None = None,
    files: list[str] | None = None,
    project_dir: str = ".",
    repo_label: str = "repo",
    budgets: settings.Budgets | None = None,
) -> AskContext:
    """Assemble tracked-file context for a question (see ``_assemble``).

    The fully rendered context, including work-item diagnostics and the file
    listing, is scanned once more: a high-severity finding anywhere refuses
    the whole request (proposal Decision 3), naming categories only; medium
    categories are kept as context-wide warnings.
    """
    ctx = _assemble(
        repo=repo,
        revision=revision,
        work_item=work_item,
        files=files,
        project_dir=project_dir,
        repo_label=repo_label,
        budgets=budgets,
    )
    warnings = sources.check_text_allowed("assembled context", ctx.text)
    return dataclasses.replace(ctx, context_warnings=warnings)


def _assemble(
    *,
    repo: pathlib.Path,
    revision: str = "HEAD",
    work_item: str | None = None,
    files: list[str] | None = None,
    project_dir: str = ".",
    repo_label: str = "repo",
    budgets: settings.Budgets | None = None,
) -> AskContext:
    """Assemble tracked-file context for a question.

    With ``work_item``, reuse the LRH briefing packet (readiness diagnostics
    included). With ``files``, send those tracked files. Otherwise send the
    README and a listing of tracked paths.
    """
    budgets = budgets or settings.Budgets()
    root = sources.repo_root(repo)
    commit = sources.resolve_commit(root, revision)

    if work_item is not None:
        packet = context.build_packet(
            repo=root,
            repo_label=repo_label,
            revision=commit,
            project_dir=project_dir,
            work_item_id=work_item,
            budgets=budgets,
        )
        omitted = packet.manifest.get("omitted_sources", [])
        assert isinstance(omitted, list)
        refs = packet.manifest.get("sources", [])
        assert isinstance(refs, list)
        diagnostics = packet.manifest.get("diagnostics")
        return AskContext(
            mode=MODE_WORK_ITEM,
            repo=str(root),
            source_commit=commit,
            text=packet.text,
            source_refs=refs,
            excluded=[
                {"path": str(entry["path"]), "reason": str(entry["reason"])}
                for entry in omitted
            ],
            diagnostics=diagnostics if isinstance(diagnostics, dict) else None,
        )

    candidates: list[str] = []
    listing = ""
    if files:
        mode = MODE_FILES
        # Keep order, drop repeats: each file is sent (and counted) once.
        candidates = list(dict.fromkeys(_repo_relative(root, path) for path in files))
    else:
        mode = MODE_OVERVIEW
        tracked = sources.list_tracked_files(root, commit)
        candidates = [name for name in _README_NAMES if name in tracked][:1]
        visible = []
        for path in tracked:
            try:
                sources.check_path_allowed(path)
            except sources.SourceError:
                continue
            visible.append(path)
        shown = visible[:_LISTING_LIMIT]
        more = len(visible) - len(shown)
        listing = "### Tracked files (not citable)\n" + "\n".join(shown)
        if more > 0:
            listing += f"\n[... {more} more tracked files not listed]"
        listing += "\n"

    refs: list[dict[str, object]] = []
    excluded: list[dict[str, str]] = []
    sections: list[str] = []
    used = 0
    for path in candidates:
        remaining = budgets.max_packet_bytes - used
        if remaining <= 0:
            excluded.append({"path": path, "reason": "budget"})
            continue
        try:
            ref, text = sources.make_source(
                repo=root,
                repo_label=repo_label,
                commit=commit,
                project_dir=".",
                project_relative_path=path,
                source_id=f"S{len(refs) + 1}",
                relation="File" if mode == MODE_FILES else "README",
                max_bytes=remaining,
            )
        except sources.SourceError as error:
            excluded.append({"path": path, "reason": str(error)})
            continue
        if ref.included_bytes == 0:
            # A first line longer than the remaining budget leaves nothing to
            # send; an empty section would only invite invented citations.
            excluded.append({"path": path, "reason": "budget"})
            continue
        used += ref.included_bytes
        refs.append(ref.as_dict())
        sections.append(context.render_source(ref, text))

    body = "\n".join(sections)
    if listing:
        body = (body + "\n" + listing) if body else listing
    if excluded:
        body += "\n### Excluded sources\n" + "\n".join(
            f"- {entry['path']}: {entry['reason']}" for entry in excluded
        )
    return AskContext(
        mode=mode,
        repo=str(root),
        source_commit=commit,
        text=body,
        source_refs=refs,
        excluded=excluded,
    )


def unsendable_reason(ctx: AskContext) -> str | None:
    """Why ``ctx`` must not be sent to the model, or ``None`` if it may be.

    File questions need at least one included source, and work-item
    questions need the work item itself; otherwise the model would answer
    from little or nothing and invent citations. Overview questions always
    carry the tracked-file listing.
    """
    if ctx.mode == MODE_OVERVIEW:
        return None
    if not ctx.source_refs:
        return "all requested sources were excluded; nothing to answer from"
    if ctx.mode == MODE_WORK_ITEM and not any(
        ref.get("relation") == "WorkItem" for ref in ctx.source_refs
    ):
        return "the work item itself was excluded; its text would not be sent"
    return None


def source_summary(ctx: AskContext) -> str:
    """One short block describing what will be sent to the model."""
    sent = len(ctx.source_refs)
    requested = sent + len(ctx.excluded)
    listing = " + tracked-file listing" if ctx.mode == MODE_OVERVIEW else ""
    lines = [
        f"sources ({ctx.mode}, commit {ctx.source_commit[:12]}): "
        f"sending {sent} of {requested}{listing}"
    ]
    for ref in ctx.source_refs:
        truncated = " TRUNCATED" if ref.get("truncated") else ""
        warnings = ref.get("sensitivity_warnings") or ()
        warned = f" WARN: {', '.join(warnings)}" if warnings else ""
        lines.append(
            f"  {ref['source_id']} {ref['path']} "
            f"L{ref['line_start']}-{ref['line_end']}/{ref['total_lines']}"
            f"{truncated}{warned}"
        )
    for entry in ctx.excluded:
        lines.append(f"  excluded {entry['path']}: {entry['reason']}")
    if ctx.context_warnings:
        lines.append(
            f"  context WARN: {', '.join(ctx.context_warnings)} "
            "(medium findings anywhere in what will be sent)"
        )
    reason = unsendable_reason(ctx)
    if reason:
        lines.append(f"  NOT SENDING: {reason}")
    return "\n".join(lines)


def render_prompt(question: str, ctx: AskContext) -> str:
    template = briefing.load_prompt_template(PROMPT_VERSION)
    values = {"QUESTION": question.strip(), "CONTEXT": ctx.text}
    # One pass, so placeholder text inside the question is never expanded.
    return re.sub(r"\{\{(QUESTION|CONTEXT)\}\}", lambda m: values[m[1]], template)


def _kind_outcome(kind: str) -> str:
    return {
        model.KIND_MISSING_PREREQUISITE: "missing_prerequisite",
        model.KIND_TIMEOUT: "timeout",
    }.get(kind, "backend_error")


def run_ask(
    *,
    store: recorder.Store,
    question: str,
    ctx: AskContext,
    adapter: model.ModelAdapter,
    budgets: settings.Budgets,
    on_text: Callable[[str], None] | None = None,
) -> str:
    """Answer one question with one call; return the run id.

    The run is recorded whatever happens. ``completed`` means inference
    produced a non-empty answer, not that the answer is correct.
    """
    prompt = render_prompt(question, ctx)
    template_hash = hashlib.sha256(
        briefing.load_prompt_template(PROMPT_VERSION).encode("utf-8")
    ).hexdigest()
    run_id = store.start_run(
        {
            "record_schema_version": settings.RECORD_SCHEMA_VERSION,
            "prototype_version": settings.PROTOTYPE_VERSION,
            "kind": KIND_ASK,
            "question": question,
            **context_fields(ctx),
            "prompt_version": PROMPT_VERSION,
            "prompt_template_sha256": template_hash,
            "model": adapter.describe(),
            "budgets": budgets.as_dict(),
            "outcome": None,
            "rating": None,
        }
    )
    store.append_event(run_id, "attempt_started")

    streamed: list[str] = []

    def collect(chunk: str) -> None:
        streamed.append(chunk)
        if on_text is not None:
            on_text(chunk)

    def finish(outcome: str, detail: str, **extra: object) -> str:
        store.append_event(run_id, "outcome", outcome=outcome, detail=detail)
        store.update_run(run_id, outcome=outcome, outcome_detail=detail, **extra)
        return run_id

    def keep_partial() -> None:
        # The owner has already seen streamed text; keep it for review.
        if streamed:
            store.write_json(
                run_id, "output.json", {"answer": "".join(streamed), "partial": True}
            )

    try:
        reason = unsendable_reason(ctx)
        if reason:
            return finish("missing_prerequisite", reason)
        try:
            preflight = adapter.preflight()
        except model.BackendError as error:
            return finish(_kind_outcome(error.kind), f"preflight: {error}")
        store.append_event(run_id, "preflight_passed", preflight=preflight)
        store.update_run(run_id, preflight=preflight, model=adapter.describe())

        estimated = settings.estimate_tokens(prompt)
        if estimated > budgets.max_estimated_input_tokens:
            return finish(
                "budget_exhausted",
                f"estimated input {estimated} tokens exceeds "
                f"{budgets.max_estimated_input_tokens}; narrow the question's "
                "sources",
                estimated_input_tokens=estimated,
            )
        store.append_event(run_id, "model_request", estimated_input_tokens=estimated)
        try:
            response = adapter.generate(
                model.ModelRequest(
                    prompt=prompt, output_schema=None, budgets=budgets, on_text=collect
                )
            )
        except model.BackendError as error:
            keep_partial()
            return finish(_kind_outcome(error.kind), f"generate: {error}")

        usage = {
            "estimated_input_tokens": estimated,
            "prompt_tokens": response.prompt_tokens,
            "output_tokens": response.output_tokens,
            "thinking_chars": response.thinking_chars,
            "done_reason": response.done_reason,
            "backend_timings": response.backend_timings,
        }
        store.write_json(run_id, "output.json", {"answer": response.text})
        store.append_event(run_id, "model_response", **usage)
        citations = briefing.check_text_citations(response.text, ctx.source_refs)
        if response.done_reason == "length" or (
            response.output_tokens is not None
            and response.output_tokens > budgets.max_output_tokens
        ):
            return finish(
                "budget_exhausted",
                "answer hit the output token limit (partial answer kept)",
                usage=usage,
                citations=citations,
            )
        if not response.text.strip():
            detail = "empty answer"
            if response.thinking_chars:
                detail += f" ({response.thinking_chars} chars of hidden reasoning)"
            return finish("invalid_model_output", detail, usage=usage)
        return finish(
            "completed",
            "answer produced (not human-accepted)",
            usage=usage,
            citations=citations,
        )
    except KeyboardInterrupt:
        keep_partial()
        finish("cancelled", "interrupted by user")
        raise
    except Exception as error:
        keep_partial()
        finish("backend_error", f"unexpected {type(error).__name__}: {error}")
        raise


def context_fields(ctx: AskContext) -> dict[str, object]:
    """Run-record fields describing the assembled context (no source text)."""
    return {
        "mode": ctx.mode,
        "repo": ctx.repo,
        "source_commit": ctx.source_commit,
        "sources": ctx.source_refs,
        "excluded_sources": ctx.excluded,
        "context_warnings": list(ctx.context_warnings),
        "diagnostics": ctx.diagnostics,
    }


def record_failure(
    store: recorder.Store,
    question: str,
    outcome: str,
    detail: str,
    ctx: AskContext | None = None,
) -> str:
    """Log an ``ask`` that stopped before a model call (context, adapter, or
    confirmation); return the run id. Nothing was sent to the model.

    Pass ``ctx`` when the context was already assembled, so the record keeps
    its provenance (commit, sources, exclusions) like a normal run.
    """
    run_id = store.start_run(
        {
            "record_schema_version": settings.RECORD_SCHEMA_VERSION,
            "prototype_version": settings.PROTOTYPE_VERSION,
            "kind": KIND_ASK,
            "question": question,
            **(context_fields(ctx) if ctx is not None else {}),
            "prompt_version": PROMPT_VERSION,
            "outcome": None,
            "rating": None,
        }
    )
    store.append_event(run_id, "outcome", outcome=outcome, detail=detail)
    store.update_run(run_id, outcome=outcome, outcome_detail=detail)
    return run_id


def record_rating(
    store: recorder.Store, run_id: str, rating: str, note: str = ""
) -> dict[str, object]:
    """Store the owner's one-key rating (g/o/b or good/ok/bad) and note."""
    value = RATINGS.get(rating, rating)
    if value not in RATINGS.values():
        raise ValueError(f"rating must be one of g/o/b or {sorted(RATINGS.values())}")
    entry = {"value": value, "note": note.strip()}
    store.update_run(run_id, rating=entry)
    store.append_event(run_id, "rated", rating=value, has_note=bool(entry["note"]))
    return entry


def footer(store: recorder.Store, run_id: str) -> str:
    """One line summarizing a finished run."""
    run = store.load_run(run_id)
    usage = run.get("usage") or {}
    assert isinstance(usage, dict)
    timings = usage.get("backend_timings") or {}
    assert isinstance(timings, dict)
    parts = [f"run {run_id}", str(run.get("outcome"))]
    elapsed = timings.get("client_elapsed_seconds")
    if elapsed is not None:
        parts.append(f"{elapsed}s")
    if usage.get("output_tokens") is not None:
        parts.append(f"{usage['output_tokens']} tokens out")
    citations = run.get("citations")
    if isinstance(citations, dict) and citations.get("citations_total"):
        parts.append(
            f"citations {citations['citations_resolved']}/"
            f"{citations['citations_total']} resolve"
        )
    if run.get("outcome") != "completed":
        parts.append(str(run.get("outcome_detail")))
    return " · ".join(parts)


def _is_flagged(run: dict[str, object]) -> bool:
    citations = run.get("citations")
    unresolved = isinstance(citations, dict) and bool(
        citations.get("unresolved_citations")
    )
    return run.get("outcome") != "completed" or unresolved


def _counts(counter: dict[str, int]) -> str:
    return ", ".join(f"{key} {value}" for key, value in sorted(counter.items()))


def summarize(store: recorder.Store, limit: int = 10) -> str:
    """Recent runs plus statistics computed from every stored run."""
    runs = []
    for run_id in store.list_runs():
        try:
            runs.append(store.load_run(run_id))
        except (recorder.StoreError, ValueError):
            continue
    if not runs:
        return "no runs recorded yet\n"
    outcomes = collections.Counter(str(run.get("outcome")) for run in runs)
    kinds = collections.Counter(str(run.get("kind", "brief")) for run in runs)
    ratings = collections.Counter(
        (
            str(run["rating"]["value"])
            if isinstance(run.get("rating"), dict)
            else "unrated"
        )
        for run in runs
    )
    latencies: list[float] = []
    output_tokens: list[int] = []
    resolved = total = 0
    for run in runs:
        usage = run.get("usage")
        if isinstance(usage, dict):
            timings = usage.get("backend_timings") or {}
            if isinstance(timings, dict) and timings.get("client_elapsed_seconds"):
                latencies.append(float(timings["client_elapsed_seconds"]))
            if isinstance(usage.get("output_tokens"), int):
                output_tokens.append(int(usage["output_tokens"]))
        citations = run.get("citations")
        if isinstance(citations, dict):
            resolved += int(citations.get("citations_resolved") or 0)
            total += int(citations.get("citations_total") or 0)

    lines = [
        f"runs: {len(runs)} ({_counts(kinds)})",
        f"outcomes: {_counts(outcomes)}",
        f"ratings: {_counts(ratings)}",
    ]
    if latencies:
        ordered = sorted(latencies)
        # Nearest-rank p90: the ceil(0.9 * n)-th observation, one-based.
        p90 = ordered[max(0, math.ceil(0.9 * len(ordered)) - 1)]
        lines.append(
            f"latency: median {statistics.median(ordered):.1f}s, p90 {p90:.1f}s"
        )
    if output_tokens:
        lines.append(f"output tokens: median {statistics.median(output_tokens):.0f}")
    if total:
        lines.append(f"citations resolving: {resolved}/{total}")
    lines.append(f"flagged runs: {sum(1 for run in runs if _is_flagged(run))}")
    lines.append("")
    lines.append("recent:")
    for run in sorted(runs, key=lambda r: str(r.get("created_at")))[-limit:]:
        rating = run.get("rating")
        rated = rating["value"] if isinstance(rating, dict) else "-"
        label = run.get("question") or run.get("work_item_id") or ""
        label = str(label).replace("\n", " ")
        if len(label) > 60:
            label = label[:57] + "..."
        flag = " !" if _is_flagged(run) else ""
        lines.append(
            f"  {run.get('run_id')} {run.get('outcome')} [{rated}]{flag} {label}"
        )
    return "\n".join(lines) + "\n"
