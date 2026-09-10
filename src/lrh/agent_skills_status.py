"""Single-read status view over `project/agent_skills.yaml`.

Backs `lrh agent-skills status` / the `/lrh-config-skills` skill: reports
whether the config file exists and the effective,
CLI-over-config-over-default resolved value of each field -- reusing
`lrh.skills.installer`'s existing `load_agent_skills_config`/
`resolve_agent_skills_install_plan` functions rather than re-implementing
that precedence logic (`WI-SKILLS-LRH-CONFIG-SKILLS`).

`sources`, `targets`, and `scope` all have documented conventional
defaults (`docs/reference/schemas/agent-skills-config.md`) and are fully
exposed by the two reused functions above. `install.overwrite` has no
documented default, and neither `AgentSkillsConfig` nor
`AgentSkillsInstallPlan` carries a field for it --
`installer._validate_config_install_policy` validates and discards the
value rather than exposing it. This module does not extend
`installer.py`'s data model to add one (that would touch `lrh skills
install`'s own internal loading logic, out of this WI's scope); it reads
the raw YAML value directly instead, reporting `None` ("not set") when
the file or key is absent.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib

import yaml

from lrh.skills import installer

#: Re-exported for callers that only need the error type, not the whole
#: `installer` module.
AgentSkillsStatusError = installer.SkillSourceError


@dataclasses.dataclass(frozen=True)
class FieldStatus:
    #: The effective, resolved value (already CLI-over-config-over-default
    #: applied at the "no CLI override" case -- see `compute_status`).
    value: str
    #: True iff `project/agent_skills.yaml` supplied this value; False
    #: means the conventional default was used.
    from_config: bool


@dataclasses.dataclass(frozen=True)
class AgentSkillsStatus:
    profile_exists: bool
    sources: FieldStatus
    targets: FieldStatus
    scope: FieldStatus
    #: Raw `install.overwrite` value from the parsed config, or None if
    #: the file, the `install` table, or the `overwrite` key is absent.
    #: No conventional default exists for this field -- unlike the three
    #: above, `None` is not "resolved to a default," it is "not set."
    install_overwrite: bool | str | None


def _read_raw_overwrite(project_root: pathlib.Path) -> bool | str | None:
    path = project_root / "project" / "agent_skills.yaml"
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        raise AgentSkillsStatusError(f"could not read {path}: {err}") from err
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        return None
    install = data.get("install")
    if not isinstance(install, dict):
        return None
    return install.get("overwrite")


def compute_status(project_root: pathlib.Path) -> AgentSkillsStatus:
    """Compute the full status view in one read.

    Raises `AgentSkillsStatusError` (an alias of
    `installer.SkillSourceError`) for a malformed `project/agent_skills.yaml`
    -- the same error `load_agent_skills_config`/
    `resolve_agent_skills_install_plan` already raise, not a new error
    type, since this module computes nothing those functions don't
    already validate. Also normalizes `load_agent_skills_config`'s own
    unwrapped `OSError`/`UnicodeDecodeError` (an unreadable or non-UTF-8
    profile) into the same error type, since neither function catches
    those -- only `yaml.YAMLError` -- and an uncaught traceback would
    otherwise reach the CLI instead of the documented `error: ...` / exit
    2 contract.
    """
    try:
        config = installer.load_agent_skills_config(project_root)
        plan = installer.resolve_agent_skills_install_plan(project_root=project_root)
    except (OSError, UnicodeDecodeError) as err:
        raise AgentSkillsStatusError(
            f"could not read agent skills config under {project_root}: {err}"
        ) from err

    sources = FieldStatus(
        value=str(plan.source),
        from_config=bool(config is not None and config.source is not None),
    )
    targets = FieldStatus(
        value=plan.target.value,
        from_config=bool(config is not None and config.target is not None),
    )
    scope = FieldStatus(
        value="project" if plan.local else "user",
        from_config=bool(config is not None and config.local is not None),
    )

    return AgentSkillsStatus(
        profile_exists=config is not None,
        sources=sources,
        targets=targets,
        scope=scope,
        install_overwrite=_read_raw_overwrite(project_root),
    )


def format_json(status: AgentSkillsStatus) -> str:
    return json.dumps(
        {
            "profile_exists": status.profile_exists,
            "sources": {
                "value": status.sources.value,
                "from_config": status.sources.from_config,
            },
            "targets": {
                "value": status.targets.value,
                "from_config": status.targets.from_config,
            },
            "scope": {
                "value": status.scope.value,
                "from_config": status.scope.from_config,
            },
            "install_overwrite": status.install_overwrite,
        },
        indent=2,
    )


def format_text(status: AgentSkillsStatus) -> str:
    lines: list[str] = []
    lines.append(f"project/agent_skills.yaml exists: {status.profile_exists}")
    lines.append("Editable fields (effective value, provenance):")
    for name, field in (
        ("sources", status.sources),
        ("targets", status.targets),
        ("scope", status.scope),
    ):
        provenance = "from-config" if field.from_config else "conventional-default"
        lines.append(f"  {name}: {field.value!r} ({provenance})")
    lines.append("Read-only field (no conventional default; raw configured value):")
    lines.append(f"  install.overwrite: {status.install_overwrite!r}")
    return "\n".join(lines)
