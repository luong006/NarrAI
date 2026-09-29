# Handoff Report: Backend Copilot & Manuscript Surgery Survey

**Author**: Explorer Subagent (`explorer_r5_survey_1`)  
**Recipient**: Orchestrator / Implementer Worker  
**Date**: 2026-09-29  
**Type**: Hard Handoff (Investigation & Architecture Survey Complete)  

---

## 1. Observation

1. **`backend/agents/copilot_agent.py` Lines 360-370 & 432-440**:
   Direct manuscript editing only checks three rudimentary boolean flags:
   ```python
   is_opening = any(k in inst_lower for k in [
       "mở đầu", "đoạn mở", "mở bài", "opening", "intro", "beginning", "khởi đầu"
   ])
   is_ending = any(k in inst_lower for k in [
       "kết thúc", "đoạn kết", "kết bài", "ending", "outro", "conclusion", "cliffhanger", "cái kết"
   ])
   is_middle = any(k in inst_lower for k in [
       "ở giữa", "đoạn giữa", "thân bài", "thêm cảnh", "chèn cảnh", "thêm đoạn", "chèn đoạn", "giữa truyện", "middle"
   ])
   ```
   If an instruction targets **Target 2 (Character & Dialogue Surgery)** or **Target 5 (Tone Shift & Style Restyling)**, it evaluates as `False` for all three flags and falls into:
   ```python
   else:
       if len(story) <= self.MAX_MANUSCRIPT_CHARS:
           return "", story, ""
       cut_idx = self.MAX_MANUSCRIPT_CHARS
       last_para = story[:cut_idx].rfind("\n\n")
       if last_para > 3000:
           cut_idx = last_para
       return "", story[:cut_idx], story[cut_idx:]
   ```
   This cuts the text at 8,000 characters and dumps the remainder into `suffix`, completely ignoring the second half of the story for character renames and tone restyling.

2. **`backend/agents/copilot_agent.py` Lines 504-523**:
   Heading preservation logic is exclusively wrapped inside `if is_opening_edit:`:
   ```python
   if is_opening_edit:
       # Safeguard 1: Preserve original title (e.g. **TIÊU ĐỀ**) if present in window_text but omitted in clean_story
       title_match = re.match(r'^(\*\*[^\*\n]+\*\*\s*\n+)', window_text.strip())
       if title_match and not clean_story.strip().startswith("**"):
           clean_story = title_match.group(1).strip() + "\n\n" + clean_story.strip()
       ...
   ```
   No heading preservation logic exists for any other edits (Targets 2, 3, 4, 5). Furthermore, chapter headings `## Chương X` are not protected even in opening edits.

3. **`backend/agents/copilot_agent.py` Lines 170-206**:
   A single generic prompt (`DIRECT_EDIT_PROMPT`) is used for all manuscript modifications, combining opening, character, middle beats, ending, and tone rules into a monolithic 30-line instruction block, rather than using specialized prompts tailored to each of the 5 targets.

4. **`backend/main.py` Lines 478-498 and 1188-1215**:
   Story persistence to SQLite happens only **after** the streaming generator finishes reading all LLM chunks. Furthermore, if `current_user is None` (guest user), no `Story` record is created, and no `[STORY_ID:...]` marker is ever yielded.

5. **`backend/db/models.py` Line 33**:
   `user_id = Column(Integer, ForeignKey("users.id"))` is nullable by default in SQLAlchemy. SQLite and the NarrAI schema already permit stories with `user_id = None`.

6. **`frontend/src/lib/api.ts` Lines 193-219**:
   The frontend `streamStory` method already contains parsing logic for `[STORY_ID:(\d+)]` and cleans it from the accumulated story text:
   ```typescript
   const storyMatch = fullAccumulated.match(/\[STORY_ID:(\d+)\]/);
   ```

---

## 2. Logic Chain

1. **Step 1 (From Observation 1)**: Because `copilot_agent.py` lacks intent classification for Target 2 (Character/Dialogue) and Target 5 (Tone Shift), any long manuscript (>8,000 characters) gets truncated. Characters in the second half retain their old names, and the style remains un-restyled.
2. **Step 2 (From Observation 2)**: Because heading preservation is locked behind `if is_opening_edit:`, any tone rewrite (Target 5), scene insertion (Target 3), or character dialogue update (Target 2) risks losing `**[TITLE]**` and `## Chương X` chapter headers if the LLM omits markdown headings.
3. **Step 3 (From Observation 3)**: A monolithic prompt weakens model adherence. Having 5 dedicated prompts (`TARGET_1_OPENING`, `TARGET_2_CHARACTER_DIALOGUE`, `TARGET_3_MIDDLE_BEATS`, `TARGET_4_CLIMAX_ENDING`, `TARGET_5_TONE_STYLE`) with explicit Light Novel rules and constraints guarantees distinct, high-quality execution for each surgical goal.
4. **Step 4 (From Observations 4, 5, 6)**: The Follow-up specification requires instant `story_id` allocation upon entering the Story Editor so users can immediately convert to Manga or save drafts. Since `db/models.py` allows `user_id` to be null, the backend can create the `Story` database row at the inception of the stream (or via a dedicated `POST /api/stories/allocate` endpoint) and yield `[STORY_ID:{id}]` early, solving the guest and race condition problem cleanly without altering the frontend parser.

---

## 3. Caveats

1. **Groq Model Context Windows**: Groq models (`gpt-oss-120b`, `qwen3.8-27b`) handle up to 4,000-8,000 output tokens comfortably. For stories exceeding 12,000 characters undergoing Target 5 (Tone Restyle), a rolling chapter-by-chapter chunking approach is superior to single-pass generation to prevent context overflow or timeouts.
2. **Backward Compatibility**: `test_copilot_bilingual_resilience.py` and `test_copilot_unwrap.py` assert specific behaviors for `_is_direct_edit_request` and `unwrap_story_prose`. Any refactoring of `CopilotAgent` must preserve all existing public and private helper interfaces tested by these test suites.
3. **No Code Modification Permitted in this Turn**: In accordance with the Explorer archetype instructions, no source code in `backend/` was altered during this survey.

---

## 4. Conclusion

The NarrAI backend has a robust foundation (`unwrap_story_prose`, multi-tier LLM fallback, session caching, SQLite schema), but requires the following concrete additions to fulfill Requirement #1:

1. **Implement `backend/services/manuscript_surgery.py`**:
   - `SurgeryTarget` enum (5 targets + general fallback).
   - `classify_surgery_intent(instruction: str) -> SurgeryTarget`.
   - `SemanticChunkSlicer`: Chapter-aware dynamic slicing into `prefix` -> `window_to_edit` -> `suffix`.
   - `HeadingPreservationEngine`: Zero-loss guarantee for `**[TITLE]**` and `## Chương X`.
   - 5 dedicated prompt templates (`SURGERY_PROMPTS`).
2. **Wire Surgery Engine into `backend/agents/copilot_agent.py`**:
   - Route `_perform_direct_manuscript_edit` through the intent classifier and targeted prompt dispatcher.
   - Enforce heading preservation across all 5 targets before returning.
3. **Upgrade Story ID Allocation in `backend/main.py`**:
   - Pre-create `Story` record at stream start in `/api/generate-story` and `/api/init-story` (including guest users).
   - Add `POST /api/stories/allocate` for instant story draft binding.
4. **Detailed Reference**: Full code templates, regex patterns, schemas, and prompts are documented in:
   `e:\NarrAI\.agents\teamwork\explorer_r5_survey_1\survey_report.md`.

---

## 5. Verification Method

1. **Unit Test Verification**:
   - Run existing copilot tests:
     ```bash
     python -m unittest tests/test_copilot_bilingual_resilience.py
     python -m unittest tests/test_copilot_unwrap.py
     ```
   - Add and run a new test suite `tests/test_copilot_manuscript_surgery_5targets.py` to verify:
     * Classification of all 5 target prompt types in both Vietnamese and English.
     * Slicing into `prefix + window + suffix` matching original text.
     * 100% preservation of `**[TITLE]**` and `## Chương X` even if stripped by mock LLM.
     * Immediate `story_id` allocation in `/api/generate-story` and `/api/stories/allocate`.
2. **Files to Inspect**:
   - `e:\NarrAI\.agents\teamwork\explorer_r5_survey_1\survey_report.md`
   - `e:\NarrAI\backend\agents\copilot_agent.py`
   - `e:\NarrAI\backend\main.py`
3. **Invalidation Conditions**:
   - If an opening rewrite deletes the `**[TITLE]**` or `## Chương 1` header.
   - If a tone shift drops chapter headings or leaves the second half of a story un-restyled.
   - If `/api/generate-story` fails to yield `[STORY_ID:...]` for guest sessions.
