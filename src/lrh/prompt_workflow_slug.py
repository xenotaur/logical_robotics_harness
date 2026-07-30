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

_CAT_FILE_MISSING_PATTERN = re.compile(r"does not exist in", re.IGNORECASE)


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
    def _parsed_created_at(self) -> datetime.datetime | None:
        """The parsed ``created_at``, or ``None`` if unusable.

        Requires a timezone-aware result, not just a successful parse.
        ``datetime.fromisoformat`` also happily accepts offset-naive
        strings (e.g. a date with no time-of-day, or a timestamp missing
        its UTC offset) -- the execution-record contract requires an
        offset, so an offset-naive parse is exactly as unusable as one
        that fails outright. Treating it as "known" here would let a
        naive datetime reach ``sort_key`` and get compared against an
        offset-aware one, which raises ``TypeError`` rather than
        producing any answer at all.
        """

        try:
            parsed = datetime.datetime.fromisoformat(self.created_at)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return None
        return parsed

    @property
    def has_known_created_at(self) -> bool:
        return self._parsed_created_at is not None

    @property
    def sort_key(self) -> datetime.datetime:
        parsed = self._parsed_created_at
        if parsed is not None:
            return parsed
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)


@dataclasses.dataclass(frozen=True)
class SlugCheckResult:
    """Combined local + cross-PR slug idempotence check result."""

    slug: str
    work_item: str
    matches: list[SlugMatch]

    @property
    def _matches_at_latest_instant(self) -> list[SlugMatch]:
        """All matches tied for the latest ``sort_key``, not just one.

        ``created_at`` is truncated to whole seconds, so two independent
        records (e.g. two PRs) can legitimately share the exact same
        instant. Picking a single "winner" via ``max()`` breaks ties by
        incidental iteration/list order, which can silently make a
        `failed` match "beat" an equally-recent `in_progress` match
        purely because of ordering -- discarding real status evidence.
        Every match tied for the latest instant must be considered, not
        just an arbitrary one of them.
        """

        if not self.matches:
            return []
        latest = max(match.sort_key for match in self.matches)
        return [match for match in self.matches if match.sort_key == latest]

    @property
    def most_recent(self) -> SlugMatch | None:
        """A representative match for display/`--rerun-of` purposes.

        When multiple matches tie for the latest instant, prefers one
        that isn't terminal (the more actionable one to surface) --
        purely cosmetic when ``blocking``/``exit_code`` already account
        for every tied match, not just this single representative.
        """

        candidates = self._matches_at_latest_instant
        if not candidates:
            return None
        for candidate in candidates:
            if candidate.status not in TERMINAL_STATUSES:
                return candidate
        return candidates[0]

    @property
    def has_unresolved_recency(self) -> bool:
        """True if any match's recency cannot be established.

        A match with a missing/malformed ``created_at`` sorts as the
        oldest possible instant (see ``SlugMatch.sort_key``), which is
        merely a tiebreak for comparison -- it must never let such a match
        lose to an older-but-parseable terminal-status match and thereby
        vanish from the blocking decision. If recency can't be
        established for *any* match, we cannot trust that "most recent by
        timestamp" is genuinely the most recent attempt, so the whole
        result is unresolved and must block.
        """

        return any(not match.has_known_created_at for match in self.matches)

    @property
    def blocking(self) -> bool:
        """Default policy: block on anything but an explicit terminal status.

        This is the labeled *default* from ``DEC-PRE-MINT-SLUG-IDEMPOTENCE-
        DEFAULT``, not a mandate -- a skill may deviate (e.g.
        ``lrh-confirm-fixes``'s Decision 12 warning-only behavior) by
        interpreting this result differently rather than by changing this
        function. Only ``failed``/``reverted``/``superseded`` are
        non-blocking; ``landed``/``in_progress`` block as usual, and a
        ``planned`` or otherwise unrecognized/missing status also blocks
        -- an unresolved outcome is not license to proceed, it means stop
        and report the ambiguity (matching the shell-based idempotence
        check this module replaces, which treated any unknown status as a
        stop condition rather than a green light). A match whose recency
        cannot be established also blocks, regardless of what a naive
        "most recent by timestamp" comparison would otherwise pick. When
        multiple matches tie for the latest instant, blocks if *any* of
        them is non-terminal -- a single terminal match must not hide an
        equally-recent blocking one."""

        if not self.matches:
            return False
        if self.has_unresolved_recency:
            return True
        return any(
            match.status not in TERMINAL_STATUSES
            for match in self._matches_at_latest_instant
        )

    @property
    def unresolved_status(self) -> bool:
        """True if any match tied for latest has an unclassifiable status.

        Distinguishes an ordinary blocking match (``landed``/
        ``in_progress``) from one that blocks only because its status
        could not be classified at all -- useful for giving the human a
        more specific reason than a bare "blocking." Does not by itself
        cover the ``has_unresolved_recency`` case -- check that
        separately for the "we can't even tell which match is most
        recent" reason.
        """

        return any(
            match.status not in (BLOCKING_STATUSES | TERMINAL_STATUSES)
            for match in self._matches_at_latest_instant
        )

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
        rel_path = (rel_prefix / path.name).as_posix()
        record = prompt_workflow_records.parse_execution_record(path)
        if record is None:
            # The filename is an authoritative trailing-segment match, but
            # its frontmatter is malformed or unreadable. Preserve it as an
            # unresolved-status match rather than silently discarding it --
            # dropping it here would let a genuinely prior (if malformed)
            # record be missed entirely, permitting a duplicate mint.
            matches.append(
                SlugMatch(
                    path=rel_path,
                    execution_id="",
                    status="unparseable",
                    pr="",
                    created_at="",
                    source="local",
                )
            )
            continue
        matches.append(
            SlugMatch(
                path=rel_path,
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


def _make_default_git_runner(project_root: str | pathlib.Path) -> GitRunner:
    """Bind a git runner to ``project_root`` rather than the process cwd.

    Without this, a caller invoking ``check_slug``/``find_remote_matches``
    with ``--project-root`` pointing somewhere other than the process's
    own working directory would have every ``git`` call silently operate
    on the wrong repository -- querying (and mutating refs in) whatever
    repo the process happens to be running from instead of the requested
    target.
    """

    def runner(args: list[str]) -> "subprocess.CompletedProcess[str]":
        return subprocess.run(
            ["git", *args],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )

    return runner


def _make_default_gh_runner(project_root: str | pathlib.Path) -> GhRunner:
    def runner(argv: list[str]) -> object:
        return gh_client.run_gh_json(argv, cwd=project_root)

    return runner


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
    project_root: str | pathlib.Path = ".",
    local_paths: typing.Iterable[str] = (),
    gh_runner: GhRunner | None = None,
    git_runner: GitRunner | None = None,
) -> list[SlugMatch]:
    """Cross-PR (including fork) trailing-segment filename search.

    Raises :class:`SlugCheckError` on any ``gh``/``git`` failure instead
    of silently reporting no match, closing the
    "Idempotence cross-PR discovery doesn't fail closed on fetch errors"
    gap tracked in ``project/design/backlog.md``.

    ``gh``/``git`` calls are bound to ``project_root`` by default (via
    ``cwd``) rather than the process's own working directory, so a caller
    targeting a project root other than its cwd doesn't silently query a
    different repository. Pass explicit ``gh_runner``/``git_runner``
    callables to override (e.g. for tests).
    """

    if git_runner is None:
        git_runner = _make_default_git_runner(project_root)
    if gh_runner is None:
        gh_runner = _make_default_gh_runner(project_root)

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
            if not _CAT_FILE_MISSING_PATTERN.search(inherited.stderr or ""):
                # A nonzero exit here is normally git's ordinary "path
                # doesn't exist at this tree-ish" outcome (expected -- it
                # means the PR did introduce the file). Anything else
                # (corrupted repo, bad object database, etc.) is a real
                # git failure and must not be silently treated the same
                # way -- fail loudly instead of guessing "not inherited."
                raise SlugCheckError(
                    f"git cat-file -e {merge_base}:{rel_path} failed unexpectedly: "
                    f"{(inherited.stderr or '').strip()}"
                )

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
    gh_runner: GhRunner | None = None,
    git_runner: GitRunner | None = None,
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
            project_root=project_root,
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
    if result.has_unresolved_recency:
        lines.append(
            "BLOCKING (unresolved recency): at least one match has a "
            "missing or malformed created_at, so which match is truly "
            "most recent cannot be established -- stop and report rather "
            "than trusting a naive timestamp comparison."
        )
    elif result.unresolved_status:
        lines.append(
            "BLOCKING (unresolved status): most recent match "
            f"({recent.execution_id or recent.path!r}, status={recent.status!r}) "
            "has no recognized terminal or in-progress status -- stop and "
            "report the ambiguity rather than treating it as safe to continue."
        )
    elif result.blocking:
        lines.append(
            "BLOCKING: most recent match "
            f"({recent.execution_id}, status={recent.status}) "
            "-- stop and report unless the user explicitly asks for a rerun."
        )
    else:
        lines.append(
            "Non-blocking: most recent match "
            f"({recent.execution_id}, status={recent.status}) "
            "is terminal -- continue and link rerun_of."
        )
    return "\n".join(lines) + "\n"
