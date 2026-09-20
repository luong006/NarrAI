import os
import sys
import json
import re

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def safe_log(msg: str):
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode("ascii", "backslashreplace").decode("ascii"))
        except Exception:
            pass

def unwrap_story_prose(text: str) -> str:
    """Multi-pass unwraps stringified JSON, nested envelopes, and markdown codeblocks to guarantee pure story prose."""
    if not text:
        return ""
    current = str(text).strip()

    candidate_keys = [
        "updated_story_content",
        "story_content",
        "story",
        "content",
        "new_story_content",
        "revised_text",
        "text"
    ]

    for _ in range(10):
        prev = current
        # 1. Strip markdown code blocks (```json ... ``` or ```markdown ... ``` or ``` ... ```)
        current = re.sub(r'^```(?:json|markdown)?\s*\n?', '', current, flags=re.IGNORECASE).strip()
        current = re.sub(r'\n?```\s*$', '', current).strip()

        # If wrapped inside ```json\n{...}\n``` within a larger string
        code_fence_match = re.search(r'```(?:json|markdown)?\s*\n?(.*?)\n?```', current, re.DOTALL | re.IGNORECASE)
        if code_fence_match:
            fence_inner = code_fence_match.group(1).strip()
            if any(f'"{k}"' in fence_inner for k in candidate_keys) or '"action_params"' in fence_inner:
                current = fence_inner

        # 2. Check if current is JSON-like
        is_json_candidate = (
            (current.startswith('{') and current.endswith('}'))
            or (current.startswith('"{') and current.endswith('}"'))
            or any(f'"{k}"' in current for k in candidate_keys)
            or '"action_params"' in current
        )

        if is_json_candidate:
            extracted_val = None
            try:
                parsed = json.loads(current, strict=False)
                if isinstance(parsed, str):
                    extracted_val = parsed
                elif isinstance(parsed, dict):
                    # Check candidate keys in root
                    for k in candidate_keys:
                        val = parsed.get(k)
                        if val and isinstance(val, (str, dict)):
                            extracted_val = val
                            break
                    # If not found in root, check inside action_params
                    if not extracted_val and isinstance(parsed.get("action_params"), dict):
                        sub = parsed["action_params"]
                        for k in candidate_keys:
                            val = sub.get(k)
                            if val and isinstance(val, (str, dict)):
                                extracted_val = val
                                break
                    # If still not found, check if there's a single key containing long text
                    if not extracted_val:
                        for k, v in parsed.items():
                            if isinstance(v, str) and len(v) > 30 and k not in ("thought", "action", "message", "summary_of_changes"):
                                extracted_val = v
                                break
            except Exception:
                # Robust regex fallback for dialogue with quotes, escaped characters, and truncated streams
                match = re.search(
                    r'"updated_story_content"\s*:\s*"([\s\S]*?)(?:",\s*"(?:summary_of_changes|message|action|instruction)"\s*:|"\s*\}\s*[\}\]]?\s*|"?\s*$)',
                    current
                )
                if match and match.group(1):
                    extracted_val = match.group(1)
                else:
                    for k in candidate_keys:
                        pattern = r'"' + re.escape(k) + r'"\s*:\s*"([\s\S]*?)(?:",\s*"[a-zA-Z0-9_]+"\s*:|"\s*\}\s*[\}\]]?\s*|"?\s*$)'
                        m = re.search(pattern, current)
                        if m and m.group(1):
                            extracted_val = m.group(1)
                            break

            if extracted_val is not None:
                if isinstance(extracted_val, dict):
                    current = json.dumps(extracted_val, ensure_ascii=False)
                else:
                    current = str(extracted_val).strip()

        if current == prev:
            break

    # 3. Unconditionally unescape escaped sequences once the prose is isolated
    for _ in range(3):
        if "\\n" in current or "\\r" in current or '\\"' in current or "\\\\" in current:
            current = (
                current.replace('\\r\\n', '\n')
                .replace('\\n', '\n')
                .replace('\\r', '')
                .replace('\\"', '"')
                .replace('\\\\', '\\')
            )
        else:
            break

    # Normalize newlines
    current = current.replace('\r\n', '\n').replace('\r', '\n')
    current = re.sub(r'\n{3,}', '\n\n', current)

    return current.strip()

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
        # Avoid false positives for conversational questions
        non_edit_idioms = ["thay vì", "đổi lại", "thay cho", "bớt giận", "xóa tan"]
        if any(idiom in msg_lower for idiom in non_edit_idioms):
            return False

        edit_keywords = [
            "mở đầu", "đoạn mở", "mở bài", "đoạn kết", "kết thúc", "kết bài",
            "sửa lại", "thay đổi", "viết lại", "đổi tên", "chỉnh sửa", "thay phần",
            "thay đoạn", "tạo phần", "làm lại", "cắt bỏ", "thêm cảnh", "thêm đoạn",
            "bỏ đoạn", "đổi phong cách", "đổi giọng văn", "tăng kịch tính", "sửa câu",
            "khác đi", "hay hơn", "ngắn lại", "dài ra", "u tối hơn", "hài hước hơn",
            "soạn lại", "viết tiếp", "bản thảo"
        ]
        if any(k in msg_lower for k in edit_keywords):
            return True
        # Match single-word verbs as individual words/tokens
        single_word_verbs = ["sửa", "chỉnh", "thay", "đổi", "bớt", "xóa"]
        for verb in single_word_verbs:
            if re.search(rf'(?:\b|^){re.escape(verb)}(?:\b|$)', msg_lower):
                return True
        return False

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
            cleaned = re.sub(r'^```(?:json)?\s*\n?', '', resp.strip(), flags=re.IGNORECASE).strip()
            cleaned = re.sub(r'\n?```\s*$', '', cleaned).strip()
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            data = None
            if match:
                try:
                    data = json.loads(match.group(0), strict=False)
                except Exception as parse_err:
                    safe_log(f"[Copilot Direct Edit] json.loads strict=False failed: {parse_err}. Attempting unwrap_story_prose.")

            if isinstance(data, dict):
                content_candidate = data.get("updated_story_content")
                if not content_candidate and isinstance(data.get("action_params"), dict):
                    content_candidate = data["action_params"].get("updated_story_content")
                if not content_candidate:
                    content_candidate = data.get("story_content") or data.get("content")
                if content_candidate:
                    clean_story = unwrap_story_prose(content_candidate)
                    return {
                        "thought": f"Đã thực hiện can thiệp trực tiếp vào bản thảo theo yêu cầu: {user_instruction}",
                        "action": "edit_story_direct",
                        "action_params": {
                            "updated_story_content": clean_story,
                            "summary_of_changes": data.get("summary_of_changes", "Đã cập nhật bản thảo theo yêu cầu của bạn."),
                            "message": data.get("message", "Tôi đã chỉnh sửa trực tiếp vào bản thảo của bạn theo yêu cầu!")
                        }
                    }

            # Resilient fallback: unwrap directly on match or cleaned
            unwrapped_fallback = unwrap_story_prose(match.group(0) if match else cleaned)
            if unwrapped_fallback and not unwrapped_fallback.startswith("{"):
                return {
                    "thought": f"Đã trích xuất văn bản can thiệp trực tiếp: {user_instruction}",
                    "action": "edit_story_direct",
                    "action_params": {
                        "updated_story_content": unwrapped_fallback,
                        "summary_of_changes": "Đã cập nhật bản thảo theo yêu cầu của bạn.",
                        "message": "Tôi đã chỉnh sửa trực tiếp vào bản thảo của bạn theo yêu cầu!"
                    }
                }

            # Direct prose fallback if LLM returned text instead of JSON
            if cleaned:
                clean_story = unwrap_story_prose(cleaned)
                if clean_story and not clean_story.startswith("{"):
                    return {
                        "thought": f"Can thiệp trực tiếp bằng văn bản mới sinh: {user_instruction}",
                        "action": "edit_story_direct",
                        "action_params": {
                            "updated_story_content": clean_story,
                            "summary_of_changes": "Đã cập nhật bản thảo theo yêu cầu.",
                            "message": "Tôi đã chỉnh sửa trực tiếp vào bản thảo của bạn theo yêu cầu!"
                        }
                    }
        except Exception as e:
            safe_log(f"[Copilot Direct Edit] Error: {e}")
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

        if not user_message and isinstance(event_data, str):
            user_message = event_data

        if not current_story and memory:
            current_story = memory.get_short_context(max_chars=6000)

        # 1. Check if user requested direct manuscript intervention
        if self._is_direct_edit_request(user_message):
            safe_log(f"[Copilot] Detected direct manuscript edit request: {user_message[:40]}")
            if current_story:
                direct_edit_result = self._perform_direct_manuscript_edit(user_message, current_story)
                if direct_edit_result:
                    return direct_edit_result
            else:
                return {
                    "thought": "Yêu cầu chỉnh sửa bản thảo nhưng chưa có nội dung truyện để sửa.",
                    "action": "reply_user",
                    "action_params": {
                        "message": "Tôi rất sẵn lòng chỉnh sửa! Hãy đảm bảo bạn đã có nội dung truyện trên màn hình soạn thảo để tôi thực hiện nhé."
                    }
                }

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
            cleaned = re.sub(r'^```(?:json)?\s*\n?', '', response.strip(), flags=re.IGNORECASE).strip()
            cleaned = re.sub(r'\n?```\s*$', '', cleaned).strip()
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                res = json.loads(match.group(0), strict=False)
            else:
                res = json.loads(response, strict=False)

            if isinstance(res, dict) and res.get("action") == "edit_story_direct":
                if "action_params" not in res or not isinstance(res.get("action_params"), dict):
                    res["action_params"] = {}
                params = res["action_params"]
                if "updated_story_content" not in params and "updated_story_content" in res:
                    params["updated_story_content"] = res["updated_story_content"]
                if "updated_story_content" in params:
                    params["updated_story_content"] = unwrap_story_prose(params["updated_story_content"])
            return res
        except Exception as e:
            safe_log(f"Master Controller Error: {e}")
            return {
                "thought": f"Lỗi hệ thống khi phân tích event: {str(e)}",
                "action": "reply_user",
                "action_params": {"message": "Xin lỗi, Hệ thống chỉ huy đang gặp trục trặc nhẹ. Bạn vui lòng thử lại nhé!"}
            }
