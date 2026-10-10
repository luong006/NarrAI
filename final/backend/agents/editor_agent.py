from llm.groq_client import GroqClient

class EditorAgent:
    def __init__(self):
        self.llm = GroqClient(model_name="openai/gpt-oss-120b")
        
    def edit_text(self, original_text: str, instruction: str) -> str:
        """
        Agent 3 (Editor): Nhận đoạn văn bị bôi đen và yêu cầu sửa, trả về đoạn văn mới.
        """
        system_prompt = """Bạn là Biên tập viên Light Novel & Web Novel sắc sảo kiêm Bút vàng thịnh hành.
Nhiệm vụ của bạn là đọc "Đoạn văn gốc" (do người dùng bôi đen) và "Chỉ thị sửa đổi", sau đó viết lại đoạn văn đó theo chuẩn văn phong Light Novel / Web Novel hiện đại:
QUY TẮC BẮT BUỘC:
1. Điểm nhìn bám sát (Tight POV) & Giàu độc thoại nội tâm: Khắc họa trần trụi suy nghĩ thầm kín, lo âu, toan tính và cảm xúc chân thật của nhân vật.
2. Đối thoại tự nhiên, gãy gọn, punchy dialogue: Lời thoại sắc sảo, có subtext, mang khẩu ngữ giới trẻ đương đại, loại bỏ hoàn toàn ngữ điệu dịch thuật cổ lỗ.
3. Show, don't tell & Vi hành động: Thay thế tính từ trừu tượng bằng cử chỉ vô thức, biểu hiện sinh lý thực tế và tương tác vật lý sống động.
4. Nhịp độ nhanh (Staccato Pacing): Câu văn gãy gọn, đoạn văn thông thoáng (2-4 câu/đoạn), không miêu tả tĩnh lan man.
5. TUYỆT ĐỐI KHÔNG dùng từ ngữ sáo rỗng ("vầng trăng vằng vặc", "cười khẩy", "thời gian thấm thoắt", "trời se lạnh").
6. Giữ trọn vẹn ngữ cảnh xung quanh để đoạn văn ghép vào mạch truyện mượt mà.
7. CHỈ TRẢ VỀ ĐOẠN VĂN ĐÃ SỬA. KHÔNG giải thích, KHÔNG thêm lời chào, KHÔNG bọc trong dấu ngoặc kép thừa."""

        user_content = f"""ĐOẠN VĂN GỐC:
{original_text}

CHỈ THỊ SỬA ĐỔI CỦA TÁC GIẢ:
{instruction}

Hãy viết lại đoạn văn trên:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        # We use a slightly lower temperature for editing to keep it focused on the instruction
        response = self.llm.chat(messages, temperature=0.6, max_tokens=1000)
        return response.strip()
