from sqlalchemy import (
    Column, String, DateTime, Integer, Text, Float, Boolean,
    ForeignKey, UniqueConstraint, Index, create_engine, text, inspect, event
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True)
    full_name = Column(String(100), nullable=True, default="")
    password_hash = Column(String(128))
    coins = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stories = relationship("Story", back_populates="author")
    transactions = relationship("CoinTransaction", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("SocialPost", back_populates="author", cascade="all, delete-orphan")
    interactions = relationship("PostInteraction", back_populates="user", cascade="all, delete-orphan")
    interest_profile = relationship("UserInterestProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Story(Base):
    __tablename__ = "stories"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    initial_prompt = Column(String(500))
    refined_prompt = Column(Text)
    genre = Column(String(100))
    tone = Column(String(100))
    story_content = Column(Text)
    word_count = Column(Integer)
    bible_data = Column(Text, nullable=True)
    memory_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    author = relationship("User", back_populates="stories")
    social_posts = relationship("SocialPost", back_populates="story")

class Comic(Base):
    __tablename__ = 'comics'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    story_id = Column(Integer, ForeignKey('stories.id'), index=True, nullable=True)
    title = Column(String(200))
    adapted_offset = Column(Integer, default=0)  # tracks how many chars of story_text have been adapted
    created_at = Column(DateTime, default=datetime.utcnow)
    
    author = relationship('User')
    panels = relationship('ComicPanel', back_populates='comic', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_comics_user_id_created_at', 'user_id', 'created_at'),
    )

class ComicPanel(Base):
    __tablename__ = 'comic_panels'
    id = Column(Integer, primary_key=True)
    comic_id = Column(Integer, ForeignKey('comics.id'), index=True)
    panel_index = Column(Integer)
    image_prompt = Column(Text)
    dialogue_text = Column(Text)
    image_url = Column(String(500), nullable=True)
    layout_type = Column(String(50), default='square')
    
    comic = relationship('Comic', back_populates='panels')

    __table_args__ = (
        Index('ix_comic_panels_comic_id_panel_index', 'comic_id', 'panel_index'),
    )

# ==================== BANKING & CRYPTOGRAPHIC LEDGER MODELS ====================

class CoinTransaction(Base):
    """
    Cryptographic immutable ledger for coin balance tracking.
    Chained using SHA-256: tx_hash = SHA256(prev_hash + user_id + amount + balance_after + timestamp).
    """
    __tablename__ = "coin_transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    amount = Column(Integer, nullable=False)  # Positive for grant/refund/topup, negative for deduction
    balance_after = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False, index=True)
    description = Column(String(255), default="")
    reference_id = Column(String(100), nullable=True)
    prev_hash = Column(String(64), nullable=False)
    tx_hash = Column(String(64), nullable=False, index=True)
    timestamp = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="transactions")

    @property
    def tx_type(self) -> str:
        return self.action_type

    @tx_type.setter
    def tx_type(self, val: str):
        self.action_type = val

class DeviceFingerprint(Base):
    """
    Tracks browser hardware signatures for Multi-Signal Anti-Clone Guard.
    Composite hash combines Canvas 2D + WebGL + AudioContext + Screen Specs.
    """
    __tablename__ = "device_fingerprints"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fingerprint_hash = Column(String(64), unique=True, index=True, nullable=False)
    canvas_hash = Column(String(64), nullable=True)
    webgl_hash = Column(String(64), nullable=True)
    audio_hash = Column(String(64), nullable=True)
    screen_specs = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    has_claimed_trial = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SubnetRecord(Base):
    """
    Tracks IP /24 subnet request history to throttle Sybil/clone attacks.
    """
    __tablename__ = "subnet_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subnet = Column(String(64), unique=True, index=True, nullable=False)
    claim_count = Column(Integer, default=0, nullable=False)
    last_claim_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==================== SOCIAL & MESSENGER MODELS (M2 FOUNDATION) ====================

class SocialPost(Base):
    """
    Published literary works on NarrAI social graph.
    Stores 128-dimensional concept embedding vectors and extracted DSGO entities/spaces.
    """
    __tablename__ = "social_posts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    story_id = Column(Integer, ForeignKey("stories.id"), index=True, nullable=True)
    title = Column(String(255), nullable=False)
    content_snippet = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    genre = Column(String(100), index=True, nullable=True)
    tags = Column(Text, default="[]")  # JSON-serialized list of tags
    concept_vector = Column(Text, default="[]")  # 128-dim JSON-serialized float vector
    dsgo_entities = Column(Text, default="[]")  # JSON list of DSGO character entities
    dsgo_spaces = Column(Text, default="[]")  # JSON list of DSGO space enclosures
    completion_count = Column(Integer, default=0, nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    comments_count = Column(Integer, default=0, nullable=False)
    views_count = Column(Integer, default=0, nullable=False)
    dwell_time_avg = Column(Float, default=0.0)
    is_fanfiction = Column(Boolean, default=False, index=True)
    disclaimer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    author = relationship("User", back_populates="posts")
    story = relationship("Story", back_populates="social_posts")
    interactions = relationship("PostInteraction", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_social_posts_genre_created_at', 'genre', 'created_at'),
        Index('ix_social_posts_user_id_created_at', 'user_id', 'created_at'),
    )

class PostInteraction(Base):
    """
    Granular user interaction signal repository for recommendation scoring.
    Captures explicit (LIKE, COMMENT, BOOKMARK) and implicit (DWELL, SCROLL) signals.
    """
    __tablename__ = "post_interactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    post_id = Column(Integer, ForeignKey("social_posts.id"), index=True, nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("post_interactions.id"), nullable=True, index=True)
    interaction_type = Column(String(50), index=True, nullable=False)  # LIKE, COMMENT, BOOKMARK, SHARE, CLICK, SCROLL_50, SCROLL_100, DWELL_TIME
    dwell_seconds = Column(Float, default=0.0)
    scroll_depth = Column(Integer, default=0)  # 0, 50, 100
    comment_text = Column(Text, nullable=True)
    sentiment_score = Column(Float, default=0.0)  # -1.0 to +1.0
    extracted_entities = Column(Text, default="[]")  # JSON list of entities mentioned in comment
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="interactions")
    post = relationship("SocialPost", back_populates="interactions")
    parent_comment = relationship("PostInteraction", remote_side=[id], backref="replies")

    __table_args__ = (
        Index('ix_post_interactions_post_type_created', 'post_id', 'interaction_type', 'created_at'),
    )

    @property
    def dwell_time(self) -> float:
        return self.dwell_seconds

    @dwell_time.setter
    def dwell_time(self, val: float):
        self.dwell_seconds = float(val) if val is not None else 0.0

class UserInterestProfile(Base):
    """
    Dynamic interest profile with exponential time decay (lambda = 0.05/day).
    """
    __tablename__ = "user_interest_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    interest_vector = Column(Text, default="[]")  # 128-dim JSON float vector
    last_decay_time = Column(DateTime, default=datetime.utcnow)
    genre_affinity = Column(Text, default="{}")  # JSON map: {"Kiếm hiệp": 0.85, ...}
    entity_affinity = Column(Text, default="{}")  # JSON map: {"Trần Hưng Đạo": 1.2, ...}
    last_active_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="interest_profile")

class Conversation(Base):
    """
    1-on-1 dialogue container for Open Messenger.
    """
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    last_message_text = Column(Text, nullable=True)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    
    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")

class ConversationParticipant(Base):
    """
    Participant association with unread counter and read receipts.
    """
    __tablename__ = "conversation_participants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    last_read_message_id = Column(Integer, default=0)
    unread_count = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uq_conv_user"),
    )

class ChatMessage(Base):
    """
    Encrypted/sanitized message record in Open Messenger.
    """
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    message_text = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User")


# ==================== MILESTONE 3: SOCIAL GRAPH & COMMUNITY MODELS ====================

class Follow(Base):
    """
    Follower graph connecting readers and authors.
    """
    __tablename__ = "follows"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    follower_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    following_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    follower = relationship("User", foreign_keys=[follower_id])
    following = relationship("User", foreign_keys=[following_id])
    
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_user_follower_following"),
        Index("ix_follows_follower_following", "follower_id", "following_id"),
    )


class Bookmark(Base):
    """
    Personal library bookmark collections with categories and tags.
    """
    __tablename__ = "bookmarks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    post_id = Column(Integer, ForeignKey("social_posts.id"), index=True, nullable=False)
    category = Column(String(100), default="Yêu thích", index=True)
    tags = Column(Text, default="[]")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User")
    post = relationship("SocialPost")
    
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_user_post_bookmark"),
        Index("ix_bookmarks_user_category", "user_id", "category"),
    )


class Notification(Base):
    """
    User event notifications for social engagements (LIKE, COMMENT, FOLLOW, MESSAGE).
    """
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    notification_type = Column(String(50), index=True, nullable=False)
    post_id = Column(Integer, ForeignKey("social_posts.id"), nullable=True, index=True)
    comment_id = Column(Integer, nullable=True)
    conversation_id = Column(Integer, nullable=True)
    content = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    recipient = relationship("User", foreign_keys=[recipient_id])
    sender = relationship("User", foreign_keys=[sender_id])
    post = relationship("SocialPost", foreign_keys=[post_id])
    
    __table_args__ = (
        Index("ix_notifications_recipient_is_read_created", "recipient_id", "is_read", "created_at"),
    )


class ContentReport(Base):
    """
    Content moderation reports (distortion, spam, harassment).
    """
    __tablename__ = "content_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    post_id = Column(Integer, ForeignKey("social_posts.id"), nullable=True, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    report_reason = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    status = Column(String(30), default="PENDING", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    reporter = relationship("User", foreign_keys=[reporter_id])
    post = relationship("SocialPost", foreign_keys=[post_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    
    __table_args__ = (
        Index("ix_content_reports_status_created", "status", "created_at"),
    )


class AuthorProfile(Base):
    """
    Author public biography, stats, and social presence.
    """
    __tablename__ = "author_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    bio = Column(Text, default="")
    avatar_url = Column(String(500), nullable=True)
    cover_url = Column(String(500), nullable=True)
    genres = Column(Text, default="[]")
    followers_count = Column(Integer, default=0, nullable=False)
    following_count = Column(Integer, default=0, nullable=False)
    works_count = Column(Integer, default=0, nullable=False)
    total_likes = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_author_profiles_user_id"),
    )


# ==================== DATABASE INITIALIZATION & MIGRATIONS ====================

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./narrai.db")
if not DATABASE_URL.startswith("sqlite"):
    raise RuntimeError("NarrAI currently requires SQLite; configure DATABASE_URL with a sqlite URL.")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.close()

Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auto-migration for existing databases
try:
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        conn.execute(text("PRAGMA synchronous=NORMAL;"))
        conn.commit()

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if "comics" in tables:
            comic_cols = [c["name"] for c in inspector.get_columns("comics")]
            if "adapted_offset" not in comic_cols:
                conn.execute(text("ALTER TABLE comics ADD COLUMN adapted_offset INTEGER DEFAULT 0"))
                conn.commit()
        if "users" in tables:
            user_cols = [c["name"] for c in inspector.get_columns("users")]
            if "full_name" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(100) DEFAULT ''"))
                conn.commit()
            if "coins" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0"))
                conn.commit()

        # Single and Composite index auto-migrations
        if "comics" in tables:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_comics_user_id ON comics(user_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_comics_story_id ON comics(story_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_comics_user_id_created_at ON comics(user_id, created_at);"))
        if "comic_panels" in tables:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_comic_panels_comic_id ON comic_panels(comic_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_comic_panels_comic_id_panel_index ON comic_panels(comic_id, panel_index);"))
        if "social_posts" in tables:
            post_cols = [c["name"] for c in inspector.get_columns("social_posts")]
            if "is_fanfiction" not in post_cols:
                conn.execute(text("ALTER TABLE social_posts ADD COLUMN is_fanfiction BOOLEAN DEFAULT 0"))
                conn.commit()
            if "disclaimer" not in post_cols:
                conn.execute(text("ALTER TABLE social_posts ADD COLUMN disclaimer TEXT"))
                conn.commit()
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_posts_story_id ON social_posts(story_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_posts_genre_created_at ON social_posts(genre, created_at);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_social_posts_user_id_created_at ON social_posts(user_id, created_at);"))
        if "post_interactions" in tables:
            pi_cols = [c["name"] for c in inspector.get_columns("post_interactions")]
            if "parent_comment_id" not in pi_cols:
                conn.execute(text("ALTER TABLE post_interactions ADD COLUMN parent_comment_id INTEGER REFERENCES post_interactions(id)"))
                conn.commit()
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_post_interactions_parent_comment ON post_interactions(parent_comment_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_post_interactions_post_type_created ON post_interactions(post_id, interaction_type, created_at);"))
        if "follows" in tables:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_follows_follower_id ON follows(follower_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_follows_following_id ON follows(following_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_follows_follower_following ON follows(follower_id, following_id);"))
        if "bookmarks" in tables:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bookmarks_user_id ON bookmarks(user_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bookmarks_post_id ON bookmarks(post_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bookmarks_user_category ON bookmarks(user_id, category);"))
        if "notifications" in tables:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_recipient_id ON notifications(recipient_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_recipient_is_read_created ON notifications(recipient_id, is_read, created_at);"))
        if "content_reports" in tables:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_content_reports_status_created ON content_reports(status, created_at);"))
        if "author_profiles" in tables:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_author_profiles_user_id ON author_profiles(user_id);"))
        conn.commit()
except Exception as exc:
    raise RuntimeError("NarrAI database schema initialization or migration failed.") from exc

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "User",
    "Story",
    "Comic",
    "ComicPanel",
    "CoinTransaction",
    "DeviceFingerprint",
    "SubnetRecord",
    "SocialPost",
    "PostInteraction",
    "UserInterestProfile",
    "Conversation",
    "ConversationParticipant",
    "ChatMessage",
    "Follow",
    "Bookmark",
    "Notification",
    "ContentReport",
    "AuthorProfile",
]
