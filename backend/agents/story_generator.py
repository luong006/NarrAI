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
                "word_range": "Dưới 2000 từ",
                "max_tokens": 4000
            },
            "medium": {
                "word_range": "Từ 2000 đến 4000 từ",
                "max_tokens": 6000
            },
            "long": {
                "word_range": "Trên 4000 từ",
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
2. MẠCH TRUYỆN & CẤU TRÚC:
   - Hãy chia câu chuyện thành các CHƯƠNG (Chapters) rõ ràng. Mỗi chương cần có Tiêu đề riêng (Ví dụ: Chương 1: Khởi đầu...).
   - Đảm bảo mạch truyện xuyên suốt, logic chặt chẽ từ đầu đến cuối. Sự phát triển tâm lý nhân vật và các biến cố phải hợp lý, không rời rạc.
   - Tập trung đi thẳng vào cốt truyện và hành động. BỚT ĐI TÍNH HOA MỸ, sáo rỗng. Không miêu tả lan man lạm dụng tính từ, mà dùng hành động và hội thoại để thúc đẩy cốt truyện.
3. VĂN PHONG TÁC GIẢ LỚN:
   - Hãy học hỏi phong cách kể chuyện của các tác giả nổi tiếng thế giới (như Stephen King về sự dồn dập kịch tính, J.K. Rowling về thế giới quan sinh động, hay George R.R. Martin về sự trần trụi thực tế) tùy theo thể loại truyện.
   - Tiếng Việt chuẩn mực, sắc sảo, câu từ gãy gọn.
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
