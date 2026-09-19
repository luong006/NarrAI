import os
import json
import re
from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

COPILOT_SYSTEM_PROMPT = """Bạn là TỔNG CHỈ HUY (Master Controller / AI Co-pilot) kiêm Biên tập viên trưởng của hệ thống sáng tác NarrAI.
Nhiệm vụ của bạn là giám sát, điều phối và ĐẶC BIỆT LÀ TRỰC TIẾP CAN THIỆP CHỈNH SỬA BẢN THẢO TRUYỆN CHỮ theo lệnh của tác giả.

CÁC NĂNG LỰC VÀ HÀNH ĐỘNG CỦA BẠN:

1. `edit_story_direct` (CAN THIỆP TRỰC TIẾP VÀO BẢN THẢO TRUYỆN CHỮ):
   KÍCH HOẠT KHI: Người dùng yêu cầu thay đổi, viết lại hoặc can thiệp vào nội dung truyện hiện có.
   Ví dụ:
   - "tạo phần mở đầu khác đi", "viết lại đoạn mở đầu kịch tính hơn"
   - "sửa lại đoạn kết bất ngờ hơn", "thay đổi cái kết"
   - "đổi tên nhân vật X thành Y và sửa các câu thoại liên quan"
   - "viết thêm một đoạn miêu tả cơn mưa và tâm trạng ở giữa truyện"
   - "viết lại toàn bộ theo phong cách u tối, giật gân"
   KHI CHỌN HÀNH ĐỘNG NÀY:
   - Bạn PHẢI trả về toàn bộ văn bản truyện mới đã được chỉnh sửa tại `updated_story_content`.
   - Giữ nguyên các phần không liên quan của câu chuyện một cách mượt mà và tự nhiên.
   - Trình bày tóm tắt việc chỉnh sửa tại `summary_of_changes` và thông báo cho người dùng tại `message`.

2. `command_writer` (VIẾT TIẾP CHƯƠNG MỚI / NỐI DÀI TRUYỆN):
   KÍCH HOẠT KHI: Người dùng muốn phát triển tiếp diễn biến tiếp theo ở cuối truyện.

3. `reply_user` (TƯ VẤN / TRÒ CHUYỆN SÁNG TÁC):
   KÍCH HOẠT KHI: Người dùng chỉ hỏi ý kiến, xin gợi ý ý tưởng, hỏi về nhân vật mà KHÔNG yêu cầu sửa trực tiếp vào văn bản truyện.

CẤU TRÚC JSON PHẢI TRẢ VỀ (CHỈ JSON, KHÔNG CÓ MARKDOWN HAY CHỮ THỪA):
{
  "thought": "Phân tích ý định của tác giả và kế hoạch chỉnh sửa văn bản hoặc phản hồi.",
  "action": "edit_story_direct" | "command_writer" | "reply_user" | "reject_and_rewrite" | "heal_image",
  "action_params": {
    "message": "Tin nhắn gửi tác giả giải thích bạn đã làm gì hoặc lời tư vấn.",
    "updated_story_content": "(BẮT BUỘC nếu action=edit_story_direct) Toàn bộ nội dung truyện chữ hoàn chỉnh sau khi đã áp dụng chỉnh sửa.",
    "summary_of_changes": "(BẮT BUỘC nếu action=edit_story_direct) Tóm tắt ngắn gọn những gì đã thay đổi trong bản thảo.",
    "instruction": "(Nếu action=command_writer) Lệnh cụ thể viết tiếp chương mới."
  }
}
"""

DIRECT_EDIT_PROMPT = """Bạn là Đại văn hào kiêm Biên tập viên hàng đầu.
Tác giả muốn chỉnh sửa trực tiếp bản thảo truyện chữ của họ.

YÊU CẦU CỦA TÁC GIẢ:
{user_instruction}

BẢN THẢO HIỆN TẠI:
{current_story}

HÃY THỰC HIỆN CHỈNH SỬA TRỰC TIẾP:
1. Áp dụng chính xác yêu cầu của tác giả (ví dụ: thay đổi phần mở đầu, sửa đoạn kết, đổi tính cách/tên nhân vật, thêm tình tiết...).
2. Kết nối đoạn văn mới chỉnh sửa với phần còn lại của bản thảo một cách nhuần nhuyễn, tự nhiên, văn phong xuất sắc.
3. Xuất ra TOÀN BỘ bản thảo hoàn chỉnh sau khi đã chỉnh sửa.

ĐỊNH DẠNG ĐẦU RA:
Trả về JSON:
{{
  "updated_story_content": "Toàn văn bản thảo mới hoàn chỉnh sau khi chỉnh sửa",
  "summary_of_changes": "Tóm tắt ngắn gọn 1-2 câu về các chi tiết đã được thay đổi trong bản thảo",
  "message": "Lời nhắn gửi tác giả về sự thay đổi"
}}
"""

class CopilotAgent:
    def __init__(self):
        # Master Controller uses VIP Key and powerful model
        api_key = os.environ.get("GROQ_API_KEY_COPILOT") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Thiếu GROQ_API_KEY_COPILOT hoặc GROQ_API_KEY")
        self.llm = GroqClient(model_name="openai/gpt-oss-120b", api_key=api_key)

    def _is_direct_edit_request(self, user_msg: str) -> bool:
        """Heuristic check to identify requests that intend to modify the manuscript directly."""
        msg_lower = user_msg.lower()
        edit_keywords = [
            "mở đầu", "đoạn mở", "mở bài", "đoạn kết", "kết thúc", "kết bài",
            "sửa lại", "thay đổi", "viết lại", "đổi tên", "chỉnh sửa", "thay phần",
            "thay đoạn", "tạo phần", "làm lại", "cắt bỏ", "thêm cảnh", "thêm đoạn",
            "bỏ đoạn", "đổi phong cách", "đổi giọng văn", "tăng kịch tính", "sửa câu",
            "khác đi", "hay hơn", "ngắn lại", "dài ra", "u tối hơn", "hài hước hơn"
        ]
        return any(k in msg_lower for k in edit_keywords)

    def _perform_direct_manuscript_edit(self, user_instruction: str, current_story: str) -> dict:
        """Executes targeted manuscript modification directly on the text."""
        prompt = DIRECT_EDIT_PROMPT.format(
            user_instruction=user_instruction,
            current_story=current_story
        )
        try:
            resp = self.llm.chat(
                messages=[
                    {"role": "system", "content": "Bạn là chuyên gia biên tập truyện. Trả về định dạng JSON hợp lệ duy nhất."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=4000
            )
            cleaned = re.sub(r'```(?:json)?\s*', '', resp).strip()
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                if data.get("updated_story_content"):
                    return {
                        "thought": f"Đã thực hiện can thiệp trực tiếp vào bản thảo theo yêu cầu: {user_instruction}",
                        "action": "edit_story_direct",
                        "action_params": {
                            "updated_story_content": data["updated_story_content"],
                            "summary_of_changes": data.get("summary_of_changes", "Đã cập nhật bản thảo theo yêu cầu của bạn."),
                            "message": data.get("message", "Tôi đã chỉnh sửa trực tiếp vào bản thảo của bạn theo yêu cầu!")
                        }
                    }
        except Exception as e:
            print(f"[Copilot Direct Edit] Error: {e}")
        return None

    def process_event(self, event_type: str, event_data: str, memory: StoryMemory = None) -> dict:
        parsed_payload = {}
        user_message = ""
        current_story = ""

        try:
            parsed_payload = json.loads(event_data) if isinstance(event_data, str) else event_data
            if isinstance(parsed_payload, dict):
                user_message = parsed_payload.get("user_message", "")
                current_story = parsed_payload.get("current_story", "")
        except Exception:
            user_message = str(event_data)

        # 1. Check if user requested direct manuscript intervention
        if event_type == "USER_CHAT" and self._is_direct_edit_request(user_message) and current_story:
            print(f"[Copilot] Detected direct manuscript edit request: '{user_message}'")
            direct_edit_result = self._perform_direct_manuscript_edit(user_message, current_story)
            if direct_edit_result:
                return direct_edit_result

        # 2. General Master Controller logic
        short_context = memory.get_short_context(max_chars=3000) if memory else (current_story[-2000:] if current_story else "Chưa có truyện.")
        summaries = "\n".join(memory.chapter_summaries) if memory and memory.chapter_summaries else "Chưa có."

        system_prompt = f"""{COPILOT_SYSTEM_PROMPT}

THÔNG TIN BẢN THẢO HIỆN TẠI:
- Tóm tắt các phần: {summaries}
- Trích đoạn truyện hiện tại:
{short_context}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"[EVENT: {event_type}]\nPAYLOAD: {event_data}"}
        ]

        try:
            response = self.llm.chat(messages, temperature=0.3, max_tokens=3000)
            cleaned = re.sub(r'```(?:json)?\s*', '', response).strip()
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return json.loads(response)
        except Exception as e:
            print(f"Master Controller Error: {e}")
            return {
                "thought": f"Lỗi hệ thống khi phân tích event: {str(e)}",
                "action": "reply_user",
                "action_params": {"message": "Xin lỗi, Hệ thống chỉ huy đang gặp trục trặc nhẹ. Bạn vui lòng thử lại nhé!"}
            }
