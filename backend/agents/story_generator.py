from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory


MODERN_NOVEL_WRITING_RULES = """QUY TẮC SÁNG TÁC TIỂU THUYẾT HIỆN ĐẠI (ĐÚC KẾT TỪ 5 DÒNG WEB NOVEL KINH ĐIỂN):

1. KHỞI ĐẦU IN MEDIAS RES (HOOK ĐỘC GIẢ TRONG 3 CÂU ĐẦU):
   - Ném nhân vật ngay vào xung đột, nguy cơ hoặc hành động cụ thể đang diễn ra.
   - CẤM mở đầu bằng miêu tả thời tiết chung chung ("trời thu se lạnh", "ánh nắng le lói"), bình minh/hoàng hôn sáo rỗng, hoặc thuyết minh lịch sử dài dòng.
   - Neo độc giả bằng chi tiết giác quan: tiếng kim loại va chạm, mùi khói khét, giọt mồ hôi cay xè mắt, hoặc một câu thoại sắc lạnh.

2. SHOW, DON'T TELL & ĐỊNH CẢNH CHI TIẾT (VISCERAL SENSORY):
   - CẤM nói thẳng cảm xúc nhân vật ("hắn rất sợ", "cô ấy buồn bã", "họ phẫn nộ").
   - Tả BIỂU HIỆN SINH LÝ và VI HÀNH ĐỘNG: Bàn tay siết chặt đến trắng bệch đốt ngón tay, đồng tử co rút, cơ hàm bạnh ra, hơi thở đứt quãng, ngón chân bấu chặt xuống sàn.
   - Môi trường xung quanh phải có sự tương tác vật lý (tiếng mưa gõ trên mái tôn gỉ, ánh đèn chớp nháy rè rè, tàn thuốc lá rơi trên bàn kính).

3. NHỊP ĐIỆU CÂU VĂN CO GIÃN (SENTENCE PACING):
   - Cảnh hành động / đấu trí / căng thẳng: Câu ngắn, đanh thép, tiết tấu dồn dập (3-8 từ/câu). Ngắt nhịp dứt khoát.
   - Cảnh suy luận / nội tâm / chuyển tiếp: Câu phức giàu hình ảnh nhưng gãy gọn, không lan man, không sến sẩm.
   - TUYỆT ĐỐI LOẠI BỎ văn phong hoa mỹ rỗng tuếch.

4. HỘI THOẠI ĐẮT GIÁ, CÓ SUBTEXT (KHÔNG NÓI CHUYỆN VÔ THƯỞNG VÔ PHẠT):
   - Mỗi câu thoại phải phản ánh đúng VỊ THẾ, TÂM CƠ và ĐỘNG CƠ NGẦM của nhân vật.
   - Không ai giải thích điều đối phương đã biết. Dùng thoại để thăm dò, thao túng, đe dọa hoặc che giấu.
   - Đan xen cử chỉ thực tế giữa các câu thoại (gõ nhẹ ngón tay lên bàn, khựng lại một nhịp trước khi đáp).

5. TUÂN THỦ BỘ KHUNG NARRATIVE ONTOLOGY:
   - Các thuộc tính nhân vật, quy tắc thế giới (World Axioms), và chuỗi nhân quả đã thiết lập là BẤT BIẾN.
   - CẤM xuất hiện "Bàn tay vàng vô lý" (Deus Ex Machina). Mọi bước ngoặt đều phải có nguyên nhân logic từ trước.

6. CLIFFHANGER CUỐI CHƯƠNG:
   - Mỗi chương BẮT BUỘC kết thúc bằng một cú ngoặt (plot twist), một phát hiện chấn động, một tiếng bước chân bất thường ngoài cửa, hoặc một thế cờ ngàn cân treo sợi tóc.

7. DANH SÁCH CẤM TUYỆT ĐỐI (ANTI-CLICHÉ BANLIST):
   - CẤM: "vầng trăng vằng vặc trôi trên nền trời nhung đen", "hắn ta khẽ cười khẩy / cười lạnh một tiếng", "thời gian thấm thoắt trôi đi", "không khỏi hít vào một ngụm khí lạnh", "mắt phượng mày ngài", "trời quang mây tạnh lòng người u sầu", "bỗng nhiên một chuyện bất ngờ xảy ra".
   - Viết văn xuôi tự nhiên, chân thực, hiện đại, cuốn hút."""

WRITING_RULES = MODERN_NOVEL_WRITING_RULES


class StoryGenerator:
    def __init__(self):
        self.llm = GroqClient(model_name="openai/gpt-oss-120b")

    def _extract_narrative_ontology(self, refined_prompt: str) -> str:
        """
        Trích xuất Bộ khung Narrative Ontology để neo giữ tính nhất quán của truyện chữ:
        - Thực thể (Entities): Nhân vật chính, ngoại hình, mục tiêu ngầm, điểm yếu
        - Quan hệ (Relations): Ma trận xung đột & động cơ
        - Tiền đề thế giới (World Axioms): Quy tắc vật lý/xã hội, giới hạn công nghệ/phép thuật
        - Chuỗi nhân quả (Causal Milestones): Tiến trình nguyên nhân - kết quả
        """
        prompt = f"""Phân tích bản phác thảo và trích xuất BỘ KHUNG NARRATIVE ONTOLOGY dưới dạng cấu trúc ngắn gọn:
BẢN PHÁC THẢO:
{refined_prompt[:3000]}

Yêu cầu xuất ra cấu trúc chính xác sau:
[THỰC THỂ & NHÂN VẬT]: (Tên, ngoại hình nhận diện, mục tiêu, điểm yếu chí mạng)
[QUAN HỆ & ĐỘNG CƠ]: (Mối quan hệ cụ thể và điểm ngờ vực ngầm giữa các nhân vật)
[QUY TẮC THẾ GIỚI & BỐI CẢNH (WORLD AXIOMS)]: (Địa điểm cụ thể, thời đại, các quy tắc bất biến không thể phá vỡ)
[CHUỖI NHÂN QUẢ CHÍNH]: (Nguyên nhân A -> Dẫn đến hệ quả B -> Đẩy vào xung đột C)
"""
        try:
            ontology_text = self.llm.chat(
                messages=[
                    {"role": "system", "content": "Bạn là Kiến trúc sư Ontology Cốt truyện. Trích xuất Bộ khung Narrative Ontology ngắn gọn, chính xác."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            if ontology_text and ontology_text.strip():
                return ontology_text.strip()
            return f"[BỐI CẢNH & CỐT TRUYỆN GỐC]:\n{refined_prompt[:600]}\n[QUY TẮC BẤT BIẾN]: Giữ nguyên tính cách, không dùng phép màu vô lý, logic nhân quả chặt chẽ."
        except Exception as e:
            return f"[BỐI CẢNH & CỐT TRUYỆN GỐC]:\n{refined_prompt[:600]}\n[QUY TẮC BẤT BIẾN]: Giữ nguyên tính cách, không dùng phép màu vô lý, logic nhân quả chặt chẽ."

    def _get_config(self, story_length: str):
        config = {
            "short": {"word_range": "Khoảng 1200 đến 2200 từ", "max_tokens": 5500, "chapter_mode": False},
            "medium": {"word_range": "Khoảng 2500 đến 4000 từ", "max_tokens": 6000, "chapter_mode": False},
            "long": {"word_range": "Khoảng 1800 đến 2500 từ cho CHƯƠNG NÀY", "max_tokens": 6000, "chapter_mode": True}
        }
        return config.get(story_length, config["medium"])

    def _build_prompt(self, refined_prompt: str, story_length: str):
        cfg = self._get_config(story_length)
        ontology_block = self._extract_narrative_ontology(refined_prompt)

        system_prompt = f"""Bạn là một đại tiểu thuyết gia xuất chúng tầm cỡ quốc tế, chuyên sáng tác truyện bằng tiếng Việt hiện đại.
TUYỆT ĐỐI CHỈ VIẾT BẰNG TIẾNG VIỆT, không được pha trộn tiếng Anh.

=== BỘ KHUNG NARRATIVE ONTOLOGY (BẤT BIẾN - TUYỆT ĐỐI TUÂN THỦ) ===
{ontology_block}
====================================================================

{MODERN_NOVEL_WRITING_RULES}

NHIỆM VỤ: Dựa vào "Bộ khung Narrative Ontology" và "Bản Phác Thảo Cốt Truyện", hãy viết câu chuyện hoàn chỉnh, bám sát tuyệt đối vào các thực thể, mối quan hệ và quy tắc thế giới. Không đổi tên nhân vật hay chệch hướng logic.

ĐỘ DÀI: Khoảng {cfg['word_range']}. Khai triển chi tiết từng tình huống, từng vi hành động."""
        if cfg['chapter_mode']:
            system_prompt += """
CHẾ ĐỘ VIẾT TỪNG CHƯƠNG:
- Chỉ được viết DUY NHẤT 1 CHƯƠNG (1800-2500 từ).
- Chương có tiêu đề: ## Chương X: [Tên chương]
- KẾT THÚC bằng Cliffhanger mạnh mẽ.
- KHÔNG viết thêm chương nào khác."""
        else:
            system_prompt += """
QUY TẮC CHƯƠNG:
- Mỗi chương có Tiêu đề: ## Chương X: [Tên chương]
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
    def generate_story(self, refined_prompt: str, story_length: str = "medium") -> str:
        messages, max_tokens = self._build_prompt(refined_prompt, story_length)
        return self.llm.chat(messages, temperature=0.8, max_tokens=max_tokens)

    def generate_story_stream(self, refined_prompt: str, story_length: str = "medium"):
        messages, max_tokens = self._build_prompt(refined_prompt, story_length)
        return self.llm.chat_stream(messages, temperature=0.8, max_tokens=max_tokens)

    # ===== NEW: Memory-based Chapter Generation =====
    def generate_chapter_stream(self, memory: StoryMemory, user_instruction: str = ""):
        """Viết 1 chương mới dựa trên Memory System (streaming)."""
        bible_block = memory.story_bible.to_prompt_block()
        memory_block = memory.to_prompt_block()
        short_context = memory.get_short_context(max_chars=6000)
        next_chapter = memory.current_chapter + 1

        system_prompt = f"""Ban la tac gia dang truc tiep viet mot chuong tieu thuyet bang tieng Viet.
    NHIEM VU CUA BAN LA VIET VAN XUOI NGAY BAY GIO, khong phan tich va khong hoi lai nguoi dung.
    TUYET DOI KHONG viet loi xin loi, khong nhac lai chi dan, khong noi rang ban chi duoc viet mot chuong,
    khong mo ta nhiem vu cua ban, va khong tra loi theo dang tro chuyen.
    TUYET DOI CHI VIET BANG TIENG VIET.

{bible_block}

{memory_block}

{WRITING_RULES}

NHIEM VU HIEN TAI: Viet CHUONG {next_chapter} cua cau chuyen, bat dau ngay bang tieu de va van xuoi.
- Chi viet DUY NHAT 1 chuong, dai 2000-3000 tu.
- Bat dau bang: ## Chuong {next_chapter}: [Ten chuong]
- Phai tiep noi tu nhien voi noi dung da viet truoc do.
- GIAI QUYET it nhat 1 tuyen truyen dang mo va TAO RA it nhat 1 tuyen truyen moi.
- Ket thuc bang Cliffhanger manh me.
- TUYET DOI KHONG in ra nhan ky thuat. Viet van xuoi thuan tuy.
- TUYET DOI KHONG them loi mo dau hay ket thuc mang tinh tro chuyen."""

        if user_instruction:
            system_prompt += f"\n\nYEU CAU DAC BIET TU TAC GIA: {user_instruction}"

        user_msg = f"Hay viet CHUONG {next_chapter} ngay bay gio. Dong dau tien phai la: ## Chuong {next_chapter}: [Ten chuong]. Sau do viet ngay van xuoi, khong giai thich."
        if short_context:
            user_msg = f"NOI DUNG GAN NHAT DA VIET:\n---\n{short_context[-3000:]}\n---\n\nHay viet CHUONG {next_chapter} tiep noi tu nhien. Dong dau tien phai la: ## Chuong {next_chapter}: [Ten chuong]. Khong giai thich, chi viet van xuoi:"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]
        return self.llm.chat_stream(messages, temperature=0.8, max_tokens=6000)

    def generate_ending_stream(self, memory: StoryMemory):
        """Viết đoạn kết thúc truyện dựa trên Memory."""
        bible_block = memory.story_bible.to_prompt_block()
        memory_block = memory.to_prompt_block()
        short_context = memory.get_short_context(max_chars=6000)

        system_prompt = f"""Ban la mot tieu thuyet gia xuat chung, chuyen sang tac truyen bang tieng Viet.
TUYET DOI CHI VIET BANG TIENG VIET.

{bible_block}

{memory_block}

{WRITING_RULES}

NHIEM VU: Viet DOAN KET THUC cho cau chuyen.
- Goi gon TAT CA cac tuyen truyen dang mo.
- Giai quyet xung dot chinh.
- Mang lai cam xuc tron ven cho nguoi doc.
- Khong ket thuc dot ngot hay gay mach.
- Dai toi thieu 2000 tu.
- TUYET DOI KHONG in ra nhan ky thuat."""

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
