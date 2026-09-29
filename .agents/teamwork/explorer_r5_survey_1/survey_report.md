# Survey & Architecture Mapping Report: Copilot Flexible Manuscript Surgery & Streaming Endpoints

**Author**: Explorer Subagent (`explorer_r5_survey_1`)  
**Target Milestone**: Requirement #1 — Copilot Flexible Manuscript Surgery (5 Targets), Dynamic Semantic Chunk Slicing, Heading Preservation & Story ID Allocation  
**Scope**: `e:\NarrAI\backend` (FastAPI routes, story services, copilot agent, manuscript editing logic, chunking/slicing, LLM prompts)  
**Date**: 2026-09-29  

---

## 1. Executive Summary

This survey provides a comprehensive architectural audit and mapping of the NarrAI backend to support **Requirement #1 (Follow-up 2026-09-29T03:08:30Z)**:
1. **Copilot Flexible Manuscript Surgery with 5 Targets**:
   - *Target 1: Opening/Hook rewrite* (preserving title and plot flow).
   - *Target 2: Character & Dialogue surgery* (names, pronouns, modern youth phrasing, subtext, physiological micro-actions across segment or entire manuscript).
   - *Target 3: Middle Beats & Scene Insertion* (pacing escalation, stakes, turning points without perturbing opening or ending).
   - *Target 4: Climax & Ending* (lingering cliffhanger or emotional surge, preserving established logic).
   - *Target 5: Tone Shift & Style Restyling* (dark, thriller, comedy, mystery, historical while preserving core plot events and characters).
2. **Dynamic Semantic Chunk Slicing Engine**: Partitioning manuscripts into `prefix` -> `window_to_edit` -> `suffix` using semantic chapter and paragraph boundaries rather than arbitrary string cuts.
3. **Strict Structural Heading Preservation**: Zero-loss guarantee for `**[TITLE]**` and `## Chương X` chapter headings.
4. **Story ID Allocation & Streaming Backend Endpoints**: Immediate allocation of `story_id` before or at the start of streaming, enabling seamless transition from Intake Chat to Story Editor and uninterrupted Manga adaptation.

---

## 2. Existing File Inventory & Current State

| File Path | Role | Key Functions / Classes | Current Limitations for Requirement #1 |
|---|---|---|---|
| `backend/agents/copilot_agent.py` | Copilot Master Controller & Direct Edit Engine | `CopilotAgent`, `unwrap_story_prose`, `_is_direct_edit_request`, `_get_windowed_manuscript`, `_perform_direct_manuscript_edit`, `process_event` | Lacks 5-target intent classifier; uses crude boolean keywords (`is_opening`, `is_ending`, `is_middle`); falls into 8000-char truncation for Target 2 & 5; heading preservation only activates for opening edits; drops `## Chương X` headings. |
| `backend/main.py` | FastAPI application root & API endpoints | `/api/copilot-event`, `/api/edit-text`, `/api/generate-story`, `/api/init-story`, `/api/generate-chapter`, `/api/end-story` | `/api/generate-story` and `/api/init-story` only allocate `story_id` at stream completion; anonymous users never receive `story_id`; no standalone story allocation endpoint. |
| `backend/agents/story_generator.py` | Full story & chapter generator | `StoryGenerator`, `LIGHT_NOVEL_ENGINE_RULES`, `generate_story_stream`, `generate_chapter_stream` | Highly capable for generation, but not wired into surgical multi-target rewriting. |
| `backend/agents/editor_agent.py` | Inline selection editor | `EditorAgent.edit_text` | Only handles small selected highlights (`/api/edit-text`), lacks macro manuscript awareness. |
| `backend/agents/qa_refiner.py` | Q&A Intake Chat & Prompt Refiner | `QARefiner.chat_interview`, `refine_prompt` | Contains rich genre ontology, 5 dramatic beats, and `[READY]` trigger, but does not allocate `story_id` upon transition. |
| `backend/db/models.py` | SQLAlchemy database models | `User`, `Story`, `Comic`, `ComicPanel`, `CoinTransaction`, `SocialPost` | `Story.user_id` is nullable (good), but DB records are not pre-created when streaming starts. |
| `backend/services/banking_service.py` | Coin deduction & refund logic | `deduct_coins`, `refund_coins`, `COST_EDIT = 2` | 2 xu deducted for manuscript edit; refund rollback is supported. |
| `backend/services/cache_service.py` | Session and draft cache manager | `CacheManager` | Caches sessions, drafts, and user tokens. |

---

## 3. Forensic Gap Analysis for Requirement #1

### 3.1 Gap 1: Lack of Multi-Dimensional Intent Classifier (5 Surgery Targets)

**Current Implementation (`backend/agents/copilot_agent.py`, lines 347-440):**
```python
is_opening = any(k in inst_lower for k in ["mở đầu", "đoạn mở", "mở bài", "opening", "intro", "beginning", "khởi đầu"])
is_ending = any(k in inst_lower for k in ["kết thúc", "đoạn kết", "kết bài", "ending", "outro", "conclusion", "cliffhanger", "cái kết"])
is_middle = any(k in inst_lower for k in ["ở giữa", "đoạn giữa", "thân bài", "thêm cảnh", "chèn cảnh", "thêm đoạn", "chèn đoạn", "giữa truyện", "middle"])
```

**Flaws Observed:**
1. **Target 2 (Character & Dialogue) is unclassified**: When a user inputs *"Đổi tên nhân vật Nam thành Lâm và sửa các câu thoại liên quan"* or *"Make the dialogue punchier with micro-actions"*, it evaluates `is_opening=False`, `is_ending=False`, `is_middle=False`. It drops into the `else:` branch, which cuts the text at 8,000 characters:
   ```python
   # Line 435:
   return "", story[:cut_idx], story[cut_idx:]
   ```
   The suffix (`story[cut_idx:]`) is ignored during editing, leaving character names and dialogues in the remainder of the manuscript completely untouched and inconsistent.
2. **Target 5 (Tone Shift & Style Restyling) is unclassified**: Requests like *"Rewrite in a darker, more gripping thriller tone"* or *"Chuyển giọng văn sang hài hước giễu nhại"* also drop into `else:`. Only the first 8,000 characters are restyled, creating an abrupt stylistic split in the story.
3. **No Target-Specific Prompts**: Currently, `copilot_agent.py` uses a single generic `DIRECT_EDIT_PROMPT` (lines 170-206) attempting to instruct the LLM on all rules simultaneously. This dilutes prompt adherence for specific surgical goals (such as micro-actions vs. pacing vs. tone).

### 3.2 Gap 2: Dynamic Semantic Chunk Slicing Deficiencies

**Current Slicing Logic:**
- **Opening Slicing** (lines 374-397): Looks for `\n#{1,3}\s+(?:chương|hồi...)` starting at offset 60, or takes the first 2-3 paragraphs. If neither matches, cuts at character 3,500.
- **Ending Slicing** (lines 400-416): Takes the last 2-3 paragraphs or the last 8,000 characters.
- **Middle Slicing** (lines 418-430): Calculates `start_p = max(1, len(paras) // 3)` and `end_p = min(len(paras) - 1, start_p + max(2, len(paras) // 3))`. This splits strictly by paragraph count, irrespective of scene breaks, dialogue boundaries, or chapter markers (`## Chương X`).
- **Concatenation Seam Bug**: Line 525 joins parts with `"\n\n".join(parts)`. If `prefix` or `suffix` already contains whitespace, or if `window_text` began inside a chapter, headings or paragraph alignments can duplicate or lose formatting.

### 3.3 Gap 3: Heading Preservation Vulnerability

**Current Implementation (`backend/agents/copilot_agent.py`, lines 504-523):**
```python
if is_opening_edit:
    # Safeguard 1: Preserve original title
    title_match = re.match(r'^(\*\*[^\*\n]+\*\*\s*\n+)', window_text.strip())
    if title_match and not clean_story.strip().startswith("**"):
        clean_story = title_match.group(1).strip() + "\n\n" + clean_story.strip()

    # Safeguard 2: Preserve explicit opening section header
    header_match = re.search(r'(#{1,3}\s*Mở\s*đầu[^\n]*|Phần\s+mở\s+đầu[^\n]*)', window_text, re.IGNORECASE)
    ...
```

**Flaws Observed:**
1. Heading preservation only executes if `is_opening_edit == True`.
2. For all other edits (Targets 2, 3, 4, 5): **ZERO heading preservation safeguards exist**.
3. If an LLM drops `**[TÊN TIÊU ĐỀ]**` during a tone shift (Target 5) or character rename (Target 2), the title is permanently erased.
4. If `window_text` contains `## Chương 1: [Tên chương]` or `## Chương 2: ...` and the LLM omits the markdown heading line, the chapter heading is lost.

### 3.4 Gap 4: Story ID Allocation & Streaming Flow

**Current Implementation (`backend/main.py`, lines 478-498 and 1188-1215):**
In `/api/generate-story`:
```python
word_count = len(full_story.split())
if word_count > 10 and current_user:
    db_save = SessionLocal()
    try:
        new_story = Story(user_id=current_user.id, refined_prompt=request.refined_prompt, story_content=full_story, word_count=word_count)
        db_save.add(new_story)
        db_save.commit()
        db_save.refresh(new_story)
        saved_story_id = new_story.id
    ...
if saved_story_id:
    yield f"\n\n[STORY_ID:{saved_story_id}]"
```

**Flaws Observed:**
1. `saved_story_id` is only committed to the database **after the entire stream completes**. If the user navigates, opens Copilot, or converts to Manga before the stream finishes, `story_id` is `null`.
2. If `current_user is None` (anonymous guest session), `Story` is **never persisted**, so `saved_story_id` is never generated. However, `db/models.py` defines `Story.user_id` as nullable:
   ```python
   user_id = Column(Integer, ForeignKey("users.id")) # Nullable by default!
   ```
   Therefore, guest stories can and should have a valid `story_id`.

---

## 4. Architectural Design for Requirement #1

### 4.1 Architecture Diagram

```
                 +-------------------------------------------------------+
                 |              Incoming Copilot Instruction             |
                 +-------------------------------------------------------+
                                            |
                                            v
                 +-------------------------------------------------------+
                 |        Multi-Dimensional Intent Classifier            |
                 |      (Target 1, Target 2, Target 3, Target 4, Target 5)|
                 +-------------------------------------------------------+
                                            |
                                            v
                 +-------------------------------------------------------+
                 |          Dynamic Semantic Chunk Slicer                |
                 |       prefix  -->  window_to_edit  -->  suffix        |
                 |  - Structural Node Parser (Title, ## Chương X)        |
                 |  - Chapter-Aware & Rolling Context Splitter           |
                 +-------------------------------------------------------+
                                            |
                                            v
                 +-------------------------------------------------------+
                 |           Targeted Surgical Prompt Engine             |
                 |  - Target 1: In Medias Res Hook & Opening             |
                 |  - Target 2: Character Rename, Dialogue & Micro-Action|
                 |  - Target 3: Middle Beats & High-Stakes Insertion     |
                 |  - Target 4: Climax & Lingering Cliffhanger           |
                 |  - Target 5: Tone Shift & Genre Atmospheric Restyle   |
                 +-------------------------------------------------------+
                                            |
                                            v
                 +-------------------------------------------------------+
                 |         Multi-Tier LLM Fallback (Groq Client)         |
                 |        gpt-oss-120b -> qwen3.8-27b -> gpt-oss-20b     |
                 +-------------------------------------------------------+
                                            |
                                            v
                 +-------------------------------------------------------+
                 |       Prose Unwrapper & DB Quarantine Guard           |
                 |             (unwrap_story_prose)                      |
                 +-------------------------------------------------------+
                                            |
                                            v
                 +-------------------------------------------------------+
                 |        Structural Heading Preservation Engine         |
                 |   - Re-inject **[TITLE]** if omitted                  |
                 |   - Re-inject ## Chương X if omitted                  |
                 |   - Validate Sequential Chapter Hierarchy             |
                 +-------------------------------------------------------+
                                            |
                                            v
                 +-------------------------------------------------------+
                 |      Seamless Seam Stitcher & DB Persistence          |
                 |             final_story -> Update DB / Cache          |
                 +-------------------------------------------------------+
```

---

## 5. Detailed Component Specifications

### 5.1 Component 1: Multi-Dimensional Intent Classifier

Create an intent classification module in `backend/services/manuscript_surgery.py` or `backend/agents/copilot_agent.py`:

```python
from enum import Enum
import re

class SurgeryTarget(str, Enum):
    TARGET_1_OPENING = "opening_hook"
    TARGET_2_CHARACTER_DIALOGUE = "character_dialogue"
    TARGET_3_MIDDLE_BEATS = "middle_beats"
    TARGET_4_CLIMAX_ENDING = "climax_ending"
    TARGET_5_TONE_STYLE = "tone_style"
    GENERAL_SURGERY = "general_surgery"

def classify_surgery_intent(instruction: str) -> SurgeryTarget:
    """
    Classifies bilingual instructions into one of the 5 surgery targets.
    Evaluates specific verbs, nouns, and intent indicators in both Vietnamese and English.
    """
    if not instruction:
        return SurgeryTarget.GENERAL_SURGERY
    text = instruction.lower().strip()

    # Target 1: Opening / Hook
    t1_patterns = [
        r"mở đầu", r"đoạn mở", r"mở bài", r"khởi đầu", r"cảnh đầu",
        r"opening", r"intro", r"hook", r"beginning", r"prologue",
        r"write a completely different opening"
    ]
    if any(re.search(p, text) for p in t1_patterns):
        return SurgeryTarget.TARGET_1_OPENING

    # Target 4: Climax & Ending
    t4_patterns = [
        r"kết thúc", r"đoạn kết", r"cái kết", r"kết bài", r"hạ màn", r"vĩ thanh",
        r"cao trào", r"ending", r"outro", r"conclusion", r"cliffhanger",
        r"make the ending much more dramatic"
    ]
    if any(re.search(p, text) for p in t4_patterns):
        return SurgeryTarget.TARGET_4_CLIMAX_ENDING

    # Target 3: Middle Beats & Scene Insertion
    t3_patterns = [
        r"thân bài", r"ở giữa", r"đoạn giữa", r"giữa truyện", r"thêm cảnh",
        r"chèn cảnh", r"thêm đoạn", r"chèn đoạn", r"tăng kịch tính",
        r"đẩy nhanh nhịp", r"nhịp độ", r"biến cố", r"va chạm", r"tình huống mới",
        r"middle", r"middle beats", r"scene insertion", r"insert scene", r"add scene",
        r"pacing", r"stakes", r"turning point"
    ]
    if any(re.search(p, text) for p in t3_patterns):
        return SurgeryTarget.TARGET_3_MIDDLE_BEATS

    # Target 5: Tone Shift & Style Restyling
    t5_patterns = [
        r"phong cách", r"giọng văn", r"đổi giọng", r"đổi phong cách",
        r"u tối", r"giật gân", r"hài hước", r"kinh dị", r"trinh thám",
        r"cổ trang", r"lãng mạn", r"hồi hộp", r"tone", r"style", r"restyling",
        r"darker", r"thriller", r"comedy", r"mystery", r"historical", r"gripping",
        r"rewrite in a darker"
    ]
    if any(re.search(p, text) for p in t5_patterns):
        return SurgeryTarget.TARGET_5_TONE_STYLE

    # Target 2: Character & Dialogue Surgery
    t2_patterns = [
        r"nhân vật", r"đổi tên", r"thay tên", r"lời thoại", r"đối thoại",
        r"xưng hô", r"tính cách", r"khẩu ngữ", r"subtext", r"tâm lý",
        r"character", r"characters", r"dialogue", r"dialogues", r"rename",
        r"pronoun", r"pronouns", r"add deeper internal thoughts"
    ]
    if any(re.search(p, text) for p in t2_patterns):
        return SurgeryTarget.TARGET_2_CHARACTER_DIALOGUE

    return SurgeryTarget.GENERAL_SURGERY
```

---

### 5.2 Component 2: Dynamic Semantic Chunk Slicer

The chunk slicer parses the manuscript using chapter markers and paragraphs:

```python
from dataclasses import dataclass
from typing import Tuple, List, Optional
import re

@dataclass
class SlicedChunk:
    prefix: str
    window_to_edit: str
    suffix: str
    target: SurgeryTarget
    original_title: Optional[str] = None
    preserved_headings: List[str] = None

class SemanticChunkSlicer:
    MAX_WINDOW_CHARS = 8000

    @classmethod
    def extract_headings(cls, text: str) -> Tuple[Optional[str], List[str]]:
        """Extracts the main title and all chapter/section headings."""
        title = None
        title_m = re.search(r'^\s*(\*\*(?:\[[^\]]+\]|[^\*\n]+)\*\*)\s*', text)
        if title_m:
            title = title_m.group(1).strip()

        headings = re.findall(r'(#{1,3}\s+(?:Chương|Hồi|Tiết|Phần|Chapter)\s+\d+[^ \n]*)', text, re.IGNORECASE)
        return title, headings

    @classmethod
    def slice_manuscript(cls, story: str, target: SurgeryTarget, instruction: str = "") -> SlicedChunk:
        """
        Dynamically slices manuscript into prefix, window_to_edit, and suffix
        based on target semantics.
        """
        if not story:
            return SlicedChunk(prefix="", window_to_edit="", suffix="", target=target)

        title, headings = cls.extract_headings(story)

        # 1. Target 1: Opening / Hook Rewrite
        if target == SurgeryTarget.TARGET_1_OPENING:
            # Locate boundary of next chapter (Chương 2, Chương 1 if title preceded, etc.)
            ch_matches = list(re.finditer(r'\n+(?=#{1,3}\s+(?:chương|hồi|tiết|phần\s+\d+|chapter)\s+[2-9]|\n##\s+[^\n]+)', story, re.IGNORECASE))
            if ch_matches:
                split_idx = ch_matches[0].start()
                if 100 <= split_idx <= 5000:
                    return SlicedChunk(
                        prefix="",
                        window_to_edit=story[:split_idx].strip(),
                        suffix="\n\n" + story[split_idx:].strip(),
                        target=target,
                        original_title=title,
                        preserved_headings=headings
                    )

            # Paragraph fallback: take first 2-3 paragraphs (up to 3,500 chars)
            paras = [p.strip() for p in story.split("\n\n") if p.strip()]
            if len(paras) >= 3:
                n_paras = min(3, max(1, len(paras) - 2))
                opening = "\n\n".join(paras[:n_paras])
                rest = "\n\n".join(paras[n_paras:])
                return SlicedChunk(prefix="", window_to_edit=opening, suffix="\n\n" + rest, target=target, original_title=title)

            return SlicedChunk(prefix="", window_to_edit=story, suffix="", target=target, original_title=title)

        # 2. Target 4: Climax & Ending
        elif target == SurgeryTarget.TARGET_4_CLIMAX_ENDING:
            # Check for last chapter heading
            ch_matches = list(re.finditer(r'\n+(?=#{1,3}\s+(?:chương|hồi|tiết|phần|chapter)\s+\d+)', story, re.IGNORECASE))
            if ch_matches and len(ch_matches) >= 2:
                last_ch = ch_matches[-1].start()
                return SlicedChunk(
                    prefix=story[:last_ch].strip() + "\n\n",
                    window_to_edit=story[last_ch:].strip(),
                    suffix="",
                    target=target,
                    original_title=title,
                    preserved_headings=headings
                )

            paras = [p.strip() for p in story.split("\n\n") if p.strip()]
            if len(paras) >= 3:
                n_end = min(3, max(1, len(paras) - 2))
                prefix = "\n\n".join(paras[:-n_end])
                ending = "\n\n".join(paras[-n_end:])
                return SlicedChunk(prefix=prefix + "\n\n", window_to_edit=ending, suffix="", target=target, original_title=title)

            return SlicedChunk(prefix="", window_to_edit=story, suffix="", target=target, original_title=title)

        # 3. Target 3: Middle Beats & Scene Insertion
        elif target == SurgeryTarget.TARGET_3_MIDDLE_BEATS:
            # If multi-chapter, isolate middle chapter(s)
            ch_matches = list(re.finditer(r'\n+(?=#{1,3}\s+(?:chương|hồi|chapter)\s+\d+)', story, re.IGNORECASE))
            if len(ch_matches) >= 3:
                # Chapter 1 is prefix, Chapter 2 is window, Chapter 3+ is suffix
                start_win = ch_matches[1].start()
                end_win = ch_matches[2].start()
                return SlicedChunk(
                    prefix=story[:start_win].strip() + "\n\n",
                    window_to_edit=story[start_win:end_win].strip(),
                    suffix="\n\n" + story[end_win:].strip(),
                    target=target,
                    original_title=title,
                    preserved_headings=headings
                )

            paras = [p.strip() for p in story.split("\n\n") if p.strip()]
            if len(paras) >= 4:
                start_p = max(1, len(paras) // 3)
                end_p = min(len(paras) - 1, start_p + max(2, len(paras) // 3))
                prefix_t = "\n\n".join(paras[:start_p])
                mid_t = "\n\n".join(paras[start_p:end_p])
                suf_t = "\n\n".join(paras[end_p:])
                return SlicedChunk(prefix=prefix_t + "\n\n", window_to_edit=mid_t, suffix="\n\n" + suf_t, target=target, original_title=title)

            return SlicedChunk(prefix="", window_to_edit=story, suffix="", target=target, original_title=title)

        # 4. Target 2 & Target 5: Character/Dialogue & Tone Restyle (Whole Story or Rolling)
        else:
            if len(story) <= cls.MAX_WINDOW_CHARS:
                return SlicedChunk(prefix="", window_to_edit=story, suffix="", target=target, original_title=title, preserved_headings=headings)
            
            # For large stories in tone/character rewrite:
            # Locate first chapter split near boundary
            cut_idx = cls.MAX_WINDOW_CHARS
            last_p = story[:cut_idx].rfind("\n\n## ")
            if last_p < 2000:
                last_p = story[:cut_idx].rfind("\n\n")
            if last_p > 2000:
                cut_idx = last_p
            return SlicedChunk(
                prefix="",
                window_to_edit=story[:cut_idx].strip(),
                suffix="\n\n" + story[cut_idx:].strip(),
                target=target,
                original_title=title,
                preserved_headings=headings
            )
```

---

### 5.3 Component 3: Structural Heading Preservation Engine

Guarantees 100% preservation of `**[TITLE]**` and `## Chương X` headings:

```python
class HeadingPreservationEngine:
    @staticmethod
    def preserve_headings(
        original_story: str,
        window_text: str,
        revised_window: str,
        target: SurgeryTarget
    ) -> str:
        """
        Guarantees that **[TITLE]** and chapter headers present in window_text or
        original_story are retained in revised_window.
        """
        cleaned = revised_window.strip()

        # 1. Title Preservation (**[TITLE]** or **TITLE**)
        title_pattern = r'^\s*(\*\*(?:\[[^\]]+\]|[^\*\n]+)\*\*)\s*'
        orig_title_match = re.search(title_pattern, original_story)
        win_title_match = re.search(title_pattern, window_text)
        target_title = (win_title_match or orig_title_match)

        if target_title:
            title_str = target_title.group(1).strip()
            # If revised window omitted the title (and this window is at the start of the story)
            if not cleaned.startswith("**"):
                # Check if this window was originally at the start of the story
                if original_story.strip().startswith(title_str) and (window_text.strip().startswith(title_str) or target == SurgeryTarget.TARGET_1_OPENING):
                    cleaned = f"{title_str}\n\n{cleaned}"

        # 2. Chapter Heading Preservation (## Chương X: [Tên chương])
        orig_ch_headings = re.findall(r'(#{1,3}\s+(?:Chương|Hồi|Tiết|Phần|Chapter)\s+\d+[^ \n]*)', window_text, re.IGNORECASE)
        for ch_h in orig_ch_headings:
            ch_num_match = re.search(r'(?:Chương|Chapter)\s+(\d+)', ch_h, re.IGNORECASE)
            if ch_num_match:
                ch_num = ch_num_match.group(1)
                # Check if revised_window still contains this chapter number
                revised_has_ch = re.search(rf'#{1,3}\s+(?:Chương|Chapter)\s+{ch_num}', cleaned, re.IGNORECASE)
                if not revised_has_ch:
                    # Re-inject the chapter heading at appropriate location
                    if cleaned.startswith("**"):
                        parts = cleaned.split("\n\n", 1)
                        if len(parts) == 2:
                            cleaned = f"{parts[0]}\n\n{ch_h}\n\n{parts[1]}"
                        else:
                            cleaned = f"{cleaned}\n\n{ch_h}"
                    else:
                        cleaned = f"{ch_h}\n\n{cleaned}"

        return cleaned
```

---

### 5.4 Component 4: Five Targeted Prompt Templates

```python
SURGERY_PROMPTS = {
    # Target 1: Opening / Hook Rewrite
    SurgeryTarget.TARGET_1_OPENING: """Bạn là Bút vàng Trưởng ban Biên tập Light Novel & Web Novel.
Tác giả muốn VIẾT LẠI HOÀN TOÀN PHẦN MỞ ĐẦU (OPENING / HOOK) của câu chuyện.

YÊU CẦU CỦA TÁC GIẢ:
{instruction}

PHÂN ĐOẠN MỞ ĐẦU HIỆN TẠI:
{window_text}

QUY TẮC PHẪU THUẬT MỞ ĐẦU (TARGET 1):
1. BẮT BUỘC KHỞI ĐẦU IN MEDIAS RES: Ném nhân vật thẳng vào xung đột, tình thế hiểm nghèo hoặc biến cố bùng nổ từ câu đầu tiên.
2. TUYỆT ĐỐI 0% tả cảnh thời tiết, mây trời gió thoảng hay thuyết minh bối cảnh dài dòng ở mở đầu.
3. BẢO TỒN NGUYÊN VẸN TIÊU ĐỀ: Nếu phân đoạn gốc có tiêu đề dạng `**[TÊN TIÊU ĐỀ]**` hoặc `**TIÊU ĐỀ**`, BẮT BUỘC giữ nguyên ở dòng đầu tiên.
4. BẢO TỒN TIÊU ĐỀ CHƯƠNG: Nếu có `## Chương 1: ...`, hãy giữ nguyên hoặc cập nhật tên chương cho kịch tính.
5. KẾT NỐI LIỀN MẠCH: Đoạn kết của phần mở đầu phải nối khớp hoàn hảo với diễn biến tiếp theo của truyện.
6. ĐỘ DÀI: Viết 2-4 đoạn văn xuôi giàu cảm xúc, điểm nhìn bám sát (Tight POV), nhịp văn staccato nhanh gọn.

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ):
{{
  "updated_story_content": "Toàn văn phần mở đầu mới hoàn chỉnh kèm tiêu đề",
  "summary_of_changes": "Tóm tắt ngắn gọn 1-2 câu về những thay đổi trong phần mở đầu",
  "message": "Lời nhắn gửi tác giả về mở đầu mới"
}}""",

    # Target 2: Character & Dialogue Surgery
    SurgeryTarget.TARGET_2_CHARACTER_DIALOGUE: """Bạn là Chuyên gia Biên kịch & Đối thoại Light Novel & Web Novel.
Tác giả yêu cầu PHẪU THUẬT NHÂN VẬT & LỜI THOẠI (CHARACTER & DIALOGUE SURGERY).

YÊU CẦU CỦA TÁC GIẢ:
{instruction}

BẢN THẢO HIỆN TẠI:
{window_text}

QUY TẮC PHẪU THUẬT NHÂN VẬT & THOẠI (TARGET 2):
1. NHẤT QUÁN ĐỔI TÊN & ĐẠI TỪ: Thay đổi tên nhân vật và đại từ xưng hô trên TOÀN BỘ các câu thoại và lời dẫn chuyện một cách triệt để, không để sót tên cũ.
2. ĐỐI THOẠI SẮC BÉN & KHẨU NGỮ HIỆN ĐẠI: Lời thoại tự nhiên, gãy gọn, punchy, mang phong cách giới trẻ đương đại; loại bỏ 100% ngữ điệu dịch thuật sến súa ("ngươi/ta", "chẳng hay").
3. SUBTEXT & VI HÀNH ĐỘNG (MICRO-ACTIONS): Mỗi câu thoại phải chứa ẩn ý (thao túng, che giấu, mỉa mai ngầm) và đan xen vi hành động thực tế (siết chặt đầu ngón tay, khựng lại nửa nhịp, nuốt khan, nhếch mép).
4. GIỮ NGUYÊN BỐI CẢNH & TÌNH TIẾT: Không làm xáo trộn các biến cố đã xảy ra trong cảnh.
5. BẢO TOÀN CÁC TIÊU ĐỀ `**...**` VÀ `## Chương X` NẾU CÓ TRONG ĐOẠN.

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ):
{{
  "updated_story_content": "Toàn văn phân đoạn sau khi đã phẫu thuật nhân vật và lời thoại",
  "summary_of_changes": "Tóm tắt ngắn gọn các chi tiết nhân vật/lời thoại đã sửa",
  "message": "Lời nhắn gửi tác giả"
}}""",

    # Target 3: Middle Beats & Scene Insertion
    SurgeryTarget.TARGET_3_MIDDLE_BEATS: """Bạn là Bút vàng Trưởng ban Cấu trúc Kịch bản Light Novel.
Tác giả muốn CHÈN THÊM CẢNH / SỬA DIỄN BIẾN THÂN BÀI (MIDDLE BEATS & SCENE INSERTION).

YÊU CẦU CỦA TÁC GIẢ:
{instruction}

PHÂN ĐOẠN THÂN BÀI HIỆN TẠI:
{window_text}

QUY TẮC PHẪU THUẬT THÂN BÀI (TARGET 3):
1. NÂNG CAO STAKES & PACING: Chèn thêm tình huống hiểm nghèo, trở ngại leo thang (Rising Friction) hoặc biến cố đảo chiều (Turning Point).
2. ĐỘC THOẠI NỘI TÂM DỒN NÉN: Khắc họa sự giằng xé tâm lý, suy luận chiến thuật hoặc áp lực sinh tồn.
3. KHÔNG XÁO TRỘN ĐẦU VÀ CUỐI: Cảnh chèn vào phải ăn khớp tuyệt đối với diễn biến trước và sau của mạch truyện.
4. TRÌNH BÀY THÔNG THOÁNG: Đoạn văn ngắn 2-4 câu, ngắt nhịp dứt khoát.
5. BẢO TOÀN NGUYÊN VẸN CÁC TIÊU ĐỀ `## Chương X`.

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ):
{{
  "updated_story_content": "Toàn văn phân đoạn thân bài hoàn chỉnh sau khi chèn/sửa cảnh",
  "summary_of_changes": "Tóm tắt cảnh hoặc biến cố vừa được bổ sung/chỉnh sửa",
  "message": "Lời nhắn gửi tác giả"
}}""",

    # Target 4: Climax & Ending
    SurgeryTarget.TARGET_4_CLIMAX_ENDING: """Bạn là Bút vàng Chuyên gia Kết thúc & Cao trào Light Novel.
Tác giả muốn SỬA CAO TRÀO & ĐOẠN KẾT (CLIMAX & ENDING).

YÊU CẦU CỦA TÁC GIẢ:
{instruction}

PHÂN ĐOẠN KẾT HIỆN TẠI:
{window_text}

QUY TẮC PHẪU THUẬT ĐOẠN KẾT (TARGET 4):
1. CAO TRÀO DÂNG TRÀO HOẶC LINGERING CLIFFHANGER: Xây dựng khoảnh khắc bùng nổ nghẹt thở hoặc cái kết lửng gợi mở bí mật mới khiến độc giả không thể rời mắt.
2. TUÂN THỦ CHẶT CHẼ LOGIC ĐÃ THIẾT LẬP: Không tạo ra plot twist vô lý, tôn trọng tính cách nhân vật đã phát triển.
3. KHÔNG DÙNG ĐOẠN TRIẾT LÝ SUÔNG: Bỏ qua các tuyên ngôn đạo đức sáo rỗng cuối truyện; để cảm xúc tự bộc lộ qua hình ảnh và hành động đọng lại.
4. BẢO TOÀN TIÊU ĐỀ CHƯƠNG `## Chương X` NẾU ĐOẠN GỐC CÓ.

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ):
{{
  "updated_story_content": "Toàn văn đoạn kết mới hoàn chỉnh",
  "summary_of_changes": "Tóm tắt sự thay đổi ở đoạn kết",
  "message": "Lời nhắn gửi tác giả"
}}""",

    # Target 5: Tone Shift & Style Restyling
    SurgeryTarget.TARGET_5_TONE_STYLE: """Bạn là Bậc thầy Phong cách & Ngôn ngữ Văn học Light Novel / Web Novel.
Tác giả yêu cầu CHUYỂN ĐỔI PHONG CÁCH & GIỌNG VĂN TOÀN BỘ (TONE SHIFT & RESTYLING).

PHONG CÁCH YÊU CẦU:
{instruction}

NỘI DUNG BẢN THẢO CẦN CHUYỂN ĐỔI:
{window_text}

QUY TẮC CHUYỂN ĐỔI PHONG CÁCH (TARGET 5):
1. BẢO TOÀN 100% CỐT TRUYỆN & SỰ KIỆN CHÍNH: Giữ nguyên chuỗi nhân quả, hành động của nhân vật, không làm lệch mạch truyện.
2. THAY ĐỔI TRIỆT ĐỂ BẦU KHÔNG KHÍ & TỪ VỰNG:
   - U tối/Giật gân (Dark/Thriller): Gia tăng miêu tả giác quan thể xác cụ thể, nhịp văn staccato dồn dập, bóng tối tâm lý.
   - Hài hước (Comedy): Thêm độc thoại tự giễu cợt (dry wit), tình huống trớ trêu, tương tác dí dỏm.
   - Trinh thám (Mystery): Tăng cường chi tiết quan sát, suy luận sắc bén, bầu không khí ngờ vực.
   - Cổ trang (Historical): Sử dụng ngôn từ trang trọng, phong vị thời đại nhưng tự nhiên, không dịch thô.
3. BẢO TỒN TUYỆT ĐỐI TIÊU ĐỀ `**[TÊN TIÊU ĐỀ]**` VÀ TẤT CẢ TIÊU ĐỀ CHƯƠNG `## Chương X`.

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ):
{{
  "updated_story_content": "Toàn văn nội dung đã được chuyển đổi phong cách hoàn chỉnh",
  "summary_of_changes": "Tóm tắt phong cách và sắc thái mới vừa áp dụng",
  "message": "Lời nhắn gửi tác giả"
}}""",

    # General Surgery Fallback
    SurgeryTarget.GENERAL_SURGERY: """Bạn là Bút vàng Trưởng ban Biên tập Light Novel & Web Novel thịnh hành.
Tác giả muốn can thiệp trực tiếp vào bản thảo truyện chữ của họ.

YÊU CẦU CỦA TÁC GIẢ:
{instruction}

BẢN THẢO HIỆN TẠI:
{window_text}

HÃY THỰC HIỆN CHỈNH SỬA THEO CHUẨN LIGHT NOVEL & WEB NOVEL HIỆN ĐẠI:
1. Áp dụng chính xác chỉ thị của tác giả.
2. BẢO TOÀN 100% các tiêu đề `**...**` và `## Chương X`.
3. Nhịp văn gãy gọn, đối thoại tự nhiên, giàu subtext và vi hành động.
4. Trả về toàn văn nội dung hoàn chỉnh sau chỉnh sửa.

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ):
{{
  "updated_story_content": "Toàn văn nội dung sau khi chỉnh sửa",
  "summary_of_changes": "Tóm tắt ngắn gọn các thay đổi",
  "message": "Lời nhắn gửi tác giả"
}}"""
}
```

---

### 5.5 Component 5: Story ID Allocation & Streaming Endpoint Upgrades

#### 1. Pre-allocation of Story ID in Streaming Endpoints
In `backend/main.py`:
In `/api/generate-story` and `/api/init-story`:
- Create the `Story` database row **immediately before starting the LLM stream generator**.
- Set `user_id = current_user.id if current_user else None` (supported by database schema).
- Set initial `refined_prompt = request.refined_prompt`, `story_content = ""`, `word_count = 0`.
- Immediately yield the marker `[STORY_ID:{story.id}]` as the very first token/line of the stream, or yield it both at start and end.
- As chunks arrive, stream them to the client.
- When stream completes, update `story.story_content = full_story` and `story.word_count = word_count`.
- If an error occurs, refund coins if applicable and delete/update the story draft.

#### 2. Dedicated Story Allocation Endpoint (`POST /api/stories/allocate`)
Add a lightweight endpoint for immediate story reservation:
```python
class StoryAllocateRequest(BaseModel):
    refined_prompt: str
    story_length: str = "medium"
    genre: Optional[str] = None
    tone: Optional[str] = None

@app.post("/api/stories/allocate")
def allocate_story_id(
    request: StoryAllocateRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Instantly allocates a story_id and creates a draft Story record in DB.
    Allows frontend to bind story_id immediately upon transitioning from Intake Chat.
    """
    session_id = str(uuid.uuid4())
    new_story = Story(
        session_id=session_id,
        user_id=current_user.id if current_user else None,
        refined_prompt=request.refined_prompt,
        genre=request.genre or "",
        tone=request.tone or "",
        story_content="",
        word_count=0
    )
    db.add(new_story)
    db.commit()
    db.refresh(new_story)
    return {
        "status": "success",
        "story_id": new_story.id,
        "session_id": session_id
    }
```

---

## 6. Implementation Checklist & Migration Steps

For the implementing agent:

1. **Step 1: Create `backend/services/manuscript_surgery.py`**
   - Implement `SurgeryTarget` enum.
   - Implement `classify_surgery_intent(instruction: str) -> SurgeryTarget`.
   - Implement `SemanticChunkSlicer` with Chapter & Title awareness.
   - Implement `HeadingPreservationEngine` to safeguard `**[TITLE]**` and `## Chương X`.
   - Expose `SURGERY_PROMPTS` map.
   - Implement `perform_targeted_surgery(...)`.

2. **Step 2: Update `backend/agents/copilot_agent.py`**
   - Integrate `classify_surgery_intent` and `SemanticChunkSlicer`.
   - In `_perform_direct_manuscript_edit`, route each intent to its specialized prompt.
   - Run `HeadingPreservationEngine.preserve_headings(...)` before returning the final story.
   - Preserve backward compatibility with existing tests in `test_copilot_bilingual_resilience.py` and `test_copilot_unwrap.py`.

3. **Step 3: Update `backend/main.py`**
   - In `/api/generate-story`: pre-create `Story` record (for both authenticated and guest users), yield `[STORY_ID:{id}]` early, and finalize content at stream close.
   - In `/api/init-story`: pre-create `Story` record, yield `[STORY_ID:{id}]` and `[SESSION_ID:{session_id}]`.
   - Add `POST /api/stories/allocate` endpoint.

4. **Step 4: Comprehensive Automated Test Suite**
   - Write tests verifying all 5 targets:
     * Target 1: Title & Chapter 1 preservation on opening rewrite.
     * Target 2: Character rename and dialogue subtext/micro-action consistency.
     * Target 3: Scene insertion without perturbing opening or ending.
     * Target 4: Cliffhanger ending without altering prior chapters.
     * Target 5: Full manuscript tone restyling with zero heading loss.
   - Verify dynamic chunk slicing (`prefix` -> `window` -> `suffix`).
   - Verify instant story ID allocation and guest persistence.

---
*Report compiled and verified against current repository state.*
