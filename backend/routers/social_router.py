"""
NarrAI Social & Literary Recommender Router
Endpoints:
- GET  /feed: Retrieve personalized 3-stage hybrid recommended feed
- POST /publish: Publish a story to the literary social network
- POST /interact: Record explicit and implicit interaction signals
- GET  /post/{post_id}: Retrieve single post details and interactions
"""

import json
import math
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

try:
    from db.models import (
        get_db, User, SocialPost, PostInteraction,
        Follow, Bookmark, Notification, ContentReport, AuthorProfile
    )
    from auth import decode_access_token
    from services.cache_service import get_cache_manager
    from services.recommender_service import (
        get_feed,
        publish_post,
        record_interaction,
        get_post_details,
        export_concept_vectors,
        get_quantized_model_weights
    )
    from services.ontology import (
        HistoricalGroundingGatekeeper,
        auto_detect_narrative_mode,
        detect_commercial_ip,
        NarrativeMode
    )
except ImportError:
    from backend.db.models import (
        get_db, User, SocialPost, PostInteraction,
        Follow, Bookmark, Notification, ContentReport, AuthorProfile
    )
    from backend.auth import decode_access_token
    from backend.services.cache_service import get_cache_manager
    from backend.services.recommender_service import (
        get_feed,
        publish_post,
        record_interaction,
        get_post_details,
        export_concept_vectors,
        get_quantized_model_weights
    )
    from backend.services.ontology import (
        HistoricalGroundingGatekeeper,
        auto_detect_narrative_mode,
        detect_commercial_ip,
        NarrativeMode
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


async def require_moderator(
    current_user: User = Depends(require_current_user)
) -> User:
    moderator_usernames = {
        username.strip().casefold()
        for username in os.environ.get("NARRAI_MODERATOR_USERNAMES", "").split(",")
        if username.strip()
    }
    if current_user.username.casefold() not in moderator_usernames:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền kiểm duyệt nội dung.",
        )
    return current_user


# ==================== PYDANTIC SCHEMAS ====================

class PublishPostRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Tiêu đề bài đăng")
    content_snippet: str = Field(..., min_length=1, description="Trích đoạn tác phẩm")
    story_id: Optional[int] = Field(None, description="ID truyện gốc liên kết nếu có")
    story_text: Optional[str] = Field(None, description="Toàn văn tác phẩm để tự động lưu/cập nhật Story")
    genre: Optional[str] = Field("Chung", description="Thể loại văn học")
    tags: Optional[List[str]] = Field(default_factory=list, description="Danh sách nhãn")
    cover_image_url: Optional[str] = Field(None, description="URL ảnh bìa")
    dsgo_entities: Optional[List[str]] = Field(default_factory=list, description="Thực thể DSGO")
    dsgo_spaces: Optional[List[str]] = Field(default_factory=list, description="Không gian DSGO")
    concept_vector: Optional[List[float]] = Field(None, description="128-dim concept embedding")
    is_fanfiction: Optional[bool] = Field(None, description="Cờ đánh dấu tác phẩm fanfiction / phái sinh")
    disclaimer: Optional[str] = Field(None, description="Tuyên bố miễn trừ trách nhiệm pháp lý")


class InteractPostRequest(BaseModel):
    post_id: int = Field(..., description="ID bài viết tương tác")
    interaction_type: str = Field(
        ...,
        description="Loại tương tác: LIKE, COMMENT, BOOKMARK, SHARE, CLICK, SCROLL_50, SCROLL_100, DWELL_TIME"
    )
    dwell_seconds: Optional[float] = Field(0.0, ge=0.0, description="Số giây dừng đọc")
    scroll_depth: Optional[int] = Field(0, ge=0, le=100, description="Độ sâu cuộn trang (%)")
    comment_text: Optional[str] = Field(None, description="Nội dung bình luận")
    parent_comment_id: Optional[int] = Field(None, description="ID bình luận cha nếu là bình luận trả lời (threaded reply)")


class CreateBookmarkRequest(BaseModel):
    post_id: int = Field(..., description="ID bài viết cần lưu vào tủ sách")
    category: Optional[str] = Field("Yêu thích", description="Danh mục tủ sách: Yêu thích, Đang đọc, v.v.")
    tags: Optional[List[str]] = Field(default_factory=list, description="Thẻ nhãn cá nhân")
    notes: Optional[str] = Field(None, description="Ghi chú cá nhân")


class CreateReportRequest(BaseModel):
    post_id: Optional[int] = Field(None, description="ID bài viết bị báo cáo")
    target_user_id: Optional[int] = Field(None, description="ID người dùng bị báo cáo")
    report_reason: str = Field(..., description="Lý do báo cáo: distortion, spam, harassment, etc.")
    details: Optional[str] = Field(None, description="Chi tiết báo cáo")


class ResolveReportRequest(BaseModel):
    status: Optional[str] = Field("RESOLVED", description="Trạng thái giải quyết: RESOLVED hoặc REJECTED")
    moderator_notes: Optional[str] = Field(None, description="Ghi chú kiểm duyệt")


class UpdateAuthorProfileRequest(BaseModel):
    bio: Optional[str] = Field(None, description="Tiểu sử tác giả")
    avatar_url: Optional[str] = Field(None, description="URL ảnh đại diện")
    cover_url: Optional[str] = Field(None, description="URL ảnh bìa hồ sơ")
    genres: Optional[List[str]] = Field(None, description="Thể loại sáng tác thế mạnh")
    full_name: Optional[str] = Field(None, description="Họ và tên hiển thị")


# ==================== ROUTE HANDLERS: FEED & PUBLISH ====================

@router.get("/feed", summary="Lấy bảng tin đề xuất hoặc bảng tin người theo dõi")
async def get_social_feed(
    limit: int = Query(20, ge=1, le=100, description="Số bài đăng mỗi trang"),
    offset: int = Query(0, ge=0, description="Độ dời vị trí phân trang"),
    genre: Optional[str] = Query(None, description="Bộ lọc theo thể loại"),
    feed_type: str = Query("recommended", description="Loại feed: recommended hoặc following"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves either the personalized 3-stage recommended feed or the following feed:
    - feed_type="following": filters strictly by followed authors.
    - feed_type="recommended": 3-stage hybrid recommender (Cosine + DSGO + Freshness + Quality + MMR + Bandit).
    """
    feed_type_norm = feed_type.lower().strip()
    if feed_type_norm == "following":
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Yêu cầu đăng nhập để xem bảng tin người theo dõi."
            )
        followed_subquery = db.query(Follow.following_id).filter(
            Follow.follower_id == current_user.id
        ).subquery()

        q = db.query(SocialPost).filter(SocialPost.user_id.in_(followed_subquery))
        if genre:
            q = q.filter(SocialPost.genre == genre)

        total = q.count()
        posts = q.order_by(desc(SocialPost.created_at)).offset(offset).limit(limit).all()

        serialized = []
        for p in posts:
            author = p.author
            tags = []
            try:
                tags = json.loads(p.tags or "[]")
            except Exception:
                pass
            serialized.append({
                "id": p.id,
                "title": p.title,
                "content_snippet": p.content_snippet,
                "cover_image_url": p.cover_image_url,
                "genre": p.genre,
                "tags": tags,
                "likes_count": p.likes_count,
                "comments_count": p.comments_count,
                "views_count": p.views_count,
                "dwell_time_avg": round(p.dwell_time_avg or 0.0, 1),
                "completion_count": getattr(p, "completion_count", 0) or 0,
                "is_fanfiction": bool(p.is_fanfiction),
                "disclaimer": p.disclaimer,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "author": {
                    "id": author.id if author else p.user_id,
                    "username": author.username if author else "author",
                    "full_name": getattr(author, "full_name", "") or ""
                }
            })

        return {
            "success": True,
            "feed_type": "following",
            "data": {
                "posts": serialized,
                "total": total,
                "has_more": (offset + len(serialized)) < total
            }
        }

    # Default to 3-stage recommended feed
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
        "feed_type": "recommended",
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
    Enforces Vietnamese historical invariant validation (rejecting distortion with 422)
    and commercial IP copyright detection with fanfiction disclaimer attachment.
    """
    combined_text = f"{req.title}\n{req.content_snippet}\n{req.story_text or ''}".strip()

    # Auto-detect narrative mode
    detected_mode, _ = auto_detect_narrative_mode(combined_text, genre=req.genre or "")

    # Validate Vietnamese historical invariants
    is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
        combined_text,
        mode=detected_mode
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tác phẩm vi phạm chuẩn mực lịch sử Việt Nam và bị từ chối xuất bản: {'; '.join(violations)}"
        )

    # Detect commercial IP & fanfiction copyright
    ip_result = detect_commercial_ip(combined_text)
    is_fanfic = bool(req.is_fanfiction if req.is_fanfiction is not None else ip_result.get("has_commercial_ip", False))
    disclaimer = req.disclaimer or (ip_result.get("fanfiction_disclaimer", "") if is_fanfic else None)

    tags = list(req.tags or [])
    if is_fanfic and "Fanfiction" not in tags:
        tags.append("Fanfiction")

    try:
        import re as _re
        clean_title = _re.sub(r'<[^>]+>', '', req.title or '').strip()
        clean_snippet = _re.sub(r'<[^>]+>', '', req.content_snippet or '').strip()
        clean_story_text = _re.sub(r'<[^>]+>', '', req.story_text or '').strip() if req.story_text else None

        post = publish_post(
            db=db,
            user_id=current_user.id,
            title=clean_title,
            content_snippet=clean_snippet,
            story_id=req.story_id,
            story_text=clean_story_text,
            genre=req.genre,
            tags=tags,
            cover_image_url=req.cover_image_url,
            dsgo_entities=req.dsgo_entities,
            dsgo_spaces=req.dsgo_spaces,
            concept_vector=req.concept_vector,
            is_fanfiction=is_fanfic,
            disclaimer=disclaimer
        )
        return {
            "success": True,
            "message": "Xuất bản bài viết thành công!",
            "post_id": post.id,
            "data": {
                "id": post.id,
                "title": post.title,
                "genre": post.genre,
                "is_fanfiction": post.is_fanfiction,
                "disclaimer": post.disclaimer,
                "created_at": post.created_at.isoformat() if post.created_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lỗi khi xuất bản bài viết: {str(e)}"
        )


# ==================== ROUTE HANDLERS: INTERACTIONS & THREADED COMMENTS ====================

@router.post("/interact", summary="Ghi nhận tín hiệu tương tác độc giả & threaded comments")
async def interact_with_post(
    req: InteractPostRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Records explicit (LIKE, COMMENT) or implicit (DWELL_TIME, SCROLL_100) interactions.
    Supports hierarchical comment replies via parent_comment_id and auto-generates notifications.
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

        itype = req.interaction_type.upper().strip()

        # Handle threaded comment hierarchy
        if itype == "COMMENT" and req.parent_comment_id:
            parent_comment = db.query(PostInteraction).filter(
                PostInteraction.id == req.parent_comment_id,
                PostInteraction.post_id == req.post_id
            ).first()
            if parent_comment:
                interaction.parent_comment_id = req.parent_comment_id
                db.commit()
                meta["parent_comment_id"] = req.parent_comment_id

                # Notify parent comment author if not current user
                if parent_comment.user_id != current_user.id:
                    reply_notif = Notification(
                        recipient_id=parent_comment.user_id,
                        sender_id=current_user.id,
                        notification_type="COMMENT",
                        post_id=req.post_id,
                        comment_id=interaction.id,
                        content=f"{current_user.full_name or current_user.username} đã trả lời bình luận của bạn.",
                        created_at=datetime.utcnow()
                    )
                    db.add(reply_notif)
                    db.commit()

        # Notify post author on LIKE or root COMMENT
        post = db.query(SocialPost).filter(SocialPost.id == req.post_id).first()
        if post and post.user_id != current_user.id:
            if itype == "LIKE":
                like_notif = Notification(
                    recipient_id=post.user_id,
                    sender_id=current_user.id,
                    notification_type="LIKE",
                    post_id=req.post_id,
                    content=f"{current_user.full_name or current_user.username} đã thích tác phẩm của bạn.",
                    created_at=datetime.utcnow()
                )
                db.add(like_notif)
                db.commit()
            elif itype == "COMMENT" and not req.parent_comment_id:
                comment_notif = Notification(
                    recipient_id=post.user_id,
                    sender_id=current_user.id,
                    notification_type="COMMENT",
                    post_id=req.post_id,
                    comment_id=interaction.id,
                    content=f"{current_user.full_name or current_user.username} đã bình luận bài viết của bạn.",
                    created_at=datetime.utcnow()
                )
                db.add(comment_notif)
                db.commit()

        return {
            "success": True,
            "message": "Ghi nhận tương tác thành công!",
            "interaction_id": interaction.id,
            "parent_comment_id": getattr(interaction, "parent_comment_id", None),
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


@router.get("/post/{post_id}", summary="Lấy chi tiết bài viết và bình luận phân cấp")
@router.get("/posts/{post_id}", summary="Alias lấy chi tiết bài viết")
async def get_single_post(
    post_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves single post details, increments view counter, and lists recent comments
    including parent_comment_id for nested comment threads.
    """
    user_id = current_user.id if current_user else None
    details = get_post_details(db, post_id, current_user_id=user_id)
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy bài viết ID {post_id}."
        )

    # Enrich comments with parent_comment_id
    if "comments" in details and details["comments"]:
        comment_ids = [c["id"] for c in details["comments"]]
        if comment_ids:
            parent_map = dict(
                db.query(PostInteraction.id, PostInteraction.parent_comment_id)
                .filter(PostInteraction.id.in_(comment_ids))
                .all()
            )
            for c in details["comments"]:
                c["parent_comment_id"] = parent_map.get(c["id"])

    return {
        "success": True,
        "data": details
    }


# ==================== ROUTE HANDLERS: FOLLOW / UNFOLLOW ====================

@router.post("/follow/{user_id}", summary="Theo dõi tác giả", status_code=status.HTTP_200_OK)
async def follow_author(
    user_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Reader follows an author. Enforces self-follow guard, uniqueness,
    updates AuthorProfile follower counts, and generates notification.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn không thể tự theo dõi chính mình."
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng này."
        )

    existing = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()
    if existing:
        return {
            "success": True,
            "message": "Bạn đã theo dõi tác giả này rồi.",
            "following_id": user_id,
            "already_following": True
        }

    follow = Follow(
        follower_id=current_user.id,
        following_id=user_id,
        created_at=datetime.utcnow()
    )
    db.add(follow)

    # Sync author profile counts if profiles exist
    t_prof = db.query(AuthorProfile).filter(AuthorProfile.user_id == user_id).first()
    if t_prof:
        t_prof.followers_count = (t_prof.followers_count or 0) + 1
    c_prof = db.query(AuthorProfile).filter(AuthorProfile.user_id == current_user.id).first()
    if c_prof:
        c_prof.following_count = (c_prof.following_count or 0) + 1

    # Dispatch follow notification
    notif = Notification(
        recipient_id=user_id,
        sender_id=current_user.id,
        notification_type="FOLLOW",
        content=f"{current_user.full_name or current_user.username} đã bắt đầu theo dõi bạn.",
        created_at=datetime.utcnow()
    )
    db.add(notif)
    db.commit()

    return {
        "success": True,
        "message": f"Theo dõi tác giả {target_user.full_name or target_user.username} thành công!",
        "following_id": user_id
    }


@router.post("/unfollow/{user_id}", summary="Bỏ theo dõi tác giả", status_code=status.HTTP_200_OK)
async def unfollow_author(
    user_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Reader unfollows an author. Updates AuthorProfile follower counters.
    """
    follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()
    if not follow:
        return {
            "success": True,
            "message": "Bạn chưa theo dõi tác giả này.",
            "unfollowed_id": user_id,
            "already_unfollowed": True
        }

    db.delete(follow)

    t_prof = db.query(AuthorProfile).filter(AuthorProfile.user_id == user_id).first()
    if t_prof and t_prof.followers_count > 0:
        t_prof.followers_count -= 1
    c_prof = db.query(AuthorProfile).filter(AuthorProfile.user_id == current_user.id).first()
    if c_prof and c_prof.following_count > 0:
        c_prof.following_count -= 1

    db.commit()
    return {
        "success": True,
        "message": "Bỏ theo dõi tác giả thành công!",
        "unfollowed_id": user_id
    }


# ==================== ROUTE HANDLERS: BOOKMARKS / PERSONAL LIBRARY ====================

@router.post("/bookmark", summary="Lưu tác phẩm vào tủ sách cá nhân", status_code=status.HTTP_200_OK)
async def create_or_update_bookmark(
    req: CreateBookmarkRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves or updates a bookmark in user's personal library.
    """
    post = db.query(SocialPost).filter(SocialPost.id == req.post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy bài viết."
        )

    bm = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.post_id == req.post_id
    ).first()

    tags_json = json.dumps(req.tags or [])
    if bm:
        bm.category = req.category or "Yêu thích"
        bm.tags = tags_json
        bm.notes = req.notes
        db.commit()
        db.refresh(bm)
        return {
            "success": True,
            "message": "Đã cập nhật dấu trang thành công!",
            "bookmark_id": bm.id,
            "category": bm.category
        }

    bm = Bookmark(
        user_id=current_user.id,
        post_id=req.post_id,
        category=req.category or "Yêu thích",
        tags=tags_json,
        notes=req.notes,
        created_at=datetime.utcnow()
    )
    db.add(bm)
    db.commit()
    db.refresh(bm)

    return {
        "success": True,
        "message": "Đã lưu tác phẩm vào tủ sách thành công!",
        "bookmark_id": bm.id,
        "category": bm.category
    }


@router.delete("/bookmark/{post_id}", summary="Xóa tác phẩm khỏi tủ sách cá nhân")
async def delete_bookmark(
    post_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Removes a bookmarked post from user's personal library.
    """
    deleted = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.post_id == post_id
    ).delete()
    db.commit()

    return {
        "success": True,
        "message": "Đã xóa tác phẩm khỏi tủ sách.",
        "post_id": post_id,
        "deleted": deleted > 0
    }


@router.get("/bookmarks", summary="Lấy danh sách tủ sách cá nhân")
async def get_user_bookmarks(
    category: Optional[str] = Query(None, description="Lọc theo danh mục: Yêu thích, Đang đọc, v.v."),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves user's personal library bookmarks with optional category filter.
    """
    q = db.query(Bookmark).filter(Bookmark.user_id == current_user.id)
    if category:
        q = q.filter(Bookmark.category == category)

    total = q.count()
    bookmarks = q.order_by(desc(Bookmark.created_at)).offset(offset).limit(limit).all()

    result = []
    for b in bookmarks:
        post = b.post or db.query(SocialPost).filter(SocialPost.id == b.post_id).first()
        post_data = None
        if post:
            p_author = post.author
            post_data = {
                "id": post.id,
                "title": post.title,
                "content_snippet": post.content_snippet,
                "cover_image_url": post.cover_image_url,
                "genre": post.genre,
                "likes_count": post.likes_count,
                "comments_count": post.comments_count,
                "views_count": post.views_count,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "author": {
                    "id": p_author.id if p_author else post.user_id,
                    "username": p_author.username if p_author else "author",
                    "full_name": getattr(p_author, "full_name", "") or ""
                }
            }
        b_tags = []
        try:
            b_tags = json.loads(b.tags or "[]")
        except Exception:
            pass
        result.append({
            "id": b.id,
            "user_id": b.user_id,
            "post_id": b.post_id,
            "category": b.category,
            "tags": b_tags,
            "notes": b.notes,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "post": post_data
        })

    return {
        "success": True,
        "total": total,
        "category": category,
        "data": result
    }


# ==================== ROUTE HANDLERS: NOTIFICATIONS ====================

@router.get("/notifications", summary="Lấy danh sách thông báo người dùng")
async def get_user_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False, description="Chỉ lấy thông báo chưa đọc"),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns user notifications and total unread count.
    """
    unread_count = db.query(Notification).filter(
        Notification.recipient_id == current_user.id,
        Notification.is_read == False
    ).count()

    q = db.query(Notification).filter(Notification.recipient_id == current_user.id)
    if unread_only:
        q = q.filter(Notification.is_read == False)

    notifs = q.order_by(desc(Notification.created_at)).offset(offset).limit(limit).all()

    items = []
    for n in notifs:
        sender = n.sender or db.query(User).filter(User.id == n.sender_id).first()
        items.append({
            "id": n.id,
            "recipient_id": n.recipient_id,
            "sender_id": n.sender_id,
            "sender": {
                "id": sender.id if sender else n.sender_id,
                "username": sender.username if sender else "user",
                "full_name": getattr(sender, "full_name", "") or ""
            },
            "notification_type": n.notification_type,
            "post_id": n.post_id,
            "comment_id": n.comment_id,
            "conversation_id": n.conversation_id,
            "content": n.content,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None
        })

    return {
        "success": True,
        "unread_count": unread_count,
        "data": items
    }


@router.post("/notifications/{notification_id}/read", summary="Đánh dấu thông báo đã đọc")
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Marks a single notification as read.
    """
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông báo."
        )

    notif.is_read = True
    db.commit()

    return {
        "success": True,
        "message": "Đã đánh dấu thông báo đã đọc.",
        "notification_id": notification_id
    }


@router.post("/notifications/read-all", summary="Đánh dấu tất cả thông báo đã đọc")
async def mark_all_notifications_as_read(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Marks all notifications for current user as read.
    """
    updated_count = db.query(Notification).filter(
        Notification.recipient_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()

    return {
        "success": True,
        "message": "Đã đánh dấu tất cả thông báo đã đọc.",
        "updated_count": updated_count
    }


# ==================== ROUTE HANDLERS: CONTENT REPORTS ====================

@router.post("/report", summary="Báo cáo nội dung vi phạm", status_code=status.HTTP_201_CREATED)
async def submit_content_report(
    req: CreateReportRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a content moderation report for distortion, spam, harassment, etc.
    """
    if not req.post_id and not req.target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phải chỉ định post_id hoặc target_user_id để báo cáo."
        )

    report = ContentReport(
        reporter_id=current_user.id,
        post_id=req.post_id,
        target_user_id=req.target_user_id,
        report_reason=req.report_reason,
        details=req.details,
        status="PENDING",
        created_at=datetime.utcnow()
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "success": True,
        "message": "Báo cáo nội dung đã được tiếp nhận và đang chờ xử lý.",
        "report_id": report.id,
        "status": report.status
    }


@router.get("/reports", summary="Danh sách báo cáo nội dung (Admin/Mod)")
async def list_content_reports(
    status_filter: Optional[str] = Query(None, alias="status", description="Lọc theo trạng thái: PENDING, RESOLVED, REJECTED"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_moderator),
    db: Session = Depends(get_db)
):
    """
    Lists content moderation reports.
    """
    q = db.query(ContentReport)
    if status_filter:
        q = q.filter(ContentReport.status == status_filter.upper())

    total = q.count()
    reports = q.order_by(desc(ContentReport.created_at)).offset(offset).limit(limit).all()

    items = []
    for r in reports:
        items.append({
            "id": r.id,
            "reporter_id": r.reporter_id,
            "post_id": r.post_id,
            "target_user_id": r.target_user_id,
            "report_reason": r.report_reason,
            "details": r.details,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    return {
        "success": True,
        "total": total,
        "data": items
    }


@router.post("/report/{report_id}/resolve", summary="Giải quyết báo cáo vi phạm")
async def resolve_content_report(
    report_id: int,
    req: Optional[ResolveReportRequest] = None,
    current_user: User = Depends(require_moderator),
    db: Session = Depends(get_db)
):
    """
    Transitions report status to RESOLVED or REJECTED.
    """
    report = db.query(ContentReport).filter(ContentReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy báo cáo."
        )

    new_status = (req.status if req and req.status else "RESOLVED").upper()
    if new_status not in {"RESOLVED", "REJECTED"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Trạng thái báo cáo phải là RESOLVED hoặc REJECTED.",
        )
    report.status = new_status
    db.commit()

    return {
        "success": True,
        "message": f"Báo cáo ID {report_id} đã được cập nhật thành {new_status}.",
        "report_id": report_id,
        "status": report.status
    }


# ==================== ROUTE HANDLERS: AUTHOR PROFILES ====================

@router.get("/profile/{user_id}", summary="Lấy thông tin hồ sơ tác giả và tác phẩm")
async def get_author_profile(
    user_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves public author profile, bio, follower counts, total likes, and published works.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng."
        )

    profile = db.query(AuthorProfile).filter(AuthorProfile.user_id == user_id).first()
    if not profile:
        profile = AuthorProfile(user_id=user_id, bio="")
        db.add(profile)
        db.commit()
        db.refresh(profile)

    # Realtime sync stats
    followers_count = db.query(Follow).filter(Follow.following_id == user_id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user_id).count()
    works_count = db.query(SocialPost).filter(SocialPost.user_id == user_id).count()
    total_likes = db.query(func.coalesce(func.sum(SocialPost.likes_count), 0)).filter(
        SocialPost.user_id == user_id
    ).scalar() or 0

    profile.followers_count = followers_count
    profile.following_count = following_count
    profile.works_count = works_count
    profile.total_likes = int(total_likes)
    db.commit()

    is_following = False
    if current_user:
        is_following = db.query(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        ).first() is not None

    works = db.query(SocialPost).filter(
        SocialPost.user_id == user_id
    ).order_by(desc(SocialPost.created_at)).limit(30).all()

    serialized_works = []
    for p in works:
        w_tags = []
        try:
            w_tags = json.loads(p.tags or "[]")
        except Exception:
            pass
        serialized_works.append({
            "id": p.id,
            "title": p.title,
            "content_snippet": p.content_snippet,
            "cover_image_url": p.cover_image_url,
            "genre": p.genre,
            "tags": w_tags,
            "likes_count": p.likes_count,
            "comments_count": p.comments_count,
            "views_count": p.views_count,
            "completion_count": getattr(p, "completion_count", 0) or 0,
            "created_at": p.created_at.isoformat() if p.created_at else None
        })

    genres_list = []
    try:
        genres_list = json.loads(profile.genres or "[]")
    except Exception:
        pass

    return {
        "success": True,
        "data": {
            "user_id": user.id,
            "username": user.username,
            "full_name": user.full_name or "",
            "bio": profile.bio or "",
            "avatar_url": profile.avatar_url,
            "cover_url": profile.cover_url,
            "genres": genres_list,
            "followers_count": followers_count,
            "following_count": following_count,
            "works_count": works_count,
            "total_likes": int(total_likes),
            "is_following": is_following,
            "works": serialized_works
        }
    }


@router.put("/profile", summary="Cập nhật hồ sơ tác giả cá nhân")
async def update_my_author_profile(
    req: UpdateAuthorProfileRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates authenticated user's bio, avatar, cover, genres, or display full name.
    """
    profile = db.query(AuthorProfile).filter(AuthorProfile.user_id == current_user.id).first()
    if not profile:
        profile = AuthorProfile(user_id=current_user.id)
        db.add(profile)

    if req.bio is not None:
        profile.bio = req.bio
    if req.avatar_url is not None:
        profile.avatar_url = req.avatar_url
    if req.cover_url is not None:
        profile.cover_url = req.cover_url
    if req.genres is not None:
        profile.genres = json.dumps(req.genres)
    if req.full_name is not None:
        current_user.full_name = req.full_name

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    genres_list = []
    try:
        genres_list = json.loads(profile.genres or "[]")
    except Exception:
        pass

    return {
        "success": True,
        "message": "Cập nhật hồ sơ tác giả thành công!",
        "data": {
            "user_id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name or "",
            "bio": profile.bio or "",
            "avatar_url": profile.avatar_url,
            "cover_url": profile.cover_url,
            "genres": genres_list
        }
    }


# ==================== ROUTE HANDLERS: TRENDING LEADERBOARD ====================

@router.get("/trending", summary="Bảng xếp hạng thịnh hành theo vận tốc suy giảm thời gian")
async def get_trending_leaderboard(
    period: str = Query("weekly", description="Chu kỳ: weekly (7 ngày) hoặc monthly (30 ngày)"),
    genre: Optional[str] = Query(None, description="Lọc theo thể loại"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Computes time-decayed velocity score:
    Score = (3*likes + 5*comments + 0.5*views + 4*completions) / ((age_in_hours + 2) ** 1.4)
    Filters within 7 days for weekly or 30 days for monthly, ordered by velocity score descending.
    """
    period_norm = period.lower().strip()
    if period_norm not in ("weekly", "monthly"):
        period_norm = "weekly"

    now = datetime.utcnow()
    days = 7 if period_norm == "weekly" else 30
    cutoff = now - timedelta(days=days)

    q = db.query(SocialPost).filter(SocialPost.created_at >= cutoff)
    if genre:
        q = q.filter(SocialPost.genre == genre)

    candidates = q.all()

    scored_posts = []
    for p in candidates:
        created_time = p.created_at or now
        age_hours = max(0.0, (now - created_time).total_seconds() / 3600.0)

        likes = float(p.likes_count or 0)
        comments = float(p.comments_count or 0)
        views = float(p.views_count or 0)
        completions = float(getattr(p, "completion_count", 0) or 0)

        numerator = 3.0 * likes + 5.0 * comments + 0.5 * views + 4.0 * completions
        denominator = (age_hours + 2.0) ** 1.4
        score = numerator / denominator if denominator > 0 else 0.0

        scored_posts.append((score, p))

    scored_posts.sort(key=lambda x: x[0], reverse=True)
    total = len(scored_posts)
    paged = scored_posts[offset : offset + limit]

    result = []
    for rank_idx, (score, p) in enumerate(paged, start=offset + 1):
        author = p.author
        tags = []
        try:
            tags = json.loads(p.tags or "[]")
        except Exception:
            pass
        result.append({
            "rank": rank_idx,
            "trending_score": round(score, 4),
            "id": p.id,
            "title": p.title,
            "content_snippet": p.content_snippet,
            "cover_image_url": p.cover_image_url,
            "genre": p.genre,
            "tags": tags,
            "likes_count": p.likes_count,
            "comments_count": p.comments_count,
            "views_count": p.views_count,
            "completion_count": getattr(p, "completion_count", 0) or 0,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "author": {
                "id": author.id if author else p.user_id,
                "username": author.username if author else "author",
                "full_name": getattr(author, "full_name", "") or ""
            }
        })

    return {
        "success": True,
        "period": period_norm,
        "cutoff_days": days,
        "total": total,
        "data": result
    }


# ==================== RECOMMENDER & TF.JS EXPORT ROUTER (FEATURE 26) ====================

recommender_router = APIRouter(prefix="/api/recommender", tags=["Recommender"])


@recommender_router.get("/export-vectors")
def export_recommender_vectors(
    limit: int = Query(100, ge=1, le=500, description="Số lượng vector tối đa cần trích xuất (1-500)"),
    since: Optional[str] = Query(None, description="Thời điểm ISO mốc delta synchronization"),
    format: str = Query("json", description="Định dạng trả về ('json' hoặc 'binary')"),
    db: Session = Depends(get_db)
):
    """
    Trích xuất danh sách concept vector 128 chiều đã chuẩn hóa L2 của các bài đăng
    cùng metadata tương ứng phục vụ on-device TensorFlow.js re-ranking và offline caching.
    """
    return export_concept_vectors(db=db, limit=limit, since=since, format=format)


@recommender_router.get("/model-weights")
def get_recommender_model_weights(
    format: str = Query("json", description="Định dạng trọng số neural ('json' hoặc 'binary')")
):
    """
    Xuất cấu trúc mô hình mạng nơ-ron và trọng số đã lượng tử hóa int8 (~2MB buffer / JSON)
    cho client TensorFlow.js suy luận trực tiếp trên trình duyệt.
    """
    return get_quantized_model_weights(format=format)


# Also mount directly on social router for convenience (/api/social/export-vectors and /api/social/model-weights)
@router.get("/export-vectors")
def social_export_vectors(
    limit: int = Query(100, ge=1, le=500),
    since: Optional[str] = Query(None),
    format: str = Query("json"),
    db: Session = Depends(get_db)
):
    return export_concept_vectors(db=db, limit=limit, since=since, format=format)


@router.get("/model-weights")
def social_model_weights(
    format: str = Query("json")
):
    return get_quantized_model_weights(format=format)

