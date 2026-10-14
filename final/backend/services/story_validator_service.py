import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger("narrai.story_validator")

class StoryValidatorService:
    """
    Automated Multi-Layer Quality & Safety Gatekeeper:
    Enforces Structural, Content, Duplicate, Source, and Security invariants before PR creation.
    """

    MIN_WORD_COUNT = 300
    MAX_SUMMARY_LENGTH = 600
    FORBIDDEN_PLACEHOLDERS = [
        "todo", "lorem ipsum", "tôi chưa thể", "nan", "undefined", "null",
        "insert text here", "đoạn văn mẫu", "[placeholder]", "lời thoại mẫu"
    ]
    SECRET_PATTERNS = [
        r'gsk_[A-Za-z0-9_]{20,}',
        r'sk-ant-[A-Za-z0-9_\-]{20,}',
        r'ghp_[A-Za-z0-9]{20,}',
        r'github_pat_[A-Za-z0-9_]{20,}',
        r'bearer\s+[a-zA-Z0-9_\-\.]{25,}',
        r'password\s*=\s*["\'][^"\']+["\']'
    ]

    def __init__(self, data_dir: Optional[str] = None):
        if not data_dir:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_dir = os.path.join(backend_dir, "data")
        else:
            self.data_dir = data_dir

    def validate_story(
        self,
        story: Dict[str, Any],
        existing_stories: Optional[List[Dict[str, Any]]] = None,
        is_update: bool = False
    ) -> Dict[str, Any]:
        """
        Validates the story dictionary across all 5 verification layers.
        Returns validation result dictionary.
        """
        errors: List[str] = []
        warnings: List[str] = []
        duplicate_candidates: List[str] = []

        # 1. Structural Check
        self._check_structure(story, errors)

        # 2. Content Quality Check
        word_count = self._check_content(story, errors, warnings)

        # 3. Duplicate Check
        self._check_duplicates(story, existing_stories, duplicate_candidates, warnings, is_update)

        # 4. Source Verification Check
        self._check_sources(story, errors, warnings)

        # 5. Security & Safety Check
        self._check_security(story, errors)

        passed = len(errors) == 0

        return {
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "wordCount": word_count,
            "duplicateCandidates": duplicate_candidates
        }

    def _check_structure(self, story: Dict[str, Any], errors: List[str]):
        required_fields = [
            "id", "title", "slug", "category", "genre",
            "summary", "content", "lesson", "sources", "metadata"
        ]

        if not isinstance(story, dict):
            errors.append("Cấu trúc story phải là một JSON Object.")
            return

        for field in required_fields:
            if field not in story:
                errors.append(f"Thiếu trường bắt buộc: '{field}'.")
            elif story[field] is None:
                errors.append(f"Trường '{field}' không được mang giá trị null.")

        # Slug validation (no path traversal, alphanumeric & hyphens only)
        slug = str(story.get("slug", "")).strip()
        if not slug:
            errors.append("Slug truyện không được để trống.")
        elif not re.match(r'^[a-z0-9\-]+$', slug):
            errors.append("Slug chỉ được chứa chữ cái thường, số và dấu gạch ngang (kebab-case).")
        if ".." in slug or "/" in slug or "\\" in slug:
            errors.append("Slug vi phạm an toàn đường dẫn hệ thống (Path Traversal attempt).")

        # Genres check
        genres = story.get("genre")
        if not isinstance(genres, list) or len(genres) == 0:
            errors.append("Trường 'genre' phải là một mảng danh sách thể loại chứa ít nhất 1 thể loại.")

    def _check_content(self, story: Dict[str, Any], errors: List[str], warnings: List[str]) -> int:
        content = str(story.get("content", "")).strip()
        summary = str(story.get("summary", "")).strip()
        lesson = str(story.get("lesson", "")).strip()

        # Word count calculation
        words = re.findall(r'\S+', content)
        word_count = len(words)

        if word_count < self.MIN_WORD_COUNT:
            errors.append(f"Nội dung truyện quá ngắn ({word_count} từ). Yêu cầu tối thiểu {self.MIN_WORD_COUNT} từ.")

        if len(summary) > self.MAX_SUMMARY_LENGTH:
            warnings.append(f"Tóm tắt truyện hơi dài ({len(summary)} ký tự). Khuyến nghị dưới {self.MAX_SUMMARY_LENGTH} ký tự.")

        if not lesson or len(lesson) < 15:
            warnings.append("Bài học rút ra ('lesson') còn ngắn hoặc chưa rõ ràng.")

        # Placeholder checks
        combined_text = f"{content} {summary} {lesson}".lower()
        for placeholder in self.FORBIDDEN_PLACEHOLDERS:
            if placeholder in combined_text:
                errors.append(f"Phát hiện văn bản placeholder / chưa hoàn thiện: '{placeholder}'.")

        # Degenerate repeating paragraph check
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 30]
        seen_p: Set[str] = set()
        for p in paragraphs:
            norm_p = re.sub(r'\s+', ' ', p.lower())
            if norm_p in seen_p:
                errors.append("Phát hiện đoạn văn bị lặp lại bất thường trong nội dung truyện.")
                break
            seen_p.add(norm_p)

        return word_count

    def _check_duplicates(
        self,
        story: Dict[str, Any],
        existing_stories: Optional[List[Dict[str, Any]]],
        duplicate_candidates: List[str],
        warnings: List[str],
        is_update: bool
    ):
        curr_id = str(story.get("id", "")).strip().lower()
        curr_slug = str(story.get("slug", "")).strip().lower()
        curr_title_norm = self._normalize_for_comparison(str(story.get("title", "")))

        # Load existing stories from local files if not provided
        stories_to_check: List[Dict[str, Any]] = existing_stories or []
        if not existing_stories:
            stories_to_check = self._load_all_local_stories()

        for s in stories_to_check:
            s_id = str(s.get("id", "")).strip().lower()
            s_slug = str(s.get("slug", "")).strip().lower()
            s_title_norm = self._normalize_for_comparison(str(s.get("title", "")))

            # If updating the same story ID, skip self
            if is_update and (curr_id == s_id or curr_slug == s_slug):
                continue

            if curr_id == s_id or curr_slug == s_slug:
                duplicate_candidates.append(f"Trùng ID/Slug với truyện: '{s.get('title')}' (ID: {s_id})")
            elif curr_title_norm and s_title_norm and curr_title_norm == s_title_norm:
                duplicate_candidates.append(f"Trùng tiêu đề với truyện đã có: '{s.get('title')}' (ID: {s_id})")

        if duplicate_candidates:
            warnings.append(f"Cảnh báo trùng lặp: {', '.join(duplicate_candidates)}")

    def _check_sources(self, story: Dict[str, Any], errors: List[str], warnings: List[str]):
        sources = story.get("sources", [])
        if not isinstance(sources, list) or len(sources) == 0:
            warnings.append("Truyện chưa có nguồn tư liệu tham khảo xác thực.")
            return

        for idx, src in enumerate(sources):
            if not isinstance(src, dict):
                errors.append(f"Nguồn tham khảo thứ {idx+1} không đúng định dạng object.")
                continue
            url = str(src.get("url", "")).strip()
            if not url or not (url.startswith("http://") or url.startswith("https://")):
                errors.append(f"URL nguồn '{url}' không hợp lệ hoặc rỗng.")
            # Check for hallucinated domains
            if "example.com" in url or "placeholder.com" in url:
                errors.append(f"URL nguồn '{url}' là liên kết giả lập.")

    def _check_security(self, story: Dict[str, Any], errors: List[str]):
        raw_dump = json.dumps(story, ensure_ascii=False)
        for pattern in self.SECRET_PATTERNS:
            if re.search(pattern, raw_dump, re.IGNORECASE):
                errors.append("Phát hiện dữ liệu nhạy cảm hoặc API Key bị lộ trong nội dung JSON!")
                break

    def _load_all_local_stories(self) -> List[Dict[str, Any]]:
        stories = []
        stories_dir = os.path.join(self.data_dir, "stories")
        if os.path.exists(stories_dir):
            for fname in os.listdir(stories_dir):
                if fname.endswith(".json"):
                    fpath = os.path.join(stories_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                stories.append(data)
                    except Exception:
                        pass
        return stories

    @staticmethod
    def _normalize_for_comparison(text: str) -> str:
        text = text.lower()
        patterns = {
            '[àáạảãâầấậẩẫăằắặẳẵ]': 'a',
            '[èéẹẻẽêềếệểễ]': 'e',
            '[ìíịỉĩ]': 'i',
            '[òóọỏõôồốộổỗơờớợởỡ]': 'o',
            '[ùúụủũưừứựửữ]': 'u',
            '[ỳýỵỷỹ]': 'y',
            '[đ]': 'd',
        }
        for pattern, replacement in patterns.items():
            text = re.sub(pattern, replacement, text)
        return re.sub(r'[^a-z0-9]', '', text).strip()
