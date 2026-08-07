"""Probe Codex app-server stdio thread APIs without printing transcript text."""

from __future__ import annotations

import argparse
import json
import os
import selectors
import subprocess
import sys
import time
from collections import Counter
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
    summary: dict[str, Any] = {
        "id": thread.get("id"),
        "name_present": bool(thread.get("name")),
        "ephemeral": thread.get("ephemeral"),
        "status_type": status.get("type") if isinstance(status, dict) else None,
        "keys": sorted(thread.keys()),
        "turns_present": isinstance(turns, list),
        "turn_count": len(turns) if isinstance(turns, list) else None,
    }
    if isinstance(turns, list):
        summary["turn_summary"] = _summarize_turns(turns)
    return summary


def _summarize_turns(turns: list[Any]) -> dict[str, Any]:
    item_types: Counter[str] = Counter()
    item_key_sets: Counter[str] = Counter()
    turn_statuses: Counter[str] = Counter()
    max_items_per_turn = 0
    sample_turns = []

    for turn in turns:
        if not isinstance(turn, dict):
            continue
        status = turn.get("status")
        if isinstance(status, str):
            turn_statuses[status] += 1
        items = turn.get("items")
        if isinstance(items, list):
            max_items_per_turn = max(max_items_per_turn, len(items))
            for item in items:
                if isinstance(item, dict):
                    item_type = item.get("type")
                    if isinstance(item_type, str):
                        item_types[item_type] += 1
                    item_key_sets[",".join(sorted(item.keys()))] += 1
        if len(sample_turns) < 3:
            sample_turns.append(_summarize_one_turn(turn))

    return {
        "count": len(turns),
        "item_types": dict(sorted(item_types.items())),
        "item_key_sets": dict(sorted(item_key_sets.items())),
        "max_items_per_turn": max_items_per_turn,
        "sample_turns": sample_turns,
        "turn_statuses": dict(sorted(turn_statuses.items())),
    }


def _summarize_one_turn(turn: dict[str, Any]) -> dict[str, Any]:
    items = turn.get("items")
    item_types = []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                item_types.append(item.get("type"))
            else:
                item_types.append(type(item).__name__)
    return {
        "id": turn.get("id"),
        "keys": sorted(turn.keys()),
        "status": turn.get("status"),
        "item_count": len(items) if isinstance(items, list) else None,
        "item_types": item_types,
    }


def _send_request(
    proc: subprocess.Popen[str],
    selector: selectors.BaseSelector,
    *,
    request: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    request_id = request.get("id")
    while True:
        response = _read_json_line(proc, selector, timeout_seconds=timeout_seconds)
        if response.get("id") == request_id:
            return response


def _summarize_response(
    response: dict[str, Any],
    *,
    label: str,
    method: str,
    request_params: dict[str, Any],
) -> dict[str, Any]:
    if "error" in response:
        return {
            "label": label,
            "method": method,
            "ok": False,
            "error_code": response.get("error", {}).get("code")
            if isinstance(response.get("error"), dict)
            else None,
            "error_message": response.get("error", {}).get("message")
            if isinstance(response.get("error"), dict)
            else None,
        }

    result = response.get("result")
    if not isinstance(result, dict):
        return {
            "label": label,
            "method": method,
            "ok": False,
            "error": "missing result object",
        }

    summary: dict[str, Any] = {
        "label": label,
        "method": method,
        "ok": True,
        "request_params": request_params,
        "result_keys": sorted(result.keys()),
    }

    thread = result.get("thread")
    if isinstance(thread, dict):
        summary["thread"] = _summarize_thread(thread)

    data = result.get("data")
    if isinstance(data, list):
        summary["data_count"] = len(data)
        summary["turn_summary"] = _summarize_turns(data)

    for cursor_key in ("nextCursor", "backwardsCursor"):
        if cursor_key in result:
            summary[f"{cursor_key}_present"] = bool(result.get(cursor_key))

    return summary


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
    parser.add_argument(
        "--mode",
        choices=("thread-read", "compare"),
        default="thread-read",
        help="Run one stable thread/read probe or compare multiple turn-data routes.",
    )
    parser.add_argument(
        "--turn-limit",
        type=int,
        default=5,
        help="Limit for thread/turns/list comparison requests.",
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
                },
                "capabilities": {"experimentalApi": True},
            },
        }
        init_response = _send_request(
            proc,
            selector,
            request=initialize,
            timeout_seconds=args.timeout_seconds,
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
        proc.stdin.flush()

        requests = [
            (
                "thread-read",
                "thread/read",
                {"threadId": args.thread_id, "includeTurns": bool(args.include_turns)},
            )
        ]
        if args.mode == "compare":
            requests = [
                (
                    "stable-thread-read-include-turns",
                    "thread/read",
                    {"threadId": args.thread_id, "includeTurns": True},
                ),
                (
                    "paged-turns-not-loaded",
                    "thread/turns/list",
                    {
                        "threadId": args.thread_id,
                        "limit": args.turn_limit,
                        "sortDirection": "desc",
                        "itemsView": "notLoaded",
                    },
                ),
                (
                    "paged-turns-summary",
                    "thread/turns/list",
                    {
                        "threadId": args.thread_id,
                        "limit": args.turn_limit,
                        "sortDirection": "desc",
                        "itemsView": "summary",
                    },
                ),
                (
                    "paged-turns-full",
                    "thread/turns/list",
                    {
                        "threadId": args.thread_id,
                        "limit": min(args.turn_limit, 2),
                        "sortDirection": "desc",
                        "itemsView": "full",
                    },
                ),
            ]

        summaries = []
        for index, (label, method, params) in enumerate(requests, start=1):
            response = _send_request(
                proc,
                selector,
                request={"method": method, "id": index, "params": params},
                timeout_seconds=args.timeout_seconds,
            )
            summaries.append(
                _summarize_response(
                    response, label=label, method=method, request_params=params
                )
            )
            if args.mode == "compare" and label == "paged-turns-summary":
                next_cursor = response.get("result", {}).get("nextCursor")
                if isinstance(next_cursor, str) and next_cursor:
                    page_2_params = {
                        **params,
                        "cursor": next_cursor,
                    }
                    page_2_response = _send_request(
                        proc,
                        selector,
                        request={
                            "method": "thread/turns/list",
                            "id": len(requests) + 1,
                            "params": page_2_params,
                        },
                        timeout_seconds=args.timeout_seconds,
                    )
                    summaries.append(
                        _summarize_response(
                            page_2_response,
                            label="paged-turns-summary-page-2",
                            method="thread/turns/list",
                            request_params={
                                **params,
                                "cursor_present": True,
                            },
                        )
                    )

        print(
            json.dumps(
                {"ok": all(s["ok"] for s in summaries), "probes": summaries},
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
