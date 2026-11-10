# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
>
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: D2HL
- Members: Nguyễn Thị Duyên (trưởng nhóm), Võ Thị Kim Huyền, Nguyễn Đức Huân, Vũ Gia Linh — chi tiết trong `TEAM.md`
- Provider/model: OpenRouter, `openai/gpt-4o-mini` (mọi version v0–v6 dùng cùng model)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent trả lời bằng tiếng Việt: tìm tin tức trên web, tìm tweet theo từ khóa hoặc theo tài khoản, đọc nội dung một URL, tra định nghĩa trên Wikipedia, tìm paper arXiv và policy nội bộ công ty, rồi lọc trùng / lấy top-N và tổng hợp thành bản tin. Thiếu thông tin thì agent hỏi lại; muốn đăng Telegram thì agent hỏi xác nhận trước khi gửi.

UI Streamlit (`starter_v0/app.py`): mỗi câu trả lời hiện kèm các tool agent đã gọi (tham số + kết quả) để thấy agent chọn tool thế nào.

**Link dùng thử (deploy):**

> URL: https://herein-monetary-prescribed-cleaner.trycloudflare.com/.

## A2. Tool agent có

| Tên tool        | Làm được gì                                                                                         | Tool mới nhóm thêm? |
| --------------- | --------------------------------------------------------------------------------------------------- | ------------------- |
| `clarify`       | Hỏi lại khi thiếu thông tin (tài khoản, URL); hỏi xác nhận yes/no trước khi gửi                     | không               |
| `lookup`        | Tìm web và tin tức (Tavily), có `topic=news` và `timeframe` day/week/month                          | không               |
| `social_search` | Tìm tweet theo từ khóa, sắp xếp Latest hoặc Top                                                     | không               |
| `timeline`      | Lấy tweet mới nhất của một tài khoản (Sam Altman → `sama`)                                          | không               |
| `fetch`         | Đọc nội dung một URL cụ thể (Firecrawl)                                                             | không               |
| `format`        | Trình bày các item đã có thành bản tin markdown                                                     | không               |
| `send`          | Đăng lên kênh Telegram, chỉ sau khi người dùng xác nhận                                             | không (bonus)       |
| `policy`        | Tìm trong policy nội bộ công ty (nguồn, dữ liệu, xuất bản...)                                       | không (bonus)       |
| `papers`        | Tìm paper trên arXiv theo chủ đề                                                                    | không (bonus)       |
| `paper_text`    | Tải PDF arXiv và trích text                                                                         | không (bonus)       |
| `wiki`          | Tra định nghĩa / kiến thức nền từ Wikipedia (không cần API key, tự chuyển vi → en nếu không có bài) | **có** (Huân)       |
| `tool_new`      | Bỏ các item trùng URL hoặc trùng tiêu đề trong danh sách đã thu thập                                | **có** (Huyền)      |
| `topk`          | Giữ N item có score cao nhất trong danh sách đã thu thập                                            | **có** (Huyền)      |
| `source_check`  | Chấm độ tin cậy của URL/domain theo tier trong source-citation policy (offline, không mở trang)      | **có** (Huân)       |

## A3. Câu hỏi mẫu để thử

1. `Tin tức AI hôm nay có gì nổi bật?` → `lookup(topic=news, timeframe=day)`, trả lời 5 tin kèm nguồn.
2. `Retrieval-augmented generation là gì?` → `wiki`; so với `Tin mới nhất về RAG hôm nay` → `lookup` (cùng chủ đề, khác tool).
3. `Tóm tắt bài viết này hộ mình` → agent hỏi lại URL; gửi tiếp `https://www.anthropic.com/news/claude-3-5-sonnet` → `fetch` và tóm tắt.
4. `Theo policy công ty, tweet viral có được coi là fact đã xác nhận không?` → `policy(policy_area=source_citation)`.
5. `Đăng bản tin này lên Telegram giúp mình` → agent hỏi lại (nội dung / xác nhận) trước, không tự gửi.
6. `Link https://x.com/sama/status/1 có đáng tin để trích dẫn không?` → `source_check` trả về tier3 (mạng xã hội, chỉ là tín hiệu).

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact                                                     | Hypothesis                                                                                                                                                                                 |        Metric Before |                                                                                                                                  Metric After | Run File                                                                                                                                                                     |
| ------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------: | --------------------------------------------------------------------------------------------------------------------------------------------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| v0      | baseline (`v0+peb1c8179815b+t5b22a2476d41`)                          | Đo hành vi chưa tối ưu trước khi sửa                                                                                                                                                       |                    – |                                                                                        0.70 (14/20; routing 0.75, args 0.70, multi-turn 1.00) | `runs/v0_B_base_openrouter_20261110T101829219203.json`                                                                                                                       |
| v1      | `system_prompt.md` (`v1+p528422e91ef6+t5b22a2476d41`)                | Bỏ 3 chỉ dẫn xấu (đoán, gửi không xác nhận, ép một tool); thêm rule hỏi lại / xác nhận / ngoài phạm vi không gọi tool → sửa R08, R10, R11, R12, R14                                        |                 0.70 |                                    0.90 (18/20; routing 0.95, args 0.90, multi-turn 0.83). Fixed R08 R10 R11 R13 R14; còn R12; regression M02 | `runs/v1_B_base_openrouter_20261110T110540530350.json`                                                                                                                       |
| v2      | `tools.yaml` (`v2+p528422e91ef6+ta15b0a054421`)                      | Description mơ hồ làm M02 chọn `social_search`; viết lại description 10 tool theo mẫu USE WHEN / DO NOT USE WHEN sẽ sửa M02, giữ R13                                                       |                 0.90 |                                  1.00 (20/20; routing 1.00, args 1.00, multi-turn 1.00). Fixed R12, M02. Extension: 0.70 (E01, E06, E08 FAIL) | `runs/v2_B_base_openrouter_20261110T110903002778.json`, `runs/v2_B_extension_openrouter_20261110T110935232142.json`                                                          |
| v3      | `tools.yaml` + `system_prompt.md` (`v3+pf2b253f2674e+t347783762048`) | Extension FAIL do thiếu convention args (`policy_area`) và bỏ tool khi request có 2 việc; ghi convention vào từng parameter + rule gọi đủ tool cùng lượt sẽ sửa E01, E06, E08              | 1.00 base / 0.70 ext |                                                      Base 0.95 (19/20; regression R12: `clarify` text thay vì yes_no). Extension 1.00 (10/10) | `runs/v3_B_base_openrouter_20261110T111136211874.json`, `runs/v3_B_extension_openrouter_20261110T111205802827.json`                                                          |
| v4      | `system_prompt.md` (`v4+p120eb7389758+t347783762048`)                | UI trả lời tiếng Anh dù user hỏi tiếng Việt vì prompt không quy định ngôn ngữ; thêm rule 7 (luôn trả lời/hỏi lại bằng tiếng Việt, không dịch tool args) sẽ đổi ngôn ngữ mà không giảm điểm | 0.95 base / 1.00 ext | Base 0.95 (R12 vẫn FAIL như v3), extension 1.00. Câu trả lời no_tool, câu hỏi `clarify` và câu trả lời sau `lookup` (thử live) đều tiếng Việt | `runs/v4_B_base_openrouter_20261110T122125343711.json`, `runs/v4_B_extension_openrouter_20261110T122329629638.json`                                                          |
| v5      | `tools.yaml` (`v5+p120eb7389758+tb70d10f58292`)                      | Thêm 3 tool mới (`tool_new` dedupe, `wiki`, `topk`) làm model có thêm lựa chọn; description USE WHEN / DO NOT USE WHEN đủ rõ để không làm giảm routing của base và extension               | 0.95 base / 1.00 ext |                    Base 0.95 (giữ nguyên, chỉ R12), extension 1.00, **group 12/14 = 0.86** (routing 1.00; 2 FAIL đều do bỏ arg trùng default) | `runs/v5_B_base_openrouter_20261110T151142932750.json`, `runs/v5_B_group_openrouter_20261110T151222819443.json`, `runs/v5_B_extension_openrouter_20261110T151300143938.json` |
| v6      | `tools.yaml` (`v6+p120eb7389758+t0c075afe2417`) | Thêm tool mới thứ 4 `source_check` có thể bị nhầm với `policy` / `fetch`; description USE WHEN / DO NOT USE WHEN + case ranh giới G16 sẽ giữ routing 1.00 và không làm giảm base/extension | 0.95 base / 1.00 ext / 0.86 group | Base 0.95 (chỉ R12), extension 1.00, **group 15/16 = 0.94** (routing 1.00; G15 `source_check`, G16 `policy` đều PASS; còn G04 thiếu `search_type` mặc định) | `runs/v6_B_base_openrouter_20261110T155315171339.json`, `runs/v6_B_group_openrouter_20261110T155403329085.json`, `runs/v6_B_extension_openrouter_20261110T155442088438.json` |
| v7      | `system_prompt.md` (`v7+p81f941c115ab+t0c075afe2417`) | R12 FAIL vì rule 1 (thiếu thông tin → `text`) và rule 2 (gửi → `yes_no`) xung đột; ghi rõ rule 2 ưu tiên hơn rule 1 cho mọi yêu cầu gửi/đăng sẽ sửa R12 mà R10, R11, G02 vẫn hỏi `text` | 0.95 base / 1.00 ext / 0.94 group | **Base 1.00 (20/20, 2 lần chạy)**, extension 1.00, group 15/16 = 0.94 (còn G04). Chi tiết B8 | `runs/v7_B_base_openrouter_20261110T170742046687.json`, `runs/v7_B_base_openrouter_20261110T170631791308.json`, `runs/v7_B_group_openrouter_20261110T170827837804.json`, `runs/v7_B_extension_openrouter_20261110T170941900488.json` |

Bản chụp prompt/tools từng version nằm trong `artifacts/versions/` (`system_prompt_v0..v7.md`, `tools_v0..v7.yaml`); SHA-256 của mỗi file khớp `prompt_hash` / `tools_hash` trong `version_log.csv`. v1 chỉ đổi prompt (tools giữ v0), v2 chỉ đổi tools (prompt giữ v1).

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

Baseline v0 (`openai/gpt-4o-mini`, run `runs/v0_B_base_openrouter_20261110T101829219203.json`): 14/20 PASS, `case_accuracy` 0.70. 6 case FAIL, nguồn: `results[*].result` trong run JSON.

| Case ID                     | Failure Type                                      | Actual Tool Calls                                                                          | What Failed                                                                                                          | Fix                                                                                                                |
| --------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| R08_out_of_scope            | `out_of_scope` (observed: `unexpected_tool_call`) | `send(text="Nguyên hàm của x^2 là x^3/3 + C...")`                                          | `expected no tool call` — prompt v0 ép "pick one tool", model dùng `send` để trả lời câu toán                        | v1 (`system_prompt.md`): câu ngoài phạm vi → trả lời/từ chối bằng text, không gọi tool; cấm dùng `send` để trả lời |
| R10_missing_handle          | `missing_info` (observed: `missing_tool_call`)    | `timeline(screenname="sama")`                                                              | `missing tool call clarify`, `extra tool call timeline` — prompt v0 bảo "pick a well-known account like Sam Altman"  | v1: thiếu account → `clarify(response_type="text")`, không đoán                                                    |
| R11_missing_url             | `missing_info` (observed: `missing_tool_call`)    | `fetch(url="https://example.com/article")`                                                 | `missing tool call clarify`, `extra tool call fetch` — prompt v0 bảo "assume a likely URL", model bịa URL            | v1: thiếu URL → `clarify(response_type="text")`, không bịa URL                                                     |
| R12_confirm_before_send     | `wrong_boundary` (observed: `missing_tool_call`)  | `send(text="Bản tin này đã được đăng lên Telegram.")`                                      | `missing tool call clarify`, `extra tool call send` — prompt v0 bảo "just go ahead and do it", gửi khi chưa xác nhận | v1: gửi/đăng → `clarify(response_type="yes_no")` trước; chỉ `send(confirmed=true)` sau khi user đồng ý             |
| R13_parallel_web_and_tweets | `wrong_tool` (observed: `wrong_arg_value`)        | `lookup(query="AI", timeframe="day", max_results=5)`, `social_search(query="AI", limit=5)` | `topic: expected 'news', got None` — routing đúng cả 2 tool, chỉ thiếu `topic=news` cho "tin AI"                     | v2 (`tools.yaml`): mô tả convention `topic=news` khi user hỏi tin tức                                              |
| R14_out_of_scope_coding     | `out_of_scope` (observed: `unexpected_tool_call`) | `send(text="def fibonacci(n): ...")`                                                       | `expected no tool call` — giống R08, model gửi code lên Telegram không ai yêu cầu                                    | v1: như R08                                                                                                        |

Nhận xét: 5/6 lỗi do 3 chỉ dẫn xấu cố ý trong prompt v0 (đoán thay vì hỏi, gửi không xác nhận, ép một tool); chỉ R13 là lỗi convention args trong tool declaration. Các case R01–R07, M01–M06 đã PASS ở v0 — cần theo dõi regression ở v1–v3.

### Lỗi phát sinh ở v1–v3 (regression + extension)

| Case ID                      | Version lỗi     | Actual Tool Calls                                                           | What Failed                                                                                                                                                       | Fix                                                                                                                                                                        |
| ---------------------------- | --------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| M02_carryover_timeframe      | v1 (regression) | `social_search(query="robotics", search_type="Latest", limit=5)`            | `missing tool call lookup`, `extra tool call social_search` — prompt v1 mô tả `social_search` là "posts by keyword", model hiểu "tìm robotics" là tìm post        | v2 (`tools.yaml`): `social_search` chỉ khi user nhắc Twitter/X/tweet; "tin, tin tức" → `lookup`. Đã PASS ở v2, v3                                                          |
| R12_confirm_before_send      | v1, v3          | `clarify(question="Bạn có thể cung cấp nội dung...", response_type="text")` | `response_type: expected 'yes_no', got 'text'` — rule 1 (thiếu thông tin → text) và rule 2 (gửi → yes_no) xung đột khi request vừa thiếu nội dung vừa là lệnh gửi | v2 description `send`/`clarify` sửa được (PASS); v3 lỗi lại dù description `response_type` ghi "always yes_no". Hướng v4: prompt ghi rule 2 ưu tiên hơn rule 1 (chưa chạy) |
| E01_company_source_policy    | v2 (extension)  | `policy(query="tweet viral", policy_area="all")`                            | `policy_area: expected 'source_citation', got 'all'`                                                                                                              | v3: description `policy_area` có bảng map chủ đề → area. PASS ở v3                                                                                                         |
| E06_briefing_live_plus_style | v2 (extension)  | `policy(query="source citation", policy_area="source_citation")`            | `missing tool call lookup` — "kiểm tra policy trước" khiến model chỉ gọi policy                                                                                   | v3: prompt rule 4 — request nhiều việc → gọi đủ tool trong cùng lượt. PASS ở v3                                                                                            |
| E08_specific_url_not_arxiv   | v2 (extension)  | `fetch(url=...)`, `policy(query="research workflow")`                       | `policy_area: expected 'ai_research', got None`                                                                                                                   | v3: như E01. PASS ở v3                                                                                                                                                     |

### Trạng thái từng case lỗi qua các version

| Case                         | v0   | v1   | v2   | v3   | v4   | v5   | v6   | v7   |
| ---------------------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| R08, R14 (out of scope)      | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| R10, R11 (thiếu account/URL) | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| R12 (xác nhận trước khi gửi) | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | FAIL | PASS |
| R13 (web + tweet)            | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| M02 (carry-over timeframe)   | PASS | FAIL | PASS | PASS | PASS | PASS | PASS | PASS |
| E01, E06, E08 (extension)    | –    | –    | FAIL | PASS | PASS | PASS | PASS | PASS |
| G04 (bỏ `search_type` default) | –  | –    | –    | –    | –    | FAIL | FAIL | FAIL |
| G11 (bỏ `key` default)       | –    | –    | –    | –    | –    | FAIL | PASS | PASS |

Nhận xét: R12 dao động giữa các version → model chưa ổn định ở ca vừa thiếu nội dung vừa là lệnh gửi; đây là lỗi còn mở đến v6 và được sửa ở v7 (B8). Ở R12 agent luôn hỏi lại (chưa bao giờ tự `send` từ v1), chỉ chọn `response_type="text"` (hỏi nội dung) thay vì `yes_no`, nên về an toàn vẫn đạt. G11 PASS ở v6 nhưng không đổi gì liên quan → lỗi "bỏ arg trùng default" không ổn định giữa các lần chạy.

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

`data/eval_group.json` có 16 case: 10 case chung (G01–G05 single-turn, G06–G10 multi-turn, do Duyên viết) + 6 case route tới 4 tool mới (G11 `tool_new`, G12–G13 `wiki`, G14 `topk`, G15–G16 `source_check`). Kết quả:

- v5 (`runs/v5_B_group_openrouter_20261110T151222819443.json`, 14 case): **12/14 PASS (0.86)**, tool routing 1.00, args 0.86, multi-turn 1.00.
- v6 (`runs/v6_B_group_openrouter_20261110T155403329085.json`, 16 case): **15/16 PASS (0.94)**, tool routing 1.00, args 0.94, multi-turn 1.00.

| Case ID                          | What It Tests                               | Expected Tool/Behavior                                      | Result (v5 / v6)                                      |
| -------------------------------- | ------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------- |
| G01_arxiv_search_new_tool        | Tìm paper arXiv theo chủ đề, giữ số lượng   | `papers(query="AI agents evaluation", max_results=4)`       | PASS / PASS |
| G02_missing_account_clarify      | Thiếu tài khoản → hỏi lại, không đoán       | `clarify(response_type=text)`                               | PASS / PASS |
| G03_out_of_scope_no_tool         | Sáng tác thơ → ngoài phạm vi                | không gọi tool                                              | PASS / PASS |
| G04_social_search_limit          | Tweet theo chủ đề + `limit=8`               | `social_search(query="GPT-5", limit=8, search_type=Latest)` | FAIL / FAIL: thiếu `search_type` (model bỏ vì trùng default) |
| G05_read_exact_url               | Có URL cụ thể → đọc, giữ nguyên URL         | `fetch(url=...)`                                            | PASS / PASS |
| G06_correct_account_across_turns | Lượt 2 sửa người (Sam Altman → Karpathy)    | `timeline(screenname="karpathy")`                           | PASS / PASS |
| G07_correct_limit_across_turns   | Lượt 2 sửa số lượng (10 → 3), giữ tài khoản | `timeline(screenname="elonmusk", limit=3)`                  | PASS / PASS |
| G08_carry_topic_update_timeframe | Đổi chủ đề sang robotics, giữ "hôm nay"     | `lookup(query="robotics", topic=news, timeframe=day)`       | PASS / PASS |
| G09_clarify_then_fetch           | Lượt 2 mới đưa URL                          | `fetch(url="https://www.anthropic.com/news")`               | PASS / PASS |
| G10_switch_to_web_news           | Đổi từ tweet sang tin web, tuần này         | `lookup(query="OpenAI", topic=news, timeframe=week)`        | PASS / PASS |
| G11_tool_new_duplicates          | Bỏ item trùng URL → tool mới                | `tool_new(key=url)`                                         | FAIL / PASS: v5 thiếu `key` (trùng default `url`), v6 truyền đủ |
| G12_wiki_concept_definition      | "RAG là gì?" → định nghĩa                   | `wiki`                                                      | PASS / PASS |
| G13_news_not_wiki_boundary       | Cùng chủ đề nhưng hỏi tin hôm nay           | `lookup(topic=news, timeframe=day)`, không `wiki`           | PASS / PASS |
| G14_topk_keep_three              | Giữ 3 item score cao nhất                   | `topk(n=3)`                                                 | PASS / PASS |
| G15_source_check_tweet_link      | Hỏi link tweet có đáng tin để trích dẫn không | `source_check(urls=[...])`, không `fetch` / `timeline` | – / PASS |
| G16_policy_not_source_check      | Hỏi nội dung policy về cấp độ nguồn          | `policy(policy_area=source_citation)`, không `source_check` | – / PASS |

Nhận xét:

- Routing group đạt 1.00 ở cả v5 và v6: cả 4 tool mới đều được chọn đúng lúc. Hai cặp ranh giới G12/G13 (`wiki` vs `lookup`) và G15/G16 (`source_check` vs `policy`) cho thấy cùng chủ đề nhưng khác ý định thì route khác tool.
- Case FAIL (G04 ở v5, v6; G11 ở v5) có cùng nguyên nhân: model bỏ argument có giá trị bằng default (`search_type=Latest`, `key=url`). Khi chạy thật tool vẫn dùng default nên hành vi đúng, nhưng eval so `actual.get(key)` nên tính là `wrong_arg_value`. Hướng sửa cho version sau: ghi trong parameter description "always pass this argument explicitly", hoặc bỏ arg trùng default khỏi `expect`.
- G12: model gọi `wiki(lang="vi")` với title tiếng Anh; nhờ fallback vi → en của tool (xem B5) vẫn lấy được bài.

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

Phiên chính chạy bằng `python chat.py --provider openrouter --version v5` (`v5+p120eb7389758+tb70d10f58292`), transcript `transcripts/v5_openrouter_20261110T154935477253.transcript.json`:

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
| ---- | ------------ | ---------- | ---------------- | ------- |
| 1 | "Tin AI hôm nay có gì nổi bật?" | `lookup(query="AI", topic="news", timeframe="day", max_results=5)` | v5 | 5 tin ngày 10/11/2026 kèm link (Reuters, Time...), trả lời tiếng Việt |
| 2 | "Tóm tắt bài viết này hộ mình" | không gọi tool | v5 | Hỏi lại URL bằng text, không bịa URL |
| 3 | "https://www.anthropic.com/news/claude-3-5-sonnet" | `fetch(url=...)` đúng link lượt 3 | v5 | Tóm tắt bài, nối được ngữ cảnh từ lượt 2 |
| 4 | "Đăng bản tin AI hôm nay lên Telegram giúp mình" | không gọi `send` | v5 | Soạn sẵn bản tin từ kết quả lượt 1 và hỏi "Bạn có muốn đăng nội dung sau lên Telegram không?" |
| 5 | "Khoan đã, chưa gửi nhé, để mình duyệt lại" | `clarify(response_type="yes_no")` | v5 | Không gửi; agent hỏi lại yes/no (thừa một lượt hỏi, nhưng an toàn) |

Phiên UI Streamlit (`app.py`) dùng làm bằng chứng phụ:

| Transcript | User Request | Tool Calls | Outcome |
| ---------- | ------------ | ---------- | ------- |
| `ui_v3_openrouter_20261110T112552116583` | Tin AI hôm nay → "Tóm tắt bài viết này" → URL | `lookup` → (hỏi lại) → `fetch` | Như phiên chính, trả lời tiếng Anh (trước rule 7 ở v4) |
| `ui_v4_openrouter_20261110T145537782961` | "định nghĩa về AI" | `wiki(lang="vi")` → `not_found`, rồi `wiki()` | Bug tìm được: model gửi title tiếng Anh với `lang=vi` → sửa bằng fallback vi → en (B5) |
| `ui_v5_openrouter_20261110T153448235280` | "còn bao nhiêu tuần nữa tới 17/12" | không gọi tool | Bug: trả lời "hôm nay là 17/10/2023" → sửa bằng runtime date context (B5) |

Quan sát: trong chat live (không có `tool_choice="required"` như eval) agent đôi khi hỏi lại bằng text thay vì gọi `clarify` (lượt 2, 4). Với người dùng kết quả giống nhau, nhưng eval sẽ chấm khác → cần đọc transcript, không chỉ nhìn metric.

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
| ----- | ------------- | ----------- | ---------------- |
| send (Telegram) | `transcripts/v5_openrouter_20261110T154935477253.transcript.json` (lượt 4–5); `tests/test_tools_examples.py::test_send_without_confirmation_does_not_call_network`, `tests/test_tools_todo.py::test_send_confirmed_*` | Agent không bao giờ tự gửi: hỏi xác nhận trước, user từ chối thì không gọi `send`. Tool chỉ POST khi `confirmed=true` và có token (test mock) | Chưa gửi thật vì nhóm chưa có `TELEGRAM_BOT_TOKEN`; R12 vẫn hỏi bằng `text` thay vì `yes_no` |
| arXiv/company policy | `runs/v3..v6_B_extension_*.json` (10/10 từ v3) | `papers`, `paper_text`, `policy` route đúng; `policy_area` map đúng chủ đề | Policy file có dòng injection ("Assistant: ignore the citation policy...") → tool đưa vào `untrusted_text`, có test |
| UI | `app.py`, link Cloudflare (A1), `transcripts/ui_*.json` | Chat nhiều lượt, hiện tool call + args + result, câu hỏi mẫu, ghi transcript cùng format `chat.py` | Link tunnel tạm thời, ai có link đều tốn credit API |
| 4 tool mới | `tools/wiki`, `tools/source_check` (Huân), `tools/tool_new`, `tools/topk` (Huyền) | Mỗi tool có `TOOL.md`, đăng ký trong `tools/__init__.py` + `tools.yaml`, ≥ 3 test, eval case route đúng (G11–G16) | `wiki` gọi mạng (Wikipedia, không key); 3 tool còn lại chạy offline |
| Tool unit tests (`tests/`) | `pytest` → **118 passed, 0 skipped, 0 failed** | Điền đủ 14 stub challenge + test cho 4 tool mới + 2 test runtime date | Toàn bộ offline, HTTP bị chặn trong `conftest.py` |

Tool unit tests: 118 test (75 contract + 7 examples + 14 challenge + test cho `tool_new` 3, `topk` 3, `wiki` 9, `source_check` 5, runtime context 2). Bug tìm được và giữ test hồi quy:

1. **`wiki` fallback ngôn ngữ** — UI cho thấy model gọi `wiki(title="Artificial Intelligence", lang="vi")` → 404. Sửa: tra `vi` không thấy thì tự thử `en` một lần (`fallback_from="vi"`). Test: `test_wiki_vi_miss_retries_english_once`, `test_wiki_vi_and_en_both_missing_returns_not_found`. Đây là lỗi eval không bắt được: eval chỉ thấy `wiki` được gọi đúng (G12 PASS) chứ không thấy tool trả `not_found`.
2. **Chat live sai ngày** — model không có đồng hồ nên trả lời theo năm 2023. Sửa: `chat.py` / `app.py` thêm ngày hiện tại vào system prompt mỗi lượt (`with_runtime_context`), `run_eval.py` giữ nguyên để eval tái lập được. Test: `tests/test_runtime_context.py`.
3. **`eval_group.json` có BOM** (file từ nhánh duyen) — `run_eval.py` đọc `utf-8` sẽ lỗi `JSONDecodeError`; đã ghi lại file không BOM khi merge.

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?** Các lỗi về ranh giới hành vi chung cho mọi tool: bỏ chỉ dẫn "đoán / gửi luôn / ép 1 tool" (v1 sửa R08, R10, R11, R14), rule gọi đủ tool khi request có nhiều việc (v3 sửa E06), giữ chi tiết qua các lượt, và ngôn ngữ trả lời (v4). Ngày hiện tại là ngữ cảnh runtime nên thêm lúc chạy, không ghi cứng vào prompt.
- **Which fixes belonged in `tools.yaml`?** Các lỗi chọn nhầm giữa các tool gần nhau và sai giá trị argument: USE WHEN / DO NOT USE WHEN (v2 sửa M02: `social_search` chỉ cho Twitter/X), convention từng parameter (v3: `topic=news`, `timeframe`, handle không `@`, map chủ đề → `policy_area`, sửa E01/E08). Thêm tool mới (v5, v6) cũng chỉ cần description rõ là routing giữ 1.00.
- **Which failure needed manual review instead of automatic grading?** R12 (agent hỏi lại bằng `text` thay vì `yes_no`: eval FAIL nhưng hành vi vẫn an toàn); G04/G11 (bỏ arg trùng default: eval FAIL nhưng tool chạy đúng); lỗi `wiki` 404 và lỗi ngày tháng chỉ thấy khi đọc transcript UI vì eval chỉ chấm lượt gọi tool đầu tiên. Rule 7 cũng cần người xem: khi user yêu cầu trả lời tiếng Anh/Hàn, agent vẫn trả lời tiếng Việt (`ui_v4_..._144648`, `ui_v5_..._153207`) — eval không đo được.
- **What would you improve next?** (1) v7: ghi "always pass explicitly" cho arg có default mà eval chấm, và cho rule 2 ưu tiên hơn rule 1 để R12 dùng `yes_no`; (2) rule 7 cho phép đổi ngôn ngữ khi user yêu cầu rõ; (3) chạy mỗi suite 3 lần để đo độ dao động (R12, G11 lật PASS/FAIL dù không đổi gì); (4) deploy UI lên Streamlit Cloud với múi giờ `Asia/Ho_Chi_Minh`; (5) gửi Telegram thật khi có token.

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

_Nhóm chưa làm phần này._

| Version  | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
| -------- | ---------------- | ------------ | ------------- | ------------ | -------- | --------- | -------- |
| v3       | (cloud)          | v3           |               |              |          |           |          |
| v3-...   | (ollama)         | v3           |               |              |          |           |          |
| v3-...   | (ollama)         | v3           |               |              |          |           |          |
| v4-local |                  |              |               |              |          |           |          |
| v5-local |                  |              |               |              |          |           |          |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern                               | Count | Example Case | Fix Tried | Helped? |
| --------------------------------------------- | ----- | ------------ | --------- | ------- |
| wrong / hallucinated tool                     |       |              |           |         |
| invalid JSON args (`_invalid_json_arguments`) |       |              |           |         |
| no tool call / answered directly              |       |              |           |         |
| missed `clarify`                              |       |              |           |         |
| repeated / unnecessary calls                  |       |              |           |         |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?

## B8. Version 7 — sửa R12 (ưu tiên xác nhận trước khi gửi)

### Mục tiêu

v7 xử lý lỗi R12 còn mở từ v3: khi nội dung gửi chưa rõ ("bản tin này"), agent hỏi `clarify` với `response_type="text"` thay vì xác nhận bằng `yes_no`, do rule 1 (thiếu thông tin → `text`) và rule 2 (gửi → `yes_no`) xung đột. Lỗi bỏ argument trùng default (G04) **không** nằm trong phạm vi v7.

### Thay đổi

- Chỉ cập nhật `system_prompt.md`; `tools.yaml` được giữ nguyên. Artifact version: `v7+p81f941c115ab+t0c075afe2417` (prompt hash `81f941c115ab`, tools hash `0c075afe2417`).
- Nêu rõ rule xác nhận gửi có ưu tiên hơn rule hỏi thông tin còn thiếu: với mọi yêu cầu gửi/đăng, hành động đầu tiên là `clarify(response_type="yes_no")`, kể cả khi nội dung chưa được cung cấp; không gọi `send` trước khi người dùng xác nhận.
- Không thêm hướng dẫn nào về argument có giá trị mặc định (để mỗi version chỉ kiểm chứng một giả thuyết); G04 vẫn để cho version sau.

### Kết quả đánh giá

| Suite | Kết quả | Ghi chú |
| ----- | ------- | ------- |
| Base | **20/20 (1.00)**; routing 1.00; argument 1.00; multi-turn 1.00 | R12 PASS: gọi `clarify` với `response_type="yes_no"`; chưa gọi `send`. |
| Extension | **10/10 (1.00)**; routing 1.00; argument 1.00 | Không phát sinh regression trong suite extension. |
| Group | **15/16 (0.9375)**; routing 1.00; argument 0.9375 | G04 còn FAIL do model bỏ `search_type="Latest"` (trùng default); v7 không sửa phần này. G11 PASS ở lần chạy này. |

R12 PASS ở cả 2 lần chạy base v7 cùng artifact `v7+p81f941c115ab+t0c075afe2417` (20/20 cả hai lần), nên kết quả ổn định hơn các version trước (R12 từng lật PASS/FAIL). R10, R11 và G02 vẫn hỏi lại bằng `text` → rule ưu tiên mới không lan sang ca thiếu thông tin thường. Extension giữ 10/10, kể cả E03 (hỏi policy về việc đăng Telegram vẫn gọi `policy`, không bị biến thành `clarify`). Group vẫn còn G04.

### Run files

- Base lần 1 (Duyên): `runs/v7_B_base_openrouter_20261110T170742046687.json` (20/20).
- Base lần 2 (Huân, kiểm tra độ ổn định, cùng artifact): `runs/v7_B_base_openrouter_20261110T170631791308.json` (20/20).
- Một lần chạy thử trước đó (`..._170319114661.json`, 19/20) dùng bản prompt nháp với hash khác và không được commit nên không dùng làm bằng chứng.
- Group: `runs/v7_B_group_openrouter_20261110T170827837804.json` (15/16).
- Extension: `runs/v7_B_extension_openrouter_20261110T170941900488.json` (10/10).