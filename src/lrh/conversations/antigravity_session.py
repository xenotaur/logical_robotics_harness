"""Antigravity conversation identity helpers (metadata only)."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path

ANTIGRAVITY_CONVERSATION_ID_ENV = "ANTIGRAVITY_CONVERSATION_ID"
ANTIGRAVITY_APP_DATA_DIR_ENV = "ANTIGRAVITY_APP_DATA_DIR"
ANTIGRAVITY_SESSION_TRANSCRIPT_PREFIX = "antigravity-app:"
DEFAULT_APP_DATA_DIR = "~/.gemini/antigravity"


class AntigravitySessionIdentityError(ValueError):
    """Raised when an Antigravity conversation identity cannot be resolved."""


@dataclasses.dataclass(frozen=True)
class AntigravitySessionIdentity:
    """Resolved Antigravity conversation identity for export and closeout pointers."""

    conversation_id: str
    transcript_path: Path | None = None
    is_latest: bool = False

    @property
    def session_transcript(self) -> str:
        """Return the LRH execution-record session pointer."""

        return f"{ANTIGRAVITY_SESSION_TRANSCRIPT_PREFIX}{self.conversation_id}"


def _is_valid_uuid(val: str) -> bool:
    try:
        parsed = uuid.UUID(val)
        return str(parsed).lower() == val.lower()
    except (ValueError, AttributeError):
        return False


def _derive_conversation_id_from_path(path: Path, brain_dir: Path | None = None) -> str:
    if brain_dir is not None:
        try:
            rel = path.resolve().relative_to(brain_dir.resolve())
            if rel.parts:
                return rel.parts[0]
        except ValueError:
            pass
    parts = path.parts
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "brain" and i + 1 < len(parts):
            return parts[i + 1]
    return ""


def _find_transcript_path_for_id(
    conversation_id: str, app_data_dir: Path
) -> Path | None:
    brain_dir = app_data_dir / "brain"
    candidate = (
        brain_dir / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"
    )
    if candidate.exists() and candidate.is_file():
        return candidate
    candidate_full = (
        brain_dir
        / conversation_id
        / ".system_generated"
        / "logs"
        / "transcript_full.jsonl"
    )
    if candidate_full.exists() and candidate_full.is_file():
        return candidate_full
    return None


def _discover_latest_transcript(app_data_dir: Path) -> tuple[Path, str]:
    brain_dir = app_data_dir / "brain"
    if not brain_dir.exists():
        raise AntigravitySessionIdentityError(
            f"Antigravity brain directory does not exist: {brain_dir}"
        )
    matches = list(brain_dir.glob("*/.system_generated/logs/transcript.jsonl")) + list(
        brain_dir.glob("*/.system_generated/logs/transcript_full.jsonl")
    )
    matches = [p for p in matches if not p.is_symlink() and p.is_file()]
    if not matches:
        raise AntigravitySessionIdentityError(
            f"no Antigravity transcript files found in {brain_dir}"
        )
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    best = matches[0]
    cid = _derive_conversation_id_from_path(best, brain_dir)
    if not _is_valid_uuid(cid):
        raise AntigravitySessionIdentityError(
            f"discovered transcript directory '{cid}' is not a valid conversation UUID"
        )
    return best, str(uuid.UUID(cid)).lower()


def resolve_antigravity_session_identity(
    conversation_id: str | None = None,
    *,
    latest: bool = False,
    app_data_dir: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> AntigravitySessionIdentity:
    """Resolve the current Antigravity conversation's identity, pointer, and
    transcript path, without reading or returning transcript content.

    Hierarchy:
    1. Explicit conversation_id (validated as UUID)
    2. ANTIGRAVITY_CONVERSATION_ID env var (validated as UUID, hard error if malformed)
    3. If latest=True and ANTIGRAVITY_CONVERSATION_ID is absent,
       heuristic discovery under brain/
    4. Otherwise, raises AntigravitySessionIdentityError
    """

    if conversation_id is not None and latest:
        raise AntigravitySessionIdentityError(
            "cannot specify both conversation_id and latest=True"
        )

    env = os.environ if environ is None else environ

    if app_data_dir is not None:
        resolved_app_dir = Path(app_data_dir).expanduser()
    else:
        env_app_dir = env.get(ANTIGRAVITY_APP_DATA_DIR_ENV)
        resolved_app_dir = Path(env_app_dir or DEFAULT_APP_DATA_DIR).expanduser()

    if conversation_id is not None:
        trimmed = conversation_id.strip()
        if not trimmed:
            raise AntigravitySessionIdentityError(
                "conversation ID must not be empty or whitespace-only"
            )
        if not _is_valid_uuid(trimmed):
            raise AntigravitySessionIdentityError(
                f"malformed conversation ID '{conversation_id}'; "
                "expected 36-character UUID"
            )
        normalized_id = str(uuid.UUID(trimmed)).lower()
        t_path = _find_transcript_path_for_id(normalized_id, resolved_app_dir)
        return AntigravitySessionIdentity(
            conversation_id=normalized_id,
            transcript_path=t_path,
            is_latest=False,
        )

    raw_env_id = env.get(ANTIGRAVITY_CONVERSATION_ID_ENV)
    if raw_env_id is not None:
        trimmed = raw_env_id.strip()
        if not trimmed or not _is_valid_uuid(trimmed):
            raise AntigravitySessionIdentityError(
                f"malformed {ANTIGRAVITY_CONVERSATION_ID_ENV} '{raw_env_id}'; "
                "expected 36-character UUID"
            )
        normalized_id = str(uuid.UUID(trimmed)).lower()
        t_path = _find_transcript_path_for_id(normalized_id, resolved_app_dir)
        return AntigravitySessionIdentity(
            conversation_id=normalized_id,
            transcript_path=t_path,
            is_latest=False,
        )

    if latest:
        t_path, norm_id = _discover_latest_transcript(resolved_app_dir)
        return AntigravitySessionIdentity(
            conversation_id=norm_id,
            transcript_path=t_path,
            is_latest=True,
        )

    raise AntigravitySessionIdentityError(
        f"{ANTIGRAVITY_CONVERSATION_ID_ENV} is not set; "
        "no active Antigravity conversation environment detected. "
        "Provide --conversation-id or --latest to resolve."
    )


def run_current_antigravity_conversation_id_cli(
    argv: Sequence[str] | None = None,
    *,
    prog: str = "lrh conversation current-antigravity-conversation-id",
) -> int:
    """Run the metadata-only current Antigravity conversation id CLI."""

    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Report the current Antigravity conversation ID and LRH "
            "session_transcript pointer without exporting or reading "
            "transcript content."
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--conversation-id",
        default=None,
        help="explicit Antigravity conversation ID to report",
    )
    group.add_argument(
        "--latest",
        action="store_true",
        help="discover the most recently modified transcript file under app-data-dir",
    )
    parser.add_argument(
        "--app-data-dir",
        default=None,
        help=(
            "path to Antigravity application data directory "
            f"(default: ${ANTIGRAVITY_APP_DATA_DIR_ENV} or {DEFAULT_APP_DATA_DIR})"
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
        choices=("all", "conversation-id", "session-transcript", "transcript-path"),
        default="all",
        help="single-field text output for scripts (default: all)",
    )

    args = parser.parse_args(argv)

    try:
        identity = resolve_antigravity_session_identity(
            conversation_id=args.conversation_id,
            latest=args.latest,
            app_data_dir=args.app_data_dir,
        )
    except AntigravitySessionIdentityError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    if identity.is_latest:
        print(
            "warning: resolved Antigravity conversation ID via filesystem "
            "recency fallback (--latest)",
            file=sys.stderr,
        )

    if args.format == "json":
        payload = {
            "conversation_id": identity.conversation_id,
            "session_transcript": identity.session_transcript,
            "transcript_path": (
                str(identity.transcript_path) if identity.transcript_path else None
            ),
            "exported": False,
        }
        print(json.dumps(payload, sort_keys=True))
        return 0

    if args.field == "conversation-id":
        print(identity.conversation_id)
    elif args.field == "session-transcript":
        print(identity.session_transcript)
    elif args.field == "transcript-path":
        print(str(identity.transcript_path or ""))
    else:
        print(f"Conversation ID: {identity.conversation_id}")
        print(f"Session transcript: {identity.session_transcript}")
        t_display = (
            str(identity.transcript_path) if identity.transcript_path else "none"
        )
        print(f"Transcript path: {t_display}")
        print("Exported: no")
    return 0
