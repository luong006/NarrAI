from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True)
    full_name = Column(String(100), nullable=True, default="")
    password_hash = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with stories
    stories = relationship("Story", back_populates="author")

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

# Initialize DB (Moved to end)

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

# Initialize DB
engine = create_engine('sqlite:///narrai.db', connect_args={'check_same_thread': False})
Base.metadata.create_all(engine)

# Auto-migration for existing databases
try:
    with engine.connect() as conn:
        from sqlalchemy import text, inspect
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
except Exception:
    pass  # Column already exists or table freshly created

