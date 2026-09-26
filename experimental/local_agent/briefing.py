"""Briefing prompt, output schema, and deterministic output checks."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re

from local_agent import settings

_PROMPT_DIR = pathlib.Path(__file__).resolve().parent / "prompts"
_REF_PATTERN = re.compile(
    r"^S(?P<source>\d+)(?::L(?P<start>\d+)(?:-L?(?P<end>\d+))?)?$"
)
CLAIM_KINDS = ("fact", "suggestion", "question")
CLAIM_LISTS = (
    "constraints",
    "dependencies",
    "evidence_gaps",
    "relevant_sources",
    "open_questions",
)

_CLAIM_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "kind": {"type": "string", "enum": list(CLAIM_KINDS)},
        "refs": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["text", "kind", "refs"],
}

OUTPUT_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "readiness_statement": {"type": "string"},
        **{name: {"type": "array", "items": _CLAIM_SCHEMA} for name in CLAIM_LISTS},
    },
    "required": ["summary", "readiness_statement", *CLAIM_LISTS],
}


class InvalidBriefingError(ValueError):
    """Raised when model output is not a schema-valid briefing."""


def load_prompt_template(version: str = settings.PROMPT_VERSION) -> str:
    return (_PROMPT_DIR / f"{version}.md").read_text(encoding="utf-8")


def prompt_template_sha256(version: str = settings.PROMPT_VERSION) -> str:
    return hashlib.sha256(load_prompt_template(version).encode("utf-8")).hexdigest()


def render_prompt(packet_text: str, version: str = settings.PROMPT_VERSION) -> str:
    return load_prompt_template(version).replace("{{PACKET}}", packet_text)


def parse_briefing(raw_text: str) -> dict[str, object]:
    """Parse and structurally validate model output.

    Raises:
        InvalidBriefingError: on malformed JSON or a schema violation.
    """
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise InvalidBriefingError(f"output is not JSON: {error}") from error
    if not isinstance(data, dict):
        raise InvalidBriefingError("output is not a JSON object")
    for key in ("summary", "readiness_statement"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise InvalidBriefingError(f"missing or empty string field: {key}")
    for name in CLAIM_LISTS:
        claims = data.get(name)
        if not isinstance(claims, list):
            raise InvalidBriefingError(f"missing list field: {name}")
        for index, claim in enumerate(claims):
            _check_claim(name, index, claim)
    return data


def _check_claim(name: str, index: int, claim: object) -> None:
    where = f"{name}[{index}]"
    if not isinstance(claim, dict):
        raise InvalidBriefingError(f"{where} is not an object")
    if not isinstance(claim.get("text"), str) or not claim["text"].strip():
        raise InvalidBriefingError(f"{where}.text is missing")
    if claim.get("kind") not in CLAIM_KINDS:
        raise InvalidBriefingError(f"{where}.kind is not one of {CLAIM_KINDS}")
    refs = claim.get("refs")
    if not isinstance(refs, list) or not all(isinstance(ref, str) for ref in refs):
        raise InvalidBriefingError(f"{where}.refs is not a list of strings")


def check_citations(
    briefing: dict[str, object], source_refs: list[dict[str, object]]
) -> dict[str, object]:
    """Report which citations resolve to included source ids and line ranges.

    Resolution is mechanical; whether a cited source *supports* a claim is a
    human judgment recorded separately in the evaluation.
    """
    ranges = {
        str(ref["source_id"]): (int(ref["line_start"]), int(ref["line_end"]))
        for ref in source_refs
    }
    total = 0
    resolved = 0
    unresolved: list[str] = []
    malformed = 0
    uncited_facts = 0
    for name in CLAIM_LISTS:
        for claim in briefing.get(name, []):  # type: ignore[union-attr]
            refs = claim.get("refs", [])
            if claim.get("kind") == "fact" and not refs:
                uncited_facts += 1
            for ref in refs:
                total += 1
                if _REF_PATTERN.match(ref.strip()) is None:
                    # Free-form text is counted, never copied into records
                    # that sanitized exports include.
                    malformed += 1
                elif _ref_resolves(ref, ranges):
                    resolved += 1
                else:
                    unresolved.append(ref.strip())
    return {
        "citations_total": total,
        "citations_resolved": resolved,
        "unresolved_citations": unresolved,
        "malformed_citations": malformed,
        "uncited_facts": uncited_facts,
    }


def _ref_resolves(ref: str, ranges: dict[str, tuple[int, int]]) -> bool:
    match = _REF_PATTERN.match(ref.strip())
    if match is None:
        return False
    key = f"S{match.group('source')}"
    if key not in ranges:
        return False
    if match.group("start") is None:
        return True
    low, high = ranges[key]
    start = int(match.group("start"))
    end = int(match.group("end") or start)
    return low <= start <= end <= high
