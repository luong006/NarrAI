from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy-load agents
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
from fastapi.responses import StreamingResponse
from db.models import Story, User, engine
from sqlalchemy.orm import sessionmaker, Session
from auth import verify_password, get_password_hash, create_access_token, decode_access_token

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    username: str = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    return user

# ============ PYDANTIC MODELS ============
class ChatInterviewRequest(BaseModel):
    chat_history: list

class GenerateStoryRequest(BaseModel):
    refined_prompt: str
    story_length: str = "medium"

class EditTextRequest(BaseModel):
    original_text: str
    instruction: str

class UserCreate(BaseModel):
    username: str
    password: str

# ============ AUTH ENDPOINTS ============

@app.post("/api/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    return {"status": "success", "message": "Đăng ký thành công"}

@app.post("/api/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Sai tên đăng nhập hoặc mật khẩu")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}

@app.get("/api/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    return {"username": current_user.username}

# ============ CORE ENDPOINTS ============

@app.post("/api/chat-interview")
async def chat_interview(request: ChatInterviewRequest):
    try:
        qa = get_qa_refiner()
        response = qa.chat_interview(request.chat_history)
        is_ready = "[READY]" in response
        cleaned_response = response.replace("[READY]", "").strip()
        return {"status": "success", "message": cleaned_response, "is_ready": is_ready}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/refine-prompt")
async def refine_prompt(request: ChatInterviewRequest):
    try:
        qa = get_qa_refiner()
        refined = qa.refine_prompt(request.chat_history)
        return {"status": "success", "refined_prompt": refined}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/edit-text")
async def edit_text(request: EditTextRequest):
    try:
        from agents.editor_agent import EditorAgent
        editor = EditorAgent()
        revised = editor.edit_text(request.original_text, request.instruction)
        return {"status": "success", "revised_text": revised}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/generate-story")
async def generate_story(request: GenerateStoryRequest, current_user: User = Depends(get_current_user)):
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
                
            word_count = len(full_story.split())
            if word_count > 10 and current_user:
                db = SessionLocal()
                try:
                    new_story = Story(
                        user_id=current_user.id,
                        refined_prompt=request.refined_prompt,
                        story_content=full_story,
                        word_count=word_count
                    )
                    db.add(new_story)
                    db.commit()
                except Exception as e:
                    print(f"DB Error: {e}")
                finally:
                    db.close()

        return StreamingResponse(stream_and_save(), media_type="text/plain")
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
async def get_stories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        return {"status": "success", "stories": []}
        
    try:
        stories = db.query(Story).filter(Story.user_id == current_user.id).order_by(Story.created_at.desc()).limit(20).all()
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

@app.get("/api/stories/{story_id}")
async def get_story_detail(story_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        return {"status": "error", "message": "Yêu cầu đăng nhập"}
        
    try:
        story = db.query(Story).filter(Story.id == story_id, Story.user_id == current_user.id).first()
        if not story:
            return {"status": "error", "message": "Không tìm thấy truyện hoặc không có quyền xem"}
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

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "Backend is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
