## 2026-09-19T13:41:20Z

You are a Worker subagent for the NarrAI project.
Working directory: e:\NarrAI\.agents\worker_m1
Identity: worker_m1
Parent conversation ID: 6bf39d70-f735-4c2a-8a7a-0d9642a300c3

Read e:\NarrAI\.agents\ORIGINAL_REQUEST.md carefully before doing anything else.
Also read e:\NarrAI\PROJECT.md and the survey report e:\NarrAI\.agents\explorer_survey_1\handoff.md and analysis.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Exclusive File Ownership for Milestone 1 (R1: Triệt Tiêu Lỗi Hiển Thị Raw JSON Trong Editor):
Files you own:
- backend/agents/copilot_agent.py
- backend/main.py (lines ~675-710 dealing with copilot edit_story_direct persistence and unwrap)
- frontend/src/app/page.tsx (handleSendCopilotMessage and unwrapStoryProseFrontend)
- frontend/src/components/editor/StoryEditor.tsx (editor DOM safety net unwrap)

Tasks to implement:
1. Backend `backend/agents/copilot_agent.py`:
   - Overhaul `unwrap_story_prose(text)`:
     - Use a multi-pass loop (up to 10 iterations) to peel nested JSON and codeblocks.
     - Strip markdown codeblocks (```json ... ``` or ```markdown ... ```).
     - Try `json.loads(text, strict=False)`.
     - Scan keys: `updated_story_content`, `action_params` (sub-dict `updated_story_content`), `story_content`, `story`, `content`, `new_story_content`, `revised_text`, `text`.
     - Robust regex fallback for `"updated_story_content": "..."` that handles dialogue with quotes and escaped characters without prematurely truncating.
     - Unconditionally unescape `\\n` -> `\n`, `\\r\\n` -> `\n`, `\\"` -> `"`, `\\\\` -> `\\` (REMOVE the broken `and "\n" not in text` condition!).
   - In `_perform_direct_manuscript_edit`:
     - Parse with `strict=False`.
     - Fallback if `len(cleaned) > 50` rather than returning `None`.
     - Expand `edit_keywords` in `_is_direct_edit_request` to include single-word verbs like "sửa", "chỉnh", "thay", "đổi", "viết lại", "soạn lại".
2. Backend `backend/main.py`:
   - In `copilot_event` under `if result.get("action") == "edit_story_direct":`, ensure `story.story_content` is strictly unwrapped clean prose, and if the string starts with `{` or contains raw JSON markers after unwrapping, do not save raw JSON to DB.
3. Frontend `frontend/src/app/page.tsx`:
   - Implement recursive/multi-pass `unwrapStoryProseFrontend(content: string): string` handling nested JSON, `action_params`, unescaping `\\n` unconditionally (remove `!trimmed.includes("\n\n")`), stripping markdown fences.
   - Use this helper in `handleSendCopilotMessage` for `edit_story_direct` action and whenever updating `storyContent`.
4. Frontend `frontend/src/components/editor/StoryEditor.tsx`:
   - Add safety net unwrap in `useEffect` so that if `content` ever starts with `{` or contains `"updated_story_content"`, it cleans it before setting `editorRef.current.innerText`.

Verification & Test Requirements:
- Run: `python -m py_compile backend/agents/copilot_agent.py backend/main.py`
- Run frontend build/lint: `cd frontend; npm run build`
- Run or create a python test to verify that `unwrap_story_prose` correctly unwraps single-level JSON, nested `action_params` JSON, escaped newlines `\n\n`, dialogue with internal quotes, and plain markdown prose without damage.
- Document all modified files and verified test results in:
  `e:\NarrAI\.agents\worker_m1\changes.md`
  `e:\NarrAI\.agents\worker_m1\handoff.md`
When complete, send a message to parent with your summary and test verification outputs.
