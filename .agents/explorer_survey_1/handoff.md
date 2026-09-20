# Handoff Report: Khảo Sát & Giải Pháp Triệt Tiêu Lỗi Raw JSON Trong Editor (Requirement R1)

**Agent**: `explorer_survey_1`  
**Parent Conversation ID**: `6bf39d70-f735-4c2a-8a7a-0d9642a300c3`  
**Handoff Type**: Hard (Investigation complete, actionable architecture proposal delivered)  

---

## 1. Observation

### 1.1. Backend `backend/agents/copilot_agent.py`
- **Dòng 22-50 (`unwrap_story_prose`)**:
  ```python
  33: if (text.startswith('{') and text.endswith('}')) or '"updated_story_content"' in text:
  34:     try:
  35:         parsed = json.loads(text, strict=False)
  36:         if isinstance(parsed, dict) and parsed.get("updated_story_content"):
  37:             return unwrap_story_prose(parsed["updated_story_content"])
  38:     except Exception:
  39:         # Regex fallback to extract inner string from "updated_story_content": "..."
  40:         match = re.search(r'"updated_story_content"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
  41:         if match:
  42:             inner = match.group(1)
  43:             inner = inner.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
  44:             return unwrap_story_prose(inner)
  46: # If text still has literal "\n\n" instead of real newlines
  47: if "\\n" in text and "\n" not in text:
  48:     text = text.replace('\\n', '\n')
  ```
  Quan sát thấy:
  - Nếu `parsed` là dictionary dạng `{ "action": "edit_story_direct", "action_params": { "updated_story_content": "..." } }`, `parsed.get("updated_story_content")` trả về `None`. Khối `try` kết thúc mà không bóc tách được, đồng thời vì không có lỗi nên không nhảy vào `except Exception:`. Toàn bộ chuỗi JSON thô bị trả về nguyên vẹn.
  - Dòng 47: Điều kiện `and "\n" not in text` khiến cho nếu chuỗi có chứa bất kỳ ký tự xuống dòng thực tế nào (`\n`), lệnh `text.replace('\\n', '\n')` bị bỏ qua 100%, để lại nguyên vẹn chuỗi `\n\n`.
  - Dòng 40: Regex fallback bắt đầu bằng `"((?:[^"\\]|\\.)*)"`. Nếu văn bản có đối thoại tiếng Việt chứa dấu ngoặc kép không escape (như `"Chào anh!"`), regex dừng ngay tại dấu ngoặc kép đầu tiên và làm mất phần còn lại của bản thảo.

- **Dòng 135-179 (`_perform_direct_manuscript_edit`)**:
  ```python
  152: if match:
  153:     data = json.loads(match.group(0))
  154:     if data.get("updated_story_content"):
  155:         clean_story = unwrap_story_prose(data["updated_story_content"])
  ...
  177: except Exception as e:
  178:     safe_log(f"[Copilot Direct Edit] Error: {e}")
  179: return None
  ```
  Quan sát thấy:
  - Dòng 153 gọi `json.loads(match.group(0))` không có `strict=False`. Khi LLM sinh ra truyện dài có chứa ký tự điều khiển (newline thực tế bên trong chuỗi JSON), hàm ném lỗi `JSONDecodeError`.
  - Lỗi này đẩy thẳng xuống dòng 177, log lỗi và trả về `None`, không chạy nhánh `elif len(cleaned) > 100` (dòng 165).
  - Tại `process_event` (dòng 205), khi hàm trả về `None`, hệ thống rơi xuống Step 2 (Master Controller) và gửi prompt tổng quát `COPILOT_SYSTEM_PROMPT`.

- **Dòng 126-133 (`_is_direct_edit_request`)**:
  ```python
  126: edit_keywords = [
  127:     "mở đầu", "đoạn mở", "mở bài", "đoạn kết", "kết thúc", "kết bài",
  128:     "sửa lại", "thay đổi", "viết lại", "đổi tên", "chỉnh sửa", "thay phần",
  ...
  131:     "khác đi", "hay hơn", "ngắn lại", "dài ra", "u tối hơn", "hài hước hơn"
  132: ]
  ```
  Quan sát thấy:
  - Thiếu các từ khóa phổ biến đơn lẻ: `sửa`, `chỉnh`, `thay`, `đổi`, `thêm`, `bớt`, `xóa`. Người dùng gõ *"sửa bản thảo"* hay *"thay cái kết"* sẽ bị đánh giá là `False`.

### 1.2. Backend `backend/main.py`
- **Dòng 678-703 (`copilot_event`)**:
  ```python
  678: if result.get("action") == "edit_story_direct":
  679:     params = result.get("action_params", {})
  680:     updated_content = params.get("updated_story_content")
  681:     if updated_content:
  682:         from agents.copilot_agent import unwrap_story_prose
  683:         clean_prose = unwrap_story_prose(updated_content)
  684:         params["updated_story_content"] = clean_prose
  685:         updated_content = clean_prose
  687:     if updated_content and current_user:
  ...
  697:         story.story_content = updated_content
  698:         story.word_count = len(updated_content.split())
  699:         db.commit()
  ```
  Quan sát thấy:
  - Nếu `clean_prose` chưa được giải mã sạch (vẫn là JSON), nó sẽ được commit trực tiếp vào database SQLite. Lịch sử bản thảo bị ô nhiễm vĩnh viễn và sẽ được gửi ngược lại vào LLM ở các turn tiếp theo.

### 1.3. Frontend `frontend/src/app/page.tsx`
- **Dòng 341-371 (`handleSendCopilotMessage`)**:
  ```typescript
  341: if (action === "edit_story_direct") {
  342:   let newContent = params.updated_story_content;
  343:   if (newContent) {
  344:     // Protect against stringified JSON or nested fields
  345:     if (typeof newContent === "string") {
  346:       let trimmed = newContent.trim();
  347:       if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || trimmed.includes('"updated_story_content"')) {
  348:         try {
  349:           const parsed = JSON.parse(trimmed);
  350:           if (parsed.updated_story_content) {
  351:             trimmed = String(parsed.updated_story_content).trim();
  352:           }
  353:         } catch {
  354:           const match = trimmed.match(/"updated_story_content"\s*:\s*"([\s\S]*?)(?:"\s*\}|"$)/);
  355:           if (match && match[1]) {
  356:             trimmed = match[1];
  357:           }
  358:         }
  359:       }
  360:       // Convert literal \n to real newlines if stringified
  361:       if (trimmed.includes("\\n") && !trimmed.includes("\n\n")) {
  362:         trimmed = trimmed.replace(/\\n/g, "\n").replace(/\\"/g, '"');
  363:       }
  364:       newContent = trimmed;
  365:     }
  366:     setUndoStack((prev) => [...prev, storyContent]);
  367:     setStoryContent(newContent);
  ```
  Quan sát thấy:
  - Chỉ parse 1 lần (Single-pass), không có vòng lặp unwrap nếu JSON lồng nhiều tầng.
  - Dòng 350 chỉ tìm `parsed.updated_story_content`, bỏ qua `parsed.action_params?.updated_story_content`.
  - Dòng 361: Điều kiện `!trimmed.includes("\n\n")` ngăn chặn việc thay thế `\n` sang newline thực nếu chuỗi đã có bất kỳ ngắt đoạn nào.
  - Dòng 354: Regex non-greedy `[\s\S]*?` cắt cụt đối thoại khi gặp dấu `"}`, và không unescape ký tự `\"`.

### 1.4. Frontend `frontend/src/components/editor/StoryEditor.tsx`
- **Dòng 35-41 & 107-121**:
  ```typescript
  37: if (editorRef.current.innerText !== content) {
  38:   editorRef.current.innerText = content;
  39: }
  ...
  118: className="... whitespace-pre-wrap ..."
  ```
  Quan sát thấy:
  - Component gán trực tiếp `content` vào `innerText`. Nếu `content` là raw JSON hoặc chứa `\n\n`, CSS `whitespace-pre-wrap` sẽ hiển thị nguyên văn lên màn hình soạn thảo của tác giả.

---

## 2. Logic Chain

1. **Từ Observation 1.1**: Mô hình LLM (Groq `gpt-oss-120b`) thường trả về phản hồi có cấu trúc JSON lồng nhau (`action_params`) hoặc định dạng chuỗi stringified. Khi LLM xuất ra đối thoại tiếng Việt có ngoặc kép hoặc xuống dòng, `json.loads` ở dòng 153 thất bại vì thiếu `strict=False`.
2. **Từ Observation 1.1 (Dòng 36)**: Khi rơi vào `unwrap_story_prose`, việc chỉ đọc `parsed.get("updated_story_content")` khiến các cấu trúc lồng nhau như `{ "action": "edit_story_direct", "action_params": { "updated_story_content": "..." } }` không được bóc tách và thoát ra ngoài dưới dạng chuỗi JSON nguyên vẹn.
3. **Từ Observation 1.1 (Dòng 47) & Observation 1.3 (Dòng 361)**: Cả hai đầu backend và frontend đều đặt điều kiện loại trừ (`"\n" not in text` và `!trimmed.includes("\n\n")`), dẫn đến việc ký tự literal `\n` không bao giờ được unescape nếu văn bản có chứa ngắt dòng tự nhiên.
4. **Từ Observation 1.2**: Chuỗi raw JSON chưa được unwrap được backend commit thẳng vào DB SQLite. Khi frontend tải lại hoặc Copilot thực hiện lượt chat tiếp theo, bản thảo bị ô nhiễm này được nạp vào context, ép LLM tiếp tục sinh ra JSON lồng thêm một lớp nữa.
5. **Từ Observation 1.3 & 1.4**: Frontend chỉ unwrap 1 lần và chỉ tìm key phẳng `parsed.updated_story_content`. Khi chuỗi JSON lồng nhiều tầng hoặc có cấu trúc `action_params`, frontend bỏ cuộc và gán chuỗi JSON thô vào `storyContent`, khiến `StoryEditor.tsx` render thẳng raw JSON lên DOM.
6. **Kết luận logic**: Lỗi hiển thị raw JSON và ký tự thoát dòng là hệ quả cộng hưởng từ việc thiếu thuật toán giải mã đệ quy đa tầng, điều kiện unescape newline bị viết ngược/sai logic, và thiếu cơ chế phòng thủ độc lập ở từng tầng (Backend Sanitizer, DB Guard, Frontend Cleaner, Editor Component Guard).

---

## 3. Caveats

- Cuộc khảo sát tập trung chuyên biệt vào luồng Copilot Direct Edit (Requirement R1). Các agent khác như `comic_agent.py` và `cloudflare_ai.py` (thuộc R2 và R3) không thuộc phạm vi điều tra của explorer này và được thực hiện bởi các subagent song song khác.
- Mô hình LLM chạy qua Groq API nên định dạng đầu ra của LLM có tính ngẫu nhiên (đôi khi có markdown fence ````json, đôi khi là plain JSON, đôi khi là plain prose). Giải pháp thiết kế phải có tính thích ứng 100% với mọi biến thể đầu ra của LLM.
- Quyền thực thi lệnh terminal (`run_command`) bị giới hạn/timeout trong môi trường khảo sát này (đúng với vai trò Explorer read-only), toàn bộ kết luận đều dựa trên phân tích mã nguồn tĩnh và đối chiếu luồng thực thi dữ liệu thực tế.

---

## 4. Conclusion & Actionable Solution

Để triệt tiêu hoàn toàn lỗi raw JSON và ký tự `\n\n`, Implementer Agent cần áp dụng giải pháp **Phòng thủ 6 tầng (Defense-in-Depth)** đã được đặc tả chi tiết trong `analysis.md`:

1. **Layer 1 - Backend `unwrap_story_prose` (`backend/agents/copilot_agent.py`)**:
   - Chuyển thành vòng lặp tối đa 10 lượt giải mã.
   - Bóc sạch mọi markdown codeblocks (kể cả có lời dẫn trước/sau).
   - Dùng `json.loads(text, strict=False)`.
   - Tìm kiếm linh hoạt các keys: `updated_story_content`, `action_params.updated_story_content`, `story_content`, `story`, `content`, `new_story_content`, `revised_text`, `text`.
   - Regex fallback bắt trọn chuỗi không ngắt cụt đối thoại tiếng Việt.
   - Unescape `\\n` -> `\n`, `\\r\\n` -> `\n`, `\\"` -> `"` vô điều kiện (xóa bỏ triệt để điều kiện `and "\n" not in text`).
2. **Layer 2 - Backend `_perform_direct_manuscript_edit` (`backend/agents/copilot_agent.py`)**:
   - Dùng `strict=False` khi parse JSON.
   - Nếu `json.loads` lỗi, thử trích xuất bằng regex hoặc dùng văn bản mới nếu `len(cleaned) > 50` thay vì trả về `None`.
   - Bổ sung các từ khóa trong `_is_direct_edit_request`: `sửa`, `chỉnh`, `thay`, `đổi`, `viết lại`, v.v.
3. **Layer 3 - Backend `main.py`**:
   - Luôn unwrap dữ liệu và chặn tuyệt đối việc lưu chuỗi bắt đầu bằng `{` vào SQLite DB.
4. **Layer 4 - Frontend `page.tsx`**:
   - Xây dựng hàm `unwrapStoryProseFrontend` giải mã đa vòng.
   - Bỏ điều kiện `!trimmed.includes("\n\n")`, thực hiện unescape `\\n` và `\\"` toàn diện.
   - Áp dụng cho cả nhánh Copilot direct edit, fallback chat, và nạp lịch sử.
5. **Layer 5 - Frontend `StoryEditor.tsx`**:
   - Bổ sung chốt chặn an toàn (Safety Net Guard) tại `useEffect`: Tự động unwrap trước khi gán vào `innerText` nếu phát hiện dấu hiệu chuỗi JSON.

---

## 5. Verification Method

Người tiếp nhận hoặc QA có thể xác minh độc lập theo các bước:

1. **Kiểm tra biên dịch Backend & Frontend**:
   ```powershell
   python -m py_compile backend/agents/copilot_agent.py backend/main.py
   cd frontend; npm run build
   ```
2. **Kiểm tra Benchmark Hệ thống**:
   ```powershell
   python backend/tests/run_full_system_benchmark.py
   ```
   Kiểm tra `benchmark_results.json`: Mục `AI Co-pilot Direct Manuscript Intervention` phải đạt `passed: true`, và `details` phải hiển thị `Action: edit_story_direct`.
3. **Kiểm tra chức năng giao diện người dùng**:
   - Khởi chạy backend và frontend (`localhost:3000`).
   - Tạo một câu chuyện mẫu (ví dụ đoạn văn ngắn).
   - Tại khung AI Co-pilot, gõ lệnh: *"tôi muốn một mở đầu khác"* hoặc click nút Quick Prompt *"Tạo phần mở đầu khác đi"*.
   - **Tiêu chí chấp thuận**:
     - Vùng soạn thảo Editor cập nhật văn xuôi mới ngay lập tức.
     - 0% xuất hiện dấu ngoặc `{` hoặc `}` hoặc chuỗi `"updated_story_content"`.
     - 0% xuất hiện chuỗi ký tự `\n\n`. Các đoạn văn bản hiển thị ngắt dòng Markdown chuẩn xác và mượt mà.
