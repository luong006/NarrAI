import os
import json
import re
from typing import List, Tuple, Optional, Any
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

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


# STRICT style prefix and suffix to force Diffusion model attention to Authentic 2D Monochrome Anime Manga Lineart
STYLE_PREFIX = (
    "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, "
    "official anime comic art, sharp cel shaded line art, "
)
STYLE_SUFFIX = (
    ", clean G-pen ink lineart, authentic manga screentone shading, fine dot pattern tones, "
    "high contrast black ink on crisp white paper, pure monochrome, "
    "2D anime manga drawing, expressive anime character design, sharp contours, single panel composition, no realistic portrait"
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
BEAT_DIRECTOR_PROMPT = """You are a master manga director and storyboard artist specializing in cohesive sequential storytelling, strict character continuity, and expressive anime manga panel composition.

YOUR MISSION: Faithfully adapt the provided Vietnamese story text into EXACTLY 4 SEQUENTIAL, COHESIVE MANGA PANELS that tell a single, continuous, connected scene.

ABSOLUTE CRITICAL RULES FOR VISUAL & CHARACTER CONSISTENCY:
1. UNIFIED 2D ANIME MANGA ART STYLE:
   - All panels MUST be generated in pure 2D Japanese anime manga style with clean ink lineart, delicate screentone shading, and cel shading.
   - Absolutely NO realistic portraits, NO 3D, NO pencil sketch drawings, NO graphite portraits, NO collage or multi-frame layouts in a single panel.
2. STRICT CHARACTER CONTINUITY:
   - Identify the characters in the story (e.g. Duy, An, or the protagonist).
   - In `image_prompt`, EVERY panel featuring a character MUST use their EXACT same physical DNA description from the CHARACTER REGISTRY (exact face, hair style/color, age, and signature outfit).
   - NEVER switch outfits, hairstyles, or artistic styles between panels.
3. SCENE & ENVIRONMENT CONTINUITY:
   - The 4 panels MUST depict the sequential flow of the EXACT SAME story scene from the text (e.g. if it is a rainy night by the window with a contract, keep the rain on the window, the moody lighting, and the room environment consistent across all 4 panels).
   - Panel 1: Establishing scene & mood (wide/medium shot introducing the character in their environment).
   - Panel 2: Key action / gesture / focus (character holding document, looking intently, starting dialogue).
   - Panel 3: Emotional dialogue / reaction / rising drama (medium close-up of intense facial expression, interacting).
   - Panel 4: Impactful turning point / cliffhanger / resolution of this beat (dramatic angle, decisive posture, powerful closing thought).
4. COMPLETE DIALOGUE & CONTEXT SUBTITLE (VIETNAMESE):
   - NO TRUNCATION / NO ELLIPSES (...): Every dialogue and caption MUST be a complete, grammatically sound, expressive Vietnamese sentence ending with (.), (!), or (?).
   - If there is a speaker, format clearly as: `[Tên nhân vật]: "[Câu thoại trọn vẹn giàu cảm xúc]"` (e.g. `Duy: "Tôi đã ký tên trên tờ giấy, không còn đường quay lại."`).
   - If it is narrative description, provide a vivid, engaging narrator sentence (e.g. `Mưa rơi không ngớt bên ngoài khung cửa kính mờ, giam hãm mọi thanh âm trong sự tĩnh lặng nặng nề.`).
5. IMAGE PROMPT (ENGLISH):
   - Concise prompt under 55 words: `[Character Visual DNA], [Specific Action & Expression], [Environment details], [Camera framing], [2D manga lineart]`.
   - Never use "realistic", "pencil sketch", "portrait drawing", "multi-panel".

OUTPUT FORMAT:
Return ONLY a valid JSON array of 4 panel objects:
[
  {
    "panel_index": 1,
    "image_prompt": "young Vietnamese protagonist with neat dark hair and expressive dark eyes wearing casual jacket and white shirt, standing near large rain-streaked window looking out at gloomy storm, moody 2D anime manga screentone",
    "dialogue_text": "Mưa rơi không ngớt, từng giọt va vào kính mờ tạo thành bức tường âm thanh ngăn cách với thế giới bên ngoài.",
    "layout_type": "wide"
  },
  {
    "panel_index": 2,
    "image_prompt": "young Vietnamese protagonist with neat dark hair and expressive dark eyes wearing casual jacket and white shirt, sitting at wooden desk holding pen over a signed document with resolute focused gaze, medium shot 2D manga lineart",
    "dialogue_text": "Duy: \\\"Tôi đã ký tên trên tờ giấy, không còn đường quay lại.\\\"",
    "layout_type": "square"
  },
  {
    "panel_index": 3,
    "image_prompt": "young Vietnamese protagonist with neat dark hair and expressive dark eyes wearing casual jacket and white shirt, close-up intense profile view, sharp determined eyes, dramatic manga contrast",
    "dialogue_text": "Duy: \\\"Nếu không có tôi, họ sẽ không bao giờ biết được sự thật phía sau bóng tối này.\\\"",
    "layout_type": "square"
  },
  {
    "panel_index": 4,
    "image_prompt": "young Vietnamese protagonist with neat dark hair and expressive dark eyes wearing casual jacket and white shirt, standing tall against the night window, clenching fist with unyielding resolve, dramatic low angle 2D manga",
    "dialogue_text": "Duy: \\\"Dù phải trả bất cứ giá nào, tôi cũng sẽ đi đến cùng con đường đã chọn!\\\"",
    "layout_type": "tall"
  }
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
        dynamic_anchor = sdna.get("setting_anchor") or "detailed atmospheric story setting"
        matched_enc = {
            "key": "dynamic_scene",
            "detection_keywords": [],
            "anchor_description": dynamic_anchor,
            "forbidden_spatial_tokens": sdna.get("forbidden_spatial_tokens", [])
        }

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
    Strips conflicting keywords for specific enclosures while strictly preserving valid subwords.
    Handles modifiers, prepositions, irregular plurals, and collapses consecutive commas cleanly.
    """
    if not prompt or not isinstance(prompt, str):
        return ""
    if enclosure is None or enclosure.get("key") == "dynamic_scene":
        # Keep clean story tokens for dynamic scenes
        return re.sub(r'[,.\s]*,[,.\s]*', ', ', prompt).strip(' ,.-')

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
    """
    pre_text = text[:match_start]
    clause_parts = re.split(CLAUSE_DELIMITERS_PATTERN, pre_text, flags=re.IGNORECASE)
    immediate_clause = clause_parts[-1] if clause_parts else ""
    words = re.findall(r'\b\w+\b', immediate_clause.lower())
    window_words = words[-6:] if len(words) > 6 else words
    return any(w in VIETNAMESE_NEGATION_WORDS for w in window_words)

# ==================== ACTION & GESTURE SEMANTIC MAPPING ====================
ACTION_GESTURE_MAPPINGS = [
    # 1. Ký tên, viết lách, làm việc với giấy tờ / tài liệu
    (
        r'(?:cúi đầu|cặm cụi|chăm chú|ký tên|ký|đặt bút)\s*(?:[\w\s]{0,15})\b(?:viết|chép|ghi|giấy|văn bản|hợp đồng|tờ giấy|bản cam kết|bút)\b',
        'holding pen attentively, writing or signing signature on paper document with serious focused gaze',
        'medium close-up'
    ),
    # 2. Nhìn ra ngoài cửa sổ, ngắm mưa, nhìn bầu trời
    (
        r'(?:nhìn|ngắm|hướng mắt|dõi theo)\s*(?:ra|qua)?\s*(?:cửa sổ|bầu trời|mây|mưa|màn đêm)',
        'standing or sitting near window, looking out through glass at the weather, contemplative dramatic mood',
        'medium shot'
    ),
    # 3. Quay sang nói chuyện, biểu cảm đối thoại
    (
        r'(?:quay|ngoảnh|xoay)\s*(?:người|lại|sang)\s*(?:nhìn|cười|nói|hỏi|trò chuyện)',
        'turning toward companion with expressive engaged reaction, dramatic anime dialogue pose',
        'over-the-shoulder shot'
    ),
    # 4. Đứng bật dậy, quả quyết, kiên định
    (
        r'(?:đứng\s*bật\s*dậy|đập\s*tay|nắm\s*chặt\s*tay|kiên\s*quyết|dứt\s*khoát)',
        'standing tall with resolute posture, clenched fist, intense determined gaze',
        'dramatic low angle'
    ),
    # 5. Bước vào phòng, mở cửa
    (
        r'(?:bước\s*vào|mở\s*cửa|đứng\s*ở\s*cửa)\s*(?:phòng|nhà|sảnh)',
        'stepping forward through doorway into room, dynamic entrance posture',
        'wide establishing shot'
    ),
    # 6. Suy tư, dằn vặt, thở dài
    (
        r'(?:gục đầu|úp mặt|thở dài|dằn vặt|trầm ngâm|suy tư)',
        'lowered head in deep contemplation, conflicted emotional expression, moody shadows',
        'close-up'
    ),
    # 7. Đưa đồ vật, trao đổi tài liệu
    (
        r'(?:chuyền|đưa|trao|gửi|cầm)\s*(?:tờ giấy|hồ sơ|tài liệu|vật|bức thư|chìa khóa)',
        'holding and extending document with focused hand gesture',
        'tight focus on hands and object'
    ),
    # 8. Ánh mắt kiên định, trực diện cao trào
    (
        r'(?:ánh mắt|nhìn thẳng|quyết tâm|không lùi bước|đối mặt)',
        'intense profile close-up, sharp piercing eyes, dramatic black and white manga screentone contrast',
        'dramatic close-up'
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


def infer_fallback_character_dna(story_text: str) -> dict:
    """Dynamically infer authentic character DNA from Vietnamese story context without modern classroom bias."""
    text_lower = str(story_text).lower()

    # 1. Legendary & Historical figures
    if any(k in text_lower for k in ["thánh gióng", "phù đổng", "ngựa sắt", "roi sắt", "bụi tre"]):
        return {
            "Thánh Gióng": {
                "gender": "male",
                "role": "lead",
                "dna": "heroic legendary Vietnamese youth Thánh Gióng, powerful stature, wearing ancient iron battle armor and headband, fierce heroic eyes, wielding iron rod or bamboo clump",
                "aliases": ["thánh gióng", "gióng", "phù đổng thiên vương", "cậu bé", "chàng trai", "tráng sĩ", "nghĩa sĩ"]
            }
        }
    if any(k in text_lower for k in ["an dương vương", "âu lạc", "cổ loa", "nỏ thần"]):
        return {
            "An Dương Vương": {
                "gender": "male",
                "role": "lead",
                "dna": "legendary Vietnamese King An Dương Vương, stately regal presence, royal Đại Việt imperial headband and embroidered robes, majestic resolute expression",
                "aliases": ["an dương vương", "nhà vua", "vua", "bệ hạ", "thục phán"]
            }
        }
    if any(k in text_lower for k in ["trần hưng đạo", "trần quốc tuấn", "vạn kiếp", "bạch đằng"]):
        return {
            "Trần Hưng Đạo": {
                "gender": "male",
                "role": "lead",
                "dna": "venerable Đại Việt supreme commander Trần Hưng Đạo, weathered noble warrior face, sharp tactical gaze, wearing medieval Vietnamese general battle armor and flowing cape",
                "aliases": ["trần hưng đạo", "quốc công tiết chế", "tiết chế", "hưng đạo vương", "tướng quân", "chủ tướng"]
            }
        }
    if any(k in text_lower for k in ["quang trung", "nguyễn huệ", "tây sơn", "đống đa"]):
        return {
            "Quang Trung": {
                "gender": "male",
                "role": "lead",
                "dna": "emperor Quang Trung Nguyễn Huệ, fierce commanding warrior king, wearing battle-tested royal armor and crimson cloak, resolute fiery eyes",
                "aliases": ["quang trung", "nguyễn huệ", "bắc bình vương", "vua quang trung", "hoàng đế"]
            }
        }
    if any(k in text_lower for k in ["hai bà trưng", "trưng trắc", "mê linh"]):
        return {
            "Trưng Trắc": {
                "gender": "female",
                "role": "lead",
                "dna": "heroic Vietnamese warrior queen Trưng Trắc, commanding fearless gaze, wearing ancient bronze-age warrior queen battle attire with yellow sash, tied hair",
                "aliases": ["trưng trắc", "bà trưng", "nữ vương", "chủ tướng", "nàng"]
            }
        }
    if any(k in text_lower for k in ["sơn tinh", "thủy tinh", "tản viên"]):
        return {
            "Sơn Tinh": {
                "gender": "male",
                "role": "lead",
                "dna": "noble mountain deity Sơn Tinh, powerful physique, ancient Vietnamese chieftain attire with sacred feather ornaments, calm commanding presence",
                "aliases": ["sơn tinh", "tản viên", "chúa núi", "chàng"]
            }
        }
    if any(k in text_lower for k in ["tấm cám", "cô tấm", "nàng tấm"]):
        return {
            "Tấm": {
                "gender": "female",
                "role": "lead",
                "dna": "gentle beautiful Vietnamese folk maiden Tấm, kind dark eyes, wearing traditional rural Áo Tứ Thân with dark scarf and graceful belt, modest rustic grace",
                "aliases": ["tấm", "cô tấm", "nàng tấm", "cô gái", "nàng", "cô bé"]
            }
        }
    if any(k in text_lower for k in ["thạch sanh", "chằn tinh"]):
        return {
            "Thạch Sanh": {
                "gender": "male",
                "role": "lead",
                "dna": "brave Vietnamese folk hero Thạch Sanh, muscular woodcutter physique, simple loincloth and fabric wrap, wielding wooden axe or mythical bow, fearless honest eyes",
                "aliases": ["thạch sanh", "chàng", "người dũng sĩ", "chàng trai"]
            }
        }

    # 2. General Historical / Folklore Context
    hist_cues = ["vua", "tướng", "quân", "giặc", "chiến thuyền", "sa trường", "triều đình", "hoàng cung", "đại việt", "chúa", "thần", "đền", "thôn dã"]
    if any(k in text_lower for k in hist_cues):
        is_female = any(k in text_lower for k in ["nàng", "cô gái", "công chúa", "hoàng hậu", "thiếu nữ", "bà"])
        if is_female:
            return {
                "Nữ nhân vật": {
                    "gender": "female",
                    "role": "lead",
                    "dna": "Vietnamese historical maiden, elegant posture, gentle expressive dark eyes, wearing traditional Áo Ngũ Thân or Áo Tứ Thân with tied hair",
                    "aliases": ["nàng", "tiểu thư", "cô gái", "nữ nhân", "người", "she"]
                }
            }
        return {
            "Nhân vật lịch sử": {
                "gender": "male",
                "role": "lead",
                "dna": "heroic Vietnamese historical figure, determined sharp gaze, wearing traditional Đại Việt historical robes or warrior armor with tied sash",
                "aliases": ["chàng", "tướng quân", "nghĩa sĩ", "người", "chàng trai", "he"]
            }
        }

    # 3. Modern School / Slice of Life
    if any(k in text_lower for k in ["lớp", "học sinh", "trường học", "thầy giáo", "cô giáo", "bảng đen", "tiết học"]):
        return {
            "Học sinh": {
                "gender": "unknown",
                "role": "lead",
                "dna": "young Vietnamese student, neat dark hair, expressive dark eyes, wearing clean school uniform with white collared shirt",
                "aliases": ["học sinh", "bạn học", "cậu bé", "cô bé", "cậu ấy", "cô ấy", "nam sinh", "nữ sinh", "protagonist"]
            }
        }

    # 4. Contemporary / Open Drama Default
    return {
        "Nhân vật chính": {
            "gender": "unknown",
            "role": "lead",
            "dna": "young Vietnamese protagonist, neat dark hair, expressive dark eyes, wearing casual modern attire (jacket over collared shirt), natural posture",
            "aliases": ["nhân vật chính", "người", "chàng trai", "cô gái", "tôi", "mình", "cậu ấy", "cô ấy", "protagonist"]
        }
    }


def infer_fallback_setting_dna(story_text: str) -> dict:
    """Dynamically infer authentic setting anchor from Vietnamese story context without classroom bias."""
    text_lower = str(story_text).lower()

    if any(k in text_lower for k in ["bạch đằng", "chiến trận", "chiến thuyền", "bãi cọc", "sa trường", "sông", "giặc"]):
        return {
            "location_name": "Chiến trường lịch sử Việt Nam",
            "setting_anchor": "historic Vietnamese battlefield along the river, wooden stakes rising from swirling waters, historic battle boats, fluttering war banners, dynamic manga ink lineart",
            "atmosphere": "epic dramatic historical battlefield screentone with wind and smoke"
        }
    if any(k in text_lower for k in ["hoàng cung", "kinh thành", "thăng long", "cung điện", "ngai vàng", "triều đình"]):
        return {
            "location_name": "Hoàng thành Đại Việt",
            "setting_anchor": "grand historic Đại Việt imperial palace hall, carved wooden pillars, ornate dragon motifs, solemn royal court architecture",
            "atmosphere": "majestic solemn imperial manga screentone"
        }
    if any(k in text_lower for k in ["làng", "cây đa", "bến nước", "mái đình", "thôn", "đồng ruộng", "bờ tre"]):
        return {
            "location_name": "Làng quê truyền thống Việt Nam",
            "setting_anchor": "historic Vietnamese village, ancient mossy village gate, banyan tree by the river wharf, rustic thatched cottages and bamboo grove",
            "atmosphere": "peaceful nostalgic Vietnamese rural screentone"
        }
    if any(k in text_lower for k in ["núi", "rừng", "sơn tinh", "hang", "thác"]):
        return {
            "location_name": "Vùng rừng núi hùng vĩ",
            "setting_anchor": "majestic ancient Vietnamese mountain landscape, misty primeval forest, towering rocky crags, sacred natural aura",
            "atmosphere": "mystical legendary nature lineart"
        }
    if any(k in text_lower for k in ["lớp", "trường", "phòng học", "bảng đen"]):
        return {
            "location_name": "Lớp học",
            "setting_anchor": "bright high school classroom interior, neat student wooden desks, large chalkboard on front wall, window sunlight",
            "atmosphere": "peaceful youth school manga screentone"
        }

    return {
        "location_name": "Bối cảnh câu chuyện",
        "setting_anchor": "atmospheric narrative setting matching the scene, cinematic composition, authentic screentone textures",
        "atmosphere": "expressive high contrast manga screentone"
    }


def infer_fallback_action(beat: str, is_dialogue: bool = False) -> str:
    """Extract realistic physical gesture and posture from Vietnamese beat text."""
    b_lower = str(beat).lower()
    if any(w in b_lower for w in ["cưỡi", "phi", "ngựa"]):
        return "galloping forward heroically on steed with intense momentum, dramatic wide angle"
    if any(w in b_lower for w in ["nhổ", "tre", "gậy sắt", "vung"]):
        return "wielding weapon heroically with fierce strength, dynamic action manga lines"
    if any(w in b_lower for w in ["chém", "đánh", "tiêu diệt", "tấn công", "chiến đấu", "xông"]):
        return "lunging forward in fierce combat stance, dynamic motion blur and battle impact"
    if any(w in b_lower for w in ["bay", "lên trời", "biến mất"]):
        return "ascending gracefully into the open sky and clouds, awe-inspiring legendary farewell"
    if any(w in b_lower for w in ["quỳ", "lạy", "tạ ơn"]):
        return "kneeling solemnly with bowed head in profound reverence, emotional camera angle"
    if any(w in b_lower for w in ["khóc", "nước mắt", "đau đớn", "ngậm ngùi"]):
        return "tearful emotional face, hand clasped over chest, heart-wrenching close-up manga panel"
    if any(w in b_lower for w in ["cười", "vui mừng", "reo hò"]):
        return "joyful triumphant smile, arms raised in victory, uplifting manga screentone"
    if any(w in b_lower for w in ["bước", "đi", "tiến", "chạy"]):
        return "striding forward with resolute determination, dynamic diagonal perspective"
    if any(w in b_lower for w in ["nhìn", "trông", "quan sát", "hướng mắt"]):
        return "gazing resolutely into the distance, watchful focused expression, cinematic framing"
    if is_dialogue:
        return "speaking passionately with expressive emotion, intense facial reaction, dramatic angle"
    return "standing attentively in scene, focused posture engaged with the surroundings"


class ComicDirectorAgent:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY_COMIC") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Thiếu GROQ_API_KEY_COMIC hoặc GROQ_API_KEY")
        comic_model = os.environ.get("GROQ_MODEL_COMIC", "qwen/qwen3.8-27b")
        self.llm = GroqClient(model_name=comic_model, api_key=api_key)

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
            cleaned = re.sub(r'<think>.*?</think>', '', resp, flags=re.DOTALL).strip()
            cleaned = re.sub(r'```(?:json)?\s*', '', cleaned).strip()
            cleaned = re.sub(r'```', '', cleaned).strip()
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

        # Guaranteed rich dynamic fallback if nothing extracted
        if not existing_dna:
            existing_dna = infer_fallback_character_dna(story_text)

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
            cleaned = re.sub(r'<think>.*?</think>', '', resp, flags=re.DOTALL).strip()
            cleaned = re.sub(r'```(?:json)?\s*', '', cleaned).strip()
            cleaned = re.sub(r'```', '', cleaned).strip()
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
                existing_setting = infer_fallback_setting_dna(story_text)

        return existing_setting

    def _parse_json_array(self, raw_output):
        """Extract and parse a JSON array from LLM output."""
        if not raw_output or not isinstance(raw_output, str):
            raise ValueError("Empty LLM output")
        # Strip potential reasoning/thinking blocks
        cleaned = re.sub(r'<think>.*?</think>', '', raw_output, flags=re.DOTALL).strip()
        cleaned = re.sub(r'```(?:json)?\s*', '', cleaned).strip()
        cleaned = re.sub(r'```', '', cleaned).strip()
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

            # Pre-flight quality verification: if cultural tier is historical, purge accidental modern leaks
            is_historical = tier in (1, 2) or (mode and str(mode).lower() in ("chinh_su", "da_su", "strict_historical", "historical_fiction"))
            if is_historical:
                for modern_leak in ["school uniform", "schoolgirl", "schoolboy", "classroom", "student desk", "blackboard", "ribbon tie", "blazer", "modern jacket"]:
                    final_prompt = re.sub(rf'\b{re.escape(modern_leak)}\b', '', final_prompt, flags=re.IGNORECASE)
                final_prompt = re.sub(r'[,.\s]*,[,.\s]*', ', ', final_prompt).strip(' ,.-')

            raw_layout = str(item.get("layout_type") or "square").lower().strip()
            normalized_layout = LAYOUT_MAP.get(raw_layout, "square")

            scene_summary = dialogue or (narrator if narrator else clean_prompt[:120])
            char_names = [c["name"] for c in matched_chars] if matched_chars else ["Protagonist"]

            # Structured Scene Data Contract
            panel_entry = {
                "panel_index": i + 1,
                "scene_id": i + 1,
                "scene_summary": scene_summary,
                "characters": char_names,
                "setting": panel_setting_anchor or "atmospheric narrative setting",
                "action": action_desc or (infer_fallback_action(dialogue, is_dialogue=True) if dialogue else "standing attentively in scene"),
                "continuity": f"panel_{i}" if i > 0 else "initial_establishing_shot",
                "positive_prompt": final_prompt,
                "image_prompt": final_prompt,
                "dialogue_text": dialogue,
                "narrator_text": narrator,
                "layout_type": normalized_layout
            }

            if is_historical:
                panel_entry["negative_prompt"] = MASTER_NEGATIVE_VIETNAMESE
                panel_entry["master_negative"] = MASTER_NEGATIVE_VIETNAMESE
                panel_entry["cultural_tier"] = tier or 1
            elif tier == 3:
                panel_entry["cultural_tier"] = 3
                panel_entry["negative_prompt"] = "bad anatomy, blurry, low quality, color, 3d, realistic portrait, deformed limbs"
            else:
                panel_entry["negative_prompt"] = "bad anatomy, blurry, low quality, color, 3d, realistic portrait, deformed limbs"

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

        user_content = f"""Adapt this Vietnamese story text into EXACTLY 4 sequential manga panels beat-by-beat.
Treat the supplied character DNA registry and setting anchor as established story canon. Keep identities, appearance, costumes, location, and persistent fixtures consistent; do not invent replacements.
Structure the 4 panels with clear cinematic manga rhythm:
- Panel 1: Establishing wide or medium shot setting the mood, location, and initial tension.
- Panel 2: Key character focus / action / expressive dialogue.
- Panel 3: Rising drama or interaction between characters.
- Panel 4: Climax / cliffhanger / impactful transition of this scene beat.
DO NOT SKIP ANY CRITICAL ACTION OR DIALOGUE.
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
                max_tokens=2500
            )
            panels_raw = self._parse_json_array(response)
            validated_panels = self._validate_panels(
                panels_raw,
                character_dna_map=character_dna,
                setting_dna=setting_dna,
                cultural_tier=c_tier,
                narrative_mode=n_mode
            )
            final_panels = validated_panels[:4] if len(validated_panels) >= 4 else validated_panels
            print(f"[Comic] Successfully created {len(final_panels)} detailed 4-panel batch.")
            return final_panels
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
        user_content = f"""Continue the comic from the previous progression with EXACTLY 4 new sequential manga panels adapting this new text beat-by-beat.
Treat the supplied character DNA registry and setting anchor as established story canon. Keep identities, appearance, costumes, location, and persistent fixtures consistent with earlier panels.
Structure the 4 new panels sequentially (Panel 1 -> Panel 2 -> Panel 3 -> Panel 4).
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
                max_tokens=2500
            )
            panels_raw = self._parse_json_array(response)
            validated = self._validate_panels(panels_raw, character_dna_map=character_dna, setting_dna=setting_dna)
            final_panels = validated[:4] if len(validated) >= 4 else validated
            return final_panels
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

        if not character_dna:
            character_dna = infer_fallback_character_dna(story_text)
        if not setting_dna:
            setting_dna = infer_fallback_setting_dna(story_text)

        first_val = list(character_dna.values())[0] if character_dna else {}
        lead_dna = first_val.get("dna", first_val) if isinstance(first_val, dict) else str(first_val)
        bg_anchor = setting_dna.get("setting_anchor", "atmospheric narrative setting") if setting_dna else "atmospheric narrative setting"

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
            else:
                shot_desc = infer_fallback_action(beat, is_dialogue=is_dialogue)

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
            if len(raw_panels) >= 4:
                break

        validated = self._validate_panels(raw_panels, character_dna_map=character_dna, setting_dna=setting_dna)
        return validated[:4]
