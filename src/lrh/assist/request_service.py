"""Request generation orchestration for the compatibility request script."""

import argparse
import pathlib
import re

from lrh.assist import request_templates, request_variables
from lrh.control import parser as control_parser

_TEMPLATE_VAR_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def validate_args(args: argparse.Namespace) -> str | None:
    """Validate request arguments and return an error message if invalid."""
    target_input = resolve_target_input(args)

    if args.template_name == "improve_coverage" and not target_input:
        return "error: improve_coverage requires a target module path."

    if args.template_name == "bootstrap_project":
        if not args.repo_name and not target_input:
            return (
                "error: bootstrap_project requires --repo-name or a target value "
                "that can be used as the repository identifier."
            )

    if args.template_name == "assessment":
        if not args.scope:
            return (
                "error: assessment requires --scope "
                "(project, current_focus, or work_item)."
            )
        if args.scope == "work_item" and not target_input:
            return (
                "error: assessment --scope work_item requires --target "
                "(for example --target WI-0003)."
            )

    if args.template_name == "work_items_from_audit":
        if not args.audit_file:
            return "error: work_items_from_audit requires --audit-file."
        if not args.style_file:
            return "error: work_items_from_audit requires --style-file."

    if args.template_name == "codex_prompt_from_work_item":
        if not args.work_item_file and not target_input:
            return (
                "error: codex_prompt_from_work_item requires a target "
                "work item ID/path or --work-item-file."
            )

    if args.template_name == "pr_against_work_item":
        if not args.work_item_file:
            return "error: pr_against_work_item requires --work-item-file."
        if not args.patch_file:
            return "error: pr_against_work_item requires --patch-file."
        if not args.style_file:
            return "error: pr_against_work_item requires --style-file."

    return None


def generate_request(
    args: argparse.Namespace,
    *,
    template_root: pathlib.Path | None = None,
) -> tuple[str, dict[str, str]]:
    """Load template and render it using computed request variables."""
    template_text = request_templates.load_template_text(
        args.template_name,
        template_root=template_root,
    )
    variables = build_variables(args)
    return render_template(template_text, variables), variables


def render_template(template_text: str, variables: dict[str, str]) -> str:
    """Interpolate ``{{VARNAME}}`` tokens, preserving unknown placeholders."""

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return _TEMPLATE_VAR_RE.sub(repl, template_text)


def resolve_target_input(args: argparse.Namespace) -> str:
    """Resolve optional target value from positional/named CLI arguments."""
    if args.target_option:
        return args.target_option
    if args.target:
        return args.target
    return ""


def build_variables(args: argparse.Namespace) -> dict[str, str]:
    """Build template interpolation variables from parsed request arguments."""
    target_input = resolve_target_input(args)
    work_item_file, work_item_resolution = _resolve_codex_work_item_file(
        args=args,
        target_input=target_input,
    )
    style_file = _resolve_codex_style_file(args)
    target_module_gha = request_variables.normalize_target_for_gha(target_input)
    module_name = pathlib.Path(target_module_gha).stem if target_module_gha else ""
    suggested_test_path = request_variables.compute_suggested_test_path(
        target_module_gha
    )

    background_context = args.background_text or request_variables.read_optional_text(
        args.background_file
    )
    repo_name = request_variables.infer_repo_name(target_input, args.repo_name)

    audit_report = request_variables.read_optional_text(args.audit_file)
    work_item = request_variables.read_optional_text(work_item_file)
    style_guide_context = request_variables.read_optional_text(style_file)
    patch_text = request_variables.read_optional_text(args.patch_file)
    background_file_path = request_variables.normalize_file_reference(
        args.background_file
    )
    audit_file_path = request_variables.normalize_file_reference(args.audit_file)
    work_item_file_path = request_variables.normalize_file_reference(work_item_file)
    style_file_path = request_variables.normalize_file_reference(style_file)
    patch_file_path = request_variables.normalize_file_reference(args.patch_file)

    return {
        "TEMPLATE_NAME": args.template_name,
        "TARGET_INPUT": target_input,
        "TARGET_MODULE_GHA": target_module_gha,
        "MODULE_NAME": module_name,
        "SUGGESTED_TEST_PATH": suggested_test_path,
        "REPO_NAME": repo_name,
        "PROJECT_GOAL": args.project_goal or "",
        "BACKGROUND_CONTEXT": background_context,
        "BACKGROUND_FILE": background_file_path,
        "BACKGROUND_PATH": background_file_path,
        "BACKGROUND_CONTENT": background_context,
        "PROJECT_TYPE": args.project_type or "",
        "BOOTSTRAP_SCOPE": args.bootstrap_mode or "",
        "ASSESSMENT_SCOPE": args.scope or "",
        "ASSESSMENT_TARGET": target_input,
        "AUDIT_REPORT": audit_report,
        "AUDIT_FILE": audit_file_path,
        "AUDIT_PATH": audit_file_path,
        "AUDIT_CONTENT": audit_report,
        "WORK_ITEM": work_item,
        "WORK_ITEM_FILE": work_item_file_path,
        "WORK_ITEM_PATH": work_item_file_path,
        "WORK_ITEM_CONTENT": work_item,
        "WORK_ITEM_RESOLUTION": work_item_resolution,
        "STYLE_GUIDE_CONTEXT": style_guide_context,
        "STYLE_FILE": style_file_path,
        "STYLE_GUIDE_PATH": style_file_path,
        "STYLE_GUIDE_CONTENT": style_guide_context,
        "PATCH": patch_text,
        "PATCH_FILE": patch_file_path,
        "PATCH_PATH": patch_file_path,
        "PATCH_CONTENT": patch_text,
    }


def _resolve_codex_style_file(args: argparse.Namespace) -> str | None:
    """Resolve style-file behavior for codex_prompt_from_work_item templates."""
    if args.template_name != "codex_prompt_from_work_item":
        return args.style_file

    if args.style_file:
        style_path = pathlib.Path(args.style_file)
        if not style_path.is_file():
            raise FileNotFoundError(f"Style guide file not found: {args.style_file}")
        return args.style_file

    repo_root = request_variables.find_repo_root()
    candidates = [pathlib.Path.cwd() / "STYLE.md"]
    if repo_root is not None:
        candidates.append(repo_root / "STYLE.md")

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)

    raise FileNotFoundError(
        "error: codex_prompt_from_work_item could not find STYLE.md from the current "
        "working tree. Pass --style-file explicitly."
    )


def _resolve_codex_work_item_file(
    *, args: argparse.Namespace, target_input: str
) -> tuple[str | None, str]:
    """Resolve codex_prompt_from_work_item work item path and resolution method."""
    if args.template_name != "codex_prompt_from_work_item":
        return args.work_item_file, ""

    if args.work_item_file:
        explicit_path = pathlib.Path(args.work_item_file)
        if not explicit_path.is_file():
            raise FileNotFoundError(
                f"error: --work-item-file does not exist: {args.work_item_file}"
            )
        return args.work_item_file, "explicit_flag"

    target_path = pathlib.Path(target_input)
    if target_path.is_file():
        return target_input, "target_path"

    repo_root = request_variables.find_repo_root()
    if not target_path.is_absolute() and repo_root is not None:
        repo_relative_path = (repo_root / target_path).resolve()
        if repo_relative_path.is_file():
            return str(repo_relative_path), "repo_root_relative_path"

    if _looks_like_path_target(target_input):
        raise FileNotFoundError(
            "error: target looks like a work-item path but does not exist: "
            f"{target_input}"
        )

    work_item_root = _resolve_work_item_root()
    work_item_dirs = [
        work_item_root / "proposed",
        work_item_root / "active",
        work_item_root / "resolved",
        work_item_root / "abandoned",
    ]
    candidates = _find_work_item_candidates(
        target_input=target_input,
        work_item_dirs=work_item_dirs,
    )
    if not candidates:
        searched = "\n".join(f"- {directory}" for directory in work_item_dirs)
        raise FileNotFoundError(
            "error: No work item matched target "
            f"'{target_input}'. Searched:\n{searched}\n"
            "Try: lrh request codex_prompt_from_work_item WI-EXAMPLE\n"
            "Or:  lrh request codex_prompt_from_work_item --work-item-file "
            "project/work_items/proposed/WI-EXAMPLE.md"
        )

    by_path: dict[pathlib.Path, str] = {}
    for path, resolution in candidates:
        by_path.setdefault(path, resolution)
    if len(by_path) > 1:
        candidate_paths = "\n".join(f"- {path}" for path in sorted(by_path.keys()))
        raise FileNotFoundError(
            "error: Ambiguous work item target "
            f"'{target_input}'. Matches:\n{candidate_paths}\n"
            "Pass --work-item-file explicitly."
        )

    only_path = next(iter(by_path.keys()))
    return str(only_path), by_path[only_path]


def _resolve_work_item_root() -> pathlib.Path:
    """Resolve project work item root using repository root when available."""
    repo_root = request_variables.find_repo_root()
    if repo_root is not None:
        return repo_root / "project" / "work_items"
    return pathlib.Path.cwd() / "project" / "work_items"


def _find_work_item_candidates(
    *, target_input: str, work_item_dirs: list[pathlib.Path]
) -> list[tuple[pathlib.Path, str]]:
    """Collect candidate work-item files by id, stem, and filename matching."""
    matches: list[tuple[pathlib.Path, str]] = []
    lookup = target_input.strip()
    lookup_stem = pathlib.Path(lookup).stem
    lookup_names = {lookup}
    if not lookup.lower().endswith(".md"):
        lookup_names.add(f"{lookup}.md")

    for directory in work_item_dirs:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            resolution = _match_work_item_target(
                path=path,
                lookup=lookup,
                lookup_stem=lookup_stem,
                lookup_names=lookup_names,
            )
            if resolution:
                matches.append((path, resolution))
    return matches


def _match_work_item_target(
    *,
    path: pathlib.Path,
    lookup: str,
    lookup_stem: str,
    lookup_names: set[str],
) -> str:
    """Return matching resolution method, or empty string when unmatched."""
    try:
        parsed = control_parser.parse_markdown_file(path)
        work_item_id = parsed.frontmatter.get("id")
        if isinstance(work_item_id, str) and work_item_id == lookup:
            return "frontmatter_id"
    except (FileNotFoundError, OSError, ValueError):
        pass

    if path.stem == lookup_stem:
        return "filename_stem"

    if path.name in lookup_names:
        return "filename"

    return ""


def _looks_like_path_target(target_input: str) -> bool:
    """Return True when a target string should be treated as a file path."""
    normalized = target_input.strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    return "/" in normalized or "\\" in normalized or lowered.endswith(".md")
