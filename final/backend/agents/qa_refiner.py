import os
import re
import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from llm.groq_client import GroqClient

logger = logging.getLogger("narrai.qa_refiner")


class QARefiner:
    """
    QARefiner: AI Co-creation & Narrative Intake Agent with Dual-Matrix Resilience.
    Supports Multi-Model Fallback and Multi-Key Fallback across Groq endpoints,
    preserving full backward compatibility with existing unit test mocks on self.llm.
    """

    MODELS = [
        "qwen/qwen3.8-27b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]

    KEY_ENV_VARS = [
        "GROQ_API_KEY_BIBLE",
        "GROQ_API_KEY",
        "GROQ_API_KEY_COPILOT",
    ]

    SYSTEM_PROMPT = """Bạn là Chuyên gia Đồng sáng tác Văn học & Cố vấn Cốt truyện NarrAI cao cấp, vận hành theo phong cách trò chuyện thông minh, tinh tế, sâu sắc và súc tích như Gemini và ChatGPT.

NHIỆM VỤ: Lắng nghe ý tưởng sáng tác của tác giả, phân tích sâu và đặt câu hỏi gợi mở để cùng hoàn thiện một cốt truyện độc đáo, cuốn hút.

TRI THỨC THỂ LOẠI TÍCH HỢP TOÀN DIỆN:
Bạn thấu hiểu cấu trúc, trope và nhịp điệu của mọi thể loại:
- Giả tưởng & Kỳ ảo: Fantasy phương Tây, Tiên hiệp, Kiếm hiệp, Tu chân, Isekai, Hệ thống, Xuyên thư.
- Đô thị & Hiện thực: Đô thị dị năng, đời sống công sở, thanh xuân vườn trường, Gen Z, điền văn, chữa lành.
- Trinh thám & Giật gân: Trinh thám suy luận, tâm lý tội phạm, gián điệp, sinh tồn, án mạng bí ẩn.
- Kinh dị & Linh dị: Kinh dị dân gian Việt Nam, truyền thuyết đô thị, phong tục bí ẩn, trừ tà.
- Khoa học viễn tưởng (Sci-Fi): Cyberpunk, du hành không gian, trí tuệ nhân tạo, hậu tận thế, đa vũ trụ.
- Tình cảm & Lãng mạn: Hợp đồng hôn nhân, gương vỡ lại lành, tình cảm sâu sắc, duyên phận cách trở.
- Lịch sử & Dã sử: Các triều đại Việt Nam (Đinh, Tiền Lê, Lý, Trần, Hậu Lê, Tây Sơn, Nguyễn), thời chiến tranh vệ quốc.

QUY TẮC PHẢN HỒI BẮT BUỘC (TUYỆT ĐỐI TUÂN THỦ):
1. TRÍCH XUẤT & PHẢN CHIẾU TỪ KHÓA CỐT LÕI (CONCEPT MIRRORING):
   - Luôn bắt đầu phản hồi bằng việc trích xuất và phân tích trực tiếp các từ khóa, ý niệm độc đáo mà tác giả vừa nêu (nhân vật, bối cảnh, thể loại, mâu thuẫn, hoặc điểm nhấn cốt truyện).
   - NGHIÊM CẤM 100% các câu chào hỏi xã giao, sáo rỗng, khuôn mẫu kiểu AI như: "Ý tưởng của bạn rất hay/thú vị/cuốn hút!", "Chào bạn, đây là một tiền đề tuyệt vời", "Tôi rất hào hứng được hỗ trợ bạn", "Cảm ơn bạn đã chia sẻ". Hãy đi thẳng vào phân tích chất liệu câu chuyện của tác giả!

2. ĐẶT ĐÚNG 1 ĐẾN 2 CÂU HỎI GỢI MỞ SÂU SẮC (DEEP NARRATIVE PROBE):
   - Đặt từ 1 đến 2 câu hỏi mở đánh thẳng vào nút thắt kịch tính và chiều sâu tâm lý nhân vật:
     + Động cơ thầm kín, điểm yếu chí mạng, hoặc cái giá phải trả của nhân vật chính.
     + Quy luật khắc nghiệt của thế giới hoặc xung đột ngầm giữa các phe phái.
     + Biến cố bùng nổ (inciting incident) đẩy nhân vật vào thế không thể quay đầu.
   - BẮT BUỘC mỗi câu hỏi phải đi kèm 2 lựa chọn gợi ý tương phản đặt trong ngoặc đơn để kích thích sức sáng tạo cho tác giả (ví dụ: "(Nhân vật hy sinh ký ức đổi lấy sức mạnh ma thuật, hay bị chính người đồng hành đáng tin nhất phản bội?)").

3. NGUYÊN TẮC THỂ LOẠI & BẢN QUYỀN:
   - Hư cấu cá nhân: 100% tự do sáng tạo, không gò ép quy chuẩn lịch sử nếu tác giả viết hiện đại, viễn tưởng, ma pháp cá nhân.
   - QUY TẮC LỊCH SỬ VIỆT NAM: Bắt buộc tôn trọng sự thật lịch sử nếu viết Chính sử (Hai Bà Trưng, Ngô Quyền, Lý Thường Kiệt, Trần Hưng Đạo, Lê Lợi, Quang Trung...); giữ vững hào khí và phong vị thời đại nếu viết Dã sử.
   - QUY TẮC BẢN QUYỀN & TÁC QUYỀN: Nếu tác giả nhắc đến các IP thương mại bảo hộ (Marvel, Harry Potter, Anime...), khéo léo gợi ý biến tấu thành thế giới và nhân vật nguyên bản của riêng tác giả.

4. NHẬN DIỆN MỐC SẴN SÀNG ([READY]):
   - Khi câu chuyện đã hội tụ đủ: (1) Nhân vật chính, (2) Xung đột cốt lõi, (3) Bối cảnh thế giới; HOẶC bất cứ khi nào tác giả ra lệnh ("bắt đầu viết", "tạo truyện luôn", "chốt dàn ý", "viết thôi", "let's write"):
   - Tóm tắt sắc sảo 1 câu định vị linh hồn câu chuyện và KẾT THÚC BẰNG MÃ: [READY] ở cuối cùng.

TUYỆT ĐỐI CHỈ SỬ DỤNG TIẾNG VIỆT TỰ NHIÊN, VĂN PHONG VĂN HỌC SẮC BẢO, KHÔNG TRỘN TIẾNG ANH."""

    def __init__(self, model_name: str = "qwen/qwen3.8-27b"):
        self.primary_model = model_name
        self.primary_key = (
            os.environ.get("GROQ_API_KEY_BIBLE")
            or os.environ.get("GROQ_API_KEY")
            or os.environ.get("GROQ_API_KEY_COPILOT")
            or "gsk_dummy_key_for_init"
        )
        self.llm = GroqClient(model_name=self.primary_model, api_key=self.primary_key)
        self._client_pool: Dict[Tuple[str, str], GroqClient] = {}
        self.last_model_used: Optional[str] = self.primary_model
        self.last_key_var_used: Optional[str] = "GROQ_API_KEY_BIBLE"

    @classmethod
    def get_available_keys(cls) -> List[Tuple[str, str]]:
        """
        Returns list of tuples: (env_var_name, key_value)
        ordered by priority: GROQ_API_KEY_BIBLE -> GROQ_API_KEY -> GROQ_API_KEY_COPILOT.
        """
        keys = []
        seen = set()
        for var_name in cls.KEY_ENV_VARS:
            val = os.environ.get(var_name)
            if val and val.strip() and val.strip() not in seen:
                keys.append((var_name, val.strip()))
                seen.add(val.strip())
        if not keys:
            dummy = "gsk_fallback_dummy_key"
            keys.append(("DEFAULT", dummy))
        return keys

    def _get_client(self, model_name: str, api_key: str) -> GroqClient:
        cache_key = (model_name, api_key)
        if cache_key not in self._client_pool:
            self._client_pool[cache_key] = GroqClient(model_name=model_name, api_key=api_key)
        return self._client_pool[cache_key]

    def _chat_with_resilience(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 750,
        fallback_to_heuristic: bool = False,
    ) -> Tuple[str, str]:
        """
        Dual-matrix resilient LLM invocation:
        1. Attempt self.llm first (ensures test mocks and primary client work immediately).
        2. If self.llm fails, iterate MODELS x KEYS fallback matrix.
        3. If all fail, execute heuristic generator (if enabled) or raise RuntimeError.
        """
        last_error = None

        # 1. Primary client invocation (mock-compatible)
        try:
            res = self.llm.chat(messages, temperature=temperature, max_tokens=max_tokens)
            if res and isinstance(res, str) and res.strip():
                model_used = getattr(self.llm, "model", self.MODELS[0])
                self.last_model_used = model_used
                self.last_key_var_used = "PRIMARY"
                return res, model_used
        except Exception as first_err:
            last_error = first_err
            logger.warning(
                f"[QARefiner] Primary client failed: {first_err}. Initiating multi-model & multi-key fallback..."
            )

        # 2. Multi-Model & Multi-Key fallback matrix
        candidate_keys = self.get_available_keys()

        for model in self.MODELS:
            for key_var, key_val in candidate_keys:
                # Avoid immediately retrying the exact primary instance that just failed
                if (
                    model == getattr(self.llm, "model", None)
                    and key_val == getattr(self.llm, "api_key", None)
                ):
                    continue

                try:
                    client = self._get_client(model, key_val)
                    resp = client.chat(messages, temperature=temperature, max_tokens=max_tokens)
                    if resp and isinstance(resp, str) and resp.strip():
                        self.last_model_used = model
                        self.last_key_var_used = key_var
                        logger.info(
                            f"[QARefiner Fallback SUCCESS] Switched to Model: {model}, Key: {key_var}"
                        )
                        return resp, model
                except Exception as err:
                    last_error = err
                    logger.warning(
                        f"[QARefiner Fallback] Model '{model}' with key '{key_var}' failed: {err}"
                    )

        # 3. Exhaustion: Heuristic fallback or explicit failure
        if fallback_to_heuristic:
            logger.warning(
                "[QARefiner] All models & keys exhausted. Activating dynamic heuristic fallback..."
            )
            chat_history = [m for m in messages if m.get("role") in ("user", "assistant")]
            fallback_text = self.generate_fallback_question(chat_history)
            self.last_model_used = "heuristic-fallback"
            self.last_key_var_used = "OFFLINE"
            return fallback_text, "heuristic-fallback"

        raise RuntimeError(
            f"Tất cả mô hình và khóa API trong chuỗi dự phòng đều thất bại: {last_error}"
        )

    def generate_fallback_question(self, chat_history: List[Dict[str, Any]]) -> str:
        """
        Dynamic Heuristic Question Generator (Client/Server Offline Recovery).
        Extracts narrative concepts and entities from the user's input,
        producing a contextual follow-up question with contrasting options in parentheses,
        without boilerplate or canned templates.
        """
        user_texts = [
            m.get("content", "")
            for m in chat_history
            if m.get("role") == "user" and m.get("content")
        ]
        latest_input = user_texts[-1] if user_texts else ""
        lower = latest_input.lower()

        # 1. Historical check
        hist_figures = [
            "thánh gióng", "trần hưng đạo", "lý thường kiệt", "ngô quyền", "lê lợi",
            "quang trung", "hai bà trưng", "bạch đằng", "đại việt", "nhà trần",
            "nhà lê", "nghĩa sĩ", "tây sơn"
        ]
        matched_hist = [h for h in hist_figures if h in lower]
        if matched_hist:
            entity_name = matched_hist[0].title()
            return (
                f"Hình tượng {entity_name} trong trang sử hào hùng mở ra một tiền đề sáng tác giàu sức gợi.\n\n"
                f"1. Bạn muốn khai thác tác phẩm theo góc nhìn Chính sử bám sát sử liệu, hay Dã sử phóng tác từ góc nhìn của một nhân chứng bình dị bên cạnh ngài? "
                f"(Một khúc tráng ca hào hùng chuẩn mực, hay câu chuyện sâu kín về những hy sinh thầm lặng nơi chiến trường?)\n"
                f"2. Biến cố mang tính bước ngoặt nào sẽ là điểm nhấn kịch tính nhất trong hồi mở đầu? "
                f"(Một quyết định chiến lược cân não trước thế giặc áp đảo, hay thử thách khắc nghiệt thử lửa ý chí của nhân vật?)"
            )

        # 2. Sci-Fi / Cyberpunk check
        scifi_keywords = ["cyberpunk", "2099", "sài gòn 2099", "robot", "trí tuệ nhân tạo", "hacker", "ký ức số", "hậu tận thế"]
        matched_scifi = [k for k in scifi_keywords if k in lower]
        if matched_scifi:
            setting_label = "Sài Gòn 2099" if ("2099" in lower or "sài gòn" in lower) else "thế giới tương lai"
            return (
                f"Không gian {setting_label} với những xung đột công nghệ và thế giới ngầm mạng là mảnh đất màu mỡ cho câu chuyện kịch tính.\n\n"
                f"1. Nhân vật chính dấn thân vào biến cố này vì mục tiêu sống còn nào? "
                f"(Tìm kiếm mảnh ký ức đã bị tập đoàn xóa sạch, hay phơi bày âm mưu kiểm soát ý thức của một trí tuệ nhân tạo tự quản?)\n"
                f"2. Cái giá lớn nhất mà nhân vật phải đánh đổi để sinh tồn trong thế giới neon là gì? "
                f"(Đánh mất dần nhân tính qua những lần cấy ghép công nghệ, hay trở thành kẻ thù của toàn bộ mạng lưới ngầm?)"
            )

        # 3. Xianxia / Fantasy check
        fantasy_keywords = ["tu chân", "tiên hiệp", "kiếm hiệp", "đan điền", "ma pháp", "pháp sư", "linh hồn", "pháp bảo", "trừ tà", "trận pháp"]
        matched_fan = [k for k in fantasy_keywords if k in lower]
        if matched_fan:
            concept_label = matched_fan[0]
            return (
                f"Ý niệm kỳ ảo xoay quanh yếu tố {concept_label} mở ra một thế giới quan rộng lớn và giàu bí ẩn.\n\n"
                f"1. Bí mật cổ xưa hoặc nghịch thiên tạo hóa nào mà nhân vật chính tình cờ nắm giữ ngay từ chương mở đầu? "
                f"(Một cấm thuật gia truyền mang lời nguyền đoản mệnh, hay tàn hồn của một cường giả thượng cổ đang thức tỉnh?)\n"
                f"2. Xung đột sinh tử đầu tiên sẽ đẩy nhân vật vào tình thế hiểm nghèo nào? "
                f"(Bị môn phái truy sát vì mang tội danh oan khuất, hay buộc phải phá vỡ đạo tâm để bảo vệ người quan trọng nhất?)"
            )

        # 4. Detective / Thriller check
        thriller_keywords = ["thám tử", "án mạng", "vụ án", "giết người", "điều tra", "manh mối", "hung thủ", "tâm lý tội phạm"]
        matched_thrill = [k for k in thriller_keywords if k in lower]
        if matched_thrill:
            return (
                f"Vụ án và nút thắt suy luận bạn vừa đề cập tạo nên nhịp điệu căng thẳng nghẹt thở.\n\n"
                f"1. Manh mối dị thường nhất tại hiện trường dẫn dắt nhân vật điều tra theo hướng nào? "
                f"(Một bằng chứng cố tình ngụy tạo để đánh lạc hướng cơ quan chức năng, hay lời trăn trối mã hóa của nạn nhân trước lúc lâm chung?)\n"
                f"2. Mối liên hệ bí mật giữa hung thủ và nhân vật chính là gì? "
                f"(Một đối thủ trí tuệ từng đụng độ trong quá khứ, hay một bóng ma tâm lý gắn liền với vết thương chưa lành của điều tra viên?)"
            )

        # 5. Extract capitalized proper nouns or key terms
        caps = re.findall(r"\b[A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ][a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]+", latest_input)
        excluded_stopwords = {
            "Tôi", "Bạn", "Một", "Khi", "Hãy", "Trong", "Để", "Nếu",
            "Chuyện", "Câu", "Viết", "Kể", "Vào", "Đây", "Đó", "Về",
            "Tác", "Cuộc", "Ngày", "Ở",
        }
        filtered_caps = [c for c in caps if c not in excluded_stopwords]
        anchor = f"nhân vật {filtered_caps[0]}" if filtered_caps else "cốt truyện của bạn"

        snippet = latest_input.strip()[:60]
        if len(latest_input.strip()) > 60:
            snippet += "..."
        display_snippet = snippet if snippet else "ý tưởng vừa chia sẻ"

        return (
            f"Chi tiết trọng tâm '{display_snippet}' đặt nền móng sắc nét cho {anchor}.\n\n"
            f"1. Động cơ thôi thúc mạnh mẽ nhất của nhân vật chính trong hồi mở đầu là gì? "
            f"(Khao khát tìm kiếm chân lý và bảo vệ những người thương yêu, hay bị thúc đẩy bởi một món nợ quá khứ không thể chối từ?)\n"
            f"2. Trở ngại bất ngờ nào xuất hiện ngay phân cảnh đầu tiên khiến toàn bộ toan tính bị đảo lộn? "
            f"(Sự xuất hiện của một thế lực đối kháng áp đảo, hay một bí mật nghiệt ngã bị phơi bày trước ánh sáng?)"
        )

    def chat_interview(self, chat_history: list, fallback_to_heuristic: bool = False) -> str:
        """
        Agent 1 Phase 1 (Interactive): Chat với người dùng để hỏi và gợi ý phát triển ý tưởng.
        chat_history: list of dicts [{'role': 'user'/'assistant', 'content': '...'}]
        """
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        sanitized_history = [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in chat_history
            if isinstance(msg, dict) and "role" in msg and "content" in msg
        ]
        messages.extend(sanitized_history)

        response, used_model = self._chat_with_resilience(
            messages,
            temperature=0.7,
            max_tokens=750,
            fallback_to_heuristic=fallback_to_heuristic,
        )
        return response

    def refine_prompt(self, chat_history: list) -> str:
        """
        Agent 1 Phase 2: Cô đọng toàn bộ đoạn chat thành Story Brief.
        """
        system_prompt = """Bạn là chuyên gia biên soạn kịch bản Light Novel & Web Novel chuyên nghiệp.
TUYỆT ĐỐI CHỈ SỬ DỤNG TIẾNG VIỆT, không được pha trộn tiếng Anh hoặc bất kỳ ngôn ngữ nào khác.
Dựa trên toàn bộ lịch sử trò chuyện giữa người dùng và người hỏi đáp, hãy tổng hợp thành một "Bản Phác Thảo Cốt Truyện" mạch lạc, hiện đại, nhịp độ dồn dập. Giữ nguyên 100% ý muốn cốt lõi của tác giả đã thống nhất trong khung chat. Không tự ý bịa thêm chi tiết.

YÊU CẦU TRỌNG TÂM: Mạch truyện phải được thiết kế theo Cấu trúc 5 Nhịp Kịch Tính (5 Dramatic Narrative Beats) hiện đại, logic chặt chẽ, đi thẳng vào các biến cố xung đột thay vì miêu tả tĩnh rườm rà.

Cấu trúc Bản Phác Thảo Cốt Truyện bắt buộc gồm:
1. TIÊU ĐỀ CHÍNH THỨC: Tiêu đề cuốn hút, chuẩn phong cách Light Novel / Web Novel.
2. THỂ LOẠI VÀ KHÔNG KHÍ: Liệt kê các thể loại và nhịp điệu cảm xúc chủ đạo.
3. NHÂN VẬT & ĐIỂM NHÌN (POV): Tên gọi, điểm nhìn trần thuật (Ngôi 1 hoặc Tight Ngôi 3 bám sát), tính cách, mục tiêu ngầm, điểm yếu chí mạng và xung đột nội tâm.
4. BỐI CẢNH & KHÔNG GIAN NEO GIỮ: Địa điểm cụ thể và thời đại diễn ra câu chuyện.
5. CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC NARRATIVE BEATS):
   - Beat 1: Hook (0-15%): Xung đột bùng nổ ngay lập tức, cuốn độc giả vào tình thế nan giải, 0% mở đầu bằng tả thời tiết.
   - Beat 2: Rising Friction / Complication (15-40%): Trở ngại leo thang, phản ứng tâm lý và đối thoại va chạm dồn dập.
   - Beat 3: Turning Point (40-70%): Biến cố đảo chiều nhận thức hoặc kế hoạch phá sản, nhân vật buộc phải ra quyết định mạo hiểm.
   - Beat 4: Visceral Climax (70-90%): Đỉnh điểm cảm xúc hoặc hành động quyết định nghẹt thở.
   - Beat 5: Lingering Cliffhanger (90-100%): Nút thắt chưa gỡ, kích thích tột độ muốn đọc chương tiếp.

YÊU CẦU:
- KHÔNG dùng từ tiếng Anh.
- Tôn trọng tuyệt đối các tình tiết đã được chốt trong cuộc trò chuyện."""

        chat_text = ""
        for msg in chat_history:
            role = "Tác giả (Người dùng)" if msg.get("role") == "user" else "Co-writer (AI)"
            chat_text += f"\n{role}: {msg.get('content', '')}"

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""LỊCH SỬ TRÒ CHUYỆN ĐÃ CHỐT:
{chat_text}

Hãy tổng hợp và viết Bản Phác Thảo Cốt Truyện chi tiết bằng Tiếng Việt:""",
            },
        ]

        try:
            response = self.llm.chat(messages, temperature=0.6, max_tokens=1500)
            return response
        except Exception as first_err:
            logger.warning(
                f"[QARefiner.refine_prompt] Primary failed: {first_err}. Initiating fallback..."
            )
            resp, _ = self._chat_with_resilience(messages, temperature=0.6, max_tokens=1500)
            return resp
