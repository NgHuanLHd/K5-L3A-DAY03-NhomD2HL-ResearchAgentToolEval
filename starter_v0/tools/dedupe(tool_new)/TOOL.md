---
name: tool_new
track: bonus
kind: local_formatter
requires_env: []
inputs: [items, key]
outputs: [items, kept_count, removed_count]
side_effect: false
---

# tool_new

Removes duplicate research items that were already collected. It does not search or fetch.
Keep the first item for each `url` or `title`.
