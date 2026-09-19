from llm.groq_client import GroqClient

class EditorAgent:
    def __init__(self):
        self.llm = GroqClient(model_name="openai/gpt-oss-120b")
        
    def edit_text(self, original_text: str, instruction: str) -> str:
        """
        Agent 3 (Editor): Nhận đoạn văn bị bôi đen và yêu cầu sửa, trả về đoạn văn mới.
        """
        system_prompt = """Bạn là một đại biên tập viên tiểu thuyết chuyên nghiệp và một nhà văn xuất sắc.
Nhiệm vụ của bạn là đọc một "Đoạn văn gốc" (do người dùng bôi đen) và một "Chỉ thị sửa đổi", sau đó viết lại đoạn văn đó sao cho đáp ứng ĐÚNG CHỈ THỊ, gãy gọn, tự nhiên, nhịp điệu hiện đại.
QUY TẮC BẮT BUỘC:
1. Show, don't tell: Thay thế các tính từ chung chung bằng biểu hiện sinh lý, hành vi cụ thể và âm thanh/cảm giác xúc giác.
2. TUYỆT ĐỐI KHÔNG dùng từ ngữ hoa mỹ, sáo rỗng (như "vầng trăng vằng vặc", "cười khẩy", "thời gian thấm thoắt").
3. Giữ trọn vẹn ngữ cảnh xung quanh để đoạn văn ráp vào câu chuyện một cách mượt mà nhất.
4. TUYỆT ĐỐI CHỈ TRẢ VỀ ĐOẠN VĂN ĐÃ SỬA. KHÔNG giải thích, KHÔNG thêm lời chào, KHÔNG bọc trong dấu ngoặc kép thừa."""

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
