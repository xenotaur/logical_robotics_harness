"""Small wrapper around the gh CLI."""

from __future__ import annotations

import json
import subprocess


def run_gh_json(argv: list[str]) -> object:
    """Run gh and decode JSON, raising clean errors."""
    try:
        result = subprocess.run(
            ["gh", *argv],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("gh CLI not found") from exc
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "gh command failed")
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
