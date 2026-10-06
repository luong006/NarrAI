import os
import json
import re
from typing import List, Tuple, Optional, Any
from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

try:
    from services.ontology import (
        NarrativeMode,
        CulturalTier,
        TriTierOntologyResolver,
        MASTER_NEGATIVE_VIETNAMESE,
        normalize_narrative_mode,
        normalize_cultural_tier
    )
except ImportError:
    try:
        from backend.services.ontology import (
            NarrativeMode,
            CulturalTier,
            TriTierOntologyResolver,
            MASTER_NEGATIVE_VIETNAMESE,
            normalize_narrative_mode,
            normalize_cultural_tier
        )
    except ImportError:
        NarrativeMode = None
        CulturalTier = None
        TriTierOntologyResolver = None
        MASTER_NEGATIVE_VIETNAMESE = "hanfu, kimono, yukata, hanbok, samurai, samurai armor, ninja, katana, geisha"
        normalize_narrative_mode = lambda x: x
        normalize_cultural_tier = lambda x: 1


# STRICT style prefix and suffix to force Diffusion model attention to Modern Monochrome School Manga
STYLE_PREFIX = (
    "masterpiece monochrome Japanese manga illustration, professional manga comic art, "
    "crisp clean black and white ink lineart, "
)
STYLE_SUFFIX = (
    ", clean G-pen lineart, delicate screentone shading, fine dot pattern tones, "
    "high contrast black ink on bright white paper, no color, pure monochrome, "
    "studio quality 2D manga illustration, expressive anime aesthetic, sharp contours"
)


def _format_character_dna_registry(character_dna: dict) -> str:
    """Render canonical visual traits with the aliases used to resolve characters."""
    lines = []
    for name, data in character_dna.items():
        if isinstance(data, dict):
            details = [
                str(data.get(key, "")).strip()
                for key in ("gender", "role")
                if str(data.get(key, "")).strip() and str(data.get(key, "")).lower() != "unknown"
            ]
            aliases = data.get("aliases", [])
            if isinstance(aliases, str):
                aliases = [aliases]
            elif not isinstance(aliases, (list, tuple, set)):
                aliases = []
            aliases = list(dict.fromkeys(str(alias).strip() for alias in aliases if str(alias).strip()))
            visual_dna = str(data.get("dna", "")).strip()
            identity = f" ({', '.join(details)})" if details else ""
            alias_context = f"; aliases: {', '.join(aliases[:8])}" if aliases else ""
            lines.append(f"- {name}{identity}: {visual_dna}{alias_context}")
        else:
            lines.append(f"- {name}: {data}")
    return "\n".join(lines)


LAYOUT_MAP = {
    "wide": "wide", "horizontal": "wide", "landscape": "wide", "panoramic": "wide", "establishing": "wide",
    "tall": "tall", "vertical": "tall", "portrait": "tall", "dramatic": "tall",
    "square": "square", "medium": "square", "close-up": "square", "closeup": "square", "standard": "square",
}

# ==================== CHARACTER DNA EXTRACTOR ====================
DNA_EXTRACTOR_PROMPT = """You are a lead character designer and visual continuity director for a professional manga studio.
Analyze the Vietnamese story text and extract the EXACT, IMMUTABLE visual physical traits, identifying signature costume, and all aliases/pronouns for each character.

CRITICAL VISUAL CONTINUITY SPECIFICATIONS (MANDATORY EXTREME DETAIL):
0. CANONICAL STORY DNA: When prior character details are supplied from the Dynamic Scene Graph or Story Bible, treat their appearance, age, hairstyle, and costume as immutable canon. Preserve those details exactly; infer only missing fields and never replace canon with a new design.
1. Signature Identifying Costume (MANDATORY):
   - Exact garment type & cut: e.g. crisp button-up short-sleeve school uniform shirt, tailored navy blazer, pleated skirt, tailored trousers, knit vest, trench coat, or Vietnamese traditional attire (Áo Ngũ Thân, Áo Nhật Bình, Áo Tấc, Khăn Đóng, Áo Bà Ba, Nón Lá).
   - Specific fabric texture & colors: e.g. pure white cotton shirt, dark navy pleated skirt, charcoal grey tailored trousers, dark navy blazer.
   - Collar, Neck & Chest Accessories (ABSOLUTELY REQUIRED): Specify exact collar style (button-down collar, stiff collar, sailor collar) AND neck/chest accessories (ribbon tie, bow tie, school necktie, brooch, collar pin, chest crest badge, uniform pendant).
   - Outerwear & layering: knit cardigan, sweater vest, tailored school blazer.
2. Exact Hairstyle & Head Details (IMMUTABLE):
   - Specific cut, length, and texture: e.g. straight jet-black hair reaching collarbones, high ponytail tied with ribbon, messy textured dark hair.
   - Bangs & parting: blunt bangs straight across forehead, curtain bangs parted in center, swept back.
   - Hair accessories: ribbon tie, hairpins, clips.
3. Immutable Facial Features:
   - Age, facial structure, eye shape and color: e.g. 17yo Vietnamese student, gentle almond dark eyes, sharp defined jawline, expressive dark eyes.
   - Permanent marks: beauty mark under right eye, faint birthmark, glasses.
4. Comprehensive Aliases & Pronoun Registry:
   - Must include character names, nicknames.
   - Vietnamese pronouns & generic terms: "cô bé", "cậu bé", "cô gái", "chàng trai", "cậu ấy", "anh ấy", "cô ấy", "nữ sinh", "nam sinh", "học sinh", "anh bạn cùng bàn", "bạn cùng bàn", "bạn cùng lớp", "bạn học", "người bạn", "chị", "em gái", "bé gái", "thiếu niên", "cậu bạn", "chàng", "nàng", "tiểu thư", "công tử", "tướng quân", "nghĩa sĩ", "bệ hạ".
   - English equivalents: "she", "her", "he", "him", "the girl", "the boy", "schoolgirl", "schoolboy", "student", "classmate", "desk mate".
5. Compact Visual DNA Representation:
   - Keep visual DNA representation compact under 30 words per character to strictly preserve CLIP 77 token budget.
6. Metadata: Specify "gender" ("female" or "male") and primary "role" ("lead", "student", "desk_mate", "supporting").

OUTPUT FORMAT:
Return ONLY a valid JSON object:
{
  "An": {
    "gender": "female",
    "role": "lead",
    "aliases": ["An", "cô bé", "nữ sinh", "cô", "cô ấy", "cô gái", "she", "girl", "schoolgirl", "female student", "bạn cùng bàn"],
    "dna": "17yo Vietnamese schoolgirl, soft oval face, gentle dark almond eyes, sharp jawline, straight jet-black hair with blunt bangs across forehead and shoulder-length bob, wearing crisp white short-sleeve school uniform button-up shirt with stiff collar, small dark navy ribbon tie pinned at collar, pleated dark navy skirt"
  }
}
"""

# ==================== SPATIAL SETTING DNA EXTRACTOR ====================
SETTING_EXTRACTOR_PROMPT = """You are an art director and world-building designer for a manga studio.
Analyze the story text and extract the PRIMARY SPATIAL SETTING & ENVIRONMENT ANCHOR to guarantee strict background consistency across all manga panels.
If a canonical setting is supplied from the Dynamic Scene Graph or Story Bible, preserve its location and architectural anchor exactly. Do not replace it with a newly inferred location.

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
BEAT_DIRECTOR_PROMPT = """You are a professional manga director and storyboard artist specializing in clear sequential storytelling, expressive acting, and readable panel composition.

YOUR MISSION: Faithfully adapt the provided Vietnamese story text into a SEQUENTIAL, BEAT-BY-BEAT MANGA SCRIPT.

ABSOLUTE CRITICAL RULES:
1. NO SKIPPING / NO SUMMARIZING: DO NOT summarize several paragraphs into one generic panel! Adapt EVERY significant exchange, dialogue line, reaction, and physical action into sequential panels.
   - If Character A says something and Character B responds, that is AT LEAST 2 sequential panels (Speaker A -> Reaction/Reply B).
   - If an action or dramatic gesture occurs (e.g. someone stands up, looks out the window, draws a breath, opens a door), give it its own panel.
2. CHARACTER CONSISTENCY: Every panel featuring a character MUST name each visible character and describe their exact hair, face, and signature costume from the CHARACTER REGISTRY in `image_prompt`. Do NOT change character clothing, age, or hairstyle across panels. Do not add characters who are not in the story beat.
3. SETTING & BACKGROUND CONSISTENCY: Identify the location of each individual story beat. Reuse the matching architecture, lighting, and persistent props from the SETTING REGISTRY for scenes in that location. For a different location, describe that location from the story instead of forcing the primary setting into the panel.
4. IMAGE PROMPT (English): Under 65 words. Every prompt MUST describe the visible subject(s), their physical action and expression, camera framing, and concrete background/environment details. Avoid abstract-only prompts, empty establishing scenes where a character is acting, generic "manga scene", and details unsupported by the story.
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
    "dialogue_text": "An: \\\\\"Chào bạn, chúng ta cùng nhau cố gắng nhé!\\\\\"",
    "layout_type": "square"
]
"""


# ==================== SPATIAL SCENE ENCLOSURE REGISTRY & QUARANTINE ====================
SPATIAL_ENCLOSURES = {
    "classroom": {
        "detection_keywords": [
            "lớp học", "phòng học", "bàn học", "bảng đen", "classroom", "schoolroom",
            "tiết học", "giờ học", "bàn giáo viên", "bàn đầu", "cuối lớp", "bàn cùng bàn"
        ],
        "anchor_description": (
            "modern Japanese high school classroom interior, neat wooden student desks and chairs, "
            "large green chalkboard mounted on front wall, tall multi-pane glass windows with sunlight "
            "streaming across wooden floor, peaceful classroom atmosphere"
        ),
        "forbidden_spatial_tokens": [
            "street", "road", "alley", "highway", "traffic", "car", "bus", "store", "shop",
            "market", "forest", "park", "palace", "temple", "castle", "dungeon", "battlefield",
            "sword", "blade", "weapon"
        ]
    },
    "school_hallway": {
        "detection_keywords": ["hành lang", "cửa lớp", "dãy phòng học", "hallway", "corridor"],
        "anchor_description": (
            "bright school hallway interior, wooden lockers lining the corridor wall, "
            "tall rectangular windows overlooking the school courtyard, clean screentone floor"
        ),
        "forbidden_spatial_tokens": [
            "palace", "temple", "castle", "dungeon", "highway", "forest", "sword", "blade", "weapon"
        ]
    },
    "school_rooftop": {
        "detection_keywords": ["sân thượng", "rooftop"],
        "anchor_description": (
            "school rooftop on a clear day, protective chain-link wire fence, "
            "distant city horizon in clean manga screentone, wide open sky"
        ),
        "forbidden_spatial_tokens": [
            "indoor", "classroom", "palace", "dungeon", "cave", "sword", "blade", "weapon"
        ]
    },
    "vietnamese_village": {
        "detection_keywords": [
            "cổng làng", "bến sông", "cây đa", "giếng nước", "mái đình", "làng quê",
            "con đê", "bờ sông", "thôn dã", "chùa làng", "xóm nhỏ"
        ],
        "anchor_description": (
            "historic Vietnamese village, ancient mossy village gate, banyan tree by the river wharf, "
            "tranquil communal house curved roof, rustic screentone atmosphere"
        ),
        "forbidden_spatial_tokens": [
            "neon", "car", "bus", "cyberware", "skyscraper", "highway", "traffic"
        ]
    },
    "imperial_palace_vn": {
        "detection_keywords": [
            "hoàng thành", "cung điện", "thăng long", "kinh thành", "điện kính thiên",
            "ngai vàng", "triều đình", "cung đình", "hoàng cung", "tử cấm thành"
        ],
        "anchor_description": (
            "grand Đại Việt imperial palace hall, carved wooden pillars, ornate throne chamber, "
            "solemn royal court atmosphere, delicate screentone shading"
        ),
        "forbidden_spatial_tokens": [
            "car", "bus", "classroom", "school desk", "blackboard", "neon", "highway", "traffic"
        ]
    },
    "battlefield_vn": {
        "detection_keywords": [
            "bạch đằng", "chiến trận", "bãi cọc", "chiến thuyền", "quân reo",
            "như nguyệt", "ngọc hồi", "đống đa", "sa trường", "chiến trường"
        ],
        "anchor_description": (
            "historic Vietnamese battlefield, wooden stakes rising along the river, war boats, "
            "fluttering battle banners, dramatic ink lineart"
        ),
        "forbidden_spatial_tokens": [
            "classroom", "blackboard", "school desk", "locker", "traffic", "car", "neon"
        ]
    }
}

def resolve_spatial_enclosure(
    story_text: str = "",
    setting_dna: dict = None,
    cultural_tier: Optional[int] = None,
    narrative_mode: Optional[str] = None
) -> dict:
    """Determine dominant Spatial Scene Enclosure to anchor the manga scene."""
    sdna = setting_dna or {}
    matched_enc = None
    scene_text = str(story_text)[:1500].lower()
    setting_context = f"{sdna.get('setting_anchor', '')} {sdna.get('location_name', '')}".lower()

    # An explicit location in this panel takes precedence over the story's primary setting.
    for enc_key, enc_data in SPATIAL_ENCLOSURES.items():
        if any(kw in scene_text for kw in enc_data["detection_keywords"]):
            matched_enc = dict(enc_data)
            matched_enc["key"] = enc_key
            break

    if not matched_enc:
        for enc_key, enc_data in SPATIAL_ENCLOSURES.items():
            if any(kw in setting_context for kw in enc_data["detection_keywords"]):
                matched_enc = dict(enc_data)
                matched_enc["key"] = enc_key
                break

    combined = f"{setting_context} {scene_text}"
    # If cultural_tier is Tier 3 (Open Domain) or setting_dna provides an explicit setting_anchor outside school
    tier = cultural_tier or sdna.get("cultural_tier")
    if not matched_enc and (tier == 3 or (sdna.get("setting_anchor") and any(w in combined for w in ["office", "forest", "space", "street", "city", "room", "castle"]))):
        matched_enc = {
            "key": "open_domain",
            "detection_keywords": [],
            "anchor_description": sdna.get("setting_anchor") or f"custom open domain setting: {story_text[:60]}",
            "forbidden_spatial_tokens": sdna.get("forbidden_spatial_tokens", [])
        }

    if not matched_enc:
        matched_enc = dict(SPATIAL_ENCLOSURES["classroom"])
        matched_enc["key"] = "classroom"

    # If setting_dna provides specific forbidden tokens from DSGO, merge them in cleanly
    if sdna.get("forbidden_spatial_tokens"):
        merged_tokens = list(matched_enc.get("forbidden_spatial_tokens", []))
        for tok in sdna["forbidden_spatial_tokens"]:
            if tok not in merged_tokens:
                merged_tokens.append(tok)
        matched_enc["forbidden_spatial_tokens"] = merged_tokens
    return matched_enc

def sanitize_spatial_prompt(prompt: str, enclosure: dict = None) -> str:
    """
    Spatial Quarantine Filter:
    Strips conflicting/outdoor/traffic/ancient/weapon keywords (street, road, highway, car, bus, traffic, palace, sword)
    before rendering indoor classroom scenes, while strictly preserving subwords like 'classroom', 'cardigan', and 'scarf'.
    Handles modifiers, prepositions, irregular plurals, and collapses consecutive commas cleanly.
    """
    if not prompt or not isinstance(prompt, str):
        return ""
    if enclosure is None:
        enclosure = SPATIAL_ENCLOSURES["classroom"]

    clean = prompt
    forbidden = enclosure.get("forbidden_spatial_tokens", [])
    
    # Prepositions including compound directions (out at, out to)
    prepositions = r'(?:on|in|along|across|down|near|beside|by|at|to|through|into|outside|towards|out\s+at|out\s+to|out\s+of)?'
    # Articles
    articles = r'(?:the|a|an)?'
    # Modifiers including ancient, stone, old, abandoned, wooden
    modifiers = r'(?:(?:\b(?:busy|moving|crowded|noisy|outdoor|distant|speeding|passing|ancient|stone|old|abandoned|wooden)\b)\s+)*'

    for token in forbidden:
        # Match preposition + article + modifiers + token with singular or plural (-s, -es)
        clean = re.sub(
            rf'\b{prepositions}\s*{articles}\s*{modifiers}\b{re.escape(token)}(?:es|s)?\b',
            '',
            clean,
            flags=re.IGNORECASE
        )

    # Clean dangling prepositions at clause/string boundaries
    clean = re.sub(
        r'\b(?:at|to|through|into|outside|towards|on|in|along|across|down|near|beside|by)\s*(?:the|a|an)?(?=,|\.|$)',
        '',
        clean,
        flags=re.IGNORECASE
    )

    # Collapse consecutive/orphaned commas and whitespace
    clean = re.sub(r'[,.\s]*,[,.\s]*', ', ', clean).strip(' ,.-')
    clean = re.sub(r'^(?:and|or|with)\s+', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s+(?:and|or|with)$', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s{2,}', ' ', clean).strip(' ,.-')
    return clean

# ==================== VIETNAMESE NEGATION & PROHIBITION GUARD ====================
VIETNAMESE_NEGATION_WORDS = {
    "không", "chẳng", "chưa", "đừng", "cấm", "ngừng", "thôi", "chớ", "ko", "k"
}
CLAUSE_DELIMITERS_PATTERN = r'[,;.!?:\—\-"“”\'\(\)\[\]\n]|\b(?:nhưng|mà|song|tuy\s+nhiên|thế\s+nhưng)\b'

def is_action_negated(text: str, match_start: int) -> bool:
    """
    Checks if a matched action phrase is preceded by a Vietnamese negation or prohibition word
    within the same clause (inspects up to 6 words preceding match_start).
    Prevents negated actions (e.g., 'không nhìn ra cửa sổ') and dialogue reprimands
    (e.g., 'đừng có quay sang nói chuyện') from triggering visual gestures.
    """
    pre_text = text[:match_start]
    # Split by clause boundaries to isolate the immediate clause containing the match
    clause_parts = re.split(CLAUSE_DELIMITERS_PATTERN, pre_text, flags=re.IGNORECASE)
    immediate_clause = clause_parts[-1] if clause_parts else ""
    # Extract preceding words in the immediate clause
    words = re.findall(r'\b\w+\b', immediate_clause.lower())
    window_words = words[-6:] if len(words) > 6 else words
    return any(w in VIETNAMESE_NEGATION_WORDS for w in window_words)

# ==================== ACTION & GESTURE SEMANTIC MAPPING ====================
ACTION_GESTURE_MAPPINGS = [
    # 1. Viết bài, làm việc tại bàn (Strictly requires pairing with viết, chép, ghi, vẽ, làm bài, vở, bài)
    (
        r'(?:cúi đầu|cặm cụi|chăm chú|lúi húi)\s*(?:[\w\s]{0,15})\b(?:viết|chép|ghi|vẽ|làm bài|ghi chép|vở|bài)\b',
        'sitting at wooden student desk, head gently bowed down, writing attentively in a notebook with pen',
        'medium close-up'
    ),
    # 2. Nhìn ra ngoài cửa sổ
    (
        r'(?:nhìn|ngắm|hướng mắt|dõi theo)\s*(?:ra|qua)?\s*(?:cửa sổ|bầu trời|mây)',
        'sitting beside the large classroom window, cheek resting on palm, gazing pensively through the glass at sky',
        'medium shot'
    ),
    # 3. Quay sang nói chuyện với bạn cùng bàn
    (
        r'(?:quay|ngoảnh|xoay)\s*(?:người|lại|sang)\s*(?:nhìn|cười|nói|hỏi|trò chuyện)',
        'turning slightly in chair toward desk mate, gentle warm smile, engaging direct eye contact',
        'over-the-shoulder shot'
    ),
    # 4. Đứng bật dậy, đập bàn (Strict physical action; removes internal feeling 'kinh ngạc' and standalone thoughts)
    (
        r'(?:đứng\s*bật\s*dậy|đập\s*tay\s*(?:xuống)?\s*bàn)',
        'standing up abruptly from desk, hands braced against wooden desktop, wide eyes with sudden realization',
        'dramatic low angle'
    ),
    # 5. Bước vào lớp học, mở cửa
    (
        r'(?:bước\s*vào|mở\s*cửa|đứng\s*ở\s*cửa)\s*(?:lớp|phòng)',
        'standing in the open sliding classroom doorway, holding school backpack strap, stepping inside',
        'wide establishing shot'
    ),
    # 6. Gục đầu xuống bàn (Requires pairing 'thở dài' with gục, bàn, nằm)
    (
        r'(?:gục đầu|úp mặt|nằm gục)\s*(?:xuống)?\s*(?:bàn)?|(?:thở dài)\s*(?:[\w\s]{0,15})\b(?:gục|bàn|nằm)\b|\b(?:gục|bàn|nằm)\b\s*(?:[\w\s]{0,15})\b(?:thở dài)\b',
        'resting head down on folded arms upon wooden desk, soft melancholic expression, delicate hair framing face',
        'close-up'
    ),
    # 7. Chuyền giấy, đưa đồ vật
    (
        r'(?:chuyền|đưa|trao|gửi)\s*(?:tờ giấy|mẩu tin|cuốn vở|cây bút|mẩu giấy)',
        'hand delicately passing a small folded note across the wooden desk space toward classmate',
        'tight focus on hands and note'
    ),
    # 8. Nhìn lên bảng đen
    (
        r'(?:nhìn|ngước|chú ý)\s*(?:lên)?\s*(?:bảng đen|bài giảng|thầy|cô)',
        'looking forward toward the classroom blackboard, attentive expression, sitting upright at desk',
        'medium shot'
    ),
]

def extract_action_from_prose(dialogue_or_prose: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts physical character gesture and camera angle from Vietnamese narrative prose or dialogue.
    Enforces strict negation checking across all pattern matches to eliminate action hallucinations.
    """
    if not dialogue_or_prose:
        return None, None
    text_lower = str(dialogue_or_prose).lower()
    for pattern, action_en, suggested_shot in ACTION_GESTURE_MAPPINGS:
        for m in re.finditer(pattern, text_lower):
            if not is_action_negated(text_lower, m.start()):
                return action_en, suggested_shot
    return None, None


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
    vn_particles = r'(?:sẽ|(?<!chờ\s)đã|đang|sắp|rất|quá|lắm|thực|thật|cực|cũng|vẫn|cứ|đều|lại|vừa|mới|hãy|đừng|chớ|bị|được|bởi|do|tại|vì|để|cho|với|cùng|và|hay|hoặc|của|ở|từ|lên|xuống|ra|vào)'
    s = re.sub(r'(?i)\b(' + vn_particles + r')\s*(?:-\s*|\.{2,3}\s*|(?:\s*\.\s*){2,3})', r'\1 ', s)

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

    def is_dialogue_unit(u: str) -> bool:
        return bool(re.search(r'["“”—\-]|:\s*["“]', u)) or u.startswith('-') or u.startswith('—')

    beats = []
    for para in paragraphs:
        raw_sentences = sentence_split_regex.split(para)
        para_units = []
        for s in raw_sentences:
            s_clean = s.strip()
            if s_clean and re.search(r'[\w\dÀ-ỹ]', s_clean):
                para_units.append(s_clean)

        if not para_units:
            continue

        curr_beat = []
        curr_len = 0
        for unit in para_units:
            unit_is_dialogue = is_dialogue_unit(unit)
            has_action = bool(extract_action_from_prose(unit)[0])

            if curr_beat:
                curr_has_dialogue = any(is_dialogue_unit(s) for s in curr_beat)
                curr_has_action = any(bool(extract_action_from_prose(s)[0]) for s in curr_beat)
                should_break = (
                    len(curr_beat) >= 3 or
                    (unit_is_dialogue != curr_has_dialogue) or
                    (has_action and curr_has_action) or
                    (curr_len + len(unit) > 200)
                )
                if should_break:
                    b_text = sanitize_complete_dialogue(" ".join(curr_beat).strip())
                    if b_text:
                        beats.append(b_text)
                    curr_beat = []
                    curr_len = 0
            curr_beat.append(unit)
            curr_len += len(unit)

        if curr_beat:
            b_text = sanitize_complete_dialogue(" ".join(curr_beat).strip())
            if b_text:
                beats.append(b_text)

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

        # Step 1: Query Dynamic Scene-Graph Ontology (DSGO) from StoryMemory
        dsg = getattr(memory, "dynamic_scene_graph", None) or getattr(memory, "scene_graph", None) if memory else None
        if dsg and hasattr(dsg, "entities") and dsg.entities:
            prior_context = "PRIOR KNOWN CHARACTERS FROM DYNAMIC SCENE GRAPH (DSGO):\n"
            for ent_id, ent in dsg.entities.items():
                c_name = getattr(ent, "name", ent_id)
                c_app = getattr(ent, "visual_dna", "") or getattr(ent, "dna", "")
                c_role_val = getattr(ent, "role", "supporting")
                c_role = str(getattr(c_role_val, "value", c_role_val)).lower()
                c_gender = str(getattr(ent, "gender", "unknown")).lower()
                prior_context += f"- {c_name} ({c_role}): {c_app}\n"

                name_lower = c_name.lower().strip()
                alias_set = {name_lower}
                if hasattr(ent, "aliases") and ent.aliases:
                    for a in ent.aliases:
                        a_str = str(a).strip().lower()
                        if a_str:
                            alias_set.add(a_str)
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

        # Step 2: Graceful fallback to StoryBible characters if DSGO entities absent
        elif memory and memory.story_bible and memory.story_bible.characters:
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
                    for parsed_name, parsed_value in parsed.items():
                        if isinstance(parsed_value, dict):
                            parsed_entry = parsed_value
                        elif isinstance(parsed_value, str):
                            alias_tokens = [parsed_name.lower()] + [
                                part.lower() for part in parsed_name.split() if len(part) > 1
                            ]
                            parsed_entry = {
                                "dna": parsed_value,
                                "aliases": alias_tokens,
                                "gender": "unknown",
                                "role": "supporting",
                            }
                        else:
                            continue

                        parsed_aliases = parsed_entry.get("aliases", [])
                        if isinstance(parsed_aliases, str):
                            parsed_aliases = [parsed_aliases]
                        parsed_aliases = [str(alias) for alias in parsed_aliases if str(alias).strip()]

                        parsed_name_key = str(parsed_name).strip().casefold()
                        canonical_name = next(
                            (
                                name for name, entry in existing_dna.items()
                                if parsed_name_key == name.casefold()
                                or parsed_name_key in {
                                    str(alias).strip().casefold()
                                    for alias in (entry.get("aliases", []) if isinstance(entry, dict) else [])
                                }
                            ),
                            None,
                        )
                        if canonical_name is None:
                            existing_dna[parsed_name] = {
                                **parsed_entry,
                                "aliases": parsed_aliases,
                            }
                            continue

                        # Story-memory DNA is authoritative; the extractor may
                        # only fill missing traits or add useful aliases.
                        canonical_entry = existing_dna[canonical_name]
                        aliases = list(canonical_entry.get("aliases", []))
                        for alias in parsed_aliases:
                            if alias.casefold() not in {str(item).casefold() for item in aliases}:
                                aliases.append(alias)
                        canonical_entry["aliases"] = aliases
                        if not str(canonical_entry.get("dna", "")).strip():
                            canonical_entry["dna"] = parsed_entry.get("dna", "")
                        if str(canonical_entry.get("gender", "")).lower() in ("", "unknown"):
                            canonical_entry["gender"] = parsed_entry.get("gender", "unknown")
                        if not str(canonical_entry.get("role", "")).strip():
                            canonical_entry["role"] = parsed_entry.get("role", "supporting")
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

        # Step 1: Query Dynamic Scene-Graph Ontology (DSGO) active SpaceEnclosure
        dsg = getattr(memory, "dynamic_scene_graph", None) or getattr(memory, "scene_graph", None) if memory else None
        if dsg and hasattr(dsg, "get_active_enclosure"):
            active_enc = dsg.get_active_enclosure()
            if active_enc:
                loc_name = getattr(active_enc, "name", "Bối cảnh chính")
                anchor = ""
                if hasattr(active_enc, "architectural_anchor") and active_enc.architectural_anchor:
                    anchor = active_enc.architectural_anchor
                elif hasattr(active_enc, "build_enclosure_fragment"):
                    anchor = active_enc.build_enclosure_fragment()

                atmosphere = getattr(active_enc, "lighting_atmosphere", "") or "atmospheric manga screentone background"

                existing_setting["location_name"] = loc_name
                existing_setting["setting_anchor"] = anchor or loc_name
                existing_setting["atmosphere"] = atmosphere

                if hasattr(active_enc, "persistent_fixtures") and active_enc.persistent_fixtures:
                    existing_setting["persistent_fixtures"] = list(active_enc.persistent_fixtures)
                if hasattr(active_enc, "negative_drift_tokens") and active_enc.negative_drift_tokens:
                    existing_setting["forbidden_spatial_tokens"] = list(active_enc.negative_drift_tokens)
                if hasattr(dsg, "get_combined_negative_tokens"):
                    existing_setting["quarantine_negative_tokens"] = dsg.get_combined_negative_tokens()

        # Step 2: Graceful fallback to StoryBible world_setting if DSGO setting absent
        if not existing_setting and memory and memory.story_bible and memory.story_bible.world_setting:
            existing_setting["location_name"] = "Bối cảnh chính"
            existing_setting["setting_anchor"] = memory.story_bible.world_setting
            existing_setting["atmosphere"] = "atmospheric manga screentone background"

        try:
            sample_text = story_text[:3500]
            canonical_context = (
                "CANONICAL STORY SETTING DNA (preserve its known location and anchor):\n"
                f"{json.dumps(existing_setting, ensure_ascii=False)}\n\n"
                if existing_setting else ""
            )
            resp = self.llm.chat(
                messages=[
                    {"role": "system", "content": SETTING_EXTRACTOR_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"{canonical_context}Extract Primary Spatial Setting DNA for this story:\n\n"
                            f"{sample_text}"
                        ),
                    }
                ],
                temperature=0.2,
                max_tokens=800
            )
            cleaned = re.sub(r'```(?:json)?\s*', '', resp).strip()
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    for key, value in parsed.items():
                        if key not in existing_setting or not existing_setting[key]:
                            existing_setting[key] = value
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

    def _validate_panels(
        self,
        script_data,
        character_dna_map=None,
        setting_dna=None,
        cultural_tier: Optional[int] = None,
        narrative_mode: Optional[str] = None
    ):
        """Validate, normalize layout, enforce character visual DNA, background anchor, and complete dialogue."""
        if not isinstance(script_data, list):
            raise ValueError("Output is not a JSON array")

        dna_map = character_dna_map or {}
        setting_anchor = ""
        tier = cultural_tier or (setting_dna.get("cultural_tier") if isinstance(setting_dna, dict) else None)
        mode = narrative_mode or (setting_dna.get("narrative_mode") if isinstance(setting_dna, dict) else None)

        if setting_dna and isinstance(setting_dna, dict):
            setting_anchor = setting_dna.get("setting_anchor", "").strip()

        enclosure = resolve_spatial_enclosure("", setting_dna=setting_dna, cultural_tier=tier, narrative_mode=mode)
        if not setting_anchor:
            setting_anchor = enclosure["anchor_description"]

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

        # Feature 17: Map first-person pronouns ("tôi", "mình", "I", "me") to lead protagonist
        # The first character in dna_map is assumed to be the lead/POV character
        if char_entry_list:
            lead = char_entry_list[0]
            first_person_aliases = [
                "tôi", "mình", "ta", "tớ",  # Vietnamese first-person
                "I", "me", "my", "myself",    # English first-person
            ]
            existing_aliases = set(a.lower() for a in lead["aliases"])
            for fp in first_person_aliases:
                if fp.lower() not in existing_aliases:
                    lead["aliases"].append(fp)

        # Sequential panel character memory is only used when a panel depicts a person.
        last_active_chars = []
        human_indicators = [
            "girl", "boy", "student", "man", "woman", "person", "character", "face",
            "sitting", "standing", "looking", "staring", "writing", "holding", "talking",
            "crying", "walking", "running", "người", "nhân vật", "khuôn mặt", "bước", "đứng", "ngồi", "nhìn"
        ]

        validated = []
        for i, item in enumerate(script_data):
            raw_prompt = str(item.get("image_prompt") or "a detailed manga scene").strip()
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

            # Choose the setting for this panel, rather than applying one global background.
            panel_enclosure = resolve_spatial_enclosure(
                f"{raw_prompt} {dialogue}",
                setting_dna=setting_dna,
                cultural_tier=tier,
                narrative_mode=mode
            )
            panel_setting_anchor = setting_anchor
            if panel_enclosure.get("key") != enclosure.get("key"):
                panel_setting_anchor = panel_enclosure.get("anchor_description", setting_anchor)

            # Step 1: Spatial Quarantine Filter - strip tokens that conflict with this panel's location.
            clean_prompt = sanitize_spatial_prompt(raw_prompt, panel_enclosure)
            if not clean_prompt:
                clean_prompt = "sitting quietly in classroom"

            # Step 2: Semantic Action & Gesture Extraction from Prose/Dialogue
            action_desc, suggested_shot = extract_action_from_prose(f"{dialogue} {raw_prompt}")

            # Step 3: Smart Character DNA matching
            search_text = f"{clean_prompt} {dialogue}"
            has_human = any(
                re.search(rf"(?<!\w){re.escape(indicator)}(?!\w)", clean_prompt, re.IGNORECASE)
                for indicator in human_indicators
            )
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
                female_cues = [
                    "girl", "woman", "schoolgirl", "female", "she", "her", "cô gái", "cô bé", "nữ sinh", "nữ", "nàng", "chị", "em gái"
                ]
                male_cues = [
                    "boy", "man", "schoolboy", "male", "he", "his", "him", "chàng trai", "cậu bé", "nam sinh", "nam", "anh", "cậu"
                ]

                # Fallback only triggers if visual prompt depicts a human figure/action
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

            # Step 4: Sequential Panel Character Memory
            # If no characters matched in current panel, carry forward from previous panel
            if not matched_chars and last_active_chars and has_human:
                matched_chars = list(last_active_chars)  # inherit from previous panel

            # Update sequential memory with current panel's characters
            if matched_chars and has_human:
                last_active_chars = list(matched_chars)

            # Step 4b: Inject Character Visual DNA for ALL matched characters
            injected_dnas = []
            for c in matched_chars:
                c_dna = c["dna"].strip()
                if c_dna and c_dna.lower() not in clean_prompt.lower():
                    injected_dnas.append(c_dna)

            # Step 5 & 6: CLIP 77-Token Budget Prioritization
            # Order: Character Visual DNA FIRST -> Core Action -> Setting Anchor -> Scene Nuances
            # Character DNA at Position 1 (tokens ~15-42) ensures face/hair/outfit consistency
            # across all panels, as CLIP strongly weights early tokens.
            prompt_components = []

            # Component 1: Character Visual DNA (Position 1, tokens ~15-42) — HIGHEST PRIORITY
            if injected_dnas:
                prompt_components.append(", ".join(injected_dnas))

            # Component 2: Core Action Gesture (tokens ~42-55)
            if action_desc and action_desc.lower() not in clean_prompt.lower():
                prompt_components.append(action_desc)

            # Component 3: Spatial Enclosure Anchor (tokens ~55-70)
            if panel_setting_anchor and panel_setting_anchor.lower() not in clean_prompt.lower():
                prompt_components.append(f"setting: {panel_setting_anchor}")

            # Component 4: Remaining Scene / Camera Shot Nuances (tokens ~70-77+)
            if clean_prompt:
                prompt_components.append(clean_prompt)

            assembled_prompt = ", ".join(prompt_components)

            # Clean duplicate style tags
            for tag in ["manga panel", "black and white", "monochrome", "screentone", "comic art"]:
                assembled_prompt = re.sub(rf'\b{re.escape(tag)}\b', "", assembled_prompt, flags=re.IGNORECASE)

            # Clean duplicate commas and normalize whitespace
            assembled_prompt = re.sub(r'[,.\s]*,[,.\s]*', ', ', assembled_prompt).strip(' ,.-')

            final_prompt = f"{STYLE_PREFIX}{assembled_prompt}{STYLE_SUFFIX}"

            raw_layout = str(item.get("layout_type") or "square").lower().strip()
            normalized_layout = LAYOUT_MAP.get(raw_layout, "square")

            panel_entry = {
                "panel_index": i + 1,
                "image_prompt": final_prompt,
                "dialogue_text": dialogue,
                "layout_type": normalized_layout
            }

            if tier in (1, 2) or (mode and str(mode).lower() in ("chinh_su", "da_su", "strict_historical", "historical_fiction")):
                panel_entry["negative_prompt"] = MASTER_NEGATIVE_VIETNAMESE
                panel_entry["master_negative"] = MASTER_NEGATIVE_VIETNAMESE
                panel_entry["cultural_tier"] = tier or 1
            elif tier == 3:
                panel_entry["cultural_tier"] = 3

            validated.append(panel_entry)
        return validated

    def generate_comic_script(
        self,
        story_text: str,
        memory: StoryMemory = None,
        cultural_tier: Optional[int] = None,
        narrative_mode: Optional[str] = None
    ) -> list:
        """
        Adapts the story text into a beat-by-beat sequential manga storyboard.
        Produces detailed sequential panels closely tracking every dialogue and action beat.
        """
        print(f"[Comic] Generating beat-by-beat storyboard for {len(story_text)} chars...")
        c_tier = cultural_tier
        n_mode = narrative_mode
        if memory and memory.story_bible:
            if c_tier is None:
                c_tier = getattr(memory.story_bible, "cultural_tier", None)
            if n_mode is None:
                n_mode = getattr(memory.story_bible, "narrative_mode", None)

        character_dna = self.extract_character_dna(story_text, memory=memory)
        setting_dna = self.extract_setting_dna(story_text, memory=memory)
        if c_tier is not None and isinstance(setting_dna, dict):
            setting_dna["cultural_tier"] = c_tier
        if n_mode is not None and isinstance(setting_dna, dict):
            setting_dna["narrative_mode"] = n_mode

        dna_context = _format_character_dna_registry(character_dna)
        setting_context = (
            f"Location: {setting_dna.get('location_name', 'Main Setting')}\n"
            f"Anchor: {setting_dna.get('setting_anchor', '')}\n"
            f"Persistent fixtures: {', '.join(setting_dna.get('persistent_fixtures', []))}\n"
            f"Atmosphere: {setting_dna.get('atmosphere', '')}"
        )

        system_instruction = f"{BEAT_DIRECTOR_PROMPT}\n\nCHARACTER VISUAL REGISTRY (IMMUTABLE):\n{dna_context}\n\nSETTING VISUAL ANCHOR (IMMUTABLE):\n{setting_context}\n"

        words_count = len(story_text.split())
        target_min = max(8, min(16, words_count // 50))
        target_max = max(12, min(24, words_count // 30))

        user_content = f"""Adapt this Vietnamese story text into sequential manga panels beat-by-beat.
Treat the supplied character DNA registry and setting anchor as established story canon. Keep identities, appearance, costumes, location, and persistent fixtures consistent; do not invent replacements.
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
            validated_panels = self._validate_panels(
                panels_raw,
                character_dna_map=character_dna,
                setting_dna=setting_dna,
                cultural_tier=c_tier,
                narrative_mode=n_mode
            )
            print(f"[Comic] Successfully created {len(validated_panels)} detailed beat-by-beat panels with background & character consistency.")
            return validated_panels
        except Exception as e:
            print(f"[Comic] Storyboard LLM failed ({e}), creating structured beat fallback...")
            return self._create_structured_beat_fallback(story_text, character_dna, setting_dna)

    def generate_continuation(self, previous_summary: str, new_text: str, memory: StoryMemory = None) -> list:
        """Continues an existing comic with new sequential panels from newly added text."""
        character_dna = self.extract_character_dna(new_text, memory=memory)
        setting_dna = self.extract_setting_dna(new_text, memory=memory)
        dna_context = _format_character_dna_registry(character_dna)
        setting_context = (
            f"Location: {setting_dna.get('location_name', 'Main Setting')}\n"
            f"Anchor: {setting_dna.get('setting_anchor', '')}\n"
            f"Persistent fixtures: {', '.join(setting_dna.get('persistent_fixtures', []))}\n"
            f"Atmosphere: {setting_dna.get('atmosphere', '')}"
        )

        system_instruction = f"""{BEAT_DIRECTOR_PROMPT}

PREVIOUS COMIC PROGRESSION:
{previous_summary}

CHARACTER VISUAL REGISTRY (IMMUTABLE):
{dna_context}

SETTING VISUAL ANCHOR (IMMUTABLE):
{setting_context}
"""
        user_content = f"""Continue the comic from the previous progression with sequential panels adapting this new text beat-by-beat.
Treat the supplied character DNA registry and setting anchor as established story canon. Keep identities, appearance, costumes, location, and persistent fixtures consistent with earlier panels.
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

            action_desc, suggested_shot = extract_action_from_prose(beat)
            if action_desc:
                shot_desc = action_desc
            elif is_dialogue:
                shot_desc = "sitting at wooden desk, talking with expressive emotion"
            else:
                shot_desc = "sitting attentively in classroom, natural posture"

            scene_enclosure = resolve_spatial_enclosure(beat, setting_dna=setting_dna)
            scene_anchor = (
                scene_enclosure.get("anchor_description", bg_anchor)
                if scene_enclosure.get("key") != resolve_spatial_enclosure("", setting_dna=setting_dna).get("key")
                else bg_anchor
            )
            prompt = f"{lead_dna}, {shot_desc}, setting: {scene_anchor}"

            raw_panels.append({
                "panel_index": idx + 1,
                "image_prompt": prompt,
                "dialogue_text": beat,
                "layout_type": layout
            })

        return self._validate_panels(raw_panels, character_dna_map=character_dna, setting_dna=setting_dna)
