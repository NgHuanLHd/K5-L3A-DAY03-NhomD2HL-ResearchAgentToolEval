---
name: source_check
track: bonus
kind: local_knowledge
requires_env: []
inputs: [urls]
outputs: [results]
side_effect: false
---
# source_check

Rates how trustworthy each source is from its URL or domain, using the tiers in
`company_policy/source-citation-policy.md`. Offline: it does not open the page.

- `tier1`: primary source (official blog, docs, paper, dataset, regulator), e.g. `openai.com`, `arxiv.org`.
- `tier2`: reputable reporting, e.g. `reuters.com`, `theverge.com`, `vnexpress.net`.
- `tier3`: social / forum posts (`x.com`, `reddit.com`...), signal only, never confirmed fact.
- `unknown`: not in the list, needs verification.

Domains are normalized (scheme, `www.`, case and path removed; subdomains match their parent).
A single string is accepted as a one-item list. At most 20 URLs per call.
Never raises: empty or wrong-typed input returns an error dict.
