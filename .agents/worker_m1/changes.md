# Changes Report: Milestone 1 (R1: Triệt Tiêu Lỗi Hiển Thị Raw JSON Trong Editor)

## Overview
Implementer: `worker_m1`  
Scope: Milestone 1 (Requirement R1)  
Objective: Completely eliminate raw JSON leaking and escaped newline characters (`\n\n`) into the Editor when Copilot intervenes or revises the manuscript, ensuring a 6-layer defense-in-depth across backend and frontend.

---

## Files Modified & Summary of Changes

### 1. `backend/agents/copilot_agent.py`
- **Overhauled `unwrap_story_prose(text: str) -> str`**:
  - Implemented multi-pass iterative peeling loop (up to 10 iterations) to peel arbitrarily nested stringified JSON envelopes and markdown fences.
  - Added stripping of markdown code fences (` ```json `, ` ```markdown `, ` ``` `) even when surrounded by prose or whitespace.
  - Implemented candidate key scanning: checks root dictionary for `updated_story_content`, `story_content`, `story`, `content`, `new_story_content`, `revised_text`, `text`.
  - Added inspection into nested `action_params` sub-dictionary for the same candidate keys.
  - Implemented robust regex fallback for dialogue containing unescaped quotes (e.g., `"updated_story_content": "Cô ấy nói: "Đi thôi!" và rời đi."`), bounding the match to next field (`,\s*"(?:summary_of_changes|message|action|instruction)"\s*:`) or ending brace, preventing premature dialogue truncation.
  - **Removed the broken `and "\n" not in text` condition**: now unconditionally unescapes `\\r\\n` -> `\n`, `\\n` -> `\n`, `\\"` -> `"`, and `\\\\` -> `\\`.
  - Normalizes line breaks (`\r\n` -> `\n`) and limits excessive consecutive newlines to maximum 2 (`\n\n`).
- **Enhanced `_is_direct_edit_request(user_msg: str) -> bool`**:
  - Expanded phrase keywords with: `"soạn lại"`, `"viết tiếp"`, `"bản thảo"`.
  - Added token/word-boundary matching for single-word Vietnamese editing verbs: `"sửa"`, `"chỉnh"`, `"thay"`, `"đổi"`, `"bớt"`, `"xóa"`.
- **Hardened `_perform_direct_manuscript_edit`**:
  - Used `json.loads(..., strict=False)` to tolerate unescaped control characters in manuscript text.
  - Added multi-tier fallback: if `json.loads` fails, attempts `unwrap_story_prose` directly on the matched JSON string or response. If unwrapped prose has length > 50 characters, successfully returns `edit_story_direct` instead of dropping to `None`.
- **Secured `process_event` Master Controller JSON parsing**:
  - Added `strict=False` to JSON decoding of Master Controller LLM responses.

### 2. `backend/main.py`
- **In `copilot_event` under `if result.get("action") == "edit_story_direct":`**:
  - Added **Database Quarantine Guard**: strictly checks if `updated_content` still starts with `{` or contains raw JSON markers (`"updated_story_content"`, `"action":`).
  - If detected, executes a secondary unwrap pass; if still raw JSON, blocks writing to `story.story_content` and SQLite database to prevent permanent manuscript database contamination.

### 3. `frontend/src/app/page.tsx`
- **Implemented `unwrapStoryProseFrontend(content: string): string`**:
  - Up to 10 passes of recursive peeling for JSON strings and markdown code fences.
  - Parses `JSON.parse` with comprehensive key extraction: root keys, `action_params` sub-dictionary, single long string keys.
  - Robust regex fallback for dialogue quotes.
  - Unconditionally unescapes `\\r\\n` -> `\n`, `\\n` -> `\n`, `\\"` -> `"`, `\\\\` -> `\\` (eliminated the restrictive `!trimmed.includes("\n\n")`).
- **Integrated `unwrapStoryProseFrontend` across state update paths**:
  - `handleSendCopilotMessage`: unwraps `params.updated_story_content` before `setStoryContent`.
  - `handleSendCopilotMessage` fallback: unwraps `chatRes.new_story_content`.
  - `handleContinueChapterWithInstruction`: unwraps `res.new_story_content`.
  - `handleEndStory`: unwraps `res.new_story_content`.
  - `handleSelectStory`: unwraps `story.story_content` when loading saved stories from history.

### 4. `frontend/src/components/editor/StoryEditor.tsx`
- **Added `sanitizeProseSafetyNet(text: string): string`**:
  - Built-in multi-pass sanitizer function.
- **Added DOM Safety Net in `useEffect`**:
  - If `content` passed to the component starts with `{`, contains `"updated_story_content"`, or contains `\\n`, runs `sanitizeProseSafetyNet` before setting `editorRef.current.innerText`.

### 5. `backend/tests/test_copilot_unwrap.py` (New Verification Test Suite)
- Added 8 automated test cases:
  1. `test_single_level_json`: unwraps `action_params.updated_story_content`.
  2. `test_root_level_key`: unwraps root `updated_story_content`.
  3. `test_nested_json`: unwraps double-stringified JSON.
  4. `test_escaped_newlines_unconditional`: verifies `\\n` is converted to `\n` even when string already has real `\n`.
  5. `test_dialogue_with_quotes_regex_fallback`: verifies dialogue quotes inside non-standard JSON are preserved without truncation.
  6. `test_markdown_codeblock`: verifies code fences are cleanly removed.
  7. `test_plain_markdown_prose_undamaged`: verifies pure markdown prose remains undamaged.
  8. `test_is_direct_edit_request_keywords`: verifies single-word verbs and edit phrases.
