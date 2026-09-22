"""Claude Code current-session identity helpers (metadata only)."""

from __future__ import annotations

import argparse
import dataclasses
import glob as glob_module
import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

CLAUDE_SESSION_ID_ENV = "CLAUDE_CODE_SESSION_ID"
CLAUDE_HOST_SESSION_ID_ENV = "CLAUDE_CODE_HOST_SESSION_ID"
CLAUDE_SESSION_TRANSCRIPT_PREFIX = "claude-app:"
_HOST_ID_LOCAL_PREFIX = "local_"


class ClaudeSessionIdentityError(ValueError):
    """Raised when the current Claude Code session cannot be resolved."""


@dataclasses.dataclass(frozen=True)
class ClaudeSessionIdentity:
    """Resolved current Claude Code session identity, metadata only."""

    session_id: str
    transcript_path: Path
    host_session_id: str | None = None

    @property
    def session_transcript(self) -> str | None:
        """Return the LRH execution-record session pointer, if resolvable.

        ``None`` when ``CLAUDE_CODE_HOST_SESSION_ID`` was not set -- the
        session id and transcript path can still be resolved from
        ``CLAUDE_CODE_SESSION_ID`` alone, so an unset host id does not fail
        resolution, only leaves this pointer unavailable.
        """

        if self.host_session_id is None:
            return None
        return f"{CLAUDE_SESSION_TRANSCRIPT_PREFIX}{self.host_session_id}"


def resolve_current_claude_session_identity(
    *,
    environ: Mapping[str, str] | None = None,
    app_data_dir: Path | None = None,
) -> ClaudeSessionIdentity:
    """Resolve the current Claude Code session's id, host pointer, and
    transcript path, without reading or returning transcript content.

    Reads ``CLAUDE_CODE_SESSION_ID`` (required) and
    ``CLAUDE_CODE_HOST_SESSION_ID`` (optional) from the environment. The
    transcript path is found by globbing
    ``<app-data-dir>/projects/*/<session-id>.jsonl``, honouring
    ``CLAUDE_CONFIG_DIR`` the same way ``export-claude-session`` does when
    ``app_data_dir`` is not explicitly supplied.
    """

    env = os.environ if environ is None else environ
    session_id = _normalized_session_id(env.get(CLAUDE_SESSION_ID_ENV))
    if session_id is None:
        raise ClaudeSessionIdentityError(
            f"{CLAUDE_SESSION_ID_ENV} is not set; the current Claude Code "
            "session cannot be resolved"
        )

    resolved_app_data_dir = (
        Path(default_app_data_dir()) if app_data_dir is None else app_data_dir
    )
    transcript_path = resolve_transcript_path_by_session_id(
        session_id, resolved_app_data_dir
    )
    host_session_id = _normalized_host_id(env.get(CLAUDE_HOST_SESSION_ID_ENV))

    return ClaudeSessionIdentity(
        session_id=session_id,
        transcript_path=transcript_path,
        host_session_id=host_session_id,
    )


def resolve_transcript_path_by_session_id(session_id: str, app_data_dir: Path) -> Path:
    """Glob ``<app-data-dir>/projects/*/<session-id>.jsonl`` for one match.

    Zero or more than one match is an error -- this never guesses, and
    never falls back to any other discovery mode.
    """

    app_dir = app_data_dir.expanduser()
    projects_dir = app_dir / "projects"
    matches = sorted(projects_dir.glob(f"*/{glob_module.escape(session_id)}.jsonl"))
    if not matches:
        raise ClaudeSessionIdentityError(
            f"no transcript file found for session id '{session_id}' under "
            f"{projects_dir}"
        )
    if len(matches) > 1:
        raise ClaudeSessionIdentityError(
            f"multiple transcript files found for session id '{session_id}' "
            f"under {projects_dir}; disambiguate with an explicit transcript "
            "path: " + ", ".join(str(match) for match in matches)
        )
    return matches[0]


def default_app_data_dir() -> str:
    """Return the default Claude Code application data directory.

    Honors ``CLAUDE_CONFIG_DIR`` the same way ``export-claude-session``
    does; falls back to ``~/.claude`` when unset.
    """

    return os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude"


def run_current_claude_session_id_cli(
    argv: Sequence[str] | None = None,
    *,
    prog: str,
) -> int:
    """Run the metadata-only current Claude Code session id CLI."""

    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Report the current Claude Code session id, host pointer, and "
            "resolved transcript path without reading transcript content."
        ),
    )
    parser.add_argument(
        "--app-data-dir",
        default=default_app_data_dir(),
        help=(
            "path to Claude Code's application data directory "
            "(default: $CLAUDE_CONFIG_DIR, or ~/.claude if unset)"
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--field",
        choices=("all", "session-id", "session-transcript", "transcript-path"),
        default="all",
        help="single-field text output for scripts (default: all)",
    )
    args = parser.parse_args(argv)

    try:
        identity = resolve_current_claude_session_identity(
            app_data_dir=Path(args.app_data_dir)
        )
    except ClaudeSessionIdentityError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(
            json.dumps(
                {
                    "session_id": identity.session_id,
                    "session_transcript": identity.session_transcript,
                    "transcript_path": str(identity.transcript_path),
                    "exported": False,
                },
                sort_keys=True,
            )
        )
        return 0

    if args.field == "session-id":
        print(identity.session_id)
    elif args.field == "session-transcript":
        print(identity.session_transcript or "unknown")
    elif args.field == "transcript-path":
        print(str(identity.transcript_path))
    else:
        print(f"Session ID: {identity.session_id}")
        print(f"Session transcript: {identity.session_transcript or 'unknown'}")
        print(f"Transcript path: {identity.transcript_path}")
        print("Exported: no")
    return 0


def _normalized_session_id(raw_session_id: str | None) -> str | None:
    if raw_session_id is None:
        return None
    normalized = raw_session_id.strip()
    if not normalized:
        return None
    if any(character.isspace() for character in normalized):
        raise ClaudeSessionIdentityError(
            f"{CLAUDE_SESSION_ID_ENV} must not contain whitespace: "
            f"{raw_session_id!r}"
        )
    if "/" in normalized or "\\" in normalized:
        raise ClaudeSessionIdentityError(
            f"invalid Claude Code session id: {raw_session_id!r}"
        )
    return normalized


def _normalized_host_id(raw_host_id: str | None) -> str | None:
    if raw_host_id is None:
        return None
    normalized = raw_host_id.strip()
    if not normalized:
        return None
    if normalized.startswith(_HOST_ID_LOCAL_PREFIX):
        normalized = normalized[len(_HOST_ID_LOCAL_PREFIX) :]
    return normalized
