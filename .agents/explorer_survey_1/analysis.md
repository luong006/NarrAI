# Phân Tích Kỹ Thuật Chuyên Sâu: Triệt Tiêu Lỗi Hiển Thị Raw JSON Trong Editor Khi Copilot Sửa Bản Thảo (Requirement R1)

## 1. Tóm Tắt Tổng Quan (Executive Summary)

Khi người dùng ra lệnh cho AI Co-pilot chỉnh sửa trực tiếp bản thảo (ví dụ: *"tôi muốn một mở đầu khác"*, *"sửa lại đoạn kết kịch tính hơn"* hoặc bấm nút Quick Prompt), hệ thống NarrAI gặp lỗi rò rỉ mã JSON nguyên bản (`raw JSON`) dạng `{"updated_story_content": "..."}` và/hoặc các ký tự thoát dòng (`\n\n`) hiển thị trực tiếp lên khung soạn thảo văn xuôi của tác giả.

Qua quá trình điều tra toàn diện từ Backend (`copilot_agent.py`, `main.py`) đến Frontend (`page.tsx`, `StoryEditor.tsx`, `AICopilotPanel.tsx`, `api.ts`), nguyên nhân cốt lõi bao gồm:
1. **Thuật toán `unwrap_story_prose` ở backend bị thiếu sót nghiêm trọng**: Chỉ kiểm tra key cấp 1 `parsed.get("updated_story_content")` mà bỏ qua cấu trúc lồng nhau (`action_params.updated_story_content`); điều kiện giải mã ký tự xuống dòng `if "\\n" in text and "\n" not in text` hoàn toàn vô hiệu hóa việc thay thế khi văn bản có bất kỳ dấu xuống dòng thực tế nào.
2. **Cơ chế parse JSON mong manh trong `_perform_direct_manuscript_edit`**: Sử dụng `json.loads` mặc định (không có `strict=False`). Khi mô hình sinh ra hội thoại tiếng Việt có dấu ngoặc kép hoặc xuống dòng thực tế trong chuỗi, `json.loads` ném ngoại lệ `JSONDecodeError`, khiến backend âm thầm trả về `None` rồi rơi vào nhánh fallback không được làm sạch.
3. **Frontend xử lý nông (Single-pass), regex sai lệch và chặn thay thế `\n`**: `page.tsx` chỉ parse 1 lần duy nhất, regex non-greedy bị ngắt cụt nếu hội thoại có dấu ngoặc kép kết thúc câu, và điều kiện `!trimmed.includes("\n\n")` ngăn cản 100% việc convert `\n` sang newline thực tế nếu văn bản đã có đoạn văn.
4. **Vòng lặp nhiễm bẩn Database**: Khi backend lưu trữ chuỗi JSON nguyên bản vào cơ sở dữ liệu SQLite (`Story.story_content`), các lần gọi Copilot tiếp theo sẽ gửi chính chuỗi JSON này làm `current_story`, khiến LLM sinh ra JSON lồng 2-3 lớp (`{"updated_story_content": "{\"updated_story_content\": ...}"}`).

---

## 2. Phạm Vi & Ranh Giới Khảo Sát (Scope & Boundaries)

- **Backend**:
  - `backend/agents/copilot_agent.py`: Hàm `unwrap_story_prose()`, prompt `COPILOT_SYSTEM_PROMPT`, prompt `DIRECT_EDIT_PROMPT`, hàm nhận diện ý định `_is_direct_edit_request()`, hàm thực thi sửa trực tiếp `_perform_direct_manuscript_edit()`, và hàm xử lý sự kiện `process_event()`.
  - `backend/main.py`: Endpoint `POST /api/copilot-event`, cơ chế lấy context bộ nhớ `get_story_session()`, và logic lưu trữ `Story.story_content` vào DB.
  - `backend/agents/editor_agent.py` & `backend/agents/story_generator.py`: Kiểm tra các đường dẫn phụ trợ (`/api/edit-text`, `/api/chat`).
- **Frontend**:
  - `frontend/src/app/page.tsx`: Hàm `handleSendCopilotMessage`, logic bóc tách `res.data.action === "edit_story_direct"`, logic fallback chat, và cơ chế khôi phục từ history.
  - `frontend/src/components/editor/StoryEditor.tsx`: Cơ chế đồng bộ `useEffect` với `contentEditable` div (`whitespace-pre-wrap`).
  - `frontend/src/components/editor/AICopilotPanel.tsx`: Khung chat và các nút Quick Prompts (ví dụ: *"Tạo phần mở đầu khác đi"*).
  - `frontend/src/lib/api.ts` & `frontend/src/lib/types.ts`: Cấu trúc dữ liệu `CopilotEventResponse`.

---

## 3. Bản Đồ Dòng Dữ Liệu (Data Flow Architecture)

Dưới đây là sơ đồ luồng dữ liệu từ khi người dùng gửi lệnh đến khi Editor hiển thị:

```
[User Action in AICopilotPanel]
Người dùng gõ: "tôi muốn một mở đầu khác" (hoặc click Quick Prompt)
                     │
                     ▼
[frontend/src/app/page.tsx: handleSendCopilotMessage] (Line 320-335)
- Cắt ngữ cảnh: storyContext = storyContent.slice(0, 15000)
- Gọi API: api.sendCopilotEvent(sessionId, storyId, "USER_CHAT", payload)
                     │ HTTP POST /api/copilot-event
                     ▼
[backend/main.py: copilot_event] (Line 641-665)
- Nhận request: session_id, story_id, event_type="USER_CHAT", event_data
- Nạp memory từ DB / STORY_SESSIONS
- Gọi: agent = get_copilot() -> agent.process_event(...)
                     │
                     ▼
[backend/agents/copilot_agent.py: process_event] (Line 181-215)
- Parse payload: user_message, current_story
- Kiểm tra intent: _is_direct_edit_request(user_message)
  ┌──────────────────┴──────────────────┐
  │ [Matched Intent: True]              │ [Not Matched: False]
  ▼                                     ▼
[_perform_direct_manuscript_edit]     [General Master Controller]
- Prompt DIRECT_EDIT_PROMPT           - Prompt COPILOT_SYSTEM_PROMPT
- LLM Chat (Groq GPT-OSS-120B)        - LLM Chat (Groq GPT-OSS-120B)
- Parse JSON output                   - Parse JSON output
  │                                     │
  └──────────────────┬──────────────────┘
                     ▼
[backend/agents/copilot_agent.py: unwrap_story_prose] (Line 22-50)
  ⚠️ LỖI 1: Chỉ lấy parsed.get("updated_story_content"), bỏ qua action_params.
  ⚠️ LỖI 2: if "\\n" in text and "\n" not in text: skip toàn bộ replace \n.
  ⚠️ LỖI 3: Regex fallback dừng non-greedy tại dấu ngoặc kép hội thoại.
                     │
                     ▼
[backend/main.py: copilot_event (Persistence)] (Line 678-703)
- Gọi unwrap_story_prose lần 2
- Ghi đè vào DB: story.story_content = updated_content (Nhiễm bẩn DB nếu unwrap lỗi)
- Trả về HTTP: {"status": "success", "data": result}
                     │ HTTP Response JSON
                     ▼
[frontend/src/app/page.tsx: handleSendCopilotMessage] (Line 337-377)
- Nhận action === "edit_story_direct"
- newContent = params.updated_story_content
  ⚠️ LỖI 4: Chỉ parse JSON 1 lần (Single-pass), không hỗ trợ double/nested JSON.
  ⚠️ LỖI 5: Chỉ check parsed.updated_story_content.
  ⚠️ LỖI 6: if (trimmed.includes("\\n") && !trimmed.includes("\n\n")): bỏ qua replace \n nếu đã có \n\n.
- setStoryContent(newContent)
                     │
                     ▼
[frontend/src/components/editor/StoryEditor.tsx] (Line 35-41, 107-121)
- useEffect: editorRef.current.innerText = content;
- Render DOM: Div contentEditable có whitespace-pre-wrap
  ==> KẾT QUẢ: Hiển thị nguyên văn chuỗi raw JSON hoặc ký tự \n\n lên màn hình!
```

---

## 4. Chi Tiết Các Lỗ Hổng & Vị Trí Code (Detailed Code Audit)

### 4.1. Lỗ hổng tại `backend/agents/copilot_agent.py`

#### A. Hàm `unwrap_story_prose` (Dòng 22 - 50)
```python
22: def unwrap_story_prose(text: str) -> str:
23:     """Recursively unwraps stringified JSON or markdown codeblocks to ensure pure story prose."""
24:     if not text:
25:         return ""
26:     text = str(text).strip()
27:     
28:     # Strip markdown code blocks
29:     text = re.sub(r'^```(?:json|markdown)?\s*', '', text, flags=re.MULTILINE)
30:     text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE).strip()
31:     
32:     # Check if text is a JSON string or contains updated_story_content
33:     if (text.startswith('{') and text.endswith('}')) or '"updated_story_content"' in text:
34:         try:
35:             parsed = json.loads(text, strict=False)
36:             if isinstance(parsed, dict) and parsed.get("updated_story_content"):
37:                 return unwrap_story_prose(parsed["updated_story_content"])
38:         except Exception:
39:             # Regex fallback to extract inner string from "updated_story_content": "..."
40:             match = re.search(r'"updated_story_content"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
41:             if match:
42:                 inner = match.group(1)
43:                 inner = inner.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
44:                 return unwrap_story_prose(inner)
45:     
46:     # If text still has literal "\n\n" instead of real newlines
47:     if "\\n" in text and "\n" not in text:
48:         text = text.replace('\\n', '\n')
49:         
50:     return text.strip()
```

**Các sai lầm cụ thể**:
1. **Dòng 36**: `parsed.get("updated_story_content")`:
   Khi LLM trả về JSON cấu trúc Master Controller:
   `{"action": "edit_story_direct", "action_params": {"updated_story_content": "..."}}`
   `parsed.get("updated_story_content")` trả về `None`! `json.loads` thành công nên KHÔNG nhảy vào `except Exception:` (dòng 38), regex fallback không chạy. Hàm thoát ra khỏi khối `if` và trả về nguyên khối raw JSON string!
2. **Dòng 47**: `if "\\n" in text and "\n" not in text:`
   Điều kiện này có logic ngược hoàn toàn: Nếu trong văn bản có BẤT KỲ ký tự xuống dòng thực tế `\n` nào (ví dụ dòng tiêu đề, hoặc đoạn văn markdown phía trước), thì `"\n" not in text` trả về `False`! Kết quả là `text.replace('\\n', '\n')` KHÔNG BAO GIỜ được gọi. Các ký tự `\n\n` do LLM sinh ra trong chuỗi JSON stringified vẫn giữ nguyên dạng 4 ký tự `\`, `n`, `\`, `n`.
3. **Dòng 40**: `r'"updated_story_content"\s*:\s*"((?:[^"\\]|\\.)*)"'`
   Biểu thức regex này match theo kiểu greedy trong nhóm `((?:[^"\\]|\\.)*)` nhưng phụ thuộc vào dấu ngoặc kép kết thúc `"`. Nếu bản thảo truyện có đối thoại tiếng Việt chưa được escape chuẩn (ví dụ: `Nam nói: "Đi thôi!"`), regex sẽ dừng ngay tại dấu ngoặc kép đầu tiên của lời thoại, cắt cụt 90% nội dung truyện!
4. **Dòng 29-30**: Sử dụng `re.MULTILINE` với `^```...` và ````\s*$`. Nếu LLM chèn markdown codeblock có lời dẫn trước/sau (ví dụ: `Đây là bản thảo mới:\n```json\n...`), code không bóc tách được khối JSON.

---

#### B. Hàm `_perform_direct_manuscript_edit` (Dòng 135 - 179)
```python
150:             cleaned = re.sub(r'```(?:json)?\s*', '', resp).strip()
151:             match = re.search(r'\{.*\}', cleaned, re.DOTALL)
152:             if match:
153:                 data = json.loads(match.group(0))
154:                 if data.get("updated_story_content"):
155:                     clean_story = unwrap_story_prose(data["updated_story_content"])
...
177:         except Exception as e:
178:             safe_log(f"[Copilot Direct Edit] Error: {e}")
179:         return None
```
**Các sai lầm cụ thể**:
1. **Dòng 153**: `data = json.loads(match.group(0))` KHÔNG có tham số `strict=False`. Theo chuẩn JSON RFC 8259, các ký tự điều khiển (control characters như `\n`, `\r`, `\t`) bên trong chuỗi string literal là bất hợp pháp. Khi LLM sinh ra truyện dài có ngắt đoạn bằng Enter thực tế bên trong chuỗi JSON, `json.loads` văng lỗi `JSONDecodeError: Invalid control character`.
2. Khối `try...except` bao trùm toàn bộ. Khi `json.loads` văng lỗi ở dòng 153, luồng thực thi nhảy ngay xuống dòng 177 (`except Exception: return None`), KHÔNG BAO GIỜ chạy vào nhánh `elif len(cleaned) > 100` (dòng 165).
3. Kết quả: Hàm trả về `None`. Tại `process_event` (dòng 205), hệ thống bỏ qua và rơi xuống Step 2 (General Master Controller), nơi tiếp tục có nguy cơ parse lỗi tương tự.

---

#### C. Hàm `_is_direct_edit_request` (Dòng 123 - 134)
```python
126:         edit_keywords = [
127:             "mở đầu", "đoạn mở", "mở bài", "đoạn kết", "kết thúc", "kết bài",
128:             "sửa lại", "thay đổi", "viết lại", "đổi tên", "chỉnh sửa", "thay phần",
129:             "thay đoạn", "tạo phần", "làm lại", "cắt bỏ", "thêm cảnh", "thêm đoạn",
130:             "bỏ đoạn", "đổi phong cách", "đổi giọng văn", "tăng kịch tính", "sửa câu",
131:             "khác đi", "hay hơn", "ngắn lại", "dài ra", "u tối hơn", "hài hước hơn"
132:         ]
```
- Các lệnh ngắn hoặc thông dụng của người dùng như: *"sửa bản thảo"*, *"chỉnh chương này"*, *"thay cái kết"*, *"đổi bối cảnh"*, *"bớt thoại đi"*, *"thêm miêu tả"* không nằm trong danh sách từ khóa chính xác (`sửa` đơn lẻ, `chỉnh`, `thay`, `đổi` không đi kèm từ ghép tương ứng). Khi đó, intent bị nhận định sai là `False`, rơi vào prompt tổng quát của Master Controller.

---

### 4.2. Lỗ hổng tại `backend/main.py` (Dòng 678 - 704)

```python
678:         if result.get("action") == "edit_story_direct":
679:             params = result.get("action_params", {})
680:             updated_content = params.get("updated_story_content")
681:             if updated_content:
682:                 from agents.copilot_agent import unwrap_story_prose
683:                 clean_prose = unwrap_story_prose(updated_content)
684:                 params["updated_story_content"] = clean_prose
685:                 updated_content = clean_prose
686: 
687:             if updated_content and current_user:
688:                 db = SessionLocal()
...
697:                     story.story_content = updated_content
698:                     story.word_count = len(updated_content.split())
699:                     db.commit()
```
- Nếu `unwrap_story_prose` ở dòng 683 thất bại và trả về chuỗi JSON thô, `main.py` sẽ lưu trực tiếp chuỗi JSON thô này vào cột `story.story_content` trong DB.
- Khi người dùng refresh trang hoặc gọi API tiếp theo, `story_content` bị ô nhiễm JSON sẽ được nạp làm `current_story` gửi cho LLM. LLM nhìn thấy bản thảo hiện tại là JSON nên tiếp tục bọc thêm một lớp JSON mới khi chỉnh sửa.

---

### 4.3. Lỗ hổng tại `frontend/src/app/page.tsx` (Dòng 341 - 371)

```typescript
341:         if (action === "edit_story_direct") {
342:           let newContent = params.updated_story_content;
343:           if (newContent) {
344:             // Protect against stringified JSON or nested fields
345:             if (typeof newContent === "string") {
346:               let trimmed = newContent.trim();
347:               if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || trimmed.includes('"updated_story_content"')) {
348:                 try {
349:                   const parsed = JSON.parse(trimmed);
350:                   if (parsed.updated_story_content) {
351:                     trimmed = String(parsed.updated_story_content).trim();
352:                   }
353:                 } catch {
354:                   const match = trimmed.match(/"updated_story_content"\s*:\s*"([\s\S]*?)(?:"\s*\}|"$)/);
355:                   if (match && match[1]) {
356:                     trimmed = match[1];
357:                   }
358:                 }
359:               }
360:               // Convert literal \n to real newlines if stringified
361:               if (trimmed.includes("\\n") && !trimmed.includes("\n\n")) {
362:                 trimmed = trimmed.replace(/\\n/g, "\n").replace(/\\"/g, '"');
363:               }
364:               newContent = trimmed;
365:             }
366:             setUndoStack((prev) => [...prev, storyContent]);
367:             setStoryContent(newContent);
```

**Các sai lầm cụ thể**:
1. **Single-pass unwrap (Không đệ quy/vòng lặp)**: Khối `try...catch` ở dòng 348-358 chỉ chạy đúng 1 lần. Nếu backend gửi về JSON lồng 2 lớp:
   `"{\"updated_story_content\": \"{\\\"updated_story_content\\\": \\\"Đoạn văn...\\\"}\"}"`
   Frontend chỉ bóc được 1 lớp ngoài, lớp trong vẫn là `{"updated_story_content": "..."}` và gán thẳng vào `setStoryContent(newContent)`.
2. **Key hẹp**: Dòng 350 chỉ kiểm tra `parsed.updated_story_content`. Nếu JSON có dạng `{ action_params: { updated_story_content: "..." } }`, `parsed.updated_story_content` là `undefined`, `trimmed` không thay đổi và toàn bộ chuỗi JSON thô được hiển thị lên Editor.
3. **Regex fallback nguy hiểm (Dòng 354)**:
   `trimmed.match(/"updated_story_content"\s*:\s*"([\s\S]*?)(?:"\s*\}|"$)/)`
   Ký hiệu `([\s\S]*?)` là non-greedy. Nếu trong truyện có lời thoại kết thúc bằng `"}`, regex dừng ngay lập tức, làm mất toàn bộ phần sau của câu chuyện. Đồng thời, các ký tự thoát `\"` trong `match[1]` không được giải mã.
4. **Chặn replace `\n` vô lý (Dòng 361)**:
   `if (trimmed.includes("\\n") && !trimmed.includes("\n\n"))`
   Nếu bản thảo đã có bất kỳ khoảng cách đoạn văn thực tế `\n\n` nào, `!trimmed.includes("\n\n")` trả về `false`! Lệnh `trimmed.replace(/\\n/g, "\n")` bị bỏ qua 100%. Người dùng thấy hàng loạt ký tự `\n\n` xuất hiện trên Editor.
5. **Không làm sạch Markdown Codeblocks**: Nếu backend trả về văn bản bọc trong ````markdown ... ```` hoặc ````json ... ````, frontend không loại bỏ các fence này.

---

### 4.4. Cơ chế hiển thị tại `frontend/src/components/editor/StoryEditor.tsx`

```typescript
35:   // Sync content when streaming or loaded externally
36:   useEffect(() => {
37:     if (editorRef.current && !isTypingRef.current) {
38:       if (editorRef.current.innerText !== content) {
39:         editorRef.current.innerText = content;
40:       }
41:     }
42:   }, [content]);
...
108:           <div
109:             ref={editorRef}
110:             contentEditable
...
118:             className="outline-none font-serif text-slate-900 dark:text-slate-100 text-base sm:text-lg leading-[1.85] tracking-wide whitespace-pre-wrap min-h-[70vh]"
119:           />
```
- `StoryEditor` hiển thị trực tiếp giá trị `content` thông qua `innerText` trên một thẻ `div` có thuộc tính CSS `whitespace-pre-wrap`.
- Do không có bất kỳ bộ lọc phòng thủ (Sanitizer Guard) nào tại tầng Editor component, bất kỳ ký tự rác nào từ state `storyContent` (như `{`, `}`, `"updated_story_content"`, `\n\n`) đều lập tức đập thẳng vào mắt người dùng.

---

## 5. Bảng Tổng Hợp Các Tình Huống Gây Lỗi (Edge Cases & Failure Modes)

| STT | Kịch bản đầu vào từ LLM / Người dùng | Hiện tượng lỗi quan sát được | Nguyên nhân kỹ thuật |
|---|---|---|---|
| 1 | Người dùng ra lệnh: *"tôi muốn một mở đầu khác"* | Editor hiển thị `{"updated_story_content": "..."}` | LLM bọc JSON kép hoặc trả về `action_params`, backend & frontend chỉ unwrap 1 cấp và tìm key phẳng. |
| 2 | Bản thảo có lời thoại: `An nói: "Mình đi thôi!"` | Editor bị cắt ngắn còn `An nói: ` hoặc crash parse | `json.loads` không có `strict=False`, regex non-greedy bị dừng sớm tại dấu ngoặc kép. |
| 3 | LLM sinh ra ký tự `\n\n` thoát dòng trong JSON | Editor hiển thị chữ `\n\n` nguyên bản thay vì xuống dòng | Điều kiện `"\n" not in text` (backend) và `!trimmed.includes("\n\n")` (frontend) chặn đứng việc replace. |
| 4 | LLM trả về văn bản bọc trong ````json ... ```` | Editor hiển thị cả thẻ backticks và JSON | Regex stripping chỉ bắt đầu dòng có multiline, frontend không có bộ lọc fence. |
| 5 | Người dùng reload trang hoặc mở lại lịch sử truyện | Editor tải lại chuỗi JSON cũ | `main.py` đã lưu chuỗi JSON chưa unwrap vào SQLite DB `story.story_content`. |
| 6 | Người dùng dùng lệnh sửa nhưng không khớp từ khóa | Copilot chỉ chat tư vấn, không sửa truyện | `_is_direct_edit_request` thiếu các từ khóa đơn lẻ như `sửa`, `chỉnh`, `đổi`, `thay`. |

---

## 6. Chiến Lược Kiến Trúc Sửa Chữa Toàn Diện (Architectural Fix Strategy)

Để triệt tiêu 100% lỗi hiển thị raw JSON và ký tự thoát dòng, kiến trúc giải pháp phải áp dụng mô hình **Phòng thủ đa tầng theo chiều sâu (Defense-in-Depth)**:

```
[Layer 1: Prompt Hardening]
Yêu cầu LLM xuất văn xuôi thuần túy Markdown, cấm lồng JSON
                 │
                 ▼
[Layer 2: Backend Deep Recursive Sanitizer (unwrap_story_prose)]
Vòng lặp giải mã đa cấp + Quét mọi keys khả dĩ + Unescape \n unconditional
                 │
                 ▼
[Layer 3: Backend Resilient Parsing in CopilotAgent]
strict=False + Regex fallback không ngắt cụt + Fallback văn xuôi nếu len > 50
                 │
                 ▼
[Layer 4: Database Persistence Safety Check in main.py]
Chặn lưu chuỗi có định dạng JSON vào DB, đảm bảo DB luôn chứa thuần Markdown
                 │
                 ▼
[Layer 5: Frontend Deep Recursive Unwrapper (page.tsx)]
Vòng lặp giải mã frontend + Phá bỏ điều kiện chặn \n + Regex làm sạch
                 │
                 ▼
[Layer 6: Editor Component Final Defense (StoryEditor.tsx)]
Phát hiện và tự động giải mã chuỗi JSON nếu lọt vào component trước khi gán innerText
```

### 6.1. Thiết kế chi tiết Layer 1 & 2: Backend `copilot_agent.py`

#### A. Hàm `unwrap_story_prose` hoàn thiện
Cần được nâng cấp thành một hàm lặp đa vòng (Multi-iteration Unwrapper, tối đa 10 vòng):
1. **Loại bỏ Codeblocks và Lời dẫn**:
   - Dùng regex bóc sạch ```json ... ```, ```markdown ... ```, hoặc ``` ... ``` kể cả khi có khoảng trắng hoặc lời dẫn xung quanh.
2. **Kiểm tra JSON linh hoạt**:
   - Nếu chuỗi bắt đầu bằng `{` hoặc có cấu trúc `{...}`:
     - Thử `json.loads(text, strict=False)`.
     - Nếu kết quả là chuỗi (`str`), tiếp tục vòng lặp.
     - Nếu kết quả là `dict`, duyệt qua danh sách các key ưu tiên:
       `["updated_story_content", "story_content", "story", "content", "new_story_content", "revised_text", "text"]`.
     - Nếu không thấy ở cấp 1, kiểm tra trong `parsed.get("action_params", {})`.
     - Nếu vẫn không thấy nhưng `dict` có duy nhất 1 key chứa chuỗi dài (> 30 ký tự), lấy chuỗi đó.
3. **Regex Fallback thông minh (Không ngắt cụt đối thoại)**:
   - Nếu `json.loads` thất bại (do quotes trong đối thoại tiếng Việt), sử dụng regex tìm key `"updated_story_content"\s*:\s*"`.
   - Tìm điểm kết thúc bằng cách tìm ranh giới `",\s*"(?:summary_of_changes|message|action)"` hoặc `"\s*\}\s*$`.
   - Giải mã các ký tự escape: `\\"` thành `"`, `\\n` thành `\n`, `\\r` thành ``, `\\\\` thành `\`.
4. **Giải mã ký tự thoát dòng vô điều kiện (Unconditional Escape Decoding)**:
   - Thay thế `\\r\\n` -> `\n`.
   - Thay thế `\\n` -> `\n` bất kể trong chuỗi đã có `\n` hay chưa (Trong văn xuôi tiếng Việt, không bao giờ có chuỗi literal `\n`).
   - Chuẩn hóa ngắt dòng: thay `\r\n` -> `\n`, giới hạn tối đa 2 dấu `\n` liên tiếp (`\n\n`).

#### B. Nâng cấp `_perform_direct_manuscript_edit`
- Gọi `self.llm.chat(...)`.
- Khi parse JSON: dùng `json.loads(..., strict=False)`.
- Nếu parse lỗi: KHÔNG return `None` ngay; thử trích xuất bằng regex nội dung `updated_story_content`. Nếu trích xuất được hoặc nếu toàn bộ phản hồi là văn xuôi tiếng Việt (không có dấu ngoặc JSON), trực tiếp dùng làm bản thảo mới và trả về action `edit_story_direct`.

#### C. Nâng cấp `_is_direct_edit_request`
- Mở rộng thêm các từ khóa linh hoạt:
  `["sửa", "chỉnh", "đổi", "thay", "mở đầu", "kết", "viết lại", "viết tiếp", "bản thảo", "đoạn", "câu", "chương", "văn phong", "giọng văn", "kịch tính", "hồi hộp", "bỏ", "xóa", "thêm", "bớt", "tạo mới"]`.

---

### 6.2. Thiết kế chi tiết Layer 3 & 4: Backend `main.py`
Tại `POST /api/copilot-event`:
- Sau khi nhận `result` từ `agent.process_event`:
  - Luôn đảm bảo `clean_prose = unwrap_story_prose(params.get("updated_story_content"))`.
  - Cập nhật lại vào `params["updated_story_content"] = clean_prose`.
  - Trước khi commit vào DB (`story.story_content = updated_content`):
    - Kiểm tra bảo vệ: Nếu `clean_prose` vẫn còn dấu hiệu là JSON thô (`clean_prose.strip().startswith("{")`), thực hiện unwrap lần cuối hoặc trích xuất văn xuôi thuần túy. Tuyệt đối không commit raw JSON vào database.

---

### 6.3. Thiết kế chi tiết Layer 5: Frontend `page.tsx`
Xây dựng hàm tiện ích `unwrapStoryProseFrontend(content: string): string`:
1. Vòng lặp tối đa 5 lần giải mã.
2. Xóa bỏ hoàn toàn điều kiện `!trimmed.includes("\n\n")`. Thay bằng:
   `trimmed = trimmed.replace(/\\r\\n/g, '\n').replace(/\\n/g, '\n').replace(/\\"/g, '"');`
3. Parse `JSON.parse`: Hỗ trợ cả `parsed.updated_story_content`, `parsed.action_params?.updated_story_content`, `parsed.story_content`, `parsed.story`, v.v.
4. Gỡ bỏ triệt để các codeblocks ````markdown ... ```` hoặc ````json ... ````.
5. Áp dụng hàm này tại:
   - `handleSendCopilotMessage`: khi nhận `edit_story_direct`.
   - `chatCopilot`: nhánh fallback.
   - Khi load truyện từ lịch sử: `setStoryContent(unwrapStoryProseFrontend(story.story_content || ""))`.

---

### 6.4. Thiết kế chi tiết Layer 6: Frontend `StoryEditor.tsx`
Trong `StoryEditor.tsx`, tại `useEffect` đồng bộ `content`:
```typescript
  useEffect(() => {
    if (editorRef.current && !isTypingRef.current) {
      let displayContent = content;
      // Safety net: if content accidentally contains stringified JSON envelope
      if (typeof displayContent === "string" && (displayContent.startsWith("{") || displayContent.includes('"updated_story_content"'))) {
        displayContent = unwrapStoryProseFrontend(displayContent);
      }
      if (editorRef.current.innerText !== displayContent) {
        editorRef.current.innerText = displayContent;
      }
    }
  }, [content]);
```

---

## 7. Kế Hoạch Xác Minh Độc Lập (Independent Verification Plan)

Sau khi giải pháp được triển khai bởi Agent tiếp theo, các bước kiểm thử sau đây sẽ chứng minh yêu cầu R1 được thỏa mãn 100%:

1. **Kiểm thử cú pháp & build**:
   - Backend: Chạy `python -m py_compile backend/agents/copilot_agent.py backend/main.py`.
   - Frontend: Chạy `npm run build` trong thư mục `frontend/`.
2. **Kiểm thử Benchmark Copilot**:
   - Chạy `python backend/tests/run_full_system_benchmark.py`.
   - Xác nhận endpoint `POST /api/copilot-event` trả về `passed: True`, `status_code: 200`, và dữ liệu không chứa ký tự JSON rò rỉ.
3. **Kiểm thử Functional Trực tiếp**:
   - Gửi lệnh can thiệp: *"tôi muốn một mở đầu khác"*.
   - Xác nhận:
     - Editor cập nhật 100% văn xuôi tiếng Việt sạch sẽ định dạng Markdown.
     - 0% xuất hiện dấu ngoặc nhọn `{` hay `}` hoặc chuỗi `"updated_story_content"`.
     - 0% xuất hiện các ký tự thoát dòng `\n\n`. Các đoạn văn ngắt dòng tự nhiên và chuẩn xác.
