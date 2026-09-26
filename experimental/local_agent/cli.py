"""Command line for the stage-0 briefing prototype.

Typical flow::

    packet   -> build and store a pinned context packet; prints its sha256
    run      -> brief it once, only if --approve matches that sha256
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

from local_agent import context, export, model, recorder, runner, settings, sources
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

    run = sub.add_parser("run", help="brief an approved packet with one model call")
    run.add_argument("--packet", required=True, help="packet sha256")
    run.add_argument(
        "--approve", required=True, help="repeat the packet sha256 to approve it"
    )
    run.add_argument("--task-id", default=None)
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

    if args.command == "run":
        try:
            adapter = _adapter(args)
            run_id = runner.run_briefing(
                store=store,
                packet_sha256=args.packet,
                approved_sha256=args.approve,
                adapter=adapter,
                budgets=_budgets(args),
                task_id=args.task_id,
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
        scores = json.loads(args.scores.read_text(encoding="utf-8"))
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
