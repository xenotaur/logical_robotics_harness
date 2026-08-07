#!/usr/bin/env python3
"""Summarize saved Codex read_thread JSON pages without printing transcript text."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return data


def _iter_page_paths(inputs: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for input_path in inputs:
        if input_path.is_dir():
            paths.extend(sorted(input_path.glob("*.json")))
        else:
            paths.append(input_path)
    return paths


def summarize(paths: list[Path]) -> dict[str, Any]:
    page_count = 0
    turn_count = 0
    item_count = 0
    turn_statuses: Counter[str] = Counter()
    item_types: Counter[str] = Counter()
    page_orders: Counter[str] = Counter()
    has_more_count = 0
    thread_ids: set[str] = set()
    errors: list[str] = []

    for path in paths:
        try:
            page = _load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
            continue

        page_count += 1
        thread = page.get("thread")
        if isinstance(thread, dict) and isinstance(thread.get("id"), str):
            thread_ids.add(thread["id"])

        page_meta = page.get("page")
        if isinstance(page_meta, dict):
            order = page_meta.get("order")
            if isinstance(order, str):
                page_orders[order] += 1
            if page_meta.get("hasMore") is True:
                has_more_count += 1

        turns = page.get("turns")
        if not isinstance(turns, list):
            errors.append(f"{path}: missing or invalid turns list")
            continue

        for turn in turns:
            if not isinstance(turn, dict):
                item_count += 1
                item_types["<invalid-turn>"] += 1
                continue
            turn_count += 1
            status = turn.get("status")
            if isinstance(status, str):
                turn_statuses[status] += 1
            items = turn.get("items")
            if not isinstance(items, list):
                errors.append(f"{path}: turn {turn.get('id', '<unknown>')} has no items list")
                continue
            for item in items:
                item_count += 1
                if isinstance(item, dict) and isinstance(item.get("type"), str):
                    item_types[item["type"]] += 1
                else:
                    item_types["<invalid-item>"] += 1

    return {
        "pages": page_count,
        "threads": sorted(thread_ids),
        "turns": turn_count,
        "items": item_count,
        "turn_statuses": dict(sorted(turn_statuses.items())),
        "item_types": dict(sorted(item_types.items())),
        "page_orders": dict(sorted(page_orders.items())),
        "pages_with_has_more": has_more_count,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize saved codex_app.read_thread JSON pages without printing "
            "private message or transcript body text."
        )
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="JSON page files or directories containing JSON page files",
    )
    args = parser.parse_args()

    paths = _iter_page_paths(args.inputs)
    if not paths:
        parser.error("no JSON files found")

    print(json.dumps(summarize(paths), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
