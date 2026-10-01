from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

try:
    from services.ontology import (
        NarrativeMode,
        CulturalTier,
        HistoricalGroundingGatekeeper,
        TriTierOntologyResolver,
        SmartSelectiveLanguageFilter,
        resolve_ontology,
        normalize_narrative_mode,
        auto_detect_narrative_mode,
        HistoricalDistortionError,
    )
except ImportError:
    try:
        from backend.services.ontology import (
            NarrativeMode,
            CulturalTier,
            HistoricalGroundingGatekeeper,
            TriTierOntologyResolver,
            SmartSelectiveLanguageFilter,
            resolve_ontology,
            normalize_narrative_mode,
            auto_detect_narrative_mode,
            HistoricalDistortionError,
        )
    except ImportError:
        NarrativeMode = None
        CulturalTier = None
        HistoricalGroundingGatekeeper = None
        TriTierOntologyResolver = None
        SmartSelectiveLanguageFilter = None
        resolve_ontology = None
        normalize_narrative_mode = lambda x: x
        auto_detect_narrative_mode = None
        class HistoricalDistortionError(ValueError): pass


# ==============================================================================
# MODERN LIGHT NOVEL & WEB NOVEL WRITING ENGINE RULES (VIETNAMESE EDITION)
# ==============================================================================
LIGHT_NOVEL_ENGINE_RULES = """QUY TẮC ĐỘNG CƠ SÁNG TÁC LIGHT NOVEL & WEB NOVEL THỊNH HÀNH:

1. ĐIỂM NHÌN BÁM SÁT (TIGHT POV) & KHỞI ĐẦU BÙNG NỔ (IN MEDIAS RES):
   - Sử dụng Ngôi thứ nhất ("Tôi") hoặc Ngôi thứ ba bám sát (Tight 3rd-Person Limited) gắn chặt vào giác quan, nhận thức và lăng kính cảm xúc của nhân vật chính.
   - HOOK ĐỘC GIẢ NGAY TỪ CÂU ĐẦU TIÊN (In Medias Res): Quăng người đọc thẳng vào tâm điểm hành động, xung đột bùng nổ, tình thế nan giải hoặc khoảnh khắc bất thường.
   - TUYỆT ĐỐI CẤM 0% tả thời tiết mây gió dông dài ("trời thu se lạnh", "ánh nắng le lói chiếu qua kẽ lá"), bình minh/hoàng hôn sáo rỗng hoặc thuyết minh lịch sử bối cảnh dài dòng ở mở đầu.

2. HỆ THỐNG ĐỘC THOẠI NỘI TÂM ĐA TẦNG (RICH INTERIOR MONOLOGUE):
   - Đan xen dày đặc dòng độc thoại nội tâm sắc bén: phản ứng tâm lý tức thời, nỗi lo âu, toan tính chiến thuật, suy luận logic hoặc những câu tự giễu cợt, mỉa mai ngầm (dry wit).
   - Thể hiện sự giằng xé nội tâm, áp lực sinh tồn hoặc xung đột xã hội, tạo chiều sâu đồng cảm tột độ cho độc giả trẻ.

3. ĐỐI THOẠI SẮC BÉN, GÃY GỌN & KHẨU NGỮ GIỚI TRẺ HIỆN ĐẠI (SHARP YOUTH DIALOGUE):
   - Đối thoại tự nhiên, gãy gọn, đanh thép, mang hơi thở ngôn ngữ giới trẻ đương đại, giàu subtext (thao túng, thăm dò, che giấu hoặc mỉa mai).
   - TUYỆT ĐỐI CẤM ngữ điệu dịch thuật gượng gạo, văn dịch Hán Việt sến súa cổ lỗ ("ngươi/ta", "chẳng hay", "nói đoạn", "không khỏi hít vào một ngụm khí lạnh" - trừ khi truyện thuần cổ trang).
   - Đan xen vi hành động và biểu hiện sinh lý trong đối thoại: siết chặt ngón tay, khựng lại nửa nhịp, nuốt khan, nhếch khóe môi.

4. NHỊP ĐIỆU CÂU VĂN CO GIÃN & ĐOẠN VĂN THÔNG THOÁNG (FAST-PACED STACCATO PACING):
   - Lược bỏ mọi đoạn chuyển cảnh rườm rà (thức dậy, ăn sáng, di chuyển không mục đích).
   - Cảnh căng thẳng/hành động: Câu ngắn (3-7 từ), ngắt nhịp dồn dập, tạo nhịp tim đập nhanh.
   - Trình bày đoạn văn ngắn gọn (2-4 câu/đoạn), xuống dòng dứt khoát, tối ưu cho trải nghiệm đọc web novel lôi cuốn.

5. CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC NARRATIVE BEATS):
   - Beat 1: Hook (0-15%): Xung đột bùng nổ ngay lập tức, cuốn độc giả vào tình thế nan giải.
   - Beat 2: Rising Friction / Complication (15-40%): Trở ngại leo thang, phản ứng tâm lý và đối thoại va chạm dồn dập.
   - Beat 3: Turning Point (40-70%): Biến cố đảo chiều nhận thức hoặc kế hoạch phá sản, nhân vật buộc phải ra quyết định mạo hiểm.
   - Beat 4: Visceral Climax (70-90%): Đỉnh điểm cảm xúc hoặc hành động quyết định nghẹt thở.
   - Beat 5: Lingering Cliffhanger (90-100%): Nút thắt chưa gỡ, kích thích tột độ muốn đọc chương tiếp.

6. DANH MỤC CẤM KỴ (ANTI-CLICHÉ BANLIST):
   - CẤM sáo ngữ mở đầu và miêu tả sáo rỗng: "vầng trăng vằng vặc", "thời gian thấm thoắt thoi đưa", "hắn cười khẩy / cười lạnh", "mắt phượng mày ngài", "trời quang mây tạnh lòng người u sầu", "bỗng nhiên một chuyện bất ngờ xảy ra".
   - CẤM liệt kê tính từ trừu tượng chung chung ("cô ấy rất buồn", "hắn vô cùng tức giận"). Hãy thể hiện bằng hành vi thực tế và phản ứng sinh lý (Show, don't tell).
   - CẤM lặp từ dẫn thoại đơn điệu ("hắn nói", "cô ấy nói"). Hãy để hành động và biểu cảm dẫn dắt câu thoại.
   - CẤM TUYỆT ĐỐI sáo ngữ AI điển hình: "nhanh như nhịp tim chậm rãi", "khoảng trống trong lòng", "nỗi lo đè nặng lên vai", "thở dài giọng nhẹ", "trái tim đập thình thịch", "nụ cười bí ẩn nở trên môi", "đôi mắt sáng rực lên", "cảm xúc trào dâng trong lồng ngực", "lòng tôi chợt nặng trĩu", "một cảm giác kỳ lạ lan tỏa", "thế giới dường như dừng lại", "thời gian như ngừng trôi", "tim tôi nhói đau", "giọng nói ấm áp như nắng", "nỗi buồn man mác", "lòng nhẹ nhõm như trút được gánh nặng".
   - CẤM đoạn triết lý suông không phục vụ cốt truyện, tuyên ngôn đạo đức sáo rỗng cuối chương. Mọi suy ngẫm phải bật ra từ hành động cụ thể và tình huống kịch tính.

7. QUY TẮC SHOW, DON'T TELL - 4 TRỤ CỘT (4-PILLAR SHOW DON'T TELL):
   - TRỤ 1 - CẢM GIÁC THỂ XÁC CỤ THỂ (Visceral Physical Sensations): Thay vì "anh ấy sợ" → "lưng áo ướt đẫm mồ hôi lạnh, cổ họng siết lại, móng tay cào vào lòng bàn tay". Luôn gắn cảm xúc với phản ứng sinh lý thực tế.
   - TRỤ 2 - VI HÀNH ĐỘNG (Micro-Actions): Thay vì "cô ấy lo lắng" → "ngón tay gõ liên hồi lên mặt bàn, đầu bút bi bấm lên bấm xuống không ngừng". Hành vi vô thức tiết lộ nội tâm.
   - TRỤ 3 - BIỂU CẢM VI MÔ (Micro-Expressions): Thay vì "hắn tức giận" → "cơ hàm siết chặt, khóe mắt co lại, mạch máu thái dương nổi lên rõ rệt". Khuôn mặt là bản đồ cảm xúc.
   - TRỤ 4 - TƯƠNG TÁC VẬT LÝ (Physical Object Interactions): Thay vì "cô ấy buồn" → "cô xoay chiếc nhẫn trên ngón áp út, nhìn chằm chằm vào vết cà phê loang trên giấy". Đồ vật trở thành biểu tượng cảm xúc."""

WRITING_RULES = LIGHT_NOVEL_ENGINE_RULES
MODERN_NOVEL_WRITING_RULES = LIGHT_NOVEL_ENGINE_RULES


# ==============================================================================
# PROGRAMMATIC ANTI-CLICHÉ COMPLIANCE VALIDATOR
# ==============================================================================
import re as _re
from typing import Tuple, List

# Comprehensive AI cliché patterns - regex for flexible matching
AI_CLICHE_BANLIST = [
    # Vietnamese AI tropes
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
    # Classical clichés
    r"vầng trăng vằng vặc",
    r"thời gian thấm thoắt thoi đưa",
    r"hắn cười khẩy",
    r"cười lạnh",
    r"mắt phượng mày ngài",
    r"trời quang mây tạnh lòng người u sầu",
    r"bỗng nhiên một chuyện bất ngờ xảy ra",
    # Common lazy patterns
    r"cô ấy rất buồn",
    r"hắn vô cùng tức giận",
    r"không khỏi hít vào một ngụm khí lạnh",
    r"giọng nói run rẩy",
    r"đôi mắt ngấn lệ",
    r"nắm chặt tay thành nắm đấm",
    r"tim đập loạn nhịp",
    r"một giọt nước mắt lăn dài trên má",
    r"ánh mắt lạnh lẽo như băng",
    r"nụ cười ấm áp",
    r"trái tim tan vỡ",
]

def validate_anti_cliche_compliance(text: str, genre: str = "", narrative_mode: Any = None) -> Tuple[bool, List[str]]:
    """
    Validates generated text against the AI cliché banlist and Chinese translation clichés.
    Delegates to SmartSelectiveLanguageFilter when available.
    Returns (is_clean, list_of_violations).
    """
    if not text or not isinstance(text, str):
        return True, []

    if SmartSelectiveLanguageFilter is not None:
        mode_enum = normalize_narrative_mode(narrative_mode) if normalize_narrative_mode else NarrativeMode.HU_CAU_TU_DO
        return SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            text=text,
            genre=genre,
            narrative_mode=mode_enum
        )

    violations = []
    text_lower = text.lower()
    for pattern in AI_CLICHE_BANLIST:
        matches = list(_re.finditer(pattern, text_lower))
        for m in matches:
            # Find approximate line by counting newlines before match
            line_num = text[:m.start()].count('\n') + 1
            snippet = text[max(0, m.start() - 20):m.end() + 20].replace('\n', ' ')
            violations.append(f"Line ~{line_num}: '{m.group()}' in \"...{snippet}...\"")

    return len(violations) == 0, violations


class StoryGenerator:
    def __init__(self):
        self.llm = GroqClient(model_name="openai/gpt-oss-120b")

    def _extract_narrative_ontology(self, refined_prompt: str, narrative_mode: Any = None, genre: str = "") -> str:
        """
        Trích xuất Bộ khung Dynamic Scene-Graph Ontology (3 Chiều: Thực thể - Không gian - Thời đại) & Chuỗi 5 Nhịp Kịch Tính:
        - Thực thể & Nhân vật (Entities & Tight POV)
        - Quan hệ & Động cơ xung đột ngầm (Conflict Matrix)
        - Tiền đề thế giới & Không gian neo giữ (World Axioms & Spatial Anchors)
        - Không gian phân cảnh (Spatial Scene Enclosure)
        - Cấu trúc 5 Nhịp Kịch Tính (5 Dramatic Narrative Beats)
        """
        mode_enum = normalize_narrative_mode(narrative_mode) if normalize_narrative_mode else NarrativeMode.HU_CAU_TU_DO
        mode_note = ""
        if mode_enum == NarrativeMode.CHINH_SU:
            mode_note = "\nCHẾ ĐỘ SÁNG TÁC: CHÍNH SỬ (Tuân thủ nghiêm ngặt sự thật lịch sử Đại Việt, tuyệt đối không xuyên tạc biến cố hay nhân vật có thật)."
        elif mode_enum == NarrativeMode.DA_SU:
            mode_note = "\nCHẾ ĐỘ SÁNG TÁC: DÃ SỬ (Bối cảnh lịch sử có thật, nhân vật chính hư cấu vi mô, neo giữ tinh thần thời đại)."

        prompt = f"""Phân tích bản phác thảo và trích xuất BỘ KHUNG NARRATIVE ONTOLOGY (RÀNG BUỘC 3 CHIỀU) & CẤU TRÚC 5 NHỊP KỊCH TÍNH:{mode_note}
BẢN PHÁC THẢO:
{refined_prompt[:3000]}

Yêu cầu xuất ra cấu trúc chính xác sau:
[THỰC THỂ & NHÂN VẬT]: (Tên, điểm nhìn POV bám sát, ngoại hình nhận diện, mục tiêu ngầm, điểm yếu chí mạng)
[QUAN HỆ & ĐỘNG CƠ]: (Mối quan hệ cụ thể và điểm ngờ vực ngầm giữa các nhân vật)
[QUY TẮC THẾ GIỚI & BỐI CẢNH (WORLD AXIOMS)]: (Địa điểm cụ thể, thời đại, các quy tắc bất biến không thể phá vỡ)
[KHÔNG GIAN PHÂN CẢNH & NEO GIỮ KIẾN TRÚC (SPATIAL SCENE ENCLOSURE)]: (Tên phòng/khu vực ban đầu, ranh giới khép kín, đạo cụ cố định, cấm trôi dạt ngoại cảnh)
[CHUỖI NHÂN QUẢ CHÍNH]: (Nguyên nhân A -> Dẫn đến hệ quả B -> Đẩy vào xung đột C)
[CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC BEATS)]:
  + Beat 1: Hook (0-15%): Xung đột bùng nổ ngay lập tức, cuốn độc giả vào tình thế nan giải.
  + Beat 2: Rising Friction / Complication (15-40%): Trở ngại leo thang, phản ứng tâm lý và đối thoại va chạm.
  + Beat 3: Turning Point (40-70%): Biến cố đảo chiều nhận thức hoặc kế hoạch phá sản.
  + Beat 4: Visceral Climax (70-90%): Đỉnh điểm cảm xúc hoặc hành động quyết định.
  + Beat 5: Lingering Cliffhanger (90-100%): Nút thắt chưa gỡ, kích thích tột độ muốn đọc chương tiếp.
"""
        try:
            ontology_text = self.llm.chat(
                messages=[
                    {"role": "system", "content": "Bạn là Kiến trúc sư Dynamic Scene-Graph Ontology kiêm Chuyên gia Light Novel. Trích xuất Bộ khung Narrative Ontology 3 chiều và Cấu trúc 5 Nhịp Kịch Tính ngắn gọn, chính xác."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=950
            )
            if ontology_text and ontology_text.strip():
                return ontology_text.strip()
            
            if mode_enum in (NarrativeMode.CHINH_SU, NarrativeMode.DA_SU):
                world_axiom = "Đại Việt lịch sử chính thống, tuân thủ đúng niên đại, chiến cục và cốt cách danh nhân."
                enc_note = "Đại bản doanh chiến dịch, doanh trại quân ngũ hoặc hoàng cung tôn nghiêm."
            else:
                world_axiom = "Hiện đại, tuân thủ logic thực tế, cấm phép màu vô lý."
                enc_note = "Không gian khép kín ban đầu, neo giữ vị trí, cấm trôi dạt ngoại cảnh."

            return (
                f"[THỰC THỂ & NHÂN VẬT]:\n{refined_prompt[:400]}\n"
                f"[QUAN HỆ & ĐỘNG CƠ]: Xung đột mục tiêu ngầm và áp lực nội tâm.\n"
                f"[QUY TẮC THẾ GIỚI & BỐI CẢNH (WORLD AXIOMS)]: {world_axiom}\n"
                f"[KHÔNG GIAN PHÂN CẢNH & NEO GIỮ KIẾN TRÚC (SPATIAL SCENE ENCLOSURE)]: {enc_note}\n"
                f"[CHUỖI NHÂN QUẢ CHÍNH]: Khởi phát -> Leo thang -> Bùng nổ.\n"
                f"[CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC BEATS)]:\n"
                f"  + Beat 1: Hook (0-15%): Xung đột bùng nổ ngay lập tức.\n"
                f"  + Beat 2: Rising Friction (15-40%): Trở ngại leo thang, tâm lý dồn nén.\n"
                f"  + Beat 3: Turning Point (40-70%): Biến cố đảo chiều nhận thức.\n"
                f"  + Beat 4: Visceral Climax (70-90%): Đỉnh điểm cảm xúc và va chạm.\n"
                f"  + Beat 5: Lingering Cliffhanger (90-100%): Nút thắt chưa gỡ kết thúc chương."
            )
        except Exception as e:
            if mode_enum in (NarrativeMode.CHINH_SU, NarrativeMode.DA_SU):
                world_axiom = "Đại Việt lịch sử chính thống, tuân thủ đúng niên đại, chiến cục và cốt cách danh nhân."
                enc_note = "Đại bản doanh chiến dịch, doanh trại quân ngũ hoặc hoàng cung tôn nghiêm."
            else:
                world_axiom = "Hiện đại, tuân thủ logic thực tế, cấm phép màu vô lý."
                enc_note = "Không gian khép kín ban đầu, neo giữ vị trí, cấm trôi dạt ngoại cảnh."

            return (
                f"[THỰC THỂ & NHÂN VẬT]:\n{refined_prompt[:400]}\n"
                f"[QUAN HỆ & ĐỘNG CƠ]: Xung đột mục tiêu ngầm và áp lực nội tâm.\n"
                f"[QUY TẮC THẾ GIỚI & BỐI CẢNH (WORLD AXIOMS)]: {world_axiom}\n"
                f"[KHÔNG GIAN PHÂN CẢNH & NEO GIỮ KIẾN TRÚC (SPATIAL SCENE ENCLOSURE)]: {enc_note}\n"
                f"[CHUỖI NHÂN QUẢ CHÍNH]: Khởi phát -> Leo thang -> Bùng nổ.\n"
                f"[CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC BEATS)]:\n"
                f"  + Beat 1: Hook (0-15%): Xung đột bùng nổ ngay lập tức.\n"
                f"  + Beat 2: Rising Friction (15-40%): Trở ngại leo thang, tâm lý dồn nén.\n"
                f"  + Beat 3: Turning Point (40-70%): Biến cố đảo chiều nhận thức.\n"
                f"  + Beat 4: Visceral Climax (70-90%): Đỉnh điểm cảm xúc và va chạm.\n"
                f"  + Beat 5: Lingering Cliffhanger (90-100%): Nút thắt chưa gỡ kết thúc chương."
            )

    def _get_config(self, story_length: str):
        config = {
            "short": {"word_range": "Khoảng 1200 đến 2200 từ", "max_tokens": 5500, "chapter_mode": False},
            "medium": {"word_range": "Khoảng 2500 đến 4000 từ", "max_tokens": 6000, "chapter_mode": False},
            "long": {"word_range": "Khoảng 1800 đến 2500 từ cho CHƯƠNG NÀY", "max_tokens": 6000, "chapter_mode": True}
        }
        return config.get(story_length, config["medium"])

    def _build_prompt(self, refined_prompt: str, story_length: str = "medium", narrative_mode: Any = None, genre: str = ""):
        cfg = self._get_config(story_length)
        if narrative_mode is None and auto_detect_narrative_mode is not None:
            mode_enum, _ = auto_detect_narrative_mode(refined_prompt, genre=genre)
        else:
            mode_enum = normalize_narrative_mode(narrative_mode) if normalize_narrative_mode else NarrativeMode.HU_CAU_TU_DO
        ontology_block = self._extract_narrative_ontology(refined_prompt, narrative_mode=mode_enum, genre=genre)

        mode_directives = ""
        if HistoricalGroundingGatekeeper is not None:
            mode_directives += HistoricalGroundingGatekeeper.get_historical_grounding_prompt(mode_enum)
        if SmartSelectiveLanguageFilter is not None:
            mode_directives += SmartSelectiveLanguageFilter.get_prompt_cliche_instructions(genre, mode_enum)
        if TriTierOntologyResolver is not None:
            sim = TriTierOntologyResolver.calculate_cultural_similarity(refined_prompt, genre=genre)
            tier = TriTierOntologyResolver.resolve_tier(sim)
            mode_directives += TriTierOntologyResolver.get_honorifics_guidelines(tier, mode_enum)

        system_prompt = f"""Bạn là Bút vàng chuyên gia sáng tác Light Novel & Web Novel thịnh hành, chuyên sáng tác các tác phẩm lôi cuốn, kịch tính, nhịp độ dồn dập dành cho giới trẻ bằng tiếng Việt hiện đại.
TUYỆT ĐỐI CHỈ VIẾT BẰNG TIẾNG VIỆT, văn phong tự nhiên, giàu sắc thái đương đại, không lai tạp tiếng Anh.
{mode_directives}
=== BỘ KHUNG NARRATIVE ONTOLOGY & 5 DRAMATIC BEATS (BẤT BIẾN - TUYỆT ĐỐI TUÂN THỦ) ===
{ontology_block}
====================================================================

{LIGHT_NOVEL_ENGINE_RULES}

NHIỆM VỤ: Dựa vào "Bộ khung Narrative Ontology" và "Cấu trúc 5 Nhịp Kịch Tính (5 Dramatic Beats)", hãy viết câu chuyện hoàn chỉnh với nhịp độ dồn dập, giàu độc thoại nội tâm và đối thoại sắc bén. Triển khai đầy đủ qua 5 nhịp kịch tính: Hook -> Rising Friction -> Turning Point -> Visceral Climax -> Lingering Cliffhanger. Không đổi tên nhân vật hay chệch hướng logic.

ĐỘ DÀI: Khoảng {cfg['word_range']}. Phân bổ tình tiết theo đúng sườn 5 nhịp kịch tính, đoạn văn ngắn gọn, thoáng đãng."""
        if cfg['chapter_mode']:
            system_prompt += """
CHẾ ĐỘ VIẾT TỪNG CHƯƠNG:
- Chỉ được viết DUY NHẤT 1 CHƯƠNG (1800-2500 từ).
- Bắt đầu dòng 1 bằng tiêu đề: ## Chương X: [Tên chương]
- Triển khai trọn vẹn 5 nhịp kịch tính: Mở đầu bằng Hook bùng nổ, phát triển trở ngại, tạo bước ngoặt đảo chiều, đẩy lên cao trào và KẾT THÚC bằng Cliffhanger nghẹt thở.
- KHÔNG viết thêm chương nào khác."""
        else:
            system_prompt += """
QUY TẮC CHƯƠNG:
- Mỗi chương có Tiêu đề: ## Chương X: [Tên chương]
- Mỗi chương phải vận hành theo 5 nhịp kịch tính để duy trì sức hút liên tục.
- Tối thiểu 800 từ/chương. Truyện ngắn: tối đa 3-4 chương. Truyện trung bình: tối đa 5-6 chương."""

        system_prompt += """

Bản Phác Thảo Cốt Truyện:
Quy tắc định dạng:
- Dùng markdown (##) cho tiêu đề Chương.
- Bắt đầu NGAY LẬP TỨC bằng: **[TÊN TIÊU ĐỀ TRUYỆN]** ở dòng đầu tiên.
- TUYỆT ĐỐI KHÔNG thêm lời mở đầu hay kết thúc mang tính trò chuyện."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"BAN PHAC THAO COT TRUYEN YEU CAU:\n---\n{refined_prompt}\n---\n\nHay bat dau viet ngay bay gio:"}
        ]
        return messages, cfg["max_tokens"]

    # ===== LEGACY METHODS (giữ tương thích ngược) =====
    def generate_story(self, refined_prompt: str, story_length: str = "medium", narrative_mode: Any = None, genre: str = "") -> str:
        if narrative_mode is None and auto_detect_narrative_mode is not None:
            detected_mode, _ = auto_detect_narrative_mode(refined_prompt, genre=genre)
            mode_enum = detected_mode
        else:
            mode_enum = normalize_narrative_mode(narrative_mode) if normalize_narrative_mode else NarrativeMode.HU_CAU_TU_DO

        # Preflight check on input prompt
        if HistoricalGroundingGatekeeper is not None:
            pre_valid, pre_violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                refined_prompt, mode=mode_enum, user_prompt=refined_prompt
            )
            if not pre_valid:
                raise HistoricalDistortionError(f"Vi phạm tính chân thực lịch sử Việt Nam: {'; '.join(pre_violations)}")

        messages, max_tokens = self._build_prompt(refined_prompt, story_length, narrative_mode=mode_enum, genre=genre)
        raw_story = self.llm.chat(messages, temperature=0.8, max_tokens=max_tokens)

        # Post-generation validation
        if HistoricalGroundingGatekeeper is not None:
            post_valid, post_violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                raw_story, mode=mode_enum, user_prompt=refined_prompt
            )
            if not post_valid:
                raise HistoricalDistortionError(f"Phát hiện nội dung sinh ra vi phạm lịch sử: {'; '.join(post_violations)}")

        return raw_story

    def generate_story_stream(self, refined_prompt: str, story_length: str = "medium", narrative_mode: Any = None, genre: str = ""):
        if narrative_mode is None and auto_detect_narrative_mode is not None:
            detected_mode, _ = auto_detect_narrative_mode(refined_prompt, genre=genre)
            mode_enum = detected_mode
        else:
            mode_enum = normalize_narrative_mode(narrative_mode) if normalize_narrative_mode else NarrativeMode.HU_CAU_TU_DO

        # Preflight check on input prompt
        if HistoricalGroundingGatekeeper is not None:
            pre_valid, pre_violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                refined_prompt, mode=mode_enum, user_prompt=refined_prompt
            )
            if not pre_valid:
                raise HistoricalDistortionError(f"Vi phạm tính chân thực lịch sử Việt Nam: {'; '.join(pre_violations)}")

        messages, max_tokens = self._build_prompt(refined_prompt, story_length, narrative_mode=mode_enum, genre=genre)
        return self.llm.chat_stream(messages, temperature=0.8, max_tokens=max_tokens)

    # ===== NEW: Memory-based Chapter Generation =====
    def generate_chapter_stream(self, memory: StoryMemory, user_instruction: str = ""):
        """Viết 1 chương mới dựa trên Memory System & 5 Dramatic Narrative Beats (streaming)."""
        bible_block = memory.story_bible.to_prompt_block()
        memory_block = memory.to_prompt_block()
        short_context = memory.get_short_context(max_chars=6000)
        next_chapter = memory.current_chapter + 1

        genre = getattr(memory.story_bible, "genre", "")
        raw_mode = getattr(memory.story_bible, "narrative_mode", None)
        if not raw_mode and getattr(memory, "dynamic_scene_graph", None):
            raw_mode = getattr(memory.dynamic_scene_graph, "narrative_mode", None)
        mode_enum = normalize_narrative_mode(raw_mode) if normalize_narrative_mode else NarrativeMode.HU_CAU_TU_DO

        mode_directives = ""
        if HistoricalGroundingGatekeeper is not None:
            mode_directives += HistoricalGroundingGatekeeper.get_historical_grounding_prompt(mode_enum)
        if SmartSelectiveLanguageFilter is not None:
            mode_directives += SmartSelectiveLanguageFilter.get_prompt_cliche_instructions(genre, mode_enum)
        if TriTierOntologyResolver is not None:
            c_tier = getattr(memory.story_bible, "cultural_tier", None)
            if c_tier is None and getattr(memory, "dynamic_scene_graph", None):
                c_tier = getattr(memory.dynamic_scene_graph, "cultural_tier", 1)
            tier_enum = CulturalTier(c_tier) if c_tier in (1, 2, 3) else CulturalTier.TIER_1_CANONICAL_VN
            mode_directives += TriTierOntologyResolver.get_honorifics_guidelines(tier_enum, mode_enum)

        system_prompt = f"""Bạn là Bút vàng chuyên gia sáng tác Light Novel & Web Novel thịnh hành, đang trực tiếp chấp bút chương mới bằng tiếng Việt hiện đại.
NHIỆM VỤ CỦA BẠN LÀ VIẾT VĂN XUÔI CHƯƠNG TRUYỆN NGAY BÂY GIỜ, không phân tích, không giải thích, không hỏi lại người dùng.
TUYỆT ĐỐI KHÔNG viết lời chào, lời xin lỗi hay bất kỳ câu trò chuyện phi văn xuôi nào.
TUYỆT ĐỐI CHỈ VIẾT BẰNG TIẾNG VIỆT VĂN XUÔI NGUYÊN BẢN.
{mode_directives}
{bible_block}

{memory_block}

{LIGHT_NOVEL_ENGINE_RULES}

YÊU CẦU BẮT BUỘC CHO CHƯƠNG {next_chapter}:
- Viết DUY NHẤT 1 chương, độ dài 2000-3000 từ.
- Bắt đầu dòng 1 bằng tiêu đề: ## Chương {next_chapter}: [Tên chương gợi mở kịch tính]
- BẮT BUỘC TRIỂN KHAI THEO CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC BEATS):
  1. Beat 1: Hook (0-15%): Xung đột bùng nổ ngay lập tức từ câu đầu tiên, nối tiếp tình thế của chương trước, 0% tả thời tiết mây gió dông dài.
  2. Beat 2: Rising Friction / Complication (15-40%): Trở ngại và biến số mới leo thang, phản ứng tâm lý giằng xé và đối thoại va chạm dồn dập.
  3. Beat 3: Turning Point (40-70%): Biến cố đảo chiều nhận thức hoặc kế hoạch phá sản, nhân vật đưa ra lựa chọn liều lĩnh/chủ động.
  4. Beat 4: Visceral Climax (70-90%): Đỉnh điểm cảm xúc hoặc đối đầu quyết định nghẹt thở (lời thoại đanh thép, hành động cao trào).
  5. Beat 5: Lingering Cliffhanger (90-100%): Nút thắt chưa gỡ cực mạnh, hé lộ bí mật mới hoặc hiểm họa cận kề, kích thích tột độ muốn đọc chương tiếp theo.
- Giàu độc thoại nội tâm sắc bén, điểm nhìn bám sát (Tight POV), đối thoại tự nhiên mang ngôn ngữ giới trẻ hiện đại, câu văn co giãn staccato, đoạn văn thoáng đãng (2-4 câu/đoạn).
- TUYỆT ĐỐI KHÔNG in ra nhãn kỹ thuật (không ghi "Beat 1:", "Nhịp 1:"). Viết văn xuôi thuần túy.
- TUYỆT ĐỐI KHÔNG thêm lời mở đầu hay kết thúc mang tính trò chuyện."""

        spatial_enclosure_note = ""
        if getattr(memory, "dynamic_scene_graph", None):
            enc = memory.dynamic_scene_graph.get_active_enclosure()
            if enc:
                spatial_enclosure_note = (
                    f"\nKHÓA CHẶT KHÔNG GIAN PHÂN CẢNH (SPATIAL SCENE ENCLOSURE):\n"
                    f"- Địa điểm phân cảnh: {enc.name} | Kiến trúc: {enc.architectural_anchor or 'Phòng khép kín'}.\n"
                    f"- CẤM 100% việc tự ý dời cảnh ra ngoài phố, vỉa hè hay ngoại cảnh nếu không có hành động di chuyển cụ thể.\n"
                    f"- Giữ vững tính nhất quán thời đại: {memory.dynamic_scene_graph.era_genre.era_name}.\n"
                )

        if spatial_enclosure_note:
            system_prompt += f"\n\n{spatial_enclosure_note}"

        if user_instruction:
            system_prompt += f"\n\nYEU CAU DAC BIET TU TAC GIA: {user_instruction}"

        user_msg = f"Hay viet CHUONG {next_chapter} ngay bay gio. Dong dau tien phai la: ## Chuong {next_chapter}: [Ten chuong]. Sau do viet ngay van xuoi, khong giai thich."
        if short_context:
            user_msg = f"NOI DUNG GAN NHAT DA VIET:\n---\n{short_context[-3000:]}\n---\n\nHay viet CHUONG {next_chapter} tiep noi tu nhien theo 5 nhip kich tinh. Dong dau tien phai la: ## Chuong {next_chapter}: [Ten chuong]. Khong giai thich, chi viet van xuoi:"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]
        return self.llm.chat_stream(messages, temperature=0.8, max_tokens=6000)

    def generate_ending_stream(self, memory: StoryMemory):
        """Viết đoạn kết thúc truyện dựa trên Memory & chuẩn Light Novel."""
        bible_block = memory.story_bible.to_prompt_block()
        memory_block = memory.to_prompt_block()
        short_context = memory.get_short_context(max_chars=6000)

        system_prompt = f"""Bạn là Bút vàng chuyên gia sáng tác Light Novel & Web Novel thịnh hành, chuyên sáng tác truyện bằng tiếng Việt hiện đại.
TUYỆT ĐỐI CHỈ VIẾT BẰNG TIẾNG VIỆT.

{bible_block}

{memory_block}

{LIGHT_NOVEL_ENGINE_RULES}

NHIỆM VỤ: Viết ĐOẠN KẾT THÚC cho câu chuyện theo chuẩn Light Novel / Web Novel.
- Gói gọn TẤT CẢ các tuyến truyện đang mở.
- Giải quyết xung đột chính bằng cao trào cảm xúc hoặc hành động quyết liệt.
- Giàu độc thoại nội tâm, đối thoại sắc bén, mang lại cảm xúc trọn vẹn sâu sắc cho người đọc.
- Không kết thúc đột ngột hay gãy mạch.
- Dài tối thiểu 2000 từ.
- TUYỆT ĐỐI KHÔNG in ra nhãn kỹ thuật."""

        user_msg = f"NOI DUNG GAN NHAT:\n---\n{short_context[-3000:]}\n---\n\nHay viet doan ket thuc cau chuyen:"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]
        return self.llm.chat_stream(messages, temperature=0.8, max_tokens=6000)

    # ===== LEGACY: Chat instruction (giữ tương thích) =====
    def handle_chat_instruction(self, current_story: str, user_message: str):
        import json
        import re

        system_prompt = f"""Ban la Tro ly AI dong sang tac tieu thuyet.

NHIEM VU: Doc lenh cua nguoi dung va thuc hien chinh xac.
- Neu ho yeu cau "viet tiep", "them nhan vat", "doi huong": VIET TIEP DOAN TRUYEN MOI.
- Neu ho yeu cau "ket thuc truyen": Viet doan ket thuc mach lac.
- Neu ho chi hoi dap binh thuong: Tra loi than thien.

TRUYEN DA VIET TU TRUOC (5000 ky tu cuoi):
---
{current_story[-5000:] if len(current_story) > 5000 else current_story}
---

LENH CUA NGUOI DUNG: "{user_message}"

DAU RA BAT BUOC LA JSON:
{{
    "chat_reply": "Cau tra loi ngan gon gui cho nguoi dung",
    "new_story_content": "Phan truyen MOI VIET THEM. Neu khong can viet them, de chuoi rong."
}}"""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Hay thuc hien yeu cau va tra ve JSON."}
            ]
            response = self.llm.chat(messages=messages, temperature=0.7, max_tokens=4000)
            json_match = re.search(r'\{.*\}', response.replace('\n', ' '), re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(response)
        except Exception as e:
            print("Chat Error:", e)
            return {"chat_reply": "Xin loi, da co loi xay ra.", "new_story_content": ""}
