"""
Adaptive Open-Ontology & 3 Narrative Modes Service for NarrAI.
Implements:
1. 3 Narrative Modes:
   - CHINH_SU (Strict Historical Authenticity)
   - DA_SU (Historical Fiction / Alternative Lens)
   - HU_CAU_TU_DO (Free Personal Fiction / Non-Historical)
2. HistoricalGroundingGatekeeper:
   - Authentic Vietnamese historical knowledge base (Hai Bà Trưng, Ngô Quyền, Lý Thường Kiệt,
     Trần Hưng Đạo, Lê Lợi, Quang Trung; Bạch Đằng, Như Nguyệt, Ngọc Hồi - Đống Đa).
   - In CHINH_SU mode, strictly prevents and rejects historical distortion.
3. TriTierOntologyResolver:
   - Cultural similarity scoring S_cult.
   - Tier 1: Canonical Vietnamese (>=0.7): Honorifics, cultural entities, traditional attire
     (Áo Ngũ Thân, Áo Nhật Bình, Áo Tấc, Khăn Đóng, Áo Bà Ba, Nón Lá), Master Negative (Hanfu, Kimono, Hanbok, Samurai, Ninja).
   - Tier 2: Cultural Fusion / Hybrid (0.3 <= S_cult < 0.7): Cyberpunk Thăng Long 2099, Steampunk Triều Nguyễn.
   - Tier 3: Open-Domain Adaptive Graph (S_cult < 0.3): Complete semantic relaxation, disables feudal filters.
4. SmartSelectiveLanguageFilter:
   - Suppresses Chinese translation clichés ("tiêu sái", "tà mị", "lãnh khốc", "bản tọa", "đế tôn") for pure VN/historical.
   - Selectively permits them when genre is Xianxia/Wuxia in Free Fiction mode.
5. extract_dynamic_ephemeral_node:
   - On-the-fly extraction of entities, spaces, and eras for Tier 3.
"""

import re
import uuid
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
from pydantic import BaseModel, Field


# ==============================================================================
# 1. ENUMS & DATA MODELS
# ==============================================================================

class NarrativeMode(str, Enum):
    CHINH_SU = "chinh_su"               # Mode 1: Strict Historical Authenticity
    DA_SU = "da_su"                     # Mode 2: Historical Fiction / Alternative Lens
    HU_CAU_TU_DO = "hu_cau_tu_do"       # Mode 3: Free Personal Fiction / Non-Historical

    # English / Code Interoperability Aliases
    STRICT_HISTORICAL = "chinh_su"
    HISTORICAL_FICTION = "da_su"
    FREE_FICTION = "hu_cau_tu_do"


class CulturalTier(int, Enum):
    TIER_1_CANONICAL_VN = 1     # S_cult >= 0.7
    TIER_2_CULTURAL_FUSION = 2   # 0.3 <= S_cult < 0.7
    TIER_3_OPEN_DOMAIN = 3       # S_cult < 0.3


def normalize_narrative_mode(val: Any) -> NarrativeMode:
    """Safely converts string or enum input into a canonical NarrativeMode."""
    if isinstance(val, NarrativeMode):
        return val
    if not val:
        return NarrativeMode.HU_CAU_TU_DO

    s = str(val).lower().strip()
    if s in ["chinh_su", "strict_historical", "chế độ 1", "chế độ chính sử", "chính sử", "mode 1", "mode_1"]:
        return NarrativeMode.CHINH_SU
    if s in ["da_su", "historical_fiction", "chế độ 2", "chế độ dã sử", "dã sử", "mode 2", "mode_2"]:
        return NarrativeMode.DA_SU
    return NarrativeMode.HU_CAU_TU_DO


def normalize_cultural_tier(val: Any) -> CulturalTier:
    """Safely converts integer or enum input into a canonical CulturalTier."""
    if isinstance(val, CulturalTier):
        return val
    try:
        ival = int(val)
        if ival in (1, 2, 3):
            return CulturalTier(ival)
    except (ValueError, TypeError):
        pass
    return CulturalTier.TIER_1_CANONICAL_VN


class ResolvedOntology(BaseModel):
    narrative_mode: NarrativeMode = NarrativeMode.HU_CAU_TU_DO
    cultural_tier: CulturalTier = CulturalTier.TIER_1_CANONICAL_VN
    cultural_similarity: float = 1.0
    tier_name: str = "Tier 1: Canonical Vietnamese Cultural Domain"
    positive_visual_dna: str = ""
    master_negative_filter: str = ""
    honorifics_guidelines: str = ""
    historical_constraints: str = ""
    era_anchor: str = ""
    spatial_anchor: str = ""


# ==============================================================================
# 2. VIETNAMESE HISTORICAL KNOWLEDGE BASE & GROUNDING GATEKEEPER
# ==============================================================================

# Core Vietnamese Historical Canon (Inviolable Truths)
VIETNAMESE_HISTORICAL_CANON = {
    "hai_ba_trung": {
        "names": ["hai bà trưng", "trưng trắc", "trưng nhị"],
        "era": "Thời kỳ Bắc thuộc lần 1 (Năm 40)",
        "enemies": ["tô định", "quân đông hán", "nhà hán"],
        "allies": ["thi sách", "lê chân", "thánh thiên", "bát nàn"],
        "invariants": [
            "Khởi nghĩa năm 40 giành lại 65 thành trì",
            "Đền nợ nước, trả thù nhà, đánh đuổi thái thú Tô Định",
            "Tuyệt đối không đầu hàng giặc ngoại xâm"
        ],
        "defeat_regex": r"(?i)\b(?:trưng\s+trắc|trưng\s+nhị|hai\s+bà\s+trưng)\b.*?\b(?:đầu\s+hàng|phản\s+bội|quy\s+hàng|bán\s+nước|thua\s+nhục|cầu\s+xin\s+tô\s+định)\b"
    },
    "ngo_quyen": {
        "names": ["ngô quyền", "tiền ngô vương"],
        "era": "Năm 938",
        "battle": "Bạch Đằng 938",
        "enemies": ["nam hán", "lưu hoằng tháo", "kiều công tiễn"],
        "invariants": [
            "Đóng cọc ngầm gỗ bọc sắt nhọn trên sông Bạch Đằng",
            "Chém chết chủ tướng Lưu Hoằng Tháo trên sông",
            "Đại thắng quân Nam Hán năm 938, chấm dứt hơn 1000 năm Bắc thuộc"
        ],
        "defeat_regex": r"(?i)\b(?:ngô\s+quyền|tiền\s+ngô\s+vương)\b.*?\b(?:bại\s+trận|thua\s+trận|đầu\s+hàng|bị\s+lưu\s+hoằng\s+tháo\s+(?:bắt|giết)|thất\s+bại\s+trên\s+sông\s+bạch\s+đằng)\b"
    },
    "ly_thuong_kiet": {
        "names": ["lý thường kiệt", "thái úy lý thường kiệt", "ngô tuấn"],
        "era": "Thời Lý (Thế kỷ 11)",
        "battle": "Phòng tuyến sông Như Nguyệt (1077)",
        "enemies": ["nhà tống", "quân tống", "quách quỳ", "triệu tiết"],
        "invariants": [
            "Tuyên ngôn độc lập 'Nam quốc sơn hà Nam đế cư'",
            "Xây dựng phòng tuyến vững chắc bên sông Như Nguyệt (sông Cầu)",
            "Đánh tan quân xâm lược nhà Tống, giữ vững nền độc lập Đại Việt"
        ],
        "defeat_regex": r"(?i)\b(?:lý\s+thường\s+kiệt)\b.*?\b(?:bại\s+trận|thua\s+trận|đầu\s+hàng\s+quân\s+tống|thua\s+quách\s+quỳ|bị\s+quân\s+tống\s+bắt|thất\s+bại\s+ở\s+như\s+nguyệt)\b"
    },
    "tran_hung_dao": {
        "names": ["trần hưng đạo", "trần quốc tuấn", "hưng đạo đại vương", "tiết chế quốc công"],
        "era": "Thời Trần (Thế kỷ 13)",
        "battle": "Bạch Đằng 1288, Vạn Kiếp, Hàm Tử, Chương Dương",
        "enemies": ["quân nguyên mông", "nguyên mông", "thoát hoan", "ô mã nhi", "phàn tiếp"],
        "invariants": [
            "Tác giả Hịch tướng sĩ, tuyên ngôn 'Nếu bệ hạ muốn hàng, xin hãy chém đầu thần trước'",
            "Chỉ huy quân dân Đại Việt 3 lần đại thắng quân Nguyên Mông",
            "Đại thắng trận Bạch Đằng 1288, bắt sống tướng giặc Ô Mã Nhi, Phàn Tiếp",
            "Thoát Hoan phải chui vào ống đồng trốn chạy về nước",
            "Tuyệt đối không bao giờ bại trận Bạch Đằng hay đầu hàng quân Nguyên"
        ],
        "defeat_regex": r"(?i)\b(?:trần\s+hưng\s+đạo|trần\s+quốc\s+tuấn|hưng\s+đạo\s+đại\s+vương)\b.*?\b(?:bại\s+trận|thua\s+trận|thua\s+cuộc|đầu\s+hàng|bị\s+bắt|chui\s+ống\s+đồng|bị\s+thoát\s+hoan\s+bắt|thất\s+bại\s+bạch\s+đằng|thua\s+quân\s+nguyên)\b"
    },
    "le_loi": {
        "names": ["lê lợi", "bình định vương", "lê thái tổ"],
        "era": "Khởi nghĩa Lam Sơn (1418 - 1427)",
        "battle": "Tốt Động - Chúc Động, Chi Lăng - Xương Giang",
        "enemies": ["quân minh", "nhà minh", "liễu thăng", "vương thông", "lương minh"],
        "invariants": [
            "Dấy binh khởi nghĩa Lam Sơn gian khổ 10 năm",
            "Gươm thần Thuận Thiên, Nguyễn Trãi viết Bình Ngô đại cáo",
            "Đại thắng Chi Lăng - Xương Giang, chém đầu Liễu Thăng",
            "Vương Thông xin hòa mở hội thề Đông Quan rút quân về nước",
            "Giành lại độc lập toàn vẹn non sông, lập nên triều Hậu Lê"
        ],
        "defeat_regex": r"(?i)\b(?:lê\s+lợi|bình\s+định\s+vương)\b.*?\b(?:bại\s+trận|thua\s+trận|đầu\s+hàng\s+quân\s+minh|bị\s+liễu\s+thăng\s+(?:bắt|giết)|thất\s+bại\s+hoàn\s+toàn)\b"
    },
    "quang_trung": {
        "names": ["quang trung", "nguyễn huệ", "bắc bình vương", "hoàng đế quang trung"],
        "era": "Khởi nghĩa Tây Sơn - Mùa xuân Kỷ Dậu 1789",
        "battle": "Ngọc Hồi - Đống Đa (Tết Kỷ Dậu 1789)",
        "enemies": ["quân thanh", "mãn thanh", "tôn sĩ nghị", "sầm nghi đống"],
        "invariants": [
            "Hành quân thần tốc từ Phú Xuân ra Thăng Long dịp Tết Kỷ Dậu 1789",
            "Chiến thuật công phá pháo đài rơm bện tẩm nước",
            "Đại phá 29 vạn quân Mãn Thanh tại Ngọc Hồi - Đống Đa mùng 5 Tết",
            "Tướng giặc Sầm Nghi Đống thắt cổ tự vẫn, Tôn Sĩ Nghị bỏ chạy qua sông Hồng",
            "Tuyệt đối không thất bại hay đầu hàng quân Thanh"
        ],
        "defeat_regex": r"(?i)\b(?:quang\s+trung|nguyễn\s+huệ|bắc\s+bình\s+vương)\b.*?\b(?:bại\s+trận|thua\s+trận|đầu\s+hàng\s+quân\s+thanh|thua\s+tôn\s+sĩ\s+nghị|thất\s+bại\s+ở\s+ngọc\s+hồi|thất\s+bại\s+ở\s+đống\s+đa)\b"
    }
}

# Major battles and general battle distortion checks
BATTLE_OUTCOME_DISTORTION_PATTERNS = [
    (r"(?i)\btrận\s+bạch\s+đằng\b.*?\b(?:quân\s+ta\s+thua|đại\s+việt\s+thất\s+bại|nguyên\s+mông\s+toàn\s+thắng|nam\s+hán\s+toàn\s+thắng)\b", "Xuyên tạc kết quả trận Bạch Đằng lịch sử."),
    (r"(?i)\btrận\s+như\s+nguyệt\b.*?\b(?:quân\s+ta\s+thua|đại\s+việt\s+thất\s+bại|nhà\s+tống\s+chiếm\s+thăng\s+long)\b", "Xuyên tạc kết quả trận chiến phòng tuyến Như Nguyệt."),
    (r"(?i)\btrận\s+(?:ngọc\s+hồi|đống\s+đa)\b.*?\b(?:quang\s+trung\s+thua|tây\s+sơn\s+thất\s+bại|quân\s+thanh\s+chiếm\s+giữ\s+vững)\b", "Xuyên tạc đại thắng Ngọc Hồi - Đống Đa 1789."),
    (r"(?i)\bkhởi\s+nghĩa\s+lam\s+sơn\b.*?\b(?:bị\s+quân\s+minh\s+tiêu\s+diệt\s+hoàn\s+toàn|lê\s+lợi\s+thất\s+bại\s+vĩnh\s+viễn)\b", "Xuyên tạc toàn thắng khởi nghĩa Lam Sơn.")
]


class HistoricalGroundingGatekeeper:
    """
    Enforces historical fidelity for Vietnamese historical narratives.
    In CHINH_SU mode: strictly rejects historical distortions, revisionism, and falsehoods.
    In DA_SU mode: preserves macro historical truths while allowing fictional personal micro-perspectives.
    In HU_CAU_TU_DO mode: completely bypassed.
    """

    @classmethod
    def validate_historical_invariants(cls, text: str, mode: NarrativeMode = NarrativeMode.CHINH_SU) -> Tuple[bool, List[str]]:
        """
        Validates text against Vietnamese historical invariants.
        Returns (is_valid, list_of_violations).
        """
        if mode == NarrativeMode.HU_CAU_TU_DO:
            return True, []

        if not text or not isinstance(text, str):
            return True, []

        violations = []

        # Check character-specific defeat / distortion patterns
        for key, canon in VIETNAMESE_HISTORICAL_CANON.items():
            pattern = canon.get("defeat_regex")
            if pattern and re.search(pattern, text, re.DOTALL):
                hero_name = canon["names"][0].title()
                violations.append(
                    f"HISTORICAL_VIOLATION: Phát hiện xuyên tạc hình tượng lịch sử anh hùng '{hero_name}'. "
                    f"Trong lịch sử dân tộc, {hero_name} luôn giữ vững khí tiết và giành chiến thắng vĩ đại."
                )

        # Check battle outcome distortions
        for pattern, desc in BATTLE_OUTCOME_DISTORTION_PATTERNS:
            if re.search(pattern, text, re.DOTALL):
                violations.append(f"HISTORICAL_VIOLATION: {desc}")

        is_valid = len(violations) == 0
        return is_valid, violations

    @classmethod
    def validate(cls, prompt: str, generated_text: str, mode: NarrativeMode = NarrativeMode.CHINH_SU) -> Tuple[bool, str]:
        """Interface contract validator returning (bool, error_message)."""
        combined = f"{prompt}\n{generated_text}"
        is_valid, violations = cls.validate_historical_invariants(combined, mode=mode)
        if not is_valid:
            return False, "; ".join(violations)
        return True, ""

    @classmethod
    def get_historical_grounding_prompt(cls, mode: NarrativeMode) -> str:
        """Constructs system prompt directives for LLM generation based on narrative mode."""
        if mode == NarrativeMode.CHINH_SU:
            return (
                "\n=== NGUYÊN TẮC BẤT BIẾN: CHÍNH SỬ & TÔN TRỌNG SỰ THẬT LỊCH SỬ (CHẾ ĐỘ 1) ===\n"
                "- Tác phẩm viết về sự kiện hoặc nhân vật lịch sử có thật của dân tộc Việt Nam.\n"
                "- BẮT BUỘC TUÂN THỦ TUYỆT ĐỐI niên đại, tiến trình chiến dịch và đại cục quốc gia.\n"
                "- TUYỆT ĐỐI CẤM 100% việc xuyên tạc lịch sử, đổi trắng thay đen (như: Trần Hưng Đạo bại trận Bạch Đằng,\n"
                "  Ngô Quyền thua quân Nam Hán, Quang Trung bại trận Ngọc Hồi, hoặc biến anh hùng dân tộc thành kẻ phản bội).\n"
                "- Xưng hô và phong thái chuẩn mực hoàng triều, quân ngũ Đại Việt thời phong kiến tương ứng.\n"
                "===============================================================================\n"
            )
        elif mode == NarrativeMode.DA_SU:
            return (
                "\n=== NGUYÊN TẮC BỐI CẢNH: DÃ SỬ & PHÓNG TÁC GÓC NHÌN CÁ NHÂN (CHẾ ĐỘ 2) ===\n"
                "- Bối cảnh thời đại, không khí văn hóa và các đại cục lịch sử là có thật (thời Lý, Trần, Lê, Tây Sơn...).\n"
                "- Nhân vật chính và cốt truyện vi mô là HƯ CẤU CÁ NHÂN (góc nhìn người lính vô danh, đôi lứa thời chiến...).\n"
                "- Cho phép tự do sáng tạo biến cố vi mô nhưng neo giữ vững chắc tinh thần thời đại và phẩm giá dân tộc.\n"
                "===============================================================================\n"
            )
        return ""


# ==============================================================================
# 3. TRI-TIER ONTOLOGY RESOLVER
# ==============================================================================

# Lexical indicators for Vietnamese cultural density scoring
VN_HISTORICAL_NAMES = [
    "trần hưng đạo", "trần quốc tuấn", "lê lợi", "quang trung", "nguyễn huệ",
    "ngô quyền", "lý thường kiệt", "hai bà trưng", "đinh bộ lĩnh", "lê hoàn",
    "trần quốc toản", "bùi thị xuân", "nguyễn trãi", "chu văn an", "yết kiêu", "dã tượng"
]

VN_DYNASTIES_PERIODS = [
    "đại việt", "đại cồ việt", "vạn xuân", "âu lạc", "hồng bàng", "thời lý",
    "thời trần", "thời hậu lê", "triều nguyễn", "tây sơn", "nhà đinh", "nhà mạc"
]

VN_CULTURAL_ENTITIES = [
    "trống đồng", "trống đồng đông sơn", "nỏ thần", "nỏ thần kim quy", "gươm báu",
    "gươm thần thuận thiên", "cổng làng", "bến sông", "cây đa", "giếng nước", "mái đình",
    "chiếu dời đô", "hịch tướng sĩ", "bình ngô đại cáo", "thuyền rồng", "bãi cọc bạch đằng",
    "hoàng thành thăng long", "điện kính thiên", "chùa một cột", "hồ gươm", "sông hồng"
]

VN_TRADITIONAL_ATTIRE = [
    "áo ngũ thân", "áo nhật bình", "áo tấc", "khăn đóng", "áo bà ba", "nón lá",
    "nón quai thao", "áo yếm", "khăn rằn", "áo dài truyền thống", "hài thêu"
]

VN_HONORIFICS = [
    "bệ hạ", "khanh", "trẫm", "hoàng thượng", "thần", "tướng quân", "chàng",
    "nàng", "u", "tía", "má", "đồng chí", "tiểu thư", "công tử", "nghĩa sĩ"
]

VN_FUSION_MARKERS = [
    "cyberpunk thăng long", "cyberpunk hà nội", "cyberpunk sài gòn", "steampunk nguyễn triều",
    "việt nam hậu tận thế", "hà nội 2099", "sài gòn 2099", "mecha đại việt", "hologram nón lá",
    "neon áo dài", "phi thuyền thăng long", "robot ngũ thân"
]

OUT_OF_DOMAIN_MARKERS = [
    "new york", "london", "paris", "tokyo", "chicago", "hogwarts", "manhattan",
    "elf", "elves", "dwarf", "dwarves", "orc", "vampire", "werewolf", "spaceship",
    "warp drive", "galactic empire", "alien", "magic academy", "sherlock", "watson",
    "john", "alice", "arthur", "elena", "victorian", "fbi", "cia"
]

# Master Negative Filter against cultural distortion for Vietnamese settings (Tier 1 & 2)
# Ensures diffusion models do not hallucinate Chinese Hanfu, Japanese Kimono, Samurai, or Ninja.
MASTER_NEGATIVE_VIETNAMESE = (
    "hanfu, kimono, yukata, hanbok, samurai, samurai armor, ninja, katana, geisha, "
    "qing queue, pigtail hairstyle, chinese traditional clothing, japanese traditional clothing, "
    "korean traditional clothing, tangzhuang, cheongsam, qipao, wooden geta, conical rice hat of china"
)


class TriTierOntologyResolver:
    """
    Calculates cultural similarity score S_cult and resolves settings into:
    - Tier 1: Canonical Vietnamese Cultural Domain (S_cult >= 0.7)
    - Tier 2: Cultural Fusion / Hybrid Domain (0.3 <= S_cult < 0.7)
    - Tier 3: Open-Domain Adaptive Graph (S_cult < 0.3)
    """

    @classmethod
    def calculate_cultural_similarity(cls, prompt_or_text: str, genre: str = "") -> float:
        """
        Computes Vietnamese cultural similarity score S_cult in range [0.0, 1.0].
        """
        combined = f"{genre} {prompt_or_text}".lower()
        if not combined.strip():
            return 0.5

        # Check explicit genre signals
        genre_lower = genre.lower() if genre else ""
        if any(g in genre_lower for g in ["lịch sử việt nam", "dã sử", "chính sử", "truyền thuyết việt", "dân gian việt"]):
            return 0.95
        if any(g in genre_lower for g in ["tiên hiệp", "kiếm hiệp", "huyền huyễn"]):
            # Asian fantasy - not canonical VN, but not purely Western OOD
            return 0.25
        if any(g in genre_lower for g in ["sci-fi phương tây", "western detective", "cyberpunk new york", "high fantasy", "isekai"]):
            return 0.1

        # Tally signals in text
        vn_score = 0.0
        ood_score = 0.0

        for tok in VN_HISTORICAL_NAMES:
            if tok in combined:
                vn_score += 0.35
        for tok in VN_DYNASTIES_PERIODS:
            if tok in combined:
                vn_score += 0.30
        for tok in VN_CULTURAL_ENTITIES:
            if tok in combined:
                vn_score += 0.25
        for tok in VN_TRADITIONAL_ATTIRE:
            if tok in combined:
                vn_score += 0.25
        for tok in VN_HONORIFICS:
            if re.search(r"\b" + re.escape(tok) + r"\b", combined):
                vn_score += 0.15

        # Fusion markers
        for tok in VN_FUSION_MARKERS:
            if tok in combined:
                # Direct indicator of Tier 2
                return 0.50

        # Out-of-domain markers
        for tok in OUT_OF_DOMAIN_MARKERS:
            if re.search(r"\b" + re.escape(tok) + r"\b", combined):
                ood_score += 0.25

        raw_sim = (vn_score - ood_score)
        # Normalize to [0.0, 1.0]
        if raw_sim <= 0:
            # Check if there are common Vietnamese location/person cues
            vn_light_cues = ["việt nam", "hà nội", "sài gòn", "huế", "đà nẵng", "sông hương", "sông hồng"]
            if any(c in combined for c in vn_light_cues) and ood_score < 0.5:
                return 0.4
            return max(0.05, round(0.2 - ood_score * 0.1, 2))

        sim = 0.3 + min(0.65, raw_sim * 0.4)
        return min(1.0, round(sim, 2))

    @classmethod
    def resolve_tier(cls, similarity: float) -> CulturalTier:
        if similarity >= 0.7:
            return CulturalTier.TIER_1_CANONICAL_VN
        elif similarity >= 0.3:
            return CulturalTier.TIER_2_CULTURAL_FUSION
        else:
            return CulturalTier.TIER_3_OPEN_DOMAIN

    @classmethod
    def get_tier_visual_dna(cls, tier: CulturalTier) -> Tuple[str, str]:
        """
        Returns (positive_dna_anchor, master_negative_filter) for comic diffusion models.
        """
        if tier == CulturalTier.TIER_1_CANONICAL_VN:
            pos = (
                "authentic Vietnamese traditional attire, wearing Áo Ngũ Thân or Áo Nhật Bình or Áo Tấc, "
                "properly wrapped Khăn Đóng turban, Vietnamese historical aesthetic, clean ink lineart"
            )
            neg = MASTER_NEGATIVE_VIETNAMESE
            return pos, neg
        elif tier == CulturalTier.TIER_2_CULTURAL_FUSION:
            pos = (
                "Vietnamese cultural fusion aesthetic, hybrid futuristic Áo Dài with neon accents, "
                "cybernetic traditional silhouettes, stylized conical hat visor, high contrast ink"
            )
            neg = MASTER_NEGATIVE_VIETNAMESE
            return pos, neg
        else:
            # Tier 3 Open Domain: no forced traditional attire, relaxed era
            pos = "clean 2D monochrome illustration, sharp contours, dynamic composition"
            neg = ""  # standard quality negatives applied separately
            return pos, neg

    @classmethod
    def get_honorifics_guidelines(cls, tier: CulturalTier, mode: NarrativeMode) -> str:
        """Generates honorific instructions based on tier and narrative mode."""
        if tier == CulturalTier.TIER_1_CANONICAL_VN:
            return (
                "\nQUY TẮC ĐẠI TỪ XƯNG HÔ THUẦN VIỆT (TIER 1 CANONICAL VN):\n"
                "- Triều đình / Quân ngũ: Bệ hạ / Khanh / Trẫm, Hoàng thượng / Thần, Tướng quân.\n"
                "- Tình cảm / Lứa đôi: Chàng / Nàng, Huynh / Muội.\n"
                "- Gia đình / Làng quê: U / Con, Tía / Má, Thầy / Con, Bác / Cháu.\n"
                "- Lịch sử kháng chiến: Đồng chí.\n"
                "- TUYỆT ĐỐI CẤM đại từ kiếm hiệp Tàu dịch thô sượng (bản tọa, đế tôn, tiểu tử, lão phu).\n"
            )
        elif tier == CulturalTier.TIER_2_CULTURAL_FUSION:
            return (
                "\nQUY TẮC XƯNG HÔ LAI GHÉP (TIER 2 CULTURAL FUSION):\n"
                "- Kết hợp xưng hô thân mật tự nhiên của tiếng Việt (anh/em, tôi/bạn, đồng chí, cậu/tớ)\n"
                "  kèm phong thái công nghệ cao hoặc viễn tưởng.\n"
            )
        else:
            return (
                "\nQUY TẮC XƯNG HÔ MỞ (TIER 3 OPEN DOMAIN):\n"
                "- Tự do lựa chọn xưng hô phù hợp bối cảnh (hiện đại, phương Tây, kỳ ảo).\n"
                "- Không áp đặt bất kỳ quy chuẩn xưng hô phong kiến Việt Nam nào.\n"
            )


# ==============================================================================
# 4. SMART SELECTIVE LANGUAGE FILTER
# ==============================================================================

# Universal AI clichés - banned across ALL modes and genres
UNIVERSAL_AI_CLICHES = [
    r"nhanh như nhịp tim chậm rãi",
    r"khoảng trống trong lòng",
    r"nỗi lo đè nặng lên vai",
    r"thở dài giọng nhẹ",
    r"trái tim đập thình thịch",
    r"nụ cười bí ẩn nở trên môi",
    r"đôi mắt sáng rực lên",
    r"cảm xúc trào dâng trong lồng ngực",
    r"lòng tôi chợt nặng trĩu",
    r"một cảm giác kỳ lạ lan tỏa",
    r"thế giới dường như dừng lại",
    r"thời gian như ngừng trôi",
    r"tim tôi nhói đau",
    r"giọng nói ấm áp như nắng",
    r"nỗi buồn man mác",
    r"lòng nhẹ nhõm như trút được gánh nặng",
    r"vầng trăng vằng vặc",
    r"thời gian thấm thoắt thoi đưa",
    r"hắn cười khẩy",
    r"cười lạnh",
    r"mắt phượng mày ngài",
    r"trời quang mây tạnh lòng người u sầu",
    r"bỗng nhiên một chuyện bất ngờ xảy ra",
    r"cô ấy rất buồn",
    r"hắn vô cùng tức giận",
    r"giọng nói run rẩy",
    r"đôi mắt ngấn lệ",
    r"nắm chặt tay thành nắm đấm",
    r"tim đập loạn nhịp",
    r"một giọt nước mắt lăn dài trên má",
    r"ánh mắt lạnh lẽo như băng",
    r"nụ cười ấm áp",
    r"trái tim tan vỡ",
]

# Chinese-translation clichés - banned in pure Vietnamese/historical, allowed in Xianxia/Wuxia
TRANSLATION_CLICHE_BANLIST = [
    r"tiêu\s+sái",
    r"tà\s+mị",
    r"lãnh\s+khốc",
    r"bản\s+tọa",
    r"bổn\s+tọa",
    r"đế\s+tôn",
    r"không\s+khỏi\s+hít\s+vào\s+một\s+ngụm\s+khí\s+lạnh",
    r"sát\s+khí\s+cuộn\s+trào",
    r"sát\s+khí\s+ngút\s+trời",
    r"lão\s+phu",
    r"tiểu\s+súc\s+sinh",
    r"ngươi\s+dám",
    r"muốn\s+chết(?!\s*sao\b)",
    r"tiểu\s+bối",
    r"đạo\s+hữu",
    r"nghiệt\s+súc"
]


class SmartSelectiveLanguageFilter:
    """
    Selectively controls literary clichés:
    - Universal AI clichés are ALWAYS banned in all genres and modes.
    - Chinese translation clichés ("tiêu sái", "tà mị", "lãnh khốc", "bản tọa", "đế tôn") are:
      * STRICTLY BANNED in pure Vietnamese prose, historical modes (CHINH_SU, DA_SU), and modern realism.
      * PERMITTED only when user explicitly chooses Xianxia / Wuxia (Tiên hiệp / Kiếm hiệp) in Free Fiction mode.
    """

    @classmethod
    def is_wuxia_or_xianxia_genre(cls, genre: str) -> bool:
        if not genre or not isinstance(genre, str):
            return False
        g = genre.lower()
        wuxia_keywords = ["tiên hiệp", "kiếm hiệp", "xianxia", "wuxia", "tu chân", "huyền huyễn"]
        return any(kw in g for kw in wuxia_keywords)

    @classmethod
    def filter(
        cls,
        text: str,
        genre: str = "",
        mode: NarrativeMode = NarrativeMode.HU_CAU_TU_DO
    ) -> Tuple[str, List[str]]:
        """
        Validates and reports violations. Returns (original_text, violations).
        Does not blindly mutate text to avoid semantic corruption.
        """
        is_clean, violations = cls.validate_smart_language_compliance(text, genre=genre, narrative_mode=mode)
        return text, violations

    @classmethod
    def validate_smart_language_compliance(
        cls,
        text: str,
        genre: str = "",
        narrative_mode: NarrativeMode = NarrativeMode.HU_CAU_TU_DO,
        cultural_tier: int = 1
    ) -> Tuple[bool, List[str]]:
        """
        Validates text with selective cliché enforcement:
        1. Universal AI clichés are always checked.
        2. Translation clichés are suppressed unless genre is Xianxia/Wuxia and mode is HU_CAU_TU_DO.
        """
        if not text or not isinstance(text, str):
            return True, []

        violations = []
        text_lower = text.lower()

        # 1. Universal AI Clichés (Always enforced)
        for pattern in UNIVERSAL_AI_CLICHES:
            matches = list(re.finditer(pattern, text_lower))
            for m in matches:
                line_num = text[:m.start()].count('\n') + 1
                snippet = text[max(0, m.start() - 20):m.end() + 20].replace('\n', ' ')
                violations.append(f"AI_CLICHE [Line ~{line_num}]: '{m.group()}' in \"...{snippet}...\"")

        # 2. Chinese-Translation Clichés (Selective enforcement)
        allow_translation_cliches = (
            cls.is_wuxia_or_xianxia_genre(genre) and
            narrative_mode == NarrativeMode.HU_CAU_TU_DO
        )

        if not allow_translation_cliches:
            for pattern in TRANSLATION_CLICHE_BANLIST:
                matches = list(re.finditer(pattern, text_lower))
                for m in matches:
                    line_num = text[:m.start()].count('\n') + 1
                    snippet = text[max(0, m.start() - 20):m.end() + 20].replace('\n', ' ')
                    violations.append(f"TRANSLATION_CLICHE [Line ~{line_num}]: '{m.group()}' in \"...{snippet}...\" (Banned for Vietnamese/historical prose)")

        return len(violations) == 0, violations

    @classmethod
    def get_prompt_cliche_instructions(cls, genre: str = "", mode: NarrativeMode = NarrativeMode.HU_CAU_TU_DO) -> str:
        """Injects selective cliché rules into LLM system prompt."""
        allow_wuxia = cls.is_wuxia_or_xianxia_genre(genre) and mode == NarrativeMode.HU_CAU_TU_DO
        if allow_wuxia:
            return (
                "\nBỘ LỌC NGÔN NGỮ CÓ CHỌN LỌC (THỂ LOẠI TIÊN HIỆP / KIẾM HIỆP):\n"
                "- Cho phép sử dụng các thuật ngữ đặc thù thể loại (tiêu sái, sát khí, đạo hữu, bổn tọa...).\n"
                "- VẪN TUYỆT ĐỐI CẤM các sáo ngữ AI lười biếng ('nhanh như nhịp tim chậm rãi', 'khoảng trống trong lòng').\n"
            )
        else:
            return (
                "\nBỘ LỌC NGÔN NGỮ CÓ CHỌN LỌC (VĂN PHONG THUẦN VIỆT / LỊCH SỬ):\n"
                "- TUYỆT ĐỐI CẤM sáo ngữ kiếm hiệp/tiên hiệp Tàu dịch sượng ('tiêu sái', 'tà mị', 'lãnh khốc', 'bản tọa', 'đế tôn').\n"
                "- Giữ gìn sự trong sáng, tự nhiên và giàu sắc thái văn học thuần Việt.\n"
                "- TUYỆT ĐỐI CẤM các sáo ngữ AI lười biếng ('nhanh như nhịp tim chậm rãi', 'khoảng trống trong lòng').\n"
            )


# ==============================================================================
# 5. DYNAMIC EPHEMERAL NODE EXTRACTION (FOR TIER 3 OPEN DOMAIN)
# ==============================================================================

def extract_dynamic_ephemeral_node(story_text: str, genre: str = "") -> Dict[str, Any]:
    """
    Dynamically extracts ephemeral entities, space anchors, and era settings
    directly from context for Tier 3 Open Domain stories.
    Disables feudal Vietnamese constraints and classroom defaults.
    """
    clean_text = (story_text or "").strip()
    words = clean_text.split()
    sample = " ".join(words[:200]) if len(words) > 200 else clean_text

    # Extract potential setting cues from first few sentences
    setting_anchor = "open atmospheric environment"
    if any(k in sample.lower() for k in ["street", "city", "đường phố", "thành phố"]):
        setting_anchor = "urban street with ambient lighting and architectural depth"
    elif any(k in sample.lower() for k in ["space", "tàu vũ trụ", "vũ trụ", "hành tinh", "galaxy"]):
        setting_anchor = "futuristic sci-fi interior with control consoles and cosmic viewports"
    elif any(k in sample.lower() for k in ["forest", "rừng", "cây cối", "núi rừng"]):
        setting_anchor = "dense ancient forest with filtered canopy light and natural paths"
    elif any(k in sample.lower() for k in ["phòng", "room", "nhà", "office"]):
        setting_anchor = "enclosed interior space with distinctive furnishings and natural shadow"

    return {
        "tier": CulturalTier.TIER_3_OPEN_DOMAIN,
        "is_open_domain": True,
        "setting_anchor": setting_anchor,
        "genre": genre or "Open Domain Fiction",
        "era_name": "open_domain_adaptive",
        "forbidden_feudal_filters_disabled": True,
        "forced_attire_disabled": True
    }


# ==============================================================================
# 6. UNIFIED RESOLVER ENTRYPOINT
# ==============================================================================

def resolve_ontology(
    prompt: str,
    user_genre: Optional[str] = None,
    requested_mode: Optional[str] = None
) -> ResolvedOntology:
    """
    Master resolution function coordinating mode, similarity, tier, visual DNA,
    master negative filters, and honorific rules.
    """
    mode = normalize_narrative_mode(requested_mode)
    genre = (user_genre or "").strip()

    # In CHINH_SU or DA_SU, force similarity >= 0.7 (Tier 1)
    if mode in (NarrativeMode.CHINH_SU, NarrativeMode.DA_SU):
        sim = 1.0
        tier = CulturalTier.TIER_1_CANONICAL_VN
    else:
        sim = TriTierOntologyResolver.calculate_cultural_similarity(prompt, genre=genre)
        tier = TriTierOntologyResolver.resolve_tier(sim)

    pos_dna, master_neg = TriTierOntologyResolver.get_tier_visual_dna(tier)
    honorifics = TriTierOntologyResolver.get_honorifics_guidelines(tier, mode)
    hist_constraints = HistoricalGroundingGatekeeper.get_historical_grounding_prompt(mode)

    tier_names = {
        CulturalTier.TIER_1_CANONICAL_VN: "Tier 1: Canonical Vietnamese Cultural Domain",
        CulturalTier.TIER_2_CULTURAL_FUSION: "Tier 2: Cultural Fusion / Hybrid Domain",
        CulturalTier.TIER_3_OPEN_DOMAIN: "Tier 3: Open-Domain Adaptive Graph"
    }

    era_anchors = {
        CulturalTier.TIER_1_CANONICAL_VN: "Đại Việt / Triều đại phong kiến Việt Nam",
        CulturalTier.TIER_2_CULTURAL_FUSION: "Việt Nam Lai Ghép / Viễn Tưởng Hậu Tận Thế",
        CulturalTier.TIER_3_OPEN_DOMAIN: "Thế giới Mở Tự Do (Open Domain)"
    }

    return ResolvedOntology(
        narrative_mode=mode,
        cultural_tier=tier,
        cultural_similarity=sim,
        tier_name=tier_names.get(tier, "Tier 1"),
        positive_visual_dna=pos_dna,
        master_negative_filter=master_neg,
        honorifics_guidelines=honorifics,
        historical_constraints=hist_constraints,
        era_anchor=era_anchors.get(tier, "Open Domain"),
        spatial_anchor=""
    )
