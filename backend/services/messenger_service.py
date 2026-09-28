"""
NarrAI Open Messenger Service
Provides open real-time 1-on-1 dialogue management across all registered users:
- Full User Directory search across all users (by username or full_name)
- Idempotent 1-1 conversation management (get or create between any two users)
- Real-time message persistence in SQLite
- Read status tracking (is_read, last_read_message_id) and unread count aggregation
"""

import html
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session, aliased
from sqlalchemy import or_, and_, desc, func

try:
    from db.models import (
        User,
        Conversation,
        ConversationParticipant,
        ChatMessage
    )
except ImportError:
    from backend.db.models import (
        User,
        Conversation,
        ConversationParticipant,
        ChatMessage
    )


def sanitize_message_text(text: str) -> str:
    """Sanitizes text to prevent XSS while preserving legitimate content."""
    if not text:
        return ""
    # Strip leading/trailing whitespace
    clean = text.strip()
    # Escape HTML tags
    clean = html.escape(clean)
    return clean


def search_users(
    db: Session,
    query: str = "",
    current_user_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Searches the user directory across ALL registered users by username or full_name.
    Excludes the current user from query results if current_user_id is provided.
    """
    user_query = db.query(User)
    
    if current_user_id:
        user_query = user_query.filter(User.id != current_user_id)
        
    if query and query.strip():
        q_clean = query.strip()
        user_query = user_query.filter(
            or_(
                User.username.ilike(f"%{q_clean}%"),
                User.full_name.ilike(f"%{q_clean}%")
            )
        )
        
    user_query = user_query.order_by(User.username.asc())
    users = user_query.offset(offset).limit(limit).all()
    
    return [
        {
            "id": u.id,
            "username": u.username,
            "full_name": getattr(u, "full_name", "") or "",
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]


def get_or_create_conversation(
    db: Session,
    user_id_1: int,
    user_id_2: int
) -> Tuple[Conversation, bool]:
    """
    Idempotent 1-on-1 conversation manager.
    Finds existing conversation between user_id_1 and user_id_2, or creates a new one.
    Returns: (conversation, created_flag)
    """
    if user_id_1 == user_id_2:
        raise ValueError("Cannot create a conversation with yourself.")

    # Validate that both users exist
    u1 = db.query(User).filter(User.id == user_id_1).first()
    u2 = db.query(User).filter(User.id == user_id_2).first()
    if not u1 or not u2:
        raise ValueError("One or both users do not exist in the directory.")

    # Check for existing 1-1 conversation using participant joins
    p1 = aliased(ConversationParticipant)
    p2 = aliased(ConversationParticipant)
    
    existing_conv = (
        db.query(Conversation)
        .join(p1, Conversation.id == p1.conversation_id)
        .join(p2, Conversation.id == p2.conversation_id)
        .filter(
            p1.user_id == user_id_1,
            p2.user_id == user_id_2
        )
        .first()
    )

    if existing_conv:
        return existing_conv, False

    # Create new conversation
    now = datetime.utcnow()
    new_conv = Conversation(
        created_at=now,
        updated_at=now,
        last_message_text=None,
        last_message_at=now
    )
    db.add(new_conv)
    db.flush()  # Populates new_conv.id

    part1 = ConversationParticipant(
        conversation_id=new_conv.id,
        user_id=user_id_1,
        last_read_message_id=0,
        unread_count=0,
        joined_at=now
    )
    part2 = ConversationParticipant(
        conversation_id=new_conv.id,
        user_id=user_id_2,
        last_read_message_id=0,
        unread_count=0,
        joined_at=now
    )
    db.add(part1)
    db.add(part2)
    db.commit()
    db.refresh(new_conv)

    return new_conv, True


def send_message(
    db: Session,
    conversation_id: int,
    sender_id: int,
    message_text: str
) -> ChatMessage:
    """
    Sends and persists a new message in real-time.
    Updates conversation last_message snippet and increments recipient's unread_count.
    """
    clean_text = sanitize_message_text(message_text)
    if not clean_text:
        raise ValueError("Message content cannot be empty.")

    # Verify conversation exists and sender is a participant
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise ValueError(f"Conversation {conversation_id} not found.")

    sender_part = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == sender_id
    ).first()
    if not sender_part:
        raise PermissionError(f"User {sender_id} is not a participant in conversation {conversation_id}.")

    now = datetime.utcnow()

    # Create and persist message
    message = ChatMessage(
        conversation_id=conversation_id,
        sender_id=sender_id,
        message_text=clean_text,
        is_read=False,
        created_at=now
    )
    db.add(message)
    db.flush()

    # Update conversation metadata
    conv.last_message_text = clean_text[:200]
    conv.last_message_at = now
    conv.updated_at = now

    # Update sender's last_read_message_id to their own new message
    sender_part.last_read_message_id = message.id

    # Increment unread count for recipients
    db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id != sender_id
    ).update(
        {ConversationParticipant.unread_count: ConversationParticipant.unread_count + 1},
        synchronize_session=False
    )

    db.commit()
    db.refresh(message)
    return message


def get_conversation_messages(
    db: Session,
    conversation_id: int,
    current_user_id: int,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Fetches message history for a conversation.
    Automatically marks unread incoming messages as read and resets recipient unread_count.
    """
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise ValueError(f"Conversation {conversation_id} not found.")

    # Verify participant membership
    user_part = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == current_user_id
    ).first()
    if not user_part:
        raise PermissionError(f"User {current_user_id} is not a participant in conversation {conversation_id}.")

    # Identify interlocutor (the other participant)
    interlocutor_part = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id != current_user_id
    ).first()
    
    interlocutor_info = None
    if interlocutor_part and interlocutor_part.user:
        u = interlocutor_part.user
        interlocutor_info = {
            "id": u.id,
            "username": u.username,
            "full_name": getattr(u, "full_name", "") or ""
        }

    # Query total count of messages in conversation
    total_messages = db.query(func.count(ChatMessage.id)).filter(
        ChatMessage.conversation_id == conversation_id
    ).scalar() or 0

    # Query messages with pagination ordered chronologically
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Mark incoming unread messages as read
    unread_incoming = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id,
        ChatMessage.sender_id != current_user_id,
        ChatMessage.is_read == False
    ).all()

    if unread_incoming:
        max_read_id = user_part.last_read_message_id or 0
        for msg in unread_incoming:
            msg.is_read = True
            if msg.id > max_read_id:
                max_read_id = msg.id
        user_part.last_read_message_id = max_read_id
        user_part.unread_count = 0
        db.commit()

    serialized_messages = [
        {
            "id": m.id,
            "conversation_id": m.conversation_id,
            "sender_id": m.sender_id,
            "is_self": (m.sender_id == current_user_id),
            "message_text": m.message_text,
            "is_read": m.is_read,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in messages
    ]

    return {
        "conversation_id": conversation_id,
        "interlocutor": interlocutor_info,
        "messages": serialized_messages,
        "total": total_messages,
        "limit": limit,
        "offset": offset
    }


def list_conversations(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Returns list of conversations for user_id sorted by updated_at descending.
    Includes partner profile, last message snippet, and unread count.
    """
    # Fetch participant rows for current user
    user_parts = (
        db.query(ConversationParticipant)
        .filter(ConversationParticipant.user_id == user_id)
        .all()
    )
    if not user_parts:
        return []

    conv_ids = [p.conversation_id for p in user_parts]
    part_map = {p.conversation_id: p for p in user_parts}

    # Fetch conversations sorted by updated_at desc
    convs = (
        db.query(Conversation)
        .filter(Conversation.id.in_(conv_ids))
        .order_by(desc(Conversation.updated_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for conv in convs:
        my_part = part_map.get(conv.id)
        # Find other participant
        other_part = (
            db.query(ConversationParticipant)
            .filter(
                ConversationParticipant.conversation_id == conv.id,
                ConversationParticipant.user_id != user_id
            )
            .first()
        )
        
        partner_info = None
        if other_part and other_part.user:
            partner = other_part.user
            partner_info = {
                "id": partner.id,
                "username": partner.username,
                "full_name": getattr(partner, "full_name", "") or ""
            }

        results.append({
            "id": conv.id,
            "partner": partner_info,
            "last_message_text": conv.last_message_text,
            "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
            "unread_count": my_part.unread_count if my_part else 0
        })

    return results


def get_total_unread_count(db: Session, user_id: int) -> int:
    """
    Calculates total unread message count across all conversations for a user.
    """
    total = (
        db.query(func.coalesce(func.sum(ConversationParticipant.unread_count), 0))
        .filter(ConversationParticipant.user_id == user_id)
        .scalar()
    )
    return int(total or 0)
