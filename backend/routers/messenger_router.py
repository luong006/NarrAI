"""
NarrAI Open Messenger Router
Endpoints:
- GET  /users: Search user directory across all users
- GET  /conversations: List user's conversations
- POST /conversations: Idempotent get or create 1-1 conversation
- GET  /conversations/{id}/messages: Fetch message history and mark as read
- POST /conversations/{id}/messages: Send message in conversation
- GET  /unread-count: Aggregate total unread messages count
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, root_validator
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

try:
    from db.models import get_db, User, Conversation
    from auth import decode_access_token
    from services.cache_service import get_cache_manager
    from services.messenger_service import (
        search_users,
        get_or_create_conversation,
        send_message,
        get_conversation_messages,
        list_conversations,
        get_total_unread_count
    )
except ImportError:
    from backend.db.models import get_db, User, Conversation
    from backend.auth import decode_access_token
    from backend.services.cache_service import get_cache_manager
    from backend.services.messenger_service import (
        search_users,
        get_or_create_conversation,
        send_message,
        get_conversation_messages,
        list_conversations,
        get_total_unread_count
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
            detail="Yêu cầu đăng nhập để truy cập hộp thoại Messenger.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


# ==================== PYDANTIC SCHEMAS ====================

class CreateConversationRequest(BaseModel):
    target_user_id: Optional[int] = Field(None, description="ID người dùng muốn trò chuyện")
    user_id: Optional[int] = Field(None, description="Alias cho target_user_id")

    @property
    def recipient_id(self) -> int:
        res = self.target_user_id or self.user_id
        if not res:
            raise ValueError("Cần cung cấp target_user_id hoặc user_id.")
        return res


class SendMessageRequest(BaseModel):
    message_text: Optional[str] = Field(None, min_length=1, description="Nội dung tin nhắn")
    content: Optional[str] = Field(None, description="Alias cho message_text")
    text: Optional[str] = Field(None, description="Alias cho message_text")

    @property
    def resolved_text(self) -> str:
        res = self.message_text or self.content or self.text
        if not res or not res.strip():
            raise ValueError("Nội dung tin nhắn không được để trống.")
        return res.strip()


# ==================== ROUTE HANDLERS ====================

@router.get("/users", summary="Tìm kiếm người dùng trong danh bạ toàn hệ thống")
@router.get("/users/search", summary="Alias tìm kiếm người dùng")
async def search_directory_users(
    q: str = Query("", description="Từ khóa tìm kiếm (username hoặc họ tên)"),
    limit: int = Query(20, ge=1, le=100, description="Giới hạn số kết quả"),
    offset: int = Query(0, ge=0, description="Độ dời phân trang"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Searches across ALL registered users in the platform by username or full name.
    """
    my_id = current_user.id if current_user else None
    results = search_users(
        db=db,
        query=q,
        current_user_id=my_id,
        limit=limit,
        offset=offset
    )
    return {
        "success": True,
        "query": q,
        "count": len(results),
        "data": results
    }


@router.get("/conversations", summary="Lấy danh sách các cuộc hội thoại của tôi")
async def get_my_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the user's active conversations sorted by updated_at descending,
    with partner profile, last message snippet, and unread count.
    """
    convs = list_conversations(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    return {
        "success": True,
        "data": convs
    }


@router.post("/conversations", summary="Tạo mới hoặc mở lại cuộc trò chuyện 1-1")
async def create_or_open_conversation(
    req: CreateConversationRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Idempotent 1-1 conversation management.
    Opens existing conversation or creates a new one between current user and target user.
    """
    try:
        recipient_id = req.recipient_id
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))

    if recipient_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể tạo cuộc trò chuyện với chính mình."
        )

    try:
        conv, created = get_or_create_conversation(
            db=db,
            user_id_1=current_user.id,
            user_id_2=recipient_id
        )
        return {
            "success": True,
            "created": created,
            "conversation_id": conv.id,
            "data": {
                "id": conv.id,
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None
            }
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khởi tạo cuộc trò chuyện: {str(e)}"
        )


@router.get("/conversations/{id}/messages", summary="Tải lịch sử tin nhắn trong hội thoại")
async def get_messages(
    id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches message history and automatically marks incoming messages as read,
    resetting the current user's unread counter in this conversation.
    """
    try:
        messages_data = get_conversation_messages(
            db=db,
            conversation_id=id,
            current_user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        return {
            "success": True,
            "data": messages_data
        }
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe)
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )


@router.post("/conversations/{id}/messages", summary="Gửi tin nhắn mới vào hội thoại")
async def post_message(
    id: int,
    req: SendMessageRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Sends a message in conversation, persists to SQLite, and updates unread count for recipient.
    """
    try:
        text = req.resolved_text
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))

    try:
        msg = send_message(
            db=db,
            conversation_id=id,
            sender_id=current_user.id,
            message_text=text
        )
        return {
            "success": True,
            "message_id": msg.id,
            "data": {
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "sender_id": msg.sender_id,
                "message_text": msg.message_text,
                "is_read": msg.is_read,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
        }
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe)
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi gửi tin nhắn: {str(e)}"
        )


@router.get("/unread-count", summary="Tổng số tin nhắn chưa đọc")
@router.get("/unread-total", summary="Alias tổng số tin nhắn chưa đọc")
async def get_unread_messages_count(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Aggregates total unread message count across all conversations for current user.
    """
    total = get_total_unread_count(db=db, user_id=current_user.id)
    return {
        "success": True,
        "unread_count": total
    }
