import os
import json
import re
from typing import List, Tuple, Optional
from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

# STRICT style prefix and suffix to force Diffusion model attention to B&W Manga
STYLE_PREFIX = "black and white manga, Japanese manga comic art, monochrome ink drawing on paper, "
STYLE_SUFFIX = ", manga panel, screentone shading, bold ink outlines, high contrast black ink, clean lineart, no color, hand drawn 2D illustration, no photograph, no 3D render"

LAYOUT_MAP = {
    "wide": "wide", "horizontal": "wide", "landscape": "wide", "panoramic": "wide", "establishing": "wide",
    "tall": "tall", "vertical": "tall", "portrait": "tall", "dramatic": "tall",
    "square": "square", "medium": "square", "close-up": "square", "closeup": "square", "standard": "square",
}

# ==================== CHARACTER DNA EXTRACTOR ====================
DNA_EXTRACTOR_PROMPT = """You are a lead character designer and visual continuity director for a professional manga studio.
Analyze the Vietnamese story text and extract the EXACT, IMMUTABLE visual physical traits, identifying signature costume, and all aliases/pronouns for each character.

CRITICAL VISUAL CONTINUITY SPECIFICATIONS (MANDATORY EXTREME DETAIL):
1. Signature Identifying Costume (MANDATORY):
   - Exact garment type & cut: e.g. crisp button-up short-sleeve school uniform shirt, tailored blazer, high-collar martial arts robes (huyền bào), trench coat.
   - Specific fabric texture & colors: e.g. pure white cotton, dark navy pleated skirt, black silk with gold embroidered dragon hem, crimson red mantle.
   - Collar, Neck & Chest Accessories (ABSOLUTELY REQUIRED): Specify exact collar style (button-down collar, mandarin collar, sailor collar) AND neck/chest accessories (ribbon tie, bow tie, pendant, brooch, collar pin, chest badge, jade pendant on red cord).
   - Outerwear & layering: cardigan, cape, or sash belt if worn.
2. Exact Hairstyle & Head Details (IMMUTABLE):
   - Specific cut, length, and texture: e.g. straight jet-black hair reaching collarbones, high ponytail tied with silver clasp, messy textured dark hair.
   - Bangs & parting: blunt bangs straight across forehead, curtain bangs parted in center, swept back.
   - Hair accessories: ribbon tie, hairpins, clips.
3. Immutable Facial Features:
   - Age, facial structure, eye shape and color: e.g. 17yo Vietnamese student, gentle almond dark eyes, sharp defined jawline, piercing cold amber eyes.
   - Permanent marks: beauty mark under right eye, scar across left eyebrow, glasses.
4. Comprehensive Aliases & Pronoun Registry:
   - Must include character names, nicknames.
   - Vietnamese pronouns & generic terms: "cô bé", "cậu bé", "cô gái", "chàng trai", "cậu ấy", "anh ấy", "cô ấy", "hắn", "nàng", "y", "tiểu tử", "nữ sinh", "nam sinh", "học sinh", "anh bạn cùng bàn", "bạn cùng bàn", "bạn cùng lớp", "bạn học", "người bạn", "chị", "em gái", "bé gái", "thiếu niên", "cậu bạn".
   - English equivalents: "she", "her", "he", "him", "the girl", "the boy", "schoolgirl", "schoolboy", "student", "classmate", "desk mate".
5. Metadata: Specify "gender" ("female" or "male") and primary "role" ("lead", "antagonist", "supporting", "student", "desk_mate").

OUTPUT FORMAT:
Return ONLY a valid JSON object:
{
  "An": {
    "gender": "female",
    "role": "lead",
    "aliases": ["An", "cô bé", "nữ sinh", "cô", "cô ấy", "nàng", "cô gái", "she", "girl", "schoolgirl", "female student", "bạn cùng bàn"],
    "dna": "17yo Vietnamese schoolgirl, soft oval face, gentle dark almond eyes, sharp jawline, straight jet-black hair with blunt bangs across forehead and shoulder-length bob, wearing crisp white short-sleeve school uniform button-up shirt with stiff collar, small dark navy ribbon tie pinned at collar, pleated dark navy skirt"
  }
}
"""

# ==================== SPATIAL SETTING DNA EXTRACTOR ====================
SETTING_EXTRACTOR_PROMPT = """You are an art director and world-building designer for a manga studio.
Analyze the story text and extract the PRIMARY SPATIAL SETTING & ENVIRONMENT ANCHOR to guarantee strict background consistency across all manga panels.

For the primary location, specify:
1. Location type & time of day/era (e.g. vintage 1990s detective office at night, modern high-tech glass lab, ancient stone fortress)
2. Architectural details (walls, windows, flooring, distinctive structural columns)
3. Key persistent props & furniture (e.g. mahogany desk with scattered dossiers, vintage brass lamp, antique bookshelf)
4. Atmospheric lighting & shadows (e.g. moody chiaroscuro lighting, harsh fluorescent light, rain streaks on window)

Return ONLY a valid JSON object:
{
  "location_name": "Tên địa điểm ngắn gọn",
  "setting_anchor": "English visual description under 40 words specifying architecture, persistent props, and lighting atmosphere",
  "atmosphere": "e.g. gloomy noir with heavy shadows, clean sci-fi screentones, rustic vintage ink textures"
}
"""

# ==================== BEAT-BY-BEAT MANGA DIRECTOR ====================
BEAT_DIRECTOR_PROMPT = """You are a master manga director and storyboard artist (combining the meticulous narrative pacing of Naoki Urasawa, the spatial consistency of Inio Asano, and the expressive paneling of Eiichiro Oda).

YOUR MISSION: Faithfully adapt the provided Vietnamese story text into a SEQUENTIAL, BEAT-BY-BEAT MANGA SCRIPT.

ABSOLUTE CRITICAL RULES:
1. NO SKIPPING / NO SUMMARIZING: DO NOT summarize several paragraphs into one generic panel! Adapt EVERY significant exchange, dialogue line, reaction, and physical action into sequential panels.
   - If Character A says something and Character B responds, that is AT LEAST 2 sequential panels (Speaker A -> Reaction/Reply B).
   - If an action or dramatic gesture occurs (e.g. someone stands up, looks out the window, draws a breath, opens a door), give it its own panel.
2. CHARACTER CONSISTENCY: Every panel featuring a character MUST embed their exact hair, face, and signature costume from the CHARACTER REGISTRY into the `image_prompt`. Do NOT change character clothing or hairstyles across panels!
3. SETTING & BACKGROUND CONSISTENCY: Every panel taking place in the primary environment MUST maintain the architecture, lighting, and persistent props from the SETTING REGISTRY so backgrounds DO NOT drift, mutate, or hallucinate between panels.
4. IMAGE PROMPT (English): Under 65 words, describing camera angle (close-up, medium shot, low angle, over-the-shoulder), character expression/action, AND the specific background elements anchored from the setting.
5. COMPLETE DIALOGUE & CAPTION TEXT (Vietnamese):
   - TUYỆT ĐỐI CẤM SỬ DỤNG DẤU BA CHẤM (..., …, .....) VÀ CẮT XÉN: Nghiêm cấm tuyệt đối mọi dấu ba chấm hoặc chuỗi chấm lửng ở giữa câu hoặc cuối câu. Không được để câu nói cụt, đứt đoạn, hay lửng lơ.
   - Mọi lời thoại và lời dẫn dưới mỗi khung tranh BẮT BUỘC là câu nói hoàn chỉnh, giàu cảm xúc, ngữ pháp trọn vẹn và kết thúc bằng dấu câu chuẩn mực: dấu chấm (.), dấu chấm than (!), hoặc dấu chấm hỏi (?).
   - Nếu nhân vật ngập ngừng hay ngắt nhịp cảm xúc, sử dụng dấu gạch nối ( - ) hoặc dấu phẩy (,) để giữ trọn ý nghĩa và nhịp điệu cảm xúc mà không dùng dấu ba chấm.
   - Định dạng chuẩn: `[Tên nhân vật]: "[Câu thoại trọn vẹn giàu cảm xúc]"` hoặc câu độc thoại/dẫn chuyện hoàn chỉnh.
6. LAYOUT TYPE: Choose dynamically:
   - "wide": for establishing rooms, wide action scenes, panoramic moments.
   - "tall": for dramatic full-body poses, towering figures, intense emotional heights.
   - "square": for dialogues, face-to-face exchanges, medium shots.

OUTPUT FORMAT:
Return ONLY a valid JSON array of panel objects:
[
  {
    "panel_index": 1,
    "image_prompt": "wide establishing shot of a quiet sunlit classroom, wooden desks neatly arranged beside large glass windows, morning light casting soft diagonal shadows across the floor",
    "dialogue_text": "Hôm nay là một ngày thật đặc biệt đối với tôi.",
    "layout_type": "wide"
  },
  {
    "panel_index": 2,
    "image_prompt": "medium close-up shot of the young student turning around with a bright, curious smile, sitting at the wooden desk near the window",
    "dialogue_text": "An: \"Chào bạn, chúng ta cùng nhau cố gắng nhé!\"",
    "layout_type": "square"
  }
]
"""


def sanitize_complete_dialogue(text: str) -> str:
    """
    Sanitizes comic dialogue and narrator text to achieve 0% ellipsis.
    - Strips all occurrences of '...', '…', '.....', and multiple consecutive periods.
    - Converts mid-sentence pauses or speech hesitations into natural dashes (' - ') or commas (', ').
    - Preserves character emotion while strictly eliminating truncation dots.
    - Cleans all trailing dots/ellipses before terminal quotes or end of string.
    - Enforces valid terminal sentence punctuation ('.', '!', '?', '"', '”').
    - Returns an empty string if input was only dots/whitespace.
    """
    if not text or not isinstance(text, str):
        return ""

    raw = text.strip()
    if not raw:
        return ""

    # Check if string contains any alphanumeric characters (Vietnamese or ASCII)
    if not re.search(r'[\w\dÀ-ỹ]', raw):
        return ""

    # 1. Normalize unicode ellipsis characters to dots
    s = raw.replace('…', '...')

    # 2. Clean trailing dots/ellipses before closing quotes or at end of string
    # e.g., 'trả thù..."' -> 'trả thù"' or 'kết thúc...' -> 'kết thúc'
    s = re.sub(r'[\.\s…]{2,}(?=["\'”’]?\s*$)', '', s)

    # Clean dots immediately preceding existing terminal marks like '...!' or '...?'
    s = re.sub(r'[\.\s…]{2,}(?=[\!\?])', '', s)

    # 3. Handle mid-sentence pauses, spaced dots, and hesitations
    # 3a. Long dramatic pauses (4 or more consecutive dots) -> ' - '
    s = re.sub(r'\s*\.{4,}\s*', ' - ', s)

    # 3b. Speech stutter / hesitation on repeated words or word prefixes (e.g. "Tôi... tôi", "Anh... anh") -> ' - '
    s = re.sub(r'(?i)\b([a-zà-ỹ]+)\s*(?:-\s*|\.{2,3}\s*|(?:\s*\.\s*){2,3})(?=\1\b)', r'\1 - ', s)

    # 3c. Ellipsis after auxiliary/function words (e.g. "sẽ... trả thù", "đã... làm", "rất... nhiều")
    # In Vietnamese narrative, trailing dots after auxiliary/modifier words are awkward stutter artifacts:
    # convert to single space to keep the verbal phrase natural and smooth
    vn_particles = r'(?:sẽ|đã|đang|sắp|rất|quá|lắm|thực|thật|cực|cũng|vẫn|cứ|đều|lại|vừa|mới|hãy|đừng|chớ|bị|được|bởi|do|tại|vì|để|cho|với|cùng|và|hay|hoặc|của|ở|từ|lên|xuống|ra|vào)'
    s = re.sub(rf'(?i)\b({vn_particles})\s*(?:-\s*|\.{2,3}\s*|(?:\s*\.\s*){2,3})', r'\1 ', s)

    # 3d. Pre-normalize any remaining mid-sentence spaced dots or pauses -> ' - '
    # (e.g. "Tôi . . . không biết." or "Chờ đã... cậu là ai?")
    s = re.sub(r'(?:\s*\.\s*){2,}', ' - ', s)

    # 5. Clean up redundant spaces around punctuation and dashes
    s = re.sub(r'\s+([,\.!\?])', r'\1', s)
    s = re.sub(r'\s*-\s*-\s*', ' - ', s)
    s = re.sub(r'\s+', ' ', s).strip()

    # 4. Clean up any remaining sequences of 2+ dots anywhere in the text
    # (Runs AFTER Step 5 space cleanup so concatenated dots can never leak through)
    s = re.sub(r'\.{2,}', '.', s)
    s = re.sub(r'\s+([,\.!\?])', r'\1', s)

    # 6. Ensure trailing punctuation is grammatically sound and complete
    # Handle dialogue ending in quote
    if re.search(r'["”\']\s*$', s):
        # Check if punctuation exists right before the closing quote
        m = re.search(r'^(.*?)(\.*)(["”\'])$', s)
        if m:
            content, dots, quote_char = m.group(1), m.group(2), m.group(3)
            content = content.rstrip('. ')
            if not content:
                return ""
            if content[-1] not in ['.', '!', '?']:
                s = f"{content}.{quote_char}"
            else:
                s = f"{content}{quote_char}"
    else:
        # Not ending in a quote: ensure terminal punctuation
        s = s.rstrip('. ')
        if not s:
            return ""
        if s[-1] not in ['.', '!', '?']:
            s += '.'

    return s


def decompose_story_beats(story_text: str) -> list[str]:
    """
    Splits Vietnamese narrative prose cleanly at sentence boundaries (. ! ? \n quotes and dashes)
    and groups them into cohesive story beats (1-3 sentences per beat).
    - Guarantees short dialogues (< 15 chars like 'Chào bạn!', 'Đi thôi!') are NEVER discarded.
    - Preserves quotes and dialogue attribution.
    - Ensures every beat is a complete, non-truncated sentence.
    """
    if not story_text or not isinstance(story_text, str):
        return []

    # First, split into paragraph blocks
    paragraphs = [p.strip() for p in story_text.split('\n') if p.strip()]
    if not paragraphs:
        return []

    # Sentence boundary regex with fixed-width lookbehinds:
    # 1. Punctuation [.!?] followed by whitespace before capital letter / dialogue quote / dash
    # 2. Punctuation [.!?] with closing quote ["'”’] followed by whitespace
    # 3. Punctuation [.!?] followed by em-dash dialogue
    sentence_split_regex = re.compile(
        r'(?<=[.!?])\s+(?=[A-ZÀ-Ỹ0-9“"‘\'—\-])|'
        r'(?<=[.!?]["\'”’])\s+|'
        r'(?<=[.!?])\s*—\s*'
    )

    atomic_units = []
    for para in paragraphs:
        raw_sentences = sentence_split_regex.split(para)
        for s in raw_sentences:
            s_clean = s.strip()
            # Do NOT discard short dialogues like "Chào bạn!", "Đi thôi!"
            # Only ignore if completely empty or lacks letters/digits
            if s_clean and re.search(r'[\w\dÀ-ỹ]', s_clean):
                atomic_units.append(s_clean)

    if not atomic_units:
        return []

    # Group atomic sentences into cohesive beats (1-3 sentences per beat)
    beats = []
    current_beat_sentences = []
    current_beat_len = 0

    def is_dialogue_unit(u: str) -> bool:
        return bool(re.search(r'["“”—\-]|:\s*["“]', u)) or u.startswith('-') or u.startswith('—')

    for unit in atomic_units:
        unit_is_dialogue = is_dialogue_unit(unit)

        if current_beat_sentences:
            curr_has_dialogue = any(is_dialogue_unit(s) for s in current_beat_sentences)

            # Dialogue transitions: A dialogue turn should usually be its own beat
            # or if max 3 sentences reached, or len > 220
            should_break = (
                len(current_beat_sentences) >= 3 or
                (unit_is_dialogue and curr_has_dialogue) or
                (unit_is_dialogue and current_beat_len > 80) or
                (not unit_is_dialogue and curr_has_dialogue and current_beat_len > 60) or
                (current_beat_len + len(unit) > 260)
            )

            if should_break:
                beat_text = " ".join(current_beat_sentences).strip()
                sanitized_beat = sanitize_complete_dialogue(beat_text)
                if sanitized_beat:
                    beats.append(sanitized_beat)
                current_beat_sentences = []
                current_beat_len = 0

        current_beat_sentences.append(unit)
        current_beat_len += len(unit)

    if current_beat_sentences:
        beat_text = " ".join(current_beat_sentences).strip()
        sanitized_beat = sanitize_complete_dialogue(beat_text)
        if sanitized_beat:
            beats.append(sanitized_beat)

    return beats

class ComicDirectorAgent:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY_COMIC") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Thiếu GROQ_API_KEY_COMIC hoặc GROQ_API_KEY")
        self.llm = GroqClient(model_name="qwen/qwen3.8-27b", api_key=api_key)

    def sanitize_complete_dialogue(self, text: str) -> str:
        """Instance helper routing to module-level sanitize_complete_dialogue."""
        return sanitize_complete_dialogue(text)

    def decompose_story_beats(self, story_text: str) -> list[str]:
        """Instance helper routing to module-level decompose_story_beats."""
        return decompose_story_beats(story_text)

    def extract_character_dna(self, story_text: str, memory: StoryMemory = None) -> dict:
        """Extracts immutable visual character DNA with explicit costumes, metadata, and aliases."""
        existing_dna = {}
        prior_context = ""
        if memory and memory.story_bible and memory.story_bible.characters:
            prior_context = "PRIOR KNOWN CHARACTERS FROM STORY BIBLE:\n"
            for c in memory.story_bible.characters:
                if isinstance(c, dict) and c.get("name") and c.get("appearance"):
                    c_name = c["name"]
                    c_app = c.get("appearance", "")
                    c_role = str(c.get("role", "")).lower()
                    c_gender = str(c.get("gender", "")).lower()
                    prior_context += f"- {c_name} ({c_role}): {c_app}\n"

                    # Populate aliases with lowercase name and individual first/last name tokens
                    name_lower = c_name.lower().strip()
                    alias_set = {name_lower}
                    for part in name_lower.split():
                        if len(part) > 1:
                            alias_set.add(part)

                    app_lower = c_app.lower()
                    is_female = (
                        c_gender in ["female", "woman", "nữ"] or
                        bool(re.search(r"\b(?:female|woman)\b", c_gender)) or
                        "nữ" in c_gender or "nữ" in c_role or
                        any(re.search(rf"\b{re.escape(cue)}\b", app_lower) for cue in ["schoolgirl", "girl", "woman", "female"])
                    )
                    is_male = (
                        (
                            c_gender in ["male", "man", "nam"] or
                            bool(re.search(r"\b(?:male|man)\b", c_gender)) or
                            "nam" in c_gender or "nam" in c_role or
                            any(re.search(rf"\b{re.escape(cue)}\b", app_lower) for cue in ["schoolboy", "boy", "man", "male"])
                        )
                        and not is_female
                    )

                    # Populate gender-appropriate pronoun aliases
                    if is_female:
                        alias_set.update([
                            "cô bé", "nữ sinh", "cô ấy", "nàng", "cô gái", "chị", "em gái", "bé gái",
                            "she", "her", "girl", "schoolgirl", "female student"
                        ])
                    elif is_male:
                        alias_set.update([
                            "anh bạn", "bạn cùng bàn", "học sinh nam", "cậu ấy", "chàng trai", "anh ấy",
                            "thiếu niên", "cậu bạn", "cậu bé", "nam sinh", "he", "him", "boy", "schoolboy", "male student"
                        ])

                    if any(k in c_role for k in ["desk", "bàn", "classmate", "bạn"]) or any("bàn" in a for a in alias_set):
                        alias_set.update(["anh bạn cùng bàn", "bạn cùng bàn", "bạn cùng lớp", "bạn học", "người bạn", "desk mate", "classmate"])

                    if any(k in c_role for k in ["student", "học sinh"]) or "student" in app_lower:
                        alias_set.update(["học sinh", "bạn cùng lớp", "bạn học", "người bạn", "student"])

                    existing_dna[c_name] = {
                        "dna": c_app,
                        "aliases": list(alias_set),
                        "gender": c_gender or ("female" if is_female else ("male" if is_male else "unknown")),
                        "role": c_role or "lead"
                    }

        try:
            sample_text = story_text[:3500]
            user_prompt = f"Extract Visual DNA and signature costumes for characters in this story:\n\n{prior_context}\nSTORY EXCERPT:\n{sample_text}".strip()
            resp = self.llm.chat(
                messages=[
                    {"role": "system", "content": DNA_EXTRACTOR_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            cleaned = re.sub(r'```(?:json)?\s*', '', resp).strip()
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    for k, v in parsed.items():
                        if isinstance(v, dict) and "dna" in v:
                            existing_dna[k] = v
                        elif isinstance(v, str):
                            alias_tokens = [k.lower()] + [p.lower() for p in k.split() if len(p) > 1]
                            existing_dna[k] = {
                                "dna": v,
                                "aliases": alias_tokens,
                                "gender": "unknown",
                                "role": "supporting"
                            }
        except Exception as e:
            print(f"[Comic] Character DNA extraction fallback ({e})")

        # Guaranteed rich fallback if nothing extracted
        if not existing_dna:
            existing_dna["Protagonist"] = {
                "gender": "unknown",
                "role": "lead",
                "dna": "young Asian protagonist, neat dark hair, expressive dark eyes, sharp jawline, wearing crisp white collared shirt with small dark ribbon tie, dark navy jacket",
                "aliases": [
                    "protagonist", "nhân vật chính", "người", "học sinh", "cô bé", "cậu bé",
                    "cậu ấy", "cô ấy", "anh bạn", "anh bạn cùng bàn", "bạn cùng bàn", "nữ sinh",
                    "nam sinh", "chàng trai", "cô gái", "bạn cùng lớp", "bạn học", "người bạn",
                    "student", "she", "he"
                ]
            }

        return existing_dna

    def extract_setting_dna(self, story_text: str, memory: StoryMemory = None) -> dict:
        """Extracts immutable spatial setting anchor to lock background consistency across panels."""
        existing_setting = {}
        if memory and memory.story_bible and memory.story_bible.world_setting:
            existing_setting["location_name"] = "Bối cảnh chính"
            existing_setting["setting_anchor"] = memory.story_bible.world_setting
            existing_setting["atmosphere"] = "atmospheric manga screentone background"

        try:
            sample_text = story_text[:3500]
            resp = self.llm.chat(
                messages=[
                    {"role": "system", "content": SETTING_EXTRACTOR_PROMPT},
                    {"role": "user", "content": f"Extract Primary Spatial Setting DNA for this story:\n\n{sample_text}"}
                ],
                temperature=0.2,
                max_tokens=800
            )
            cleaned = re.sub(r'```(?:json)?\s*', '', resp).strip()
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    existing_setting.update(parsed)
        except Exception as e:
            print(f"[Comic] Setting DNA extraction fallback ({e})")
            if not existing_setting:
                existing_setting = {
                    "location_name": "Bối cảnh chung",
                    "setting_anchor": "detailed indoor room with wooden furniture and ambient window lighting",
                    "atmosphere": "dramatic high contrast manga screentone"
                }

        return existing_setting

    def _parse_json_array(self, raw_output):
        """Extract and parse a JSON array from LLM output."""
        cleaned = re.sub(r'```(?:json)?\s*', '', raw_output).strip()
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        return json.loads(cleaned, strict=False)

    def _validate_panels(self, script_data, character_dna_map=None, setting_dna=None):
        """Validate, normalize layout, enforce character visual DNA, background anchor, and complete dialogue."""
        if not isinstance(script_data, list):
            raise ValueError("Output is not a JSON array")

        dna_map = character_dna_map or {}
        setting_anchor = ""
        if setting_dna and isinstance(setting_dna, dict):
            setting_anchor = setting_dna.get("setting_anchor", "").strip()

        # Build normalized character lookup list with auto-enriched semantic pronouns
        char_entry_list = []
        for name, data in dna_map.items():
            if isinstance(data, dict):
                dna_text = data.get("dna", "")
                raw_aliases = [name] + list(data.get("aliases", []))
                gender = str(data.get("gender", "")).lower()
                role = str(data.get("role", "")).lower()
            else:
                dna_text = str(data)
                raw_aliases = [name]
                gender = ""
                role = ""

            dna_lower = dna_text.lower()
            name_lower = name.lower()

            # Add lowercase full name and individual name words
            alias_set = set()
            for a in raw_aliases:
                a_str = str(a).strip().lower()
                if a_str:
                    alias_set.add(a_str)
            for part in name_lower.split():
                if len(part) > 1:
                    alias_set.add(part)

            # Determine gender from explicit fields, DNA text, role, or aliases
            is_female = (
                gender in ["female", "woman", "nữ"] or
                bool(re.search(r"\b(?:female|woman)\b", gender)) or
                "nữ" in gender or
                "nữ" in role or
                any(re.search(rf"\b{re.escape(cue)}\b", dna_lower) for cue in ["schoolgirl", "girl", "woman", "female", "her", "she"]) or
                any(cue in alias_set for cue in ["cô bé", "nữ sinh", "cô ấy", "nàng", "cô gái", "she", "girl"])
            )

            is_male = (
                (
                    gender in ["male", "man", "nam"] or
                    bool(re.search(r"\b(?:male|man)\b", gender)) or
                    "nam" in gender or
                    "nam" in role or
                    any(re.search(rf"\b{re.escape(cue)}\b", dna_lower) for cue in ["schoolboy", "boy", "man", "male", "his", "he"]) or
                    any(cue in alias_set for cue in ["anh bạn", "bạn cùng bàn", "học sinh nam", "cậu ấy", "chàng trai", "anh ấy", "he", "boy"])
                )
                and not is_female
            )

            # Enrich with Vietnamese Semantic Pronoun Dictionary
            if is_female:
                alias_set.update([
                    "cô bé", "nữ sinh", "cô ấy", "nàng", "cô gái", "chị", "em gái", "bé gái",
                    "she", "her", "girl", "schoolgirl", "female student"
                ])
            elif is_male:
                alias_set.update([
                    "anh bạn", "bạn cùng bàn", "học sinh nam", "cậu ấy", "chàng trai", "anh ấy",
                    "thiếu niên", "cậu bạn", "cậu bé", "nam sinh", "anh ta", "cậu ta", "hắn",
                    "he", "him", "boy", "schoolboy", "male student", "young man"
                ])

            # Relational desk mate / classmate terms
            if any(k in role for k in ["desk", "bàn", "classmate", "bạn"]) or any("bàn" in a for a in alias_set):
                alias_set.update(["anh bạn cùng bàn", "cô bạn cùng bàn", "bạn cùng bàn", "bạn cùng lớp", "bạn học", "người bạn", "desk mate", "classmate"])

            if any(k in role for k in ["student", "học sinh"]) or "student" in dna_lower or "học sinh" in dna_lower:
                alias_set.update(["học sinh", "bạn cùng lớp", "bạn học", "người bạn", "student"])

            char_entry_list.append({
                "name": name,
                "dna": dna_text,
                "aliases": list(alias_set),
                "gender": gender,
                "role": role,
                "is_female": is_female,
                "is_male": is_male
            })

        validated = []
        for i, item in enumerate(script_data):
            prompt = str(item.get("image_prompt") or "a detailed manga scene").strip()
            raw_dialogue = str(item.get("dialogue_text") or "").strip()
            if raw_dialogue.lower() in ["none", "null"]:
                raw_dialogue = ""
            dialogue = raw_dialogue
            search_text = f"{prompt} {dialogue}"

            # Smart Character DNA injection: Inspect BOTH prompt and dialogue_text
            matched_chars = []
            for c in char_entry_list:
                for alias in c["aliases"]:
                    alias_clean = alias.strip()
                    if not alias_clean:
                        continue
                    # Safe word boundary regex check to prevent substring false positives
                    pattern = rf"(?<!\w){re.escape(alias_clean)}(?!\w)"
                    matches = list(re.finditer(pattern, search_text, re.IGNORECASE))
                    if not matches:
                        continue

                    # Safety check for English article "an" or Vietnamese compound words vs character name "An"
                    if alias_clean.lower() == "an":
                        has_valid_char_match = False
                        for m in matches:
                            before_text = search_text[:m.start()]
                            after_text = search_text[m.end():].lstrip()
                            # 1. If preceded by Vietnamese compound prefix words (e.g. "bất an", "bình an", "công an", "trị an", "quốc an", "bảo an")
                            if re.search(r'(?<!\w)(?:bất|bình|công|trị|quốc|bảo)[\s\-_]*$', before_text, re.IGNORECASE):
                                continue
                            # 2. If followed by Vietnamese compound suffix words (e.g. "an toàn", "an tâm", "an ninh", "an dưỡng", "an bài", "an nghỉ", "an ủi", "an nhiên", "an lạc", "an vui", "an cư", "an phận")
                            if re.match(r'^(?:toàn|tâm|ninh|dưỡng|bài|nghỉ|ủi|nhiên|lạc|vui|cư|phận)(?!\w)', after_text, re.IGNORECASE):
                                continue
                            # 3. If followed by English camera shot, scene description, or vowel adjectives (indefinite article "an")
                            if re.match(r'^(?:establishing|extreme|overhead|wide|interior|exterior|empty|aerial|eye-level|illustration|action|anime|epic|intense|indoor|outdoor|open|ornate|ambient|abandoned|shot|close-up|closeup|panel|angle|old|ancient|isolated|overgrown|ominous|elaborate|unusual|elderly|intricate|ordinary|eerie|electric|enormous)\b', after_text, re.IGNORECASE):
                                continue
                            has_valid_char_match = True
                            break
                        if not has_valid_char_match:
                            continue

                    if c not in matched_chars:
                        matched_chars.append(c)
                    break  # Matched this character, evaluate next character

            # Gender/role-aware fallback if no explicit match
            if not matched_chars and char_entry_list:
                human_indicators = [
                    "girl", "boy", "student", "man", "woman", "person", "character", "face",
                    "sitting", "standing", "looking", "staring", "writing", "holding", "talking",
                    "crying", "walking", "running", "người", "nhân vật", "khuôn mặt", "bước", "đứng", "ngồi", "nhìn"
                ]
                female_cues = [
                    "girl", "woman", "schoolgirl", "female", "she", "her", "cô gái", "cô bé", "nữ sinh", "nữ", "nàng", "chị", "em gái"
                ]
                male_cues = [
                    "boy", "man", "schoolboy", "male", "he", "his", "him", "chàng trai", "cậu bé", "nam sinh", "nam", "anh", "cậu"
                ]

                # Fallback only triggers if visual prompt depicts a human figure/action
                has_human = any(re.search(rf"(?<!\w){re.escape(k)}(?!\w)", prompt, re.IGNORECASE) for k in human_indicators)
                if has_human:
                    has_female_cue = any(re.search(rf"(?<!\w){re.escape(k)}(?!\w)", search_text, re.IGNORECASE) for k in female_cues)
                    has_male_cue = any(re.search(rf"(?<!\w){re.escape(k)}(?!\w)", search_text, re.IGNORECASE) for k in male_cues)

                    selected = None
                    if has_female_cue and not has_male_cue:
                        females = [c for c in char_entry_list if c.get("is_female")]
                        if females:
                            selected = females[0]
                    elif has_male_cue and not has_female_cue:
                        males = [c for c in char_entry_list if c.get("is_male")]
                        if males:
                            selected = males[0]

                    if not selected:
                        leads = [c for c in char_entry_list if "lead" in c.get("role", "").lower() or "protagonist" in c.get("role", "").lower()]
                        selected = leads[0] if leads else char_entry_list[0]

                    matched_chars.append(selected)

            # Inject DNA for ALL matched characters (no premature early break!)
            injected_dnas = []
            for c in matched_chars:
                c_dna = c["dna"].strip()
                if c_dna and c_dna.lower() not in prompt.lower():
                    injected_dnas.append(c_dna)

            if injected_dnas:
                prompt = f"{', '.join(injected_dnas)}, {prompt}"

            # Blend setting anchor to preserve background consistency across panels
            if setting_anchor and setting_anchor.lower() not in prompt.lower():
                raw_layout_check = str(item.get("layout_type", "square")).lower()
                if raw_layout_check == "wide" or i == 0 or "background" not in prompt.lower():
                    prompt = f"{prompt}, setting: {setting_anchor}"

            # Clean duplicate style tags
            clean_prompt = prompt
            for tag in ["manga panel", "black and white", "monochrome", "screentone", "comic art"]:
                clean_prompt = re.sub(re.escape(tag), "", clean_prompt, flags=re.IGNORECASE)
            clean_prompt = clean_prompt.strip(" ,.-")

            final_prompt = f"{STYLE_PREFIX}{clean_prompt}{STYLE_SUFFIX}"

            raw_layout = str(item.get("layout_type") or "square").lower().strip()
            normalized_layout = LAYOUT_MAP.get(raw_layout, "square")

            raw_dialogue = str(item.get("dialogue_text") or "").strip()
            if raw_dialogue.lower() in ["none", "null"]:
                raw_dialogue = ""
            dialogue = sanitize_complete_dialogue(raw_dialogue)

            raw_narrator = str(item.get("narrator_text") or "").strip()
            if raw_narrator.lower() in ["none", "null"]:
                raw_narrator = ""
            narrator = sanitize_complete_dialogue(raw_narrator)

            if narrator and not dialogue:
                dialogue = narrator

            if not dialogue:
                if i == 0:
                    dialogue = "Khung cảnh mở ra với sự tĩnh lặng đầy cuốn hút."
                else:
                    dialogue = "Diễn biến tiếp tục trong không gian đầy cảm xúc."

            validated.append({
                "panel_index": i + 1,
                "image_prompt": final_prompt,
                "dialogue_text": dialogue,
                "layout_type": normalized_layout
            })
        return validated

    def generate_comic_script(self, story_text: str, memory: StoryMemory = None) -> list:
        """
        Adapts the story text into a beat-by-beat sequential manga storyboard.
        Produces detailed sequential panels closely tracking every dialogue and action beat.
        """
        print(f"[Comic] Generating beat-by-beat storyboard for {len(story_text)} chars...")
        character_dna = self.extract_character_dna(story_text, memory=memory)
        setting_dna = self.extract_setting_dna(story_text, memory=memory)
        dna_context = "\n".join([f"- {name}: {dna.get('dna', dna) if isinstance(dna, dict) else dna}" for name, dna in character_dna.items()])
        setting_context = f"Location: {setting_dna.get('location_name', 'Main Setting')}\nAnchor: {setting_dna.get('setting_dna', '')}\nAtmosphere: {setting_dna.get('atmosphere', '')}"

        system_instruction = f"{BEAT_DIRECTOR_PROMPT}\n\nCHARACTER VISUAL REGISTRY (IMMUTABLE):\n{dna_context}\n\nSETTING VISUAL ANCHOR (IMMUTABLE):\n{setting_context}\n"

        words_count = len(story_text.split())
        target_min = max(8, min(16, words_count // 50))
        target_max = max(12, min(24, words_count // 30))

        user_content = f"""Adapt this Vietnamese story text into sequential manga panels beat-by-beat.
DO NOT SKIP ANY DIALOGUE OR MAJOR ACTION. Ensure every character line and key reaction is depicted with expressive dialogue text.
Aim for {target_min} to {target_max} detailed panels covering the entire excerpt.
TUYỆT ĐỐI CẤM SỬ DỤNG DẤU BA CHẤM (..., …, .....) VÀ CẮT XÉN: Mọi câu thoại và lời dẫn dưới mỗi khung tranh PHẢI LÀ CÂU HOÀN CHỈNH, TRỌN Ý, KẾT THÚC BẰNG DẤU CHẤM (.), CHẤM THAN (!), HOẶC CHẤM HỎI (?).

STORY TEXT:
{story_text}
"""
        try:
            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            panels_raw = self._parse_json_array(response)
            validated_panels = self._validate_panels(panels_raw, character_dna_map=character_dna, setting_dna=setting_dna)
            print(f"[Comic] Successfully created {len(validated_panels)} detailed beat-by-beat panels with background & character consistency.")
            return validated_panels
        except Exception as e:
            print(f"[Comic] Storyboard LLM failed ({e}), creating structured beat fallback...")
            return self._create_structured_beat_fallback(story_text, character_dna, setting_dna)

    def generate_continuation(self, previous_summary: str, new_text: str, memory: StoryMemory = None) -> list:
        """Continues an existing comic with new sequential panels from newly added text."""
        character_dna = self.extract_character_dna(new_text, memory=memory)
        setting_dna = self.extract_setting_dna(new_text, memory=memory)
        dna_context = "\n".join([f"- {name}: {dna.get('dna', dna) if isinstance(dna, dict) else dna}" for name, dna in character_dna.items()])
        setting_context = f"Location: {setting_dna.get('location_name', 'Main Setting')}\nAnchor: {setting_dna.get('setting_dna', '')}\nAtmosphere: {setting_dna.get('atmosphere', '')}"

        system_instruction = f"""{BEAT_DIRECTOR_PROMPT}

PREVIOUS COMIC PROGRESSION:
{previous_summary}

CHARACTER VISUAL REGISTRY (IMMUTABLE):
{dna_context}

SETTING VISUAL ANCHOR (IMMUTABLE):
{setting_context}
"""
        user_content = f"""Continue the comic from the previous progression with sequential panels adapting this new text beat-by-beat.
DO NOT SKIP DIALOGUES OR ACTIONS. Keep dialogue text expressive, complete, and rich in meaning.
TUYỆT ĐỐI CẤM SỬ DỤNG DẤU BA CHẤM (..., …, .....) VÀ CẮT XÉN: Mọi câu thoại và lời dẫn dưới mỗi khung tranh PHẢI LÀ CÂU HOÀN CHỈNH, TRỌN Ý, KẾT THÚC BẰNG DẤU CHẤM (.), CHẤM THAN (!), HOẶC CHẤM HỎI (?).

NEW STORY TEXT:
{new_text}
"""
        try:
            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            panels_raw = self._parse_json_array(response)
            validated = self._validate_panels(panels_raw, character_dna_map=character_dna, setting_dna=setting_dna)
            return validated
        except Exception as e:
            print(f"[Comic] Continuation failed ({e}), creating structured fallback...")
            return self._create_structured_beat_fallback(new_text, character_dna, setting_dna)

    def _create_structured_beat_fallback(self, story_text: str, character_dna: dict, setting_dna: dict = None) -> list:
        """
        Parses raw text into individual dialogue and action panels as a guaranteed fallback with complete sentences.
        Uses decompose_story_beats to generate sequential panels matching the full story progression without arbitrary line truncations or 12-panel cutoffs.
        Guarantees 0% ellipsis in any panel.
        """
        beats = decompose_story_beats(story_text)

        lead_dna = "young Asian protagonist in casual clothes"
        if character_dna:
            first_val = list(character_dna.values())[0]
            lead_dna = first_val.get("dna", first_val) if isinstance(first_val, dict) else str(first_val)
        bg_anchor = setting_dna.get("setting_anchor", "detailed indoor room with wooden furniture") if setting_dna else "indoor room"

        if not beats:
            raw_fallback = [
                {
                    "panel_index": 1,
                    "image_prompt": f"wide establishing shot of {bg_anchor}",
                    "dialogue_text": "Câu chuyện bắt đầu với những diễn biến đầy bất ngờ.",
                    "layout_type": "wide"
                },
                {
                    "panel_index": 2,
                    "image_prompt": f"medium shot of {lead_dna} speaking with intense emotion, setting: {bg_anchor}",
                    "dialogue_text": "Chúng ta nhất định phải kiên trì bước tiếp!",
                    "layout_type": "square"
                }
            ]
            return self._validate_panels(raw_fallback, character_dna_map=character_dna, setting_dna=setting_dna)

        raw_panels = []
        for idx, beat in enumerate(beats):
            is_dialogue = bool(re.search(r'["“”—\-]|:\s*"', beat))
            if idx == 0:
                layout = "wide"
            elif is_dialogue:
                layout = "square"
            elif idx % 3 == 1:
                layout = "tall"
            else:
                layout = "square"

            shot_desc = "expressive dialogue close-up, talking intensely" if is_dialogue else "dramatic narrative scene, engaging posture"
            prompt = f"{lead_dna}, {shot_desc}, setting: {bg_anchor}"

            raw_panels.append({
                "panel_index": idx + 1,
                "image_prompt": prompt,
                "dialogue_text": beat,
                "layout_type": layout
            })

        return self._validate_panels(raw_panels, character_dna_map=character_dna, setting_dna=setting_dna)
