"""T1 brief: a work-item briefing preset built on T0 ``ask``.

``brief <WI-ID>`` is ``ask --wi <WI-ID>`` with a fixed briefing prompt. The
readiness section is written by the tool from LRH's diagnostics and stored as
the answer's ``preamble``. The model is told not to state readiness, but its
prose is not checked. It must end with one ``READINESS:`` line, which is
compared with the diagnostics; a contradicting, missing, misplaced, or
duplicated line flags the run.
"""

from __future__ import annotations

import pathlib
import re
from collections.abc import Callable

from local_agent import ask, model, recorder, settings

PROMPT_VERSION = "brief_v2"
KIND_BRIEF = "brief"

STATUS_AGREES = "agrees"
STATUS_CONTRADICTS = "contradicts"
STATUS_MISSING = "missing"
STATUS_UNAVAILABLE = "unavailable"
STATUS_MISPLACED = "misplaced"
STATUS_DUPLICATED = "duplicated"

_READINESS_LINE = re.compile(
    r"READINESS:\s*prompt_ready=(?P<prompt>yes|no)\s+"
    r"execution_ready=(?P<execution>yes|no)",
    re.IGNORECASE,
)
# Markdown a small model may wrap the line in: bold, code, quote, list, heading.
_LEAD = " \t*_`>-#"
_TRAIL = " \t*_`."


def _normalized(line: str) -> str:
    return line.strip().lstrip(_LEAD).rstrip(_TRAIL)


def _claim(line: str) -> dict[str, bool] | None:
    match = _READINESS_LINE.fullmatch(_normalized(line))
    if match is None:
        return None
    return {
        "prompt_ready": match["prompt"].lower() == "yes",
        "execution_ready": match["execution"].lower() == "yes",
    }


def question(work_item: str) -> str:
    return f"Brief the owner on work item {work_item}."


def build_context(
    *,
    repo: pathlib.Path,
    work_item: str,
    revision: str = "HEAD",
    project_dir: str = ".",
    budgets: settings.Budgets | None = None,
) -> ask.AskContext:
    """The ``ask --wi`` context: the work item, its sources, and diagnostics."""
    return ask.build_context(
        repo=repo,
        revision=revision,
        work_item=work_item,
        project_dir=project_dir,
        budgets=budgets,
    )


def expected_readiness(ctx: ask.AskContext) -> dict[str, bool] | None:
    """Readiness values from LRH's diagnostics, or ``None`` if unavailable."""
    diagnostics = ctx.diagnostics or {}
    prompt = diagnostics.get("prompt_readiness")
    execution = diagnostics.get("execution_readiness")
    if not isinstance(prompt, dict) or not isinstance(execution, dict):
        return None
    prompt_ready = prompt.get("prompt_ready")
    execution_ready = execution.get("execution_ready")
    if not isinstance(prompt_ready, bool) or not isinstance(execution_ready, bool):
        return None
    return {"prompt_ready": prompt_ready, "execution_ready": execution_ready}


def readiness_check(text: str, ctx: ask.AskContext) -> dict[str, object]:
    """Compare the briefing's ``READINESS:`` line(s) with the diagnostics.

    Lines may be wrapped in light Markdown (bold, code, quote, list item) and
    end with a period. Any disagreeing line is ``contradicts``; none is
    ``missing``; more than one agreeing line is ``duplicated``; an agreeing
    line that is not the final non-blank line is ``misplaced``. Without usable
    diagnostics the check is ``unavailable``.
    Only the ``READINESS:`` line is checked, not the briefing's prose.
    """
    expected = expected_readiness(ctx)
    lines = [line for line in text.splitlines() if line.strip()]
    claims = [claim for claim in map(_claim, lines) if claim is not None]
    last_is_claim = bool(lines) and _claim(lines[-1]) is not None
    if expected is None:
        status = STATUS_UNAVAILABLE
    elif not claims:
        status = STATUS_MISSING
    elif any(claim != expected for claim in claims):
        status = STATUS_CONTRADICTS
    elif len(claims) > 1:
        status = STATUS_DUPLICATED
    elif not last_is_claim:
        status = STATUS_MISPLACED
    else:
        status = STATUS_AGREES
    mismatches = sorted(
        {
            key
            for claim in claims
            for key, value in claim.items()
            if expected is not None and expected[key] != value
        }
    )
    return {
        "readiness_check": {
            "status": status,
            "expected": expected,
            "claimed": claims,
            "mismatches": mismatches,
        }
    }


def _one_line(value: object) -> str:
    return " ".join(str(value).split())


def _yes_no(value: object) -> str:
    return "yes" if value is True else "no" if value is False else "unknown"


def readiness_block(ctx: ask.AskContext) -> str:
    """The authoritative readiness section, written from LRH's diagnostics.

    The model is told not to restate readiness; this block is shown first and
    stored as the answer's ``preamble``. Values are collapsed to one line each,
    so diagnostics text cannot add lines to the block.
    """
    diagnostics = ctx.diagnostics or {}
    prompt = diagnostics.get("prompt_readiness")
    execution = diagnostics.get("execution_readiness")
    prompt = prompt if isinstance(prompt, dict) else {}
    execution = execution if isinstance(execution, dict) else {}
    lines = [
        "## Readiness (from LRH diagnostics)",
        "",
        f"- prompt_ready: {_yes_no(prompt.get('prompt_ready'))}",
    ]
    for reason in prompt.get("blocking_reasons") or []:
        lines.append(f"  - blocking: {_one_line(reason)}")
    for warning in prompt.get("warnings") or []:
        lines.append(f"  - warning: {_one_line(warning)}")
    lines.append(f"- execution_ready: {_yes_no(execution.get('execution_ready'))}")
    for issue in execution.get("issues") or []:
        if isinstance(issue, dict):
            lines.append(
                f"  - {_one_line(issue.get('severity'))}: "
                f"{_one_line(issue.get('code'))}: {_one_line(issue.get('message'))}"
            )
    if not diagnostics:
        lines = ["## Readiness (from LRH diagnostics)", "", "- unavailable"]
    return "\n".join(lines) + "\n\n"


def run_brief(
    *,
    store: recorder.Store,
    work_item: str,
    ctx: ask.AskContext,
    adapter: model.ModelAdapter,
    budgets: settings.Budgets,
    on_text: Callable[[str], None] | None = None,
) -> str:
    """Brief one work item with one call; return the run id."""
    return ask.run_ask(
        store=store,
        question=question(work_item),
        ctx=ctx,
        adapter=adapter,
        budgets=budgets,
        on_text=on_text,
        kind=KIND_BRIEF,
        prompt_version=PROMPT_VERSION,
        post_check=readiness_check,
        record={"work_item_id": work_item},
        preamble=readiness_block(ctx),
    )
