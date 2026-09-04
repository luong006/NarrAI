from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from dotenv import load_dotenv

# Load .env from current directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

app = FastAPI(title="NarrAI MVP")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy-load agents only when needed
qa_refiner = None
story_generator = None

def get_qa_refiner():
    global qa_refiner
    if qa_refiner is None:
        from agents.qa_refiner import QARefiner
        qa_refiner = QARefiner()
    return qa_refiner

def get_story_generator():
    global story_generator
    if story_generator is None:
        from agents.story_generator import StoryGenerator
        story_generator = StoryGenerator()
    return story_generator

import re

# ============ PYDANTIC MODELS ============
class ChatInterviewRequest(BaseModel):
    chat_history: list

class GenerateStoryRequest(BaseModel):
    refined_prompt: str
    story_length: str = "medium"

# ============ ENDPOINTS ============

@app.post("/api/chat-interview")
async def chat_interview(request: ChatInterviewRequest):
    """
    Agent 1 Phase 1 (Interactive): Generate the next interview question
    """
    try:
        qa = get_qa_refiner()
        response = qa.chat_interview(request.chat_history)
        
        # Check if the AI wants to finish the interview
        is_ready = "[READY]" in response
        cleaned_response = response.replace("[READY]", "").strip()
            
        return {
            "status": "success",
            "message": cleaned_response,
            "is_ready": is_ready
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/refine-prompt")
async def refine_prompt(request: ChatInterviewRequest):
    """
    Agent 1 Phase 2: Compress chat history into refined story brief
    """
    try:
        qa = get_qa_refiner()
        refined = qa.refine_prompt(request.chat_history)
        return {
            "status": "success",
            "refined_prompt": refined
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

from fastapi.responses import StreamingResponse
from db.models import Story, engine
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.post("/api/generate-story")
async def generate_story(request: GenerateStoryRequest):
    """
    Agent 2: Generate complete story from refined prompt (Streaming)
    """
    try:
        gen = get_story_generator()
        
        async def stream_and_save():
            full_story = ""
            try:
                for chunk in gen.generate_story_stream(request.refined_prompt, request.story_length):
                    full_story += chunk
                    yield chunk
            except Exception as e:
                yield f"\n\n[Lỗi kết nối sinh truyện: {str(e)}]"
                return
                
            # After streaming finishes, save to database
            word_count = len(full_story.split())
            if word_count > 10:
                db = SessionLocal()
                try:
                    new_story = Story(
                        refined_prompt=request.refined_prompt,
                        story_content=full_story,
                        word_count=word_count
                    )
                    db.add(new_story)
                    db.commit()
                except Exception as e:
                    print(f"Database save error: {e}")
                finally:
                    db.close()

        return StreamingResponse(
            stream_and_save(),
            media_type="text/plain"
        )
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/trending-topics")
async def get_trending_topics():
    try:
        file_path = os.path.join(os.path.dirname(__file__), "data", "trending_themes.json")
        with open(file_path, "r", encoding="utf-8") as f:
            topics = json.load(f)
        return {"status": "success", "topics": topics}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/stories")
async def get_stories():
    """
    Lấy danh sách các truyện đã tạo gần đây từ Database
    """
    db = SessionLocal()
    try:
        stories = db.query(Story).order_by(Story.created_at.desc()).limit(20).all()
        result = []
        for s in stories:
            first_line = s.story_content.strip().split('\n')[0] if s.story_content else "Truyện chưa đặt tên"
            title = first_line.replace("**", "").replace("#", "").strip()
            if len(title) > 60:
                title = title[:60] + "..."
            result.append({
                "id": s.id,
                "title": title,
                "word_count": s.word_count,
                "created_at": s.created_at.strftime("%H:%M %d/%m/%Y") if s.created_at else "",
                "snippet": s.story_content[:120].strip() + "..." if s.story_content else ""
            })
        return {"status": "success", "stories": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@app.get("/api/stories/{story_id}")
async def get_story_detail(story_id: int):
    """
    Lấy nội dung đầy đủ của một truyện theo ID
    """
    db = SessionLocal()
    try:
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            return {"status": "error", "message": "Không tìm thấy truyện"}
        return {
            "status": "success",
            "story": {
                "id": story.id,
                "refined_prompt": story.refined_prompt,
                "story_content": story.story_content,
                "word_count": story.word_count,
                "created_at": story.created_at.strftime("%H:%M %d/%m/%Y") if story.created_at else ""
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@app.get("/api/health")
async def health():
    api_key = os.environ.get("GROQ_API_KEY")
    has_key = "***" if api_key else "NOT SET"
    return {
        "status": "ok",
        "groq_api_key": has_key,
        "message": "Backend is running!"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
