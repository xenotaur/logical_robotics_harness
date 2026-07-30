"""Pre-mint slug idempotence checking for LRH prompt workflows.

Implements the mechanism described by
``project/memory/decisions/DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT.md``: a
filename search matched to the complete trailing segment of a slug is
authoritative evidence that a prompt slug has already produced an
execution record, for the narrow case where no prompt ID exists yet to
look up exactly (``lrh prompt label`` mints a fresh timestamped ID every
call, so ``check_execution`` alone cannot detect a rerun of the same
logical slug).

Two search scopes are combined:

- **Local**: the current checkout's execution bucket.
- **Remote**: every open PR (including forks), via GitHub's universal
  ``refs/pull/<N>/head`` ref, with a ``git merge-base`` check against
  each PR's declared base ref so a stacked PR that merely *inherited* a
  file from its parent branch is not misattributed as having introduced
  it.

Any ``gh``/``git`` failure raises :class:`SlugCheckError` rather than
being swallowed -- silence must never be conflated with "no prior
record found."
"""

from __future__ import annotations

import dataclasses
import datetime
import pathlib
import re
import subprocess
import typing

from lrh import prompt_workflow_records
from lrh.integrations.github import gh_client

BLOCKING_STATUSES = {"landed", "in_progress"}
TERMINAL_STATUSES = {"failed", "reverted", "superseded"}

GitRunner = typing.Callable[[list[str]], "subprocess.CompletedProcess[str]"]
GhRunner = typing.Callable[[list[str]], object]


class SlugCheckError(RuntimeError):
    """A gh/git call failed while searching for a prior slug match.

    Callers must treat this as "unable to determine an answer," not as
    "no prior record" -- fail loudly rather than silently risk minting a
    duplicate or acting on stale information.
    """


def _slug_upper_underscore(slug: str) -> str:
    return slug.replace("-", "_").upper()


def _trailing_segment_pattern(slug_upper: str) -> re.Pattern[str]:
    return re.compile(rf"_{re.escape(slug_upper)}\.md$")


@dataclasses.dataclass(frozen=True)
class SlugMatch:
    """One execution record matched by trailing-segment slug search."""

    path: str
    execution_id: str
    status: str
    pr: str
    created_at: str
    source: str

    @property
    def sort_key(self) -> datetime.datetime:
        try:
            return datetime.datetime.fromisoformat(self.created_at)
        except ValueError:
            return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)


@dataclasses.dataclass(frozen=True)
class SlugCheckResult:
    """Combined local + cross-PR slug idempotence check result."""

    slug: str
    work_item: str
    matches: list[SlugMatch]

    @property
    def most_recent(self) -> SlugMatch | None:
        if not self.matches:
            return None
        return max(self.matches, key=lambda match: match.sort_key)

    @property
    def blocking(self) -> bool:
        """Default policy: block on landed/in_progress, else continue.

        This is the labeled *default* from ``DEC-PRE-MINT-SLUG-IDEMPOTENCE-
        DEFAULT``, not a mandate -- a skill may deviate (e.g.
        ``lrh-confirm-fixes``'s Decision 12 warning-only behavior) by
        interpreting this result differently rather than by changing this
        function. A ``planned`` (or otherwise unrecognized) status is
        deliberately left non-blocking here: the decision record leaves
        that gap unresolved centrally, and defaulting to "continue" is the
        safer of the two guesses.
        """

        recent = self.most_recent
        return recent is not None and recent.status in BLOCKING_STATUSES

    @property
    def exit_code(self) -> int:
        return 1 if self.blocking else 0


def find_local_matches(
    project_root: str | pathlib.Path,
    slug: str,
    work_item: str = "AD_HOC",
    output_root: str | pathlib.Path = "project/executions",
) -> list[SlugMatch]:
    """Trailing-segment filename search of the local checkout's bucket."""

    slug_upper = _slug_upper_underscore(slug)
    pattern = _trailing_segment_pattern(slug_upper)
    bucket = pathlib.Path(project_root) / output_root / work_item
    rel_prefix = pathlib.PurePosixPath(str(output_root)) / work_item

    matches: list[SlugMatch] = []
    if not bucket.is_dir():
        return matches
    for path in sorted(bucket.glob("*.md")):
        if not pattern.search(path.name):
            continue
        record = prompt_workflow_records.parse_execution_record(path)
        if record is None:
            continue
        matches.append(
            SlugMatch(
                path=(rel_prefix / path.name).as_posix(),
                execution_id=record.execution_id,
                status=record.status,
                pr=record.pr,
                created_at=record.created_at,
                source="local",
            )
        )
    return matches


@dataclasses.dataclass(frozen=True)
class _OpenPr:
    number: int
    base_ref: str


def _list_open_prs(gh_runner: GhRunner) -> list[_OpenPr]:
    try:
        payload = gh_runner(
            [
                "pr",
                "list",
                "--state",
                "open",
                "--limit",
                "1000",
                "--json",
                "number,baseRefName",
            ]
        )
    except RuntimeError as error:
        raise SlugCheckError(f"gh pr list failed: {error}") from error
    if not isinstance(payload, list):
        raise SlugCheckError("gh pr list returned an unexpected response shape")
    prs: list[_OpenPr] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        prs.append(
            _OpenPr(number=int(entry["number"]), base_ref=str(entry["baseRefName"]))
        )
    return prs


def _default_git_runner(args: list[str]) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(["git", *args], check=False, capture_output=True, text=True)


def _run_git_or_raise(git_runner: GitRunner, args: list[str], *, context: str) -> str:
    result = git_runner(args)
    if result.returncode != 0:
        raise SlugCheckError(
            f"git {' '.join(args)} failed ({context}): {result.stderr.strip()}"
        )
    return result.stdout


def find_remote_matches(
    slug: str,
    work_item: str = "AD_HOC",
    output_root: str | pathlib.Path = "project/executions",
    *,
    local_paths: typing.Iterable[str] = (),
    gh_runner: GhRunner = gh_client.run_gh_json,
    git_runner: GitRunner = _default_git_runner,
) -> list[SlugMatch]:
    """Cross-PR (including fork) trailing-segment filename search.

    Raises :class:`SlugCheckError` on any ``gh``/``git`` failure instead
    of silently reporting no match, closing the
    "Idempotence cross-PR discovery doesn't fail closed on fetch errors"
    gap tracked in ``project/design/backlog.md``.
    """

    slug_upper = _slug_upper_underscore(slug)
    pattern = _trailing_segment_pattern(slug_upper)
    bucket_prefix = (pathlib.PurePosixPath(str(output_root)) / work_item).as_posix()
    local_path_set = set(local_paths)

    matches: list[SlugMatch] = []
    for pr in _list_open_prs(gh_runner):
        pr_ref = f"refs/remotes/pr/{pr.number}"
        _run_git_or_raise(
            git_runner,
            ["fetch", "origin", f"+refs/pull/{pr.number}/head:{pr_ref}", "--quiet"],
            context=f"fetching PR #{pr.number}",
        )
        _run_git_or_raise(
            git_runner,
            ["fetch", "origin", pr.base_ref, "--quiet"],
            context=f"fetching base ref '{pr.base_ref}' for PR #{pr.number}",
        )
        merge_base = _run_git_or_raise(
            git_runner,
            ["merge-base", pr_ref, f"origin/{pr.base_ref}"],
            context=f"computing merge-base for PR #{pr.number}",
        ).strip()

        ls_tree_output = _run_git_or_raise(
            git_runner,
            ["ls-tree", "-r", pr_ref, "--name-only", "--", bucket_prefix],
            context=f"listing execution bucket for PR #{pr.number}",
        )
        for rel_path in ls_tree_output.splitlines():
            rel_path = rel_path.strip()
            if not rel_path or not pattern.search(rel_path):
                continue
            if rel_path in local_path_set:
                continue

            inherited = git_runner(["cat-file", "-e", f"{merge_base}:{rel_path}"])
            if inherited.returncode == 0:
                # Already present at this PR's own merge-base with its
                # declared base ref: inherited from a stacked branch, not
                # newly introduced by this PR.
                continue

            show_output = _run_git_or_raise(
                git_runner,
                ["show", f"{pr_ref}:{rel_path}"],
                context=f"reading {rel_path} from PR #{pr.number}",
            )
            fields = prompt_workflow_records.parse_front_matter_fields_from_text(
                show_output
            )
            matches.append(
                SlugMatch(
                    path=rel_path,
                    execution_id=fields.get("execution_id", ""),
                    status=fields.get("status", ""),
                    pr=fields.get("pr", ""),
                    created_at=fields.get("created_at", ""),
                    source=f"PR#{pr.number}",
                )
            )
    return matches


def check_slug(
    project_root: str | pathlib.Path,
    slug: str,
    work_item: str = "AD_HOC",
    output_root: str | pathlib.Path = "project/executions",
    *,
    include_remote: bool = True,
    gh_runner: GhRunner = gh_client.run_gh_json,
    git_runner: GitRunner = _default_git_runner,
) -> SlugCheckResult:
    """Combined local + cross-PR slug idempotence check."""

    local_matches = find_local_matches(
        project_root=project_root,
        slug=slug,
        work_item=work_item,
        output_root=output_root,
    )
    remote_matches: list[SlugMatch] = []
    if include_remote:
        remote_matches = find_remote_matches(
            slug=slug,
            work_item=work_item,
            output_root=output_root,
            local_paths=[match.path for match in local_matches],
            gh_runner=gh_runner,
            git_runner=git_runner,
        )
    return SlugCheckResult(
        slug=slug,
        work_item=work_item,
        matches=local_matches + remote_matches,
    )


def format_text_result(result: SlugCheckResult) -> str:
    """Render a human-readable slug idempotence check result."""

    lines = [f"slug: {result.slug}", f"work_item: {result.work_item}"]
    if not result.matches:
        lines.append("No prior execution record found for this slug.")
        return "\n".join(lines) + "\n"

    for match in sorted(result.matches, key=lambda match: match.sort_key, reverse=True):
        lines.append(
            f"{match.path}\tstatus={match.status}"
            f"\texecution_id={match.execution_id}\tsource={match.source}"
        )

    recent = result.most_recent
    assert recent is not None
    if result.blocking:
        lines.append(
            "BLOCKING: most recent match "
            f"({recent.execution_id}, status={recent.status}) "
            "-- stop and report unless the user explicitly asks for a rerun."
        )
    else:
        lines.append(
            "Non-blocking: most recent match "
            f"({recent.execution_id}, status={recent.status}) "
            "is terminal or unrecognized -- continue and link rerun_of."
        )
    return "\n".join(lines) + "\n"
