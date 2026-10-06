"""Command line for the local-agent toys.

T0 (use these)::

    ask      -> answer a question from tracked files; streams, logs, asks a rating
    rate     -> rate a run later (g/o/b) with an optional note
    log      -> recent runs and statistics computed from the private log
    delete   -> remove one run's private records
    prune    -> remove runs older than a date

Legacy stage-0 pilot commands (superseded; kept until reworked)::

    packet   -> build and store a pinned context packet; prints its sha256
    task     -> the same, for a pre-registered task id from tasks.yaml
    run      -> brief it once, only if --approve matches that sha256
    b0       -> record an owner-written baseline briefing for a packet
    inspect  -> readable run summary (no raw content)
    evaluate -> record human rubric scores from a JSON file
    export   -> sanitized JSON export (briefing text only on request)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

from local_agent import (
    ask,
    briefing,
    context,
    export,
    model,
    recorder,
    runner,
    settings,
    sources,
    tasks,
)
from lrh.work_items import readiness


def _git_output(*args: str) -> str:
    here = pathlib.Path(__file__).resolve().parent
    completed = subprocess.run(
        ["git", "-C", str(here), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _lrh_commit() -> str | None:
    return _git_output("rev-parse", "HEAD") or None


def _lrh_code_dirty() -> bool:
    """Whether the prototype code differs from the recorded commit."""
    here = pathlib.Path(__file__).resolve().parent
    return bool(_git_output("status", "--porcelain", "--", str(here)))


def _budgets(args: argparse.Namespace) -> settings.Budgets:
    defaults = settings.Budgets()
    return settings.Budgets(
        max_packet_bytes=args.max_packet_bytes or defaults.max_packet_bytes,
        max_source_bytes=defaults.max_source_bytes,
        max_estimated_input_tokens=defaults.max_estimated_input_tokens,
        num_ctx=getattr(args, "num_ctx", None) or defaults.num_ctx,
        max_output_tokens=getattr(args, "max_output_tokens", None)
        or defaults.max_output_tokens,
        wall_time_seconds=getattr(args, "timeout", None) or defaults.wall_time_seconds,
        temperature=defaults.temperature,
        seed=defaults.seed,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="local_agent",
        description="Stage-0 local work-item briefing prototype (experimental).",
    )
    parser.add_argument(
        "--store",
        type=pathlib.Path,
        default=None,
        help=f"private store root (default: ${settings.STORE_ENV_VAR} or "
        "~/.local/share/lrh/local-agent)",
    )
    parser.add_argument(
        "--max-packet-bytes", type=int, default=None, help=argparse.SUPPRESS
    )
    sub = parser.add_subparsers(dest="command", required=True)

    asker = sub.add_parser("ask", help="T0: answer a question from tracked files")
    asker.add_argument("question")
    scope = asker.add_mutually_exclusive_group()
    scope.add_argument("--wi", default=None, help="scope to a work item (WI-...)")
    scope.add_argument("--files", nargs="+", default=None, help="tracked files")
    asker.add_argument(
        "--repo", type=pathlib.Path, default=pathlib.Path("."), help="checkout"
    )
    asker.add_argument("--commit", default="HEAD", help="revision to read")
    asker.add_argument(
        "--project-dir", default=".", help="subdirectory holding project/ (--wi)"
    )
    asker.add_argument("--no-rate", action="store_true", help="skip the rating prompt")
    asker.add_argument(
        "--yes", action="store_true", help="send without the confirmation prompt"
    )
    _add_backend_args(asker)

    rater = sub.add_parser("rate", help="rate a run: g(ood), o(k), or b(ad)")
    rater.add_argument("run_id")
    rater.add_argument("rating", choices=("g", "o", "b", "good", "ok", "bad"))
    rater.add_argument("--note", default="")

    logger = sub.add_parser("log", help="recent runs and summary statistics")
    logger.add_argument("--limit", type=int, default=10)

    deleter = sub.add_parser("delete", help="permanently remove one run")
    deleter.add_argument("run_id")

    pruner = sub.add_parser("prune", help="remove runs created before a date")
    pruner.add_argument("--before", required=True, help="ISO date, e.g. 2026-12-31")
    pruner.add_argument("--dry-run", action="store_true")

    packet = sub.add_parser("packet", help="build and store a pinned context packet")
    packet.add_argument("--repo", type=pathlib.Path, required=True)
    packet.add_argument("--repo-label", required=True, help="e.g. LRH or LCATS")
    packet.add_argument("--commit", required=True, help="pinned source revision")
    packet.add_argument(
        "--project-dir", default=".", help="subdirectory holding project/"
    )
    packet.add_argument("--work-item", required=True)
    packet.add_argument(
        "--show", action="store_true", help="print the full packet text"
    )

    task = sub.add_parser(
        "task", help="build the packet for a pre-registered task (e.g. T01)"
    )
    task.add_argument("task_id")
    task.add_argument(
        "--lrh-repo", type=pathlib.Path, default=None, help="LRH checkout path"
    )
    task.add_argument(
        "--lcats-repo", type=pathlib.Path, default=None, help="LCATS checkout path"
    )
    task.add_argument(
        "--tasks-file", type=pathlib.Path, default=tasks.DEFAULT_TASKS_FILE
    )
    task.add_argument("--show", action="store_true", help="print the full packet")

    b0 = sub.add_parser("b0", help="record an owner-written B0 baseline briefing")
    b0.add_argument("--packet", required=True, help="packet sha256 the owner read")
    b0.add_argument("--task-id", default=None)
    b0.add_argument("--briefing-file", type=pathlib.Path, required=True)
    b0.add_argument(
        "--minutes",
        type=float,
        required=True,
        help="active minutes spent reading the packet and writing the briefing",
    )

    run = sub.add_parser("run", help="brief an approved packet with one model call")
    run.add_argument("--packet", required=True, help="packet sha256")
    run.add_argument(
        "--approve", required=True, help="repeat the packet sha256 to approve it"
    )
    run.add_argument("--task-id", default=None)
    run.add_argument(
        "--prompt-version",
        default=settings.PROMPT_VERSION,
        help="prompt template in prompts/ (e.g. briefing_v2)",
    )
    run.add_argument("--backend", choices=("ollama", "fake"), default="ollama")
    run.add_argument("--base-url", default=settings.DEFAULT_OLLAMA_BASE_URL)
    run.add_argument("--model", default=settings.DEFAULT_MODEL)
    run.add_argument("--model-digest", default=settings.DEFAULT_MODEL_MANIFEST_DIGEST)
    run.add_argument(
        "--fake-response",
        type=pathlib.Path,
        default=None,
        help="file whose contents the fake backend returns",
    )
    run.add_argument("--num-ctx", type=int, default=None)
    run.add_argument("--max-output-tokens", type=int, default=None)
    run.add_argument("--timeout", type=float, default=None)

    inspect = sub.add_parser("inspect", help="summarize a run")
    inspect.add_argument("run_id")

    sub.add_parser("list", help="list stored run ids")

    evaluate = sub.add_parser("evaluate", help="record human scores for a run")
    evaluate.add_argument("run_id")
    evaluate.add_argument("--scores", type=pathlib.Path, required=True)

    exporter = sub.add_parser("export", help="write a sanitized export")
    exporter.add_argument("run_id")
    exporter.add_argument("--out", type=pathlib.Path, required=True)
    exporter.add_argument(
        "--include-output",
        action="store_true",
        help="include briefing text if the sensitivity scan is clean",
    )

    recover = sub.add_parser("recover", help="mark an interrupted run incomplete")
    recover.add_argument("run_id")
    return parser


def _add_backend_args(command: argparse.ArgumentParser) -> None:
    command.add_argument("--backend", choices=("ollama", "fake"), default="ollama")
    command.add_argument("--base-url", default=settings.DEFAULT_OLLAMA_BASE_URL)
    command.add_argument("--model", default=settings.DEFAULT_MODEL)
    command.add_argument(
        "--model-digest", default=settings.DEFAULT_MODEL_MANIFEST_DIGEST
    )
    command.add_argument(
        "--fake-response",
        type=pathlib.Path,
        default=None,
        help="file whose contents the fake backend returns",
    )
    command.add_argument("--num-ctx", type=int, default=None)
    command.add_argument("--max-output-tokens", type=int, default=None)
    command.add_argument("--timeout", type=float, default=None)


def _prompt_rating(store: recorder.Store, run_id: str) -> None:
    """Ask for a one-key rating; skipping is fine and recorded as unrated."""
    try:
        choice = input("rate [g]ood / [o]k / [b]ad / [enter] skip: ").strip().lower()
        if choice not in ask.RATINGS:
            return
        note = input("note (optional): ")
    except (EOFError, KeyboardInterrupt):
        print(file=sys.stderr)
        return
    ask.record_rating(store, run_id, choice, note)


def _run_ask(args: argparse.Namespace, store: recorder.Store) -> int:
    budgets = _budgets(args)
    try:
        ctx = ask.build_context(
            repo=args.repo,
            revision=args.commit,
            work_item=args.wi,
            files=args.files,
            project_dir=args.project_dir,
            budgets=budgets,
        )
    except (readiness.WorkItemReadinessError, sources.SourceError) as error:
        run_id = ask.record_failure(
            store, args.question, "missing_prerequisite", f"context: {error}"
        )
        print(f"error: {error} (run {run_id})", file=sys.stderr)
        return 2
    print(ask.source_summary(ctx), file=sys.stderr)
    interactive = sys.stdin.isatty()
    if interactive and not args.yes:
        try:
            answer = input("send to the local model? [Y/n] ").strip().lower()
            declined = answer not in ("", "y", "yes")
        except (EOFError, KeyboardInterrupt):
            declined = True
        if declined:
            run_id = ask.record_failure(
                store, args.question, "cancelled", "declined before sending"
            )
            print(f"\nnot sent (run {run_id})", file=sys.stderr)
            return 1
    try:
        adapter = _adapter(args)
    except (OSError, UnicodeDecodeError) as error:
        run_id = ask.record_failure(
            store, args.question, "missing_prerequisite", f"adapter: {error}"
        )
        print(f"error: {error} (run {run_id})", file=sys.stderr)
        return 2
    except model.BackendError as error:
        outcome = (
            "missing_prerequisite"
            if error.kind == model.KIND_MISSING_PREREQUISITE
            else "backend_error"
        )
        run_id = ask.record_failure(store, args.question, outcome, f"adapter: {error}")
        print(f"error: {error} (run {run_id})", file=sys.stderr)
        return 2

    def stream(chunk: str) -> None:
        sys.stdout.write(chunk)
        sys.stdout.flush()

    try:
        run_id = ask.run_ask(
            store=store,
            question=args.question,
            ctx=ctx,
            adapter=adapter,
            budgets=budgets,
            on_text=stream,
        )
    except KeyboardInterrupt:
        print("\ncancelled (recorded)", file=sys.stderr)
        return 130
    print()
    print(ask.footer(store, run_id), file=sys.stderr)
    if interactive and not args.no_rate:
        _prompt_rating(store, run_id)
    return 0 if store.load_run(run_id).get("outcome") == "completed" else 1


def _adapter(args: argparse.Namespace) -> model.ModelAdapter:
    if args.backend == "fake":
        text = "{}"
        if args.fake_response is not None:
            text = args.fake_response.read_text(encoding="utf-8")
        return model.FakeModel(
            [model.ModelResponse(text, "stop", None, None, {"fake": True})]
        )
    return model.OllamaModel(
        base_url=args.base_url, model=args.model, manifest_digest=args.model_digest
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _dispatch(args)
    except (recorder.StoreError, export.ExportError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _dispatch(args: argparse.Namespace) -> int:
    store = recorder.Store(args.store or recorder.default_store_root())

    if args.command == "ask":
        return _run_ask(args, store)

    if args.command == "rate":
        try:
            ask.record_rating(store, args.run_id, args.rating, args.note)
        except ValueError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        print(f"rated {args.run_id}")
        return 0

    if args.command == "log":
        print(ask.summarize(store, limit=args.limit), end="")
        return 0

    if args.command == "delete":
        store.delete_run(args.run_id)
        print(f"deleted {args.run_id}")
        return 0

    if args.command == "prune":
        try:
            removed = store.prune(args.before, dry_run=args.dry_run)
        except ValueError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        verb = "would remove" if args.dry_run else "removed"
        print(f"{verb} {len(removed)} run(s)")
        for run_id in removed:
            print(f"  {run_id}")
        return 0

    if args.command == "task":
        try:
            resolved = tasks.resolve_task(args.task_id, args.tasks_file)
        except tasks.TaskError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        repos = {"LRH": args.lrh_repo, "LCATS": args.lcats_repo}
        repo = repos.get(resolved.repo_label)
        if repo is None:
            flag = f"--{resolved.repo_label.lower()}-repo"
            print(f"error: task {resolved.task_id} needs {flag}", file=sys.stderr)
            return 2
        print(
            f"task {resolved.task_id} ({resolved.split}, {resolved.task_type}): "
            f"{resolved.work_item} @ {resolved.repo_label} {resolved.commit}"
        )
        args.repo = repo
        args.repo_label = resolved.repo_label
        args.commit = resolved.commit
        args.project_dir = resolved.project_dir
        args.work_item = resolved.work_item
        args.command = "packet"

    if args.command == "packet":
        try:
            built = context.build_packet(
                repo=args.repo,
                repo_label=args.repo_label,
                revision=args.commit,
                project_dir=args.project_dir,
                work_item_id=args.work_item,
                budgets=_budgets(args),
                lrh_commit=_lrh_commit(),
                lrh_code_dirty=_lrh_code_dirty(),
            )
        except (readiness.WorkItemReadinessError, sources.SourceError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        sha = built.sha256
        store.save_packet(sha, built.manifest, built.text)
        summary = {
            "packet_sha256": sha,
            "work_item_id": built.manifest["work_item_id"],
            "source_commit": built.manifest["source_commit"],
            "source_bytes": built.manifest["source_bytes"],
            "rendered_bytes": built.manifest["rendered_bytes"],
            "lrh_code_dirty": built.manifest["lrh_code_dirty"],
            "sources": [
                f"{s['source_id']} {s['path']} L{s['line_start']}-{s['line_end']}"
                f"{' TRUNCATED' if s['truncated'] else ''}"
                for s in built.manifest["sources"]  # type: ignore[union-attr]
            ],
            "omitted_sources": built.manifest["omitted_sources"],
            "diagnostics": built.manifest["diagnostics"],
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        if args.show:
            print(built.text)
        print(f"\nReview the packet, then approve with: --approve {sha}")
        return 0

    if args.command == "b0":
        try:
            run_id = runner.record_manual_briefing(
                store=store,
                packet_sha256=args.packet,
                briefing_text=args.briefing_file.read_text(encoding="utf-8"),
                author_minutes=args.minutes,
                task_id=args.task_id,
            )
        except (runner.ApprovalError, ValueError, OSError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        print(export.inspect_run(store, run_id), end="")
        return 0

    if args.command == "run":
        if args.prompt_version not in briefing.available_prompt_versions():
            print(
                f"error: unknown prompt version {args.prompt_version!r}; available: "
                f"{', '.join(briefing.available_prompt_versions())}",
                file=sys.stderr,
            )
            return 2
        try:
            adapter = _adapter(args)
            run_id = runner.run_briefing(
                store=store,
                packet_sha256=args.packet,
                approved_sha256=args.approve,
                adapter=adapter,
                budgets=_budgets(args),
                task_id=args.task_id,
                prompt_version=args.prompt_version,
            )
        except (runner.ApprovalError, model.BackendError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        print(export.inspect_run(store, run_id))
        outcome = store.load_run(run_id).get("outcome")
        return 0 if outcome == runner.OUTCOME_COMPLETED else 1

    if args.command == "inspect":
        print(export.inspect_run(store, args.run_id), end="")
        return 0

    if args.command == "list":
        for run_id in store.list_runs():
            print(run_id)
        return 0

    if args.command == "evaluate":
        try:
            scores = json.loads(args.scores.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            print(f"error: cannot read scores file: {error}", file=sys.stderr)
            return 2
        if not isinstance(scores, dict):
            print("error: scores file must contain a JSON object", file=sys.stderr)
            return 2
        export.record_evaluation(store, args.run_id, scores)
        print(f"recorded evaluation for {args.run_id}")
        return 0

    if args.command == "export":
        path = export.export_run(
            store, args.run_id, args.out, include_output=args.include_output
        )
        print(f"wrote {path}")
        return 0

    if args.command == "recover":
        manifest = store.recover_run(args.run_id)
        print(f"{args.run_id}: outcome={manifest.get('outcome')}")
        return 0

    return 2
