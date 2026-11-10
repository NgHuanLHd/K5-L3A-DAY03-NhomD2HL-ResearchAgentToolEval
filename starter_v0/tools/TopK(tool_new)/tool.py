from __future__ import annotations

from typing import Any

from tools._shared import err


def keep_topk(items: list[dict[str, Any]] | None = None, n: int = 3) -> dict[str, Any]:
    """Keep the n highest-score items already collected. Does not search or fetch."""
    try:
        if isinstance(n, bool) or not isinstance(n, (int, float)):
            raise ValueError("n must be an integer >= 1")
        if isinstance(n, float):
            if not n.is_integer():
                raise ValueError("n must be an integer >= 1")
            n = int(n)
        if n < 1:
            raise ValueError("n must be an integer >= 1")
        if items is None:
            items = []
        if not isinstance(items, list):
            raise TypeError("items must be a list")

        ranked: list[tuple[int, float, dict[str, Any]]] = []
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise TypeError("each item must be an object")
            raw = item.get("score", 0)
            try:
                score = float(raw) if raw is not None else 0.0
            except (TypeError, ValueError):
                score = 0.0
            ranked.append((index, score, item))
        ranked.sort(key=lambda row: (-row[1], row[0]))
        kept = [item for _, _, item in ranked[:n]]
        return {
            "tool": "topk",
            "n": n,
            "items": kept,
            "kept_count": len(kept),
            "removed_count": max(0, len(items) - len(kept)),
        }
    except Exception as exc:
        return err("topk", exc)
