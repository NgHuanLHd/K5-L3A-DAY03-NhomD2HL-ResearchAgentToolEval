from __future__ import annotations

from typing import Any

from tools._shared import err


def dedupe_items(items: list[dict[str, Any]] | None = None, key: str = "url") -> dict[str, Any]:
    """Drop duplicate research items. Keep the first occurrence of each key."""
    try:
        if key not in ("url", "title"):
            raise ValueError("key must be 'url' or 'title'")
        if items is None:
            items = []
        if not isinstance(items, list):
            raise TypeError("items must be a list")
        seen: set[str] = set()
        kept: list[dict[str, Any]] = []
        removed = 0
        for item in items:
            if not isinstance(item, dict):
                raise TypeError("each item must be an object")
            raw = str(item.get(key) or "").strip().lower().rstrip("/")
            if raw and raw in seen:
                removed += 1
                continue
            if raw:
                seen.add(raw)
            kept.append(item)
        return {
            "tool": "tool_new",
            "key": key,
            "items": kept,
            "kept_count": len(kept),
            "removed_count": removed,
        }
    except Exception as exc:
        return err("tool_new", exc)
