import os
import json
import base64
import logging
from typing import Dict, Any, Optional, List
import httpx
from dotenv import load_dotenv

logger = logging.getLogger("narrai.github")

class GitHubService:
    """
    Manages GitHub Pull Request automation for AI-compiled stories:
    Creates feature branches, commits JSON story files, and opens PRs for human approval.
    """

    def __init__(self):
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        load_dotenv(dotenv_path=env_path)
        
        self.token = os.getenv("GITHUB_TOKEN", "").strip()
        self.owner = os.getenv("GITHUB_OWNER", "anhdinh0701").strip()
        self.repo = os.getenv("GITHUB_REPO", "final").strip()
        self.base_branch = os.getenv("GITHUB_BASE_BRANCH", "main").strip()
        self.api_base = "https://api.github.com"

    def is_configured(self) -> bool:
        return bool(self.token and self.owner and self.repo)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "NarrAI-Story-Pipeline"
        }

    async def create_story_pull_request(
        self,
        story: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Creates branch, commits story file, and opens PR on GitHub.
        If GITHUB_TOKEN is not configured, returns local staged preview.
        """
        slug = story.get("slug") or story.get("id")
        title = story.get("title", slug)
        branch_name = f"ai-stories/{slug}"
        file_path = f"data/stories/{slug}.json"
        story_content_json = json.dumps(story, ensure_ascii=False, indent=2)

        # Fallback if no token is configured
        if not self.is_configured():
            logger.info("GITHUB_TOKEN not configured. Operating in Local Staging Mode.")
            return {
                "success": True,
                "isMock": True,
                "branchName": branch_name,
                "filePath": file_path,
                "prUrl": f"https://github.com/{self.owner}/{self.repo}/compare/{self.base_branch}...{branch_name}",
                "prNumber": 0,
                "state": "staged_local",
                "message": "Đã lưu bản thảo cục bộ. Cấu hình GITHUB_TOKEN để mở PR tự động trên GitHub."
            }

        async with httpx.AsyncClient(headers=self._get_headers(), timeout=30.0) as client:
            # 1. Get base branch commit SHA
            base_ref_url = f"{self.api_base}/repos/{self.owner}/{self.repo}/git/ref/heads/{self.base_branch}"
            res_ref = await client.get(base_ref_url)
            if res_ref.status_code != 200:
                raise RuntimeError(f"Không thể truy cập nhánh gốc '{self.base_branch}' trên GitHub: {res_ref.text}")
            
            base_sha = res_ref.json().get("object", {}).get("sha")

            # 2. Check if branch already exists, or create it
            branch_ref_url = f"{self.api_base}/repos/{self.owner}/{self.repo}/git/refs/heads/{branch_name}"
            res_check_branch = await client.get(branch_ref_url)
            
            if res_check_branch.status_code == 404:
                # Create branch
                create_ref_url = f"{self.api_base}/repos/{self.owner}/{self.repo}/git/refs"
                res_create_ref = await client.post(create_ref_url, json={
                    "ref": f"refs/heads/{branch_name}",
                    "sha": base_sha
                })
                if res_create_ref.status_code not in (200, 201):
                    raise RuntimeError(f"Lỗi khi tạo nhánh '{branch_name}': {res_create_ref.text}")

            # 3. Check existing file SHA in branch (for update if already exists)
            file_url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{file_path}?ref={branch_name}"
            res_file = await client.get(file_url)
            existing_file_sha = None
            if res_file.status_code == 200:
                existing_file_sha = res_file.json().get("sha")

            # 4. Commit story JSON file
            commit_payload = {
                "message": f"feat(story-pipeline): biên soạn tự động truyện '{title}' [{slug}]",
                "content": base64.b64encode(story_content_json.encode("utf-8")).decode("utf-8"),
                "branch": branch_name
            }
            if existing_file_sha:
                commit_payload["sha"] = existing_file_sha

            put_file_url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{file_path}"
            res_commit = await client.put(put_file_url, json=commit_payload)
            if res_commit.status_code not in (200, 201):
                raise RuntimeError(f"Lỗi khi commit tệp truyện '{file_path}': {res_commit.text}")

            # 5. Check if PR already exists for this branch
            pulls_url = f"{self.api_base}/repos/{self.owner}/{self.repo}/pulls"
            res_pulls = await client.get(pulls_url, params={"head": f"{self.owner}:{branch_name}", "state": "open"})
            if res_pulls.status_code == 200 and len(res_pulls.json()) > 0:
                existing_pr = res_pulls.json()[0]
                return {
                    "success": True,
                    "isMock": False,
                    "branchName": branch_name,
                    "filePath": file_path,
                    "prUrl": existing_pr.get("html_url"),
                    "prNumber": existing_pr.get("number"),
                    "state": existing_pr.get("state", "open"),
                    "message": "Pull Request đã tồn tại và đã được cập nhật commit mới."
                }

            # 6. Create new Pull Request
            pr_body = self._build_pr_body(story, validation_result)
            pr_payload = {
                "title": f"[AI Story Pipeline] Biên soạn: {title}",
                "head": branch_name,
                "base": self.base_branch,
                "body": pr_body,
                "draft": False
            }
            res_create_pr = await client.post(pulls_url, json=pr_payload)
            if res_create_pr.status_code not in (200, 201):
                raise RuntimeError(f"Lỗi khi tạo Pull Request trên GitHub: {res_create_pr.text}")

            pr_data = res_create_pr.json()
            return {
                "success": True,
                "isMock": False,
                "branchName": branch_name,
                "filePath": file_path,
                "prUrl": pr_data.get("html_url"),
                "prNumber": pr_data.get("number"),
                "state": "open",
                "message": f"Đã tạo thành công Pull Request #{pr_data.get('number')}."
            }

    async def get_pull_request_status(self, pr_number: int) -> Dict[str, Any]:
        """
        Queries the current status of a GitHub PR (open, merged, closed).
        """
        if not self.is_configured() or not pr_number:
            return {"state": "open", "merged": False, "isMock": True}

        pr_url = f"{self.api_base}/repos/{self.owner}/{self.repo}/pulls/{pr_number}"
        async with httpx.AsyncClient(headers=self._get_headers(), timeout=15.0) as client:
            res = await client.get(pr_url)
            if res.status_code != 200:
                return {"state": "unknown", "merged": False, "error": res.text}
            
            data = res.json()
            return {
                "state": data.get("state"),
                "merged": data.get("merged", False),
                "mergedAt": data.get("merged_at"),
                "closedAt": data.get("closed_at"),
                "htmlUrl": data.get("html_url"),
                "title": data.get("title")
            }

    def _build_pr_body(self, story: Dict[str, Any], validation: Dict[str, Any]) -> str:
        sources = story.get("sources", [])
        sources_md = "\n".join([f"- [{s.get('title', 'Nguồn')}]({s.get('url', '#')}) ({s.get('language', 'vi')})" for s in sources]) or "*(Chưa có nguồn URL)*"
        
        warnings_md = "\n".join([f"> ⚠️ {w}" for w in validation.get("warnings", [])]) or "✅ Không có cảnh báo."
        model_name = story.get("metadata", {}).get("aiModel", "Claude 3.5 Sonnet")
        word_count = validation.get("wordCount", story.get("metadata", {}).get("wordCount", 0))

        return f"""## 📚 [NarrAI Pipeline] Đề xuất bổ sung truyện: {story.get('title')}

### 📝 Thông tin tổng quan
- **Tiêu đề**: {story.get('title')}
- **Thể loại**: {', '.join(story.get('genre', []))}
- **Danh mục**: {story.get('category')}
- **Số từ**: ~{word_count} từ
- **AI Model**: `{model_name}`
- **Tập tin**: `data/stories/{story.get('slug')}.json`

---

### 📖 Tóm tắt tác phẩm
> {story.get('summary')}

---

### 🏛️ Nguồn tư liệu xác thực
{sources_md}

---

### 🔍 Kết quả kiểm định tự động (Validation)
- **Trạng thái**: {'✅ ĐẠT YÊU CẦU' if validation.get('passed') else '❌ CHƯA ĐẠT'}
- **Cảnh báo**:
{warnings_md}

---

### 📋 Checklist dành cho Người Quản Trị (Admin Review)
- [ ] Kiểm tra tính chính xác lịch sử / tính văn hóa dân gian.
- [ ] Kiểm tra câu từ, văn phong thuần Việt, không sai sót chính tả.
- [ ] Xác nhận bài học nhân văn ('lesson') phù hợp định hướng.
- [ ] Sẵn sàng Merge vào nhánh `{self.base_branch}` để tự động deploy lên website.
"""
