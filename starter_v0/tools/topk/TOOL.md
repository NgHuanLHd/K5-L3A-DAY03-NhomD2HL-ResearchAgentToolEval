---
name: topk
track: bonus
kind: local_formatter
requires_env: []
inputs: [items, n]
outputs: [items, kept_count, removed_count]
side_effect: false
---

# topk

Companion to `tool_new` (dedupe).

Keeps the `n` highest-`score` items already collected. It does not search or fetch.
Missing or invalid scores count as 0. Ties keep the original order.
