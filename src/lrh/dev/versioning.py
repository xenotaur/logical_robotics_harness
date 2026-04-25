"""Release workflow helpers for the scripts/version command."""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys

from lrh import version as lrh_version

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


class VersioningError(RuntimeError):
    """Raised when a release-workflow check fails."""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LRH version and release workflow helper.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "tools", help="Print tool versions used by the release workflow"
    )

    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify release prerequisites (clean tree, lint, format, tests)",
    )
    verify_parser.add_argument(
        "tag", nargs="?", default="", help="Optional tag to validate"
    )

    tag_parser = subparsers.add_parser(
        "tag", help="Create release tag after verification"
    )
    tag_parser.add_argument("tag", help="Tag to create")

    push_parser = subparsers.add_parser("push", help="Push release tag to origin")
    push_parser.add_argument("tag", help="Tag to push")

    return parser


def _run_command(
    command: list[str], *, capture_output: bool = False
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=False,
            cwd=REPO_ROOT,
            text=True,
            capture_output=capture_output,
        )
    except FileNotFoundError as error:
        raise VersioningError(f"required command not found: {command[0]}") from error


def _ensure_command_exists(command_name: str) -> None:
    if shutil.which(command_name) is None:
        raise VersioningError(f"required command not found: {command_name}")


def _ensure_valid_tag(tag: str) -> None:
    result = _run_command(["git", "check-ref-format", f"refs/tags/{tag}"])
    if result.returncode != 0:
        raise VersioningError(f"invalid tag name: {tag}")


def _ensure_clean_working_tree() -> None:
    _ensure_command_exists("git")
    status_result = _run_command(["git", "status", "--porcelain"], capture_output=True)
    if status_result.returncode != 0:
        raise VersioningError("failed to inspect git working tree")
    if status_result.stdout.strip():
        raise VersioningError("working tree must be clean before release verification")


def _run_verification_commands() -> None:
    checks = [
        ["scripts/lint"],
        ["scripts/format", "--check"],
        ["scripts/test"],
    ]
    for command in checks:
        print(f"Running: {' '.join(command)}")
        completed = _run_command(command)
        if completed.returncode != 0:
            raise VersioningError(f"verification command failed: {' '.join(command)}")


def _resolve_head_commit() -> str:
    result = _run_command(["git", "rev-parse", "HEAD"], capture_output=True)
    if result.returncode != 0:
        raise VersioningError("failed to resolve HEAD commit")
    return result.stdout.strip()


def _resolve_local_tag_commit(tag: str) -> str | None:
    result = _run_command(
        ["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"],
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _resolve_remote_tag_commit(tag: str) -> str | None:
    dereferenced_ref = f"refs/tags/{tag}^{{}}"
    result = _run_command(
        ["git", "ls-remote", "--tags", "origin", dereferenced_ref],
        capture_output=True,
    )
    if result.returncode != 0:
        raise VersioningError("failed to query remote tags from origin")
    output = result.stdout.strip()
    if not output:
        direct_tag_result = _run_command(
            ["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"],
            capture_output=True,
        )
        if direct_tag_result.returncode != 0:
            raise VersioningError("failed to query remote tags from origin")
        direct_output = direct_tag_result.stdout.strip()
        if not direct_output:
            return None
        return direct_output.split()[0]
    return output.split()[0]


def print_lrh_version() -> None:
    """Print installed LRH version."""
    print(lrh_version.format_cli_version())


def _print_tool_version(
    label: str,
    command: list[str],
    *,
    optional: bool,
) -> None:
    print(label)
    try:
        completed = _run_command(command)
    except VersioningError as error:
        if optional:
            print(f"not installed ({error})")
            print()
            return
        raise

    if completed.returncode != 0:
        message = f"version command failed for {label}: {' '.join(command)}"
        if optional:
            print(message)
            print()
            return
        raise VersioningError(message)

    print()


def print_tool_versions() -> None:
    """Print versions for release workflow tooling."""
    print("LRH package metadata")
    print(lrh_version.format_cli_version())
    print()

    for label, command, optional in (
        ("LRH CLI", ["lrh", "version"], True),
        ("Python", ["python", "--version"], False),
        ("Ruff", ["ruff", "--version"], False),
        ("Black", ["black", "--version"], False),
        ("Pylint", ["pylint", "--version"], True),
        ("Pyright", ["pyright", "--version"], True),
        ("Conda", ["conda", "--version"], True),
        ("pip", ["pip", "--version"], False),
    ):
        _print_tool_version(label, command, optional=optional)


def verify_release(tag: str = "") -> None:
    """Verify release preconditions, optionally including tag validation."""
    if tag:
        _ensure_valid_tag(tag)
    _ensure_clean_working_tree()
    _run_verification_commands()


def create_tag(tag: str) -> None:
    """Create a release tag, safely and idempotently."""
    _ensure_valid_tag(tag)
    head_commit = _resolve_head_commit()
    existing_commit = _resolve_local_tag_commit(tag)

    if existing_commit is not None:
        if existing_commit == head_commit:
            print(f"Tag {tag} already exists at HEAD; nothing to do.")
            return
        error_message = (
            f"tag {tag} already exists at {existing_commit}, "
            f"not current HEAD {head_commit}"
        )
        raise VersioningError(error_message)

    verify_release(tag)
    create_result = _run_command(["git", "tag", tag])
    if create_result.returncode != 0:
        raise VersioningError(f"failed to create tag: {tag}")
    print(f"Created tag {tag} at {head_commit}.")


def push_tag(tag: str) -> None:
    """Push a release tag to origin, safely and idempotently."""
    _ensure_valid_tag(tag)

    local_commit = _resolve_local_tag_commit(tag)
    if local_commit is None:
        raise VersioningError(f"local tag not found: {tag}")

    remote_commit = _resolve_remote_tag_commit(tag)
    if remote_commit is not None:
        if remote_commit == local_commit:
            print(
                f"Tag {tag} already exists on origin at {local_commit}; nothing to do."
            )
            return
        error_message = (
            f"remote tag {tag} points to {remote_commit}, "
            f"local tag points to {local_commit}"
        )
        raise VersioningError(error_message)

    push_result = _run_command(["git", "push", "origin", f"refs/tags/{tag}"])
    if push_result.returncode != 0:
        raise VersioningError(f"failed to push tag: {tag}")
    print(f"Pushed tag {tag} to origin.")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command is None:
            print_lrh_version()
        elif args.command == "tools":
            print_tool_versions()
        elif args.command == "verify":
            verify_release(args.tag)
        elif args.command == "tag":
            create_tag(args.tag)
        elif args.command == "push":
            push_tag(args.tag)
        else:
            parser.error(f"unsupported command: {args.command}")
    except VersioningError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
