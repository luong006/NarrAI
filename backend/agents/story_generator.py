from llm.groq_client import GroqClient

class StoryGenerator:
    def __init__(self):
        self.llm = GroqClient(model_name="openai/gpt-oss-120b")
    
    def _get_config(self, story_length: str):
        """
        Cấu hình số từ mục tiêu và max_tokens an toàn theo TPM của Groq
        """
        config = {
            "short": {
                "word_range": "Dưới 5000 từ",
                "max_tokens": 8192
            },
            "medium": {
                "word_range": "Từ 5000 đến 6000 từ",
                "max_tokens": 8192
            },
            "long": {
                "word_range": "Hơn 10000 từ (Cực kỳ dài và chi tiết)",
                "max_tokens": 8192
            }
        }
        return config.get(story_length, config["medium"])

    def _build_prompt(self, refined_prompt: str, story_length: str):
        cfg = self._get_config(story_length)
        
        system_prompt = f"""Bạn là một tiểu thuyết gia xuất chúng tầm cỡ quốc tế, chuyên sáng tác truyện bằng tiếng Việt.
TUYỆT ĐỐI CHỈ VIẾT BẰNG TIẾNG VIỆT, không được pha trộn tiếng Anh hoặc ký tự ngoại ngữ nào khác.
Nhiệm vụ của bạn: Dựa vào "Bản Phác Thảo Cốt Truyện" được cung cấp, hãy viết một câu chuyện hoàn chỉnh, bám sát tuyệt đối vào cốt truyện đã yêu cầu. Không được đổi tên nhân vật hay chệch hướng khỏi cốt truyện gốc.

Quy tắc sáng tác BẮT BUỘC:
1. ĐỘ DÀI: Khoảng {cfg['word_range']}. Hãy khai triển chi tiết từng tình huống, không viết vắn tắt.
2. KIẾN TRÚC TIỂU THUYẾT VÀ CHƯƠNG (CỐT LÕI):
   - Mọi chương truyện (Chapter) bắt buộc phải là một câu chuyện thu nhỏ có tự trị, đồng thời thúc đẩy cốt truyện chính.
   - Cấu trúc mỗi chương: [Mở đầu lôi cuốn / Mục tiêu tức thời] -> [Xung đột leo thang / Trở ngại] -> [Cao trào / Bước ngoặt] -> [Biến thiên trạng thái / Kết thúc hấp dẫn].
   - Cấm viết các chương chỉ để "giải thích" (filler/exposition). Nếu chương không làm thay đổi cục diện, tuyệt đối không viết.
3. CHUỖI NHÂN - QUẢ (THEREFORE / BUT):
   - Không bao giờ kết nối các sự kiện bằng "Và rồi..." (And then). Mọi sự kiện phải là kết quả của "Vì vậy..." (hệ quả hành động) hoặc "Nhưng..." (trở ngại bất ngờ).
   - Cao trào của Chương N phải trực tiếp tạo ra tình thế tiến thoái lưỡng nan cho Chương N+1.
4. ĐỘNG CƠ KÉP (CẢNH CHỦ ĐỘNG & PHẢN ỨNG):
   - Cảnh chủ động: Nhân vật có mục tiêu -> Gặp xung đột -> Thất bại/Trả giá.
   - Cảnh phản ứng: Nhân vật sốc/đau đớn -> Đứng giữa 2 lựa chọn tồi tệ -> Quyết định mới -> Mục tiêu mới.
   - Luân phiên 2 loại cảnh này để kiểm soát nhịp độ và chiều sâu cảm xúc.
5. SỰ BIẾN THIÊN TRẠNG THÁI (VALUE SHIFT):
   - Cuối mỗi chương, trạng thái cảm xúc hoặc hoàn cảnh của nhân vật BẮT BUỘC phải thay đổi (Từ Tích cực sang Tiêu cực, hoặc ngược lại). 
   - Đào sâu sự mâu thuẫn giữa WANTS (Thứ nhân vật muốn) và NEEDS (Thứ nhân vật thực sự cần để trưởng thành).
6. MỞ ĐẦU VÀ KẾT THÚC CHƯƠNG:
   - Mở đầu: Bắt đầu ngay giữa hành động (In medias res). Neo giữ người đọc bằng các giác quan cụ thể (mùi, vị, âm thanh) ngay trong 2 đoạn đầu.
   - Kết thúc: Không bao giờ kết thúc êm đềm. Luôn kết chương bằng: Một mối đe dọa mới, Một câu hỏi chưa lời đáp, hoặc Lật ngược tình thế gây sốc (Cliffhanger).

Bản Phác Thảo Cốt Truyện:
{refined_prompt}

Quy tắc định dạng:
- Trình bày rõ ràng. Dùng markdown (##) cho tiêu đề Chương.
- Bắt đầu NGAY LẬP TỨC bằng: **[TÊN TIÊU ĐỀ TRUYỆN]** ở dòng đầu tiên.
- TUYỆT ĐỐI KHÔNG thêm lời mở đầu hay kết thúc mang tính trò chuyện."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"BẢN PHÁC THẢO CỐT TRUYỆN YÊU CẦU:\n{refined_prompt}\n\nHãy bắt đầu viết câu chuyện hoàn chỉnh bằng Tiếng Việt ngay bây giờ:"}
        ]
        return messages, cfg["max_tokens"]

    def generate_story(self, refined_prompt: str, story_length: str = "medium") -> str:
        """
        Agent 2: Tạo truyện chữ hoàn chỉnh (đồng bộ)
        """
        messages, max_tokens = self._build_prompt(refined_prompt, story_length)
        return self.llm.chat(messages, temperature=0.8, max_tokens=max_tokens)

    def generate_story_stream(self, refined_prompt: str, story_length: str = "medium"):
        """
        Agent 2: Tạo truyện chữ hoàn chỉnh (Streaming thời gian thực)
        """
        messages, max_tokens = self._build_prompt(refined_prompt, story_length)
        return self.llm.chat_stream(messages, temperature=0.8, max_tokens=max_tokens)


    def handle_chat_instruction(self, current_story: str, user_message: str):
        import json
        import re
        
        system_prompt = f"""Bạn là Trợ lý AI đồng sáng tác tiểu thuyết xuất chúng.
        
Người dùng đang viết một cuốn tiểu thuyết. Đây là nội dung TRUYỆN ĐÃ VIẾT TỪ TRƯỚC:
---
{current_story[-5000:] if len(current_story) > 5000 else current_story}
---

Người dùng vừa ra lệnh: \"{user_message}\"

Nhiệm vụ của bạn:
1. Đọc lệnh của người dùng. Nếu họ yêu cầu "viết tiếp", "thêm nhân vật", "đổi hướng", hãy VIẾT TIẾP ĐOẠN TRUYỆN ĐÓ (tuân thủ văn phong Show, don't tell và cấu trúc tiểu thuyết chuyên nghiệp).
2. Nếu họ chỉ hỏi đáp bình thường, hãy trả lời.

ĐẦU RA BẮT BUỘC LÀ JSON có định dạng:
{{
    "chat_reply": "Câu trả lời ngắn gọn, thân thiện gửi cho người dùng (ví dụ: Dạ, em đã viết tiếp chương 2 với cao trào như anh yêu cầu rồi ạ!)",
    "new_story_content": "Phần truyện chữ MỚI ĐƯỢC VIẾT THÊM (tuyệt đối không lặp lại đoạn cũ). Nếu lệnh không yêu cầu viết thêm truyện, để chuỗi rỗng."
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
            
            # Clean JSON if wrapped in markdown
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
