"""Hermetic fixtures shared by the prototype's fake-backend tests."""

from __future__ import annotations

import itertools
import pathlib
import subprocess

READY_ITEM = """---
id: WI-T-1
title: "Ready fixture item"
type: deliverable
status: proposed
blocked: false
depends_on:
  - WI-T-0
related_design:
  - project/design/demo.md
---

# Ready fixture item

## Summary

Add a small feature.

## Scope

- One module.

## Required Changes

1. Change the module.

## Acceptance Criteria

- The feature works.

## Validation

- `scripts/test`
"""

THIN_ITEM = """---
id: WI-T-2
title: "Thin fixture item"
type: deliverable
status: proposed
blocked: false
---

# Thin fixture item

## Summary

An idea without a plan.
"""

DEPENDENCY_ITEM = """---
id: WI-T-0
title: "Dependency fixture item"
type: deliverable
status: proposed
blocked: false
---

# Dependency fixture item

## Summary

Must land first.
"""

DESIGN_DOC = "# Demo design\n\n" + "".join(f"Design line {n}.\n" for n in range(1, 41))


def run_git(root: pathlib.Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def make_repo(root: pathlib.Path, project_dir: str = ".") -> str:
    """Create a small Git repository with a control plane; return the commit."""
    base = root if project_dir in ("", ".") else root / project_dir
    files = {
        "project/work_items/proposed/WI-T-1.md": READY_ITEM,
        "project/work_items/proposed/WI-T-2.md": THIN_ITEM,
        "project/work_items/proposed/WI-T-0.md": DEPENDENCY_ITEM,
        "project/design/demo.md": DESIGN_DOC,
        "project/design/proposals/a/00_proposal.md": "# Proposal A\n",
        "project/design/proposals/b/00_proposal.md": "# Proposal B\n",
        "project/executions/AD_HOC/private.md": "private execution notes\n",
        "project/data.bin": "",
    }
    for relative, content in files.items():
        path = base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    (base / "project/data.bin").write_bytes(b"\x00\x01binary")
    run_git(root, "init", "-q")
    run_git(root, "config", "user.email", "test@example.com")
    run_git(root, "config", "user.name", "Test")
    run_git(root, "add", "-A")
    run_git(root, "commit", "-q", "-m", "fixture")
    return run_git(root, "rev-parse", "HEAD")


class SteppingClock:
    """Deterministic ISO timestamps that advance one second per call."""

    def __init__(self) -> None:
        self._counter = itertools.count(0)

    def __call__(self) -> str:
        second = next(self._counter)
        return f"2026-01-01T00:{second // 60:02d}:{second % 60:02d}+00:00"
