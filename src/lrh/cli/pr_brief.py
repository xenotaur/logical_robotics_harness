"""CLI handler for `lrh pr-brief` (gather and render PR briefings)."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from lrh.pr_brief import gather, render


def _gather(args: argparse.Namespace) -> int:
    out_dir = pathlib.Path(args.out)
    data_path = out_dir / "data.json"
    diff_path = out_dir / "pr.diff"
    if data_path.exists() and not args.force:
        print(
            f"{data_path} already exists and may hold authored briefing content; "
            "pass --force to overwrite it",
            file=sys.stderr,
        )
        return 1
    repo_dir = pathlib.Path(args.repo_dir) if args.repo_dir else None
    if repo_dir is not None and not repo_dir.is_dir():
        print(f"--repo-dir is not a directory: {repo_dir}", file=sys.stderr)
        return 2
    try:
        ref = gather.resolve_ref(args.target, args.number)
        data, diff_text = gather.gather_briefing_data(ref, repo_dir=repo_dir)
    except (RuntimeError, ValueError) as error:
        print(f"lrh pr-brief gather: {error}", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    diff_path.write_text(diff_text, encoding="utf-8")
    status = data["status"]
    conflicts = status["conflicts"]
    if conflicts.get("checked"):
        conflict_text = (
            "clean"
            if conflicts.get("clean")
            else f"{len(conflicts.get('files') or [])} conflicting file(s)"
        )
    else:
        conflict_text = "not checked" + (
            f" ({conflicts['error']})" if conflicts.get("error") else ""
        )
    pr = data["pr"]
    print(f"data: {data_path}")
    print(f"diff: {diff_path} ({len(diff_text.splitlines())} lines)")
    print(
        f"pr: {pr['repo']}#{pr['number']} {pr['state']} "
        f"+{pr['additions']} -{pr['deletions']} in {len(data['files'])} files"
    )
    print(f"behind base by: {status.get('behind_by')}; trial merge: {conflict_text}")
    return 0


def _render(args: argparse.Namespace) -> int:
    data_path = pathlib.Path(args.data)
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"lrh pr-brief render: cannot read {data_path}: {error}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("lrh pr-brief render: data must be a JSON object", file=sys.stderr)
        return 2
    errors, warnings = render.validate(data)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    if args.check:
        print(f"ok: {len(warnings)} warning(s)")
        return 0
    try:
        page = render.render(data, output_format=args.format)
    except render.BriefingError as error:
        print(f"lrh pr-brief render: {error}", file=sys.stderr)
        return 1
    out_path = (
        pathlib.Path(args.out) if args.out else data_path.with_name("briefing.html")
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")
    print(f"wrote {out_path} ({len(page):,} bytes, {len(warnings)} warning(s))")
    return 0


def run_pr_brief_cli(argv: list[str], prog: str) -> int:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Gather facts for, and render, a visual pull request briefing.",
    )
    subparsers = parser.add_subparsers(dest="pr_brief_command", required=True)

    gather_parser = subparsers.add_parser(
        "gather",
        help="Write data.json and pr.diff for a pull request.",
    )
    gather_parser.add_argument(
        "target", help="PR URL, OWNER/REPO (with NUMBER), or a bare PR number"
    )
    gather_parser.add_argument("number", nargs="?", type=int)
    gather_parser.add_argument(
        "--out", required=True, help="Directory for data.json and pr.diff."
    )
    gather_parser.add_argument(
        "--repo-dir",
        help=(
            "A local clone of the repository; enables a trial merge that lists "
            "conflicting files (fetches objects only, changes no refs or files)."
        ),
    )
    gather_parser.add_argument(
        "--force", action="store_true", help="Overwrite an existing data.json."
    )

    render_parser = subparsers.add_parser(
        "render",
        help="Render data.json into an HTML briefing page.",
    )
    render_parser.add_argument("data", help="Path to data.json.")
    render_parser.add_argument(
        "--out", help="Output HTML path (default: briefing.html beside data.json)."
    )
    render_parser.add_argument(
        "--format",
        choices=render.FORMATS,
        default="artifact",
        help=(
            "artifact: page body for an Artifact publish (no doctype wrapper); "
            "standalone: a complete HTML document to open directly."
        ),
    )
    render_parser.add_argument(
        "--check",
        action="store_true",
        help="Validate data.json and report warnings without writing HTML.",
    )

    args = parser.parse_args(argv)
    if args.pr_brief_command == "gather":
        return _gather(args)
    return _render(args)
