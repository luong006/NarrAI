# Technical Survey & Codebase Investigation Report
**Agent:** explorer_survey_1 (teamwork_preview_explorer)  
**Date:** 2026-09-30  
**Parent Orchestrator:** orchestrator_r6_1 (conv ID: `92e67f82-c02c-4fa1-9967-5963454f8d77`)  
**Scope:** R1 (Copilot Manuscript Surgery) and R5 (Database & Performance)

---

## Executive Summary
This survey provides a comprehensive investigation of the NarrAI codebase covering two core engineering areas specified in the authoritative request:
1. **R1: Copilot Manuscript Surgery:** Root cause analysis and concrete implementation designs for:
   - Frontend selection (`selectedText`) and caret offset (`cursorPosition`) extraction and propagation to Copilot API.
   - Chapter targeting (e.g., "sửa Chương 3") in `SemanticChunkSlicer`.
   - Activating the currently unused `instruction` argument in `SemanticChunkSlicer.slice_manuscript`.
   - Eliminating the Path B 2000-character manuscript truncation/overwrite bug in `copilot_agent.py`.
   - Resolving intermediate chapter heading bunching at the top in `HeadingPreservationEngine`.
2. **R5: Database & Performance:**
   - Enabling SQLite WAL mode (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`) in SQLAlchemy connection pools and startup migrations.
   - Adding missing single-column indexes on `Comic.user_id`, `Comic.story_id`, `ComicPanel.comic_id`, `SocialPost.story_id`, plus high-impact composite indexes for hot query paths.
   - Integrating FastAPI `GZipMiddleware` with `minimum_size=500` in `backend/main.py`.

---

## 1. Architectural Map of Key Components

| Component | File Path | Line Range | Role |
|---|---|---|---|
| **Copilot Agent** | `backend/agents/copilot_agent.py` | 1–927 | Core agent handling direct manuscript edits and general chat |
| **Heading Preservation** | `backend/agents/copilot_agent.py` | 265–341 | Preserves markdown bold titles and chapter headers |
| **Semantic Chunk Slicer** | `backend/agents/copilot_agent.py` | 343–421 | Splits manuscript into `prefix`, `window_to_edit`, `suffix` |
| **Path A (Direct Edit)** | `backend/agents/copilot_agent.py` | 734–829 | Targeted surgery with chunk slicing & heading preservation |
| **Path B (Master Controller)** | `backend/agents/copilot_agent.py` | 873–926 | General event handler fallback with 2000-char context |
| **FastAPI Main App** | `backend/main.py` | 1–1501 | API routes, middleware, DB sessions, `/api/copilot-event` |
| **DB Models & Engine** | `backend/db/models.py` | 1–293 | SQLAlchemy models, SQLite engine init, auto-migrations |
| **Recommender Service** | `backend/services/recommender_service.py` | 1–1203 | 3-stage ranking, queries for posts & interactions |
| **Story Editor UI** | `frontend/src/components/editor/StoryEditor.tsx` | 1–281 | ContentEditable manuscript editor & selection toolbar |
| **AI Copilot Panel UI** | `frontend/src/components/editor/AICopilotPanel.tsx` | 1–310 | Copilot drawer, quick prompt buttons, chat input |
| **Workspace Page** | `frontend/src/app/page.tsx` | 1–966 | Workspace container, copilot event dispatch, state management |
| **API Client** | `frontend/src/lib/api.ts` | 1–457 | Typed client for backend REST & streaming endpoints |

---

## 2. Investigation of R1: Copilot Manuscript Surgery

### 2.1. Capturing `selectedText` and `cursorPosition` in Frontend and Transmitting to API

#### Current Frontend Implementation
1. **In `StoryEditor.tsx` (lines 136–158):**
   ```typescript
   const handleMouseUp = () => {
     const selection = window.getSelection();
     if (!selection || selection.isCollapsed) {
       setFloatingPos(null);
       setSelectedText("");
       return;
     }
     const text = selection.toString().trim();
     if (text.length > 3) {
       ...
       setSelectedText(text);
       onSelectText(text); // Only sends text string, no position!
     }
   };
   ```
2. **In `page.tsx` (lines 460–476):**
   ```typescript
   const handleSendCopilotMessage = async (msg: string) => {
     ...
     const storyContext = storyContent.slice(0, 15000);
     const res = await api.sendCopilotEvent(
       sessionId,
       storyId,
       "USER_CHAT",
       JSON.stringify({
         user_message: msg,
         current_story: storyContext,
         // selectedText and cursorPosition are completely omitted!
       })
     );
   ```
3. **In `api.ts` (lines 246–263):**
   `sendCopilotEvent` takes `eventData: string` and wraps it in a JSON body.

#### Solution & Implementation Design
1. **In `StoryEditor.tsx`:**
   Add a DOM caret calculation utility that calculates exact character offsets in `contentEditable`:
   ```typescript
   function getCaretOffset(element: HTMLElement): { start: number; end: number } {
     let start = 0;
     let end = 0;
     const sel = window.getSelection();
     if (sel && sel.rangeCount > 0) {
       const range = sel.getRangeAt(0);
       const preCaretRange = range.cloneRange();
       preCaretRange.selectNodeContents(element);
       preCaretRange.setEnd(range.startContainer, range.startOffset);
       start = preCaretRange.toString().length;
       end = start + range.toString().length;
     }
     return { start, end };
   }
   ```
   Update `handleMouseUp` (and `onKeyUp`/`onClick` on `editorRef.current`) to compute `{ start, end }`.
   Update `Props` and callback:
   ```typescript
   onSelectText: (text: string, cursorPosition?: number) => void;
   ```
   When text is selected: pass `text` and `start`. When cursor is placed without selection: pass `""` and `start`.

2. **In `page.tsx`:**
   Add state:
   ```typescript
   const [cursorPosition, setCursorPosition] = useState<number | null>(null);
   ```
   Update `onSelectText`:
   ```typescript
   onSelectText={(txt, pos) => {
     setSelectedText(txt);
     setCursorPosition(pos ?? null);
   }}
   ```
   In `handleSendCopilotMessage`:
   ```typescript
   const payload = {
     user_message: msg,
     current_story: storyContext,
     selected_text: selectedText || undefined,
     cursor_position: cursorPosition !== null ? cursorPosition : undefined,
   };
   await api.sendCopilotEvent(sessionId, storyId, "USER_CHAT", JSON.stringify(payload));
   ```

3. **In `backend/main.py` (`CopilotEventRequest`, line 1066):**
   ```python
   class CopilotEventRequest(BaseModel):
       session_id: str
       event_type: str
       event_data: str
       story_id: int | None = None
       selected_text: str | None = None
       cursor_position: int | None = None
   ```

4. **In `backend/agents/copilot_agent.py` (`process_event`, line 831):**
   Extract `selected_text` and `cursor_position` from `parsed_payload`:
   ```python
   selected_text = parsed_payload.get("selected_text") or parsed_payload.get("selectedText") or ""
   cursor_position = parsed_payload.get("cursor_position") or parsed_payload.get("cursorPosition")
   ```
   Pass them to `_perform_direct_manuscript_edit` and `SemanticChunkSlicer.slice_manuscript`.

---

### 2.2. Chapter Targeting and Activating `instruction` in `SemanticChunkSlicer`

#### Current Status
- `backend/agents/copilot_agent.py:347`:
  `def slice_manuscript(cls, story: str, target: Any, instruction: str = "") -> ChunkSlice:`
  The parameter `instruction` is accepted but **completely unused** in lines 348–421!
- Existing slicing only inspects `target` (e.g., `TARGET_1_OPENING` slices before Chapter 2; `TARGET_4_CLIMAX_ENDING` slices before the last chapter).
- There is **no mechanism** to identify or target specific chapters like "sửa Chương 3" or "sửa Chương 2".

#### Concrete Design for Chapter Targeting & Position Slicing
In `SemanticChunkSlicer.slice_manuscript`:
Add prioritized resolution:

```python
@classmethod
def slice_manuscript(
    cls,
    story: str,
    target: Any,
    instruction: str = "",
    selected_text: str = "",
    cursor_position: Optional[int] = None
) -> ChunkSlice:
    if not story:
        return ChunkSlice("", "", "")

    # Priority 1: Explicit selected_text from frontend
    if selected_text and selected_text.strip():
        clean_sel = selected_text.strip()
        idx = -1
        if cursor_position is not None and 0 <= cursor_position < len(story):
            candidate = story[cursor_position:cursor_position + len(clean_sel)]
            if candidate == clean_sel:
                idx = cursor_position
        if idx == -1:
            idx = story.find(clean_sel)
        if idx != -1:
            prefix = story[:idx]
            window = story[idx:idx + len(clean_sel)]
            suffix = story[idx + len(clean_sel):]
            return ChunkSlice(prefix, window, suffix)

    # Priority 2: Chapter Targeting extracted from instruction (e.g. "sửa Chương 3", "edit chapter 2")
    if instruction:
        ch_target_m = re.search(
            r'(?:sửa|chỉnh\s*sửa|viết\s*lại|thay\s*đổi|chương|chapter|hồi|tiết|phần)\s*(?:chương|chapter|hồi|tiết|phần)?\s*(\d+)',
            instruction,
            re.IGNORECASE
        )
        if ch_target_m:
            target_ch_num = ch_target_m.group(1).strip()
            # Scan all chapter markers in the story
            ch_headers = list(re.finditer(
                r'(?:^|\n)(#{1,3}\s+(?:chương|chapter|hồi|tiết|phần)\s*(\d+)[^\n]*)',
                story,
                re.IGNORECASE
            ))
            for i, match in enumerate(ch_headers):
                if match.group(2).strip() == target_ch_num:
                    # Found targeted chapter
                    start_pos = match.start() + (1 if story[match.start()] == '\n' else 0)
                    if i + 1 < len(ch_headers):
                        end_pos = ch_headers[i + 1].start() + (1 if story[ch_headers[i + 1].start()] == '\n' else 0)
                        return ChunkSlice(story[:start_pos], story[start_pos:end_pos].strip(), "\n\n" + story[end_pos:].strip())
                    else:
                        return ChunkSlice(story[:start_pos], story[start_pos:].strip(), "")

    # Priority 3: Fallback to existing Target 1, 4, 3, 5 semantic chunking
    ...
```

**Key Invariants Maintained:**
- `prefix + window_to_edit + suffix == story` when window is untouched.
- When "sửa Chương 3" is issued, `window_to_edit` is bounded precisely to Chapter 3's text, leaving Chapter 1, 2, and 4+ in `prefix` and `suffix`.

---

### 2.3. Path B (Master Controller Fallback) 2000-Char Overwrite Bug

#### Root Cause Analysis
- **Exact Location:** `backend/agents/copilot_agent.py`, lines 873–914.
- In line 880:
  ```python
  short_context = memory.get_short_context(max_chars=3000) if memory else (current_story[-2000:] if current_story else "Chưa có truyện.")
  ```
  If `_is_direct_edit_request` evaluates to False or fails, execution falls through to Path B.
  Path B provides the LLM only with `short_context` (which is `current_story[-2000:]`).
- In lines 906–914:
  ```python
  if isinstance(res, dict) and res.get("action") == "edit_story_direct":
      if "action_params" not in res or not isinstance(res.get("action_params"), dict):
          res["action_params"] = {}
      params = res["action_params"]
      if "updated_story_content" not in params and "updated_story_content" in res:
          params["updated_story_content"] = res["updated_story_content"]
      if "updated_story_content" in params:
          params["updated_story_content"] = unwrap_story_prose(params["updated_story_content"])
      return res
  ```
  If the LLM returns `action = "edit_story_direct"`, `params["updated_story_content"]` contains ONLY the rewritten 2000-character snippet.
  When sent to frontend (`page.tsx:487`), the editor executes:
  `setStoryContent(newContent)`
  **Result:** The entire preceding manuscript (`current_story[:-2000]`) is deleted!

#### Remediation Strategy
1. **Primary Route-Through:**
   If Path B produces an `edit_story_direct` action and `current_story` is non-empty, re-route through Path A (`_perform_direct_manuscript_edit`):
   ```python
   if isinstance(res, dict) and res.get("action") == "edit_story_direct":
       # Route through Path A surgery engine to preserve full manuscript integrity
       if current_story and user_message:
           direct_res = self._perform_direct_manuscript_edit(
               user_instruction=user_message,
               current_story=current_story,
               selected_text=selected_text,
               cursor_position=cursor_position
           )
           if direct_res:
               return direct_res
   ```
2. **Safe Prefix/Suffix Merging Fallback:**
   If Path A cannot be called, reconstruct the story rather than overwriting:
   ```python
   raw_snippet = params.get("updated_story_content", "")
   if raw_snippet and len(current_story) > 2000:
       # If raw_snippet does not contain the beginning of the story, merge safely with prefix
       if not raw_snippet.strip().startswith(current_story[:100].strip()):
           prefix = current_story[:-2000].rstrip()
           merged_content = f"{prefix}\n\n{raw_snippet}".strip()
           params["updated_story_content"] = HeadingPreservationEngine.preserve_headings(
               current_story, short_context, merged_content
           )
   ```

---

### 2.4. HeadingPreservationEngine Intermediate Chapter Titles Bunching

#### Root Cause Analysis
- **Exact Location:** `backend/agents/copilot_agent.py`, lines 312–339.
- Current code:
  ```python
  if window_text:
      orig_ch_headings = re.findall(
          r'(#{1,3}\s+(?:Chương|Hồi|Tiết|Phần|Chapter)[^\n]*)',
          window_text,
          re.IGNORECASE
      )
      for ch_h in orig_ch_headings:
          ch_h_clean = ch_h.strip()
          ...
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
- **The Bug:**
  When `window_text` contains multiple chapters (e.g. Chapter 1, Chapter 2, Chapter 3 in `TARGET_3_MIDDLE_BEATS` or `TARGET_5_TONE_STYLE`), if the LLM drops or alters the headings for Chapter 2 and Chapter 3, `has_heading` is False.
  The engine prepends each missing heading to the very top:
  `cleaned = f"{ch_h_clean}\n\n{cleaned}"`
  Because this loop runs in order, Chapter 2 is prepended to the top, and then Chapter 3 is prepended to the top of Chapter 2!
  **Outcome:** The output begins with:
  ```markdown
  ## Chương 3: [Tên chương 3]

  ## Chương 2: [Tên chương 2]

  ## Chương 1: [Tên chương 1]
  ```
  All intermediate chapter headings bunch at the top in reverse order!

#### Remediation Design
Rather than unconditionally prepending missing chapter headings, compute their relative positions:

1. **Heading Offset Tracking:**
   Extract each heading's character start offset in `window_text`:
   $P_i = \text{offset}(H_i)$ in `window_text`.
   Relative position $r_i = P_i / \text{len}(window\_text) \in [0.0, 1.0]$.

2. **Placement Strategy:**
   - If $r_i < 0.1$ (opening chapter): Place at the top (under title if title exists).
   - If $r_i \ge 0.1$ (intermediate/later chapter):
     - **Anchor Method:** In `window_text`, take the first sentence following $H_i$. If that sentence or key phrase exists in `cleaned`, insert $H_i$ immediately before that paragraph.
     - **Proportional Paragraph Method:** Split `cleaned` into paragraphs: `paragraphs = cleaned.split("\n\n")`. Insert $H_i$ at index $k = \max(1, \text{round}(r_i \times \text{len}(paragraphs)))$.
   - Guarantee strict ascending order: $pos(H_1) < pos(H_2) < \dots < pos(H_n)$.

---

## 3. Investigation of R5: Database & Performance

### 3.1. SQLite WAL Mode Configuration

#### Current Configuration
- In `backend/db/models.py:261`:
  ```python
  engine = create_engine('sqlite:///narrai.db', connect_args={'check_same_thread': False})
  Base.metadata.create_all(engine)
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  ```
- In `backend/main.py:78`:
  ```python
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  ```
- No `PRAGMA journal_mode=WAL` or `PRAGMA synchronous=NORMAL` is currently configured.

#### Implementation Design
1. **SQLAlchemy Event Listener on `engine` (or `Engine` class):**
   ```python
   from sqlalchemy import event

   @event.listens_for(engine, "connect")
   def set_sqlite_pragma(dbapi_connection, connection_record):
       cursor = dbapi_connection.cursor()
       cursor.execute("PRAGMA journal_mode=WAL;")
       cursor.execute("PRAGMA synchronous=NORMAL;")
       cursor.close()
   ```
2. **Auto-Migration Execution in `backend/db/models.py`:**
   Execute immediately during database initialization:
   ```python
   with engine.connect() as conn:
       conn.execute(text("PRAGMA journal_mode=WAL;"))
       conn.execute(text("PRAGMA synchronous=NORMAL;"))
       conn.commit()
   ```
3. **Verification Command:**
   ```python
   with engine.connect() as conn:
       mode = conn.execute(text("PRAGMA journal_mode;")).scalar()
       assert mode.lower() == "wal"
   ```

---

### 3.2. Missing Indexes and Composite Indexes in `backend/db/models.py`

#### Audit of Current Indexes

| Model | Column | Current State | Required State | Rationale |
|---|---|---|---|---|
| `Comic` | `user_id` | `Column(Integer, ForeignKey('users.id'))` | `index=True` | Queried in `continue_comic` and author lookups |
| `Comic` | `story_id` | `Column(Integer, ForeignKey('stories.id'))` | `index=True` | Queried in `continue_comic`, `recommender_service` |
| `ComicPanel` | `comic_id` | `Column(Integer, ForeignKey('comics.id'))` | `index=True` | `Comic.panels` relationship & panel queries |
| `SocialPost` | `story_id` | `Column(Integer, ForeignKey('stories.id'))` | `index=True` | `Story.social_posts` relationship & duplicate checks |

#### Required Composite Indexes for Hot Query Paths

1. **`ComicPanel`: `(comic_id, panel_index)`**
   - **Hot Path:** `main.py:903`
     ```python
     db.query(ComicPanel).filter(ComicPanel.comic_id == comic.id).order_by(ComicPanel.panel_index).all()
     ```
   - **Index Definition:** `Index('ix_comic_panels_comic_id_panel_index', 'comic_id', 'panel_index')`

2. **`SocialPost`: `(genre, created_at)`**
   - **Hot Path:** `recommender_service.py:444` and `social_router.py:121`
     ```python
     query.filter(SocialPost.genre.ilike(...)).order_by(SocialPost.created_at.desc())
     ```
   - **Index Definition:** `Index('ix_social_posts_genre_created_at', 'genre', 'created_at')`

3. **`SocialPost`: `(user_id, created_at)`**
   - **Hot Path:** Author profile & author works list:
     ```python
     db.query(SocialPost).filter(SocialPost.user_id == user_id).order_by(SocialPost.created_at.desc())
     ```
   - **Index Definition:** `Index('ix_social_posts_user_id_created_at', 'user_id', 'created_at')`

4. **`PostInteraction`: `(post_id, interaction_type, created_at)`**
   - **Hot Path:** `recommender_service.py:1116`
     ```python
     db.query(PostInteraction).filter(
         PostInteraction.post_id == post_id,
         PostInteraction.interaction_type == "COMMENT"
     ).order_by(desc(PostInteraction.created_at)).all()
     ```
   - **Index Definition:** `Index('ix_post_interactions_post_type_created', 'post_id', 'interaction_type', 'created_at')`

5. **`Comic`: `(user_id, created_at)`**
   - **Hot Path:** `recommender_service.py:959`
     ```python
     db.query(Comic).filter(Comic.user_id == user_id).order_by(Comic.created_at.desc()).first()
     ```
   - **Index Definition:** `Index('ix_comics_user_id_created_at', 'user_id', 'created_at')`

#### Existing Database Migration in `backend/db/models.py`
In the `try...except` migration block (lines 273–293), add DDL statements:
```python
conn.execute(text("CREATE INDEX IF NOT EXISTS ix_comics_user_id ON comics(user_id);"))
conn.execute(text("CREATE INDEX IF NOT EXISTS ix_comics_story_id ON comics(story_id);"))
conn.execute(text("CREATE INDEX IF NOT EXISTS ix_comic_panels_comic_id ON comic_panels(comic_id);"))
conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_posts_story_id ON social_posts(story_id);"))
conn.execute(text("CREATE INDEX IF NOT EXISTS ix_comic_panels_comic_id_panel_index ON comic_panels(comic_id, panel_index);"))
conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_posts_genre_created_at ON social_posts(genre, created_at);"))
conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_posts_user_id_created_at ON social_posts(user_id, created_at);"))
conn.execute(text("CREATE INDEX IF NOT EXISTS ix_post_interactions_post_type_created ON post_interactions(post_id, interaction_type, created_at);"))
conn.execute(text("CREATE INDEX IF NOT EXISTS ix_comics_user_id_created_at ON comics(user_id, created_at);"))
conn.commit()
```

---

### 3.3. FastAPI GZip Middleware Integration

#### Current Status
- `backend/main.py:44–50` has `CORSMiddleware`.
- `GZipMiddleware` is not currently mounted.

#### Implementation Design
- Import:
  ```python
  from fastapi.middleware.gzip import GZipMiddleware
  ```
- Placement: Right after `app.add_middleware(CORSMiddleware, ...)` at lines 50–51:
  ```python
  # GZip response compression for responses >= 500 bytes
  app.add_middleware(GZipMiddleware, minimum_size=500)
  ```
- This compresses all large payloads (JSON feeds, story chapters, SVG morphicons) exceeding 500 bytes, reducing bandwidth consumption while keeping small messages uncompressed.

---

## 4. Synthesis of Proposed Code Changes

### Target 1: `frontend/src/components/editor/StoryEditor.tsx`
- Add `getCaretOffset` helper.
- Update `handleMouseUp` and `onKeyUp` to capture caret character offset.
- Expand `onSelectText: (text: string, cursorPosition?: number) => void`.

### Target 2: `frontend/src/app/page.tsx`
- Add state `const [cursorPosition, setCursorPosition] = useState<number | null>(null)`.
- Pass `cursorPosition` to `handleSendCopilotMessage`.
- Include `selected_text` and `cursor_position` in the `USER_CHAT` JSON payload.

### Target 3: `backend/agents/copilot_agent.py`
- In `SemanticChunkSlicer.slice_manuscript`:
  - Accept `selected_text` and `cursor_position`.
  - Priority 1: Exact `selected_text` slicing.
  - Priority 2: Chapter targeting regex from `instruction` (e.g. `r'chương\s*(\d+)'`).
- In `HeadingPreservationEngine.preserve_headings`:
  - Calculate relative offsets $r_i$ for missing headings.
  - Insert missing intermediate headings at appropriate relative paragraph breaks rather than prepending to top.
- In `process_event` (Path B):
  - If LLM returns `edit_story_direct`, route to Path A (`_perform_direct_manuscript_edit`) or merge with `current_story[:-2000]`.

### Target 4: `backend/db/models.py`
- Add `@event.listens_for(engine, "connect")` for `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`.
- Add `index=True` to `Comic.user_id`, `Comic.story_id`, `ComicPanel.comic_id`, `SocialPost.story_id`.
- Add `__table_args__` composite indexes to `ComicPanel`, `SocialPost`, `PostInteraction`, `Comic`.
- Execute `CREATE INDEX IF NOT EXISTS` in the auto-migration block.

### Target 5: `backend/main.py`
- Add `from fastapi.middleware.gzip import GZipMiddleware`.
- Add `app.add_middleware(GZipMiddleware, minimum_size=500)`.
- Add optional fields `selected_text` and `cursor_position` to `CopilotEventRequest`.

---

## 5. Verification Plan

1. **Syntax & Compilation:**
   - Backend: `python -m py_compile backend/agents/copilot_agent.py backend/db/models.py backend/main.py`
   - Frontend: `npm run build` in `frontend/`
2. **Regression Test Suite:**
   - `python backend/tests/run_all_tests.py` (ensure all 182 existing tests pass 100%).
3. **Dedicated R1 Tests:**
   - Selected text targeting test: send `selected_text` -> only selected text replaced.
   - Chapter targeting test: "sửa Chương 3" -> only Chapter 3 window returned.
   - Multi-chapter heading preservation test: test with 3 chapters where LLM strips headings -> verify headings maintain 1, 2, 3 ordering and do not bunch at top.
   - Path B regression test: feed 5000-character story to Master Controller -> verify returned story retains full length and prefix.
4. **Dedicated R5 Tests:**
   - WAL mode test: `conn.execute(text("PRAGMA journal_mode;")).scalar() == "wal"`.
   - Index verification: `inspector.get_indexes("comics")`, `inspector.get_indexes("comic_panels")`, `inspector.get_indexes("social_posts")`.
   - GZip test: Client request with `Accept-Encoding: gzip` receiving response > 500 bytes returns `Content-Encoding: gzip`.
