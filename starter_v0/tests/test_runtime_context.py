"""Live chat (chat.py / app.py) must tell the model today's date; eval must not."""
from __future__ import annotations

from datetime import datetime

from chat import with_runtime_context


def test_runtime_context_appends_todays_date_in_vietnamese() -> None:
    prompt = with_runtime_context("BASE PROMPT\n", now=datetime(2026, 11, 10, 15, 35))

    assert prompt.startswith("BASE PROMPT\n\nRuntime context:")
    assert "Thứ Ba, 10/11/2026" in prompt
    assert "ISO 2026-11-10" in prompt
    assert "15:35" in prompt


def test_runtime_context_keeps_original_prompt_unchanged() -> None:
    base = "Rule 1.\nRule 2."
    prompt = with_runtime_context(base, now=datetime(2026, 1, 4))

    assert prompt.startswith(base)
    assert "Chủ Nhật, 04/01/2026" in prompt
