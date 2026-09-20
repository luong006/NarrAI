# HANDOFF REPORT: Requirement 3 (R3)
## Elimination of Ellipsis/Truncation (".....") in Comic Panels & Sentence Boundary Decomposition

**Author**: `explorer_survey_3`  
**Target Recipient**: Orchestrator / Implementer Agent  
**Type**: Hard Handoff (Investigation Complete)  
**Date**: 2026-09-19  

---

## 1. Observation

Direct code inspections and pattern matches revealed the following specific locations and behaviors:

1. **Schema Few-Shot Pattern Leakage in `BEAT_DIRECTOR_PROMPT`**:
   - Path: `backend/agents/comic_agent.py`
   - Lines: 80–82
   - Verbatim code:
     ```python
     80:     "image_prompt": "wide establishing shot of...",
     81:     "dialogue_text": "...",
     82:     "layout_type": "wide"
     ```
   - LLMs receive `"..."` as the example value for `dialogue_text` in the output schema, encouraging truncated dialogue strings ending in `...`.

2. **Incomplete Regex Cleaning in `_validate_panels`**:
   - Path: `backend/agents/comic_agent.py`
   - Lines: 238–243
   - Verbatim code:
     ```python
     238: dialogue = str(item.get("dialogue_text", "")).strip()
     239: # Clean complete sentence, NEVER truncate with "..." or chop words midway
     240: dialogue = re.sub(r'[\.\s…]{2,}$', '', dialogue).strip()
     241: if dialogue and dialogue[-1] not in ['.', '!', '?', '"', '”']:
     242:     dialogue += '.'
     ```
   - `re.sub(r'[\.\s…]{2,}$', '', dialogue)` only checks the end of the string. Mid-sentence ellipses (`...`, `.....`, `…`), multiple scattered dots, and strings consisting entirely of `...` are not handled properly. Mid-sentence cuts by the LLM remain grammatically incomplete.

3. **Hardcoded Ellipsis & Defective Fallback Generation in `_create_structured_beat_fallback`**:
   - Path: `backend/agents/comic_agent.py`
   - Lines: 337, 345, 365
   - Verbatim code:
     ```python
     337: lines = [line.strip() for line in story_text.split("\n") if len(line.strip()) > 15]
     ...
     345: for idx, line in enumerate(lines[:12]):
     ...
     365: {"panel_index": 1, "image_prompt": f"{STYLE_PREFIX}{lead_dna}, wide establishing shot of {bg_anchor}{STYLE_SUFFIX}", "dialogue_text": "Câu chuyện bắt đầu...", "layout_type": "wide"},
     ```
   - Line 365 contains a hardcoded ellipsis: `"Câu chuyện bắt đầu..."`.
   - Paragraphs are split only by newline `\n`, cramming 200+ word paragraphs into a single panel.
   - Short dialogue lines under 16 chars are discarded.
   - Panels are capped at 12 lines, discarding the remaining story beats.

4. **Arbitrary Character Slicing at Chunk Boundaries**:
   - Path: `backend/main.py`
   - Lines: 442–444 & 502–503
   - Verbatim code:
     ```python
     442: chunk_size = 6000
     443: text_to_adapt = request.story_text[:chunk_size]
     444: adapted_len = len(text_to_adapt)
     ...
     502: chunk_size = 6000
     503: new_text = remaining_text[:chunk_size]
     ```
   - Slicing `story_text[:6000]` cuts at the 6000th character regardless of sentence boundaries, frequently amputating words and sentences mid-thought.

5. **Frontend Speech Bubble Integrity**:
   - Path: `frontend/src/components/comic/ComicViewer.tsx:70–74` and `frontend/src/app/globals.css:66–86`
   - `.speech-bubble` has `overflow: visible !important; max-height: none !important; word-wrap: break-word;`
   - No CSS truncation or line-clamp exists. Frontend cleanly displays whatever text the backend delivers.

---

## 2. Logic Chain

1. **Premise**: Acceptance criteria state: *"Dưới mỗi khung truyện tranh, lời thoại/phụ đề dẫn chuyện hiển thị trọn câu, hoàn toàn không có dấu ..... cắt cụt chữ."*
2. **Cause of Truncation Occurrence**:
   - When a user submits a long story, `backend/main.py` cuts at 6000 characters without checking sentence boundaries, providing an incomplete sentence to `ComicDirectorAgent`.
   - In `ComicDirectorAgent`, the Groq LLM is guided by `BEAT_DIRECTOR_PROMPT`. Because the schema example demonstrates `"dialogue_text": "..."`, the LLM adopts this pattern and emits dialogue ending in `...` or `.....`.
   - When `_validate_panels` runs, its regex only cleans trailing dots at the end of the string; it does not replace internal ellipses or repair incomplete sentence fragments.
   - If the LLM call fails, `_create_structured_beat_fallback` splits only by `\n` and hardcodes `"dialogue_text": "Câu chuyện bắt đầu..."`.
3. **Remediation Path**:
   - Implement `extract_sentence_bounded_chunk` in `backend/main.py` to guarantee that text chunking always snaps to the nearest complete sentence boundary before the character limit.
   - Replace the `"..."` format examples in `BEAT_DIRECTOR_PROMPT` with complete sentence examples.
   - Implement `decompose_story_beats` in `comic_agent.py` to parse long paragraphs into atomic dialogue and narrative beats.
   - Replace trailing and internal ellipses in `sanitize_complete_dialogue`, ensuring all dialogues and captions are grammatically complete sentences ending with valid terminal punctuation.
   - Overhaul `_create_structured_beat_fallback` to map decomposed beats into sequential panels with zero ellipsis.

---

## 3. Caveats

1. **Vietnamese Dialogue Variations**: Spoken dialogue in fiction can begin with em-dashes (`—`), hyphens (`-`), or direct quotes (`"..."`, `“...”`). The sentence boundary regex and beat splitter must support all common Vietnamese dialogue conventions.
2. **Hesitation Representation**: In natural human speech, characters sometimes hesitate (e.g. `"Tôi... tôi không biết"`). R3 strictly prohibits `...` and `.....` in comic panels. Converting hesitations to em-dash breaks (`"Tôi - tôi không biết."`) or commas (`"Tôi, tôi không biết."`) preserves character emotion while strictly satisfying the zero-ellipsis requirement.
3. **Read-Only Scope**: This report provides verified locations and code proposals. Implementation should be carried out by the designated implementer agent.

---

## 4. Conclusion

Requirement 3 can be fully resolved with precise, surgical changes across two files:
- **`backend/agents/comic_agent.py`**:
  1. Update `BEAT_DIRECTOR_PROMPT` to remove `"dialogue_text": "..."` and replace with full-sentence examples.
  2. Implement `decompose_story_beats(story_text: str)` to break paragraphs into complete sentences and beats.
  3. Implement `sanitize_complete_dialogue(text: str)` to eliminate all occurrences of `...`, `…`, and `.....`, converting internal pauses to natural punctuation and enforcing terminal punctuation.
  4. Overhaul `_create_structured_beat_fallback` to generate beat-by-beat panels from `decompose_story_beats` and remove hardcoded `"Câu chuyện bắt đầu..."`.
- **`backend/main.py`**:
  1. Add `extract_sentence_bounded_chunk(text, target_size=5000)` to ensure chunks in `create_comic` and `continue_comic` end strictly at sentence boundaries.

---

## 5. Verification Method

### Test 1: Python Compilation
```bash
python -m py_compile backend/agents/comic_agent.py
python -m py_compile backend/main.py
```
*Expected*: Zero syntax or import errors.

### Test 2: Unit Test for Zero Ellipsis Sanitizer & Beat Decomposition
Execute a test script against `comic_agent.py`:
- Input string containing multiple trailing and internal dots:
  `'Lý Tiêu: "Không thể nào..... tôi nhất định sẽ... trả thù..."'`
- Call `sanitize_complete_dialogue(text)`
- *Assert*: `dialogue == 'Lý Tiêu: "Không thể nào - tôi nhất định sẽ trả thù."'`
- *Assert*: `'...' not in dialogue and '…' not in dialogue and '.....' not in dialogue`

### Test 3: Sentence Boundary Chunking Test
- Create a 7000-character test story with 30 sentences.
- Call `extract_sentence_bounded_chunk(test_story, target_size=5000)`
- *Assert*: The returned chunk ends with `.`, `!`, `?`, or `"`.
- *Assert*: The next character in `test_story` is whitespace or the capital letter of a new sentence.

### Test 4: Full System Benchmark
```bash
python backend/tests/run_full_system_benchmark.py
```
*Expected*: Comic Beat-by-Beat panel test passes with all panels containing complete sentences and zero ellipses.
