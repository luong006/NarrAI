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
import json
import uuid
import unicodedata
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
from pydantic import BaseModel, Field


def _normalize_historical_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.casefold())
    without_diacritics = "".join(
        character
        for character in decomposed
        if unicodedata.category(character) != "Mn"
    )
    return without_diacritics.replace("đ", "d")


def _matches_normalized_historical_pattern(pattern: str, normalized_text: str) -> bool:
    normalized_pattern = _normalize_historical_text(pattern)
    return re.search(normalized_pattern, normalized_text, re.DOTALL) is not None


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

# Core Vietnamese Historical Canon (Inviolable Truths) across 6 Epochs (31+ Heroes & Major Victories)
VIETNAMESE_HISTORICAL_CANON = {
    # Epoch 1: Thời đại Hồng Bàng & Dựng nước
    "hung_vuong": {
        "names": ["vua hùng", "hùng vương", "các vua hùng", "lạc long quân", "âu cơ"],
        "era": "Thời đại Hồng Bàng (Văn Lang)",
        "enemies": ["giặc ân", "ngoại bang"],
        "invariants": [
            "Cội nguồn dựng nước Văn Lang của dân tộc Việt Nam",
            "Truyền thuyết bọc trăm trứng, đồng bào gắn kết một nhà",
            "Không bao giờ đầu hàng hay bị giặc xóa sổ"
        ],
        "defeat_regex": r"(?i)\b(?:vua\s+hùng|hùng\s+vương)\b.*?\b(?:đầu\s+hàng|bán\s+nước|bị\s+giặc\s+ân\s+xóa\s+sổ|quy\s+hàng)\b"
    },
    "thanh_giong": {
        "names": ["thánh gióng", "phù đổng thiên vương", "gióng"],
        "era": "Thời Hùng Vương thứ 6",
        "battle": "Đánh tan giặc Ân ở chân núi Sóc",
        "enemies": ["giặc ân"],
        "invariants": [
            "Cưỡi ngựa sắt, mặc giáp sắt, nhổ tre đằng ngà quét sạch giặc Ân",
            "Bay về trời sau khi đánh tan giặc, biểu tượng bất diệt của sức mạnh quật khởi",
            "Tuyệt đối không bại trận trước giặc Ân"
        ],
        "defeat_regex": r"(?i)\b(?:thánh\s+gióng|phù\s+đổng\s+thiên\s+vương)\b.*?\b(?:bại\s+trận|đầu\s+hàng|thua\s+giặc\s+ân|quy\s+hàng)\b"
    },
    "an_duong_vuong": {
        "names": ["an dương vương", "thục phán"],
        "era": "Nước Âu Lạc (Thế kỷ 3 TCN)",
        "battle": "Thành Cổ Loa chống Triệu Đà",
        "enemies": ["triệu đà", "quân nam việt"],
        "invariants": [
            "Hợp nhất người Văn Lang và Tây Âu lập nước Âu Lạc",
            "Xây thành Cổ Loa kiên cố, nỏ thần Kim Quy đánh lui nhiều đợt xâm lăng của Triệu Đà",
            "Khí phách quật cường, không đầu hàng hèn nhát"
        ],
        "defeat_regex": r"(?i)\b(?:an\s+dương\s+vương|thục\s+phán)\b.*?\b(?:hèn\s+nhát|đầu\s+hàng\s+triệu\s+đà|bán\s+nước\s+cho\s+triệu\s+đà)\b"
    },

    # Epoch 2: Khởi nghĩa thời Bắc thuộc
    "hai_ba_trung": {
        "names": ["hai bà trưng", "trưng trắc", "trưng nhị"],
        "era": "Thời kỳ Bắc thuộc lần 1 (Năm 40)",
        "enemies": ["tô định", "quân đông hán", "nhà hán"],
        "allies": ["thi sách", "lê chân", "thánh thiên", "bát nàn"],
        "invariants": [
            "Khởi nghĩa năm 40 giành lại 65 thành trì",
            "Đền nợ nước, trả thù nhà, đánh đuổi thái thú Tô Định",
            "Tuyệt đối không đầu hàng giặc ngoại xâm hay cầu xin Tô Định"
        ],
        "defeat_regex": r"(?i)\b(?:trưng\s+trắc|trưng\s+nhị|hai\s+bà\s+trưng)\b.*?\b(?:đầu\s+hàng|phản\s+bội|quy\s+hàng|bán\s+nước|thua\s+nhục|cầu\s+xin\s+tô\s+định)\b"
    },
    "ba_trieu": {
        "names": ["bà triệu", "triệu thị trinh", "triệu ẩu"],
        "era": "Năm 248 SCN",
        "battle": "Khởi nghĩa chống quân Đông Ngô",
        "enemies": ["lục dận", "quân đông ngô", "nhà ngô"],
        "invariants": [
            "Tuyên ngôn đạp luồng sóng dữ, chém cá kình Biển Đông, quét sạch giặc Ngô",
            "Cưỡi voi xung trận dũng mãnh, khí phách kiên trinh bất khuất",
            "Tuyệt đối không đầu hàng quân Ngô"
        ],
        "defeat_regex": r"(?i)\b(?:bà\s+triệu|triệu\s+thị\s+trinh)\b.*?\b(?:đầu\s+hàng|bán\s+nước|quy\s+hàng\s+quân\s+ngô|sợ\s+hãi\s+lục\s+dận)\b"
    },
    "ly_nam_de": {
        "names": ["lý nam đế", "lý bí"],
        "era": "Năm 544",
        "battle": "Khởi nghĩa chống ách đô hộ nhà Lương",
        "enemies": ["tiêu tư", "quân nhà lương", "trần bá tiên"],
        "invariants": [
            "Đánh đuổi thứ sử Tiêu Tư, giải phóng Giao Châu",
            "Thành lập nhà nước Vạn Xuân độc lập, tự xưng Hoàng đế năm 544",
            "Không bao giờ đầu hàng quân Lương hay phản bội Vạn Xuân"
        ],
        "defeat_regex": r"(?i)\b(?:lý\s+bí|lý\s+nam\s+đế)\b.*?\b(?:đầu\s+hàng\s+nhà\s+lương|phản\s+bội\s+vạn\s+xuân|quy\s+hàng\s+tiêu\s+tư)\b"
    },
    "trieu_quang_phuc": {
        "names": ["triệu quang phục", "dạ trạch vương"],
        "era": "Thế kỷ 6",
        "battle": "Căn cứ đầm Dạ Trạch",
        "enemies": ["quân nhà lương", "trần bá tiên"],
        "invariants": [
            "Xây dựng căn cứ đầm lầy Dạ Trạch, sáng tạo chiến thuật du kích tài tình",
            "Đánh bại tướng Lương Trần Bá Tiên, giữ vững nền độc lập nước Vạn Xuân",
            "Không bao giờ đầu hàng quân Lương"
        ],
        "defeat_regex": r"(?i)\b(?:triệu\s+quang\s+phục|dạ\s+trạch\s+vương)\b.*?\b(?:đầu\s+hàng\s+nhà\s+lương|thua\s+nhục\s+ở\s+dạ\s+trạch|quy\s+hàng)\b"
    },
    "mai_thuc_loan": {
        "names": ["mai thúc loan", "mai hắc đế"],
        "era": "Năm 713 - 722",
        "battle": "Khởi nghĩa Hoan Châu",
        "enemies": ["nhà đường", "quân nhà đường", "dương tư húc"],
        "invariants": [
            "Lãnh đạo nhân dân Hoan Châu khởi nghĩa chống sưu cao thuế nặng của nhà Đường",
            "Xây dựng thành Vạn An kiên cố, xưng Mai Hắc Đế khẳng định chủ quyền",
            "Không bao giờ quy hàng nhà Đường"
        ],
        "defeat_regex": r"(?i)\b(?:mai\s+thúc\s+loan|mai\s+hắc\s+đế)\b.*?\b(?:đầu\s+hàng\s+nhà\s+đường|cầu\s+xin\s+giặc|quy\s+hàng)\b"
    },
    "phung_hung": {
        "names": ["phùng hưng", "bố cái đại vương"],
        "era": "Năm 766 - 791",
        "battle": "Bao vây đánh chiếm phủ Tống Bình",
        "enemies": ["nhà đường", "đô hộ phủ nhà đường"],
        "invariants": [
            "Hào trưởng Đường Lâm khởi binh đánh chiếm thành Tống Bình",
            "Nhân dân tôn xưng Bố Cái Đại Vương, xây dựng chính quyền tự chủ",
            "Không bao giờ phản bội dân tộc hay đầu hàng quan đô hộ"
        ],
        "defeat_regex": r"(?i)\b(?:phùng\s+hưng|bố\s+cái\s+đại\s+vương)\b.*?\b(?:đầu\s+hàng\s+quan\s+đô\s+hộ|phản\s+bội\s+dân\s+tộc|quy\s+hàng)\b"
    },

    # Epoch 3: Ngô - Đinh - Tiền Lê
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
        "defeat_regex": (
            r"(?i)(?:"
            r"\b(?:ngô\s+quyền|tiền\s+ngô\s+vương)\b"
            r"(?:\s+(?:đã|lại|bị|phải|chịu|suýt|hoàn\s+toàn|cay\s+đắng|ở|trên\s+sông\s+bạch\s+đằng)){0,4}\s+"
            r"(?:bại\s+trận|thua\s+trận|thất\s+bại|đại\s+bại|đầu\s+hàng|bị\s+lưu\s+hoằng\s+tháo\s+(?:bắt|giết)|thua\s+quân\s+nam\s+hán)\b"
            r"|"
            r"\b(?:ngô\s+quyền|tiền\s+ngô\s+vương)\b.*?\b(?:đầu\s+hàng|quy\s+hàng|chịu\s+thua)\s+(?:quân\s+)?(?:nam\s+hán|lưu\s+hoằng\s+tháo)\b"
            r"|"
            r"\b(?:thất\s+bại|sự\s+thất\s+bại)\s+của\s+(?:ngô\s+quyền|tiền\s+ngô\s+vương)\b"
            r")"
        )
    },
    "dinh_bo_linh": {
        "names": ["đinh bộ lĩnh", "đinh tiên hoàng", "vạn thắng vương"],
        "era": "Năm 968",
        "battle": "Dẹp loạn 12 sứ quân",
        "enemies": ["12 sứ quân"],
        "invariants": [
            "Cờ lau tập trận, trăm trận trăm thắng được tôn vinh Vạn Thắng Vương",
            "Thống nhất non sông, dẹp tan loạn 12 sứ quân, định đô Hoa Lư lập nước Đại Cồ Việt",
            "Tuyệt đối không bại trận trước 12 sứ quân hay đầu hàng"
        ],
        "defeat_regex": r"(?i)\b(?:đinh\s+bộ\s+lĩnh|đinh\s+tiên\s+hoàng)\b.*?\b(?:bại\s+trận\s+trước\s+12\s+sứ\s+quân|chia\s+cắt\s+đất\s+nước|đầu\s+hàng|thua\s+12\s+sứ\s+quân)\b"
    },
    "le_hoan": {
        "names": ["lê hoàn", "lê đại hành"],
        "era": "Năm 981",
        "battle": "Bạch Đằng 981, Tây Kết",
        "enemies": ["nhà tống", "hầu nhân bảo", "quân tống"],
        "invariants": [
            "Được Thái hậu Dương Vân Nga trao áo long bào thống lĩnh kháng chiến",
            "Chém chết tướng giặc Hầu Nhân Bảo trên sông Bạch Đằng năm 981",
            "Phá Tống bình Chiêm, giữ yên bờ cõi độc lập"
        ],
        "defeat_regex": r"(?i)\b(?:lê\s+hoàn|lê\s+đại\s+hành)\b.*?\b(?:thua\s+hầu\s+nhân\s+bảo|đầu\s+hàng\s+quân\s+tống|thất\s+bại\s+năm\s+981|bại\s+trận\s+năm\s+981)\b"
    },

    # Epoch 4: Lý - Trần thịnh trị
    "ly_thai_to": {
        "names": ["lý thái tổ", "lý công uẩn"],
        "era": "Năm 1010",
        "battle": "Định đô Thăng Long",
        "enemies": [],
        "invariants": [
            "Soạn Chiếu dời đô dời kinh thành từ Hoa Lư về Đại La - Thăng Long năm 1010",
            "Đặt nền móng ngàn năm văn hiến cho kinh đô Thăng Long - Hà Nội",
            "Bậc minh quân sáng suốt, tuyệt đối không phản quốc bán đất"
        ],
        "defeat_regex": r"(?i)\b(?:lý\s+thái\s+tổ|lý\s+công\s+uẩn)\b.*?\b(?:hối\s+hận\s+dời\s+đô|phản\s+quốc|bán\s+đất|đầu\s+hàng)\b"
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
    "tran_quoc_toan": {
        "names": ["trần quốc toản", "hoài văn hầu"],
        "era": "Năm 1285",
        "battle": "Bến Bình Than, Trận Tây Kết, Hàm Tử",
        "enemies": ["quân nguyên mông", "thoát hoan"],
        "invariants": [
            "Bóp nát quả cam tại hội nghị Bình Than vì tuổi nhỏ không được dự bàn việc quân",
            "Thêu lá cờ 6 chữ vàng 'Phá cường địch, báo hoàng ân', dũng cảm xung trận hàng đầu",
            "Tuyệt đối không đầu hàng Thoát Hoan, không vứt cờ hay sợ chết"
        ],
        "defeat_regex": r"(?i)\b(?:trần\s+quốc\s+toản|hoài\s+văn\s+hầu)\b.*?\b(?:phản\s+bội|đầu\s+hàng\s+thoát\s+hoan|sợ\s+chết|vứt\s+cờ\s+sáu\s+chữ|quy\s+hàng)\b"
    },
    "tran_nhan_tong": {
        "names": ["trần nhân tông", "phật hoàng", "phật hoàng trần nhân tông"],
        "era": "Thời Trần (Thế kỷ 13)",
        "battle": "Hội nghị Diên Hồng, Hội nghị Bình Than",
        "enemies": ["quân nguyên mông"],
        "invariants": [
            "Lãnh tụ tối cao cùng Quốc công Tiết chế lãnh đạo toàn dân đánh thắng Nguyên Mông",
            "Mở Hội nghị Diên Hồng hỏi ý kiến bô lão 'Nên hòa hay nên đánh', muôn người đồng thanh 'Đánh'",
            "Sáng lập Thiền phái Trúc Lâm Yên Tử, từ bỏ ngai vàng xuất gia tu hành",
            "Tuyệt đối không đầu hàng hay chạy trốn nhục nhã"
        ],
        "defeat_regex": r"(?i)\b(?:trần\s+nhân\s+tông|phật\s+hoàng)\b.*?\b(?:đầu\s+hàng\s+quân\s+nguyên|bán\s+nước|chạy\s+trốn\s+nhục\s+nhã|quy\s+hàng)\b"
    },
    "tran_khanh_du": {
        "names": ["trần khánh dư", "nhân huệ vương"],
        "era": "Thời Trần (1288)",
        "battle": "Trận Vân Đồn 1288",
        "enemies": ["trương văn hổ", "đoàn thuyền lương nguyên mông"],
        "invariants": [
            "Bổ nhào đánh tan đoàn thuyền lương của Trương Văn Hổ tại Vân Đồn năm 1288",
            "Cắt đứt hoàn toàn huyết mạch lương thảo quân Nguyên Mông, tạo thế đảo chiều chiến lược",
            "Tuyệt đối không bại trận trước Trương Văn Hổ"
        ],
        "defeat_regex": r"(?i)\b(?:trần\s+khanh\s+dư|trần\s+khánh\s+dư|trận\s+vân\s+đồn)\b.*?\b(?:thua\s+trương\s+văn\s+hổ|đầu\s+hàng|bị\s+tiêu\s+diệt\s+hoàn\s+toàn)\b"
    },
    "yet_kieu": {
        "names": ["yết kiêu", "phạm hữu thế"],
        "era": "Thời Trần (Thế kỷ 13)",
        "battle": "Thủy chiến sông Bạch Đằng, Vạn Kiếp",
        "enemies": ["ô mã nhi", "quân nguyên mông"],
        "invariants": [
            "Gia tướng tài ba bơi lặn phi thường, đục thủng thuyền chiến giặc Ô Mã Nhi",
            "Trung thành vô hạn với Hưng Đạo Đại Vương Trần Quốc Tuấn",
            "Không bao giờ phản bội chủ hay đầu hàng giặc"
        ],
        "defeat_regex": r"(?i)\b(?:yết\s+kiêu)\b.*?\b(?:phản\s+bội\s+trần\s+hưng\s+đạo|bán\s+chủ|đầu\s+hàng\s+thoát\s+hoan|quy\s+hàng)\b"
    },
    "da_tuong": {
        "names": ["dã tượng"],
        "era": "Thời Trần (Thế kỷ 13)",
        "battle": "Tượng binh kháng chiến Nguyên Mông",
        "enemies": ["quân nguyên mông", "thoát hoan"],
        "invariants": [
            "Chỉ huy đội quân tượng binh dũng mãnh, một lòng bảo vệ Quốc công Tiết chế",
            "Tuyệt đối trung trinh ái quốc, không bao giờ đầu hàng quân Nguyên Mông"
        ],
        "defeat_regex": r"(?i)\b(?:dã\s+tượng)\b.*?\b(?:phản\s+bội\s+trần\s+hưng\s+đạo|bán\s+chủ|đầu\s+hàng\s+thoát\s+hoan|quy\s+hàng)\b"
    },
    "yet_kieu_da_tuong": {
        "names": ["yết kiêu", "dã tượng", "yết kiêu dã tượng"],
        "era": "Thời Trần (Thế kỷ 13)",
        "battle": "Kháng chiến chống quân Nguyên Mông",
        "enemies": ["quân nguyên mông", "thoát hoan"],
        "invariants": [
            "Tướng tài thủy chiến và tượng binh, đục thuyền giặc Ô Mã Nhi",
            "Trung thành tuyệt đối với Hưng Đạo Vương Trần Quốc Tuấn"
        ],
        "defeat_regex": r"(?i)\b(?:yết\s+kiêu|dã\s+tượng)\b.*?\b(?:phản\s+bội\s+trần\s+hưng\s+đạo|bán\s+chủ|đầu\s+hàng\s+thoát\s+hoan)\b"
    },

    # Epoch 5: Hậu Lê - Tây Sơn
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
        "defeat_regex": r"(?i)\b(?:lê\s+lợi|bình\s+định\s+vương|khởi\s+nghĩa\s+lam\s+sơn)\b.*?\b(?:bại\s+trận|thua\s+trận|đầu\s+hàng\s+quân\s+minh|bị\s+liễu\s+thăng\s+(?:bắt|giết)|thất\s+bại\s+hoàn\s+toàn)\b"
    },
    "nguyen_trai": {
        "names": ["nguyễn trãi", "ức trai"],
        "era": "Khởi nghĩa Lam Sơn (1418 - 1427)",
        "battle": "Mưu phạt tâm công Khởi nghĩa Lam Sơn",
        "enemies": ["quân minh", "nhà minh", "vương thông"],
        "invariants": [
            "Mưu sĩ lỗi lạc, tác giả Bình Ngô đại cáo bất hủ",
            "Tư tưởng nhân nghĩa 'Đem đại nghĩa để thắng hung tàn, lấy chí nhân để thay cường bạo'",
            "Tuyệt đối không phản bội Lê Lợi hay làm tay sai cho giặc Minh"
        ],
        "defeat_regex": r"(?i)\b(?:nguyễn\s+trãi|ức\s+trai)\b.*?\b(?:phản\s+bội\s+lê\s+lợi|làm\s+tay\s+sai\s+quân\s+minh|bán\s+nước|đầu\s+hàng)\b"
    },
    "le_thanh_tong": {
        "names": ["lê thánh tông", "vua lê thánh tông", "hồng đức hoàng đế"],
        "era": "Thế kỷ 15 (Triều Hậu Lê)",
        "battle": "Thời kỳ Hồng Đức thịnh trị",
        "enemies": [],
        "invariants": [
            "Thời kỳ hoàng kim thịnh trị Hồng Đức, bản đồ Hồng Đức, Luật Hồng Đức",
            "Thành lập Tao Đàn Nhị thập bát tú, văn võ toàn tài",
            "Kiên quyết giữ vững từng tấc đất bờ cõi giang sơn Đại Việt"
        ],
        "defeat_regex": r"(?i)\b(?:lê\s+thánh\s+tông)\b.*?\b(?:làm\s+mất\s+nước|bán\s+giang\s+sơn|hèn\s+nhát|đầu\s+hàng)\b"
    },
    "quang_trung": {
        "names": ["quang trung", "nguyễn huệ", "bắc bình vương", "hoàng đế quang trung"],
        "era": "Khởi nghĩa Tây Sơn - Mùa xuân Kỷ Dậu 1789",
        "battle": "Ngọc Hồi - Đống Đa (Tết Kỷ Dậu 1789), Rạch Gầm - Xoài Mút",
        "enemies": ["quân thanh", "mãn thanh", "tôn sĩ nghị", "sầm nghi đống", "quân xiêm"],
        "invariants": [
            "Hành quân thần tốc từ Phú Xuân ra Thăng Long dịp Tết Kỷ Dậu 1789",
            "Chiến thuật công phá pháo đài rơm bện tẩm nước",
            "Đại phá 29 vạn quân Mãn Thanh tại Ngọc Hồi - Đống Đa mùng 5 Tết",
            "Đại phá 2 vạn quân Xiêm tại trận Rạch Gầm - Xoài Mút 1785",
            "Tướng giặc Sầm Nghi Đống thắt cổ tự vẫn, Tôn Sĩ Nghị bỏ chạy qua sông Hồng",
            "Tuyệt đối không thất bại hay đầu hàng quân Thanh, quân Xiêm"
        ],
        "defeat_regex": r"(?i)\b(?:quang\s+trung|nguyễn\s+huệ|bắc\s+bình\s+vương)\b.*?\b(?:bại\s+trận|đại\s+bại|thua\s+trận|thua\s+cuộc|đầu\s+hàng|thua\s+tôn\s+sĩ\s+nghị|thất\s+bại\s+ở\s+ngọc\s+hồi|thất\s+bại\s+ở\s+đống\s+đa|thua\s+quân\s+xiêm|thua\s+quân\s+thanh)\b"
    },
    "bui_thi_xuan": {
        "names": ["bùi thị xuân", "nữ tướng bùi thị xuân"],
        "era": "Thời Tây Sơn (Cuối thế kỷ 18)",
        "battle": "Trấn thủ Quy Nhơn, Trận Trấn Ninh",
        "enemies": ["quân nguyễn ánh", "quân trịnh"],
        "invariants": [
            "Đô đốc nữ tướng kiệt xuất của phong trào Tây Sơn, huấn luyện tượng binh thiện chiến",
            "Khí phách lẫm liệt, thà chết vinh quang chứ tuyệt đối không cúi đầu cầu xin tha mạng"
        ],
        "defeat_regex": r"(?i)\b(?:bùi\s+thị\s+xuân)\b.*?\b(?:đầu\s+hàng\s+hèn\s+nhát|cầu\s+xin\s+tha\s+mạng|phản\s+bội\s+tây\s+sơn|quy\s+hàng)\b"
    },

    # Epoch 6: Cận đại & Hiện đại
    "truong_dinh": {
        "names": ["trương định", "bình tây đại nguyên soái"],
        "era": "Kháng Pháp Nam Kỳ (1859 - 1864)",
        "battle": "Căn cứ Tân Phước, Gò Công",
        "enemies": ["thực dân pháp", "quân pháp"],
        "invariants": [
            "Nhận phong 'Bình Tây Đại Nguyên Soái' từ nhân dân, thà chết vì nghĩa chứ không tuân lệnh triều đình đầu hàng Pháp",
            "Chiến đấu kiên cường đến hơi thở cuối cùng vì nền độc lập non sông"
        ],
        "defeat_regex": r"(?i)\b(?:trương\s+định|bình\s+tây\s+đại\s+nguyên\s+soái)\b.*?\b(?:đầu\s+hàng\s+giặc\s+pháp|làm\s+tay\s+sai\s+cho\s+pháp|quy\s+hàng)\b"
    },
    "nguyen_trung_truc": {
        "names": ["nguyễn trung trực"],
        "era": "Kháng chiến chống Pháp (1861 - 1868)",
        "battle": "Đốt tàu Espérance trên sông Nhật Tảo, chiếm đồn Rạch Giá",
        "enemies": ["thực dân pháp", "quân pháp"],
        "invariants": [
            "Chỉ huy trận đốt tàu Espérance tại Nhật Tảo và đánh úp đồn Kiên Giang",
            "Lời tuyên bố bất hủ: 'Bao giờ người Tây nhổ hết cỏ nước Nam thì mới hết người Nam đánh Tây'",
            "Tuyệt đối không quy hàng hay làm tay sai cho giặc Pháp"
        ],
        "defeat_regex": r"(?i)\b(?:nguyễn\s+trung\s+trực)\b.*?\b(?:đầu\s+hàng\s+quân\s+pháp|quy\s+hàng|phản\s+bội\s+nghĩa\s+quân|cầu\s+xin\s+giặc)\b"
    },
    "phan_dinh_phung": {
        "names": ["phan đình phùng", "cao thắng", "nghĩa quân hương khê"],
        "era": "Khởi nghĩa Hương Khê (1885 - 1896)",
        "battle": "Căn cứ Vụ Quang, Hương Khê",
        "enemies": ["thực dân pháp", "quân pháp"],
        "invariants": [
            "Lãnh tụ tiêu biểu của phong trào Cần Vương, Cao Thắng tự chế tạo súng trường",
            "Kiên trì chiến đấu anh dũng nơi rừng sâu, không bao giờ đầu hàng hay phản bội Cần Vương"
        ],
        "defeat_regex": r"(?i)\b(?:phan\s+đình\s+phùng|cao\s+thắng|khởi\s+nghĩa\s+hương\s+khê)\b.*?\b(?:đầu\s+hàng\s+pháp|phản\s+bội\s+cần\s+vương|làm\s+tay\s+sai|quy\s+hàng)\b"
    },
    "hoang_hoa_tham": {
        "names": ["hoàng hoa thám", "đề thám", "hùm xám yên thế"],
        "era": "Khởi nghĩa Yên Thế (1884 - 1913)",
        "battle": "Căn cứ Yên Thế (Bắc Giang)",
        "enemies": ["thực dân pháp", "quân pháp"],
        "invariants": [
            "Hùm xám Yên Thế kiên cường lãnh đạo phong trào nông dân kháng chiến suốt gần 30 năm",
            "Tuyệt đối không làm tay sai cho thực dân Pháp hay phản bội nghĩa quân"
        ],
        "defeat_regex": r"(?i)\b(?:hoàng\s+hoa\s+thám|đề\s+thám|hùm\s+xám\s+yên\s+thế)\b.*?\b(?:đầu\s+hàng\s+pháp|làm\s+tay\s+sai\s+thực\s+dân|phản\s+bội|quy\s+hàng)\b"
    },
    "vo_thi_sau": {
        "names": ["võ thị sáu", "kim đồng", "bế văn đàn", "tô vĩnh diện"],
        "era": "Kháng chiến chống Pháp (1945 - 1954)",
        "battle": "Nhà tù Côn Đảo, Chiến dịch Điện Biên Phủ",
        "enemies": ["thực dân pháp", "quân pháp"],
        "invariants": [
            "Nữ anh hùng Đất Đỏ kiên cường ngẩng cao đầu trước họng súng kẻ thù tại Côn Đảo",
            "Tấm gương thiếu niên dũng cảm, tuyệt đối không khai báo phản bội hay cúi đầu xin giặc tha mạng"
        ],
        "defeat_regex": r"(?i)\b(?:võ\s+thị\s+sáu|kim\s+đồng|tô\s+vĩnh\s+diện|bế\s+văn\s+đàn)\b.*?\b(?:đầu\s+hàng|khai\s+báo\s+phản\s+bội|hèn\s+nhát\s+cầu\s+xin|quy\s+hàng)\b"
    },
    "vo_nguyen_giap": {
        "names": ["võ nguyên giáp", "đại tướng võ nguyên giáp", "đại tướng giáp"],
        "era": "Năm 1954 (Chiến dịch Điện Biên Phủ)",
        "battle": "Chiến dịch Điện Biên Phủ 1954",
        "enemies": ["de castries", "đờ cát", "thực dân pháp", "quân pháp"],
        "invariants": [
            "Tổng tư lệnh Quân đội Nhân dân Việt Nam chỉ huy Chiến dịch Điện Biên Phủ toàn thắng",
            "Chiến thắng 'lừng lẫy năm châu, chấn động địa cầu', bắt sống tướng De Castries ngày 7/5/1954",
            "Tuyệt đối không thất bại trước thực dân Pháp hay đầu hàng tướng De Castries"
        ],
        "defeat_regex": (
            r"(?i)(?:"
            r"\b(?:võ\s+nguyên\s+giáp|đại\s+tướng\s+(?:võ\s+nguyên\s+)?giáp)\b"
            r"(?:\s+(?:đã|lại|bị|phải|chịu|suýt|hoàn\s+toàn|cay\s+đắng|ở|tại\s+điện\s+biên(?:\s+phủ)?)){0,4}\s+"
            r"(?:thua\s+trận|thất\s+bại|bại\s+trận|đại\s+bại|đầu\s+hàng|thua\s+cuộc|quy\s+hàng|thua\s+(?:quân\s+)?pháp|thua\s+đờ\s+cát|bị\s+(?:bắt|giết|tiêu\s+diệt))\b"
            r"|"
            r"\b(?:võ\s+nguyên\s+giáp|đại\s+tướng\s+(?:võ\s+nguyên\s+)?giáp)\b.*?\b(?:đầu\s+hàng|quy\s+hàng|chịu\s+thua)\s+(?:quân\s+)?(?:pháp|đờ\s+cát|de\s+castries)\b"
            r"|"
            r"\b(?:thất\s+bại|sự\s+thất\s+bại|việc\s+đầu\s+hàng)\s+của\s+(?:đại\s+tướng\s+)?(?:võ\s+nguyên\s+)?giáp\b"
            r")"
        )
    },
    "chien_dich_ho_chi_minh": {
        "names": ["chiến dịch hồ chí minh", "đại thắng mùa xuân 1975", "ngày 30/4", "30/4/1975"],
        "era": "Tháng 4 năm 1975",
        "battle": "Chiến dịch Hồ Chí Minh lịch sử",
        "enemies": ["quân xâm lược", "chính quyền sài gòn"],
        "invariants": [
            "Chiến dịch Hồ Chí Minh lịch sử, tiến vào Dinh Độc Lập trưa ngày 30 tháng 4 năm 1975",
            "Giải phóng hoàn toàn miền Nam, thống nhất non sông đất nước",
            "Tuyệt đối không thất bại hay đảo ngược đại thắng non sông"
        ],
        "defeat_regex": r"(?i)\b(?:chiến\s+dịch\s+hồ\s+chí\s+minh|đại\s+thắng\s+mùa\s+xuân\s+1975|ngày\s+30\/4)\b.*?\b(?:thất\s+bại\s+hoàn\s+toàn|quân\s+ta\s+bị\s+tiêu\s+diệt|không\s+thống\s+nhất\s+được|thất\s+bại\s+năm\s+1975)\b"
    }
}

# Major battles and general battle distortion checks
BATTLE_OUTCOME_DISTORTION_PATTERNS = [
    (r"(?i)\btrận\s+bạch\s+đằng\b.*?\b(?:quân\s+ta\s+thua|đại\s+việt\s+thất\s+bại|nguyên\s+mông\s+toàn\s+thắng|nam\s+hán\s+toàn\s+thắng)\b", "Xuyên tạc kết quả trận Bạch Đằng lịch sử."),
    (r"(?i)\btrận\s+như\s+nguyệt\b.*?\b(?:quân\s+ta\s+thua|đại\s+việt\s+thất\s+bại|nhà\s+tống\s+chiếm\s+thăng\s+long|tống\s+toàn\s+thắng)\b", "Xuyên tạc kết quả trận chiến phòng tuyến Như Nguyệt."),
    (r"(?i)\btrận\s+(?:ngọc\s+hồi|đống\s+đa)\b.*?\b(?:quang\s+trung\s+thua|tây\s+sơn\s+thất\s+bại|quân\s+thanh\s+chiếm\s+giữ\s+vững|quân\s+thanh\s+toàn\s+thắng)\b", "Xuyên tạc đại thắng Ngọc Hồi - Đống Đa 1789."),
    (r"(?i)\bkhởi\s+nghĩa\s+lam\s+sơn\b.*?\b(?:bị\s+quân\s+minh\s+tiêu\s+diệt\s+hoàn\s+toàn|lê\s+lợi\s+thất\s+bại\s+vĩnh\s+viễn|quân\s+minh\s+toàn\s+thắng)\b", "Xuyên tạc toàn thắng khởi nghĩa Lam Sơn."),
    (r"(?i)\b(?:trận\s+điện\s+biên\s+phủ|chiến\s+dịch\s+điện\s+biên\s+phủ)\b.*?\b(?:quân\s+ta\s+(?:thua|thất\s+bại)|việt\s+minh\s+(?:thua|thất\s+bại)|võ\s+nguyên\s+giáp\s+(?:thua|thất\s+bại)|quân\s+pháp\s+toàn\s+thắng|pháp\s+thắng\s+trận)\b", "Xuyên tạc đại thắng Điện Biên Phủ 1954."),
    (r"(?i)\b(?:chiến\s+dịch\s+hồ\s+chí\s+minh|mùa\s+xuân\s+1975)\b.*?\b(?:thất\s+bại\s+hoàn\s+toàn|quân\s+giải\s+phóng\s+bại\s+trận|không\s+giải\s+phóng\s+được)\b", "Xuyên tạc Đại thắng Mùa Xuân 1975."),
    (r"(?i)\btrận\s+rạch\s+gầm\s*[-–]\s*xoài\s+mút\b.*?\b(?:tây\s+sơn\s+thua|quân\s+xiêm\s+toàn\s+thắng)\b", "Xuyên tạc chiến thắng Rạch Gầm - Xoài Mút 1785."),
    (r"(?i)\btrận\s+vân\s+đồn\b.*?\b(?:trương\s+văn\s+hổ\s+thắng|đoàn\s+thuyền\s+lương\s+nguyên\s+vẹn|đại\s+việt\s+thua)\b", "Xuyên tạc chiến thắng Vân Đồn 1288.")
]


class HistoricalDistortionError(ValueError):
    """Raised when text violates Vietnamese historical invariants."""
    pass


class AISemanticHistoricalClassifier:
    """
    Two-pass hybrid classifier:
    Pass 1: Fast rule-based semantic evasion patterns (passive voice, inversion, metaphor).
    Pass 2: LLM semantic analysis fallback (if available).
    """
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def classify_semantic_distortion(self, text: str, context: str = "") -> Tuple[bool, float, str]:
        """
        Analyzes text for semantic distortions of Vietnamese history.
        Returns: (is_distortion: bool, confidence: float, violation_reason: str)
        """
        if not text or not isinstance(text, str):
            return False, 0.0, ""

        normalized_text = _normalize_historical_text(text)

        # Pass 1: Semantic evasion patterns
        # 1. Mongol triumph evasion on Bach Dang
        if _matches_normalized_historical_pattern(r"(?i)\b(?:quân\s+)?(?:mông\s+cổ|nguyên\s+mông|nam\s+hán)\b.*?\b(?:ca\s+khúc\s+khải\s+hoàn|khải\s+hoàn|toàn\s+thắng|đại\s+thắng|chiến\s+thắng|làm\s+chủ|thắng\s+lớn)\b.*?\b(?:sông\s+bạch\s+đằng|bạch\s+đằng)\b", normalized_text):
            return True, 0.95, "Xuyên tạc kết quả trận Bạch Đằng (quân xâm lược thắng)"
        if _matches_normalized_historical_pattern(r"(?i)\b(?:sông\s+bạch\s+đằng|bạch\s+đằng)\b.*?\b(?:quân\s+)?(?:mông\s+cổ|nguyên\s+mông|nam\s+hán)\b.*?\b(?:ca\s+khúc\s+khải\s+hoàn|khải\s+hoàn|toàn\s+thắng|đại\s+thắng|chiến\s+thắng)\b", normalized_text):
            return True, 0.95, "Xuyên tạc kết quả trận Bạch Đằng (quân xâm lược thắng)"

        # 2. De Castries / French victory inversion at Dien Bien Phu
        if _matches_normalized_historical_pattern(r"(?i)\b(?:tướng\s+)?(?:de\s+castries|đờ\s+cát|quân\s+pháp|thực\s+dân\s+pháp)\b.*?\b(?:mừng|uống\s+(?:champagne|sâm\s+panh)|nâng\s+ly(?:\s+(?:sâm\s+panh|champagne))?|sâm\s+panh|champagne|hân\s+hoan|toàn\s+thắng)\b.*?\b(?:(?:đánh\s+tan|tiêu\s+diệt)\s+(?:quân\s+đội\s+)?(?:việt\s+minh|quân\s+ta)|(?:chiến\s+thắng|toàn\s+thắng|đại\s+thắng|thắng\s+trận)\s*(?:tại|ở)?\s*(?:điện\s+biên|mường\s+thanh))\b", normalized_text):
            return True, 0.98, "Xuyên tạc lịch sử chiến dịch Điện Biên Phủ (quân Pháp thắng)"
        if _matches_normalized_historical_pattern(r"(?i)\b(?:tướng\s+)?(?:de\s+castries|đờ\s+cát)\b.*?\b(?:chiến\s+thắng\s+(?:tại|ở)?\s*(?:điện\s+biên|mường\s+thanh)|toàn\s+thắng\s+(?:tại|ở)?\s*(?:điện\s+biên|mường\s+thanh)|đánh\s+tan\s+việt\s+minh)\b", normalized_text):
            return True, 0.98, "Xuyên tạc lịch sử chiến dịch Điện Biên Phủ"

        # 3. Metaphorical defamation of hero Tran Quoc Toan
        if _matches_normalized_historical_pattern(r"(?i)\b(?:ngọn\s+cờ\s+thêu\s+sáu\s+chữ\s+vàng|cờ\s+thêu\s+sáu\s+chữ\s+vàng|sáu\s+chữ\s+vàng)\b.*?\b(?:chìm\s+nghỉm|vứt\s+bỏ|bị\s+đốt|rách\s+nát)\b.*?\b(?:quỳ\s+gối|bảo\s+toàn\s+tính\s+mạng|cầu\s+xin|xin\s+hàng)\b", normalized_text):
            return True, 0.92, "Xúc phạm hình tượng anh hùng thiếu niên Trần Quốc Toản"

        # 4. Other historic battle inversions
        if _matches_normalized_historical_pattern(r"(?i)\b(?:tôn\s+sĩ\s+nghị|quân\s+thanh|mãn\s+thanh)\b.*?\b(?:ca\s+khúc\s+khải\s+hoàn|toàn\s+thắng|tiêu\s+diệt\s+quân\s+tây\s+sơn)\b.*?\b(?:ngọc\s+hồi|đống\s+đa|thăng\s+long)\b", normalized_text):
            return True, 0.95, "Xuyên tạc đại thắng Ngọc Hồi - Đống Đa"

        if _matches_normalized_historical_pattern(r"(?i)\b(?:quách\s+quỳ|quân\s+tống|nhà\s+tống)\b.*?\b(?:chọc\s+thủng|vượt\s+qua|tiêu\s+diệt\s+đại\s+việt|toàn\s+thắng)\b.*?\b(?:như\s+nguyệt)\b", normalized_text):
            return True, 0.95, "Xuyên tạc chiến thắng phòng tuyến Như Nguyệt"

        # Pass 2: LLM semantic analysis fallback
        if self.llm:
            try:
                system_prompt = (
                    "Bạn là Hệ thống Thẩm định Lịch sử Quốc gia NarrAI. Phân tích ngữ nghĩa xem văn bản có XUYÊN TẠC, "
                    "ĐẢO NGƯỢC KẾT QUẢ CHIẾN TRANH hay BÔI NHỌ ANH HÙNG DÂN TỘC VIỆT NAM hay không (chú ý câu bị động, ẩn dụ).\n"
                    "Trả về JSON duy nhất: {\"is_distortion\": bool, \"confidence\": float, \"violation_reason\": str}"
                )
                resp = self.llm.chat([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text[:1500]}
                ], temperature=0.0, max_tokens=250, response_format={"type": "json_object"})
                parsed = json.loads(resp)
                if isinstance(parsed, dict) and parsed.get("is_distortion"):
                    return True, float(parsed.get("confidence", 0.9)), str(parsed.get("violation_reason", "Xuyên tạc lịch sử theo phân tích ngữ nghĩa AI"))
            except Exception:
                pass

        return False, 0.0, ""


class HistoricalGroundingGatekeeper:
    """
    Enforces historical fidelity for Vietnamese historical narratives.
    In CHINH_SU mode: strictly rejects historical distortions, revisionism, and falsehoods.
    In DA_SU mode: preserves macro historical truths while allowing fictional personal micro-perspectives.
    In HU_CAU_TU_DO mode: completely bypassed.
    """

    @classmethod
    def validate_historical_invariants(cls, text: str, mode: NarrativeMode = NarrativeMode.CHINH_SU, user_prompt: str = "") -> Tuple[bool, List[str]]:
        """
        Validates text against Vietnamese historical invariants.
        Returns (is_valid, list_of_violations).
        """
        if mode == NarrativeMode.HU_CAU_TU_DO:
            return True, []

        if not text or not isinstance(text, str):
            return True, []

        violations = []
        combined_text = f"{user_prompt}\n{text}".strip() if user_prompt else text
        normalized_text = _normalize_historical_text(combined_text)

        # Check character-specific defeat / distortion patterns
        for key, canon in VIETNAMESE_HISTORICAL_CANON.items():
            pattern = canon.get("defeat_regex")
            if pattern and _matches_normalized_historical_pattern(pattern, normalized_text):
                hero_name = canon["names"][0].title()
                violations.append(
                    f"HISTORICAL_VIOLATION: Phát hiện xuyên tạc hình tượng lịch sử anh hùng '{hero_name}'. "
                    f"Trong lịch sử dân tộc, {hero_name} luôn giữ vững khí tiết và giành chiến thắng vĩ đại."
                )

        # Check battle outcome distortions
        for pattern, desc in BATTLE_OUTCOME_DISTORTION_PATTERNS:
            if _matches_normalized_historical_pattern(pattern, normalized_text):
                violations.append(f"HISTORICAL_VIOLATION: {desc}")

        # Check AI semantic classifier for regex evasion
        if len(violations) == 0:
            classifier = AISemanticHistoricalClassifier()
            is_distorted, conf, reason = classifier.classify_semantic_distortion(combined_text)
            if is_distorted and conf >= 0.7:
                violations.append(f"HISTORICAL_VIOLATION: {reason}")

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


# ==============================================================================
# 7. AUTO-DETECTION OF NARRATIVE MODES (R2.4)
# ==============================================================================

class AutoDetectResult(tuple):
    """
    Subclass of tuple (mode, label) that also supports direct equality comparison
    with NarrativeMode (e.g. result == NarrativeMode.CHINH_SU) and attribute access.
    """
    def __new__(cls, mode: NarrativeMode, label: str):
        return super().__new__(cls, (mode, label))

    @property
    def mode(self) -> NarrativeMode:
        return self[0]

    @property
    def label(self) -> str:
        return self[1]

    def __eq__(self, other):
        if isinstance(other, (NarrativeMode, str)):
            return self[0] == other or (hasattr(self[0], "value") and self[0].value == other)
        return super().__eq__(other)


def auto_detect_narrative_mode(prompt: str, context: str = "", genre: str = "") -> AutoDetectResult:
    """
    Automatically detects the narrative mode from user prompt and context:
    1. CHÍNH SỬ: Focuses directly on canonical Vietnamese heroes or major patriotic battles.
    2. DÃ SỬ: Historical era/dynasty is real, but protagonist/plot is fictional perspective.
    3. HƯ CẤU TỰ DO: Free personal fiction (Sci-Fi, Cyberpunk, Xianxia, Western Fantasy, Urban).
    """
    combined = f"{genre} {context} {prompt}".lower().strip()

    # 1. Check Out of Domain (OOD) signals
    ood_signals = [
        "sci-fi", "science fiction", "cyberpunk", "isekai", "tiên hiệp", "tu chân",
        "phương tây", "ma pháp", "new york", "hogwarts", "phi thuyền", "thiên hà",
        "không gian", "đô thị", "vũ trụ", "tông môn", "võ hồn", "kim đan", "hệ thống"
    ]
    if any(sig in combined for sig in ood_signals):
        return AutoDetectResult(NarrativeMode.HU_CAU_TU_DO, "Hư cấu tự do")

    # 2. Check canonical heroes
    has_hero = False
    for hero_key, hero_data in VIETNAMESE_HISTORICAL_CANON.items():
        if hero_key.replace("_", " ") in combined:
            has_hero = True
            break
        for alias in hero_data.get("names", []):
            if alias in combined:
                has_hero = True
                break
        if has_hero:
            break

    # 3. Check historical battles and dynasties
    historical_battles = [
        "bạch đằng", "như nguyệt", "ngọc hồi", "đống đa", "lam sơn",
        "chi lăng", "xương giang", "điện biên phủ", "chiến dịch hồ chí minh",
        "rạch gầm", "xoài mút", "dạ trạch", "vạn xuân", "cổ loa", "đại la", "thăng long"
    ]
    has_battle = any(b in combined for b in historical_battles)

    historical_dynasties = [
        "nhà trần", "thời trần", "nhà lý", "thời lý", "nhà lê", "thời lê",
        "nhà nguyễn", "thời nguyễn", "tây sơn", "hùng vương", "âu lạc",
        "đại cồ việt", "đại việt", "thời kháng chiến", "thời kỳ bắc thuộc"
    ]
    has_dynasty = any(d in combined for d in historical_dynasties)

    if not (has_hero or has_battle or has_dynasty):
        return AutoDetectResult(NarrativeMode.HU_CAU_TU_DO, "Hư cấu tự do")

    # 4. Distinguish between CHINH_SU and DA_SU
    fictional_lens_markers = [
        "nghĩa sĩ vô danh", "người lính cấm vệ", "đôi trai gái", "thợ rèn",
        "cô gái thêu", "góc nhìn của", "chuyện tình thời chiến", "thiếu niên thời trần",
        "lữ khách", "người lính vô danh", "người lính thường", "dã sử", "phóng tác",
        "nhân vật tự nghĩ", "nghĩa sĩ thầm lặng", "chuyện tình"
    ]
    is_fictional_perspective = any(m in combined for m in fictional_lens_markers)

    if is_fictional_perspective:
        return AutoDetectResult(NarrativeMode.DA_SU, "Dã sử (Góc nhìn phóng tác)")

    if has_hero or has_battle:
        return AutoDetectResult(NarrativeMode.CHINH_SU, "Chính sử (Tôn trọng sự thật)")

    if has_dynasty:
        return AutoDetectResult(NarrativeMode.DA_SU, "Dã sử (Góc nhìn phóng tác)")

    return AutoDetectResult(NarrativeMode.HU_CAU_TU_DO, "Hư cấu tự do")


# ==============================================================================
# 8. COMMERCIAL IP REGISTRY & FANFICTION DISCLAIMER PROTECTION (R2)
# ==============================================================================

COMMERCIAL_IP_REGISTRY = {
    "Harry Potter": {
        "franchise": "Wizarding World / J.K. Rowling",
        "keywords": [
            "harry potter", "hermione", "hermione granger", "ron weasley", "voldemort",
            "dumbledore", "albus dumbledore", "hogwarts", "gryffindor", "slytherin",
            "hufflepuff", "ravenclaw", "quidditch", "tử thần thực tử", "chúa tể voldemort"
        ],
        "creative_alternatives": {
            "Harry Potter": "Hải Phong / Harry Vance",
            "Hogwarts": "Học viện Pháp thuật Thăng Long / Trường Cổ Sơn",
            "Voldemort": "Chúa tể U Hồn / Ma Tôn Hắc Ám"
        }
    },
    "Marvel Cinematic Universe": {
        "franchise": "Marvel / Disney",
        "keywords": [
            "iron man", "tony stark", "spider-man", "spiderman", "peter parker",
            "captain america", "steve rogers", "thanos", "thor odinson", "avengers",
            "hulk", "bruce banner", "black widow", "natasha romanoff", "wolverine",
            "x-men", "deadpool"
        ],
        "creative_alternatives": {
            "Iron Man": "Chiến giáp Kim Thần / Giáp Sắt Thần Binh",
            "Thanos": "Bá vương Tinh vân / Bạo chúa Không gian",
            "Spider-Man": "Người Nhện Thiếu Niên / Chu Vực"
        }
    },
    "DC Comics": {
        "franchise": "DC / Warner Bros",
        "keywords": [
            "batman", "bruce wayne", "superman", "clark kent", "joker",
            "wonder woman", "harley quinn", "gotham", "metropolis", "justice league"
        ],
        "creative_alternatives": {
            "Batman": "Hiệp sĩ Bóng đêm Dạ Thành / Ám Dạ Du Hiệp",
            "Gotham": "Thành phố Hắc Lạc / Đô thị Tội ác"
        }
    },
    "Anime & Manga": {
        "franchise": "Shueisha / Kodansha",
        "keywords": [
            "naruto", "sasuke", "kakashi", "sharingan", "luffy", "zoro",
            "one piece", "goku", "vegeta", "saiyan", "tanjiro", "nezuko",
            "gojo satoru", "sukuna", "jujutsu kaisen", "levi ackerman", "eren yeager"
        ],
        "creative_alternatives": {
            "Naruto": "Thiếu niên Phong Ma / Nhẫn giả Lôi Thần",
            "Gojo Satoru": "Ngũ Nhãn Tiên Sinh / Cường giả Vô Hạn"
        }
    },
    "Star Wars & Disney": {
        "franchise": "Lucasfilm / Disney",
        "keywords": [
            "darth vader", "luke skywalker", "jedi", "sith", "lightsaber",
            "yoda", "mickey mouse", "elsa", "olaf"
        ],
        "creative_alternatives": {
            "Jedi": "Hiệp sĩ Tinh Tế / Kiếm sĩ Quang Năng",
            "Lightsaber": "Thần kiếm Ánh sáng"
        }
    }
}


class CommercialIPResult(dict):
    """Result object behaving as a dict and unpackable as (has_ip, matched_ips, disclaimer)."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __iter__(self):
        yield self.get("has_commercial_ip", False)
        yield self.get("matched_ips", [])
        yield self.get("fanfiction_disclaimer", "")

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self.get("has_commercial_ip", False)
            if key == 1:
                return self.get("matched_ips", [])
            if key == 2:
                return self.get("fanfiction_disclaimer", "")
        return super().__getitem__(key)


def detect_commercial_ip(text: str) -> CommercialIPResult:
    """
    Scans text for protected commercial franchises.
    Returns CommercialIPResult (dict + unpackable 3-tuple).
    """
    if not text or not isinstance(text, str):
        return CommercialIPResult({
            "has_commercial_ip": False,
            "matched_ips": [],
            "matched_franchises": [],
            "creative_suggestions": {},
            "fanfiction_disclaimer": ""
        })

    text_lower = text.lower()
    matched_ips = []
    matched_franchises = []
    suggestions = {}

    for ip_name, ip_data in COMMERCIAL_IP_REGISTRY.items():
        franchise_matched = False
        for kw in ip_data["keywords"]:
            pattern = r"(?i)\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text_lower):
                matched_ips.append(kw)
                franchise_matched = True
        if franchise_matched:
            matched_franchises.append(ip_name)
            for orig, alt in ip_data.get("creative_alternatives", {}).items():
                if orig.lower() in text_lower:
                    suggestions[orig] = alt

    unique_ips = list(dict.fromkeys(matched_ips))
    has_ip = len(unique_ips) > 0
    disclaimer = (
        "⚠️ Tác phẩm fan fiction — không liên quan đến tác phẩm gốc và không nhằm mục đích thương mại."
        if has_ip else ""
    )

    return CommercialIPResult({
        "has_commercial_ip": has_ip,
        "matched_ips": unique_ips,
        "matched_franchises": matched_franchises,
        "creative_suggestions": suggestions,
        "fanfiction_disclaimer": disclaimer
    })
