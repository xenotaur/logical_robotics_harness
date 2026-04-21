#!/usr/bin/env python
"""
Create a filled-out request from a template.

Examples:
    scripts/aiprog/request.py improve_coverage src/lrh/analysis/llm_extractor.py

    scripts/aiprog/request.py bootstrap_project \
        --repo-name taurworks \
        --project-goal "Turn taurworks into a robust project bootstrap CLI" \
        --background-file notes/taurworks_background.md

    scripts/aiprog/request.py work_items_from_audit \
        --audit-file audits/style_audit_2026_04_10.md \
        --style-file STYLE.md

    scripts/aiprog/request.py codex_prompt_from_work_item \
        --work-item-file project/work_items/WI-STYLE-0001.md \
        --style-file STYLE.md \
        --background-file notes/context.md

    scripts/aiprog/request.py pr_against_work_item \
        --work-item-file project/work_items/WI-STYLE-0001.md \
        --patch-file patches/WI-STYLE-0001.diff \
        --style-file STYLE.md

Templates live in:
    scripts/aiprog/templates/request/<template_name>.md

Interpolation variables use the form:
    {{VARIABLE_NAME}}
"""

import pathlib
import sys

from lrh.assist import request_cli


def _default_template_root() -> pathlib.Path:
    """Resolve request templates relative to this script location."""
    return pathlib.Path(__file__).resolve().parent / "templates" / "request"


def main(argv=None) -> int:
    return request_cli.run_request_cli(
        argv=argv if argv is not None else sys.argv[1:],
        template_root=_default_template_root(),
        prog="request.py",
    )


if __name__ == "__main__":
    raise SystemExit(main())
