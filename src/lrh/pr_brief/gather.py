"""Gather the machine-checkable facts behind a pull request briefing.

`gather_briefing_data` collects PR metadata, per-file change stats, CI and
review state, base-branch drift, and (optionally) a trial-merge conflict list
into one JSON-serializable dict. It also seeds an empty `briefing` section
that the `/lrh-pr-explain` skill fills with authored narrative before
`lrh pr-brief render` turns the whole document into HTML.

Every GitHub call goes through `gh_client`; the only git invocation is the
optional trial merge, which fetches objects (no ref updates beyond
FETCH_HEAD) and runs `git merge-tree`, so a caller's checkout is never
modified.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import subprocess
from typing import Any, Callable

from lrh.integrations.github import gh_client, pr_ref

SCHEMA_VERSION = 1

CATEGORIES = (
    {"key": "code", "label": "Code"},
    {"key": "scripts", "label": "Scripts and shell"},
    {"key": "tests", "label": "Tests"},
    {"key": "docs", "label": "Docs"},
    {"key": "config", "label": "Config and build"},
)

_PR_VIEW_FIELDS = (
    "number,title,url,author,state,isDraft,baseRefName,headRefName,"
    "baseRefOid,headRefOid,additions,deletions,changedFiles,commits,createdAt,"
    "updatedAt,mergeable,mergeStateStatus,reviewDecision,reviews,"
    "statusCheckRollup,body,labels"
)

_DOC_SUFFIXES = (".md", ".rst", ".adoc", ".txt")
_SCRIPT_SUFFIXES = (".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat")
_CONFIG_SUFFIXES = (
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".cfg",
    ".ini",
    ".lock",
    ".conf",
)
_CONFIG_NAMES = (
    "Dockerfile",
    "Makefile",
    "CODEOWNERS",
    "LICENSE",
    "requirements.txt",
    "package.json",
    "package-lock.json",
)

_PASSING_CONCLUSIONS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
_FAILING_CONCLUSIONS = {
    "FAILURE",
    "TIMED_OUT",
    "CANCELLED",
    "ACTION_REQUIRED",
    "STARTUP_FAILURE",
    "ERROR",
}

GitRunner = Callable[[list[str], pathlib.Path], subprocess.CompletedProcess]


def categorize_path(path: str) -> str:
    """Return the default briefing category key for a changed file path."""
    parts = path.split("/")
    name = parts[-1]
    lowered = [part.lower() for part in parts]
    stem = name.rsplit(".", 1)[0].lower()
    if (
        any(part in ("test", "tests", "__tests__", "spec", "specs") for part in lowered)
        or stem.startswith("test_")
        or stem.endswith(("_test", ".test", "_spec", ".spec"))
    ):
        return "tests"
    if name.lower().endswith(_DOC_SUFFIXES) or lowered[0] in ("docs", "doc"):
        return "docs"
    if name.lower().endswith(_SCRIPT_SUFFIXES):
        return "scripts"
    if (
        name.startswith(".")
        or lowered[0] in (".github", ".circleci", ".devcontainer")
        or name in _CONFIG_NAMES
        or name.lower().endswith(_CONFIG_SUFFIXES)
    ):
        return "config"
    return "code"


def resolve_ref(target: str, number: int | None = None) -> pr_ref.PullRequestRef:
    """Resolve a PR URL, `OWNER/REPO NUMBER`, or bare number in the cwd repo."""
    if target.startswith(("http://", "https://")):
        return pr_ref.parse_pull_request_url(target)
    if target.isdigit() and number is None:
        repo = gh_client.run_gh_json(["repo", "view", "--json", "nameWithOwner"])
        name_with_owner = str(repo.get("nameWithOwner", "")) if repo else ""
        return pr_ref.parse_pull_request_ref(name_with_owner, int(target))
    if number is None:
        raise ValueError("a PR number is required when target is OWNER/REPO")
    return pr_ref.parse_pull_request_ref(target, number)


def summarize_checks(rollup: list[dict[str, Any]] | None) -> dict[str, int]:
    """Count CI checks by outcome from a `statusCheckRollup` list."""
    counts = {"total": 0, "passing": 0, "failing": 0, "pending": 0}
    for item in rollup or []:
        counts["total"] += 1
        outcome = str(item.get("conclusion") or item.get("state") or "").upper()
        if outcome in _PASSING_CONCLUSIONS:
            counts["passing"] += 1
        elif outcome in _FAILING_CONCLUSIONS:
            counts["failing"] += 1
        else:
            counts["pending"] += 1
    return counts


def summarize_reviews(
    reviews: list[dict[str, Any]] | None, decision: str | None
) -> dict[str, Any]:
    """Summarize reviews using each reviewer's latest effective review.

    A reviewer's approval or change request stands until that reviewer
    approves, requests changes, or is dismissed again; later comment-only
    reviews do not replace it. `count` and `comments` cover all submissions.
    """
    summary: dict[str, Any] = {
        "decision": decision or "",
        "count": 0,
        "approvals": 0,
        "changes_requested": 0,
        "comments": 0,
    }
    effective: dict[str, str] = {}
    ordered = sorted(
        enumerate(reviews or []),
        key=lambda pair: (str(pair[1].get("submittedAt") or ""), pair[0]),
    )
    for index, review in ordered:
        summary["count"] += 1
        state = str(review.get("state", "")).upper()
        author = (review.get("author") or {}).get("login") or f"#{index}"
        if state in ("APPROVED", "CHANGES_REQUESTED"):
            effective[author] = state
        elif state == "DISMISSED":
            effective.pop(author, None)
        else:
            summary["comments"] += 1
    for state in effective.values():
        if state == "APPROVED":
            summary["approvals"] += 1
        else:
            summary["changes_requested"] += 1
    return summary


def parse_merge_tree_output(stdout: str, returncode: int) -> dict[str, Any]:
    """Parse `git merge-tree --write-tree --name-only --no-messages` output."""
    if returncode not in (0, 1):
        raise RuntimeError(f"git merge-tree exited with status {returncode}")
    lines = [line for line in stdout.splitlines() if line.strip()]
    files = sorted(set(lines[1:])) if returncode == 1 else []
    return {"checked": True, "clean": returncode == 0, "files": files}


def _run_git(argv: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *argv], cwd=cwd, check=False, capture_output=True, text=True
    )


def trial_merge(
    ref: pr_ref.PullRequestRef,
    base_sha: str,
    head_sha: str,
    repo_dir: pathlib.Path,
    *,
    run_git: GitRunner = _run_git,
) -> dict[str, Any]:
    """Merge head into base in memory and report conflicting files.

    Fetches the two commits by SHA from the PR's repository (objects only)
    and runs `git merge-tree`, which writes no working-tree or index state.
    """
    remote = f"https://github.com/{ref.owner}/{ref.repo}.git"
    fetch = run_git(
        ["fetch", "--quiet", "--no-tags", remote, base_sha, head_sha], repo_dir
    )
    if fetch.returncode != 0:
        detail = (fetch.stderr or "").strip().splitlines()[-1:] or ["fetch failed"]
        return {"checked": False, "clean": None, "files": [], "error": detail[0]}
    merge = run_git(
        [
            "merge-tree",
            "--write-tree",
            "--name-only",
            "--no-messages",
            base_sha,
            head_sha,
        ],
        repo_dir,
    )
    try:
        return parse_merge_tree_output(merge.stdout or "", merge.returncode)
    except RuntimeError as error:
        return {"checked": False, "clean": None, "files": [], "error": str(error)}


def _files_from_api(ref: pr_ref.PullRequestRef) -> list[dict[str, Any]]:
    stdout = gh_client.run_gh(
        [
            "api",
            f"repos/{ref.owner}/{ref.repo}/pulls/{ref.number}/files",
            "--paginate",
            "--jq",
            ".[] | {filename, status, additions, deletions, previous_filename, patch}",
        ]
    )
    return [json.loads(line) for line in stdout.splitlines() if line.strip()]


def _compare(ref: pr_ref.PullRequestRef, base: str, head_sha: str) -> dict[str, Any]:
    try:
        payload = gh_client.run_gh_json(
            [
                "api",
                f"repos/{ref.owner}/{ref.repo}/compare/{base}...{head_sha}",
                "--jq",
                "{ahead_by, behind_by, merge_base_sha: .merge_base_commit.sha, "
                "merge_base_date: .merge_base_commit.commit.committer.date}",
            ]
        )
    except RuntimeError as error:
        return {"error": str(error)}
    return payload if isinstance(payload, dict) else {}


def _base_tip(ref: pr_ref.PullRequestRef, base: str) -> tuple[str, str]:
    """Return `(sha, error)` for the base branch's current tip.

    `baseRefOid` can be months stale, so it is never used as a substitute.
    """
    try:
        sha = gh_client.run_gh(
            [
                "api",
                f"repos/{ref.owner}/{ref.repo}/git/ref/heads/{base}",
                "--jq",
                ".object.sha",
            ]
        ).strip()
    except RuntimeError as error:
        detail = str(error).strip().splitlines()[-1:] or ["lookup failed"]
        return "", f"could not resolve the current tip of {base}: {detail[0]}"
    if not sha:
        return "", f"could not resolve the current tip of {base}"
    return sha, ""


def _diff_text(ref: pr_ref.PullRequestRef, files: list[dict[str, Any]]) -> str:
    try:
        return gh_client.run_gh(
            ["pr", "diff", str(ref.number), "--repo", f"{ref.owner}/{ref.repo}"]
        )
    except RuntimeError:
        # GitHub refuses very large diffs; fall back to per-file patches.
        chunks = []
        for item in files:
            patch = item.get("patch")
            header = f"diff --git a/{item['filename']} b/{item['filename']}\n"
            body = patch if patch else "(patch unavailable from the files API)"
            chunks.append(header + body + "\n")
        return "".join(chunks)


def empty_briefing(files: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the authored-content skeleton the skill fills in."""
    return {
        "title": "",
        "headline_summary": "",
        "summary": [],
        "at_a_glance": [],
        "figures": [],
        "behavior_changes": [],
        "files": {
            item["path"]: {"gist": "", "points": [], "snippet": ""} for item in files
        },
        "tests": {"note": "", "rows": [], "gaps": []},
        "review_notes": [],
        "footer_note": "",
    }


def gather_briefing_data(
    ref: pr_ref.PullRequestRef,
    *,
    repo_dir: pathlib.Path | None = None,
    now: datetime.datetime | None = None,
    run_git: GitRunner = _run_git,
) -> tuple[dict[str, Any], str]:
    """Collect briefing facts for a PR; return `(data, diff_text)`."""
    view = gh_client.run_gh_json(
        [
            "pr",
            "view",
            str(ref.number),
            "--repo",
            f"{ref.owner}/{ref.repo}",
            "--json",
            _PR_VIEW_FIELDS,
        ]
    )
    if not isinstance(view, dict):
        raise RuntimeError("gh pr view returned an unexpected payload")
    api_files = _files_from_api(ref)
    files = [
        {
            "path": item["filename"],
            "status": item.get("status", "modified"),
            "additions": int(item.get("additions") or 0),
            "deletions": int(item.get("deletions") or 0),
            "previous_path": item.get("previous_filename") or "",
            "category": categorize_path(item["filename"]),
        }
        for item in api_files
    ]
    head_sha = str(view.get("headRefOid", ""))
    base = str(view.get("baseRefName", ""))
    base_sha = str(view.get("baseRefOid", ""))
    tip_error = "no base branch reported"
    if base:
        tip_sha, tip_error = _base_tip(ref, base)
        base_sha = tip_sha or base_sha
    compare = _compare(ref, base, head_sha) if base and head_sha else {}
    if tip_error:
        # Never trial-merge against the PR's recorded base: it can be stale.
        # Record the reason even without --repo-dir, since pr.base_sha is then
        # that recorded base rather than the current tip.
        conflicts = {"checked": False, "clean": None, "files": [], "error": tip_error}
    elif repo_dir is None or not head_sha:
        conflicts = {"checked": False, "clean": None, "files": []}
    else:
        conflicts = trial_merge(ref, base_sha, head_sha, repo_dir, run_git=run_git)
    author = view.get("author") or {}
    timestamp = (now or datetime.datetime.now(datetime.timezone.utc)).isoformat(
        timespec="seconds"
    )
    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": timestamp,
        "pr": {
            "repo": f"{ref.owner}/{ref.repo}",
            "number": ref.number,
            "url": view.get("url", ""),
            "title": view.get("title", ""),
            "author_login": author.get("login", ""),
            "author_name": author.get("name", ""),
            "state": view.get("state", ""),
            "is_draft": bool(view.get("isDraft")),
            "base": base,
            "head": view.get("headRefName", ""),
            "base_sha": base_sha,
            "base_sha_is_tip": not tip_error,
            "head_sha": head_sha,
            "created_at": view.get("createdAt", ""),
            "updated_at": view.get("updatedAt", ""),
            "additions": int(view.get("additions") or 0),
            "deletions": int(view.get("deletions") or 0),
            "changed_files": int(view.get("changedFiles") or len(files)),
            "commits": [
                {
                    "sha": str(commit.get("oid", ""))[:12],
                    "headline": commit.get("messageHeadline", ""),
                }
                for commit in view.get("commits") or []
            ],
            "labels": [label.get("name", "") for label in view.get("labels") or []],
            "body": view.get("body") or "",
        },
        "status": {
            "mergeable": view.get("mergeable", ""),
            "merge_state": view.get("mergeStateStatus", ""),
            "checks": summarize_checks(view.get("statusCheckRollup")),
            "reviews": summarize_reviews(
                view.get("reviews"), view.get("reviewDecision")
            ),
            "ahead_by": compare.get("ahead_by"),
            "behind_by": compare.get("behind_by"),
            "merge_base_sha": compare.get("merge_base_sha", ""),
            "merge_base_date": compare.get("merge_base_date", ""),
            "conflicts": conflicts,
        },
        "categories": [dict(category) for category in CATEGORIES],
        "files": files,
        "briefing": empty_briefing(files),
    }
    return data, _diff_text(ref, api_files)
