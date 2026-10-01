## 2026-09-30T16:43:32Z
You are worker_m1, a teamwork_preview_worker agent.
Your working directory is e:\NarrAI\.agents\teamwork\worker_m1.
Your parent orchestrator is orchestrator_r6_1 (conv ID: 92e67f82-c02c-4fa1-9967-5963454f8d77).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY INSTRUCTIONS:
1. Read the authoritative user request at e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md, especially section ## 2026-09-30T16:30:48Z.
2. Read the project specification at e:\NarrAI\.agents\teamwork\orchestrator_r6_1\PROJECT.md.
3. Read the technical survey at e:\NarrAI\.agents\teamwork\explorer_survey_1\survey_report.md.

ASSIGNED SCOPE: Milestone 1 (Features 1-8):
A. Copilot Manuscript Surgery:
   1. In `frontend/src/components/editor/StoryEditor.tsx`: Add DOM caret calculation on selection using Range API, extract `selectedText` and `cursorPosition` (character offset), and pass them to parent callback.
   2. In `frontend/src/app/page.tsx`: Include `selected_text` and `cursor_position` in the Copilot `USER_CHAT` payload.
   3. In `backend/agents/copilot_agent.py` (`SemanticChunkSlicer.slice_manuscript`): Use the `instruction` parameter. Detect chapter targeting commands (e.g. `r'chương\s*(\d+)'` or "sửa Chương 3"), locate the chapter heading `## Chương X`, and return a `ChunkSlice` where `window_to_edit` is that exact chapter, with `prefix` and `suffix` protecting earlier and later chapters. If `selected_text` is provided, slice that exact snippet.
   4. In `backend/agents/copilot_agent.py` (lines 880 & 906-914, Path B Master Controller fallback): Fix the 2000-character overwrite flaw. When `action == "edit_story_direct"`, safely re-route to Path A (`_perform_direct_manuscript_edit`) or safely merge `updated_story_content` with `current_story[:-2000]`. Never allow the entire manuscript to be overwritten by a 2000-char tail.
   5. In `backend/agents/copilot_agent.py` (`HeadingPreservationEngine.preserve_headings`): Fix intermediate chapter heading bunching. Instead of prepending missing chapter headings to line 1, position intermediate headings at their proportional paragraph/character offset so chapter titles remain in their correct sequential places.
B. Database & Performance:
   6. In `backend/db/models.py`: Add `@event.listens_for(engine, "connect")` executing `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`.
   7. In `backend/db/models.py`: Add `index=True` on `Comic.user_id`, `Comic.story_id`, `ComicPanel.comic_id`, `SocialPost.story_id`, and define composite indexes for hot query paths with `CREATE INDEX IF NOT EXISTS` auto-migrations.
   8. In `backend/main.py`: Import and mount `GZipMiddleware(minimum_size=500)`.

C. Verification:
   - Run `python -m py_compile backend/agents/copilot_agent.py backend/db/models.py backend/main.py`.
   - Run `python backend/tests/run_all_tests.py` and ensure all 182 existing tests pass 100%.
   - Verify SQLite WAL mode is active and verify chapter targeting.
   - Write your handoff report to `e:\NarrAI\.agents\teamwork\worker_m1\handoff.md` and send a message back to orchestrator_r6_1.
