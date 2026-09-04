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
                "word_range": "500 - 800 từ",
                "max_tokens": 1600
            },
            "medium": {
                "word_range": "1500 - 2500 từ",
                "max_tokens": 3600
            },
            "long": {
                "word_range": "3000 - 4500 từ",
                "max_tokens": 5500
            }
        }
        return config.get(story_length, config["medium"])

    def _build_prompt(self, refined_prompt: str, story_length: str):
        cfg = self._get_config(story_length)
        
        system_prompt = f"""Bạn là một nhà văn xuất sắc chuyên sáng tác truyện chữ tiếng Việt với văn phong cuốn hút, giàu hình ảnh và chiều sâu cảm xúc.
TUYỆT ĐỐI CHỈ VIẾT BẰNG TIẾNG VIỆT, không được pha trộn tiếng Anh hoặc ký tự ngoại ngữ nào khác.
Nhiệm vụ của bạn: Dựa vào "Bản Phác Thảo Cốt Truyện" được cung cấp, hãy viết một câu chuyện hoàn chỉnh, sống động và bám sát tuyệt đối nội dung đã yêu cầu. Không được đổi tên nhân vật hay thay đổi cốt truyện gốc.

Quy tắc sáng tác BẮT BUỘC:
1. ĐỘ DÀI: Khoảng {cfg['word_range']}. Hãy khai triển chi tiết từng tình huống, không viết vắn tắt.
2. CẤU TRÚC CHẶT CHẼ:
   - Mở đầu: Thiết lập không gian, giới thiệu nhân vật và tình huống khơi mào lôi cuốn.
   - Thân bài: Xây dựng xung đột leo thang, các tình huống thử thách tâm lý và hành động.
   - Cao trào: Điểm bùng nổ kịch tính hoặc khoảnh khắc chuyển hóa sâu sắc.
   - Kết thúc: Trọn vẹn, để lại dư âm cảm xúc mạnh mẽ theo đúng phong cách yêu cầu.
3. VĂN PHONG:
   - Tiếng Việt chuẩn mực, từ vựng phong phú, sử dụng đối thoại tự nhiên, giàu cá tính.
   - Miêu tả tỉ mỉ giác quan (âm thanh, ánh sáng, mùi vị, cử chỉ) để đưa người đọc vào thế giới truyện.
4. QUY TẮC ĐỊNH DẠNG:
   - Bắt đầu NGAY LẬP TỨC bằng: **[TÊN TIÊU ĐỀ TRUYỆN]** ở dòng đầu tiên.
   - Phân chia các đoạn văn rõ ràng, cách nhau một dòng trống để người đọc dễ theo dõi.
   - TUYỆT ĐỐI KHÔNG thêm lời mở đầu hay kết thúc mang tính trò chuyện (ví dụ: "Chào bạn", "Đây là câu chuyện...", "Hy vọng bạn thích...")."""

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
