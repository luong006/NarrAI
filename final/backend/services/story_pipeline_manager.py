import os
import re
import json
import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from services.wikipedia_service import WikipediaService
from services.story_compiler_service import StoryCompilerService
from services.story_validator_service import StoryValidatorService
from services.github_service import GitHubService

logger = logging.getLogger("narrai.story_pipeline_manager")

class StoryPipelineManager:
    """
    Master orchestrator for the AI Story Pipeline:
    Queue Management -> Wikipedia Research -> AI Compilation -> Automated Validation -> GitHub PR Automation.
    """

    _lock = threading.Lock()

    def __init__(self):
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.backend_dir = backend_dir
        self.root_dir = os.path.dirname(backend_dir)
        
        self.backend_data_dir = os.path.join(backend_dir, "data")
        self.root_data_dir = os.path.join(self.root_dir, "data")
        
        self.backend_queue_file = os.path.join(self.backend_data_dir, "queue.json")
        self.root_queue_file = os.path.join(self.root_data_dir, "queue.json")

        self.backend_stories_dir = os.path.join(self.backend_data_dir, "stories")
        self.root_stories_dir = os.path.join(self.root_data_dir, "stories")

        # Initialize sub-services
        self.wikipedia_service = WikipediaService()
        self.compiler_service = StoryCompilerService()
        self.validator_service = StoryValidatorService(data_dir=self.backend_data_dir)
        self.github_service = GitHubService()

        # In-memory execution logs
        self.pipeline_logs: List[Dict[str, Any]] = []

    # ==================== QUEUE PERSISTENCE ====================

    def _read_queue(self) -> Dict[str, Any]:
        with self._lock:
            target_path = self.backend_queue_file if os.path.exists(self.backend_queue_file) else self.root_queue_file
            if os.path.exists(target_path):
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Error reading queue.json: {e}")
            
            return {"version": 1, "stories": []}

    def _write_queue(self, queue_data: Dict[str, Any]):
        with self._lock:
            # Write to both backend/data/queue.json and data/queue.json for complete synchronization
            for target_path in [self.backend_queue_file, self.root_queue_file]:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(queue_data, f, ensure_ascii=False, indent=2)

    def _log_event(self, story_id: str, level: str, message: str, details: Any = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "storyId": story_id,
            "level": level,
            "message": message,
            "details": details
        }
        self.pipeline_logs.append(entry)
        if len(self.pipeline_logs) > 500:
            self.pipeline_logs = self.pipeline_logs[-500:]
        logger.info(f"[{story_id}] {level.upper()}: {message}")

    # ==================== QUEUE OPERATIONS ====================

    def get_queue(self) -> List[Dict[str, Any]]:
        data = self._read_queue()
        return data.get("stories", [])

    def get_overview(self) -> Dict[str, Any]:
        stories = self.get_queue()
        total = len(stories)
        pending = sum(1 for s in stories if s.get("status") == "pending")
        researching = sum(1 for s in stories if s.get("status") in ("researching", "writing", "validating"))
        failed = sum(1 for s in stories if s.get("status") == "failed")
        pr_created = sum(1 for s in stories if s.get("status") == "pr_created")
        merged = sum(1 for s in stories if s.get("status") == "merged")

        return {
            "totalStories": total,
            "pending": pending,
            "inProgress": researching,
            "failed": failed,
            "prCreated": pr_created,
            "merged": merged,
            "stories": stories
        }

    def add_story(self, item: Dict[str, Any]) -> Dict[str, Any]:
        title = str(item.get("title", "")).strip()
        if not title:
            raise ValueError("Tiêu đề truyện không được để trống.")

        # Generate slug/id
        raw_id = item.get("id") or self._slugify(title)
        clean_id = self._slugify(raw_id)
        if not clean_id:
            raise ValueError("Mã ID/Slug không hợp lệ.")

        queue = self._read_queue()
        stories = queue.get("stories", [])

        # Check duplicate ID
        if any(s.get("id") == clean_id for s in stories):
            raise ValueError(f"Đề bài với ID '{clean_id}' đã tồn tại trong hàng đợi.")

        new_entry = {
            "id": clean_id,
            "title": title,
            "topic": item.get("topic") or "Lịch sử & Văn hóa Việt Nam",
            "category": item.get("category") or "Lịch sử Việt Nam",
            "genre": item.get("genre") or ["Lịch sử", "Văn hóa"],
            "language": item.get("language") or "vi",
            "sourceLanguages": item.get("sourceLanguages") or ["vi", "en"],
            "status": "pending",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "prUrl": None,
            "prNumber": None,
            "branchName": None,
            "error": None
        }

        stories.append(new_entry)
        queue["stories"] = stories
        self._write_queue(queue)
        self._log_event(clean_id, "info", f"Thêm mới đề bài '{title}' vào hàng đợi.")

        return new_entry

    def batch_add_stories(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        added = []
        errors = []
        for item in items:
            try:
                entry = self.add_story(item)
                added.append(entry)
            except Exception as e:
                errors.append({"title": item.get("title"), "error": str(e)})

        return {
            "success": True,
            "addedCount": len(added),
            "errorCount": len(errors),
            "added": added,
            "errors": errors
        }

    def update_story(self, story_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        queue = self._read_queue()
        stories = queue.get("stories", [])
        target = next((s for s in stories if s.get("id") == story_id), None)
        if not target:
            raise ValueError(f"Không tìm thấy truyện với ID '{story_id}'")

        allowed_keys = ["title", "topic", "category", "genre", "language", "sourceLanguages", "status", "error"]
        for k in allowed_keys:
            if k in updates:
                target[k] = updates[k]

        target["updatedAt"] = datetime.now(timezone.utc).isoformat()
        self._write_queue(queue)
        return target

    def delete_story(self, story_id: str) -> bool:
        queue = self._read_queue()
        stories = queue.get("stories", [])
        new_stories = [s for s in stories if s.get("id") != story_id]
        if len(new_stories) == len(stories):
            return False

        queue["stories"] = new_stories
        self._write_queue(queue)
        self._log_event(story_id, "info", f"Đã xóa đề bài '{story_id}' khỏi hàng đợi.")
        return True

    # ==================== PIPELINE EXECUTION ====================

    async def run_single_story(self, story_id: str) -> Dict[str, Any]:
        """
        Executes the 4-step pipeline for a single story:
        1. Wikipedia Source Collection
        2. Claude / Groq AI Compilation
        3. 5-Layer Quality & Safety Validation
        4. GitHub Feature Branch & PR Creation
        """
        queue = self._read_queue()
        stories = queue.get("stories", [])
        story_entry = next((s for s in stories if s.get("id") == story_id), None)
        if not story_entry:
            raise ValueError(f"Không tìm thấy đề bài '{story_id}' trong hàng đợi.")

        title = story_entry.get("title", story_id)
        topic = story_entry.get("topic", "")
        category = story_entry.get("category", "Lịch sử Việt Nam")
        source_languages = story_entry.get("sourceLanguages", ["vi", "en"])
        genres = story_entry.get("genre", ["Lịch sử"])

        try:
            # Step 1: Researching
            self._update_status(story_id, "researching")
            self._log_event(story_id, "info", f"Bắt đầu thu thập tư liệu Wikipedia cho '{title}'...")
            research_data = await self.wikipedia_service.fetch_research_material(
                query=title,
                topic=topic,
                source_languages=source_languages
            )
            self._log_event(story_id, "info", f"Thu thập xong {len(research_data.get('sources', []))} nguồn tư liệu.")

            # Step 2: Compiling
            self._update_status(story_id, "writing")
            self._log_event(story_id, "info", f"Bắt đầu AI biên soạn truyện...")
            compiled_story = await self.compiler_service.compile_story(
                story_id=story_id,
                title=title,
                topic=topic,
                category=category,
                research_data=research_data,
                genres=genres,
                language=story_entry.get("language", "vi")
            )
            self._log_event(story_id, "info", f"AI đã hoàn thành bản thảo ({compiled_story['metadata']['wordCount']} từ).")

            # Step 3: Validating
            self._update_status(story_id, "validating")
            self._log_event(story_id, "info", "Tiến hành kiểm định chất lượng và tính an toàn...")
            validation_result = self.validator_service.validate_story(compiled_story)

            if not validation_result["passed"]:
                error_msg = "; ".join(validation_result["errors"])
                self._update_status(story_id, "failed", error=error_msg)
                self._log_event(story_id, "error", f"Kiểm định thất bại: {error_msg}")
                return {
                    "success": False,
                    "stage": "validation",
                    "errors": validation_result["errors"],
                    "warnings": validation_result["warnings"],
                    "story": compiled_story
                }

            # Save story locally to backend and root data directories
            self._save_story_file(story_id, compiled_story)

            # Step 4: GitHub PR Creation
            self._log_event(story_id, "info", "Bắt đầu tạo nhánh và Pull Request trên GitHub...")
            pr_result = await self.github_service.create_story_pull_request(
                story=compiled_story,
                validation_result=validation_result
            )

            # Update queue status to pr_created
            self._update_status(
                story_id,
                "pr_created",
                pr_url=pr_result.get("prUrl"),
                pr_number=pr_result.get("prNumber"),
                branch_name=pr_result.get("branchName")
            )
            self._log_event(story_id, "success", f"Đã mở Pull Request: {pr_result.get('prUrl')}")

            return {
                "success": True,
                "storyId": story_id,
                "title": title,
                "status": "pr_created",
                "validation": validation_result,
                "pr": pr_result,
                "story": compiled_story
            }

        except Exception as e:
            err_str = str(e)
            self._update_status(story_id, "failed", error=err_str)
            self._log_event(story_id, "error", f"Lỗi thực thi pipeline: {err_str}")
            return {
                "success": False,
                "stage": "execution",
                "error": err_str
            }

    async def run_batch_pipeline(self, limit: int = 3) -> Dict[str, Any]:
        """
        Processes pending items sequentially up to the configured limit.
        """
        queue = self._read_queue()
        stories = queue.get("stories", [])
        pending_items = [s for s in stories if s.get("status") == "pending"][:limit]

        results = []
        for item in pending_items:
            res = await self.run_single_story(item["id"])
            results.append(res)
            # Brief delay between stories to prevent external API burst limits
            await asyncio.sleep(2.0)

        return {
            "processedCount": len(results),
            "results": results
        }

    # ==================== PULL REQUESTS & PREVIEW ====================

    async def get_pull_requests_list(self) -> List[Dict[str, Any]]:
        stories = self.get_queue()
        pr_stories = [s for s in stories if s.get("status") in ("pr_created", "merged") or s.get("prUrl")]

        results = []
        for s in pr_stories:
            pr_num = s.get("prNumber")
            live_status = {"state": "open", "merged": False}
            if pr_num and pr_num > 0:
                try:
                    live_status = await self.github_service.get_pull_request_status(pr_num)
                    # If live status says merged and queue is not yet marked merged, auto-update
                    if live_status.get("merged") and s.get("status") != "merged":
                        self._update_status(s["id"], "merged")
                        s["status"] = "merged"
                except Exception:
                    pass

            results.append({
                "id": s["id"],
                "title": s["title"],
                "topic": s.get("topic"),
                "category": s.get("category"),
                "status": s.get("status"),
                "prUrl": s.get("prUrl"),
                "prNumber": s.get("prNumber"),
                "branchName": s.get("branchName"),
                "updatedAt": s.get("updatedAt"),
                "liveState": live_status.get("state", "open"),
                "isMerged": live_status.get("merged", False)
            })

        return results

    def get_story_preview(self, story_id: str) -> Optional[Dict[str, Any]]:
        candidate_dirs = [
            self.backend_stories_dir,
            self.root_stories_dir,
            os.path.join(self.root_dir, "final", "data", "stories"),
            os.path.join(self.root_dir, "data", "stories"),
            os.path.join(self.backend_dir, "data", "stories"),
        ]
        for d in candidate_dirs:
            if not os.path.exists(d):
                continue
            fpath = os.path.join(d, f"{story_id}.json")
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Error loading story preview {story_id}: {e}")
        return None

    def get_published_stories(self) -> List[Dict[str, Any]]:
        """
        Lists all published / verified stories for the frontend reading view.
        """
        candidate_dirs = [
            self.backend_stories_dir,
            self.root_stories_dir,
            os.path.join(self.root_dir, "final", "data", "stories"),
            os.path.join(self.root_dir, "data", "stories"),
            os.path.join(self.backend_dir, "data", "stories"),
        ]
        stories = []
        seen_ids = set()
        for d in candidate_dirs:
            if not os.path.exists(d):
                continue
            for fname in os.listdir(d):
                if fname.endswith(".json"):
                    fpath = os.path.join(d, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, dict) and data.get("id"):
                                sid = data["id"]
                                if sid not in seen_ids:
                                    seen_ids.add(sid)
                                    stories.append(data)
                    except Exception:
                        pass
        return stories

    # ==================== HELPER METHODS ====================

    def _update_status(
        self,
        story_id: str,
        status: str,
        error: Optional[str] = None,
        pr_url: Optional[str] = None,
        pr_number: Optional[int] = None,
        branch_name: Optional[str] = None
    ):
        queue = self._read_queue()
        stories = queue.get("stories", [])
        for s in stories:
            if s.get("id") == story_id:
                s["status"] = status
                s["updatedAt"] = datetime.now(timezone.utc).isoformat()
                if error is not None:
                    s["error"] = error
                elif status in ("researching", "writing", "validating", "pr_created", "merged"):
                    s["error"] = None

                if pr_url:
                    s["prUrl"] = pr_url
                if pr_number:
                    s["prNumber"] = pr_number
                if branch_name:
                    s["branchName"] = branch_name
                break

        self._write_queue(queue)

    def _save_story_file(self, story_id: str, story: Dict[str, Any]):
        for target_dir in [self.backend_stories_dir, self.root_stories_dir]:
            os.makedirs(target_dir, exist_ok=True)
            fpath = os.path.join(target_dir, f"{story_id}.json")
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(story, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _slugify(text: str) -> str:
        text = text.lower().strip()
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
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        text = re.sub(r'[\s_]+', '-', text)
        return re.sub(r'-+', '-', text).strip('-')
