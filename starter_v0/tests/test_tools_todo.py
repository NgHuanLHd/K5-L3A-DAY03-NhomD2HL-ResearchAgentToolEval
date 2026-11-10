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

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO(student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    options = ["Tin web", "Tweet"]
    result = TOOL_FUNCTIONS["clarify"](question="Bạn muốn nguồn nào?", response_type="choice", options=options)

    assert result["response_type"] == "choice"
    assert result["options"] == ["Tin web", "Tweet"]
    assert result["question"] == "Bạn muốn nguồn nào?"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "a1", "url": "https://a.com/1", "section": "A"},
        {"title": "b1", "url": "https://b.com/1", "section": "B"},
        {"title": "a2", "url": "https://a.com/2", "section": "A"},
    ]
    markdown = TOOL_FUNCTIONS["format"](items=items, template="sections")["markdown"]

    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1
    assert markdown.index("a2") < markdown.index("## B")  # both A items stay under the A heading


def test_format_thread_numbers_items() -> None:
    items = [{"title": f"Tin {i}", "url": f"https://x.com/{i}"} for i in range(3)]
    markdown = TOOL_FUNCTIONS["format"](items=items, template="thread")["markdown"]

    lines = [line for line in markdown.split("\n") if line.strip()]
    assert [line.split(" ", 1)[0] for line in lines] == ["1/", "2/", "3/"]


def test_format_empty_items_does_not_crash() -> None:
    for empty in (None, []):
        result = TOOL_FUNCTIONS["format"](items=empty, template="sections")
        assert result["item_count"] == 0
        assert isinstance(result["markdown"], str)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-1001")
    calls = fake_http(FakeResponse({"ok": True}))

    result = TOOL_FUNCTIONS["send"](text="Bản tin AI", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "bot123:abc/sendMessage" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-1001"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))

    result = TOOL_FUNCTIONS["send"](text="Bản tin AI", confirmed=True)

    assert calls == []
    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))

    TOOL_FUNCTIONS["lookup"](query="AI", topic="general", timeframe=None)

    assert "time_range" not in calls[0]["json"]
    assert calls[0]["json"]["query"] == "AI"


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "Nội dung bài",
        "metadata": {"title": "T", "sourceURL": "https://www.openai.com/blog/x"},
    }}))

    result = TOOL_FUNCTIONS["fetch"](url="https://openai.com/blog/x")

    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["json"]["url"] == "https://openai.com/blog/x"
    assert result["items"][0] == {
        "title": "T",
        "url": "https://www.openai.com/blog/x",
        "source": "openai.com",
        "summary": "Nội dung bài",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000, "metadata": {}}}))

    summary = TOOL_FUNCTIONS["fetch"](url="https://example.com")["items"][0]["summary"]

    assert len(summary) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rk")
    raw = [{"text": "no id", "screen_name": "sama"}]
    raw += [{"tweet_id": str(100 + i), "text": f"tweet {i}", "screen_name": "sama"} for i in range(6)]
    calls = fake_http(FakeResponse({"timeline": raw}))

    result = TOOL_FUNCTIONS["timeline"](screenname="sama", limit=3)

    assert calls[0]["params"] == {"screenname": "sama"}
    assert len(result["items"]) == 3
    assert [item["url"] for item in result["items"]] == [
        "https://x.com/sama/status/100",
        "https://x.com/sama/status/101",
        "https://x.com/sama/status/102",
    ]


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rk")
    calls = fake_http(FakeResponse({"timeline": []}))

    result = TOOL_FUNCTIONS["social_search"](query="OpenAI", search_type="Top", limit=5)

    assert calls[0]["url"].endswith("/search.php")
    assert calls[0]["params"] == {"query": "OpenAI", "search_type": "Top"}
    assert result["search_type"] == "Top"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    for empty in ("", "   ", "là gì"):  # stopwords only -> no search terms
        assert TOOL_FUNCTIONS["policy"](query=empty)["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = TOOL_FUNCTIONS["policy"](query="API key dữ liệu khách hàng", policy_area="data_privacy", top_k=5)

    assert result["results"]
    assert {hit["policy_area"] for hit in result["results"]} == {"data_privacy"}


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = TOOL_FUNCTIONS["policy"](query="viral tweet citation verified fact", policy_area="source_citation", top_k=10)

    flagged = [hit for hit in result["results"] if any("viral tweet" in line for line in hit["untrusted_text"])]
    assert flagged, "the instruction-like line should be returned as untrusted_text"
    for hit in result["results"]:
        assert "ignore the citation policy" not in hit["facts"].lower()


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


# ---------------- topk ----------------

topk_fn = TOOL_FUNCTIONS["topk"]


def test_topk_keeps_highest_scores_in_score_order() -> None:
    items = [
        {"title": "low", "score": 0.1},
        {"title": "high", "score": 0.9},
        {"title": "mid", "score": 0.5},
        {"title": "high2", "score": 0.8},
        {"title": "low2", "score": 0.2},
    ]
    result = topk_fn(items=items, n=3)
    assert result["kept_count"] == 3
    assert result["removed_count"] == 2
    assert [item["title"] for item in result["items"]] == ["high", "high2", "mid"]


def test_topk_rejects_n_below_one() -> None:
    result = topk_fn(items=[{"title": "A", "score": 1}], n=0)
    assert result["error"] == "ValueError"
    assert "n" in result["message"]


def test_topk_bad_items_returns_error_dict() -> None:
    result = topk_fn(items="not-a-list", n=3)
    assert result["error"] == "TypeError"
    assert "items" in result["message"]


# ---------------- source_check ----------------

source_check_fn = TOOL_FUNCTIONS["source_check"]


def test_source_check_classifies_primary_media_and_social() -> None:
    result = source_check_fn(urls=[
        "https://arxiv.org/abs/1706.03762",
        "https://www.reuters.com/technology/ai",
        "https://x.com/sama/status/1",
        "https://some-random-blog.example",
    ])

    assert [r["tier"] for r in result["results"]] == ["tier1", "tier2", "tier3", "unknown"]
    assert [r["citable_as_fact"] for r in result["results"]] == [True, True, False, False]


def test_source_check_normalizes_domain() -> None:
    result = source_check_fn(urls=["HTTPS://WWW.Reuters.com/x?y=1", "reuters.com", "blog.openai.com/post"])

    assert [r["domain"] for r in result["results"]] == ["reuters.com", "reuters.com", "blog.openai.com"]
    assert [r["tier"] for r in result["results"]] == ["tier2", "tier2", "tier1"]


def test_source_check_does_not_confuse_lookalike_domains() -> None:
    # "notopenai.com" must not match "openai.com"; "x.company.com" must not match "x.com".
    result = source_check_fn(urls=["notopenai.com", "x.company.com"])

    assert [r["tier"] for r in result["results"]] == ["unknown", "unknown"]


def test_source_check_bad_input_from_model() -> None:
    assert source_check_fn(urls=[])["error"] == "ValueError"
    assert source_check_fn(urls=None)["error"] == "ValueError"
    single = source_check_fn(urls="openai.com")  # string instead of list is accepted
    assert single["results"][0]["tier"] == "tier1"
    junk = source_check_fn(urls=[123, ""])
    assert [r["tier"] for r in junk["results"]] == ["unknown", "unknown"]


def test_source_check_is_offline(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    source_check_fn(urls=["https://openai.com"])
    assert calls == []
