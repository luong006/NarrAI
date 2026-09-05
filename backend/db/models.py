from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with stories
    stories = relationship("Story", back_populates="author")

class Story(Base):
    __tablename__ = "stories"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    initial_prompt = Column(String(500))
    refined_prompt = Column(Text)
    genre = Column(String(100))
    tone = Column(String(100))
    story_content = Column(Text)
    word_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    author = relationship("User", back_populates="stories")

# Initialize DB
engine = create_engine("sqlite:///narrai.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
