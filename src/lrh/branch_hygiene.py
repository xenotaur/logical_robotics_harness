"""Report-only local branch hygiene survey.

Classifies every local branch in a checkout into a documented class and
can render reviewable ``git branch`` deletion commands to a file --
this module never deletes or modifies any branch or ref itself. Deletion
is a human action: ``git branch -d``/``-D`` are denied to agents in this
project's own permission policy (see
``docs/how-to/project-setup/claude-code-permissions.md``), and the safe,
automatable part of branch-hygiene cleanup is the survey and the
reviewable command list, not the deletion.

Two safety properties are load-bearing and covered by dedicated tests,
not left to the classification logic alone:

- The discovered default branch is never classified ``merged_or_empty``
  and never receives a generated delete command, even when it is the
  branch checked out at survey time (a feature-branch checkout makes the
  default branch an ancestor of ``HEAD``, so an unguarded "merged or
  empty" test would otherwise recommend deleting it).
- Every branch name emitted into a generated command is shell-quoted
  with an option terminator (``git branch -D -- <quoted-name>``) --
  valid git ref names can contain shell metacharacters (for example
  ``refs/heads/$(touch PWN)``), so unquoted interpolation into a file a
  human later runs risks executing arbitrary shell syntax.
"""

from __future__ import annotations

import dataclasses
import enum
import shlex
import subprocess
import typing

from lrh.integrations.github import gh_client

GitRunner = typing.Callable[[list[str]], "subprocess.CompletedProcess[str]"]
GhRunner = typing.Callable[[list[str]], object]

# `gh pr list --state all --limit N` paginates internally to satisfy any
# requested N -- a large ceiling here is "effectively all PRs" for any
# repo size that could plausibly exist, not a real cap (mirrors
# `prompt_workflow_slug._MAX_OPEN_PRS_TO_SCAN`'s own reasoning: a
# too-small hardcoded limit would silently omit PRs beyond it and
# misclassify their branches).
_MAX_PRS_TO_SCAN = 100_000


class BranchHygieneError(RuntimeError):
    """A git/gh call failed while surveying local branches.

    Callers must treat this as "unable to determine an answer," not as
    a classification result -- fail loudly rather than silently guessing
    at branch state.
    """


class BranchClass(enum.Enum):
    """The documented, mutually exclusive classes a branch can receive.

    Deterministic precedence (checked in this order by
    :func:`classify_branch`): ``DEFAULT``, ``IN_WORKTREE``, ``OPEN_PR``,
    ``MERGED_OR_EMPTY``, ``SQUASH_MERGED``, ``REVIEW_FIRST``,
    ``UNIQUE_WORK``. A branch that could match more than one class
    (for example, in a worktree *and* squash-merged) always receives the
    earliest-checked class -- ``DEFAULT``, ``IN_WORKTREE``, and
    ``OPEN_PR`` are always report-only regardless of any other class the
    branch also matches, and ``REVIEW_FIRST`` (ambiguous/unknown) is the
    fallback for anything the other checks cannot positively classify.
    """

    DEFAULT = "default"
    IN_WORKTREE = "in_worktree"
    OPEN_PR = "open_pr"
    MERGED_OR_EMPTY = "merged_or_empty"
    SQUASH_MERGED = "squash_merged"
    REVIEW_FIRST = "review_first"
    UNIQUE_WORK = "unique_work"


# Only these two classes are ever delete-eligible. Every other class --
# including UNIQUE_WORK, which has no open PR and no merge evidence but
# is not provably safe to delete either -- stays report-only.
_DELETE_FLAGS = {
    BranchClass.MERGED_OR_EMPTY: "-d",
    BranchClass.SQUASH_MERGED: "-D",
}


@dataclasses.dataclass(frozen=True)
class BranchInfo:
    """One local branch's survey result."""

    name: str
    branch_class: BranchClass
    reason: str
    has_upstream: bool
    open_pr_numbers: tuple[int, ...] = ()
    merged_pr_number: int | None = None

    @property
    def delete_flag(self) -> str | None:
        """``-d``/``-D`` if this class is delete-eligible, else ``None``."""
        return _DELETE_FLAGS.get(self.branch_class)


def quote_branch_name(name: str) -> str:
    """Shell-quote a branch name for safe interpolation into a command.

    Valid git ref names can contain shell metacharacters that are not in
    ref names' own forbidden set (space, ``~``, ``^``, ``:``, ``?``,
    ``*``, ``[``, ``\\``) -- for example ``$``, ``(``, ``)``, and ``;``
    are all legal in a ref name. :func:`shlex.quote` alone is not
    sufficient from an option-injection standpoint if a ref name could
    start with ``-``; callers combine this with an explicit ``--``
    option terminator (see :func:`render_delete_command`) rather than
    relying on quoting alone to prevent argument injection.
    """
    return shlex.quote(name)


def render_delete_command(info: BranchInfo) -> str | None:
    """Render a ``git branch <flag> -- <name>`` line, or ``None``.

    Returns ``None`` for any branch whose class is not delete-eligible
    (see :data:`_DELETE_FLAGS`) -- callers must not fabricate a flag for
    a report-only class.
    """
    flag = info.delete_flag
    if flag is None:
        return None
    return f"git branch {flag} -- {quote_branch_name(info.name)}"


def default_git_runner(project_root: str = ".") -> GitRunner:
    """Build a :data:`GitRunner` bound to ``project_root``.

    Without binding explicitly, a caller operating on a project root
    other than the process's own working directory would have every
    ``git`` call silently target the wrong repository.
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


def default_gh_runner(project_root: str = ".") -> GhRunner:
    def runner(argv: list[str]) -> object:
        return gh_client.run_gh_json(argv, cwd=project_root)

    return runner


def _run_git_or_raise(git_runner: GitRunner, args: list[str], *, context: str) -> str:
    try:
        result = git_runner(args)
    except FileNotFoundError as error:
        raise BranchHygieneError(f"git not found ({context}): {error}") from error
    if result.returncode != 0:
        raise BranchHygieneError(
            f"git {' '.join(args)} failed ({context}): {result.stderr.strip()}"
        )
    return result.stdout


def discover_default_branch(git_runner: GitRunner) -> str:
    """Discover the repository's default branch name (never hard-coded).

    Reads ``origin/HEAD``'s symbolic target rather than assuming
    ``main``/``master`` -- a client repository installing this survey
    may use either, or something else entirely.
    """
    output = _run_git_or_raise(
        git_runner,
        ["symbolic-ref", "refs/remotes/origin/HEAD"],
        context="discovering default branch",
    )
    ref = output.strip()
    prefix = "refs/remotes/origin/"
    if not ref.startswith(prefix):
        raise BranchHygieneError(f"unexpected origin/HEAD symbolic-ref target: {ref!r}")
    return ref[len(prefix) :]


def discover_worktree_branches(git_runner: GitRunner) -> frozenset[str]:
    """Return every branch name checked out in any worktree.

    Parses ``git worktree list --porcelain`` rather than assuming any
    particular worktree layout or path -- a checkout's own worktree
    paths are not something this survey should hard-code.
    """
    output = _run_git_or_raise(
        git_runner,
        ["worktree", "list", "--porcelain"],
        context="listing worktrees",
    )
    branches: set[str] = set()
    for line in output.splitlines():
        if line.startswith("branch "):
            ref = line[len("branch ") :].strip()
            if ref.startswith("refs/heads/"):
                branches.add(ref[len("refs/heads/") :])
    return frozenset(branches)


def list_local_branches(git_runner: GitRunner) -> tuple[str, ...]:
    output = _run_git_or_raise(
        git_runner,
        ["for-each-ref", "--format=%(refname:short)", "refs/heads"],
        context="listing local branches",
    )
    return tuple(line for line in output.splitlines() if line)


def _is_ancestor_of_default(
    git_runner: GitRunner, branch: str, default_branch: str
) -> bool:
    result = git_runner(
        ["merge-base", "--is-ancestor", branch, f"origin/{default_branch}"]
    )
    return result.returncode == 0


def _has_upstream(git_runner: GitRunner, branch: str) -> bool:
    result = git_runner(["rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"])
    return result.returncode == 0


def _branch_tip(git_runner: GitRunner, branch: str) -> str:
    return _run_git_or_raise(
        git_runner, ["rev-parse", branch], context=f"resolving tip of {branch}"
    ).strip()


@dataclasses.dataclass(frozen=True)
class _PrRecord:
    number: int
    state: str
    head_ref_oid: str


def _fetch_prs_by_branch(gh_runner: GhRunner) -> dict[str, list[_PrRecord]]:
    try:
        payload = gh_runner(
            [
                "pr",
                "list",
                "--state",
                "all",
                "--limit",
                str(_MAX_PRS_TO_SCAN),
                "--json",
                "number,headRefName,state,headRefOid",
            ]
        )
    except RuntimeError as error:
        raise BranchHygieneError(f"gh pr list failed: {error}") from error
    if not isinstance(payload, list):
        raise BranchHygieneError("gh pr list returned an unexpected response shape")
    by_branch: dict[str, list[_PrRecord]] = {}
    for entry in payload:
        if not isinstance(entry, dict):
            raise BranchHygieneError(
                f"gh pr list returned a non-object entry: {entry!r}"
            )
        try:
            record = _PrRecord(
                number=int(entry["number"]),
                state=str(entry["state"]),
                head_ref_oid=str(entry["headRefOid"]),
            )
            head_ref_name = str(entry["headRefName"])
        except (KeyError, TypeError, ValueError) as error:
            raise BranchHygieneError(
                f"gh pr list returned a malformed entry {entry!r}: {error}"
            ) from error
        by_branch.setdefault(head_ref_name, []).append(record)
    return by_branch


def classify_branch(
    name: str,
    *,
    is_default: bool,
    in_worktree: bool,
    is_ancestor_of_default: bool,
    has_upstream: bool,
    tip: str,
    prs: typing.Sequence[_PrRecord],
) -> BranchInfo:
    """Assign exactly one class to a branch by documented precedence."""
    open_pr_numbers = tuple(pr.number for pr in prs if pr.state == "OPEN")
    merged_match = next(
        (pr for pr in prs if pr.state == "MERGED" and pr.head_ref_oid == tip), None
    )

    if is_default:
        return BranchInfo(
            name=name,
            branch_class=BranchClass.DEFAULT,
            reason="discovered repository default branch; never delete-eligible",
            has_upstream=has_upstream,
            open_pr_numbers=open_pr_numbers,
        )
    if in_worktree:
        return BranchInfo(
            name=name,
            branch_class=BranchClass.IN_WORKTREE,
            reason="checked out in a local worktree",
            has_upstream=has_upstream,
            open_pr_numbers=open_pr_numbers,
        )
    if open_pr_numbers:
        return BranchInfo(
            name=name,
            branch_class=BranchClass.OPEN_PR,
            reason=f"has an open PR: {', '.join(f'#{n}' for n in open_pr_numbers)}",
            has_upstream=has_upstream,
            open_pr_numbers=open_pr_numbers,
        )
    if is_ancestor_of_default:
        return BranchInfo(
            name=name,
            branch_class=BranchClass.MERGED_OR_EMPTY,
            reason="an ancestor of the default branch; nothing unique",
            has_upstream=has_upstream,
        )
    if merged_match is not None:
        return BranchInfo(
            name=name,
            branch_class=BranchClass.SQUASH_MERGED,
            reason=f"tip matches the head of merged PR #{merged_match.number}",
            has_upstream=has_upstream,
            merged_pr_number=merged_match.number,
        )
    if not has_upstream:
        return BranchInfo(
            name=name,
            branch_class=BranchClass.REVIEW_FIRST,
            reason="never pushed anywhere, no associated PR",
            has_upstream=has_upstream,
        )
    if prs:
        # Pushed, has PR history, but none of it is OPEN or a tip-matching
        # MERGED record -- e.g. every associated PR was CLOSED without a
        # merge. Not provably safe to delete; surface for review rather
        # than guess.
        return BranchInfo(
            name=name,
            branch_class=BranchClass.REVIEW_FIRST,
            reason="pushed, has PR history, but no open or tip-matching merged PR",
            has_upstream=has_upstream,
        )
    return BranchInfo(
        name=name,
        branch_class=BranchClass.UNIQUE_WORK,
        reason="pushed, ahead of the default branch, no associated PR",
        has_upstream=has_upstream,
    )


def survey_local_branches(
    *,
    git_runner: GitRunner | None = None,
    gh_runner: GhRunner | None = None,
    project_root: str = ".",
) -> list[BranchInfo]:
    """Classify every local branch. Never deletes or modifies anything."""
    if git_runner is None:
        git_runner = default_git_runner(project_root)
    if gh_runner is None:
        gh_runner = default_gh_runner(project_root)

    default_branch = discover_default_branch(git_runner)
    worktree_branches = discover_worktree_branches(git_runner)
    local_branches = list_local_branches(git_runner)
    prs_by_branch = _fetch_prs_by_branch(gh_runner)

    infos: list[BranchInfo] = []
    for name in local_branches:
        is_default = name == default_branch
        in_worktree = name in worktree_branches
        tip = _branch_tip(git_runner, name)
        ancestor = (
            False
            if is_default
            else _is_ancestor_of_default(git_runner, name, default_branch)
        )
        has_upstream = _has_upstream(git_runner, name)
        prs = prs_by_branch.get(name, [])
        infos.append(
            classify_branch(
                name,
                is_default=is_default,
                in_worktree=in_worktree,
                is_ancestor_of_default=ancestor,
                has_upstream=has_upstream,
                tip=tip,
                prs=prs,
            )
        )
    return sorted(infos, key=lambda info: (info.branch_class.value, info.name))


def render_report_markdown(infos: typing.Sequence[BranchInfo]) -> str:
    lines = ["# Local branch hygiene survey", ""]
    lines.append("| Class | Branch | Delete-eligible | Reason |")
    lines.append("|---|---|---|---|")
    for info in infos:
        eligible = info.delete_flag or "no"
        row = f"| {info.branch_class.value} | `{info.name}` |"
        row += f" {eligible} | {info.reason} |"
        lines.append(row)
    lines.append("")
    return "\n".join(lines)


def render_delete_commands_file(infos: typing.Sequence[BranchInfo]) -> str:
    """Render a reviewable file of ``git branch`` delete commands.

    The default branch never appears in this output at all, not even as
    a comment -- deliberately stronger than "commented out," so there is
    no line a careless find-and-uncomment could ever turn into a command
    against the repository's own default branch. Delete-eligible classes
    (``merged_or_empty``, ``squash_merged``) get a live, ready-to-run
    command; every other non-default class gets a commented-out line for
    human review. This function only renders text -- it never executes
    anything.
    """
    lines = [
        "#!/bin/sh",
        "# Generated by `lrh branches survey --write-delete-commands`.",
        "# Review every line before running. Nothing here has been executed.",
        "# The discovered default branch is intentionally never listed.",
        "",
    ]
    for info in infos:
        if info.branch_class is BranchClass.DEFAULT:
            continue
        command = render_delete_command(info)
        if command is not None:
            lines.append(f"{command}  # {info.reason}")
        else:
            flag = "-D" if info.branch_class is BranchClass.SQUASH_MERGED else "-d"
            lines.append(
                f"# git branch {flag} -- {quote_branch_name(info.name)}"
                f"  # {info.branch_class.value}: {info.reason}"
            )
    lines.append("")
    return "\n".join(lines)
