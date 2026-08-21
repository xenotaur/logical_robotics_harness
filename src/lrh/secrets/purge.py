"""Mirror-clone-scoped secrets purge for `lrh secrets purge`.

Wraps `git-filter-repo` (https://github.com/newren/git-filter-repo), the
tool GitHub's own docs recommend for removing sensitive data from
history: https://docs.github.com/en/authentication/keeping-your-account-
and-data-secure/removing-sensitive-data-from-a-repository

`--apply`:
  1. mirror-clones `--source` into `--mirror-dir` (or a fresh temp dir) --
     never touches `--project-root`'s own working tree,
  2. runs `git-filter-repo --replace-text` against the mirror, scoped to
     exactly the refs listed in `--refs-file`,
  3. re-scans the rewritten mirror to confirm every listed secret is gone
     (literal-string match, see below),
  4. on a clean result, prints -- but never runs -- the `git push --force`
     command for each ref, together with the manual-step reminders this
     tooling has always carried (notify collaborators/branch-owners
     before pushing; file a host-support request to purge cached
     views/forks if the repo was ever public). A dirty verification is a
     hard failure: no push command is printed.

`--dry-run` validates all inputs (refs file, replacements file, the
`git-filter-repo` binary) without cloning or rewriting anything.

**`--refs-file` is mandatory.** Purging without an explicit ref scope is
refused outright -- there is no "purge everything" default.

**Runtime-enforced reviewed-replacements gate.** `--replacements` must be
`lrh secrets review --apply`'s output (`replacements.reviewed.txt`), not
`lrh secrets scan`'s unreviewed draft (`replacements.txt`) -- checked at
runtime, not just by filename convention: the file's first non-empty
line must be exactly the marker `# lrh-secrets-reviewed v1` (see
`lrh.secrets.review.MARKER_LINE`). A file missing that marker is refused
before any clone happens. The marker is stripped before the remaining
`secret==>placeholder` lines are ever passed to `git-filter-repo`.

**Literal-string verification.** Post-rewrite verification uses
`git log --all -S <secret>` without `--pickaxe-regex` -- that flag makes
git treat `<secret>` as an extended POSIX regex, which can produce a
false "clean" result (or an invalid-regex abort) for a secret containing
regex metacharacters (e.g. `ab+c`). Plain `-S<string>` is already a
literal pickaxe search.

**No `--push` flag exists, and none will be added.** This is a hard
invariant: there is no code path in this module that invokes `git push`.
The push command is always printed for a human to run manually.

Requires the `git-filter-repo` binary on PATH:
https://github.com/newren/git-filter-repo#how-do-i-install-it
"""

from __future__ import annotations

import dataclasses
import pathlib
import shutil
import subprocess
import sys
import tempfile

from lrh.secrets.review import MARKER_LINE


class PurgeInputError(Exception):
    """Raised for a missing/malformed --refs-file, --replacements, or --source."""


def check_filter_repo_available() -> None:
    if shutil.which("git-filter-repo") is None:
        print(
            "FAIL: `git-filter-repo` not found on PATH. Install it first, e.g.:\n"
            "  pip install git-filter-repo\n"
            "See https://github.com/newren/git-filter-repo#how-do-i-install-it",
            file=sys.stderr,
        )
        raise SystemExit(1)


def load_refs(refs_file: pathlib.Path) -> list[str]:
    if not refs_file.exists():
        raise PurgeInputError(f"{refs_file} not found -- --refs-file is mandatory")
    refs = [
        line.strip()
        for line in refs_file.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not refs:
        raise PurgeInputError(
            f"{refs_file} contains no refs -- purge refuses to run unscoped"
        )
    return refs


def load_stripped_replacements(replacements_path: pathlib.Path) -> list[str]:
    """Validate the reviewed-replacements marker, then return the remaining
    `secret==>placeholder` lines with the marker itself stripped off. Blank
    and comment (`#`) lines after the marker are dropped -- they are not
    secrets and must never reach git-filter-repo or the literal-string
    verification step as if they were one."""
    if not replacements_path.exists():
        raise PurgeInputError(f"{replacements_path} not found")
    lines = replacements_path.read_text().splitlines()
    non_empty = [line for line in lines if line.strip()]
    if not non_empty or non_empty[0] != MARKER_LINE:
        raise PurgeInputError(
            f"{replacements_path} does not look like review --apply's output "
            "-- run `lrh secrets review --apply` first"
        )
    marker_index = lines.index(non_empty[0])
    entries = [
        line
        for line in lines[marker_index + 1 :]
        if line.strip() and not line.strip().startswith("#")
    ]
    for entry in entries:
        if "==>" not in entry:
            raise PurgeInputError(
                f"{replacements_path}: malformed entry {entry!r} -- expected "
                "<secret>==><placeholder>"
            )
    return entries


def default_source(project_root: pathlib.Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as err:
        raise PurgeInputError(
            f"could not resolve --source: no origin remote at {project_root} "
            "-- pass --source explicitly"
        ) from err
    return result.stdout.strip()


def resolve_local_source(source: str) -> str:
    """A relative local path (e.g. `.`) resolves fine for the mirror clone
    itself (relative to this process's cwd), but the printed push command
    runs as `git -C <mirror_dir> push --force <source> <ref>` -- a relative
    `source` there resolves against `mirror_dir`, not this process's cwd,
    silently pushing back into the mirror. A URL (or an ssh-style
    `user@host:path`) is left untouched; only an existing local filesystem
    path is resolved to absolute."""
    path = pathlib.Path(source)
    if path.exists():
        return str(path.resolve())
    return source


def mirror_clone(source: str, mirror_dir: pathlib.Path) -> None:
    subprocess.run(
        ["git", "clone", "--mirror", source, str(mirror_dir)],
        check=True,
    )


def run_filter_repo(
    mirror_dir: pathlib.Path, stripped_replacements: list[str], refs: list[str]
) -> None:
    with tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False
    ) as replacements_tmp:
        replacements_tmp.write("\n".join(stripped_replacements) + "\n")
        replacements_tmp_path = pathlib.Path(replacements_tmp.name)
    try:
        cmd = [
            "git-filter-repo",
            "--replace-text",
            str(replacements_tmp_path),
            "--force",
            "--refs",
            *refs,
        ]
        subprocess.run(cmd, cwd=str(mirror_dir), check=True)
    finally:
        replacements_tmp_path.unlink(missing_ok=True)


def secret_still_present(mirror_dir: pathlib.Path, secret: str) -> bool:
    """Literal-string check -- deliberately no --pickaxe-regex (see module
    docstring)."""
    result = subprocess.run(
        ["git", "log", "--all", f"-S{secret}", "--oneline"],
        cwd=str(mirror_dir),
        check=True,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def verify_clean(mirror_dir: pathlib.Path, secrets: list[str]) -> list[str]:
    """Return the subset of `secrets` still found in the rewritten mirror."""
    return [secret for secret in secrets if secret_still_present(mirror_dir, secret)]


def secrets_from_replacements(stripped_replacements: list[str]) -> list[str]:
    secrets = []
    for line in stripped_replacements:
        secret, _, _placeholder = line.partition("==>")
        if secret:
            secrets.append(secret)
    return secrets


_MANUAL_REMINDERS = (
    "\nManual steps required -- this command never pushes automatically:\n"
    "  1. Notify every collaborator/branch-owner before pushing -- a stale\n"
    "     clone's `git pull` silently reintroduces the purged secret via\n"
    "     merge; it does not error.\n"
    "  2. If this repo was ever public, file a support request with the\n"
    "     git host to purge cached views/forks -- rewriting history and\n"
    "     pushing the rewrite does not reach those."
)


@dataclasses.dataclass(frozen=True)
class PurgeResult:
    mirror_dir: pathlib.Path
    refs: list[str]
    secrets_count: int
    source: str


def format_dry_run_text(refs: list[str], secrets_count: int, source: str) -> str:
    return (
        f"DRY RUN: would mirror-clone {source}, rewrite {len(refs)} ref(s) "
        f"to remove {secrets_count} secret(s), then verify. No clone or "
        "rewrite performed."
    )


def format_success_text(result: PurgeResult) -> str:
    lines = [
        f"Rewrote {len(result.refs)} ref(s) in {result.mirror_dir}, "
        f"removing {result.secrets_count} secret(s). Verification found no "
        "remaining occurrences.",
        "\nTo push the rewritten history, run manually:",
    ]
    for ref in result.refs:
        lines.append(f"  git -C {result.mirror_dir} push --force {result.source} {ref}")
    lines.append(_MANUAL_REMINDERS)
    return "\n".join(lines)


def run_purge(
    project_root: pathlib.Path,
    source: str | None,
    refs_file: pathlib.Path,
    replacements_path: pathlib.Path,
    mirror_dir: pathlib.Path | None,
    apply: bool,
) -> str:
    refs = load_refs(refs_file)
    stripped_replacements = load_stripped_replacements(replacements_path)
    secrets = secrets_from_replacements(stripped_replacements)
    check_filter_repo_available()
    resolved_source = resolve_local_source(source or default_source(project_root))

    if not apply:
        return format_dry_run_text(refs, len(secrets), resolved_source)

    resolved_mirror_dir = mirror_dir or pathlib.Path(
        tempfile.mkdtemp(prefix="lrh-secrets-purge-")
    )
    mirror_clone(resolved_source, resolved_mirror_dir)
    run_filter_repo(resolved_mirror_dir, stripped_replacements, refs)

    remaining = verify_clean(resolved_mirror_dir, secrets)
    if remaining:
        print(
            f"FAIL: {len(remaining)} secret(s) still present after rewrite "
            f"in {resolved_mirror_dir}. Not printing a push command.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    result = PurgeResult(
        mirror_dir=resolved_mirror_dir,
        refs=refs,
        secrets_count=len(secrets),
        source=resolved_source,
    )
    return format_success_text(result)
