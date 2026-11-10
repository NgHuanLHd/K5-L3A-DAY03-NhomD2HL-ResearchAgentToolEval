"""Streamlit UI for the Day 03 research agent.

Run from starter_v0/:
    streamlit run app.py

Reuses the multi-round tool loop from chat.py, so the UI behaves exactly like
`python chat.py` and writes the same transcript format to transcripts/.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Any

import streamlit as st

# chat.py prints tool calls with emoji; Windows consoles default to cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from chat import (  # noqa: E402  (after stdout fix)
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider  # noqa: E402
from tools import load_tool_declarations, to_openai_tools  # noqa: E402
from versioning import artifact_version_dict, build_artifact_version  # noqa: E402

PROVIDER = "openrouter"
VERSION_LABEL = "v3"
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
TRANSCRIPTS_DIR = ROOT / "transcripts"

SAMPLE_QUERIES = [
    "Tin tức AI hôm nay có gì nổi bật?",
    "Lấy 3 tweet mới nhất của Andrej Karpathy",
    "Mọi người đang bàn gì về GPT-5 trên Twitter? Lấy bài top",
    "Tóm tắt bài này giúp mình: https://www.anthropic.com/news/claude-3-5-sonnet",
    "Tìm paper arXiv về retrieval augmented generation evaluation",
    "Theo policy công ty, tweet viral có được coi là fact đã xác nhận không?",
    "Tóm tắt 5 tweet mới nhất giúp mình",
    "Đăng bản tin này lên Telegram giúp mình",
]

TOOL_ICONS = {
    "clarify": "❓", "timeline": "👤", "social_search": "🐦", "lookup": "🔎",
    "fetch": "📄", "format": "📝", "send": "📤", "policy": "📘",
    "papers": "📚", "paper_text": "📑",
}


@st.cache_resource
def load_agent_config() -> dict[str, Any]:
    declarations = load_tool_declarations(TOOLS_PATH)
    provider = make_provider(PROVIDER)
    return {
        "provider": provider,
        "model": getattr(provider, "default_model", None),
        "system_prompt": SYSTEM_PROMPT_PATH.read_text(encoding="utf-8"),
        "declarations": declarations,
        "openai_tools": to_openai_tools(declarations),
        "artifact_version": build_artifact_version(VERSION_LABEL, SYSTEM_PROMPT_PATH, TOOLS_PATH),
    }


def new_transcript(cfg: dict[str, Any]) -> tuple[dict[str, Any], Any]:
    transcript_id = "_".join([
        "ui", safe_slug(VERSION_LABEL), safe_slug(PROVIDER),
        datetime.now().strftime("%Y%m%dT%H%M%S%f"),
    ])
    path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(cfg["artifact_version"]),
        "provider": PROVIDER,
        "model": cfg["model"],
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": HISTORY_WINDOW,
        "max_tool_rounds": MAX_TOOL_ROUNDS,
        "interface": "streamlit",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    return transcript, path


def reset_session(cfg: dict[str, Any]) -> None:
    st.session_state.history = []      # model-facing history (user/assistant text)
    st.session_state.display = []      # UI-facing messages incl. tool events
    st.session_state.transcript, st.session_state.transcript_path = new_transcript(cfg)


def short_json(value: Any, max_chars: int = 4000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    return text if len(text) <= max_chars else text[:max_chars] + "\n...<truncated>"


def render_tool_events(events: list[dict[str, Any]]) -> None:
    for event in events:
        name = event.get("tool", "?")
        result = event.get("result", {})
        failed = isinstance(result, dict) and result.get("error")
        label = f"{TOOL_ICONS.get(name, '🔧')} `{name}`" + ("  ⚠️ lỗi" if failed else "")
        with st.expander(label, expanded=False):
            st.caption("Arguments")
            st.code(short_json(event.get("args", {})), language="json")
            st.caption("Result")
            st.code(short_json(result), language="json")


def run_turn(cfg: dict[str, Any], user_text: str) -> dict[str, Any]:
    messages = [
        {"role": "system", "content": cfg["system_prompt"]},
        *trim_history(st.session_state.history, HISTORY_WINDOW),
        {"role": "user", "content": user_text},
    ]
    turn: dict[str, Any] = {
        "turn_index": len(st.session_state.transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    try:
        result = run_model_tool_loop(
            provider=cfg["provider"],
            messages=messages,
            tools=cfg["openai_tools"],
            model=cfg["model"],
            max_tool_rounds=MAX_TOOL_ROUNDS,
        )
        turn.update(result)
        st.session_state.history.append({"role": "user", "content": user_text})
        st.session_state.history.append({"role": "assistant", "content": result["assistant_text"]})
    except Exception as exc:  # show provider/network errors instead of crashing the page
        turn.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}",
                     "assistant_text": f"Lỗi khi gọi model: {type(exc).__name__}: {exc}"})
    turn["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn)
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)
    return turn


def main() -> None:
    st.set_page_config(page_title="Research Agent — Nhóm D2HL", page_icon="🔎", layout="wide")
    cfg = load_agent_config()
    if "history" not in st.session_state:
        reset_session(cfg)

    with st.sidebar:
        st.header("Research Agent")
        st.caption(f"Provider `{PROVIDER}` · model `{cfg['model']}`")
        st.caption(f"Artifact `{cfg['artifact_version'].artifact_version}`")
        if st.button("🔄 Cuộc trò chuyện mới", use_container_width=True):
            reset_session(cfg)
            st.rerun()

        st.subheader("Câu hỏi mẫu")
        for query in SAMPLE_QUERIES:
            if st.button(query, key=f"sample-{query}", use_container_width=True):
                st.session_state.pending_query = query
                st.rerun()

        st.subheader("Tool")
        for decl in cfg["declarations"]:
            first_sentence = decl.get("description", "").split(". ")[0]
            st.markdown(f"{TOOL_ICONS.get(decl['name'], '🔧')} **{decl['name']}** — {first_sentence}")

        st.divider()
        st.caption(f"Transcript: `{st.session_state.transcript_path.relative_to(ROOT)}`")

    st.title("🔎 Research Agent")
    st.caption("Tìm tin theo từ khóa hoặc tài khoản, đọc URL, tra paper arXiv và policy công ty, "
               "gửi bản tin lên Telegram sau khi bạn xác nhận. Mỗi tool agent gọi được hiển thị bên dưới câu trả lời.")

    for item in st.session_state.display:
        with st.chat_message(item["role"]):
            if item.get("tool_events"):
                render_tool_events(item["tool_events"])
            st.markdown(item["content"])
            if item.get("status") == "waiting_for_user":
                st.caption("⏳ Agent đang chờ bạn trả lời câu hỏi trên.")

    typed = st.chat_input("Hỏi agent… (ví dụ: Tin AI tuần này)")
    user_text = typed or st.session_state.pop("pending_query", None)
    if not user_text:
        return

    st.session_state.display.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        with st.spinner("Agent đang chọn tool và chạy…"):
            turn = run_turn(cfg, user_text)
        render_tool_events(turn.get("tool_events", []))
        st.markdown(turn["assistant_text"] or "_(không có câu trả lời)_")
        if turn.get("status") == "waiting_for_user":
            st.caption("⏳ Agent đang chờ bạn trả lời câu hỏi trên.")

    st.session_state.display.append({
        "role": "assistant",
        "content": turn["assistant_text"] or "_(không có câu trả lời)_",
        "tool_events": turn.get("tool_events", []),
        "status": turn.get("status"),
    })


main()
