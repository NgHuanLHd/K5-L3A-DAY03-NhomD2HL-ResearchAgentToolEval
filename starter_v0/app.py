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
    with_runtime_context,
    write_transcript,
)
from providers import make_provider  # noqa: E402
from tools import load_tool_declarations, to_openai_tools  # noqa: E402
from versioning import artifact_version_dict, build_artifact_version  # noqa: E402

PROVIDER = "openrouter"
VERSION_LABEL = "v6"
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
    "papers": "📚", "paper_text": "📑", "tool_new": "🧹", "wiki": "📖", "topk": "🏆", "source_check": "🛡️",
}

# --- Giao diện xanh nhẹ nhàng -------------------------------------------------
THEME_CSS = """
<style>
:root {
    --blue-50:  #F2F8FD;
    --blue-100: #E3F0FA;
    --blue-200: #C9E1F5;
    --blue-300: #A5CDEE;
    --blue-500: #4A9BD9;
    --blue-600: #2F82C4;
    --blue-800: #1F4E79;
    --ink:      #0A0A0A;
    --radius:   16px;
}

/* Cỡ chữ lớn, rõ ràng */
html, body, .stApp { font-size: 17px; }
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li { font-size: 1.05rem; line-height: 1.65; }
[data-testid="stSidebar"] .stButton > button p { font-size: .95rem; font-weight: 500; }

/* Nền tổng thể: gradient xanh rất nhạt */
.stApp {
    background: linear-gradient(160deg, #F7FBFF 0%, #EAF4FC 55%, #E2F0F9 100%);
    color: var(--ink);
}
.block-container { padding-top: 2rem; max-width: 980px; }
header[data-testid="stHeader"] { background: transparent; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #E3F0FA 0%, #D3E8F7 100%);
    border-right: 1px solid var(--blue-200);
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #0A0A0A !important; font-weight: 800; }

/* Huy hiệu nhóm trong sidebar */
.side-brand {
    display: flex; align-items: center; gap: .75rem;
    background: #FFFFFF; border: 2px solid var(--blue-500);
    border-radius: 18px; padding: .7rem .9rem; margin-bottom: 1rem;
    box-shadow: 0 4px 14px rgba(74,155,217,.25);
}
.side-brand .logo {
    width: 48px; height: 48px; border-radius: 14px; flex: none;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.7rem; background: linear-gradient(135deg, #4A9BD9, #1F6FB5);
    box-shadow: 0 3px 8px rgba(31,111,181,.35);
}
.side-brand .name { font-size: 1.35rem; font-weight: 900; color: #0A0A0A; line-height: 1.1; }
.side-brand .sub  { font-size: .8rem; font-weight: 600; color: #1F6FB5; letter-spacing: .06em; }
[data-testid="stSidebar"] code {
    background: rgba(255,255,255,.7); color: var(--blue-800); border-radius: 8px;
}

/* Tiêu đề */
h1, h2, h3 { color: #0A0A0A !important; letter-spacing: -0.01em; font-weight: 800; }
h2 { font-size: 1.6rem !important; }

/* Banner đầu trang */
.hero {
    display: flex; align-items: center; gap: 1.4rem;
    background: linear-gradient(120deg, #BFDDF6 0%, #DCEEFB 55%, #F0F8FE 100%);
    border: 2px solid var(--blue-500);
    border-radius: 26px;
    padding: 1.6rem 1.9rem;
    margin-bottom: 1.4rem;
    box-shadow: 0 10px 28px rgba(47,130,196,.22);
}
.hero .logo {
    width: 96px; height: 96px; border-radius: 26px; flex: none;
    display: flex; align-items: center; justify-content: center;
    font-size: 3.2rem;
    background: linear-gradient(135deg, #4A9BD9 0%, #1F6FB5 100%);
    box-shadow: 0 8px 18px rgba(31,111,181,.40), inset 0 0 0 4px rgba(255,255,255,.35);
}
.hero .team {
    display: inline-block; padding: .2rem .9rem; margin-bottom: .4rem;
    background: #0A0A0A; color: #FFFFFF !important; border-radius: 999px;
    font-size: .95rem; font-weight: 800; letter-spacing: .12em;
}
.hero h1 { margin: 0; font-size: 2.6rem; line-height: 1.1; color: #0A0A0A !important; font-weight: 900; }
.hero p  { margin: .45rem 0 0; color: #0A0A0A; font-size: 1.1rem; font-weight: 500; }
.hero .chip {
    display: inline-block; margin: .8rem .45rem 0 0; padding: .25rem .85rem;
    background: #FFFFFF; border: 1.5px solid var(--blue-500);
    border-radius: 999px; font-size: .88rem; font-weight: 600; color: #0A0A0A;
}
@media (max-width: 640px) {
    .hero { flex-direction: column; text-align: center; }
    .hero h1 { font-size: 2rem; }
}

/* Nút bấm */
.stButton > button, .stDownloadButton > button {
    background: #FFFFFF;
    color: #0A0A0A;
    border: 1.5px solid var(--blue-300);
    border-radius: 12px;
    transition: all .18s ease;
    text-align: left;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background: var(--blue-200);
    color: #0A0A0A;
    border-color: var(--blue-500);
    transform: translateY(-1px);
    box-shadow: 0 6px 14px rgba(74,155,217,.28);
}

/* Thẻ gợi ý */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,.75);
    border: 1px solid var(--blue-200) !important;
    border-radius: var(--radius) !important;
    box-shadow: 0 3px 12px rgba(74,155,217,.10);
}

/* Tin nhắn chat */
[data-testid="stChatMessage"] {
    background: #FFFFFF;
    border: 1px solid var(--blue-200);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
    margin-bottom: .8rem;
    box-shadow: 0 3px 12px rgba(74,155,217,.08);
}
/* Tin nhắn của người dùng: xanh nhạt hơn */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: var(--blue-100);
    border-color: var(--blue-300);
}

/* Expander (tool call) */
[data-testid="stExpander"] {
    background: var(--blue-50);
    border: 1px solid var(--blue-200);
    border-radius: 12px;
}
[data-testid="stExpander"] summary { color: #0A0A0A; font-weight: 600; }

/* Ô nhập chat */
[data-testid="stChatInput"] {
    border: 1.5px solid var(--blue-300);
    border-radius: 18px;
    background: #FFFFFF;
    box-shadow: 0 4px 16px rgba(74,155,217,.15);
}
[data-testid="stChatInput"]:focus-within { border-color: var(--blue-500); }

/* Code block */
pre, [data-testid="stCode"] { border-radius: 10px !important; }

/* Thay thế config.toml: màu chủ đạo, chữ, spinner, link */
html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, li, label, span {
    color: var(--ink);
}
a { color: var(--blue-600) !important; }
.stSpinner > div > div { border-top-color: var(--blue-500) !important; }
hr { border-color: var(--blue-200) !important; }
[data-testid="stSidebar"] .stButton > button[kind="secondary"] { font-size: .88rem; }

/* Thanh cuộn nhẹ nhàng */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: var(--blue-300); border-radius: 8px; }
::-webkit-scrollbar-track { background: transparent; }
</style>
"""


def inject_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


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
        {"role": "system", "content": with_runtime_context(cfg["system_prompt"])},
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


def render_hero(cfg: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div class="logo">🔎</div>
            <div>
            <span class="team">NHÓM D2HL</span>
            <h1>Research Agent</h1>
            <p>Tìm kiếm, đọc và kiểm tra thông tin từ nhiều nguồn trong một cuộc trò chuyện.</p>
            <span class="chip">🤖 {cfg['model']}</span>
            <span class="chip">🛠️ {len(cfg['declarations'])} công cụ</span>
            <span class="chip">🏷️ {VERSION_LABEL}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Research Agent — Nhóm D2HL", page_icon="🔎", layout="wide")
    inject_theme()
    cfg = load_agent_config()
    if "history" not in st.session_state:
        reset_session(cfg)

    with st.sidebar:
        st.markdown(
            """
            <div class="side-brand">
                <div class="logo">🔎</div>
                <div>
                    <div class="name">Nhóm D2HL</div>
                    <div class="sub">RESEARCH AGENT</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Trợ lý nghiên cứu thông tin và nguồn tin.")
        st.markdown(f"**Model**  \n`{PROVIDER} · {cfg['model']}`")
        st.markdown(f"**Phiên bản**  \n`{cfg['artifact_version'].artifact_version}`")
        if st.button("Cuộc trò chuyện mới", icon=":material/add_comment:", width="stretch"):
            reset_session(cfg)
            st.rerun()

        st.divider()
        st.subheader("Bắt đầu nhanh")
        for index, query in enumerate(SAMPLE_QUERIES):
            if st.button(query, key=f"sample-{index}", width="stretch"):
                st.session_state.pending_query = query
                st.rerun()

        with st.expander(f"Công cụ ({len(cfg['declarations'])})", expanded=False):
            for decl in cfg["declarations"]:
                first_sentence = decl.get("description", "").split(". ")[0]
                st.markdown(f"{TOOL_ICONS.get(decl['name'], '🔧')} **{decl['name']}**  \n{first_sentence}")

        st.divider()
        st.caption("Transcript của phiên hiện tại")
        st.code(str(st.session_state.transcript_path.relative_to(ROOT)), language=None)
        st.download_button(
            "Tải transcript JSON",
            data=json.dumps(st.session_state.transcript, ensure_ascii=False, indent=2),
            file_name=f"{st.session_state.transcript['transcript_id']}.json",
            mime="application/json",
            icon=":material/download:",
            width="stretch",
        )

    render_hero(cfg)

    if not st.session_state.display:
        st.subheader("Bạn muốn nghiên cứu điều gì?")
        st.write("Chọn một gợi ý để bắt đầu, hoặc nhập câu hỏi riêng ở ô chat phía dưới.")
        for row_start in range(0, len(SAMPLE_QUERIES), 2):
            left, right = st.columns(2)
            for column, query in zip((left, right), SAMPLE_QUERIES[row_start:row_start + 2]):
                with column:
                    with st.container(border=True):
                        st.markdown(f"{TOOL_ICONS.get('lookup', '🔎')} **Gợi ý nghiên cứu**")
                        st.write(query)
                        if st.button("Dùng câu hỏi này", key=f"welcome-{row_start}-{query}", icon=":material/arrow_forward:", width="stretch"):
                            st.session_state.pending_query = query
                            st.rerun()

    for item in st.session_state.display:
        with st.chat_message(item["role"]):
            if item.get("tool_events"):
                render_tool_events(item["tool_events"])
            st.markdown(item["content"])
            if item.get("status") == "waiting_for_user":
                st.caption("⏳ Agent đang chờ bạn trả lời câu hỏi trên.")

    typed = st.chat_input("Hỏi về tin tức, mạng xã hội, paper hoặc policy…")
    pending = st.session_state.pop("pending_query", None)
    user_text = typed or pending
    if not user_text:
        return

    st.session_state.display.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm và tổng hợp thông tin…"):
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