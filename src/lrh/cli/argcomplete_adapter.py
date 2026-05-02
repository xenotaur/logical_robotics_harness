"""Optional argcomplete wiring for the LRH argparse CLI."""

from __future__ import annotations

import argparse

from lrh.assist import request_variables
from lrh.cli import completion_sources


def enable_completion(parser: argparse.ArgumentParser) -> None:
    """Enable argcomplete for a parser when the optional dependency is present."""
    try:
        import argcomplete  # type: ignore[import-not-found]
    except ImportError:
        return

    argcomplete.autocomplete(parser)


def request_template_completer(
    prefix: str,
    parsed_args: argparse.Namespace,
    **_: object,
) -> list[str]:
    """Complete request template names from package-owned template resources."""
    del parsed_args
    return completion_sources.request_template_names(prefix=prefix)


def codex_work_item_target_completer(
    prefix: str,
    parsed_args: argparse.Namespace,
    **_: object,
) -> list[str] | None:
    """Complete codex_prompt_from_work_item target IDs from active project tree."""
    if getattr(parsed_args, "template_name", "") != "codex_prompt_from_work_item":
        return None
    project_root = request_variables.find_repo_root()
    if project_root is None:
        return []
    return completion_sources.work_item_ids(project_root=project_root, prefix=prefix)
