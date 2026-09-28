from sqlalchemy import (
    Column, String, DateTime, Integer, Text, Float, Boolean,
    ForeignKey, UniqueConstraint, create_engine, text, inspect
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

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
    user_id = Column(Integer, ForeignKey('users.id'))
    story_id = Column(Integer, ForeignKey('stories.id'), nullable=True)
    title = Column(String(200))
    adapted_offset = Column(Integer, default=0)  # tracks how many chars of story_text have been adapted
    created_at = Column(DateTime, default=datetime.utcnow)
    
    author = relationship('User')
    panels = relationship('ComicPanel', back_populates='comic', cascade='all, delete-orphan')

class ComicPanel(Base):
    __tablename__ = 'comic_panels'
    id = Column(Integer, primary_key=True)
    comic_id = Column(Integer, ForeignKey('comics.id'))
    panel_index = Column(Integer)
    image_prompt = Column(Text)
    dialogue_text = Column(Text)
    image_url = Column(String(500), nullable=True)
    layout_type = Column(String(50), default='square')
    
    comic = relationship('Comic', back_populates='panels')

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
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)
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
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    author = relationship("User", back_populates="posts")
    story = relationship("Story", back_populates="social_posts")
    interactions = relationship("PostInteraction", back_populates="post", cascade="all, delete-orphan")

class PostInteraction(Base):
    """
    Granular user interaction signal repository for recommendation scoring.
    Captures explicit (LIKE, COMMENT, BOOKMARK) and implicit (DWELL, SCROLL) signals.
    """
    __tablename__ = "post_interactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    post_id = Column(Integer, ForeignKey("social_posts.id"), index=True, nullable=False)
    interaction_type = Column(String(50), index=True, nullable=False)  # LIKE, COMMENT, BOOKMARK, SHARE, CLICK, SCROLL_50, SCROLL_100, DWELL_TIME
    dwell_seconds = Column(Float, default=0.0)
    scroll_depth = Column(Integer, default=0)  # 0, 50, 100
    comment_text = Column(Text, nullable=True)
    sentiment_score = Column(Float, default=0.0)  # -1.0 to +1.0
    extracted_entities = Column(Text, default="[]")  # JSON list of entities mentioned in comment
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="interactions")
    post = relationship("SocialPost", back_populates="interactions")

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

# ==================== DATABASE INITIALIZATION & MIGRATIONS ====================

engine = create_engine('sqlite:///narrai.db', connect_args={'check_same_thread': False})
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
except Exception:
    pass  # Column already exists or table freshly created
