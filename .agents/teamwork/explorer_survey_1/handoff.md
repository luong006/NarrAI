# Handoff Report: R1 & R5 Codebase Investigation
**From:** explorer_survey_1 (teamwork_preview_explorer)  
**To:** orchestrator_r6_1 (conv ID: `92e67f82-c02c-4fa1-9967-5963454f8d77`)  
**Timestamp:** 2026-09-30T16:42:00Z  
**Type:** Hard Handoff (Investigation Complete)

---

## 1. Observation

### R1 Observations (Copilot Manuscript Surgery):
1. **Unused `instruction` in `SemanticChunkSlicer`:**
   - File: `backend/agents/copilot_agent.py`, lines 347–421.
   - Line 347 defines `def slice_manuscript(cls, story: str, target: Any, instruction: str = "") -> ChunkSlice:`.
   - In lines 348 to 421, the parameter `instruction` is never referenced or parsed anywhere in the body of `slice_manuscript`. Slicing is performed purely based on `target == SurgeryTarget.TARGET_1_OPENING`, `TARGET_4_CLIMAX_ENDING`, `TARGET_3_MIDDLE_BEATS`, or whole story fallback.
2. **Missing Chapter Targeting:**
   - There is no regex or logic detecting requests like "sửa Chương 3" in either `classify_surgery_intent` (lines 203–262) or `SemanticChunkSlicer.slice_manuscript` (lines 343–421).
3. **Path B Truncation & Overwrite:**
   - File: `backend/agents/copilot_agent.py`, lines 880 & 906–914.
   - Line 880: `short_context = memory.get_short_context(max_chars=3000) if memory else (current_story[-2000:] if current_story else "Chưa có truyện.")`.
   - Line 913: `params["updated_story_content"] = unwrap_story_prose(params["updated_story_content"])`.
   - When the LLM decides `res.get("action") == "edit_story_direct"` in Path B, `updated_story_content` is returned based solely on the 2000-character tail, and returned directly to the caller.
   - In `frontend/src/app/page.tsx:487`, `setStoryContent(newContent)` replaces the entire editor text with this snippet, obliterating `current_story[:-2000]`.
4. **HeadingPreservationEngine Heading Bunching:**
   - File: `backend/agents/copilot_agent.py`, lines 312–339.
   - Lines 331–338:
     ```python
     if not has_heading:
         if cleaned.startswith("**"):
             parts = cleaned.split("\n\n", 1)
             if len(parts) == 2:
                 cleaned = f"{parts[0]}\n\n{ch_h_clean}\n\n{parts[1]}"
             else:
                 cleaned = f"{cleaned}\n\n{ch_h_clean}"
         else:
             cleaned = f"{ch_h_clean}\n\n{cleaned}"
     ```
   - For every missing chapter heading in `window_text`, the heading is prepended to the top of `cleaned`. For multi-chapter windows where multiple headings are omitted by the LLM, headings are prepended in sequence, resulting in intermediate chapters (e.g. Chapter 3, Chapter 2) bunching at the very top in reverse order.
5. **Frontend Omission of `selectedText` and Caret Offset:**
   - File: `frontend/src/components/editor/StoryEditor.tsx`, lines 136–158: `handleMouseUp` extracts `text` via `window.getSelection()?.toString()`, but does not calculate or emit caret/selection character offsets.
   - File: `frontend/src/app/page.tsx`, lines 466–475: `handleSendCopilotMessage` serializes only `user_message` and `current_story`, omitting `selectedText` and `cursorPosition`.

### R5 Observations (Database & Performance):
1. **Missing SQLite WAL Configuration:**
   - File: `backend/db/models.py`, lines 261–264:
     ```python
     engine = create_engine('sqlite:///narrai.db', connect_args={'check_same_thread': False})
     Base.metadata.create_all(engine)
     SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
     ```
   - No `PRAGMA journal_mode=WAL;` or `PRAGMA synchronous=NORMAL;` is executed on the engine connection or via SQLAlchemy event listeners.
2. **Missing Indexes in `backend/db/models.py`:**
   - Line 50: `Comic.user_id = Column(Integer, ForeignKey('users.id'))` (no `index=True`).
   - Line 51: `Comic.story_id = Column(Integer, ForeignKey('stories.id'), nullable=True)` (no `index=True`).
   - Line 62: `ComicPanel.comic_id = Column(Integer, ForeignKey('comics.id'))` (no `index=True`).
   - Line 142: `SocialPost.story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)` (no `index=True`).
3. **Hot Query Paths Lacking Composite Indexes:**
   - `main.py:903`: `db.query(ComicPanel).filter(ComicPanel.comic_id == comic.id).order_by(ComicPanel.panel_index).all()`.
   - `recommender_service.py:444` & `social_router.py:121`: `query.filter(SocialPost.genre.ilike(...)).order_by(SocialPost.created_at.desc())`.
   - `recommender_service.py:1116`: `db.query(PostInteraction).filter(PostInteraction.post_id == post_id, PostInteraction.interaction_type == "COMMENT").order_by(desc(PostInteraction.created_at)).all()`.
4. **Missing GZipMiddleware in `backend/main.py`:**
   - Lines 44–50 mount `CORSMiddleware`. `GZipMiddleware` is neither imported nor mounted.

---

## 2. Logic Chain

1. **R1 Frontend Selection Propagation:**
   - *From Observation 5:* Because `StoryEditor.tsx` does not compute caret character offset, and `page.tsx` does not include `selectedText` / `cursorPosition` in the Copilot event payload, the backend agent has no visibility into what text the user selected or where the cursor is positioned.
   - *Inference:* Adding `getCaretOffset` using DOM `Range.selectNodeContents` in `StoryEditor.tsx` and passing `{ selected_text, cursor_position }` into the `USER_CHAT` JSON payload enables targeted surgery without altering the existing REST endpoint signature.

2. **R1 Semantic Chunk Slicing & Chapter Targeting:**
   - *From Observation 1 & 2:* Since `instruction` is ignored in `SemanticChunkSlicer.slice_manuscript`, user commands like "sửa Chương 3" fall back to generic full-story or middle-story heuristics.
   - *Inference:* Parsing `r'chương\s*(\d+)'` from `instruction` and locating the corresponding `## Chương X` header allows `slice_manuscript` to return a `ChunkSlice` where `window_to_edit` contains exactly the targeted chapter, while `prefix` and `suffix` protect preceding and subsequent chapters.

3. **R1 Path B Overwrite Fix:**
   - *From Observation 3:* Path B only passes `current_story[-2000:]` to the LLM. If the LLM generates an `edit_story_direct` action, returning that raw snippet causes the frontend to replace the entire 10,000+ character manuscript with 2,000 characters.
   - *Inference:* In Path B, when `res.get("action") == "edit_story_direct"`, re-routing to Path A (`_perform_direct_manuscript_edit`) or merging `clean_prose` with `current_story[:-2000]` guarantees that preceding manuscript content is never lost.

4. **R1 Heading Preservation Fix:**
   - *From Observation 4:* Prepending missing chapter headings to the top of `cleaned` creates an inverted bunch of headers at offset 0 whenever multiple chapters are in the editing window and the LLM strips headings.
   - *Inference:* Tracking each heading's relative character offset $r_i \in [0, 1]$ in `window_text` and inserting missing intermediate headings ($r_i \ge 0.1$) at the proportional paragraph index ($k = \text{round}(r_i \times \text{len}(paragraphs))$) guarantees that headings remain positioned between their respective chapters.

5. **R5 Performance Optimization:**
   - *From Observations 1, 2, 3, 4:* Foreign key lookups on unindexed columns cause $O(N)$ full table scans in SQLite. Connecting without WAL causes file-locking contention during concurrent transactions. Uncompressed responses inflate network payload sizes.
   - *Inference:* Applying `@event.listens_for(engine, "connect")` with `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`, adding column indexes and composite `Index(...)` definitions with `CREATE INDEX IF NOT EXISTS` auto-migrations, and mounting `GZipMiddleware(minimum_size=500)` resolves all three performance gaps.

---

## 3. Caveats

1. **SQLite In-Memory Limitation:** `PRAGMA journal_mode=WAL` is ignored by SQLite for in-memory databases (`:memory:`), returning `memory`. Automated tests validating WAL mode must test against a file-backed database (such as `narrai.db` or a temporary `.db` file).
2. **ContentEditable DOM Boundary Edge Cases:** While `Range.cloneRange()` accurately measures text length across text nodes, rich text nested inside custom DOM nodes could introduce small index drifts if HTML entities or line breaks vary between browser DOM and raw markdown string. Normalizing string content preserves exact alignment.
3. **Investigation Boundary:** This investigation strictly focused on R1 and R5 as directed. R2 (Historical Gatekeeper), R3 (TensorFlow.js), and R4 (Social Expansion schema) are separate tracks.

---

## 4. Conclusion

The technical path forward for R1 and R5 is clear, well-isolated, and actionable:
1. **R1 Frontend:** Update `StoryEditor.tsx` to calculate caret character offsets and pass `selectedText` + `cursorPosition` via `page.tsx` payload.
2. **R1 Slicer:** Update `SemanticChunkSlicer.slice_manuscript` to parse chapter targeting ("sửa Chương 3") from `instruction` and support exact `selected_text` slicing.
3. **R1 Path B Fallback:** Update `copilot_agent.py` to route Path B `edit_story_direct` actions through Path A or safely merge with `current_story[:-2000]`.
4. **R1 Heading Preservation:** Update `HeadingPreservationEngine.preserve_headings` to position missing intermediate headings by relative paragraph offset rather than prepending to the top.
5. **R5 DB & Server:** Add `@event.listens_for(engine, "connect")` for WAL pragmas, add missing single and composite indexes in `models.py` with auto-migration DDL, and mount `GZipMiddleware(minimum_size=500)` in `main.py`.

Full technical details and design snippets are documented in:
`e:\NarrAI\.agents\teamwork\explorer_survey_1\survey_report.md`.

---

## 5. Verification Method

1. **Codebase Inspection:**
   - Verify `backend/agents/copilot_agent.py` at `SemanticChunkSlicer`, `HeadingPreservationEngine`, and lines 873–914.
   - Verify `backend/db/models.py` at lines 47–69, 140–161, and 261–293.
   - Verify `backend/main.py` at lines 44–51 and 1066–1130.
   - Verify `frontend/src/components/editor/StoryEditor.tsx` at lines 136–158 and `frontend/src/app/page.tsx` at lines 460–476.
2. **Compilation Checks:**
   - `python -m py_compile backend/agents/copilot_agent.py backend/db/models.py backend/main.py`
   - `npm run build` in `frontend/`
3. **Regression & New Unit Tests:**
   - Run `python backend/tests/run_all_tests.py` (ensure 182 existing tests pass 100%).
   - Unit test `SemanticChunkSlicer.slice_manuscript` with "sửa Chương 2" on multi-chapter text.
   - Unit test `HeadingPreservationEngine.preserve_headings` with multi-chapter text when LLM strips intermediate headings -> verify headings maintain ascending order and do not bunch at top.
   - Unit test SQLite WAL mode verification: `PRAGMA journal_mode;` returns `wal`.
