"""Installed prompt workflow helpers for LRH CLI."""

from __future__ import annotations

import argparse
import datetime
import pathlib
import re

VALID_STATUSES = {
    "planned",
    "in_progress",
    "landed",
    "failed",
    "reverted",
    "superseded",
}
WORK_ITEM_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def normalize_slug(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        raise ValueError("slug must contain at least one alphanumeric character")
    return slug


def slug_upper_underscore(slug: str) -> str:
    return slug.replace("-", "_").upper()


def normalize_work_item(value: str) -> str:
    work_item = (value or "").strip() or "AD_HOC"
    if not WORK_ITEM_PATTERN.fullmatch(work_item):
        raise ValueError(
            "work-item must match ^[A-Za-z0-9][A-Za-z0-9_-]*$ "
            "(for example: WI-META-CLI-MVP or AD_HOC)"
        )
    return work_item


def resolve_output_root(project_root: str, output_root: str) -> pathlib.Path:
    return pathlib.Path(project_root) / output_root


def build_prompt_label(now: datetime.datetime, work_item: str, slug: str) -> str:
    return (
        f"PROMPT({work_item}:{slug_upper_underscore(slug)})"
        f"[{now.isoformat(timespec='seconds')}]"
    )


def suggested_execution_path(
    now: datetime.datetime,
    output_root: pathlib.Path,
    work_item: str,
    slug: str,
) -> pathlib.Path:
    timestamp_for_file = now.strftime("%Y_%m_%d_%H_%M_%S")
    return (
        output_root
        / work_item
        / f"{timestamp_for_file}_{slug_upper_underscore(slug)}.md"
    )


def render_execution_content(
    execution_id: str,
    prompt_id: str,
    work_item: str,
    status: str,
    rerun_of: str,
    pr: str,
    commit: str,
    created_at: str,
) -> str:
    return (
        "---\n"
        f"execution_id: {execution_id}\n"
        f"prompt_id: {prompt_id}\n"
        f"work_item: {work_item}\n"
        f"status: {status}\n"
        f"rerun_of: {rerun_of}\n"
        f"pr: {pr}\n"
        f"commit: {commit}\n"
        f"created_at: {created_at}\n"
        "---\n\n"
        "# Summary\n\n"
        "TODO: Briefly summarize the intended prompt-driven work.\n\n"
        "# Result\n\n"
        "TODO: Fill in what happened.\n\n"
        "# Validation\n\n"
        "TODO: List tests or checks run.\n\n"
        "# Follow-up\n\n"
        "TODO: List deferred work.\n"
    )


def run_prompt_cli(argv: list[str], *, prog: str = "lrh prompt") -> int:
    parser = argparse.ArgumentParser(prog=prog, description="Prompt workflow helpers.")
    subparsers = parser.add_subparsers(dest="prompt_command")

    label_parser = subparsers.add_parser(
        "label",
        help="Generate a prompt ID and suggested execution record path.",
    )
    label_parser.add_argument("--work-item", default="AD_HOC")
    label_parser.add_argument("--slug", required=True)
    label_parser.add_argument("--project-root", default=".")
    label_parser.add_argument("--output-root", default="project/executions")

    record_parser = subparsers.add_parser(
        "record-execution",
        help="Create execution-record markdown files.",
    )
    record_parser.add_argument("--prompt-id", required=True)
    record_parser.add_argument("--work-item", default="AD_HOC")
    record_parser.add_argument("--slug", required=True)
    record_parser.add_argument(
        "--status",
        default="planned",
        choices=sorted(VALID_STATUSES),
    )
    record_parser.add_argument("--rerun-of", default="")
    record_parser.add_argument("--pr", default="")
    record_parser.add_argument("--commit", default="")
    record_parser.add_argument("--project-root", default=".")
    record_parser.add_argument("--output-root", default="project/executions")
    record_parser.add_argument("--dry-run", action="store_true")
    record_parser.add_argument("--force", action="store_true")

    args = parser.parse_args(argv)
    if args.prompt_command is None:
        parser.error("prompt requires a subcommand (try: lrh prompt label)")

    try:
        slug = normalize_slug(args.slug)
        work_item = normalize_work_item(args.work_item)
    except ValueError as error:
        parser.error(str(error))

    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    output_root = resolve_output_root(args.project_root, args.output_root)

    if args.prompt_command == "label":
        prompt_id = build_prompt_label(now, work_item, slug)
        suggested_file = suggested_execution_path(now, output_root, work_item, slug)
        print(f"prompt_id: {prompt_id}")
        print(f"execution_dir: {(output_root / work_item).as_posix()}")
        print(f"suggested_execution_file: {suggested_file.as_posix()}")
        return 0

    timestamp_for_id = now.strftime("%Y_%m_%d_%H_%M_%S")
    execution_id = f"{timestamp_for_id}_{slug_upper_underscore(slug)}"
    output_root_resolved = output_root.resolve()
    execution_dir = (output_root_resolved / work_item).resolve()
    if (
        execution_dir != output_root_resolved
        and output_root_resolved not in execution_dir.parents
    ):
        parser.error(
            f"resolved execution directory escapes output-root: {execution_dir}"
        )
    output_file = execution_dir / f"{execution_id}.md"

    content = render_execution_content(
        execution_id=execution_id,
        prompt_id=args.prompt_id,
        work_item=work_item,
        status=args.status,
        rerun_of=args.rerun_of,
        pr=args.pr,
        commit=args.commit,
        created_at=now.isoformat(timespec="seconds"),
    )

    if args.dry_run:
        print(f"output_file: {output_file.as_posix()}")
        print(content, end="")
        return 0

    execution_dir.mkdir(parents=True, exist_ok=True)
    if output_file.exists() and not args.force:
        parser.error(f"output file already exists: {output_file}")

    output_file.write_text(content, encoding="utf-8")
    print(f"wrote: {output_file.as_posix()}")
    return 0
