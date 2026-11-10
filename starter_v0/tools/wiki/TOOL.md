---
name: wiki
track: bonus
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [title, lang]
outputs: [items, lang, is_disambiguation]
side_effect: false
---
# wiki

Returns a short encyclopedia summary (definition / background) for one concept,
person, organization or technology from the Wikipedia REST API
(`/api/rest_v1/page/summary/{title}`). No API key needed.

- Use for "X là gì", definitions, background, history.
- Not for recent news (use `lookup`), tweets (`social_search` / `timeline`) or a given URL (`fetch`).
- `lang`: `en` (default) or `vi`; any other value falls back to `en`.
- Output items use the same shape as other tools (`title`, `url`, `source`, `summary`),
  so they can be passed to `format` or `tool_new`.
- Never raises: empty/invalid title, 404 (`error: not_found`) and HTTP errors return an error dict.
