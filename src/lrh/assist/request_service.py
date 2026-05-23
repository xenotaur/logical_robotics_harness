"""Request generation orchestration for the compatibility request script."""

import argparse
import datetime
import pathlib
import re

from lrh.assist import request_templates, request_variables, work_item_prompt_core
from lrh.control import parser as control_parser
from lrh.integrations.github import formatters, pr_ref, pull_reviews

_TEMPLATE_VAR_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
_WORK_ITEM_ID_PATTERN = re.compile(r"^WI-[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*$")
_WORK_ITEM_H1_ID_PATTERN = re.compile(
    r"^#\s*(WI-[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*)(?:\s|:|$)"
)


def _request_display_name(args: argparse.Namespace) -> str:
    """Return the user-facing request name to use in diagnostics."""
    request_name = getattr(args, "request_name", None)
    if isinstance(request_name, str) and request_name.strip():
        return request_name.strip()
    return args.template_name


def validate_args(args: argparse.Namespace) -> str | None:
    """Validate request arguments and return an error message if invalid."""
    target_input = resolve_target_input(args)
    display_name = _request_display_name(args)

    if args.template_name == "improve_coverage" and not target_input:
        return f"error: {display_name} requires a target module path."

    if args.template_name == "bootstrap_project":
        if not args.repo_name and not target_input:
            return (
                f"error: {display_name} requires --repo-name or a target value "
                "that can be used as the repository identifier."
            )

    if args.template_name == "assessment":
        if not args.scope:
            return (
                f"error: {display_name} requires --scope "
                "(project, current_focus, or work_item)."
            )
        if args.scope == "work_item" and not target_input:
            return (
                f"error: {display_name} --scope work_item requires --target "
                "(for example --target WI-0003)."
            )

    if args.template_name == "work_items_from_audit":
        if not args.audit_file:
            return f"error: {display_name} requires --audit-file."
        if not args.style_file:
            return f"error: {display_name} requires --style-file."

    if args.template_name == "codex_prompt_from_work_item":
        if not args.work_item_file and not target_input:
            return (
                f"error: {display_name} requires a target "
                "work item ID/path or --work-item-file."
            )

    if args.template_name == "review_response":
        if not target_input:
            return f"error: {display_name} requires a target PR URL."

    if args.template_name == "pr_against_work_item":
        if not args.work_item_file:
            return f"error: {display_name} requires --work-item-file."
        if not args.patch_file:
            return f"error: {display_name} requires --patch-file."
        if not args.style_file:
            return f"error: {display_name} requires --style-file."

    return None


def generate_request(
    args: argparse.Namespace,
    *,
    template_root: pathlib.Path | None = None,
    project_root: pathlib.Path | None = None,
    template_dirs: list[pathlib.Path | str] | None = None,
) -> tuple[str, dict[str, str]]:
    """Load template and render it using computed request variables."""
    variables = build_variables(args)
    resolved_project_root = project_root or request_variables.find_repo_root()
    resolved_template_dirs = _resolve_template_dirs(args, template_dirs)
    if args.template_name == "codex_prompt_from_work_item":
        template_resolution = request_templates.resolve_template(
            args.template_name,
            template_root=template_root,
            project_root=resolved_project_root,
            template_dirs=resolved_template_dirs,
        )
        if template_resolution.source != "package":
            template_text = request_templates.load_template_text(
                args.template_name,
                template_root=template_root,
                project_root=resolved_project_root,
                template_dirs=resolved_template_dirs,
            )
            return render_template(template_text, variables), variables

        work_item_path = pathlib.Path(variables["WORK_ITEM_RESOLVED_FILE"])
        prompt_id = _resolve_codex_prompt_id(
            args=args,
            work_item_file=work_item_path,
        )
        rendered = work_item_prompt_core.generate_codex_cloud_prompt(
            prompt_id=prompt_id,
            work_item_path=work_item_path,
            style_guide_path=variables["STYLE_GUIDE_PATH"],
            work_item_reference_path=variables["WORK_ITEM_PATH"],
        )
        return rendered, variables

    if args.template_name == "review_response":
        target_input = resolve_target_input(args)
        ref = pr_ref.parse_pull_request_url(target_input)
        threads_data = pull_reviews.get_pull_review_threads(ref)
        variables["REVIEW_URL"] = target_input
        variables["REPO_NAME"] = f"{ref.owner}/{ref.repo}"
        has_unresolved_threads = formatters.has_threads_for_state(
            threads_data, state="unresolved"
        )
        if not has_unresolved_threads and not getattr(args, "force", False):
            return (
                "Nothing to resolve: no unresolved review threads found for "
                f"{ref.owner}/{ref.repo}#{ref.number}",
                variables,
            )
        variables["UNRESOLVED_THREADS"] = formatters.format_threads_review(
            threads_data,
            state="unresolved",
            show_pr=True,
            include_author=True,
            include_url=True,
            ref=ref,
        )

    template_text = request_templates.load_template_text(
        args.template_name,
        template_root=template_root,
        project_root=resolved_project_root,
        template_dirs=resolved_template_dirs,
    )
    return render_template(template_text, variables), variables


def _resolve_template_dirs(
    args: argparse.Namespace,
    template_dirs: list[pathlib.Path | str] | None,
) -> list[pathlib.Path | str]:
    """Return explicit request template directories in CLI/API precedence order."""
    resolved_dirs = list(template_dirs or [])
    template_dir = getattr(args, "template_dir", None)
    if template_dir:
        resolved_dirs.insert(0, template_dir)
    return resolved_dirs


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
    work_item_resolved_file = (
        str(pathlib.Path(work_item_file).resolve()) if work_item_file else ""
    )
    style_file_path = request_variables.normalize_file_reference(style_file)
    patch_file_path = request_variables.normalize_file_reference(args.patch_file)
    repo_root = pathlib.Path(getattr(args, "repo_root", None) or ".")
    project_root_value = getattr(args, "project_root", None)
    project_root = pathlib.Path(project_root_value) if project_root_value else repo_root
    docs_root_value = getattr(args, "docs_root", None)
    docs_root = (
        pathlib.Path(docs_root_value) if docs_root_value else project_root / "docs"
    )
    control_root = (
        pathlib.Path(getattr(args, "control_root", None))
        if getattr(args, "control_root", None)
        else project_root / "project"
    )
    package_roots = tuple(
        pathlib.Path(value) for value in (getattr(args, "package_root", None) or [])
    )
    audit_output = (
        pathlib.Path(getattr(args, "audit_output", None))
        if getattr(args, "audit_output", None)
        else control_root / "audits" / "YYYY-MM-DD-docs-audit.md"
    )
    package_roots_value = (
        "\n".join(f"  - `{path.as_posix()}`" for path in package_roots)
        or "  - `(describe package roots manually if multiple apply)`"
    )

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
        "WORK_ITEM_RESOLVED_FILE": work_item_resolved_file,
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
        "REQUEST_REPO_ROOT": repo_root.as_posix(),
        "REQUEST_PROJECT_ROOT": project_root.as_posix(),
        "REQUEST_DOCS_ROOT": docs_root.as_posix(),
        "REQUEST_CONTROL_ROOT": control_root.as_posix(),
        "REQUEST_PACKAGE_ROOTS": package_roots_value,
        "REQUEST_TARGET_AGENT": getattr(args, "target_agent", None) or "Codex Cloud",
        "REQUEST_AUDIT_OUTPUT": audit_output.as_posix(),
        "REQUEST_ORGANIZE_DOCS_PHASE": getattr(args, "phase", None) or "",
    }


def resolve_work_item_file_for_request(
    *,
    target_input: str,
    explicit_work_item_file: str | None = None,
    command_name: str = "codex_prompt_from_work_item",
    explicit_path_flag: str = "--work-item-file",
) -> tuple[str, str]:
    """Resolve a work-item target by explicit path, repository-relative path, or ID."""
    args = argparse.Namespace(
        template_name="codex_prompt_from_work_item",
        work_item_file=explicit_work_item_file,
        work_item_command_name=command_name,
        work_item_flag_name=explicit_path_flag,
    )
    resolved, resolution = _resolve_codex_work_item_file(
        args=args,
        target_input=target_input,
    )
    if resolved is None:
        raise FileNotFoundError(f"error: No work item matched target '{target_input}'.")
    return resolved, resolution


def _resolve_codex_style_file(args: argparse.Namespace) -> str | None:
    """Resolve style-file behavior for codex_prompt_from_work_item templates."""
    if args.template_name != "codex_prompt_from_work_item":
        return args.style_file

    if args.style_file:
        style_path = pathlib.Path(args.style_file)
        if not style_path.is_file():
            raise FileNotFoundError(
                f"error: --style-file does not exist: {args.style_file}"
            )
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

    command_name = getattr(
        args, "work_item_command_name", "codex_prompt_from_work_item"
    )
    flag_name = getattr(args, "work_item_flag_name", "--work-item-file")

    work_item_root = _resolve_work_item_root()
    candidates = _find_work_item_candidates(
        target_input=target_input,
        work_item_root=work_item_root,
    )
    if not candidates:
        searched = "\n".join(
            [
                f"- {work_item_root / '*.md'}",
                f"- {work_item_root / '**/*.md'}",
            ]
        )
        raise FileNotFoundError(
            "error: No work item matched target "
            f"'{target_input}'. Searched:\n{searched}\n"
            f"Try: lrh request {command_name} WI-EXAMPLE\n"
            f"Or:  lrh request {command_name} {flag_name} "
            "project/work_items/proposed/WI-EXAMPLE.md"
        )

    by_path: dict[pathlib.Path, str] = {}
    for path, resolution in candidates:
        by_path.setdefault(path, resolution)
    if len(by_path) > 1:
        candidate_paths = "\n".join(f"- {path}" for path in sorted(by_path.keys()))
        ambiguity_guidance = f"Pass {flag_name} with a work-item path explicitly."
        if flag_name == "--work-item-file":
            ambiguity_guidance = "Pass --work-item-file explicitly."
        raise FileNotFoundError(
            "error: Ambiguous work item target "
            f"'{target_input}'. Matches:\n{candidate_paths}\n"
            f"{ambiguity_guidance}"
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
    *, target_input: str, work_item_root: pathlib.Path
) -> list[tuple[pathlib.Path, str]]:
    """Collect candidate work-item files by id, stem, and filename matching."""
    matches: list[tuple[pathlib.Path, str]] = []
    lookup = target_input.strip()
    lookup_stem = pathlib.Path(lookup).stem
    lookup_names = {lookup}
    if not lookup.lower().endswith(".md"):
        lookup_names.add(f"{lookup}.md")

    if not work_item_root.is_dir():
        return []

    paths = set(work_item_root.glob("*.md"))
    paths.update(work_item_root.glob("**/*.md"))
    for path in sorted(path for path in paths if path.is_file()):
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
    except (FileNotFoundError, OSError, UnicodeDecodeError, ValueError):
        pass

    heading_id = _read_h1_work_item_id(path)
    if heading_id and heading_id == lookup:
        return "h1_id"

    if path.stem == lookup_stem:
        return "filename_stem"

    if path.name in lookup_names:
        return "filename"

    return ""


def _read_h1_work_item_id(path: pathlib.Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return ""
    content_lines = lines
    if content_lines and content_lines[0].strip() == "---":
        for index in range(1, len(content_lines)):
            if content_lines[index].strip() == "---":
                content_lines = content_lines[index + 1 :]
                break
    for line in content_lines:
        stripped = line.strip()
        if not stripped:
            continue
        match = _WORK_ITEM_H1_ID_PATTERN.match(stripped)
        if match is not None:
            candidate = match.group(1)
            return candidate if _WORK_ITEM_ID_PATTERN.fullmatch(candidate) else ""
    return ""


def _looks_like_path_target(target_input: str) -> bool:
    """Return True when a target string should be treated as a file path."""
    normalized = target_input.strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    return "/" in normalized or "\\" in normalized or lowered.endswith(".md")


def _resolve_codex_prompt_id(
    *, args: argparse.Namespace, work_item_file: pathlib.Path
) -> str:
    explicit_prompt_id = getattr(args, "prompt_id", None)
    if isinstance(explicit_prompt_id, str) and explicit_prompt_id.strip():
        return explicit_prompt_id.strip()

    parsed = control_parser.parse_markdown_file(work_item_file)
    work_item_id = parsed.frontmatter.get("id")
    if not isinstance(work_item_id, str) or not work_item_id.strip():
        work_item_id = "AD_HOC"

    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    timestamp = now.isoformat(timespec="seconds")
    return f"PROMPT({work_item_id}:CODEX_PROMPT_FROM_WORK_ITEM)[{timestamp}]"
