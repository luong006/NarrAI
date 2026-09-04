from sqlalchemy import Column, String, DateTime, Integer, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Story(Base):
    __tablename__ = "stories"
    
    id = Column(Integer, primary_key=True)
    initial_prompt = Column(String(500))
    refined_prompt = Column(Text)
    genre = Column(String(100))
    tone = Column(String(100))
    story_content = Column(Text)
    word_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# Initialize DB
engine = create_engine("sqlite:///narrai.db")
Base.metadata.create_all(engine)
