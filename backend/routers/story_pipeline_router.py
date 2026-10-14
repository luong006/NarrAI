from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

from db.models import User
from auth import decode_access_token
from services.story_pipeline_manager import StoryPipelineManager

logger = logging.getLogger("narrai.story_pipeline_router")

router = APIRouter(tags=["AI Story Pipeline"])
public_story_router = APIRouter(tags=["Published Stories"])

# Singleton manager instance
_manager: Optional[StoryPipelineManager] = None

def get_pipeline_manager() -> StoryPipelineManager:
    global _manager
    if _manager is None:
        _manager = StoryPipelineManager()
    return _manager


# ==================== PYDANTIC SCHEMAS ====================

class AddStoryPromptRequest(BaseModel):
    id: Optional[str] = Field(None, description="Tùy chọn ID/Slug, nếu bỏ trống hệ thống tự tạo")
    title: str = Field(..., min_length=2, max_length=200, description="Tiêu đề truyện hoặc nhân vật")
    topic: Optional[str] = Field("Lịch sử & Văn hóa Việt Nam", description="Chủ đề truyện")
    category: Optional[str] = Field("Lịch sử Việt Nam", description="Danh mục phân loại")
    genre: Optional[List[str]] = Field(default_factory=lambda: ["Lịch sử", "Văn hóa"], description="Thể loại truyện")
    language: Optional[str] = Field("vi", description="Ngôn ngữ biên soạn")
    sourceLanguages: Optional[List[str]] = Field(default_factory=lambda: ["vi", "en"], description="Ngôn ngữ nguồn tham khảo")

class BatchAddPromptRequest(BaseModel):
    items: List[AddStoryPromptRequest]

class UpdateStoryPromptRequest(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None
    category: Optional[str] = None
    genre: Optional[List[str]] = None
    language: Optional[str] = None
    sourceLanguages: Optional[List[str]] = None
    status: Optional[str] = None

class RunPipelineRequest(BaseModel):
    story_id: Optional[str] = Field(None, description="Nếu chỉ định, chạy riêng đề bài này. Nếu không, chạy các mục pending theo limit.")
    limit: Optional[int] = Field(3, ge=1, le=10, description="Số lượng đề bài tối đa xử lý trong đợt")


# ==================== PIPELINE ADMIN ENDPOINTS ====================

@router.get("/queue")
async def get_queue_list(
    mgr: StoryPipelineManager = Depends(get_pipeline_manager)
):
    """
    Lấy danh sách tất cả các đề bài trong hàng đợi queue.json kèm thông số tổng quan.
    """
    try:
        overview = mgr.get_overview()
        return {
            "status": "success",
            "data": overview
        }
    except Exception as e:
        logger.error(f"Error fetching queue: {e}")
        raise HTTPException(status_code=500, detail=f"Không thể đọc hàng đợi: {str(e)}")

@router.post("/queue")
async def add_story_to_queue(
    payload: AddStoryPromptRequest,
    mgr: StoryPipelineManager = Depends(get_pipeline_manager)
):
    """
    Thêm một đề bài mới vào hàng đợi biên soạn.
    """
    try:
        entry = mgr.add_story(payload.dict())
        return {
            "status": "success",
            "message": f"Đã thêm '{entry['title']}' vào hàng đợi.",
            "data": entry
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        logger.error(f"Error adding story to queue: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi thêm đề bài: {str(e)}")

@router.post("/queue/batch")
async def batch_add_stories_to_queue(
    payload: BatchAddPromptRequest,
    mgr: StoryPipelineManager = Depends(get_pipeline_manager)
):
    """
    Nhập hàng loạt nhiều đề bài vào hàng đợi cùng lúc.
    """
    try:
        items = [item.dict() for item in payload.items]
        res = mgr.batch_add_stories(items)
        return {
            "status": "success",
            "data": res
        }
    except Exception as e:
        logger.error(f"Error batch adding to queue: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi nhập hàng loạt: {str(e)}")

@router.patch("/queue/{story_id}")
async def update_story_in_queue(
    story_id: str,
    payload: UpdateStoryPromptRequest,
    mgr: StoryPipelineManager = Depends(get_pipeline_manager)
):
    """
    Chỉnh sửa thông tin đề bài trong hàng đợi.
    """
    try:
        updates = {k: v for k, v in payload.dict().items() if v is not None}
        updated = mgr.update_story(story_id, updates)
        return {
            "status": "success",
            "message": f"Đã cập nhật đề bài '{story_id}'.",
            "data": updated
        }
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as e:
        logger.error(f"Error updating story {story_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật đề bài: {str(e)}")

@router.delete("/queue/{story_id}")
async def delete_story_from_queue(
    story_id: str,
    mgr: StoryPipelineManager = Depends(get_pipeline_manager)
):
    """
    Xóa đề bài khỏi hàng đợi.
    """
    try:
        success = mgr.delete_story(story_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy đề bài '{story_id}'")
        return {
            "status": "success",
            "message": f"Đã xóa đề bài '{story_id}' khỏi hàng đợi."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting story {story_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa: {str(e)}")

@router.post("/run")
async def run_pipeline(
    payload: RunPipelineRequest = Body(...),
    mgr: StoryPipelineManager = Depends(get_pipeline_manager)
):
    """
    Chạy pipeline: Thu thập tư liệu Wikipedia -> Claude AI biên soạn -> 5-Layer Quality Check -> Tạo GitHub PR.
    """
    try:
        if payload.story_id:
            res = await mgr.run_single_story(payload.story_id)
            return {
                "status": "success" if res.get("success") else "failed",
                "data": res
            }
        else:
            limit = payload.limit or 3
            res = await mgr.run_batch_pipeline(limit=limit)
            return {
                "status": "success",
                "data": res
            }
    except Exception as e:
        logger.error(f"Error executing pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi thực thi pipeline: {str(e)}")

@router.get("/jobs")
async def get_pipeline_jobs_overview(
    mgr: StoryPipelineManager = Depends(get_pipeline_manager)
):
    """
    Lấy tổng quan tiến độ xử lý và logs hệ thống.
    """
    try:
        overview = mgr.get_overview()
        return {
            "status": "success",
            "overview": overview,
            "recentLogs": mgr.pipeline_logs[-50:]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{story_id}")
async def get_single_job_status(
    story_id: str,
    mgr: StoryPipelineManager = Depends(get_pipeline_manager)
):
    """
    Xem chi tiết trạng thái và lịch sử logs của một đề bài cụ thể.
    """
    queue = mgr.get_queue()
    target = next((s for s in queue if s.get("id") == story_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy đề bài '{story_id}'")

    story_logs = [l for l in mgr.pipeline_logs if l.get("storyId") == story_id]
    story_preview = mgr.get_story_preview(story_id)

    return {
        "status": "success",
        "story": target,
        "logs": story_logs,
        "preview": story_preview
    }

@router.get("/pull-requests")
async def get_pull_requests(
    mgr: StoryPipelineManager = Depends(get_pipeline_manager)
):
    """
    Lấy danh sách các Pull Request đã tạo và kiểm tra trạng thái thực tế từ GitHub API.
    """
    try:
        prs = await mgr.get_pull_requests_list()
        return {
            "status": "success",
            "count": len(prs),
            "data": prs
        }
    except Exception as e:
        logger.error(f"Error fetching PRs: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi truy vấn Pull Requests: {str(e)}")

@router.post("/validate/{story_id}")
async def revalidate_story(
    story_id: str,
    mgr: StoryPipelineManager = Depends(get_pipeline_manager)
):
    """
    Chạy lại bộ kiểm định 5 lớp (Validation) cho một truyện đã biên soạn.
    """
    story = mgr.get_story_preview(story_id)
    if not story:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy bản thảo truyện '{story_id}' để kiểm tra.")

    val_res = mgr.validator_service.validate_story(story)
    return {
        "status": "success",
        "storyId": story_id,
        "title": story.get("title"),
        "validation": val_res
    }

@router.get("/preview/{story_id}")
async def preview_story(
    story_id: str,
    mgr: StoryPipelineManager = Depends(get_pipeline_manager)
):
    """
    Xem trước toàn bộ nội dung JSON, văn phong, bài học và nguồn tư liệu của truyện.
    """
    story = mgr.get_story_preview(story_id)
    if not story:
        raise HTTPException(status_code=404, detail=f"Chưa có bản thảo cho truyện '{story_id}'")

    return {
        "status": "success",
        "data": story
    }


# ==================== PUBLIC PUBLISHED STORIES ENDPOINTS ====================

@public_story_router.get("/published")
async def list_published_stories(
    category: Optional[str] = None,
    mgr: StoryPipelineManager = Depends(get_pipeline_manager)
):
    """
    Danh sách các tác phẩm truyện lịch sử & truyền thuyết đã được biên soạn và kiểm định sẵn sàng cho độc giả.
    """
    try:
        stories = mgr.get_published_stories()
        if category:
            stories = [s for s in stories if s.get("category") == category]
        return {
            "status": "success",
            "count": len(stories),
            "data": stories
        }
    except Exception as e:
        logger.error(f"Error fetching published stories: {e}")
        raise HTTPException(status_code=500, detail=str(e))
