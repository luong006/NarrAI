# Deep Codebase Analysis: Requirement 3 (R3)
## Chấm dứt hoàn toàn tình trạng cắt xén dấu "....." trong truyện tranh NarrAI

**Agent**: `explorer_survey_3`  
**Date**: 2026-09-19  
**Focus**: Requirement 3 (R3) - Comic Panel Text Integrity, Sentence Boundaries Decomposition, Zero Truncation / Ellipsis

---

## 1. Executive Summary

Requirement 3 requires eliminating **100% of text truncation and ellipsis marks (`...`, `.....`, `…`)** in manga comic panels, ensuring that dialogues and captions under every panel are complete, expressive Vietnamese sentences, and implementing **Sentence Boundaries Decomposition** so that long paragraphs and stories are parsed into complete sequential panels matching story pacing without any missing beats or broken words.

Our investigation identified **4 critical architectural defect sites** across `backend/agents/comic_agent.py` and `backend/main.py`:
1. **Schema Few-Shot Pattern Leakage** (`comic_agent.py:81`): The JSON schema example given to Groq LLM literally specifies `"dialogue_text": "..."` and `"image_prompt": "wide establishing shot of..."`, actively training/prompting the LLM to output truncated dialogue ending with `...`.
2. **Defective Dialogue Sanitizer** (`comic_agent.py:238-243`): `re.sub(r'[\.\s…]{2,}$', '', dialogue)` only strips trailing dots at the string boundary, leaving internal ellipses (`.....`), converting strings that are only `...` into empty/punctuation-only strings, and allowing sentences truncated mid-thought by LLMs to remain amputated.
3. **Hardcoded Ellipsis & Crude Fallback Slicing** (`comic_agent.py:335-368`): The structured fallback hardcodes `"dialogue_text": "Câu chuyện bắt đầu..."`, splits paragraphs only by `\n` (ignoring multi-sentence paragraphs), silently discards dialogue lines shorter than 16 characters (`len > 15`), and caps panels arbitrarily at `lines[:12]`.
4. **Brutal String Slicing at Chunk Boundaries** (`backend/main.py:443, 503`): `request.story_text[:6000]` and `remaining_text[:6000]` cut story text at arbitrary character indices, severing words and sentences in half. This feeds truncated sentence fragments to the LLM and leaves corrupted starting fragments for subsequent continuations.

---

## 2. Root Cause Mapping & Code Inspection

### Defect 1: Schema Format Example Contamination
- **File**: `backend/agents/comic_agent.py`
- **Lines**: 76–85
```python
76: OUTPUT FORMAT:
77: Return ONLY a valid JSON array of panel objects:
78: [
79:   {
80:     "panel_index": 1,
81:     "image_prompt": "wide establishing shot of...",
82:     "dialogue_text": "...",
83:     "layout_type": "wide"
84:   }
85: ]
```
- **Mechanism**: LLMs are autoregressive pattern completion models. While line 67 states `TUYỆT ĐỐI CẤM DẤU BA CHẤM CẮT NGANG CÂU (...)`, the few-shot JSON example directly contradicts this rule by showing `"dialogue_text": "..."`. The LLM treats `"..."` as an authorized placeholder, resulting in frequent outputs ending with `...` or containing `.....` when it summarizes narrative text.

### Defect 2: Ineffective Sanitization in `_validate_panels`
- **File**: `backend/agents/comic_agent.py`
- **Lines**: 238–243
```python
238: dialogue = str(item.get("dialogue_text", "")).strip()
239: # Clean complete sentence, NEVER truncate with "..." or chop words midway
240: dialogue = re.sub(r'[\.\s…]{2,}$', '', dialogue).strip()
241: if dialogue and dialogue[-1] not in ['.', '!', '?', '"', '”']:
242:     dialogue += '.'
```
- **Vulnerabilities**:
  1. `re.sub(r'[\.\s…]{2,}$', '', dialogue)` matches only at the end (`$`). Any `...`, `…`, `.....`, or `. . .` appearing mid-dialogue (e.g. `"Tôi... tôi không biết....."`) is partially preserved (`"Tôi... tôi không biết."`).
  2. If the LLM generates a truncated string like `"Lương nhìn thấy một bóng đen đang tiến về phía..."`, stripping the trailing dots produces `"Lương nhìn thấy một bóng đen đang tiến về phía."`, which is grammatically amputated.
  3. If the input is just `"..."` or `"....."`, `re.sub` empties it completely, leaving `""`, or appends `.` resulting in a solitary `.` in the speech bubble.
  4. There is no fallback to recover missing dialogue from narrative context.

### Defect 3: Flawed Fallback Logic & Hardcoded Ellipsis
- **File**: `backend/agents/comic_agent.py`
- **Lines**: 335–368
```python
335: def _create_structured_beat_fallback(self, story_text: str, character_dna: dict, setting_dna: dict = None) -> list:
336:     """Parses raw text paragraphs into individual dialogue and action panels as a guaranteed fallback with complete sentences."""
337:     lines = [line.strip() for line in story_text.split("\n") if len(line.strip()) > 15]
...
345:     for idx, line in enumerate(lines[:12]):
...
349:         clean_line = line.replace('"', '').replace('“', '').replace('”', '').strip()
350:         clean_line = re.sub(r'[\.\s…]{2,}$', '', clean_line).strip()
351:         if clean_line and clean_line[-1] not in ['.', '!', '?']:
352:             clean_line += '.'
...
364:     if not panels:
365:         panels = [
366:             {"panel_index": 1, "image_prompt": f"{STYLE_PREFIX}{lead_dna}, wide establishing shot of {bg_anchor}{STYLE_SUFFIX}", "dialogue_text": "Câu chuyện bắt đầu...", "layout_type": "wide"},
367:             {"panel_index": 2, "image_prompt": f"{STYLE_PREFIX}{lead_dna}, medium shot of character speaking with intense emotion, setting: {bg_anchor}{STYLE_SUFFIX}", "dialogue_text": "Chúng ta phải tiếp tục!", "layout_type": "square"},
368:         ]
```
- **Vulnerabilities**:
  1. **Direct violation**: Line 365 contains hardcoded `"dialogue_text": "Câu chuyện bắt đầu..."`.
  2. **Paragraph cramming**: Splitting only by `\n` means a 250-word narrative paragraph is assigned as a single line, resulting in massive speech-bubble text overflow.
  3. **Loss of punchy dialogue**: Real manga dialogue includes short lines: `"Đi mau!"` (8 chars), `"Là ai?"` (6 chars), `"Dừng lại!"` (9 chars). All are silently dropped because of `if len(line.strip()) > 15`.
  4. **Arbitrary truncation**: `lines[:12]` discards all story progression beyond line 12.

### Defect 4: Arbitrary Character Slicing at Chunk Boundaries
- **File**: `backend/main.py`
- **Lines**: 441–444 & 502–503
```python
441: # Adapt first chunk of story (up to 6000 chars)
442: chunk_size = 6000
443: text_to_adapt = request.story_text[:chunk_size]
444: adapted_len = len(text_to_adapt)
...
502: chunk_size = 6000
503: new_text = remaining_text[:chunk_size]
```
- **Mechanism**:
  - `request.story_text[:6000]` cuts at the 6000th character regardless of sentence or word boundaries.
  - If character 6000 falls inside `"Huy rút súng ra và bắ"` / `"t đầu nổ súng..."`:
    - `text_to_adapt` ends with `"Huy rút súng ra và bắ"`. The LLM receives an amputated sentence and emits an incomplete final panel ending in `...`.
    - In `continue_comic`, `remaining_text` starts with `"t đầu nổ súng..."`, which corrupts the first panel of the continuation!

---

## 3. Data Flow Architecture

The end-to-end comic generation pipeline:

```
[User clicks "Chuyển thể Truyện tranh" in StoryEditor]
                         │
                         ▼
frontend/src/app/page.tsx : handleAdaptComic()
                         │
                         ▼
frontend/src/lib/api.ts : generateComic()
                         │ HTTP POST /api/comic/generate
                         ▼
backend/main.py : create_comic()
  ├── [FIX NEEDED]: Replace raw slice [:6000] with extract_sentence_bounded_chunk()
  │                 Guarantees 0% cut sentences between chunks
  ├── Load Story & StoryMemory from DB
  └── director = ComicDirectorAgent()
                         │
                         ▼
backend/agents/comic_agent.py : ComicDirectorAgent.generate_comic_script()
  ├── extract_character_dna() & extract_setting_dna()
  ├── [FIX NEEDED]: decompose_story_beats(story_text)
  │                 Segments story into atomic Dialogue Beats & Narrative/Action Beats
  ├── [FIX NEEDED]: Replace few-shot schema "dialogue_text": "..." with full sentence examples
  ├── Call Groq LLM (qwen/qwen3.8-27b)
  ├── _parse_json_array()
  ├── [FIX NEEDED]: _validate_panels() -> sanitize_complete_dialogue()
  │                 Purges mid-sentence & trailing dots/ellipses, fixes punctuation
  └── [FIX NEEDED]: Fallback overhaul in _create_structured_beat_fallback()
                    Uses decomposed beats, 0% ellipsis, rich sequential panels
                         │
                         ▼
backend/main.py : _save_panels()
  └── ComicPanel rows saved to DB with proxy URL /api/comic/image/{id}
                         │
                         ▼
frontend/src/components/comic/ComicViewer.tsx
  └── Renders panels in manga grid with full-sentence speech bubble (no CSS truncation)
```

---

## 4. Proposed Architectural Fix Strategy

### Phase 1: Sentence Boundary Chunking in `backend/main.py`
Add a dedicated chunking utility:
```python
def extract_sentence_bounded_chunk(text: str, target_size: int = 4500, min_size: int = 1500) -> tuple[str, int]:
    """
    Extracts a text slice ending strictly at a sentence boundary (. ! ? \n\n)
    without ever amputating a sentence or word mid-thought.
    Returns (clean_chunk, actual_cut_offset).
    """
    if len(text) <= target_size:
        return text, len(text)

    # Search for sentence terminators between min_size and target_size
    search_window = text[min_size:target_size]
    matches = list(re.finditer(r'[\.\!\?]["”\']?\s+|\n\s*\n', search_window))
    if matches:
        cut_point = min_size + matches[-1].end()
        return text[:cut_point].strip(), cut_point

    # If no delimiter in window, search forward up to target_size + 800
    forward_window = text[target_size:target_size + 800]
    f_match = re.search(r'[\.\!\?]["”\']?\s+|\n\s*\n', forward_window)
    if f_match:
        cut_point = target_size + f_match.end()
        return text[:cut_point].strip(), cut_point

    # Fallback to whitespace break
    space_pos = text.rfind(" ", min_size, target_size)
    if space_pos != -1:
        return text[:space_pos].strip(), space_pos

    return text[:target_size], target_size
```
Apply in `create_comic` and `continue_comic`:
- In `create_comic`: `text_to_adapt, adapted_len = extract_sentence_bounded_chunk(request.story_text, target_size=5000)`
- In `continue_comic`: `new_text, chunk_len = extract_sentence_bounded_chunk(remaining_text, target_size=5000)` and `comic.adapted_offset = current_offset + chunk_len`.

### Phase 2: Sentence Boundaries & Narrative Beat Decomposition in `comic_agent.py`
Implement `decompose_story_beats(story_text: str) -> list[dict]`:
- Splits text into discrete narrative and dialogue beats using Vietnamese sentence boundaries.
- Identifies dialogues (quoted strings `"..."`, `“...”`, dashes `—`, `-`, or speaker prefixes like `Lương: ...`).
- Identifies actions and descriptive sentences.
- Normalizes punctuation, removing any `...` or `…`.
- Returns a list of structured beats:
  ```python
  {
      "beat_type": "dialogue" | "action" | "setting",
      "speaker": "Lương" | None,
      "sentence": "Hoàn chỉnh 100% không cắt xén.",
      "layout": "square" | "tall" | "wide"
  }
  ```

### Phase 3: Dialogue Sanitizer Hardening in `comic_agent.py`
Implement `sanitize_complete_dialogue(raw_text: str, fallback_prompt: str = "", panel_index: int = 1) -> str`:
1. Remove all leading dots, dashes, colons: `re.sub(r'^[\s\.\…\-\—\:\,]+', '', text)`
2. Remove all trailing dots, colons, ellipses: `re.sub(r'[\s\.\…\-\—\:\,]+$', '', text)`
3. Replace mid-sentence ellipses (`...`, `…`, `.....`) with a natural pause (` - ` or `, `):
   `text = re.sub(r'[\.\…]{2,}', ' - ', text)`
4. Collapse multiple dots: `text = re.sub(r'\.{2,}', '.', text)`
5. Enforce valid terminal punctuation (`.`, `!`, `?`, or closing quote).
6. Prevent empty or single-character dialogue. If dialogue is empty, synthesize a grammatically complete caption from the panel context.

### Phase 4: Purge Few-Shot Ellipsis Leakage in `BEAT_DIRECTOR_PROMPT`
Update the JSON schema template in `BEAT_DIRECTOR_PROMPT`:
```json
OUTPUT FORMAT:
Return ONLY a valid JSON array of panel objects:
[
  {
    "panel_index": 1,
    "image_prompt": "wide establishing shot of ancient wooden library with towering bookshelves under warm lantern light",
    "dialogue_text": "Lý Tiêu: \"Chúng ta nhất định phải tìm ra bí tịch trước khi trời sáng!\"",
    "layout_type": "wide"
  },
  {
    "panel_index": 2,
    "image_prompt": "medium close-up of young woman looking nervously at the iron door, shadows stretching across stone floor",
    "dialogue_text": "Hạ Vy: \"Nhưng lính gác đã bắt đầu đi tuần tra rồi.\"",
    "layout_type": "square"
  }
]
```

### Phase 5: Overhaul Structured Fallback `_create_structured_beat_fallback`
- Use `decompose_story_beats(story_text)` instead of `story_text.split("\n")[:12]`.
- Map each beat into a sequential panel with:
  - Appropriate layout (`wide` for scene establishment, `tall` for high drama/action, `square` for dialogue).
  - Complete, expressive `dialogue_text` formatted as `Tên: "Lời thoại hoàn chỉnh."` or narration.
  - Zero `...` or `.....`.
  - Default panel if text is empty:
    `"Hành trình mới chính thức bắt đầu tại vùng đất bí ẩn."` and
    `"Chúng ta nhất định phải tiến về phía trước để tìm kiếm câu trả lời!"`

---

## 5. Verification Matrix

| Test Case | Condition | Expected Result |
|---|---|---|
| Dialogue ending in `...` | LLM outputs `"Anh đi đâu thế..."` | Sanitizer converts to `"Anh đi đâu thế?"` or `"Anh đi đâu thế."` (0% `...`) |
| Mid-dialogue ellipsis | LLM outputs `"Tôi... tôi không ngờ....."` | Sanitizer converts to `"Tôi - tôi không ngờ."` (0% `...` or `.....`) |
| Empty / only dots | LLM outputs `"..."` or `"....."` | Sanitizer replaces with clean complete context sentence |
| Long story text (8000+ chars) | User converts large story | `extract_sentence_bounded_chunk` cuts cleanly at sentence end; 0 severed words |
| Structured fallback trigger | LLM times out or errors | Fallback generates sequential panels from decomposed beats; all sentences 100% complete |
| Few-shot prompt inspection | Prompt template sent to Groq | Format example contains zero `...` |
