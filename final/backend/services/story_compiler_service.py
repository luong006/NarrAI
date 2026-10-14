import os
import re
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv

logger = logging.getLogger("narrai.story_compiler")

class StoryCompilerService:
    """
    AI Story Compiler: Consumes research materials and compiles narrative prose
    into structured JSON using Anthropic Claude API (primary) or Groq LLM (fallback).
    """

    def __init__(self):
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        load_dotenv(dotenv_path=env_path)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022").strip()
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_fallback_models = [
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "qwen/qwen3.8-27b",
            "allam-2-7b"
        ]

    async def compile_story(
        self,
        story_id: str,
        title: str,
        topic: str,
        category: str,
        research_data: Dict[str, Any],
        genres: Optional[List[str]] = None,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """
        Executes the AI story compilation pipeline.
        Returns the finalized story dictionary adhering strictly to the JSON schema.
        """
        is_legend = research_data.get("isLegend", False)
        sources = research_data.get("sources", [])
        research_notes = research_data.get("researchNotes", "")
        clean_genres = genres or (["Truyền thuyết", "Dân gian Việt Nam"] if is_legend else ["Lịch sử", "Anh hùng dân tộc"])

        system_prompt = self._build_system_prompt(is_legend=is_legend)
        user_prompt = self._build_user_prompt(
            story_id=story_id,
            title=title,
            topic=topic,
            category=category,
            genres=clean_genres,
            research_notes=research_notes,
            sources=sources,
            is_legend=is_legend,
            language=language
        )

        raw_response = None
        model_used = "unknown"

        # 1. Try Anthropic Claude API if key is provided
        if self.anthropic_api_key:
            try:
                raw_response, model_used = await self._call_claude_api(system_prompt, user_prompt)
            except Exception as e:
                logger.warning(f"Claude API compilation failed: {e}. Falling back to Groq...")

        # 2. Fallback to Groq API
        if not raw_response and self.groq_api_key:
            raw_response, model_used = await self._call_groq_api(system_prompt, user_prompt)

        if not raw_response:
            raise RuntimeError("Cả Claude API và Groq API đều không thể biên soạn truyện. Vui lòng kiểm tra API Key.")

        # 3. Parse and normalize structured JSON
        story_json = self._parse_json_response(raw_response)

        # 4. Standardize metadata & calculate exact word count in code
        story_json["id"] = story_id
        story_json["title"] = title
        story_json["slug"] = story_id
        story_json["category"] = category or ("Truyền thuyết & Thần thoại" if is_legend else "Lịch sử Việt Nam")
        story_json["genre"] = story_json.get("genre") or clean_genres
        
        # Ensure sources only contain verified real URLs from research
        story_json["sources"] = sources

        content_prose = story_json.get("content", "").strip()
        calculated_word_count = len(re.findall(r'\S+', content_prose))

        story_json["metadata"] = {
            "language": language,
            "wordCount": calculated_word_count,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "aiModel": model_used
        }

        return story_json

    def _build_system_prompt(self, is_legend: bool) -> str:
        nature_guide = (
            "Đối với TRUYỀN THUYẾT / THẦN THOẠI: Tôn trọng yếu tố kỳ ảo, huyền tích dân gian. "
            "Trong phần historicalNotes, hãy phân loại rõ loại claim là 'folklore_legend' hoặc 'mythological_element', "
            "không được trình bày truyền thuyết như sự kiện lịch sử chính sử đã được chứng minh."
            if is_legend else
            "Đối với LỊCH SỬ CHÍNH SỬ: Giữ chính xác các niên đại, nhân vật, địa danh, chiến công và sự kiện trọng đại. "
            "Trong phần historicalNotes, hãy phân loại loại claim là 'historical_fact' và liên kết với nguồn tham khảo."
        )

        return f"""Bạn là Nhà văn & Chuyên gia Sử học Việt Nam hàng đầu thuộc nền tảng NarrAI.
Nhiệm vụ của bạn là biên soạn một tác phẩm truyện hoàn chỉnh, giàu tính văn học, lôi cuốn và truyền cảm hứng dựa trên tư liệu tham khảo.

QUY TẮC BẮT BUỘC:
1. Văn phong: Thuần Việt, sinh động, giàu hình tượng, nhịp điệu kể chuyện hấp dẫn, phù hợp với mọi lứa tuổi độc giả.
2. Không sao chép nguyên văn: Tổng hợp dữ kiện từ nguồn tham khảo thành tác phẩm văn học độc lập với phong cách kể chuyện sáng tạo.
3. {nature_guide}
4. Tuyệt đối KHÔNG tự bịa nguồn URL. Nguồn tham khảo sẽ do hệ thống tự động gán từ tư liệu thực tế.
5. Nội dung 'content' phải là truyện hoàn chỉnh, độ dài từ 400 đến 1200 từ (không viết dàn ý, không viết tóm tắt trong content).
6. Định dạng đầu ra: BẮT BUỘC trả về duy nhất 1 JSON object hợp lệ, không bọc thêm bất kỳ lời dẫn giải nào ngoài khối JSON."""

    def _build_user_prompt(
        self,
        story_id: str,
        title: str,
        topic: str,
        category: str,
        genres: List[str],
        research_notes: str,
        sources: List[Dict[str, Any]],
        is_legend: bool,
        language: str
    ) -> str:
        source_titles = [s.get("title", "") for s in sources]
        
        return f"""Hãy biên soạn tác phẩm truyện hoàn chỉnh cho đề bài sau:

ĐỀ BÀI:
- ID/Slug: {story_id}
- Tiêu đề: {title}
- Chủ đề: {topic}
- Thể loại dự kiến: {', '.join(genres)}
- Thể loại truyện: {'Truyền thuyết / Thần thoại' if is_legend else 'Lịch sử Việt Nam'}
- Ngôn ngữ: {language}

TƯ LIỆU THAM KHẢO TỪ WIKIPEDIA:
{research_notes}

DANH SÁCH NGUỒN XÁC THỰC:
{json.dumps(source_titles, ensure_ascii=False)}

YÊU CẦU ĐỊNH DẠNG JSON ĐẦU RA:
Trích xuất và trả về đúng định dạng JSON như sau:
{{
  "id": "{story_id}",
  "title": "{title}",
  "slug": "{story_id}",
  "category": "{category}",
  "genre": {json.dumps(genres, ensure_ascii=False)},
  "summary": "Tóm tắt súc tích, hấp dẫn trong 2-3 câu (dưới 300 ký tự)...",
  "content": "Nội dung câu chuyện hoàn chỉnh đầy đủ mở đầu, cao trào, kết thúc...",
  "lesson": "Bài học lịch sử / nhân sinh hoặc thông điệp văn hóa sâu sắc từ câu chuyện...",
  "historicalNotes": [
    {{
      "claim": "Dữ kiện hoặc tình tiết chính cần ghi chú",
      "type": "{"folklore_legend" if is_legend else "historical_fact"}",
      "sources": {json.dumps(source_titles[:1], ensure_ascii=False)}
    }}
  ]
}}"""

    async def _call_claude_api(self, system_prompt: str, user_prompt: str) -> tuple[str, str]:
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.anthropic_model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            if res.status_code != 200:
                raise RuntimeError(f"Anthropic API error {res.status_code}: {res.text}")
            data = res.json()
            content_blocks = data.get("content", [])
            text_blocks = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
            return "\n".join(text_blocks), self.anthropic_model

    async def _call_groq_api(self, system_prompt: str, user_prompt: str) -> tuple[str, str]:
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }

        last_err = None
        for model_name in self.groq_fallback_models:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.65,
                "max_tokens": 3000
            }
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    res = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        raw_text = data["choices"][0]["message"]["content"]
                        # Verify we can extract JSON
                        try:
                            self._parse_json_response(raw_text)
                            return raw_text, model_name
                        except Exception as parse_e:
                            last_err = f"Model {model_name} response JSON parse failed: {parse_e}"
                            logger.warning(last_err)
                    else:
                        last_err = f"Groq model {model_name} returned {res.status_code}: {res.text}"
                        logger.warning(last_err)
            except Exception as e:
                last_err = f"Groq model {model_name} connection error: {e}"
                logger.warning(last_err)

        raise RuntimeError(f"All Groq models failed: {last_err}")

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """
        Cleans markdown fences, extracts outermost JSON block, and parses safely.
        """
        clean_text = text.strip()
        # Remove ```json ... ```
        clean_text = re.sub(r'^```(?:json)?\s*', '', clean_text, flags=re.MULTILINE)
        clean_text = re.sub(r'\s*```$', '', clean_text, flags=re.MULTILINE)

        # Find first '{' and last '}'
        start_idx = clean_text.find('{')
        end_idx = clean_text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            clean_text = clean_text[start_idx:end_idx+1]

        try:
            return json.loads(clean_text)
        except json.JSONDecodeError as err:
            logger.error(f"JSON decode failed for response: {clean_text[:300]}... Error: {err}")
            raise ValueError(f"AI response is not valid JSON: {err}")
