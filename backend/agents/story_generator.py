from llm.groq_client import GroqClient

class StoryGenerator:
    def __init__(self):
        self.llm = GroqClient(model_name="openai/gpt-oss-120b")
    
    def _get_config(self, story_length: str):
        config = {
            "short": {
                "word_range": "Dưới 5000 từ",
                "max_tokens": 8192,
                "chapter_mode": False
            },
            "medium": {
                "word_range": "Từ 5000 đến 6000 từ",
                "max_tokens": 8192,
                "chapter_mode": False
            },
            "long": {
                "word_range": "2000 đến 3000 từ cho CHƯƠNG NÀY",
                "max_tokens": 8192,
                "chapter_mode": True
            }
        }
        return config.get(story_length, config["medium"])

    def _build_prompt(self, refined_prompt: str, story_length: str):
        cfg = self._get_config(story_length)
        
        # Quy tắc chung cho mọi độ dài
        base_rules = f"""Bạn là một tiểu thuyết gia xuất chúng tầm cỡ quốc tế, chuyên sáng tác truyện bằng tiếng Việt.
TUYỆT ĐỐI CHỈ VIẾT BẰNG TIẾNG VIỆT, không được pha trộn tiếng Anh hoặc ký tự ngoại ngữ nào khác.
Nhiệm vụ của bạn: Dựa vào "Bản Phác Thảo Cốt Truyện" được cung cấp, hãy viết câu chuyện bám sát tuyệt đối vào cốt truyện đã yêu cầu. Không được đổi tên nhân vật hay chệch hướng khỏi cốt truyện gốc.

Quy tắc sáng tác BẮT BUỘC:
1. ĐỘ DÀI: Khoảng {cfg['word_range']}. Hãy khai triển chi tiết từng tình huống, không viết vắn tắt.

2. CẤU TRÚC 3 HỒI (THREE-ACT STRUCTURE):
   - Hồi 1 (Setup ~25%): Giới thiệu nhân vật, bối cảnh, và Sự kiện Kích hoạt (Inciting Incident) buộc nhân vật phải hành động.
   - Hồi 2 (Confrontation ~50%): Xung đột leo thang liên tục, nhân vật đối mặt thử thách ngày càng khốc liệt. Điểm giữa (Midpoint) lật ngược tình thế.
   - Hồi 3 (Resolution ~25%): Cao trào tột cùng và giải quyết xung đột.

3. KIẾN TRÚC CHƯƠNG (CHAPTER ARCHITECTURE):
   - Mỗi chương phải là một câu chuyện thu nhỏ có tự trị, đồng thời thúc đẩy cốt truyện chính.
   - Cấu trúc: [Mở đầu lôi cuốn] -> [Xung đột leo thang] -> [Cao trào / Bước ngoặt] -> [Kết thúc hấp dẫn].
   - ĐỘ DÀI TỐI THIỂU MỖI CHƯƠNG: Ít nhất 800 từ. KHÔNG ĐƯỢC tạo chương mới khi chương hiện tại chưa đủ 800 từ. Hãy phát triển đầy đủ các tình huống, đối thoại và miêu tả trong mỗi chương.
   - Cấm viết chương chỉ để "giải thích" (filler/exposition).
   - KHÔNG lạm dụng ngắt chương. Chỉ chuyển sang chương mới khi có bước ngoặt LỚN thay đổi cục diện.

4. CHUỖI NHÂN - QUẢ (THEREFORE / BUT):
   - Không kết nối sự kiện bằng "Và rồi...". Mọi sự kiện phải là "Vì vậy..." (hệ quả) hoặc "Nhưng..." (trở ngại bất ngờ).
   - Cao trào Chương N phải trực tiếp tạo tình thế cho Chương N+1.

5. ĐỘNG CƠ KÉP (SCENE & SEQUEL):
   - Cảnh chủ động: Nhân vật có mục tiêu -> Gặp xung đột -> Thất bại/Trả giá.
   - Cảnh phản ứng: Nhân vật sốc -> Đứng giữa 2 lựa chọn tồi tệ -> Quyết định mới.
   - Luân phiên 2 loại cảnh để kiểm soát nhịp độ.

6. BIẾN THIÊN TRẠNG THÁI (VALUE SHIFT):
   - Cuối mỗi chương, trạng thái nhân vật BẮT BUỘC thay đổi (Tích cực <-> Tiêu cực).
   - Đào sâu mâu thuẫn WANTS (muốn) vs NEEDS (cần để trưởng thành).

7. MỞ ĐẦU VÀ KẾT THÚC CHƯƠNG:
   - Mở: Bắt đầu ngay giữa hành động (In medias res). Neo người đọc bằng giác quan cụ thể ngay 2 đoạn đầu.
   - Kết: Luôn kết bằng Cliffhanger - mối đe dọa mới, câu hỏi chưa lời đáp, hoặc lật ngược tình thế.

8. VĂN PHONG (SHOW, DON'T TELL):
   - Tả qua hành động, đối thoại và cảm giác thay vì kể lể.
   - Đối thoại phải bộc lộ tính cách, không dùng để giải thích cốt truyện.
   - Dùng chi tiết cụ thể thay vì tính từ chung chung.
   - TUYỆT ĐỐI KHÔNG được in ra các nhãn kỹ thuật như "Cảnh Chủ Động", "Cảnh Phản Ứng", "Mục tiêu:", "Xung đột:", "Kết quả:", "Value Shift", "Cliffhanger". Đây là quy tắc NỘI BỘ để bạn tư duy, KHÔNG PHẢI định dạng đầu ra. Bạn phải viết VĂN XUÔI THUẦN TÚY như một cuốn tiểu thuyết thực sự, không có bất kỳ nhãn phân tích nào."""

        # Quy tắc bổ sung cho chế độ viết từng chương
        if cfg['chapter_mode']:
            chapter_rules = """

9. CHẾ ĐỘ VIẾT TỪNG CHƯƠNG (QUAN TRỌNG):
   - Bạn CHỈ ĐƯỢC VIẾT DUY NHẤT 1 CHƯƠNG trong lần này (khoảng 2000-3000 từ).
   - Chương phải có tiêu đề rõ ràng: ## Chương X: [Tên chương]
   - KẾT THÚC chương bằng một Cliffhanger mạnh mẽ để người đọc phải đọc tiếp.
   - KHÔNG được viết thêm chương nào khác. Dừng lại sau khi hoàn thành 1 chương."""
        else:
            chapter_rules = """

9. QUY TẮC CHƯƠNG:
   - Mỗi chương cần có Tiêu đề: ## Chương X: [Tên chương]
   - ĐỘ DÀI TỐI THIỂU MỖI CHƯƠNG: Ít nhất 800 từ. Hãy viết sâu, khai triển đầy đủ.
   - KHÔNG lạm dụng ngắt chương. Với truyện ngắn (dưới 5000 từ): tối đa 3-4 chương. Với truyện trung bình (5000-6000 từ): tối đa 5-6 chương.
   - Chỉ qua chương mới khi có bước ngoặt lớn thay đổi cục diện."""

        formatting = f"""

Bản Phác Thảo Cốt Truyện:
{refined_prompt}

Quy tắc định dạng:
- Trình bày rõ ràng. Dùng markdown (##) cho tiêu đề Chương.
- Bắt đầu NGAY LẬP TỨC bằng: **[TÊN TIÊU ĐỀ TRUYỆN]** ở dòng đầu tiên.
- TUYỆT ĐỐI KHÔNG thêm lời mở đầu hay kết thúc mang tính trò chuyện."""

        system_prompt = base_rules + chapter_rules + formatting

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"BẢN PHÁC THẢO CỐT TRUYỆN YÊU CẦU:\n{refined_prompt}\n\nHãy bắt đầu viết ngay bây giờ:"}
        ]
        return messages, cfg["max_tokens"]

    def generate_story(self, refined_prompt: str, story_length: str = "medium") -> str:
        messages, max_tokens = self._build_prompt(refined_prompt, story_length)
        return self.llm.chat(messages, temperature=0.8, max_tokens=max_tokens)

    def generate_story_stream(self, refined_prompt: str, story_length: str = "medium"):
        messages, max_tokens = self._build_prompt(refined_prompt, story_length)
        return self.llm.chat_stream(messages, temperature=0.8, max_tokens=max_tokens)

    def handle_chat_instruction(self, current_story: str, user_message: str):
        import json
        import re
        
        system_prompt = f"""Bạn là Trợ lý AI đồng sáng tác tiểu thuyết xuất chúng.

NHIỆM VỤ: Đọc lệnh của người dùng và thực hiện chính xác.
- Nếu họ yêu cầu "viết tiếp", "thêm nhân vật", "đổi hướng": VIẾT TIẾP ĐOẠN TRUYỆN MỚI (tuân thủ văn phong Show don't tell, cấu trúc tiểu thuyết chuyên nghiệp, kết thúc bằng Cliffhanger).
- Nếu họ yêu cầu "kết thúc truyện": Viết một đoạn kết thúc mạch lạc, gói gọn các tuyến truyện mà không gãy mạch.
- Nếu họ chỉ hỏi đáp bình thường: Trả lời thân thiện.

TRUYỆN ĐÃ VIẾT TỪ TRƯỚC (5000 ký tự cuối):
---
{current_story[-5000:] if len(current_story) > 5000 else current_story}
---

LỆNH CỦA NGƯỜI DÙNG: "{user_message}"

ĐẦU RA BẮT BUỘC LÀ JSON:
{{
    "chat_reply": "Câu trả lời ngắn gọn gửi cho người dùng",
    "new_story_content": "Phần truyện MỚI VIẾT THÊM. Nếu không cần viết thêm, để chuỗi rỗng."
}}"""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Hãy thực hiện yêu cầu và trả về JSON."}
            ]
            response = self.llm.chat(
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )
            
            json_match = re.search(r'\{.*\}', response.replace('\n', ' '), re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(response)
        except Exception as e:
            print("Chat Error:", e)
            return {
                "chat_reply": "Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn.",
                "new_story_content": ""
            }
