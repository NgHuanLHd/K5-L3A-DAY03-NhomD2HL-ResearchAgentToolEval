from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from tools._shared import err

# Tiers follow company_policy/source-citation-policy.md:
#   tier1 = primary source (official blog, docs, paper, dataset, regulator)
#   tier2 = reputable reporting that links to primary evidence
#   tier3 = social / forum posts -> signal only, never confirmed fact
TIER1_DOMAINS = {
    "openai.com", "anthropic.com", "deepmind.google", "ai.google", "blog.google", "ai.meta.com",
    "microsoft.com", "nvidia.com", "huggingface.co", "mistral.ai", "x.ai",
    "arxiv.org", "nature.com", "science.org", "acm.org", "ieee.org", "openreview.net",
    "github.com", "wikipedia.org", "gov.vn", "europa.eu", "whitehouse.gov", "sec.gov",
}
TIER2_DOMAINS = {
    "reuters.com", "apnews.com", "bloomberg.com", "ft.com", "wsj.com", "nytimes.com", "bbc.com",
    "bbc.co.uk", "theguardian.com", "theverge.com", "techcrunch.com", "wired.com", "arstechnica.com",
    "technologyreview.com", "vnexpress.net", "tuoitre.vn", "thanhnien.vn", "vietnamnet.vn",
}
TIER3_DOMAINS = {
    "x.com", "twitter.com", "facebook.com", "reddit.com", "threads.net", "tiktok.com",
    "youtube.com", "linkedin.com", "medium.com", "substack.com", "quora.com", "t.me",
}
REASONS = {
    "tier1": "Nguồn gốc (primary): có thể trích dẫn làm bằng chứng chính.",
    "tier2": "Báo chí uy tín: dùng được, nên kèm link tới nguồn gốc nếu có.",
    "tier3": "Mạng xã hội / diễn đàn: chỉ là tín hiệu, không coi là fact khi chưa có nguồn tier 1–2.",
    "unknown": "Không có trong danh sách: cần kiểm chứng thêm trước khi trích dẫn.",
}
MAX_URLS = 20


def _domain_of(value: str) -> str:
    text = value.strip().lower()
    if not text:
        return ""
    if "://" not in text:
        text = "http://" + text
    host = urlparse(text).hostname or ""
    return host[4:] if host.startswith("www.") else host


def _tier_of(domain: str) -> str:
    for tier, domains in (("tier1", TIER1_DOMAINS), ("tier2", TIER2_DOMAINS), ("tier3", TIER3_DOMAINS)):
        if any(domain == d or domain.endswith("." + d) for d in domains):
            return tier
    return "unknown"


def check_sources(urls: list[str] | str | None = None) -> dict[str, Any]:
    """Rate each URL/domain by source tier. Offline, deterministic, never raises."""
    try:
        if isinstance(urls, str):
            urls = [urls]
        if not isinstance(urls, list) or not urls:
            raise ValueError("urls must be a non-empty list of URLs or domains")
        results = []
        for raw in urls[:MAX_URLS]:
            domain = _domain_of(raw) if isinstance(raw, str) else ""
            tier = _tier_of(domain) if domain else "unknown"
            results.append({
                "url": raw if isinstance(raw, str) else str(raw),
                "domain": domain,
                "tier": tier,
                "citable_as_fact": tier in {"tier1", "tier2"},
                "reason": REASONS[tier] if domain else "URL không hợp lệ.",
            })
        return {"tool": "source_check", "policy": "source-citation-policy", "results": results}
    except Exception as exc:
        return err("source_check", exc)
