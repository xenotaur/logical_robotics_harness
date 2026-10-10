"""Export LRH skills as upload bundles for hosted assistants.

Hosted assistants such as ChatGPT online have no local skills directory to
install into; skills are uploaded instead. This module renders canonical
skills into one deterministic ZIP bundle per skill without modifying the
canonical source tree or any local install. Bundles are generated outputs,
never a new authoritative copy of the skill source.
"""

from __future__ import annotations

import dataclasses
import enum
import io
import os
import re
import zipfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

from lrh.skills import installer

_SKILL_MD = "SKILL.md"
_OPENAI_YAML = "agents/openai.yaml"
_BUNDLE_DIRS = ("references", "scripts", "assets")
# Codex metadata lives under agents/; it is read for manual-only detection but
# is never part of a portable bundle.
_EXCLUDED_TOP_LEVEL = ("agents",)
# Portable Agent Skills frontmatter fields. Everything else is stripped: the
# agent-specific keys (argument-hint, disable-model-invocation, context,
# disallowed-tools) and the spec's experimental allowed-tools, whose tool names
# are agent-specific and mean nothing to a hosted assistant. `when_to_use` is
# not a portable key either, but its guidance is carried into the bundle
# rather than dropped (see `_when_to_use_plan`).
PORTABLE_FRONTMATTER_KEYS = (
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
)
_SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_SKILL_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
# Agent Skills specification (https://agentskills.io/specification):
# `compatibility` "must be 1-500 characters if provided". LRH additionally
# rejects a whitespace-only value, which carries no information.
MAX_COMPATIBILITY_LENGTH = 500
_WHEN_TO_USE = "when_to_use"
_WHEN_TO_USE_HEADING = "## When to use"
# Lines split on "\n" only, and an ATX H1 heading (up to 3 spaces of indent).
_LINE_RE = re.compile(r"[^\n]*\n|[^\n]+$")
_H1_RE = re.compile(r" {0,3}#(?:[ \t]|$)")
# Upload limits documented by the OpenAI Skills API guide. They are assumed to
# apply to ChatGPT uploads until manual dogfooding confirms otherwise.
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_FILE_COUNT = 500
MAX_FILE_BYTES = 25 * 1024 * 1024
# Fixed ZIP metadata so identical inputs produce byte-identical archives.
_ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)
_ZIP_FILE_ATTRIBUTES = 0o100644 << 16
_ZIP_CREATE_SYSTEM_UNIX = 3
_ZIP_COMPRESS_LEVEL = 9

_FENCED_SHELL_PATTERN = re.compile(r"^\s*```\s*(bash|sh|shell|zsh|console)\b", re.M)
_GIT_PATTERN = re.compile(
    r"(?:^|[\s`$(])git\s+(?:add|branch|checkout|clone|commit|diff|fetch|grep|log|"
    r"ls-files|merge|pull|push|rebase|reset|rev-parse|show|stash|status|switch|"
    r"worktree)\b",
    re.M,
)
_GH_PATTERN = re.compile(
    r"(?:^|[\s`$(])gh\s+(?:api|auth|issue|pr|release|repo|run|workflow)\b", re.M
)
_LRH_CLI_PATTERN = re.compile(r"(?:^|[\s`$(])lrh\s+[a-z][a-z-]*\b", re.M)
# ChatGPT online can run commands in its own hosted environment, but not
# against the user's local repository or machine, which LRH workflows assume.
_LOCAL_TOOLS_LIMIT = (
    "which ChatGPT online cannot run against your local repository or machine"
)
_CAPABILITY_LABELS = {
    "requires_git": "local `git`",
    "requires_gh": "the GitHub `gh` CLI",
    "requires_lrh_cli": "the `lrh` CLI",
    "requires_shell": "shell commands",
}


class ExportTarget(str, enum.Enum):
    CHATGPT = "chatgpt"


class ExportStatus(str, enum.Enum):
    EXPORTED = "exported"
    SKIPPED_MANUAL_ONLY = "skipped_manual_only"
    FAILED = "failed"


class SkillExportError(ValueError):
    """Raised when an export request cannot be satisfied at all."""


@dataclasses.dataclass(frozen=True)
class ExportNotice:
    code: str
    message: str


@dataclasses.dataclass(frozen=True)
class SkillExportResult:
    name: str
    status: ExportStatus
    archive_path: Path | None = None
    notices: tuple[ExportNotice, ...] = ()
    errors: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class ExportReport:
    target: ExportTarget
    out_dir: Path
    source_label: str
    results: tuple[SkillExportResult, ...]

    @property
    def has_failures(self) -> bool:
        return any(result.status is ExportStatus.FAILED for result in self.results)


@dataclasses.dataclass(frozen=True)
class _PreparedSkill:
    result: SkillExportResult
    archive: bytes | None = None


class ChatGPTSkillRenderer:
    """Render canonical skill files into a portable ChatGPT bundle tree.

    Keeps `SKILL.md` plus the portable `references/`, `scripts/`, and
    `assets/` directories, and reduces `SKILL.md` frontmatter to the portable
    Agent Skills fields. `when_to_use` guidance is folded into `description`
    when the result fits the description limit, and otherwise added as a
    generated `## When to use` section; existing body text is never modified.
    """

    def render(
        self, skill_name: str, source_files: dict[str, bytes]
    ) -> dict[str, bytes]:
        rendered = {
            path: content
            for path, content in source_files.items()
            if _is_bundle_path(path)
        }
        skill_md = rendered.get(_SKILL_MD)
        if skill_md is not None:
            rendered[_SKILL_MD] = _render_skill_md(skill_md)
        return rendered


def export_skills(
    *,
    out_dir: Path,
    source: str | Path | installer.SkillSource = (
        installer.SkillSourceKind.PACKAGE.value
    ),
    skill_names: Sequence[str] | None = None,
    target: str | ExportTarget = ExportTarget.CHATGPT,
    project_root: Path | None = None,
) -> ExportReport:
    """Export skills from `source` as one upload bundle per skill.

    Every selected skill is rendered and validated in memory first. Bundles
    are written only when no selected skill failed validation, so a failed
    run never leaves a partial set of archives behind.

    Without `skill_names`, all public skills are selected except manual-only
    skills, which are reported as skipped. A manual-only skill is exported
    only when explicitly named, and then carries a compatibility notice.
    """
    export_target = ExportTarget(target)
    skill_source = installer.resolve_skill_source(source, project_root=project_root)
    available = skill_source.skill_names()
    if isinstance(skill_names, str):
        raise TypeError(
            "skill_names must be a sequence of skill names, not a single string"
        )
    explicit = skill_names is not None
    if explicit:
        selected = sorted(set(skill_names))
        unknown = [name for name in selected if name not in available]
        if unknown:
            raise SkillExportError(
                "unknown skill(s) for source "
                f"{skill_source.label}: {', '.join(unknown)}"
            )
        if not selected:
            raise SkillExportError("no skills selected for export")
    else:
        selected = available

    _check_output_dir(out_dir, skill_source)

    prepared = [
        _prepare_skill(name, skill_source, out_dir, explicit=explicit)
        for name in selected
    ]
    if not any(item.result.status is ExportStatus.FAILED for item in prepared):
        _publish_archives(
            [
                (item.result.archive_path, item.archive)
                for item in prepared
                if item.archive is not None and item.result.archive_path is not None
            ]
        )

    return ExportReport(
        target=export_target,
        out_dir=out_dir,
        source_label=skill_source.label,
        results=tuple(item.result for item in prepared),
    )


def format_export_report(report: ExportReport) -> str:
    lines = [f"{report.target.value}: {report.out_dir} (source: {report.source_label})"]
    for result in report.results:
        if result.status is ExportStatus.EXPORTED:
            verb = "exported" if not report.has_failures else "not written"
            lines.append(f"  {verb}: {result.name} -> {result.archive_path}")
        elif result.status is ExportStatus.SKIPPED_MANUAL_ONLY:
            lines.append(
                f"  skipped (manual-only): {result.name}"
                f" (export explicitly with --skill {result.name})"
            )
        else:
            for error in result.errors:
                lines.append(f"  error: {result.name}: {error}")
        lines.extend(
            f"  notice: {result.name}: {message}"
            for message in _grouped_notice_messages(result.notices)
        )
    if report.has_failures:
        failed = sum(
            1 for result in report.results if result.status is ExportStatus.FAILED
        )
        lines.append(f"\nno bundles written: {failed} skill(s) failed validation")
    return "\n".join(lines)


def _grouped_notice_messages(notices: Sequence[ExportNotice]) -> list[str]:
    """Collapse per-capability notices into one line for terminal output."""
    messages: list[str] = []
    capabilities: list[str] = []
    for notice in notices:
        if notice.code in _CAPABILITY_LABELS:
            capabilities.append(_CAPABILITY_LABELS[notice.code])
        else:
            messages.append(notice.message)
    if capabilities:
        messages.append(
            "workflow uses "
            + ", ".join(capabilities)
            + f", {_LOCAL_TOOLS_LIMIT}; instructions are not rewritten for it"
        )
    return messages


def build_archive(skill_name: str, files: dict[str, bytes]) -> bytes:
    """Return deterministic ZIP bytes with `files` under one `skill_name/` dir."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for relative_path in sorted(files):
            info = zipfile.ZipInfo(
                f"{skill_name}/{relative_path}", date_time=_ZIP_DATE_TIME
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = _ZIP_CREATE_SYSTEM_UNIX
            info.external_attr = _ZIP_FILE_ATTRIBUTES
            archive.writestr(
                info, files[relative_path], compresslevel=_ZIP_COMPRESS_LEVEL
            )
    return buffer.getvalue()


def _prepare_skill(
    skill_name: str,
    source: installer.SkillSource,
    out_dir: Path,
    *,
    explicit: bool,
) -> _PreparedSkill:
    try:
        source_files = installer._collect_source_files(source.skill_root(skill_name))
    except installer.SkillSourceError as err:
        return _failed(skill_name, [str(err)])

    errors: list[str] = []
    notices: list[ExportNotice] = []

    metadata = _validate_skill_md(skill_name, source_files, errors)
    manual_only = _is_manual_only(metadata, source_files, errors)
    if errors:
        return _failed(skill_name, errors)

    if manual_only and not explicit:
        stale_notices: tuple[ExportNotice, ...] = ()
        stale_archive = out_dir / f"{skill_name}.zip"
        if stale_archive.exists() or stale_archive.is_symlink():
            stale_notices = (
                ExportNotice(
                    code="stale_manual_only_bundle",
                    message=(
                        f"an earlier bundle {stale_archive.name} is still in the"
                        " output directory; remove it before uploading the folder"
                    ),
                ),
            )
        return _PreparedSkill(
            result=SkillExportResult(
                name=skill_name,
                status=ExportStatus.SKIPPED_MANUAL_ONLY,
                notices=stale_notices,
            )
        )

    notices.extend(_skipped_entry_notices(source_files))
    # YAML allows non-string keys (e.g. `1: value`); sort by string form so
    # mixed key types report cleanly instead of raising TypeError. A
    # `when_to_use` is carried into the bundle, so it is never reported here.
    stripped = sorted(
        str(key)
        for key in metadata
        if key not in PORTABLE_FRONTMATTER_KEYS and key != _WHEN_TO_USE
    )
    if stripped:
        notices.append(
            ExportNotice(
                code="stripped_metadata",
                message=(
                    "agent-specific frontmatter not included in the bundle: "
                    + ", ".join(f"`{key}`" for key in stripped)
                ),
            )
        )
    plan = _when_to_use_plan(metadata)
    if plan is not None and plan[0] == "section":
        notices.append(
            ExportNotice(
                code="when_to_use_section",
                message=(
                    "`when_to_use` guidance moved into a generated"
                    f' "{_WHEN_TO_USE_HEADING}" section in the bundled SKILL.md'
                    " because description plus guidance exceeds"
                    f" {MAX_DESCRIPTION_LENGTH} characters"
                ),
            )
        )
    if manual_only:
        notices.append(
            ExportNotice(
                code="manual_only",
                message=(
                    "manual-only skill; ChatGPT has no known explicit-only"
                    " control, so it may be selected automatically once uploaded"
                ),
            )
        )

    bundle = ChatGPTSkillRenderer().render(skill_name, source_files)
    errors.extend(_path_errors(bundle))
    errors.extend(_limit_errors(bundle))
    if errors:
        return _failed(skill_name, errors)
    notices.extend(_capability_notices(bundle))

    archive = build_archive(skill_name, bundle)
    if len(archive) > MAX_ARCHIVE_BYTES:
        return _failed(
            skill_name,
            [f"archive is {len(archive)} bytes; limit is {MAX_ARCHIVE_BYTES}"],
        )
    return _PreparedSkill(
        result=SkillExportResult(
            name=skill_name,
            status=ExportStatus.EXPORTED,
            archive_path=out_dir / f"{skill_name}.zip",
            notices=tuple(notices),
        ),
        archive=archive,
    )


def _failed(skill_name: str, errors: list[str]) -> _PreparedSkill:
    return _PreparedSkill(
        result=SkillExportResult(
            name=skill_name, status=ExportStatus.FAILED, errors=tuple(errors)
        )
    )


def _validate_skill_md(
    skill_name: str, source_files: dict[str, bytes], errors: list[str]
) -> dict[str, Any]:
    skill_md = source_files.get(_SKILL_MD)
    if skill_md is None:
        errors.append("missing SKILL.md")
        return {}
    try:
        parsed = installer._parse_skill_frontmatter(skill_md)
    except installer.SkillSourceError as err:
        errors.append(str(err))
        return {}
    if parsed is None:
        errors.append("SKILL.md must begin with a YAML frontmatter block")
        return {}
    metadata, _parts, _closing_index = parsed

    name = metadata.get("name")
    if name != skill_name:
        errors.append(
            f"frontmatter name {name!r} must match the skill directory {skill_name!r}"
        )
    if (
        not isinstance(name, str)
        or not _SKILL_NAME_PATTERN.match(name)
        or len(name) > MAX_SKILL_NAME_LENGTH
    ):
        errors.append(
            "frontmatter name must be lowercase letters, digits, and single"
            f" hyphens, at most {MAX_SKILL_NAME_LENGTH} characters"
        )
    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("frontmatter description must be a non-empty string")
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f"frontmatter description is {len(description)} characters;"
            f" limit is {MAX_DESCRIPTION_LENGTH}"
        )
    _validate_optional_portable_fields(metadata, errors)
    if _WHEN_TO_USE in metadata:
        guidance = metadata[_WHEN_TO_USE]
        if not isinstance(guidance, str) or not guidance.strip():
            errors.append(
                "frontmatter when_to_use must be a non-blank string when present;"
                " remove the key or give it text"
            )
    return metadata


def _validate_optional_portable_fields(
    metadata: dict[str, Any], errors: list[str]
) -> None:
    """Check the optional portable fields that are copied into the bundle."""
    if "license" in metadata and not isinstance(metadata["license"], str):
        errors.append("frontmatter license must be a string")
    if "compatibility" in metadata:
        compatibility = metadata["compatibility"]
        if not isinstance(compatibility, str):
            errors.append("frontmatter compatibility must be a string")
        elif not compatibility.strip():
            errors.append(
                "frontmatter compatibility must be a non-blank string when present;"
                " remove the key or give it text"
            )
        elif len(compatibility) > MAX_COMPATIBILITY_LENGTH:
            errors.append(
                f"frontmatter compatibility is {len(compatibility)} characters;"
                f" limit is {MAX_COMPATIBILITY_LENGTH}"
            )
    if "metadata" in metadata:
        extra = metadata["metadata"]
        if not isinstance(extra, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in extra.items()
        ):
            errors.append("frontmatter metadata must map string keys to string values")


def _is_manual_only(
    metadata: dict[str, Any], source_files: dict[str, bytes], errors: list[str]
) -> bool:
    # Validate both markers before combining them, so a valid Claude marker
    # cannot hide a malformed Codex policy.
    claude_manual = _claude_manual_only(metadata, errors)
    codex_manual = _codex_manual_only(source_files, errors)
    return claude_manual or codex_manual


def _claude_manual_only(metadata: dict[str, Any], errors: list[str]) -> bool:
    disable_flag = metadata.get("disable-model-invocation")
    if "disable-model-invocation" in metadata and not isinstance(disable_flag, bool):
        # A quoted "true" or a blank (null) value would otherwise read as not
        # manual-only; fail safe.
        errors.append(
            "frontmatter disable-model-invocation must be true or false;"
            " remove the key if the skill is not manual-only"
        )
        return False
    return disable_flag is True


def _codex_manual_only(source_files: dict[str, bytes], errors: list[str]) -> bool:
    openai_yaml = source_files.get(_OPENAI_YAML)
    if openai_yaml is None:
        return False
    try:
        loaded = yaml.safe_load(openai_yaml.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as err:
        # Manual-only status cannot be determined, so refuse rather than risk
        # exporting a manual-only skill as automatically selectable.
        errors.append(f"invalid Codex metadata in {_OPENAI_YAML}: {err}")
        return False
    if loaded is None:
        # An empty file declares no policy; any other non-mapping root is
        # malformed and must fail safe rather than read as "no policy".
        return False
    if not isinstance(loaded, dict):
        errors.append(f"cannot read invocation policy from {_OPENAI_YAML}")
        return False
    policy = loaded.get("policy")
    if policy is not None and not isinstance(policy, dict):
        errors.append(f"cannot read invocation policy from {_OPENAI_YAML}")
        return False
    if not isinstance(policy, dict):
        return False
    allow_implicit = policy.get("allow_implicit_invocation")
    if "allow_implicit_invocation" in policy and not isinstance(allow_implicit, bool):
        # A blank (null) value must not silently mean "no policy"; fail safe.
        errors.append(
            f"policy.allow_implicit_invocation in {_OPENAI_YAML} must be true or"
            " false; remove the key to declare no policy"
        )
        return False
    return allow_implicit is False


def _render_skill_md(content: bytes) -> bytes:
    parsed = installer._parse_skill_frontmatter(content)
    if parsed is None:
        return content
    metadata, parts, closing_index = parsed
    portable = {
        key: value
        for key, value in metadata.items()
        if key in PORTABLE_FRONTMATTER_KEYS
    }
    body = "".join(parts[closing_index + 1 :])
    plan = _when_to_use_plan(metadata)
    if plan is not None:
        kind, text = plan
        if kind == "fold":
            portable["description"] = text
        else:
            body = _insert_when_to_use_section(body, text)
    frontmatter = yaml.safe_dump(portable, sort_keys=False, allow_unicode=True)
    return f"---\n{frontmatter}---\n{body}".encode("utf-8")


def _when_to_use_plan(metadata: dict[str, Any]) -> tuple[str, str] | None:
    """Decide how a skill's `when_to_use` guidance is carried into the bundle.

    Returns `("fold", description)` when the stripped description, one space,
    and the stripped guidance fit `MAX_DESCRIPTION_LENGTH`;
    `("section", guidance)` when they do not; and `None` when there is no
    usable guidance or description (export validation rejects a blank or
    non-string `when_to_use` before rendering).
    """
    guidance = metadata.get(_WHEN_TO_USE)
    description = metadata.get("description")
    if not isinstance(guidance, str) or not guidance.strip():
        return None
    if not isinstance(description, str) or not description.strip():
        return None
    folded = f"{description.strip()} {guidance.strip()}"
    if len(folded) <= MAX_DESCRIPTION_LENGTH:
        return ("fold", folded)
    return ("section", guidance.strip())


def _insert_when_to_use_section(body: str, guidance: str) -> str:
    """Add a `## When to use` section after the body's opening H1 title.

    The H1 counts only when it is the body's first non-blank line, so text
    inside a code block, HTML block, or comment is never mistaken for the
    title; otherwise the section goes at the top of the body. The section
    uses the body's line ending (CRLF or LF), including inside multi-line
    guidance. Existing body text is kept as is; the only other change is a
    line break after an H1 that ends the body without one.
    """
    lines = _LINE_RE.findall(body)
    first = next((index for index, line in enumerate(lines) if line.strip()), None)
    if first is not None and _H1_RE.match(lines[first].rstrip("\r\n")):
        line = lines[first]
        newline = "\r\n" if line.endswith("\r\n") else "\n"
        heading = line if line.endswith("\n") else line + newline
        rest = lines[first + 1 :]
        section = _when_to_use_lines(guidance, newline)
        if rest and rest[0].strip():
            section.append(newline)
        return "".join(lines[:first] + [heading, newline] + section + rest)
    newline = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    section = _when_to_use_lines(guidance, newline)
    return "".join(section + [newline] + lines)


def _when_to_use_lines(guidance: str, newline: str) -> list[str]:
    text = guidance.replace("\r\n", "\n").replace("\n", newline)
    return [
        f"{_WHEN_TO_USE_HEADING}{newline}",
        newline,
        f"{text}{newline}",
    ]


def _is_bundle_path(path: str) -> bool:
    segments = path.split("/")
    if any(_is_ignored_segment(segment) for segment in segments):
        return False
    if len(segments) == 1:
        return path == _SKILL_MD
    return segments[0] in _BUNDLE_DIRS


def _is_ignored_segment(segment: str) -> bool:
    return (
        segment.startswith(".") or segment == "__pycache__" or segment.endswith(".pyc")
    )


def _skipped_entry_notices(source_files: dict[str, bytes]) -> list[ExportNotice]:
    skipped: set[str] = set()
    for path in source_files:
        if _is_bundle_path(path):
            continue
        top_level = path.split("/")[0]
        if top_level in _EXCLUDED_TOP_LEVEL:
            continue
        # Report an ignored file inside a bundle directory by its full path,
        # and any other non-portable top-level entry by its top-level name.
        skipped.add(path if top_level in _BUNDLE_DIRS else top_level)
    ordered = sorted(skipped)
    if not ordered:
        return []
    return [
        ExportNotice(
            code="skipped_entry",
            message="non-portable entries not included in the bundle: "
            + ", ".join(f"`{entry}`" for entry in ordered),
        )
    ]


def _path_errors(bundle: dict[str, bytes]) -> list[str]:
    errors: list[str] = []
    seen: dict[str, str] = {}
    for path in sorted(bundle):
        segments = path.split("/")
        if (
            not path
            or path.startswith("/")
            or "\\" in path
            or "\x00" in path
            or ":" in segments[0]
            or any(segment in {"", ".", ".."} for segment in segments)
        ):
            errors.append(f"unsafe archive path: {path!r}")
            continue
        folded = path.casefold()
        if folded in seen:
            errors.append(
                f"duplicate archive path (case-insensitive): {seen[folded]!r}"
                f" and {path!r}"
            )
        else:
            seen[folded] = path
    return errors


def _limit_errors(bundle: dict[str, bytes]) -> list[str]:
    errors: list[str] = []
    if len(bundle) > MAX_FILE_COUNT:
        errors.append(f"bundle has {len(bundle)} files; limit is {MAX_FILE_COUNT}")
    for path in sorted(bundle):
        if len(bundle[path]) > MAX_FILE_BYTES:
            errors.append(
                f"{path} is {len(bundle[path])} bytes; limit is {MAX_FILE_BYTES}"
            )
    return errors


def _capability_notices(bundle: dict[str, bytes]) -> list[ExportNotice]:
    text = "\n".join(
        content.decode("utf-8", errors="replace")
        for _path, content in sorted(bundle.items())
    )
    checks = (
        (_GIT_PATTERN, "requires_git"),
        (_GH_PATTERN, "requires_gh"),
        (_LRH_CLI_PATTERN, "requires_lrh_cli"),
        (_FENCED_SHELL_PATTERN, "requires_shell"),
    )
    return [
        ExportNotice(
            code=code,
            message=(f"workflow uses {_CAPABILITY_LABELS[code]}, {_LOCAL_TOOLS_LIMIT}"),
        )
        for pattern, code in checks
        if pattern.search(text)
    ]


def _check_output_dir(out_dir: Path, source: installer.SkillSource) -> None:
    if out_dir.is_symlink():
        raise SkillExportError(f"export output must not be a symlink: {out_dir}")
    if out_dir.exists() and not out_dir.is_dir():
        raise SkillExportError(f"export output is not a directory: {out_dir}")
    # Generated bundles must never land inside the canonical source tree.
    # Package sources that are not on the filesystem cannot overlap.
    if isinstance(source.root, Path) and _is_within(out_dir, source.root):
        raise SkillExportError(
            f"export output {out_dir} is inside the skill source {source.root}"
        )


def _is_within(path: Path, root: Path) -> bool:
    """Return True when `path` is `root` or lies inside it.

    Compares file identity (`os.path.samefile`) against every existing
    ancestor rather than comparing path strings, so neither symlinks nor a
    differently-cased path on a case-insensitive filesystem can bypass it.
    """
    resolved = path.resolve()
    for ancestor in (resolved, *resolved.parents):
        if ancestor.exists() and os.path.samefile(ancestor, root):
            return True
    return False


def _publish_archives(archives: list[tuple[Path, bytes]]) -> None:
    """Stage every archive before publishing any of them.

    Destinations are checked first, then every archive is staged to a
    temporary file; only when all staging succeeds are the temporaries
    promoted with `os.replace`. A staging failure removes every temporary
    written so far, so nothing is published. A failure during promotion
    itself (rare: same-directory renames) cannot un-publish archives already
    promoted, but it removes the remaining temporaries and reports the error.
    """
    for path, _archive in archives:
        if path.is_dir() and not path.is_symlink():
            raise SkillExportError(f"export destination is a directory: {path}")
    staged: list[tuple[Path, Path]] = []
    try:
        for path, archive in archives:
            staged.append((_stage_archive(path, archive), path))
    except OSError as err:
        for temporary, _path in staged:
            temporary.unlink(missing_ok=True)
        raise SkillExportError(f"could not write export bundles: {err}") from err
    for index, (temporary, path) in enumerate(staged):
        try:
            os.replace(temporary, path)
        except OSError as err:
            for remaining, _path in staged[index:]:
                remaining.unlink(missing_ok=True)
            raise SkillExportError(
                f"could not publish export bundle {path.name}: {err}"
            ) from err


def _stage_archive(path: Path, archive: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    # Remove any leftover temp entry (including a planted symlink) and create
    # the file exclusively without following links, so the write can never be
    # redirected outside the output directory.
    temporary.unlink(missing_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(archive)
    return temporary
