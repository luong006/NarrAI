import os
import sys
import json
import re

try:
    from services.ontology import (
        NarrativeMode,
        HistoricalGroundingGatekeeper,
        auto_detect_narrative_mode
    )
except ImportError:
    try:
        from backend.services.ontology import (
            NarrativeMode,
            HistoricalGroundingGatekeeper,
            auto_detect_narrative_mode
        )
    except ImportError:
        NarrativeMode = None
        HistoricalGroundingGatekeeper = None
        auto_detect_narrative_mode = None

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def safe_log(msg: str):
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode("ascii", "backslashreplace").decode("ascii"))
        except Exception:
            pass

def unwrap_story_prose(text: str) -> str:
    """Multi-pass unwraps stringified JSON, nested envelopes, and markdown codeblocks to guarantee pure story prose."""
    if not text:
        return ""
    current = str(text).strip()

    candidate_keys = [
        "updated_story_content",
        "story_content",
        "story",
        "content",
        "new_story_content",
        "revised_text",
        "text"
    ]

    for _ in range(10):
        prev = current
        # 1. Strip markdown code blocks (```json ... ``` or ```markdown ... ``` or ``` ... ```)
        current = re.sub(r'^```(?:json|markdown)?\s*\n?', '', current, flags=re.IGNORECASE).strip()
        current = re.sub(r'\n?```\s*$', '', current).strip()

        # If wrapped inside ```json\n{...}\n``` within a larger string
        code_fence_match = re.search(r'```(?:json|markdown)?\s*\n?(.*?)\n?```', current, re.DOTALL | re.IGNORECASE)
        if code_fence_match:
            fence_inner = code_fence_match.group(1).strip()
            if any(f'"{k}"' in fence_inner for k in candidate_keys) or '"action_params"' in fence_inner:
                current = fence_inner

        # 2. Check if current is JSON-like
        is_json_candidate = (
            (current.startswith('{') and current.endswith('}'))
            or (current.startswith('"{') and current.endswith('}"'))
            or any(f'"{k}"' in current for k in candidate_keys)
            or '"action_params"' in current
        )

        if is_json_candidate:
            extracted_val = None
            try:
                parsed = json.loads(current, strict=False)
                if isinstance(parsed, str):
                    extracted_val = parsed
                elif isinstance(parsed, dict):
                    # Check candidate keys in root
                    for k in candidate_keys:
                        val = parsed.get(k)
                        if val and isinstance(val, (str, dict)):
                            extracted_val = val
                            break
                    # If not found in root, check inside action_params
                    if not extracted_val and isinstance(parsed.get("action_params"), dict):
                        sub = parsed["action_params"]
                        for k in candidate_keys:
                            val = sub.get(k)
                            if val and isinstance(val, (str, dict)):
                                extracted_val = val
                                break
                    # If still not found, check if there's a single key containing long text
                    if not extracted_val:
                        for k, v in parsed.items():
                            if isinstance(v, str) and len(v) > 30 and k not in ("thought", "action", "message", "summary_of_changes"):
                                extracted_val = v
                                break
            except Exception:
                # Robust regex fallback for dialogue with quotes, escaped characters, and truncated streams
                match = re.search(
                    r'"updated_story_content"\s*:\s*"([\s\S]*?)(?:",\s*"(?:summary_of_changes|message|action|instruction)"\s*:|"\s*\}\s*[\}\]]?\s*|"?\s*$)',
                    current
                )
                if match and match.group(1):
                    extracted_val = match.group(1)
                else:
                    for k in candidate_keys:
                        pattern = r'"' + re.escape(k) + r'"\s*:\s*"([\s\S]*?)(?:",\s*"[a-zA-Z0-9_]+"\s*:|"\s*\}\s*[\}\]]?\s*|"?\s*$)'
                        m = re.search(pattern, current)
                        if m and m.group(1):
                            extracted_val = m.group(1)
                            break

            if extracted_val is not None:
                if isinstance(extracted_val, dict):
                    current = json.dumps(extracted_val, ensure_ascii=False)
                else:
                    current = str(extracted_val).strip()

        if current == prev:
            break

    # 3. Unconditionally unescape escaped sequences once the prose is isolated
    for _ in range(3):
        if "\\n" in current or "\\r" in current or '\\"' in current or "\\\\" in current:
            current = (
                current.replace('\\r\\n', '\n')
                .replace('\\n', '\n')
                .replace('\\r', '')
                .replace('\\"', '"')
                .replace('\\\\', '\\')
            )
        else:
            break

    # Normalize newlines
    current = current.replace('\r\n', '\n').replace('\r', '\n')
    current = re.sub(r'\n{3,}', '\n\n', current)

    return current.strip()

from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

COPILOT_SYSTEM_PROMPT = """Bạn là TỔNG CHỈ HUY (Master Controller / AI Co-pilot) kiêm Biên tập viên trưởng của hệ thống sáng tác NarrAI.
Nhiệm vụ của bạn là giám sát, điều phối và ĐẶC BIỆT LÀ TRỰC TIẾP CAN THIỆP CHỈNH SỬA BẢN THẢO TRUYỆN CHỮ theo lệnh của tác giả.

CÁC NĂNG LỰC VÀ HÀNH ĐỘNG CỦA BẠN:

1. `edit_story_direct` (CAN THIỆP TRỰC TIẾP VÀO BẢN THẢO TRUYỆN CHỮ):
   KÍCH HOẠT KHI: Người dùng yêu cầu thay đổi, viết lại hoặc can thiệp vào nội dung truyện hiện có.
   Ví dụ:
   - "tạo phần mở đầu khác đi", "viết lại đoạn mở đầu kịch tính hơn"
   - "sửa lại đoạn kết bất ngờ hơn", "thay đổi cái kết"
   - "đổi tên nhân vật X thành Y và sửa các câu thoại liên quan"
   - "viết thêm một đoạn miêu tả cơn mưa và tâm trạng ở giữa truyện"
   - "viết lại toàn bộ theo phong cách u tối, giật gân"
   KHI CHỌN HÀNH ĐỘNG NÀY:
   - Bạn PHẢI trả về toàn bộ văn bản truyện mới đã được chỉnh sửa tại `updated_story_content`.
   - Giữ nguyên các phần không liên quan của câu chuyện một cách mượt mà và tự nhiên.
   - Trình bày tóm tắt việc chỉnh sửa tại `summary_of_changes` và thông báo cho người dùng tại `message`.

2. `command_writer` (VIẾT TIẾP CHƯƠNG MỚI / NỐI DÀI TRUYỆN):
   KÍCH HOẠT KHI: Người dùng muốn phát triển tiếp diễn biến tiếp theo ở cuối truyện.

3. `reply_user` (TƯ VẤN / TRÒ CHUYỆN SÁNG TÁC):
   KÍCH HOẠT KHI: Người dùng chỉ hỏi ý kiến, xin gợi ý ý tưởng, hỏi về nhân vật mà KHÔNG yêu cầu sửa trực tiếp vào văn bản truyện.

CẤU TRÚC JSON PHẢI TRẢ VỀ (CHỈ JSON, KHÔNG CÓ MARKDOWN HAY CHỮ THỪA):
{
  "thought": "Phân tích ý định của tác giả và kế hoạch chỉnh sửa văn bản hoặc phản hồi.",
  "action": "edit_story_direct" | "command_writer" | "reply_user" | "reject_and_rewrite" | "heal_image",
  "action_params": {
    "message": "Tin nhắn gửi tác giả giải thích bạn đã làm gì hoặc lời tư vấn.",
    "updated_story_content": "(BẮT BUỘC nếu action=edit_story_direct) Toàn bộ nội dung truyện chữ hoàn chỉnh sau khi đã áp dụng chỉnh sửa.",
    "summary_of_changes": "(BẮT BUỘC nếu action=edit_story_direct) Tóm tắt ngắn gọn những gì đã thay đổi trong bản thảo.",
    "instruction": "(Nếu action=command_writer) Lệnh cụ thể viết tiếp chương mới."
  }
}
"""

from enum import Enum
from collections import namedtuple
from typing import Tuple, List, Optional, Dict, Any

ChunkSlice = namedtuple("ChunkSlice", ["prefix", "window_to_edit", "suffix"])

class SurgeryTarget(str, Enum):
    TARGET_1_OPENING = "opening_hook"
    TARGET_2_CHARACTER_DIALOGUE = "character_dialogue"
    TARGET_3_MIDDLE_BEATS = "middle_beats"
    TARGET_4_CLIMAX_ENDING = "climax_ending"
    TARGET_5_TONE_STYLE = "tone_style"
    GENERAL_SURGERY = "general_surgery"

    def __eq__(self, other):
        if hasattr(other, "value"):
            return self.value == other.value or self.name == getattr(other, "name", None)
        if isinstance(other, str):
            return self.value == other or self.name == other
        return super().__eq__(other)

    def __hash__(self):
        return hash(self.value)

# Direct module-level aliases
TARGET_1_OPENING = SurgeryTarget.TARGET_1_OPENING
TARGET_2_CHARACTER_DIALOGUE = SurgeryTarget.TARGET_2_CHARACTER_DIALOGUE
TARGET_3_MIDDLE_BEATS = SurgeryTarget.TARGET_3_MIDDLE_BEATS
TARGET_4_CLIMAX_ENDING = SurgeryTarget.TARGET_4_CLIMAX_ENDING
TARGET_5_TONE_STYLE = SurgeryTarget.TARGET_5_TONE_STYLE
GENERAL_SURGERY = SurgeryTarget.GENERAL_SURGERY


def classify_surgery_intent(instruction: str) -> SurgeryTarget:
    """
    Classifies bilingual instructions into one of the 5 surgery targets or general surgery.
    Evaluates specific verbs, nouns, and intent indicators in both Vietnamese and English.
    """
    if not instruction:
        return SurgeryTarget.GENERAL_SURGERY
    text = instruction.lower().strip()

    # 1. Target 1: Opening / Hook Rewrite
    t1_patterns = [
        r"mở đầu", r"đoạn mở", r"mở bài", r"khởi đầu", r"cảnh đầu",
        r"opening", r"intro", r"hook", r"beginning", r"prologue",
        r"write a completely different opening"
    ]
    if any(re.search(p, text) for p in t1_patterns):
        return SurgeryTarget.TARGET_1_OPENING

    # 2. Target 4: Climax & Ending
    t4_patterns = [
        r"kết thúc", r"đoạn kết", r"cái kết", r"kết bài", r"hạ màn", r"vĩ thanh",
        r"cao trào", r"ending", r"outro", r"conclusion", r"cliffhanger", r"climax",
        r"make the ending much more dramatic"
    ]
    if any(re.search(p, text) for p in t4_patterns):
        return SurgeryTarget.TARGET_4_CLIMAX_ENDING

    # 3. Target 3: Middle Beats & Scene Insertion
    t3_patterns = [
        r"thân bài", r"ở giữa", r"đoạn giữa", r"giữa truyện", r"thêm cảnh",
        r"chèn cảnh", r"thêm đoạn", r"chèn đoạn", r"tăng kịch tính",
        r"đẩy nhanh nhịp", r"nhịp độ", r"biến cố", r"va chạm", r"tình huống mới",
        r"middle", r"middle beats", r"scene insertion", r"insert scene", r"add scene",
        r"pacing", r"stakes", r"turning point"
    ]
    if any(re.search(p, text) for p in t3_patterns):
        return SurgeryTarget.TARGET_3_MIDDLE_BEATS

    # 4. Target 5: Tone Shift & Style Restyling
    t5_patterns = [
        r"phong cách", r"giọng văn", r"đổi giọng", r"đổi phong cách",
        r"u tối", r"giật gân", r"hài hước", r"kinh dị", r"trinh thám",
        r"cổ trang", r"lãng mạn", r"hồi hộp", r"tone", r"style", r"restyling",
        r"darker", r"thriller", r"comedy", r"mystery", r"historical", r"gripping",
        r"rewrite in a darker"
    ]
    if any(re.search(p, text) for p in t5_patterns):
        return SurgeryTarget.TARGET_5_TONE_STYLE

    # 5. Target 2: Character & Dialogue Surgery
    t2_patterns = [
        r"nhân vật", r"đổi tên", r"thay tên", r"lời thoại", r"đối thoại",
        r"xưng hô", r"tính cách", r"khẩu ngữ", r"subtext", r"tâm lý",
        r"character", r"characters", r"dialogue", r"dialogues", r"rename",
        r"pronoun", r"pronouns", r"add deeper internal thoughts", r"internal thought"
    ]
    if any(re.search(p, text) for p in t2_patterns):
        return SurgeryTarget.TARGET_2_CHARACTER_DIALOGUE

    return SurgeryTarget.GENERAL_SURGERY


class HeadingPreservationEngine:
    @staticmethod
    def preserve_headings(
        original_story: str,
        window_text: str,
        revised_window: str,
        target: SurgeryTarget = SurgeryTarget.GENERAL_SURGERY
    ) -> str:
        """
        Guarantees 100% preservation of **[TITLE]** and ## Chương X across all surgery targets.
        """
        if not revised_window:
            return revised_window

        cleaned = revised_window.strip()

        # 1. Title Preservation (**[TITLE]** or **TITLE**)
        title_pattern = r'^\s*(\*\*(?:\[[^\]\n]+\]|[^\*\n]+)\*\*)\s*'
        orig_title_m = re.search(title_pattern, original_story) if original_story else None
        win_title_m = re.search(title_pattern, window_text) if window_text else None
        target_title = win_title_m or orig_title_m

        if target_title:
            title_str = target_title.group(1).strip()
            # If cleaned does not already start with a markdown bold title
            if not cleaned.startswith("**"):
                orig_starts = original_story.strip().startswith(title_str) if original_story else False
                win_starts = window_text.strip().startswith(title_str) if window_text else False
                if orig_starts and (win_starts or target in (SurgeryTarget.TARGET_1_OPENING, SurgeryTarget.GENERAL_SURGERY)):
                    cleaned = f"{title_str}\n\n{cleaned}"

        # 2. Section Header Preservation (e.g. ## Mở đầu, Phần mở đầu) for Target 1
        if target == SurgeryTarget.TARGET_1_OPENING and window_text:
            header_match = re.search(r'(#{1,3}\s*Mở\s*đầu[^\n]*|Phần\s+mở\s+đầu[^\n]*)', window_text, re.IGNORECASE)
            if header_match:
                header_tag = header_match.group(1).strip()
                if not re.search(r'(#{1,3}\s*Mở\s*đầu|Phần\s+mở\s+đầu)', cleaned, re.IGNORECASE):
                    if cleaned.startswith("**"):
                        parts_cs = cleaned.split("\n\n", 1)
                        if len(parts_cs) == 2:
                            cleaned = f"{parts_cs[0]}\n\n{header_tag}\n\n{parts_cs[1]}"
                        else:
                            cleaned = f"{cleaned}\n\n{header_tag}"
                    else:
                        cleaned = f"{header_tag}\n\n{cleaned}"

        # 3. Chapter Heading Preservation (## Chương X: [Tên chương], ### Chương Cuối: Hồi Kết, etc.)
        if window_text:
            heading_re = re.compile(r'(#{1,3}\s+(?:Chương|Hồi|Tiết|Phần|Chapter)[^\n]*)', re.IGNORECASE)
            orig_ch_matches = list(heading_re.finditer(window_text))

            if orig_ch_matches:
                raw_paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]

                has_title = False
                title_p = None
                content_paragraphs = raw_paragraphs
                if raw_paragraphs and re.match(r'^\s*\*\*[^\*\n]+\*\*\s*$', raw_paragraphs[0]):
                    has_title = True
                    title_p = raw_paragraphs[0]
                    content_paragraphs = raw_paragraphs[1:]

                canon_headings = []
                for m in orig_ch_matches:
                    h_text = m.group(1).strip()
                    num_m = re.search(r'(?:Chương|Chapter|Hồi|Tiết|Phần)\s+([^\n:\-]+)', h_text, re.IGNORECASE)
                    ch_num = num_m.group(1).strip() if num_m else ""
                    
                    post_text = window_text[m.end():m.end() + 200].strip()
                    anchor = ""
                    for line in post_text.split("\n"):
                        s_line = line.strip()
                        if s_line and not s_line.startswith("#"):
                            anchor = s_line[:60]
                            break

                    canon_headings.append({
                        "heading": h_text,
                        "ch_num": ch_num,
                        "anchor": anchor,
                        "orig_start": m.start()
                    })

                def heading_matches_para(h_item, p_text):
                    if p_text.startswith(h_item["heading"]):
                        return True
                    if h_item["ch_num"]:
                        if re.match(rf'^\s*#{1,3}\s+(?:Chương|Chapter|Hồi|Tiết|Phần)\s+{re.escape(h_item["ch_num"])}\b', p_text, re.IGNORECASE):
                            return True
                    return False

                existing_indices = {}
                for c_idx, h_item in enumerate(canon_headings):
                    for p_idx, p_text in enumerate(content_paragraphs):
                        if heading_matches_para(h_item, p_text):
                            existing_indices[c_idx] = p_idx
                            break

                if len(existing_indices) < len(canon_headings):
                    refined_paragraphs = []
                    for p in content_paragraphs:
                        m_head = heading_re.match(p)
                        if m_head:
                            head_line = m_head.group(1).strip()
                            rest = p[m_head.end():].strip()
                            refined_paragraphs.append(head_line)
                            if rest:
                                refined_paragraphs.append(rest)
                        else:
                            refined_paragraphs.append(p)

                    existing_map = {}
                    for c_idx, h_item in enumerate(canon_headings):
                        for p_idx, p_text in enumerate(refined_paragraphs):
                            if heading_matches_para(h_item, p_text):
                                existing_map[c_idx] = p_idx
                                break

                    if not existing_map:
                        N = len(canon_headings)
                        P = len(refined_paragraphs)
                        result_paragraphs = []
                        heading_idx = 0
                        for p_idx, p_text in enumerate(refined_paragraphs):
                            while heading_idx < N:
                                target_p = round(heading_idx * P / N)
                                if target_p <= p_idx or p_idx == P - 1:
                                    result_paragraphs.append(canon_headings[heading_idx]["heading"])
                                    heading_idx += 1
                                    if target_p > p_idx:
                                        break
                                else:
                                    break
                            result_paragraphs.append(p_text)
                        while heading_idx < N:
                            result_paragraphs.append(canon_headings[heading_idx]["heading"])
                            heading_idx += 1
                        refined_paragraphs = result_paragraphs
                    else:
                        for c_idx, h_item in enumerate(canon_headings):
                            if c_idx in existing_map:
                                continue

                            prev_c_indices = [ci for ci in existing_map if ci < c_idx]
                            next_c_indices = [ci for ci in existing_map if ci > c_idx]

                            min_p_idx = (existing_map[max(prev_c_indices)] + 1) if prev_c_indices else 0
                            max_p_idx = existing_map[min(next_c_indices)] if next_c_indices else len(refined_paragraphs)

                            inserted = False
                            if h_item["anchor"] and len(h_item["anchor"]) >= 15:
                                for p_i in range(min_p_idx, max_p_idx):
                                    if h_item["anchor"] in refined_paragraphs[p_i] and not heading_re.match(refined_paragraphs[p_i]):
                                        refined_paragraphs.insert(p_i, h_item["heading"])
                                        inserted_idx = p_i
                                        inserted = True
                                        break

                            if not inserted:
                                prose_indices = [
                                    pi for pi in range(min_p_idx, max_p_idx)
                                    if not heading_re.match(refined_paragraphs[pi])
                                ]
                                if not prose_indices:
                                    target_idx = max_p_idx
                                elif len(prose_indices) == 1:
                                    target_idx = prose_indices[0] if not prev_c_indices else max_p_idx
                                else:
                                    interval_missing = [
                                        ci for ci in range(
                                            (max(prev_c_indices) + 1) if prev_c_indices else 0,
                                            min(next_c_indices) if next_c_indices else len(canon_headings)
                                        )
                                        if ci not in existing_map
                                    ]
                                    rank = interval_missing.index(c_idx)
                                    num_missing = len(interval_missing)
                                    prose_pick = round((rank + 1) * len(prose_indices) / (num_missing + 1))
                                    prose_pick = max(1 if prev_c_indices else 0, min(len(prose_indices) - 1, prose_pick))
                                    target_idx = prose_indices[prose_pick]

                                refined_paragraphs.insert(target_idx, h_item["heading"])
                                inserted_idx = target_idx

                            for k in list(existing_map.keys()):
                                if existing_map[k] >= inserted_idx:
                                    existing_map[k] += 1
                            existing_map[c_idx] = inserted_idx

                    content_paragraphs = refined_paragraphs

                if has_title:
                    cleaned = title_p + "\n\n" + "\n\n".join(content_paragraphs)
                else:
                    cleaned = "\n\n".join(content_paragraphs)

        return cleaned


class SemanticChunkSlicer:
    MAX_WINDOW_CHARS = 8000

    @classmethod
    def slice_manuscript(
        cls,
        story: str,
        target: Any = SurgeryTarget.GENERAL_SURGERY,
        instruction: str = "",
        selected_text: str = "",
        cursor_position: Optional[int] = None
    ) -> ChunkSlice:
        """
        Dynamically slices manuscript into prefix, window_to_edit, and suffix
        respecting chapter markers (## Chương X) and semantic paragraph boundaries.
        Guarantees: when untouched, prefix + window_to_edit + suffix == story.
        Returns ChunkSlice(prefix, window_to_edit, suffix).
        """
        if not story:
            return ChunkSlice("", "", "")

        # Priority 1: Explicit selected_text from frontend
        if selected_text and selected_text.strip():
            clean_sel = selected_text.strip()
            idx = -1
            if cursor_position is not None and 0 <= cursor_position <= len(story):
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

        # Priority 2: Chapter Targeting extracted from instruction (e.g. "sửa Chương 3", "chương 2", "edit chapter 4")
        if instruction:
            ch_target_m = re.search(
                r'(?:sửa|chỉnh\s*sửa|viết\s*lại|thay\s*đổi|làm\s*lại|edit|rewrite|update)?\s*(?:chương|chapter|hồi|tiết|phần)\s*(\d+)',
                instruction,
                re.IGNORECASE
            )
            if ch_target_m:
                target_ch_num = int(ch_target_m.group(1))
                ch_matches = list(re.finditer(
                    r'(?:^|\n)(#{1,3}\s+(?:chương|chapter|hồi|tiết|phần)\s*(\d+)[^\n]*)',
                    story,
                    re.IGNORECASE
                ))
                for i, match in enumerate(ch_matches):
                    try:
                        matched_num = int(match.group(2))
                    except (ValueError, TypeError):
                        continue
                    if matched_num == target_ch_num:
                        start_pos = match.start() + (1 if story[match.start()] == '\n' else 0)
                        prefix_text = story[:start_pos]
                        if prefix_text and not prefix_text.endswith("\n\n"):
                            prefix_text = prefix_text.rstrip() + "\n\n"

                        if i + 1 < len(ch_matches):
                            next_start = ch_matches[i + 1].start() + (1 if story[ch_matches[i + 1].start()] == '\n' else 0)
                            window_text = story[start_pos:next_start].strip()
                            suffix_text = story[next_start:]
                            if suffix_text and not suffix_text.startswith("\n\n"):
                                suffix_text = "\n\n" + suffix_text.lstrip()
                        else:
                            window_text = story[start_pos:].strip()
                            suffix_text = ""

                        return ChunkSlice(prefix_text, window_text, suffix_text)

        # Priority 3: Fallback to existing semantic chunking targets

        # 1. Target 1: Opening / Hook Rewrite
        if target == SurgeryTarget.TARGET_1_OPENING:
            ch_matches = list(re.finditer(r'\n+(?=#{1,3}\s+(?:chương|hồi|tiết|phần|chapter)\s*(?:[2-9]|\d{2,})\b)', story, re.IGNORECASE))
            if ch_matches:
                split_idx = ch_matches[0].start()
                if 10 <= split_idx <= cls.MAX_WINDOW_CHARS:
                    return ChunkSlice("", story[:split_idx], story[split_idx:])

            if len(story) > cls.MAX_WINDOW_CHARS:
                cut_idx = cls.MAX_WINDOW_CHARS
                last_p = story[:cut_idx].rfind("\n\n")
                if last_p > 1000:
                    cut_idx = last_p + 2
                return ChunkSlice("", story[:cut_idx], story[cut_idx:])

            paras = [p.strip() for p in story.split("\n\n") if p.strip()]
            if len(paras) >= 4:
                start_offset = 1 if paras[0].startswith("**") else 0
                n_paras = start_offset + min(3, max(1, len(paras) - start_offset - 1))
                curr_pos = 0
                for _ in range(n_paras):
                    next_break = story.find("\n\n", curr_pos)
                    if next_break != -1:
                        curr_pos = next_break + 2
                    else:
                        break
                return ChunkSlice("", story[:curr_pos], story[curr_pos:])

            return ChunkSlice("", story, "")

        # 2. Target 4: Climax & Ending
        elif target == SurgeryTarget.TARGET_4_CLIMAX_ENDING:
            ch_matches = list(re.finditer(r'\n+(?=#{1,3}\s+(?:chương|hồi|tiết|phần|chapter)\s+\d+)', story, re.IGNORECASE))
            if ch_matches and len(ch_matches) >= 2:
                last_ch = ch_matches[-1].start()
                return ChunkSlice(story[:last_ch], story[last_ch:], "")

            if len(story) > cls.MAX_WINDOW_CHARS:
                cut_idx = len(story) - cls.MAX_WINDOW_CHARS
                next_p = story[cut_idx:].find("\n\n")
                if next_p != -1:
                    cut_idx = cut_idx + next_p + 2
                return ChunkSlice(story[:cut_idx], story[cut_idx:], "")

            paras = [p.strip() for p in story.split("\n\n") if p.strip()]
            if len(paras) >= 3:
                n_end = min(3, max(1, len(paras) - 2))
                curr_pos = len(story)
                for _ in range(n_end):
                    prev_break = story.rfind("\n\n", 0, curr_pos)
                    if prev_break != -1:
                        curr_pos = prev_break
                    else:
                        break
                split_pos = curr_pos
                return ChunkSlice(story[:split_pos], story[split_pos:], "")

            return ChunkSlice("", story, "")

        # 3. Target 3: Middle Beats & Scene Insertion
        elif target == SurgeryTarget.TARGET_3_MIDDLE_BEATS:
            ch_matches = list(re.finditer(r'\n+(?=#{1,3}\s+(?:chương|hồi|chapter)\s+\d+)', story, re.IGNORECASE))
            if len(ch_matches) >= 3:
                start_win = ch_matches[0].start()
                end_win = ch_matches[-1].start()
                return ChunkSlice(story[:start_win], story[start_win:end_win], story[end_win:])

            if len(story) > cls.MAX_WINDOW_CHARS:
                mid_start = (len(story) - cls.MAX_WINDOW_CHARS) // 2
                p1 = story.find("\n\n", mid_start)
                cut1 = p1 + 2 if p1 != -1 else mid_start
                p2 = story.rfind("\n\n", cut1, min(len(story), cut1 + cls.MAX_WINDOW_CHARS))
                cut2 = p2 if p2 > cut1 else min(len(story), cut1 + cls.MAX_WINDOW_CHARS)
                return ChunkSlice(story[:cut1], story[cut1:cut2], story[cut2:])

            paras = [p.strip() for p in story.split("\n\n") if p.strip()]
            if len(paras) >= 4:
                start_p = max(1, len(paras) // 3)
                end_p = min(len(paras) - 1, start_p + max(2, len(paras) // 3))
                curr_pos = 0
                for _ in range(start_p):
                    nb = story.find("\n\n", curr_pos)
                    if nb != -1:
                        curr_pos = nb + 2
                    else:
                        break
                p_idx1 = curr_pos
                for _ in range(end_p - start_p):
                    nb = story.find("\n\n", curr_pos)
                    if nb != -1:
                        curr_pos = nb + 2
                    else:
                        break
                p_idx2 = curr_pos
                return ChunkSlice(story[:p_idx1], story[p_idx1:p_idx2], story[p_idx2:])

            return ChunkSlice("", story, "")

        # 4. Target 2 & Target 5: Whole story or rolling window
        else:
            if len(story) <= cls.MAX_WINDOW_CHARS:
                return ChunkSlice("", story, "")
            cut_idx = cls.MAX_WINDOW_CHARS
            last_p = story[:cut_idx].rfind("\n\n## ")
            if last_p < 2000:
                last_p = story[:cut_idx].rfind("\n\n")
            if last_p > 2000:
                cut_idx = last_p + 2
            return ChunkSlice("", story[:cut_idx], story[cut_idx:])


DIRECT_EDIT_PROMPT = """Bạn là Bút vàng Trưởng ban Biên tập Light Novel & Web Novel thịnh hành.
Tác giả muốn can thiệp trực tiếp vào bản thảo truyện chữ của họ.

YÊU CẦU CỦA TÁC GIẢ:
{user_instruction}

BẢN THẢO HIỆN TẠI (HOẶC PHÂN ĐOẠN ĐANG ĐƯỢC CHỈ ĐỊNH ĐỂ BIÊN TẬP):
{current_story}

HÃY THỰC HIỆN CHỈNH SỬA TRỰC TIẾP THEO CHUẨN ĐỘNG CƠ LIGHT NOVEL & WEB NOVEL HIỆN ĐẠI (TUYỆT ĐỐI KHÔNG ĐỂ VĂN PHONG BỊ THỤT LÙI VỀ MIÊU TẢ TĨNH):
1. Áp dụng chính xác yêu cầu của tác giả (thay đổi mở đầu, sửa đoạn kết, thêm độc thoại nội tâm, làm sắc bén lời thoại, đẩy nhanh nhịp độ, đổi tên/tính cách nhân vật, đổi phong cách...).
2. ĐẶC BIỆT KHI SỬA PHẦN MỞ ĐẦU (OPENING / INTRO):
   - TUYỆT ĐỐI KHÔNG ĐƯỢC CẮT BỎ, XÓA HOẶC BỎ QUA PHẦN MỞ ĐẦU.
   - BẮT BUỘC PHẢI VIẾT LẠI MỘT PHẦN MỞ ĐẦU MỚI HOÀN CHỈNH (2-4 đoạn văn xuôi giàu cảm xúc hoặc hành động kịch tính, kết nối tự nhiên với phần sau).
   - NẾU BẢN THẢO GỐC CÓ TIÊU ĐỀ (ví dụ: `**TIÊU ĐỀ**`, `### Mở đầu`, `## Mở đầu`, `Phần mở đầu:` hoặc `## Chương 1:`): BẮT BUỘC PHẢI GIỮ NGUYÊN TIÊU ĐỀ ĐÓ và viết nội dung mở đầu mới ngay dưới tiêu đề.
   - Bắt buộc tạo In Medias Res Hook giật gân ngay câu đầu, ném nhân vật vào tình thế nan giải, 0% tả cảnh thời tiết mây gió dông dài.
3. KHI SỬA ĐỐI THOẠI & NHÂN VẬT (DIALOGUE & CHARACTERS):
   - Đổi tên/tính cách nhân vật theo đúng chỉ thị, cập nhật mọi câu thoại và đại từ xưng hô liên quan một cách nhất quán.
   - Làm câu thoại tự nhiên, gãy gọn, khẩu ngữ giới trẻ hiện đại, giàu subtext (thao túng, che giấu, mỉa mai), đan xen vi hành động và phản ứng sinh lý (siết ngón tay, nuốt khan, nhếch môi).
4. KHI SỬA HOẶC CHÈN BIẾN CỐ THÂN BÀI (MIDDLE BEATS & SCENE INSERTION):
   - Đưa tình huống va chạm, biến cố đảo chiều hoặc đào sâu nội tâm giằng xé vào đúng mạch diễn biến.
   - Bám sát Tight POV, câu văn co giãn staccato, đoạn văn thoáng đãng (2-4 câu/đoạn).
   - Ráp nối mượt mà với phần trước và phần sau, không làm đứt đoạn cốt truyện.
5. KHI SỬA ĐOẠN KẾT (CLIMAX & ENDING):
   - Xây dựng cao trào cảm xúc dâng trào hoặc Lingering Cliffhanger nghẹt thở, gút lại các khúc mắc hợp lý.
6. KHI ĐỔI PHONG CÁCH / GIỌNG VĂN TOÀN TRUYỆN (TONE SHIFT):
   - Chuyển đổi triệt để sắc thái văn phong (u tối, hài hước, hồi hộp, trinh thám...) nhưng bảo toàn 100% các tình tiết cốt lõi và mối quan hệ nhân vật.
7. Ráp nối đoạn chỉnh sửa với phần còn lại của bản thảo một cách hoàn hảo, liền mạch, không để lại vết gãy ngữ nghĩa.
8. Xuất ra TOÀN BỘ nội dung hoàn chỉnh của phần được yêu cầu sau khi đã chỉnh sửa (kèm đầy đủ tiêu đề nếu có).

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ, KHÔNG CÓ MARKDOWN HAY CHỮ THỪA NGOÀI KHỐI JSON):
{{
  "updated_story_content": "Toàn văn nội dung mới hoàn chỉnh sau khi chỉnh sửa",
  "summary_of_changes": "Tóm tắt ngắn gọn 1-2 câu về các chi tiết đã được thay đổi trong bản thảo",
  "message": "Lời nhắn gửi tác giả về sự thay đổi"
}}
"""

SURGERY_PROMPTS = {
    SurgeryTarget.TARGET_1_OPENING: """Bạn là Bút vàng Trưởng ban Biên tập Light Novel & Web Novel.
Tác giả muốn VIẾT LẠI HOÀN TOÀN PHẦN MỞ ĐẦU (OPENING / HOOK) của câu chuyện.

YÊU CẦU CỦA TÁC GIẢ:
{user_instruction}

PHÂN ĐOẠN MỞ ĐẦU HIỆN TẠI:
{current_story}

QUY TẮC PHẪU THUẬT MỞ ĐẦU (TARGET 1):
1. BẮT BUỘC KHỞI ĐẦU IN MEDIAS RES: Ném nhân vật thẳng vào xung đột, tình thế hiểm nghèo hoặc biến cố bùng nổ từ câu đầu tiên.
2. TUYỆT ĐỐI 0% tả cảnh thời tiết, mây trời gió thoảng hay thuyết minh bối cảnh dài dòng ở mở đầu.
3. BẢO TỒN NGUYÊN VẸN TIÊU ĐỀ: Nếu phân đoạn gốc có tiêu đề dạng `**[TÊN TIÊU ĐỀ]**` hoặc `**TIÊU ĐỀ**`, BẮT BUỘC giữ nguyên ở dòng đầu tiên.
4. BẢO TỒN TIÊU ĐỀ CHƯƠNG: Nếu có `## Chương 1: ...` hoặc `### Mở đầu`, hãy giữ nguyên hoặc cập nhật tên chương cho kịch tính.
5. KẾT NỐI LIỀN MẠCH: Đoạn kết của phần mở đầu phải nối khớp hoàn hảo với diễn biến tiếp theo của truyện.
6. ĐỘ DÀI: Viết 2-4 đoạn văn xuôi giàu cảm xúc, điểm nhìn bám sát (Tight POV), nhịp văn staccato nhanh gọn.

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ, KHÔNG CÓ MARKDOWN HAY CHỮ THỪA NGOÀI KHỐI JSON):
{{
  "updated_story_content": "Toàn văn phần mở đầu mới hoàn chỉnh kèm tiêu đề",
  "summary_of_changes": "Tóm tắt ngắn gọn 1-2 câu về những thay đổi trong phần mở đầu",
  "message": "Lời nhắn gửi tác giả về mở đầu mới"
}}""",

    SurgeryTarget.TARGET_2_CHARACTER_DIALOGUE: """Bạn là Chuyên gia Biên kịch & Đối thoại Light Novel & Web Novel.
Tác giả yêu cầu PHẪU THUẬT NHÂN VẬT & LỜI THOẠI (CHARACTER & DIALOGUE SURGERY).

YÊU CẦU CỦA TÁC GIẢ:
{user_instruction}

BẢN THẢO HIỆN TẠI:
{current_story}

QUY TẮC PHẪU THUẬT NHÂN VẬT & THOẠI (TARGET 2):
1. NHẤT QUÁN ĐỔI TÊN & ĐẠI TỪ: Thay đổi tên nhân vật và đại từ xưng hô trên TOÀN BỘ các câu thoại và lời dẫn chuyện một cách triệt để, không để sót tên cũ.
2. ĐỐI THOẠI SẮC BÉN & KHẨU NGỮ HIỆN ĐẠI: Lời thoại tự nhiên, gãy gọn, punchy, mang phong cách giới trẻ đương đại; loại bỏ 100% ngữ điệu dịch thuật sến súa ("ngươi/ta", "chẳng hay").
3. SUBTEXT & VI HÀNH ĐỘNG (MICRO-ACTIONS): Mỗi câu thoại phải chứa ẩn ý (thao túng, che giấu, mỉa mai ngầm) và đan xen vi hành động thực tế (siết chặt đầu ngón tay, khựng lại nửa nhịp, nuốt khan, nhếch mép).
4. GIỮ NGUYÊN BỐI CẢNH & TÌNH TIẾT: Không làm xáo trộn các biến cố đã xảy ra trong cảnh.
5. BẢO TOÀN CÁC TIÊU ĐỀ `**...**` VÀ `## Chương X` NẾU CÓ TRONG ĐOẠN.

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ, KHÔNG CÓ MARKDOWN HAY CHỮ THỪA NGOÀI KHỐI JSON):
{{
  "updated_story_content": "Toàn văn phân đoạn sau khi đã phẫu thuật nhân vật và lời thoại",
  "summary_of_changes": "Tóm tắt ngắn gọn các chi tiết nhân vật/lời thoại đã sửa",
  "message": "Lời nhắn gửi tác giả"
}}""",

    SurgeryTarget.TARGET_3_MIDDLE_BEATS: """Bạn là Bút vàng Trưởng ban Cấu trúc Kịch bản Light Novel.
Tác giả muốn CHÈN THÊM CẢNH / SỬA DIỄN BIẾN THÂN BÀI (MIDDLE BEATS & SCENE INSERTION).

YÊU CẦU CỦA TÁC GIẢ:
{user_instruction}

PHÂN ĐOẠN THÂN BÀI HIỆN TẠI:
{current_story}

QUY TẮC PHẪU THUẬT THÂN BÀI (TARGET 3):
1. NÂNG CAO STAKES & PACING: Chèn thêm tình huống hiểm nghèo, trở ngại leo thang (Rising Friction) hoặc biến cố đảo chiều (Turning Point).
2. ĐỘC THOẠI NỘI TÂM DỒN NÉN: Khắc họa sự giằng xé tâm lý, suy luận chiến thuật hoặc áp lực sinh tồn.
3. KHÔNG XÁO TRỘN ĐẦU VÀ CUỐI: Cảnh chèn vào phải ăn khớp tuyệt đối với diễn biến trước và sau của mạch truyện.
4. TRÌNH BÀY THÔNG THOÁNG: Đoạn văn ngắn 2-4 câu, ngắt nhịp dứt khoát.
5. BẢO TOÀN NGUYÊN VẸN CÁC TIÊU ĐỀ `## Chương X`.

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ, KHÔNG CÓ MARKDOWN HAY CHỮ THỪA NGOÀI KHỐI JSON):
{{
  "updated_story_content": "Toàn văn phân đoạn thân bài hoàn chỉnh sau khi chèn/sửa cảnh",
  "summary_of_changes": "Tóm tắt cảnh hoặc biến cố vừa được bổ sung/chỉnh sửa",
  "message": "Lời nhắn gửi tác giả"
}}""",

    SurgeryTarget.TARGET_4_CLIMAX_ENDING: """Bạn là Bút vàng Chuyên gia Kết thúc & Cao trào Light Novel.
Tác giả muốn SỬA CAO TRÀO & ĐOẠN KẾT (CLIMAX & ENDING).

YÊU CẦU CỦA TÁC GIẢ:
{user_instruction}

PHÂN ĐOẠN KẾT HIỆN TẠI:
{current_story}

QUY TẮC PHẪU THUẬT ĐOẠN KẾT (TARGET 4):
1. CAO TRÀO DÂNG TRÀO HOẶC LINGERING CLIFFHANGER: Xây dựng khoảnh khắc bùng nổ nghẹt thở hoặc cái kết lửng gợi mở bí mật mới khiến độc giả không thể rời mắt.
2. TUÂN THỦ CHẶT CHẼ LOGIC ĐÃ THIẾT LẬP: Không tạo ra plot twist vô lý, tôn trọng tính cách nhân vật đã phát triển.
3. KHÔNG DÙNG ĐOẠN TRIẾT LÝ SUÔNG: Bỏ qua các tuyên ngôn đạo đức sáo rỗng cuối truyện; để cảm xúc tự bộc lộ qua hình ảnh và hành động đọng lại.
4. BẢO TOÀN TIÊU ĐỀ CHƯƠNG `## Chương X` NẾU ĐOẠN GỐC CÓ.

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ, KHÔNG CÓ MARKDOWN HAY CHỮ THỪA NGOÀI KHỐI JSON):
{{
  "updated_story_content": "Toàn văn đoạn kết mới hoàn chỉnh",
  "summary_of_changes": "Tóm tắt sự thay đổi ở đoạn kết",
  "message": "Lời nhắn gửi tác giả"
}}""",

    SurgeryTarget.TARGET_5_TONE_STYLE: """Bạn là Bậc thầy Phong cách & Ngôn ngữ Văn học Light Novel / Web Novel.
Tác giả yêu cầu CHUYỂN ĐỔI PHONG CÁCH & GIỌNG VĂN TOÀN BỘ (TONE SHIFT & RESTYLING).

PHONG CÁCH YÊU CẦU:
{user_instruction}

NỘI DUNG BẢN THẢO CẦN CHUYỂN ĐỔI:
{current_story}

QUY TẮC CHUYỂN ĐỔI PHONG CÁCH (TARGET 5):
1. BẢO TOÀN 100% CỐT TRUYỆN & SỰ KIỆN CHÍNH: Giữ nguyên chuỗi nhân quả, hành động của nhân vật, không làm lệch mạch truyện.
2. THAY ĐỔI TRIỆT ĐỂ BẦU KHÔNG KHÍ & TỪ VỰNG:
   - U tối/Giật gân (Dark/Thriller): Gia tăng miêu tả giác quan thể xác cụ thể, nhịp văn staccato dồn dập, bóng tối tâm lý.
   - Hài hước (Comedy): Thêm độc thoại tự giễu cợt (dry wit), tình huống trớ trêu, tương tác dí dỏm.
   - Trinh thám (Mystery): Tăng cường chi tiết quan sát, suy luận sắc bén, bầu không khí ngờ vực.
   - Cổ trang (Historical): Sử dụng ngôn từ trang trọng, phong vị thời đại nhưng tự nhiên, không dịch thô.
3. BẢO TỒN TUYỆT ĐỐI TIÊU ĐỀ `**[TÊN TIÊU ĐỀ]**` VÀ TẤT CẢ TIÊU ĐỀ CHƯƠNG `## Chương X`.

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ, KHÔNG CÓ MARKDOWN HAY CHỮ THỪA NGOÀI KHỐI JSON):
{{
  "updated_story_content": "Toàn văn nội dung đã được chuyển đổi phong cách hoàn chỉnh",
  "summary_of_changes": "Tóm tắt phong cách và sắc thái mới vừa áp dụng",
  "message": "Lời nhắn gửi tác giả"
}}""",

    SurgeryTarget.GENERAL_SURGERY: DIRECT_EDIT_PROMPT
}


class CopilotAgent:
    MAX_MANUSCRIPT_CHARS = 8000
    MODELS = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

    def __init__(self):
        # Master Controller uses VIP Key or standard key
        api_key = os.environ.get("GROQ_API_KEY_COPILOT") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            try:
                from dotenv import load_dotenv
                env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
                if os.path.exists(env_file):
                    load_dotenv(env_file)
                else:
                    load_dotenv()
                api_key = os.environ.get("GROQ_API_KEY_COPILOT") or os.environ.get("GROQ_API_KEY")
            except Exception:
                pass
        if not api_key:
            api_key = "gsk_test_dummy_key_for_testing"
        self.api_key = api_key
        self.models = list(self.MODELS)
        self._clients = {}
        # Primary client
        self.llm = self._get_client(self.models[0])

    def _get_client(self, model_name: str) -> GroqClient:
        """Lazily creates and pools GroqClient per model."""
        if model_name not in self._clients:
            self._clients[model_name] = GroqClient(model_name=model_name, api_key=self.api_key)
        return self._clients[model_name]

    def _chat_with_fallback(self, messages, temperature: float = 0.3, max_tokens: int = 3000, response_format=None) -> tuple:
        """
        Multi-tier model fallback chain across ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile', 'llama-3.1-8b-instant'].
        Retries secondary/tertiary model if primary encounters rate limit, 5xx, or context error.
        Returns (response_text, used_model_name).
        """
        last_error = None
        candidate_models = list(self.models)
        for client_name in self._clients:
            if client_name not in candidate_models:
                candidate_models.append(client_name)

        for i, model in enumerate(candidate_models):
            try:
                if i == 0 and hasattr(self, "llm") and self.llm:
                    client = self.llm
                else:
                    client = self._get_client(model)

                resp = client.chat(messages, temperature=temperature, max_tokens=max_tokens, response_format=response_format)
                if resp and resp.strip():
                    return resp, getattr(client, "model", model)
            except Exception as e:
                safe_log(f"[Copilot Model Fallback] Model {model} failed: {e}. Retrying next in chain...")
                last_error = e

        raise RuntimeError(f"All models in fallback chain failed: {last_error}")

    @staticmethod
    def _is_english_text(text: str) -> bool:
        """Determines if the text prompt is primarily in English."""
        if not text:
            return False
        vi_chars = set(
            "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
            "ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ"
        )
        if any(c in vi_chars for c in text):
            return False

        en_markers = {
            "the", "a", "an", "is", "are", "rewrite", "make", "write",
            "add", "story", "tone", "character", "in", "to", "for",
            "with", "please", "ending", "opening", "intro", "prose",
            "you", "can", "i", "me", "my", "chapter", "give", "tell", "idea"
        }
        words = re.findall(r'[a-zA-Z]+', text.lower())
        if not words:
            return False
        match_count = sum(1 for w in words if w in en_markers)
        return match_count >= 1 or len(words) >= 3

    def _is_direct_edit_request(self, user_msg: str) -> bool:
        """
        Bilingual heuristic check to identify requests intending to modify the manuscript directly.
        Supports Vietnamese commands, English quick prompts, action verbs, target nouns, and tone descriptors.
        """
        if not user_msg:
            return False
        msg_lower = user_msg.lower().strip()

        # 1. Exact Frontend Quick Prompts (from AICopilotPanel.tsx)
        quick_prompts = [
            "write a completely different opening for this story",
            "make the ending much more dramatic and suspenseful",
            "rewrite in a darker, more gripping thriller tone",
            "add deeper internal thoughts and character dialogues"
        ]
        for qp in quick_prompts:
            if qp in msg_lower:
                return True

        # 2. Exclude conversational non-edit phrases and idioms
        non_edit_idioms = [
            "thay vì", "đổi lại", "thay cho", "bớt giận", "xóa tan",
            "instead of", "rather than", "what if"
        ]
        if any(idiom in msg_lower for idiom in non_edit_idioms):
            return False

        # 3. English Action Verbs, Target Nouns, and Tone Descriptors
        en_verbs = [
            "rewrite", "re-write", "revise", "edit", "redraft",
            "rephrase", "modify", "change", "update", "shorten", "expand"
        ]
        en_nouns = [
            "opening", "intro", "ending", "outro", "conclusion",
            "tone", "style", "dialogue", "dialogues", "pacing",
            "chapter", "manuscript", "prose", "cliffhanger", "thought", "thoughts"
        ]
        en_tones = [
            "darker", "thriller", "gripping", "suspense", "suspenseful", "dramatic", "humorous"
        ]

        has_en_verb = any(re.search(rf'\b{re.escape(v)}\b', msg_lower) for v in en_verbs)
        has_en_noun = any(re.search(rf'\b{re.escape(n)}\b', msg_lower) for n in en_nouns)
        has_en_tone = any(re.search(rf'\b{re.escape(t)}\b', msg_lower) for t in en_tones)

        if has_en_verb and (has_en_noun or has_en_tone or "story" in msg_lower):
            return True

        if has_en_tone and has_en_noun:
            return True

        # 4. Vietnamese Keywords and Action Verbs
        edit_keywords = [
            "mở đầu", "đoạn mở", "mở bài", "đoạn kết", "kết thúc", "kết bài",
            "sửa lại", "thay đổi", "viết lại", "đổi tên", "chỉnh sửa", "thay phần",
            "thay đoạn", "tạo phần", "làm lại", "cắt bỏ", "thêm cảnh", "thêm đoạn",
            "bỏ đoạn", "đổi phong cách", "đổi giọng văn", "tăng kịch tính", "sửa câu",
            "khác đi", "hay hơn", "ngắn lại", "dài ra", "u tối hơn", "hài hước hơn",
            "soạn lại", "viết tiếp", "bản thảo"
        ]
        if any(k in msg_lower for k in edit_keywords):
            return True

        single_word_verbs = ["sửa", "chỉnh", "thay", "đổi", "bớt", "xóa"]
        for verb in single_word_verbs:
            if re.search(rf'(?:\b|^){re.escape(verb)}(?:\b|$)', msg_lower):
                return True

        return False

    def _get_windowed_manuscript(self, user_instruction: str, story: str, selected_text: str = "", cursor_position: Optional[int] = None) -> tuple:
        """
        Enforces intelligent section-targeted sliding window via SemanticChunkSlicer.
        Dynamically slices manuscript into prefix, window_to_edit, and suffix
        respecting chapter markers (## Chương X) and semantic paragraph boundaries.
        Returns (prefix, window_to_edit, suffix).
        """
        if not story:
            return "", "", ""
        target = classify_surgery_intent(user_instruction)
        return SemanticChunkSlicer.slice_manuscript(
            story,
            target,
            user_instruction,
            selected_text=selected_text,
            cursor_position=cursor_position
        )

    def _perform_direct_manuscript_edit(
        self,
        user_instruction: str,
        current_story: str,
        selected_text: str = "",
        cursor_position: Optional[int] = None
    ) -> dict:
        """
        Executes targeted manuscript modification directly on the text with dynamic chunk slicing,
        5 targeted Light Novel prompt templates, and structural heading preservation.
        """
        is_en = self._is_english_text(user_instruction)
        target = classify_surgery_intent(user_instruction)
        prefix, window_text, suffix = self._get_windowed_manuscript(
            user_instruction,
            current_story,
            selected_text=selected_text,
            cursor_position=cursor_position
        )

        prompt_template = SURGERY_PROMPTS.get(target, DIRECT_EDIT_PROMPT)
        prompt = prompt_template.format(
            user_instruction=user_instruction,
            current_story=window_text
        )

        messages = [
            {"role": "system", "content": "Bạn là chuyên gia biên tập truyện. Trả về định dạng JSON hợp lệ duy nhất."},
            {"role": "user", "content": prompt}
        ]

        try:
            resp, used_model = self._chat_with_fallback(messages, temperature=0.4, max_tokens=4000)
            cleaned = re.sub(r'^```(?:json)?\s*\n?', '', resp.strip(), flags=re.IGNORECASE).strip()
            cleaned = re.sub(r'\n?```\s*$', '', cleaned).strip()
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            data = None
            if match:
                try:
                    data = json.loads(match.group(0), strict=False)
                except Exception as parse_err:
                    safe_log(f"[Copilot Direct Edit] json.loads strict=False failed: {parse_err}. Attempting unwrap_story_prose.")

            default_summary = "Updated manuscript according to your instruction." if is_en else "Đã cập nhật bản thảo theo yêu cầu của bạn."
            default_msg = "I have directly modified your manuscript as requested!" if is_en else "Tôi đã chỉnh sửa trực tiếp vào bản thảo của bạn theo yêu cầu!"

            clean_story = None
            summary_of_changes = default_summary
            message_text = default_msg

            if isinstance(data, dict):
                content_candidate = data.get("updated_story_content")
                if not content_candidate and isinstance(data.get("action_params"), dict):
                    content_candidate = data["action_params"].get("updated_story_content")
                if not content_candidate:
                    content_candidate = data.get("story_content") or data.get("content")
                if content_candidate:
                    clean_story = unwrap_story_prose(content_candidate)
                    summary_of_changes = data.get("summary_of_changes", default_summary)
                    message_text = data.get("message", default_msg)

            # Resilient fallback: unwrap directly on match or cleaned
            if not clean_story:
                unwrapped_fallback = unwrap_story_prose(match.group(0) if match else cleaned)
                if unwrapped_fallback and not unwrapped_fallback.startswith("{"):
                    clean_story = unwrapped_fallback

            # Direct prose fallback if LLM returned text instead of JSON
            if not clean_story and cleaned:
                direct_prose = unwrap_story_prose(cleaned)
                if direct_prose and not direct_prose.startswith("{"):
                    clean_story = direct_prose

            if clean_story:
                # Structural Heading Preservation Engine: Zero-loss guarantee for **[TITLE]** and ## Chương X
                clean_story = HeadingPreservationEngine.preserve_headings(
                    original_story=current_story,
                    window_text=window_text,
                    revised_window=clean_story,
                    target=target
                )

                if prefix or suffix:
                    if prefix.endswith("\n") or suffix.startswith("\n") or not prefix or not suffix:
                        parts = [p.strip() for p in [prefix, clean_story, suffix] if p.strip()]
                        final_story = "\n\n".join(parts).strip()
                    else:
                        final_story = f"{prefix}{clean_story}{suffix}".strip()
                else:
                    final_story = clean_story.strip()

                # Post-modification historical validation
                if HistoricalGroundingGatekeeper is not None:
                    detected_mode = NarrativeMode.CHINH_SU
                    if auto_detect_narrative_mode is not None:
                        detected_mode, _ = auto_detect_narrative_mode(final_story)
                    is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                        final_story, mode=detected_mode, user_prompt=user_instruction
                    )
                    if not is_valid:
                        safe_log(f"[Copilot Direct Edit Blocked] Violations: {violations}")
                        rejection_msg = (
                            f"The modification was blocked because it violates Vietnamese historical integrity: {'; '.join(violations)}"
                            if is_en else
                            f"Hệ thống không thể thực hiện chỉnh sửa này vì vi phạm nguyên tắc bảo vệ lịch sử Việt Nam: {'; '.join(violations)}"
                        )
                        return {
                            "thought": f"Historical distortion detected in edited manuscript: {violations}",
                            "action": "reply_user",
                            "action_params": {
                                "message": rejection_msg
                            }
                        }

                target_name = target.value if hasattr(target, "value") else str(target)
                thought_msg = (
                    f"Directly modified manuscript ({used_model}, {target_name}): {user_instruction[:50]}"
                    if is_en else
                    f"Đã thực hiện can thiệp trực tiếp vào bản thảo ({used_model}, {target_name}): {user_instruction[:50]}"
                )

                return {
                    "thought": thought_msg,
                    "action": "edit_story_direct",
                    "action_params": {
                        "updated_story_content": final_story,
                        "summary_of_changes": summary_of_changes,
                        "message": message_text
                    }
                }
        except Exception as e:
            safe_log(f"[Copilot Direct Edit] Error: {e}")
        return None

    def process_event(self, event_type: str, event_data: str, memory: StoryMemory = None) -> dict:
        parsed_payload = {}
        user_message = ""
        current_story = ""
        selected_text = ""
        cursor_position = None

        try:
            parsed_payload = json.loads(event_data) if isinstance(event_data, str) else event_data
            if isinstance(parsed_payload, dict):
                user_message = parsed_payload.get("user_message", "")
                current_story = parsed_payload.get("current_story", "")
                selected_text = parsed_payload.get("selected_text") or parsed_payload.get("selectedText") or ""
                cursor_position = parsed_payload.get("cursor_position") or parsed_payload.get("cursorPosition")
        except Exception:
            user_message = str(event_data)

        if not user_message and isinstance(event_data, str):
            user_message = event_data

        if not current_story and memory:
            current_story = memory.get_short_context(max_chars=6000)

        is_en = self._is_english_text(user_message)

        # 1. Check if user requested direct manuscript intervention (or selected text is provided)
        if self._is_direct_edit_request(user_message) or bool(selected_text.strip()):
            safe_log(f"[Copilot] Detected direct manuscript edit request: {user_message[:40]}")
            if current_story:
                direct_edit_result = self._perform_direct_manuscript_edit(
                    user_message,
                    current_story,
                    selected_text=selected_text,
                    cursor_position=cursor_position
                )
                if direct_edit_result:
                    return direct_edit_result
            else:
                empty_msg = (
                    "I'd be glad to edit! Please ensure you have story content in the editor first."
                    if is_en else
                    "Tôi rất sẵn lòng chỉnh sửa! Hãy đảm bảo bạn đã có nội dung truyện trên màn hình soạn thảo để tôi thực hiện nhé."
                )
                return {
                    "thought": "Direct edit requested but no story content available.",
                    "action": "reply_user",
                    "action_params": {
                        "message": empty_msg
                    }
                }

        # 2. General Master Controller logic with Payload Deduplication
        if isinstance(parsed_payload, dict) and "current_story" in parsed_payload:
            stripped_payload = {k: v for k, v in parsed_payload.items() if k != "current_story"}
            user_payload_str = json.dumps(stripped_payload, ensure_ascii=False)
        else:
            user_payload_str = event_data

        short_context = memory.get_short_context(max_chars=3000) if memory else (current_story[-2000:] if current_story else "Chưa có truyện.")
        summaries = "\n".join(memory.chapter_summaries) if memory and memory.chapter_summaries else "Chưa có."

        system_prompt = f"""{COPILOT_SYSTEM_PROMPT}

THÔNG TIN BẢN THẢO HIỆN TẠI:
- Tóm tắt các phần: {summaries}
- Trích đoạn truyện hiện tại:
{short_context}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"[EVENT: {event_type}]\nPAYLOAD: {user_payload_str}"}
        ]

        try:
            response, used_model = self._chat_with_fallback(messages, temperature=0.3, max_tokens=3000)
            cleaned = re.sub(r'^```(?:json)?\s*\n?', '', response.strip(), flags=re.IGNORECASE).strip()
            cleaned = re.sub(r'\n?```\s*$', '', cleaned).strip()
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                res = json.loads(match.group(0), strict=False)
            else:
                res = json.loads(response, strict=False)

            if isinstance(res, dict) and res.get("action") == "edit_story_direct":
                # Check if we can safely re-route to Path A to preserve full manuscript integrity
                if current_story and user_message:
                    direct_res = self._perform_direct_manuscript_edit(
                        user_message,
                        current_story,
                        selected_text=selected_text,
                        cursor_position=cursor_position
                    )
                    if direct_res:
                        return direct_res

                # Fallback: Safely merge updated_story_content with prefix if current_story is long
                if "action_params" not in res or not isinstance(res.get("action_params"), dict):
                    res["action_params"] = {}
                params = res["action_params"]
                if "updated_story_content" not in params and "updated_story_content" in res:
                    params["updated_story_content"] = res["updated_story_content"]
                if "updated_story_content" in params:
                    raw_content = unwrap_story_prose(params["updated_story_content"])
                    if current_story and len(current_story) > 2000:
                        first_chunk = current_story[:100].strip()
                        if first_chunk and not raw_content.strip().startswith(first_chunk):
                            prefix = current_story[:-2000].rstrip()
                            merged = f"{prefix}\n\n{raw_content}".strip()
                            raw_content = HeadingPreservationEngine.preserve_headings(
                                original_story=current_story,
                                window_text=short_context,
                                revised_window=merged
                            )
                    params["updated_story_content"] = raw_content

                    # Historical validation on updated content
                    if HistoricalGroundingGatekeeper is not None and raw_content:
                        detected_mode = NarrativeMode.CHINH_SU
                        if auto_detect_narrative_mode is not None:
                            detected_mode, _ = auto_detect_narrative_mode(raw_content)
                        is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                            raw_content, mode=detected_mode, user_prompt=user_message
                        )
                        if not is_valid:
                            safe_log(f"[Copilot Event Blocked] Historical distortion: {violations}")
                            rejection_msg = (
                                f"The modification was blocked because it violates Vietnamese historical integrity: {'; '.join(violations)}"
                                if is_en else
                                f"Hệ thống không thể thực hiện chỉnh sửa này vì vi phạm nguyên tắc bảo vệ lịch sử Việt Nam: {'; '.join(violations)}"
                            )
                            return {
                                "thought": f"Historical distortion detected in edited manuscript: {violations}",
                                "action": "reply_user",
                                "action_params": {
                                    "message": rejection_msg
                                }
                            }
            return res
        except Exception as e:
            safe_log(f"Master Controller Error: {e}")
            err_msg = (
                "Sorry, the Co-pilot assistant is temporarily experiencing technical difficulties. Please try again shortly!"
                if is_en else
                "Xin lỗi, Hệ thống chỉ huy đang gặp trục trặc nhẹ. Bạn vui lòng thử lại nhé!"
            )
            return {
                "thought": f"Lỗi hệ thống khi phân tích event: {str(e)}",
                "action": "reply_user",
                "action_params": {"message": err_msg}
            }
