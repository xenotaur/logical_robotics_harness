"""Shared raw-text lexical detector for unsafe frontmatter plain scalars.

Operates on frontmatter TEXT before YAML parsing, so it can flag content
that would either crash ``yaml.safe_load`` or silently change meaning
under it -- the same class of bug ``WI-FRONTMATTER-PARSER-CONSOLIDATION``
fixed for the two hand-rolled parsers it replaced, generalized into one
reusable detector per ``PROP-LRH-FRONTMATTER-PARSER`` Decisions 4-5.

Used by both ``lrh validate`` (report-only lint, see ``control/validator.py``)
and ``lrh project doctor --fix-frontmatter`` (the one-time migration tool,
see ``control/frontmatter_migration.py``) so the two can never disagree
about what's unsafe -- a real risk an earlier design draft ran into (a
lint guard and a migration tool built from independent detector logic).

Not a closed enumeration: these are the four confirmed unsafe-plain-scalar
patterns as of this WI, not an exhaustive YAML-landmine catalog.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import yaml

# Fields whose values are always expected to be strings (or lists of
# strings). Used only by the implicit-non-string-type check -- a
# deliberately conservative allow-list: a genuine string field missing from
# this set produces a false negative (safe to miss), but a non-string field
# wrongly listed here would produce a false positive, so keep this to
# fields actually documented as string-typed across the planning-node and
# execution-record schemas (see ``control/validator.py``'s ``*_LIST_FIELDS``
# and ``*_REQUIRED_FIELDS`` constants, and ``project/executions/README.md``).
KNOWN_STRING_FIELDS = frozenset(
    {
        "id",
        "title",
        "type",
        "status",
        "owner",
        "stage",
        "origin",
        "summary",
        "purpose",
        "kind",
        "resolution",
        "blocked_reason",
        "instruction_source",
        "session_transcript",
        "execution_id",
        "prompt_id",
        "work_item",
        "pr",
        "commit",
        "agent",
        "display_name",
        "rerun_of",
        # "created_at" is deliberately absent: its implicit resolution to a
        # datetime/date under real YAML is an accepted divergence (Decision
        # 2 of PROP-LRH-FRONTMATTER-PARSER), not an unsafe pattern -- the
        # three real consumers were patched to handle it explicitly instead.
        # list-of-string fields -- items are checked the same way as
        # scalar-field values (see ``iter_unsafe_scalars``'s list-item walk).
        "contributors",
        "assigned_agents",
        "related_focus",
        "related_roadmap",
        "related_workstreams",
        "related_design",
        "depends_on",
        "blocked_by",
        "expected_actions",
        "forbidden_actions",
        "acceptance",
        "required_evidence",
        "artifacts_expected",
        "allowed_paths",
        "forbidden_paths",
        "validation_commands",
        "expected_artifacts",
        "policy_gates",
        "agent_constraints",
        "children",
        "work_items",
        "execution_records",
        "evidence",
        "exit_criteria",
        "implemented_by",
        "supersedes",
        "roles",
    }
)

# c-indicator characters (YAML 1.1/1.2 spec) that cannot start a plain
# scalar in block context. ``-``, ``?``, and ``:`` are omitted: they're
# only reserved when immediately followed by whitespace (block-sequence
# entry, explicit key, or mapping-value indicator respectively), which the
# unescaped-colon/hash checks below already cover for the cases that
# matter here.
_RESERVED_LEADING_CHARS = frozenset("`@%[]{},&*!|>#\"'")

CATEGORY_UNESCAPED_COLON = "unescaped_colon"
CATEGORY_UNESCAPED_HASH = "unescaped_hash"
CATEGORY_RESERVED_INDICATOR = "reserved_indicator"
CATEGORY_IMPLICIT_TYPE = "implicit_nonstring_type"

CATEGORY_DESCRIPTIONS = {
    CATEGORY_UNESCAPED_COLON: (
        "an unquoted ': ' inside a plain scalar collapses a list item into "
        "a one-entry mapping, or is a hard YAML syntax error -- quote the "
        "value"
    ),
    CATEGORY_UNESCAPED_HASH: (
        "an unquoted ' #' inside a plain scalar is read as a comment by "
        "real YAML, silently truncating everything after it -- quote the "
        "value"
    ),
    CATEGORY_RESERVED_INDICATOR: (
        "a plain scalar cannot start with this character under real YAML "
        "-- quote the value"
    ),
    CATEGORY_IMPLICIT_TYPE: (
        "this string-typed field's value would implicitly resolve to a "
        "non-string YAML type (bool, null, int, float, or date) -- quote "
        "the value to keep it a string"
    ),
}

_BLOCK_SCALAR_INDICATORS = {">", "|", ">-", "|-", ">+", "|+"}


@dataclass(frozen=True)
class UnsafeScalarFinding:
    """One unsafe-plain-scalar occurrence, located within frontmatter text."""

    line: int  # 1-indexed, relative to the start of the frontmatter text
    field: str
    category: str
    detail: str
    raw_line: str


def iter_unsafe_scalars(frontmatter_text: str) -> list[UnsafeScalarFinding]:
    """Scan raw frontmatter text for unsafe plain-scalar constructs.

    Deliberately does not parse the text as YAML first -- a file this
    detects issues in may not even be valid YAML yet. Walks the same shape
    of structure the pre-consolidation lenient parser walked (top-level
    ``key: value`` lines, ``key:`` followed by a ``- item`` block, or a
    ``key: >`` folded scalar), checking only genuine plain-scalar value
    text -- block-scalar bodies and already-quoted values are out of scope
    by construction, since YAML already treats them literally.
    """

    findings: list[UnsafeScalarFinding] = []
    lines = frontmatter_text.splitlines()
    index = 0
    current_field: str | None = None

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            index += 1
            continue

        if line.startswith((" ", "\t")):
            candidate = line.lstrip()
            if candidate.startswith("- ") and current_field is not None:
                value_text = candidate[2:]
                finding = _check_value(current_field, value_text, index + 1, line)
                if finding is not None:
                    findings.append(finding)
            # Any other indented continuation (block-scalar body lines,
            # nested mapping content) is raw text YAML already treats
            # literally -- not a plain-scalar risk, so nothing to check.
            index += 1
            continue

        if ":" not in line:
            index += 1
            continue

        key, _, raw_value = line.partition(":")
        key = key.strip()
        current_field = key
        value_text = raw_value.strip()

        if value_text and value_text not in _BLOCK_SCALAR_INDICATORS:
            finding = _check_value(key, value_text, index + 1, line)
            if finding is not None:
                findings.append(finding)

        index += 1

    return findings


def _check_value(
    field: str, value_text: str, line_number: int, raw_line: str
) -> UnsafeScalarFinding | None:
    if not value_text:
        return None
    if value_text[0] in ("'", '"'):
        # Already quoted -- YAML treats the contents literally regardless
        # of what's inside, so this is safe by construction.
        return None

    if (value_text[0] == "[" and value_text.endswith("]")) or (
        value_text[0] == "{" and value_text.endswith("}")
    ):
        # A well-formed flow sequence/mapping (e.g. "[]", "[a, b]") is
        # valid, common YAML -- not a reserved-indicator risk.
        return None

    if value_text[0] in _RESERVED_LEADING_CHARS:
        return UnsafeScalarFinding(
            line=line_number,
            field=field,
            category=CATEGORY_RESERVED_INDICATOR,
            detail=CATEGORY_DESCRIPTIONS[CATEGORY_RESERVED_INDICATOR],
            raw_line=raw_line,
        )

    if re.search(r":(\s|$)", value_text):
        return UnsafeScalarFinding(
            line=line_number,
            field=field,
            category=CATEGORY_UNESCAPED_COLON,
            detail=CATEGORY_DESCRIPTIONS[CATEGORY_UNESCAPED_COLON],
            raw_line=raw_line,
        )

    if re.search(r"\s#", value_text):
        return UnsafeScalarFinding(
            line=line_number,
            field=field,
            category=CATEGORY_UNESCAPED_HASH,
            detail=CATEGORY_DESCRIPTIONS[CATEGORY_UNESCAPED_HASH],
            raw_line=raw_line,
        )

    if field in KNOWN_STRING_FIELDS and _resolves_to_nonstring_type(value_text):
        return UnsafeScalarFinding(
            line=line_number,
            field=field,
            category=CATEGORY_IMPLICIT_TYPE,
            detail=CATEGORY_DESCRIPTIONS[CATEGORY_IMPLICIT_TYPE],
            raw_line=raw_line,
        )

    return None


def _resolves_to_nonstring_type(value_text: str) -> bool:
    try:
        resolved: Any = yaml.safe_load(value_text)
    except yaml.YAMLError:
        # A genuine syntax error is caught by the other categories, or by
        # yaml.safe_load itself downstream -- not this check's job.
        return False
    return resolved is not None and not isinstance(resolved, str)
