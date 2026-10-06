"""Small wrapper around the gh CLI."""

from __future__ import annotations

import json
import pathlib
import re
import subprocess


def run_gh_json(argv: list[str], *, cwd: str | pathlib.Path | None = None) -> object:
    """Run gh and decode JSON, raising clean errors.

    ``cwd`` binds the invocation to a specific working directory -- gh
    infers the target repository from the current directory, so a caller
    operating on a project root other than the process's own cwd must
    pass it explicitly or risk querying (and mutating refs in) the wrong
    repository.
    """
    if cwd is not None and (not str(cwd) or not pathlib.Path(cwd).is_dir()):
        raise RuntimeError(f"invalid project root: {cwd}")

    try:
        result = subprocess.run(
            ["gh", *argv],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        if cwd is not None and (not str(cwd) or not pathlib.Path(cwd).is_dir()):
            raise RuntimeError(f"invalid project root: {cwd}") from exc
        raise RuntimeError("gh CLI not found") from exc
    if result.returncode != 0:
        stderr = _sanitize_stderr(result.stderr)
        category = _classify_failure(stderr)
        detail = stderr or "no diagnostic output"
        raise RuntimeError(f"gh command failed ({category}): {detail}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("gh returned invalid JSON") from exc
    if isinstance(payload, dict) and payload.get("errors"):
        errors = payload.get("errors")
        first = errors[0] if isinstance(errors, list) and errors else errors
        if isinstance(first, dict) and "message" in first:
            raise RuntimeError(str(first["message"]))
        raise RuntimeError("GitHub GraphQL query returned errors")
    return payload


def _sanitize_stderr(stderr: str) -> str:
    """Keep command diagnostics short and remove token-shaped values."""
    single_line = " ".join(stderr.split())
    redacted = re.sub(
        r"(?i)(authorization:\s*\S+\s+)[^\s]+",
        r"\1[redacted]",
        single_line,
    )
    redacted = re.sub(
        r"(?i)(https?://)([^/\s:@]+):([^@\s/]+)@",
        r"\1[redacted]@",
        redacted,
    )
    redacted = re.sub(
        r"\b(?:gh[pousr]|github_pat)_[A-Za-z0-9_]+\b",
        "[redacted-token]",
        redacted,
    )
    return redacted[:400]


def _classify_failure(stderr: str) -> str:
    """Classify common gh failures without treating them as auth failures."""
    lowered = stderr.lower()
    if any(
        marker in lowered
        for marker in (
            "could not resolve host",
            "no such host",
            "dial tcp",
            "network is unreachable",
            "connection refused",
            "connection reset",
            "timed out",
            "timeout",
            "error connecting to api.github.com",
        )
    ):
        return "network"
    if any(
        marker in lowered
        for marker in ("authentication", "not logged in", "bad credentials", "oauth")
    ):
        return "authentication"
    if any(
        marker in lowered
        for marker in (
            "graphql",
            "api.github.com",
            "github api",
            "api rate limit",
            "rate limit exceeded",
            "internal server error",
            "service unavailable",
            "bad gateway",
            "http 4",
            "http 5",
            "status code 4",
            "status code 5",
        )
    ):
        return "api"
    return "command"
