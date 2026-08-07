"""Probe Codex app-server stdio thread/read without printing transcript text."""

from __future__ import annotations

import argparse
import json
import os
import selectors
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def _read_json_line(
    proc: subprocess.Popen[str],
    selector: selectors.BaseSelector,
    *,
    timeout_seconds: float,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        remaining = max(0.0, deadline - time.monotonic())
        events = selector.select(timeout=min(remaining, 0.25))
        if not events:
            if proc.poll() is not None:
                raise RuntimeError(f"app-server exited before response: {proc.returncode}")
            continue
        line = proc.stdout.readline() if proc.stdout else ""
        if not line:
            continue
        return json.loads(line)
    raise TimeoutError("timed out waiting for app-server response")


def _summarize_thread(thread: dict[str, Any]) -> dict[str, Any]:
    turns = thread.get("turns")
    status = thread.get("status")
    return {
        "id": thread.get("id"),
        "name_present": bool(thread.get("name")),
        "ephemeral": thread.get("ephemeral"),
        "status_type": status.get("type") if isinstance(status, dict) else None,
        "keys": sorted(thread.keys()),
        "turns_present": isinstance(turns, list),
        "turn_count": len(turns) if isinstance(turns, list) else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--codex",
        default="/opt/homebrew/bin/codex",
        help="Path to the Codex executable to probe.",
    )
    parser.add_argument(
        "--thread-id",
        default=os.environ.get("CODEX_THREAD_ID"),
        help="Stored Codex thread id to read.",
    )
    parser.add_argument(
        "--include-turns",
        action="store_true",
        help="Request full turns. Default is summary-only for safety.",
    )
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    args = parser.parse_args()

    if not args.thread_id:
        print("CODEX_THREAD_ID is required", file=sys.stderr)
        return 2

    codex = Path(args.codex)
    if not codex.exists():
        print(f"Codex executable does not exist: {codex}", file=sys.stderr)
        return 2

    proc = subprocess.Popen(
        [str(codex), "app-server", "--listen", "stdio://"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    selector = selectors.DefaultSelector()
    assert proc.stdout is not None
    selector.register(proc.stdout, selectors.EVENT_READ)

    try:
        assert proc.stdin is not None
        initialize = {
            "method": "initialize",
            "id": 0,
            "params": {
                "clientInfo": {
                    "name": "lrh_codex_export_spike",
                    "title": "LRH Codex Export Spike",
                    "version": "0.0.0",
                }
            },
        }
        proc.stdin.write(json.dumps(initialize) + "\n")
        proc.stdin.flush()
        init_response = _read_json_line(
            proc, selector, timeout_seconds=args.timeout_seconds
        )
        if init_response.get("id") != 0 or "error" in init_response:
            print(
                json.dumps(
                    {"ok": False, "stage": "initialize", "response": init_response},
                    sort_keys=True,
                )
            )
            return 1

        proc.stdin.write(json.dumps({"method": "initialized", "params": {}}) + "\n")
        read_request = {
            "method": "thread/read",
            "id": 1,
            "params": {
                "threadId": args.thread_id,
                "includeTurns": bool(args.include_turns),
            },
        }
        proc.stdin.write(json.dumps(read_request) + "\n")
        proc.stdin.flush()

        while True:
            read_response = _read_json_line(
                proc, selector, timeout_seconds=args.timeout_seconds
            )
            if read_response.get("id") == 1:
                break

        if "error" in read_response:
            print(
                json.dumps(
                    {"ok": False, "stage": "thread/read", "response": read_response},
                    sort_keys=True,
                )
            )
            return 1

        thread = read_response.get("result", {}).get("thread")
        if not isinstance(thread, dict):
            print(
                json.dumps(
                    {
                        "ok": False,
                        "stage": "thread/read",
                        "error": "missing thread object",
                    },
                    sort_keys=True,
                )
            )
            return 1

        print(
            json.dumps(
                {
                    "ok": True,
                    "include_turns": bool(args.include_turns),
                    "thread": _summarize_thread(thread),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    finally:
        selector.close()
        if proc.stdin:
            proc.stdin.close()
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)


if __name__ == "__main__":
    raise SystemExit(main())
