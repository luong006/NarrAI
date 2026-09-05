from groq import Groq
import os
import json

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama3-70b-8192" # Use llama3 for better JSON formatting

def generate_comic_script(story_text: str):
    prompt = f"""
Bạn là một Đạo diễn Truyện tranh (Comic Director) tài năng. Nhiệm vụ của bạn là chuyển thể một đoạn tiểu thuyết thành kịch bản truyện tranh (Comic Script).
Hãy phân rã nội dung sau thành 4 khung tranh (Panels).

ĐẦU RA PHẢI LÀ MỘT MẢNG JSON HỢP LỆ (VALID JSON ARRAY). Không trả về bất kỳ text nào khác ngoài JSON.
Mỗi Object trong mảng gồm các trường:
- "panel_index": số thứ tự (1, 2, 3, 4)
- "image_prompt": Mô tả hình ảnh (bằng tiếng Anh, dùng để vẽ AI)
- "dialogue_text": Lời thoại hoặc âm thanh hoặc mô tả ngắn (bằng tiếng Việt, để nhét vào bóng thoại)
- "layout_type": "square", "wide", hoặc "tall"

Nội dung tiểu thuyết:
{story_text}

JSON Output:
"""
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL,
            temperature=0.7,
            max_tokens=1500,
        )
        # Try to parse JSON from response
        raw_output = response.choices[0].message.content
        
        import re
        # Clean up in case LLM added markdown formatting or text preamble
        match = re.search(r'\[.*\]', raw_output, re.DOTALL)
        if match:
            raw_output = match.group(0)
            
        script_data = json.loads(raw_output.strip())
        return script_data
    except Exception as e:
        print("Error parsing comic script:", e)
        # Fallback dummy script
        return [
            {"panel_index": 1, "image_prompt": "A cinematic wide shot of a beautiful landscape, masterpiece", "dialogue_text": "Ngày xửa ngày xưa...", "layout_type": "wide"},
            {"panel_index": 2, "image_prompt": "Close up of a mysterious character's eyes", "dialogue_text": "Có một bí mật...", "layout_type": "tall"},
            {"panel_index": 3, "image_prompt": "An action scene with sword clash", "dialogue_text": "KENG!", "layout_type": "square"},
            {"panel_index": 4, "image_prompt": "A character walking away into the sunset", "dialogue_text": "Cuộc hành trình bắt đầu.", "layout_type": "wide"}
        ]
