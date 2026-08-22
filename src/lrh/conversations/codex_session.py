"""Codex app task/thread identity helpers."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from collections.abc import Mapping, Sequence

CODEX_THREAD_ID_ENV = "CODEX_THREAD_ID"
CODEX_SESSION_TRANSCRIPT_PREFIX = "codex-app:"


class CodexSessionIdentityError(ValueError):
    """Raised when a Codex task/thread identity cannot be resolved."""


@dataclasses.dataclass(frozen=True)
class CodexSessionIdentity:
    """Resolved Codex task/thread identity for export and closeout pointers."""

    thread_id: str

    @property
    def session_transcript(self) -> str:
        """Return the LRH execution-record session pointer."""

        return f"{CODEX_SESSION_TRANSCRIPT_PREFIX}{self.thread_id}"


def resolve_codex_session_identity(
    thread_id: str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> CodexSessionIdentity:
    """Resolve an explicit Codex thread id or fall back to CODEX_THREAD_ID."""

    raw_thread_id = (
        thread_id
        if thread_id is not None
        else (os.environ if environ is None else environ).get(CODEX_THREAD_ID_ENV)
    )
    normalized = _normalized_optional_thread_id(raw_thread_id)
    if normalized is None:
        raise CodexSessionIdentityError(
            f"--thread-id or {CODEX_THREAD_ID_ENV} is required"
        )
    return CodexSessionIdentity(thread_id=normalized)


def run_current_codex_thread_id_cli(
    argv: Sequence[str] | None = None,
    *,
    prog: str,
) -> int:
    """Run the metadata-only current Codex thread id CLI."""

    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Report the current Codex task/thread id and LRH "
            "session_transcript pointer without exporting transcript content."
        ),
    )
    parser.add_argument(
        "--thread-id",
        default=None,
        help="Codex thread id to report (default: CODEX_THREAD_ID)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--field",
        choices=("all", "thread-id", "session-transcript"),
        default="all",
        help="single-field text output for scripts (default: all)",
    )
    args = parser.parse_args(argv)
    try:
        identity = resolve_codex_session_identity(args.thread_id)
    except CodexSessionIdentityError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(
            json.dumps(
                {
                    "thread_id": identity.thread_id,
                    "session_transcript": identity.session_transcript,
                    "exported": False,
                },
                sort_keys=True,
            )
        )
        return 0

    if args.field == "thread-id":
        print(identity.thread_id)
    elif args.field == "session-transcript":
        print(identity.session_transcript)
    else:
        print(f"Thread ID: {identity.thread_id}")
        print(f"Session transcript: {identity.session_transcript}")
        print("Exported: no")
    return 0


def _normalized_optional_thread_id(raw_thread_id: str | None) -> str | None:
    if raw_thread_id is None:
        return None
    normalized = raw_thread_id.strip()
    return normalized or None
