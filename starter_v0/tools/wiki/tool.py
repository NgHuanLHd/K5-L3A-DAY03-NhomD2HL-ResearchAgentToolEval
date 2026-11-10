from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

SUMMARY_URL = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
USER_AGENT = "AI20k-Day03-Research-Agent/1.0 (educational lab)"
SUPPORTED_LANGS = {"en", "vi"}
MAX_SUMMARY_CHARS = 1500


def _normalize_title(title: Any) -> str:
    if not isinstance(title, str):
        raise TypeError("title must be a string")
    cleaned = " ".join(title.split())
    if not cleaned:
        raise ValueError("title is empty")
    return cleaned


def _get_summary(title: str, lang: str) -> tuple[str, requests.Response]:
    url = SUMMARY_URL.format(lang=lang, title=quote(title.replace(" ", "_"), safe=""))
    return url, requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=TIMEOUT)


def wiki_summary(title: str = "", lang: str = "en") -> dict[str, Any]:
    """Return a short Wikipedia summary for one concept / person / organization.

    If a non-English lookup finds no article (e.g. the model sends an English title
    with lang="vi"), it retries once on English Wikipedia.
    Never raises: bad input, missing pages and HTTP errors come back as an error dict.
    """
    try:
        clean_title = _normalize_title(title)
        lang = lang if lang in SUPPORTED_LANGS else "en"
        requested_lang = lang
        url, response = _get_summary(clean_title, lang)
        if response.status_code == 404 and lang != "en":
            lang = "en"
            url, response = _get_summary(clean_title, lang)
        if response.status_code == 404:
            return {
                "tool": "wiki",
                "error": "not_found",
                "message": f"No Wikipedia ({requested_lang}) article titled '{clean_title}'. Try a more specific or English title.",
            }
        response.raise_for_status()
        data = response.json()

        summary = (data.get("extract") or "").strip()
        if len(summary) > MAX_SUMMARY_CHARS:
            summary = summary[: MAX_SUMMARY_CHARS - 3] + "..."
        page_url = ((data.get("content_urls") or {}).get("desktop") or {}).get("page") or url
        result: dict[str, Any] = {
            "tool": "wiki",
            "lang": lang,
            "is_disambiguation": data.get("type") == "disambiguation",
            "items": [{
                "title": data.get("title") or clean_title,
                "url": page_url,
                "source": f"{lang}.wikipedia.org",
                "summary": summary,
            }],
        }
        if lang != requested_lang:
            result["fallback_from"] = requested_lang
        return result
    except Exception as exc:
        return err("wiki", exc)
