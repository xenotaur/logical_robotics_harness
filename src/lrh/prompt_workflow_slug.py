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
    # Case-insensitive to match the shell-based idempotence check this
    # module replaces (`grep -i "_<SLUG_UPPER_UNDERSCORE>\.md\$"`) -- a
    # record filename that entered the tree with non-canonical casing
    # (hand-written, or migrated from an older convention) must still be
    # found, not silently stop matching under a case-sensitive regex.
    return re.compile(rf"_{re.escape(slug_upper)}\.md$", re.IGNORECASE)


def _execution_id_or_fallback(rel_path: str, execution_id: str) -> str:
    """Fall back to the filename stem when ``execution_id`` is blank.

    A trailing-segment filename match is authoritative evidence
    regardless of whether its own ``execution_id`` frontmatter field is
    present or valid -- if it's missing, blank, or non-string, silently
    handing back an empty string would let a rerun lose its `rerun_of`
    lineage even though the match is genuinely a prior execution. The
    filename stem is always present and is exactly what `execution_id` is
    supposed to equal by convention, so it's a safe, always-available
    fallback rather than an unresolved/rejected match.
    """

    stripped = execution_id.strip() if isinstance(execution_id, str) else ""
    if stripped:
        return stripped
    return pathlib.PurePosixPath(rel_path).stem


def _raw_execution_id_or_blank(
    frontmatter: dict[str, typing.Any],
) -> str:
    """The raw ``execution_id`` frontmatter value, or "" if not a string.

    ``prompt_workflow_records.ExecutionRecord.execution_id`` (via
    ``_frontmatter_string``) coerces a non-string YAML scalar (e.g.
    ``execution_id: 123``) to ``"123"`` with ``str(value)`` -- by the
    time that already-coerced value reaches
    ``_execution_id_or_fallback``, its ``isinstance(..., str)`` check
    can no longer tell it apart from a genuinely authored string ID, so
    it would never trigger the filename-stem fallback for this case
    (inconsistent with the remote path, whose
    ``parse_front_matter_fields_from_text`` drops non-string fields
    entirely and *does* fall back correctly). Reading the type out of
    the raw, uncoerced frontmatter mapping instead closes that gap.
    """

    value = frontmatter.get("execution_id")
    return value if isinstance(value, str) else ""


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
    def _unresolved_status_match(self) -> SlugMatch | None:
        """The specific tied match whose status is actually unclassifiable.

        ``most_recent`` is a display/`--rerun-of` representative, not
        necessarily this one -- when matches tie at the latest instant,
        ``most_recent`` prefers *any* non-terminal candidate (it doesn't
        distinguish `in_progress` from `planned`), so it can point at a
        recognized blocking match even when a *different* tied match is
        the one making the result unresolved. Reporting relies on this
        property specifically so the message never names the wrong match
        as the source of the ambiguity.
        """

        for match in self._matches_at_latest_instant:
            if match.status not in (BLOCKING_STATUSES | TERMINAL_STATUSES):
                return match
        return None

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

        return self._unresolved_status_match is not None

    @property
    def exit_code(self) -> int:
        return 1 if self.blocking else 0


def _relative_output_root(
    project_root: str | pathlib.Path,
    output_root: str | pathlib.Path,
    *,
    required_for_git_pathspec: bool,
) -> pathlib.PurePosixPath:
    """``output_root`` as a POSIX path, relative to ``project_root``.

    Also normalizes through the platform-native ``PurePath`` first: on
    Windows, ``output_root`` may be backslash-separated
    (``project\\executions``), which ``PurePosixPath`` does not treat as
    a separator at all -- ``.as_posix()`` on the native form converts it
    correctly before the result is treated as POSIX-style.

    An absolute ``output_root`` works fine for a local filesystem scan
    (``pathlib``'s ``/`` operator with an absolute right-hand operand
    simply replaces the left side), but the same absolute string is not
    usable as a git pathspec -- ``git ls-tree``'s trailing ``<path>...``
    operands are always relative to the tree being listed, never a
    filesystem path, so passing an absolute path there silently matches
    nothing (a false "no prior record" for every open PR). Relativizing
    here, once, keeps the local match's ``path`` field and the remote
    search's git pathspec expressed the same way -- both project-root-
    relative POSIX strings -- so local/remote de-duplication
    (``local_paths`` in ``find_remote_matches``) still works correctly
    even when a caller passes an absolute ``--output-root``.

    ``required_for_git_pathspec`` distinguishes the two callers:
    ``find_remote_matches`` genuinely needs a git-compatible pathspec, so
    an unrelativizable absolute path must raise there. ``find_local_matches``
    has no such requirement -- an absolute path outside ``project_root``
    is still a perfectly usable local filesystem location and display/
    dedup key, so it falls back to using the resolved absolute path as-is
    rather than raising. Fixed after a regression: an earlier version of
    this function always raised regardless of caller, which meant
    ``--no-remote`` combined with an absolute, out-of-tree
    ``--output-root`` still failed with an error whose own text ("pass
    --no-remote to skip cross-PR search") was already true and had not
    helped -- confirmed by reproducing it directly against the installed
    CLI before fixing.
    """

    output_path = pathlib.PurePath(output_root)
    if output_path.is_absolute():
        project_path = pathlib.Path(project_root).resolve()
        output_abs = pathlib.Path(output_root).resolve()
        try:
            output_path = output_abs.relative_to(project_path)
        except ValueError as error:
            if required_for_git_pathspec:
                raise SlugCheckError(
                    f"--output-root {str(output_root)!r} is an absolute "
                    f"path outside --project-root {str(project_root)!r}; "
                    "it cannot be expressed as a git pathspec for remote "
                    "discovery. Use a relative --output-root, or pass "
                    "--no-remote to skip cross-PR search."
                ) from error
            return pathlib.PurePosixPath(output_abs.as_posix())
    return pathlib.PurePosixPath(output_path.as_posix())


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
    rel_prefix = (
        _relative_output_root(
            project_root, output_root, required_for_git_pathspec=False
        )
        / work_item
    )

    matches: list[SlugMatch] = []
    if not bucket.is_dir():
        return matches
    for path in sorted(bucket.iterdir()):
        # Enumerate every entry, not `bucket.glob("*.md")`: glob matching
        # is case-sensitive regardless of the underlying filesystem's own
        # case-sensitivity (confirmed empirically), so a hand-written or
        # migrated record ending in `.MD` would be silently filtered out
        # here before the trailing-segment regex (already
        # case-insensitive, matching the shell logic this module
        # replaced) ever got a chance to match it. The regex alone -- it
        # requires `.md$` case-insensitively -- is sufficient filtering.
        if not path.is_file() or not pattern.search(path.name):
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
                    execution_id=_execution_id_or_fallback(rel_path, ""),
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
                execution_id=_execution_id_or_fallback(
                    rel_path, _raw_execution_id_or_blank(record.frontmatter)
                ),
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


# `gh pr list --limit N` paginates internally (via GraphQL cursors) to
# satisfy any requested N, not just the API's single-page size -- so a
# large ceiling here is "effectively all open PRs" for any repo size that
# could plausibly exist, not a real cap. A too-small hardcoded limit
# (e.g. the previous 1,000) would silently omit PRs beyond it in a repo
# that legitimately has more open PRs than that, and since this list is
# treated as authoritative for the slug check, a blocking match hiding
# past the cutoff would produce a false "no prior record" (exit 0).
_MAX_OPEN_PRS_TO_SCAN = 100_000


def _list_open_prs(gh_runner: GhRunner) -> list[_OpenPr]:
    try:
        payload = gh_runner(
            [
                "pr",
                "list",
                "--state",
                "open",
                "--limit",
                str(_MAX_OPEN_PRS_TO_SCAN),
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
        # This list is treated as authoritative for the blocking
        # decision, so a malformed entry must fail loudly
        # (SlugCheckError) rather than either being silently skipped
        # (a false "no prior record" if that PR held a real match) or
        # crashing with a raw KeyError/TypeError/ValueError if the gh
        # payload shape ever changes.
        if not isinstance(entry, dict):
            raise SlugCheckError(f"gh pr list returned a non-object entry: {entry!r}")
        try:
            number = int(entry["number"])
            base_ref = str(entry["baseRefName"])
        except (KeyError, TypeError, ValueError) as error:
            raise SlugCheckError(
                f"gh pr list returned a malformed entry {entry!r}: {error}"
            ) from error
        prs.append(_OpenPr(number=number, base_ref=base_ref))
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
    try:
        result = git_runner(args)
    except FileNotFoundError as error:
        # subprocess.run raises this directly (rather than returning a
        # CompletedProcess with a nonzero code) when the executable
        # itself can't be launched at all -- e.g. `git` missing from
        # PATH. Left uncaught, this surfaces as a raw traceback instead
        # of the documented SlugCheckError/exit-3 contract every other
        # git failure in this module goes through. Mirrors
        # gh_client.run_gh_json's existing handling of the same failure
        # mode for `gh`.
        raise SlugCheckError(f"git not found ({context}): {error}") from error
    if result.returncode != 0:
        raise SlugCheckError(
            f"git {' '.join(args)} failed ({context}): {result.stderr.strip()}"
        )
    return result.stdout


def _delete_ref_best_effort(git_runner: GitRunner, ref: str) -> None:
    """Delete a temporary harness ref, never letting cleanup itself fail.

    Deliberately swallows every exception, including one raised by
    ``git_runner`` itself (e.g. ``FileNotFoundError`` if ``git`` is
    missing) -- not just a nonzero return code. This runs in a
    ``finally`` block after the check's real work is done; a cleanup
    failure must never replace or mask whatever exception (or lack of
    one) is already propagating, and a ref that was never created (the
    "no candidates" early-exit never fetches ``base_ref`` at all) is
    expected to fail to delete.
    """

    try:
        git_runner(["update-ref", "-d", ref])
    except Exception:
        pass


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
    # See _relative_output_root's docstring: an absolute output_root must
    # be relativized against project_root here, or the git pathspec below
    # never matches anything (a false "no prior record" for every PR).
    bucket_prefix = (
        _relative_output_root(project_root, output_root, required_for_git_pathspec=True)
        / work_item
    ).as_posix()
    local_path_set = set(local_paths)

    matches: list[SlugMatch] = []
    for pr in _list_open_prs(gh_runner):
        # A harness-owned namespace, not `refs/remotes/*` -- a client
        # repository could have an actual remote named `pr` or `pr-base`
        # (uncommon, but real), which `refs/remotes/pr/<N>` would silently
        # overwrite. `refs/lrh/pulls/<N>/...` cannot collide with any
        # configured remote's own tracking refs, and reads as clearly
        # harness-managed rather than a real remote-tracking branch.
        pr_ref = f"refs/lrh/pulls/{pr.number}/head"
        base_ref = f"refs/lrh/pulls/{pr.number}/base"
        try:
            _run_git_or_raise(
                git_runner,
                [
                    "fetch",
                    "origin",
                    f"+refs/pull/{pr.number}/head:{pr_ref}",
                    "--quiet",
                ],
                context=f"fetching PR #{pr.number}",
            )

            ls_tree_output = _run_git_or_raise(
                git_runner,
                ["ls-tree", "-r", pr_ref, "--name-only", "--", bucket_prefix],
                context=f"listing execution bucket for PR #{pr.number}",
            )
            candidate_paths = [
                candidate
                for candidate in (line.strip() for line in ls_tree_output.splitlines())
                if candidate
                and pattern.search(candidate)
                and candidate not in local_path_set
            ]
            if not candidate_paths:
                # Nothing in this PR's own tree could possibly match this
                # slug, so there is no need to resolve its base ref or
                # compute a merge-base at all. This matters beyond
                # efficiency: a PR whose base branch has since been
                # deleted or is otherwise unfetchable (a real, if
                # uncommon, occurrence for a long-open PR) would
                # otherwise make *every* --slug check fail loudly for
                # *every* PR and *every* slug, since the base-ref
                # fetch/merge-base calls below always ran unconditionally
                # -- turning one broken, unrelated PR into a repo-wide
                # single point of failure. Skipping straight past a PR
                # with zero candidate matches keeps fail-loud behavior
                # exactly where it is actually needed: a PR that might
                # hide a real match.
                continue

            _run_git_or_raise(
                git_runner,
                [
                    "fetch",
                    "origin",
                    f"+refs/heads/{pr.base_ref}:{base_ref}",
                    "--quiet",
                ],
                context=f"fetching base ref '{pr.base_ref}' for PR #{pr.number}",
            )
            merge_base = _run_git_or_raise(
                git_runner,
                ["merge-base", pr_ref, base_ref],
                context=f"computing merge-base for PR #{pr.number}",
            ).strip()

            for rel_path in candidate_paths:
                # Structural tree-membership check, not stderr-text
                # matching: `git ls-tree` either succeeds (0) and lists
                # the path if present at that tree-ish, or fails
                # (nonzero) only if `merge_base` itself is unusable -- a
                # genuine failure worth raising on. Unlike
                # `git cat-file -e`, its "not present" signal (empty
                # stdout on success) carries no free-text message at all,
                # so there is no locale/git-version-dependent wording to
                # misclassify (a real gap found in round 6 review:
                # `cat-file -e`'s error text differs between "does not
                # exist in <tree>" and "exists on disk, but not in <tree>"
                # depending on exactly how the path is absent, and
                # matching only one of those wrongly treated the other as
                # a fatal git error).
                tree_listing = _run_git_or_raise(
                    git_runner,
                    ["ls-tree", "--name-only", merge_base, "--", rel_path],
                    context=f"checking tree membership of {rel_path} at merge-base",
                )
                if tree_listing.strip():
                    # Present at this PR's own merge-base with its
                    # declared base ref: inherited from a stacked branch,
                    # not newly introduced by this PR.
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
                        execution_id=_execution_id_or_fallback(
                            rel_path, fields.get("execution_id", "")
                        ),
                        status=fields.get("status", ""),
                        pr=fields.get("pr", ""),
                        created_at=fields.get("created_at", ""),
                        source=f"PR#{pr.number}",
                    )
                )
        finally:
            _delete_ref_best_effort(git_runner, pr_ref)
            _delete_ref_best_effort(git_runner, base_ref)
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
        offender = result._unresolved_status_match
        assert offender is not None
        lines.append(
            "BLOCKING (unresolved status): tied-for-latest match "
            f"({offender.execution_id or offender.path!r}, "
            f"status={offender.status!r}) "
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
