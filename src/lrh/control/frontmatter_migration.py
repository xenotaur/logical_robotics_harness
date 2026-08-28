"""One-time content migration tool for unsafe frontmatter plain scalars.

Backs ``lrh project doctor --fix-frontmatter``. Uses the shared
``frontmatter_lint`` detector (see that module) to find unsafe raw-text
scalars, then re-encodes exactly the flagged line's value as safe YAML --
never by stripping the raw line at the unsafe construct, which would
silently lose real content (e.g. dropping " #531" from a sentence that
legitimately ends in "...verifying PR #531"). Instead it takes the FULL
value text on the flagged line, verbatim, and quotes it.

This serves the same purpose as "read the historical lenient parser's
reading" (``PROP-LRH-FRONTMATTER-PARSER`` Decision 4) without needing a
copy of that now-removed parser module: none of the raw text this tool
targets is already quoted (the detector only flags unquoted values), and
for three of the four unsafe categories the pre-consolidation lenient
parser would have done nothing but return the line's value text
unchanged for a genuine free-text scalar. The fourth category (a value
that reads as a bool/null/int/date) is exactly what "quote it" fixes,
without needing to know what any parser would have made of it -- the
digits/word themselves are already correct, only their YAML type needs
pinning to string.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from lrh.control import frontmatter_lint
from lrh.control.parser import split_frontmatter_and_body


@dataclass(frozen=True)
class FixedField:
    """One line rewritten by the migration tool."""

    line: int
    field: str
    category: str
    before: str
    after: str


@dataclass(frozen=True)
class FileFixResult:
    """Result of running the migration tool against one file."""

    path: Path
    changed: bool
    fixes: tuple[FixedField, ...]
    new_text: str


def render_safe_scalar(raw_value_text: str) -> str:
    """Re-encode a raw, unquoted plain-scalar value as safe YAML.

    Preserves the content exactly -- only the YAML encoding changes.
    Self-verifies the result round-trips to the original text.
    """

    dumped = yaml.safe_dump(
        {"x": raw_value_text},
        default_flow_style=False,
        width=float("inf"),
        allow_unicode=True,
    ).strip()
    assert dumped.startswith("x:")
    rendered = dumped[len("x:") :].lstrip(" ")
    if yaml.safe_load(rendered) != raw_value_text:
        raise ValueError(f"failed to safely re-encode scalar: {raw_value_text!r}")
    return rendered


def _extract_value_text(raw_line: str, *, is_list_item: bool) -> str:
    stripped = raw_line.lstrip()
    if is_list_item:
        assert stripped.startswith("- ")
        return stripped[2:]
    _key, _sep, rest = raw_line.partition(":")
    # Only strip the separator whitespace on the left (between ":" and the
    # value); preserve the rest verbatim, including any trailing
    # whitespace, so the "preserves content exactly" contract holds even
    # for the rare case of meaningful trailing spaces.
    return rest.lstrip()


def plan_fixes(frontmatter_text: str) -> tuple[str, list[FixedField]]:
    """Compute a fixed frontmatter text plus the fields touched.

    Returns the original text unchanged (and an empty fix list) if no
    unsafe scalar was found. Each fix rewrites exactly the one physical
    line the detector flagged -- a minimal, single-line diff per finding,
    never a full-field or full-file re-dump.
    """

    findings = frontmatter_lint.iter_unsafe_scalars(frontmatter_text)
    if not findings:
        return frontmatter_text, []

    lines = frontmatter_text.splitlines(keepends=True)
    fixes: list[FixedField] = []

    for finding in findings:
        idx = finding.line - 1
        raw_line = lines[idx]
        is_list_item = raw_line.lstrip().startswith("- ")
        indent = raw_line[: len(raw_line) - len(raw_line.lstrip())]
        value_text = _extract_value_text(
            raw_line.rstrip("\n"), is_list_item=is_list_item
        )
        safe_value = render_safe_scalar(value_text)
        if is_list_item:
            new_line = f"{indent}- {safe_value}\n"
        else:
            new_line = f"{indent}{finding.field}: {safe_value}\n"
        lines[idx] = new_line
        fixes.append(
            FixedField(
                line=finding.line,
                field=finding.field,
                category=finding.category,
                before=raw_line.rstrip("\n"),
                after=new_line.rstrip("\n"),
            )
        )

    return "".join(lines), fixes


def fix_file(path: Path, *, apply: bool) -> FileFixResult:
    """Plan (and, if ``apply``, write) the fix for one Markdown file."""

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return FileFixResult(path=path, changed=False, fixes=(), new_text=text)
    try:
        frontmatter_text, body = split_frontmatter_and_body(text)
    except ValueError:
        return FileFixResult(path=path, changed=False, fixes=(), new_text=text)

    new_frontmatter, fixes = plan_fixes(frontmatter_text)
    if not fixes:
        return FileFixResult(path=path, changed=False, fixes=(), new_text=text)

    new_text = "---\n" + new_frontmatter + "---\n" + body

    remaining = frontmatter_lint.iter_unsafe_scalars(new_frontmatter)
    if remaining:
        raise ValueError(
            f"{path}: {len(remaining)} unsafe scalar(s) remain after fixing"
        )
    yaml.safe_load(new_frontmatter)  # raises yaml.YAMLError on invalid YAML

    if apply:
        path.write_text(new_text, encoding="utf-8")

    return FileFixResult(path=path, changed=True, fixes=tuple(fixes), new_text=new_text)


def fix_project(project_root: Path, *, apply: bool) -> list[FileFixResult]:
    """Run the migration tool across every Markdown file in the tree."""

    results: list[FileFixResult] = []
    for path in sorted(project_root.glob("**/*.md")):
        result = fix_file(path, apply=apply)
        if result.changed:
            results.append(result)
    return results
