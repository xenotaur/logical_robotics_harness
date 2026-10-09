"""Backend-neutral VCS action interface and the SHA-locked merge action.

A *backend* knows how to talk to one concrete forge (GitHub via ``gh`` today).
An *action* is a stereotyped operation LRH skills perform after their own gates
have already run -- currently only the SHA-locked pull-request merge. Keeping
the action's safety checks here, and only the forge calls in the backend, is
what lets a different backend plug in without redoing the checks.

This module never decides *whether* a merge is authorized. Authorization stays
in the calling skill's human gate (``DEC-AGENT-EXECUTED-MERGE-GATE``); this
module only refuses to act on something other than what that gate verified.

Error scope: everything raised here is an error the backend could actually
observe (a subprocess exit, unreadable output) or a precondition refusal. A
host-level denial that stops the whole command from launching never reaches
this code and is the calling skill's or session's to report.
"""

from __future__ import annotations

import dataclasses
import re
import typing

MERGE_MODES = ("merge", "squash", "rebase")

_FULL_SHA = re.compile(r"[0-9a-f]{40}")


class VcsError(RuntimeError):
    """An error the backend actually observed."""


class MergeRefusedError(VcsError):
    """A precondition failed, so no merge command was issued."""


class MergeVerificationError(VcsError):
    """A merge was issued but its final state is unconfirmed.

    Either the read-back failed, or it showed a state other than MERGED or OPEN.
    """


@dataclasses.dataclass(frozen=True)
class PullRequestInfo:
    """The pull-request facts the locked merge needs."""

    url: str
    state: str
    head_sha: str
    merge_commit: str | None


@dataclasses.dataclass(frozen=True)
class MergeOutcome:
    """Result of an issued merge: ``merged`` is confirmed, ``queued`` is not."""

    status: str
    state: str
    merge_commit: str | None


class VcsBackend(typing.Protocol):
    """What a forge backend must provide for the locked merge action."""

    name: str

    def get_pull_request(self, pr: str) -> PullRequestInfo:
        """Return the pull request's current state, head SHA and merge commit."""
        ...

    def merge_pull_request(self, pr: str, *, mode: str, match_head_commit: str) -> None:
        """Merge ``pr`` only if its head is still ``match_head_commit``."""
        ...


def merge_pull_request_locked(
    backend: VcsBackend, pr: str, *, mode: str, match_head_commit: str
) -> MergeOutcome:
    """Merge ``pr`` at exactly ``match_head_commit``, then report what happened.

    Refuses before issuing any command if the inputs are malformed, the PR is
    not open, or its head is not the commit that was verified. Issues the merge
    once, never retries, and reads the PR back so a queued merge is reported as
    ``queued`` rather than mistaken for ``merged``. If the merge call itself
    fails, the error also reports the PR's state, because the call can fail
    after the forge accepted it.
    """
    if not pr or pr.startswith("-"):
        raise MergeRefusedError("pull request reference must be a URL, not an option")
    if mode not in MERGE_MODES:
        raise MergeRefusedError(f"merge mode must be one of {', '.join(MERGE_MODES)}")
    if not _FULL_SHA.fullmatch(match_head_commit):
        raise MergeRefusedError(
            "--match-head-commit must be a full 40-character lowercase hex SHA"
        )

    try:
        before = backend.get_pull_request(pr)
    except VcsError:
        raise
    except Exception as err:
        raise VcsError(
            f"could not read the pull request, so no merge was issued: {_describe(err)}"
        ) from err
    if before.state != "OPEN":
        raise MergeRefusedError(f"pull request is {before.state}, not OPEN")
    if before.head_sha != match_head_commit:
        raise MergeRefusedError(
            f"pull request head is {before.head_sha}, not the verified "
            f"{match_head_commit}; refusing to merge an unverified commit"
        )

    try:
        backend.merge_pull_request(pr, mode=mode, match_head_commit=match_head_commit)
    except Exception as err:
        raise VcsError(
            f"{_describe(err)}; {_state_after_failure(backend, pr)}"
        ) from err

    try:
        after = backend.get_pull_request(pr)
    except Exception as err:
        raise MergeVerificationError(
            f"merge command was issued but the final state could not be read "
            f"({_describe(err)}); check the pull request's state before proceeding"
        ) from err
    if after.state == "MERGED":
        return MergeOutcome("merged", after.state, after.merge_commit)
    if after.state == "OPEN":
        return MergeOutcome("queued", after.state, None)
    raise MergeVerificationError(
        f"merge command was issued but the pull request is {after.state}, "
        "not MERGED or OPEN; check it before proceeding"
    )


def _state_after_failure(backend: VcsBackend, pr: str) -> str:
    """Describe the pull request after a failed merge call, without retrying it.

    A merge command can fail after the forge already accepted it, so the bare
    error does not say whether anything merged. One read is safe to add.
    """
    try:
        info = backend.get_pull_request(pr)
    except Exception as read_err:
        return (
            f"its state could not be read afterwards either ({_describe(read_err)}); "
            "check the pull request before proceeding"
        )
    return f"the pull request is now {info.state}"


def _describe(err: Exception) -> str:
    # Backends are pluggable, so any exception type must be reported as a backend
    # error: an unhandled one would exit 1, which the CLI documents as "queued".
    if isinstance(err, VcsError):
        return str(err)
    return f"{type(err).__name__}: {err}"
