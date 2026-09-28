"""
NarrAI Social & Literary Recommender Router
Endpoints:
- GET  /feed: Retrieve personalized 3-stage hybrid recommended feed
- POST /publish: Publish a story to the literary social network
- POST /interact: Record explicit and implicit interaction signals
- GET  /post/{post_id}: Retrieve single post details and interactions
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

try:
    from db.models import get_db, User, SocialPost
    from auth import decode_access_token
    from services.cache_service import get_cache_manager
    from services.recommender_service import (
        get_feed,
        publish_post,
        record_interaction,
        get_post_details
    )
except ImportError:
    from backend.db.models import get_db, User, SocialPost
    from backend.auth import decode_access_token
    from backend.services.cache_service import get_cache_manager
    from backend.services.recommender_service import (
        get_feed,
        publish_post,
        record_interaction,
        get_post_details
    )

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)


# ==================== AUTHENTICATION DEPENDENCIES ====================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Resolves authenticated user from token or cache, backed by database."""
    if not token:
        return None

    cache_mgr = get_cache_manager()
    cached = cache_mgr.get_user_token(token)
    if cached and isinstance(cached, dict):
        user_id = cached.get("id")
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user
        return User(
            id=user_id,
            username=cached.get("username"),
            full_name=cached.get("full_name", "")
        )

    payload = decode_access_token(token)
    if not payload:
        return None

    username = payload.get("sub")
    if not username:
        return None

    user = db.query(User).filter(User.username == username).first()
    return user


async def require_current_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """Enforces authentication requirement."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu đăng nhập để thực hiện hành động này.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


# ==================== PYDANTIC SCHEMAS ====================

class PublishPostRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Tiêu đề bài đăng")
    content_snippet: str = Field(..., min_length=1, description="Trích đoạn tác phẩm")
    story_id: Optional[int] = Field(None, description="ID truyện gốc liên kết nếu có")
    genre: Optional[str] = Field("Chung", description="Thể loại văn học")
    tags: Optional[List[str]] = Field(default_factory=list, description="Danh sách nhãn")
    cover_image_url: Optional[str] = Field(None, description="URL ảnh bìa")
    dsgo_entities: Optional[List[str]] = Field(default_factory=list, description="Thực thể DSGO")
    dsgo_spaces: Optional[List[str]] = Field(default_factory=list, description="Không gian DSGO")
    concept_vector: Optional[List[float]] = Field(None, description="128-dim concept embedding")


class InteractPostRequest(BaseModel):
    post_id: int = Field(..., description="ID bài viết tương tác")
    interaction_type: str = Field(
        ...,
        description="Loại tương tác: LIKE, COMMENT, BOOKMARK, SHARE, CLICK, SCROLL_50, SCROLL_100, DWELL_TIME"
    )
    dwell_seconds: Optional[float] = Field(0.0, ge=0.0, description="Số giây dừng đọc")
    scroll_depth: Optional[int] = Field(0, ge=0, le=100, description="Độ sâu cuộn trang (%)")
    comment_text: Optional[str] = Field(None, description="Nội dung bình luận")


# ==================== ROUTE HANDLERS ====================

@router.get("/feed", summary="Lấy bảng tin đề xuất văn học thông minh 3 giai đoạn")
async def get_social_feed(
    limit: int = Query(20, ge=1, le=100, description="Số bài đăng mỗi trang"),
    offset: int = Query(0, ge=0, description="Độ dời vị trí phân trang"),
    genre: Optional[str] = Query(None, description="Bộ lọc theo thể loại"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the personalized literature feed using the 3-Stage Hybrid Recommender:
    - Stage 1: Two-Tower Cosine + Graph DSGO Traversal
    - Stage 2: Multi-Task Ranking (Cosine, Implicit Affinity, Freshness, QualityScore)
    - Stage 3: MMR Diversity (lambda=0.7) + Multi-Armed Bandit Cold-Start Exploration (15%)
    """
    user_id = current_user.id if current_user else None
    feed_data = get_feed(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
        genre=genre
    )
    return {
        "success": True,
        "data": feed_data
    }


@router.post("/publish", summary="Xuất bản tác phẩm lên mạng xã hội NarrAI", status_code=status.HTTP_201_CREATED)
async def publish_social_post(
    req: PublishPostRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Publishes a story or literary chapter to the social network with 128-dim concept vectors.
    """
    try:
        post = publish_post(
            db=db,
            user_id=current_user.id,
            title=req.title,
            content_snippet=req.content_snippet,
            story_id=req.story_id,
            genre=req.genre,
            tags=req.tags,
            cover_image_url=req.cover_image_url,
            dsgo_entities=req.dsgo_entities,
            dsgo_spaces=req.dsgo_spaces,
            concept_vector=req.concept_vector
        )
        return {
            "success": True,
            "message": "Xuất bản bài viết thành công!",
            "post_id": post.id,
            "data": {
                "id": post.id,
                "title": post.title,
                "genre": post.genre,
                "created_at": post.created_at.isoformat() if post.created_at else None
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lỗi khi xuất bản bài viết: {str(e)}"
        )


@router.post("/interact", summary="Ghi nhận tín hiệu tương tác độc giả")
async def interact_with_post(
    req: InteractPostRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Records explicit (LIKE, COMMENT) or implicit (DWELL_TIME, SCROLL_100) interactions,
    analyzes comment sentiment/entities, and dynamically updates user interest profile.
    """
    try:
        interaction, meta = record_interaction(
            db=db,
            user_id=current_user.id,
            post_id=req.post_id,
            interaction_type=req.interaction_type,
            dwell_seconds=req.dwell_seconds or 0.0,
            scroll_depth=req.scroll_depth or 0,
            comment_text=req.comment_text
        )
        return {
            "success": True,
            "message": "Ghi nhận tương tác thành công!",
            "interaction_id": interaction.id,
            "metadata": meta
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi xử lý tương tác: {str(e)}"
        )


@router.get("/post/{post_id}", summary="Lấy chi tiết bài viết và bình luận")
@router.get("/posts/{post_id}", summary="Alias lấy chi tiết bài viết")
async def get_single_post(
    post_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves single post details, increments view counter, and lists recent comments.
    """
    user_id = current_user.id if current_user else None
    details = get_post_details(db, post_id, current_user_id=user_id)
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy bài viết ID {post_id}."
        )
    return {
        "success": True,
        "data": details
    }
