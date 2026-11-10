"""TODO(student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO(student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    # Call clarify with response_type="choice" and 2 options.
    # Assert: options are returned unchanged, awaiting_user is True.
    pytest.skip(TODO)


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    # Items with section "A", "B", "A" -> markdown has exactly one "## A" and one "## B".
    pytest.skip(TODO)


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    pytest.skip(TODO)


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    pytest.skip(TODO)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    pytest.skip(TODO)


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    pytest.skip(TODO)


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    pytest.skip(TODO)


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    pytest.skip(TODO)


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    # Mock {"timeline": [...]} with 1 item missing tweet_id and 6 valid items, limit=3.
    # Assert 3 items, and each url looks like https://x.com/<handle>/status/<id>.
    pytest.skip(TODO)


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    pytest.skip(TODO)


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    pytest.skip(TODO)


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    pytest.skip(TODO)


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    pytest.skip(TODO)


# ---------------- tool_new ----------------

tool_new_fn = TOOL_FUNCTIONS["tool_new"]


def test_tool_new_keeps_first_url_and_counts_removed() -> None:
    items = [
        {"title": "A", "url": "https://openai.com/a"},
        {"title": "A again", "url": "https://openai.com/a/"},
        {"title": "B", "url": "https://example.com/b"},
    ]
    result = tool_new_fn(items=items, key="url")
    assert result["removed_count"] == 1
    assert result["kept_count"] == 2
    assert [item["title"] for item in result["items"]] == ["A", "B"]


def test_tool_new_rejects_key_outside_enum() -> None:
    result = tool_new_fn(items=[{"url": "https://x.com"}], key="author")
    assert result["error"] == "ValueError"
    assert "key" in result["message"]


def test_tool_new_bad_items_returns_error_dict() -> None:
    result = tool_new_fn(items="not-a-list", key="url")
    assert result["error"] == "TypeError"
    assert "items" in result["message"]


# ---------------- wiki ----------------

wiki_fn = TOOL_FUNCTIONS["wiki"]

WIKI_TRANSFORMER = {
    "type": "standard",
    "title": "Transformer (deep learning architecture)",
    "extract": "A transformer is a deep learning architecture based on the multi-head attention mechanism.",
    "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)"}},
}


def test_wiki_requests_summary_endpoint_and_maps_item(fake_http) -> None:
    calls = fake_http(FakeResponse(WIKI_TRANSFORMER))

    result = wiki_fn(title="Transformer (deep learning architecture)")

    assert len(calls) == 1
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == (
        "https://en.wikipedia.org/api/rest_v1/page/summary/Transformer_%28deep_learning_architecture%29"
    )
    assert "User-Agent" in calls[0]["headers"]
    assert result["lang"] == "en"
    assert result["is_disambiguation"] is False
    assert result["items"] == [{
        "title": "Transformer (deep learning architecture)",
        "url": "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)",
        "source": "en.wikipedia.org",
        "summary": WIKI_TRANSFORMER["extract"],
    }]


def test_wiki_empty_title_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse(WIKI_TRANSFORMER))

    for bad in ["", "   ", None, 123]:
        result = wiki_fn(title=bad)
        assert result["tool"] == "wiki"
        assert result["error"] in {"ValueError", "TypeError"}

    assert calls == []


def test_wiki_unknown_lang_falls_back_to_english(fake_http) -> None:
    calls = fake_http(FakeResponse(WIKI_TRANSFORMER))

    result = wiki_fn(title="OpenAI", lang="fr")

    assert calls[0]["url"].startswith("https://en.wikipedia.org/")
    assert result["lang"] == "en"


def test_wiki_vietnamese_title_is_url_encoded(fake_http) -> None:
    calls = fake_http(FakeResponse({"title": "Trí tuệ nhân tạo", "extract": "AI"}))

    wiki_fn(title="  Trí tuệ   nhân tạo ", lang="vi")

    assert calls[0]["url"] == (
        "https://vi.wikipedia.org/api/rest_v1/page/summary/Tr%C3%AD_tu%E1%BB%87_nh%C3%A2n_t%E1%BA%A1o"
    )


def test_wiki_missing_page_returns_not_found_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=404))

    result = wiki_fn(title="Definitely not a real article xyz")

    assert result["error"] == "not_found"
    assert "Definitely not a real article xyz" in result["message"]


def test_wiki_vi_miss_retries_english_once(monkeypatch) -> None:
    # Regression: in the UI the model sent title="Artificial Intelligence", lang="vi" -> 404.
    import requests

    responses = [FakeResponse(status_code=404), FakeResponse(WIKI_TRANSFORMER)]
    calls: list[str] = []

    def _fake_get(url, **kwargs):
        calls.append(url)
        return responses.pop(0)

    monkeypatch.setattr(requests, "get", _fake_get)

    result = wiki_fn(title="Artificial Intelligence", lang="vi")

    assert calls == [
        "https://vi.wikipedia.org/api/rest_v1/page/summary/Artificial_Intelligence",
        "https://en.wikipedia.org/api/rest_v1/page/summary/Artificial_Intelligence",
    ]
    assert result["lang"] == "en"
    assert result["fallback_from"] == "vi"
    assert result["items"][0]["source"] == "en.wikipedia.org"


def test_wiki_vi_and_en_both_missing_returns_not_found(fake_http) -> None:
    calls = fake_http(FakeResponse(status_code=404))

    result = wiki_fn(title="Zzqx", lang="vi")

    assert len(calls) == 2
    assert result["error"] == "not_found"
    assert "(vi)" in result["message"]


def test_wiki_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=429))
    assert wiki_fn(title="OpenAI")["error"] == "HTTPError"


def test_wiki_long_extract_is_truncated(fake_http) -> None:
    fake_http(FakeResponse({"title": "Long", "extract": "x" * 3000}))

    summary = wiki_fn(title="Long")["items"][0]["summary"]

    assert len(summary) == 1500
    assert summary.endswith("...")
