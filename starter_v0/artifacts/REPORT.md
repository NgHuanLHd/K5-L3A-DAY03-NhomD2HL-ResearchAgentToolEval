# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: D2HL
- Members: Nguyễn Thị Duyên (trưởng nhóm), Võ Thị Kim Huyền, Nguyễn Đức Huân, Vũ Gia Linh — chi tiết trong `TEAM.md`
- Provider/model: OpenRouter, `openai/gpt-4o-mini` (mọi version v0–v5 dùng cùng model)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent trả lời bằng tiếng Việt: tìm tin tức trên web, tìm tweet theo từ khóa hoặc theo tài khoản, đọc nội dung một URL, tra định nghĩa trên Wikipedia, tìm paper arXiv và policy nội bộ công ty, rồi lọc trùng / lấy top-N và tổng hợp thành bản tin. Thiếu thông tin thì agent hỏi lại; muốn đăng Telegram thì agent hỏi xác nhận trước khi gửi.

UI Streamlit (`starter_v0/app.py`): mỗi câu trả lời hiện kèm các tool agent đã gọi (tham số + kết quả) để thấy agent chọn tool thế nào.

**Link dùng thử (deploy):**

> URL: https://herein-monetary-prescribed-cleaner.trycloudflare.com/ (Cloudflare quick tunnel tới Streamlit chạy trên máy nhóm; chỉ hoạt động trong buổi showdown 10/11/2026)
>
> Tự chạy local: `cd starter_v0`, `pip install -r requirements.txt`, tạo `.env` từ `.env.example`, rồi `streamlit run app.py`.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại khi thiếu thông tin (tài khoản, URL); hỏi xác nhận yes/no trước khi gửi | không |
| `lookup` | Tìm web và tin tức (Tavily), có `topic=news` và `timeframe` day/week/month | không |
| `social_search` | Tìm tweet theo từ khóa, sắp xếp Latest hoặc Top | không |
| `timeline` | Lấy tweet mới nhất của một tài khoản (Sam Altman → `sama`) | không |
| `fetch` | Đọc nội dung một URL cụ thể (Firecrawl) | không |
| `format` | Trình bày các item đã có thành bản tin markdown | không |
| `send` | Đăng lên kênh Telegram, chỉ sau khi người dùng xác nhận | không (bonus) |
| `policy` | Tìm trong policy nội bộ công ty (nguồn, dữ liệu, xuất bản...) | không (bonus) |
| `papers` | Tìm paper trên arXiv theo chủ đề | không (bonus) |
| `paper_text` | Tải PDF arXiv và trích text | không (bonus) |
| `wiki` | Tra định nghĩa / kiến thức nền từ Wikipedia (không cần API key, tự chuyển vi → en nếu không có bài) | **có** (Huân) |
| `tool_new` | Bỏ các item trùng URL hoặc trùng tiêu đề trong danh sách đã thu thập | **có** (Huyền) |
| `topk` | Giữ N item có score cao nhất trong danh sách đã thu thập | **có** (Huyền) |

## A3. Câu hỏi mẫu để thử

1. `Tin tức AI hôm nay có gì nổi bật?` → `lookup(topic=news, timeframe=day)`, trả lời 5 tin kèm nguồn.
2. `Retrieval-augmented generation là gì?` → `wiki`; so với `Tin mới nhất về RAG hôm nay` → `lookup` (cùng chủ đề, khác tool).
3. `Tóm tắt bài viết này hộ mình` → agent hỏi lại URL; gửi tiếp `https://www.anthropic.com/news/claude-3-5-sonnet` → `fetch` và tóm tắt.
4. `Theo policy công ty, tweet viral có được coi là fact đã xác nhận không?` → `policy(policy_area=source_citation)`.
5. `Đăng bản tin này lên Telegram giúp mình` → agent hỏi lại (nội dung / xác nhận) trước, không tự gửi.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (`v0+peb1c8179815b+t5b22a2476d41`) | Đo hành vi chưa tối ưu trước khi sửa | – | 0.70 (14/20; routing 0.75, args 0.70, multi-turn 1.00) | `runs/v0_B_base_openrouter_20261110T101829219203.json` |
| v1 | `system_prompt.md` (`v1+p528422e91ef6+t5b22a2476d41`) | Bỏ 3 chỉ dẫn xấu (đoán, gửi không xác nhận, ép một tool); thêm rule hỏi lại / xác nhận / ngoài phạm vi không gọi tool → sửa R08, R10, R11, R12, R14 | 0.70 | 0.90 (18/20; routing 0.95, args 0.90, multi-turn 0.83). Fixed R08 R10 R11 R13 R14; còn R12; regression M02 | `runs/v1_B_base_openrouter_20261110T110540530350.json` |
| v2 | `tools.yaml` (`v2+p528422e91ef6+ta15b0a054421`) | Description mơ hồ làm M02 chọn `social_search`; viết lại description 10 tool theo mẫu USE WHEN / DO NOT USE WHEN sẽ sửa M02, giữ R13 | 0.90 | 1.00 (20/20; routing 1.00, args 1.00, multi-turn 1.00). Fixed R12, M02. Extension: 0.70 (E01, E06, E08 FAIL) | `runs/v2_B_base_openrouter_20261110T110903002778.json`, `runs/v2_B_extension_openrouter_20261110T110935232142.json` |
| v3 | `tools.yaml` + `system_prompt.md` (`v3+pf2b253f2674e+t347783762048`) | Extension FAIL do thiếu convention args (`policy_area`) và bỏ tool khi request có 2 việc; ghi convention vào từng parameter + rule gọi đủ tool cùng lượt sẽ sửa E01, E06, E08 | 1.00 base / 0.70 ext | Base 0.95 (19/20; regression R12: `clarify` text thay vì yes_no). Extension 1.00 (10/10) | `runs/v3_B_base_openrouter_20261110T111136211874.json`, `runs/v3_B_extension_openrouter_20261110T111205802827.json` |
| v4 | `system_prompt.md` (`v4+p120eb7389758+t347783762048`) | UI trả lời tiếng Anh dù user hỏi tiếng Việt vì prompt không quy định ngôn ngữ; thêm rule 7 (luôn trả lời/hỏi lại bằng tiếng Việt, không dịch tool args) sẽ đổi ngôn ngữ mà không giảm điểm | 0.95 base / 1.00 ext | Base 0.95 (R12 vẫn FAIL như v3), extension 1.00. Câu trả lời no_tool, câu hỏi `clarify` và câu trả lời sau `lookup` (thử live) đều tiếng Việt | `runs/v4_B_base_openrouter_20261110T122125343711.json`, `runs/v4_B_extension_openrouter_20261110T122329629638.json` |
| v5 | `tools.yaml` (`v5+p120eb7389758+tb70d10f58292`) | Thêm 3 tool mới (`tool_new` dedupe, `wiki`, `topk`) làm model có thêm lựa chọn; description USE WHEN / DO NOT USE WHEN đủ rõ để không làm giảm routing của base và extension | 0.95 base / 1.00 ext | Base 0.95 (giữ nguyên, chỉ R12), extension 1.00, **group 12/14 = 0.86** (routing 1.00; 2 FAIL đều do bỏ arg trùng default) | `runs/v5_B_base_openrouter_20261110T151142932750.json`, `runs/v5_B_group_openrouter_20261110T151222819443.json`, `runs/v5_B_extension_openrouter_20261110T151300143938.json` |

Bản chụp prompt/tools từng version nằm trong `artifacts/versions/` (`system_prompt_v0..v5.md`, `tools_v0..v5.yaml`); SHA-256 của mỗi file khớp `prompt_hash` / `tools_hash` trong `version_log.csv`. v1 chỉ đổi prompt (tools giữ v0), v2 chỉ đổi tools (prompt giữ v1).

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

Baseline v0 (`openai/gpt-4o-mini`, run `runs/v0_B_base_openrouter_20261110T101829219203.json`): 14/20 PASS, `case_accuracy` 0.70. 6 case FAIL, nguồn: `results[*].result` trong run JSON.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | `out_of_scope` (observed: `unexpected_tool_call`) | `send(text="Nguyên hàm của x^2 là x^3/3 + C...")` | `expected no tool call` — prompt v0 ép "pick one tool", model dùng `send` để trả lời câu toán | v1 (`system_prompt.md`): câu ngoài phạm vi → trả lời/từ chối bằng text, không gọi tool; cấm dùng `send` để trả lời |
| R10_missing_handle | `missing_info` (observed: `missing_tool_call`) | `timeline(screenname="sama")` | `missing tool call clarify`, `extra tool call timeline` — prompt v0 bảo "pick a well-known account like Sam Altman" | v1: thiếu account → `clarify(response_type="text")`, không đoán |
| R11_missing_url | `missing_info` (observed: `missing_tool_call`) | `fetch(url="https://example.com/article")` | `missing tool call clarify`, `extra tool call fetch` — prompt v0 bảo "assume a likely URL", model bịa URL | v1: thiếu URL → `clarify(response_type="text")`, không bịa URL |
| R12_confirm_before_send | `wrong_boundary` (observed: `missing_tool_call`) | `send(text="Bản tin này đã được đăng lên Telegram.")` | `missing tool call clarify`, `extra tool call send` — prompt v0 bảo "just go ahead and do it", gửi khi chưa xác nhận | v1: gửi/đăng → `clarify(response_type="yes_no")` trước; chỉ `send(confirmed=true)` sau khi user đồng ý |
| R13_parallel_web_and_tweets | `wrong_tool` (observed: `wrong_arg_value`) | `lookup(query="AI", timeframe="day", max_results=5)`, `social_search(query="AI", limit=5)` | `topic: expected 'news', got None` — routing đúng cả 2 tool, chỉ thiếu `topic=news` cho "tin AI" | v2 (`tools.yaml`): mô tả convention `topic=news` khi user hỏi tin tức |
| R14_out_of_scope_coding | `out_of_scope` (observed: `unexpected_tool_call`) | `send(text="def fibonacci(n): ...")` | `expected no tool call` — giống R08, model gửi code lên Telegram không ai yêu cầu | v1: như R08 |

Nhận xét: 5/6 lỗi do 3 chỉ dẫn xấu cố ý trong prompt v0 (đoán thay vì hỏi, gửi không xác nhận, ép một tool); chỉ R13 là lỗi convention args trong tool declaration. Các case R01–R07, M01–M06 đã PASS ở v0 — cần theo dõi regression ở v1–v3.

### Lỗi phát sinh ở v1–v3 (regression + extension)

| Case ID | Version lỗi | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| M02_carryover_timeframe | v1 (regression) | `social_search(query="robotics", search_type="Latest", limit=5)` | `missing tool call lookup`, `extra tool call social_search` — prompt v1 mô tả `social_search` là "posts by keyword", model hiểu "tìm robotics" là tìm post | v2 (`tools.yaml`): `social_search` chỉ khi user nhắc Twitter/X/tweet; "tin, tin tức" → `lookup`. Đã PASS ở v2, v3 |
| R12_confirm_before_send | v1, v3 | `clarify(question="Bạn có thể cung cấp nội dung...", response_type="text")` | `response_type: expected 'yes_no', got 'text'` — rule 1 (thiếu thông tin → text) và rule 2 (gửi → yes_no) xung đột khi request vừa thiếu nội dung vừa là lệnh gửi | v2 description `send`/`clarify` sửa được (PASS); v3 lỗi lại dù description `response_type` ghi "always yes_no". Hướng v4: prompt ghi rule 2 ưu tiên hơn rule 1 (chưa chạy) |
| E01_company_source_policy | v2 (extension) | `policy(query="tweet viral", policy_area="all")` | `policy_area: expected 'source_citation', got 'all'` | v3: description `policy_area` có bảng map chủ đề → area. PASS ở v3 |
| E06_briefing_live_plus_style | v2 (extension) | `policy(query="source citation", policy_area="source_citation")` | `missing tool call lookup` — "kiểm tra policy trước" khiến model chỉ gọi policy | v3: prompt rule 4 — request nhiều việc → gọi đủ tool trong cùng lượt. PASS ở v3 |
| E08_specific_url_not_arxiv | v2 (extension) | `fetch(url=...)`, `policy(query="research workflow")` | `policy_area: expected 'ai_research', got None` | v3: như E01. PASS ở v3 |

### Trạng thái từng case lỗi qua các version

| Case | v0 | v1 | v2 | v3 |
|---|---|---|---|---|
| R08, R14 (out of scope) | FAIL | PASS | PASS | PASS |
| R10, R11 (thiếu account/URL) | FAIL | PASS | PASS | PASS |
| R12 (xác nhận trước khi gửi) | FAIL | FAIL | PASS | FAIL |
| R13 (web + tweet) | FAIL | PASS | PASS | PASS |
| M02 (carry-over timeframe) | PASS | FAIL | PASS | PASS |
| E01, E06, E08 (extension) | – | – | FAIL | PASS |

Nhận xét: R12 dao động giữa các version → model chưa ổn định ở ca vừa thiếu nội dung vừa là lệnh gửi; đây là lỗi còn mở sau v3.

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

`data/eval_group.json` có 14 case: 10 case chung (G01–G05 single-turn, G06–G10 multi-turn, do Duyên viết) + 4 case route tới tool mới (G11 `tool_new`, G12–G13 `wiki`, G14 `topk`). Kết quả v5 (`runs/v5_B_group_openrouter_20261110T151222819443.json`): **12/14 PASS (0.86)**, tool routing 1.00, args 0.86, multi-turn 1.00.

| Case ID | What It Tests | Expected Tool/Behavior | Result (v5) |
|---|---|---|---|
| G01_arxiv_search_new_tool | Tìm paper arXiv theo chủ đề, giữ số lượng | `papers(query="AI agents evaluation", max_results=4)` | PASS |
| G02_missing_account_clarify | Thiếu tài khoản → hỏi lại, không đoán | `clarify(response_type=text)` | PASS |
| G03_out_of_scope_no_tool | Sáng tác thơ → ngoài phạm vi | không gọi tool | PASS |
| G04_social_search_limit | Tweet theo chủ đề + `limit=8` | `social_search(query="GPT-5", limit=8, search_type=Latest)` | FAIL: thiếu `search_type` (model bỏ vì trùng default) |
| G05_read_exact_url | Có URL cụ thể → đọc, giữ nguyên URL | `fetch(url=...)` | PASS |
| G06_correct_account_across_turns | Lượt 2 sửa người (Sam Altman → Karpathy) | `timeline(screenname="karpathy")` | PASS |
| G07_correct_limit_across_turns | Lượt 2 sửa số lượng (10 → 3), giữ tài khoản | `timeline(screenname="elonmusk", limit=3)` | PASS |
| G08_carry_topic_update_timeframe | Đổi chủ đề sang robotics, giữ "hôm nay" | `lookup(query="robotics", topic=news, timeframe=day)` | PASS |
| G09_clarify_then_fetch | Lượt 2 mới đưa URL | `fetch(url="https://www.anthropic.com/news")` | PASS |
| G10_switch_to_web_news | Đổi từ tweet sang tin web, tuần này | `lookup(query="OpenAI", topic=news, timeframe=week)` | PASS |
| G11_tool_new_duplicates | Bỏ item trùng URL → tool mới | `tool_new(key=url)` | FAIL: thiếu `key` (model bỏ vì trùng default `url`) |
| G12_wiki_concept_definition | "RAG là gì?" → định nghĩa | `wiki` | PASS |
| G13_news_not_wiki_boundary | Cùng chủ đề nhưng hỏi tin hôm nay | `lookup(topic=news, timeframe=day)`, không `wiki` | PASS |
| G14_topk_keep_three | Giữ 3 item score cao nhất | `topk(n=3)` | PASS |

Nhận xét:

- Routing group đạt 1.00: cả 3 tool mới đều được chọn đúng lúc, và cặp G12/G13 cho thấy cùng chủ đề nhưng khác ý định thì route khác tool.
- 2 case FAIL có cùng nguyên nhân: model bỏ argument có giá trị bằng default (`search_type=Latest`, `key=url`). Khi chạy thật tool vẫn dùng default nên hành vi đúng, nhưng eval so `actual.get(key)` nên tính là `wrong_arg_value`. Hướng sửa cho version sau: ghi trong parameter description "always pass this argument explicitly", hoặc bỏ arg trùng default khỏi `expect`.
- G12: model gọi `wiki(lang="vi")` với title tiếng Anh; nhờ fallback vi → en của tool (xem B5) vẫn lấy được bài.

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI |  |  |  |
| Tool unit tests (`tests/`) | `pytest` output |  |  |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
