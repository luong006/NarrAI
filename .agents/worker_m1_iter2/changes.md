# Changes Log — Milestone 1 Iteration 2

## Summary of Fixes Applied

### 1. `backend/agents/copilot_agent.py`
- **Operator Precedence Fix in `_perform_direct_manuscript_edit`**:
  - Replaced ambiguous ternary expression `content_candidate = data.get(...) or ... if ... else ...` with explicit, safe conditional branches:
    ```python
    content_candidate = data.get("updated_story_content")
    if not content_candidate and isinstance(data.get("action_params"), dict):
        content_candidate = data["action_params"].get("updated_story_content")
    if not content_candidate:
        content_candidate = data.get("story_content") or data.get("content")
    ```
  - Preserved custom `summary_of_changes` and `message` from LLM response.
  - Allowed short manuscript edits (<= 50 characters, e.g. short dialogue or poetry updates) in both primary and fallback code paths instead of dropping them.

- **Safe Code Fence Unwrapping in `unwrap_story_prose`**:
  - Replaced indiscriminate `fence_inner.startswith('{')` check with a targeted check:
    ```python
    if any(f'"{k}"' in fence_inner for k in candidate_keys) or '"action_params"' in fence_inner:
        current = fence_inner
    ```
  - Prevents author manuscripts containing embedded code blocks (e.g., JSON code snippets in sci-fi/programming novels) from having surrounding narrative erased.

- **Bounded Regex Fallback Truncation Recovery**:
  - Added `|"?\s*$` to terminal delimiters in regex fallback.
  - Rescues stream-truncated JSON lacking closing quotes or braces without prematurely failing or returning raw envelopes.

- **Conversational Idiom Filtering in `_is_direct_edit_request`**:
  - Added `non_edit_idioms = ["thay vì", "đổi lại", "thay cho", "bớt giận", "xóa tan"]` to exclude colloquial questions and expressions from triggering direct manuscript overwrite.

- **Master Controller Root-Level Schema Normalization in `process_event`**:
  - When `action == "edit_story_direct"`, normalized root-level `updated_story_content` into `res["action_params"]` and unwrapped with `unwrap_story_prose`.

---

### 2. `backend/main.py`
- **Database Quarantine Guard**:
  - Normalized root-level `updated_story_content` if present in direct edit event.
  - If unwrapped prose fails quarantine (starts with `{` or contains `"updated_story_content"`), neutralized `updated_content = None` and `params["updated_story_content"] = None`.
  - Set descriptive user notification: `"Hệ thống phát hiện lỗi định dạng bản thảo và đã ngăn chặn ghi đè để bảo vệ tác phẩm của bạn."`.
  - Prevented corrupted raw JSON strings from being persisted to SQLite `story.story_content`.

---

### 3. `frontend/src/app/page.tsx`
- **Safe Code Fence Unwrapping in `unwrapStoryProseFrontend`**:
  - Only peels code fences if candidate keys or `"action_params"` are present.
- **Bounded Regex Truncation Rescue**:
  - Added `|"?\\s*$` to both primary and candidate key regex fallbacks.
- **Frontend Direct Edit Defense-in-Depth**:
  - Checked `params.updated_story_content || (res.data as any).updated_story_content`.
  - Verified prose does not start with `{` or contain `"updated_story_content"` before committing to `setStoryContent`.

---

### 4. `backend/tests/test_copilot_unwrap.py`
- Extended test suite from 8 to 15 unit tests:
  - `test_conversational_idioms_excluded`: Verifies non-edit idioms return False while real edit requests return True.
  - `test_operator_precedence_in_direct_edit`: Verifies primary parsing path preserves custom summary and message.
  - `test_direct_edit_short_prose`: Verifies short prose revisions (<= 50 characters) are not discarded.
  - `test_master_controller_root_normalization`: Verifies root-level keys are normalized to `action_params`.
  - `test_safe_code_fence_unwrapping`: Verifies embedded code fence does not erase surrounding story text.
  - `test_truncated_stream_regex_recovery`: Verifies unclosed truncated stream is cleanly rescued.
  - `test_database_quarantine_guard_neutralization`: Verifies corrupt JSON is blocked and neutralized.
