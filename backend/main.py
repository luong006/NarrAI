import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import json
import os
import re
import uuid
from typing import Tuple, Optional, List, Dict, Any
from dotenv import load_dotenv

# Load .env from current directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

app = FastAPI(title="NarrAI MVP")

REQUIRED_API_KEYS = {
    "GROQ_API_KEY": "Story Generator and Editor",
    "GROQ_API_KEY_BIBLE": "QA Refiner and Memory Extractor",
    "GROQ_API_KEY_COPILOT": "Master Controller / Copilot",
}

def safe_generation_error(error, operation="sinh truyện"):
    message = str(error)
    if "413" in message or "rate_limit_exceeded" in message or "Request too large" in message:
        return f"Yêu cầu {operation} vượt giới hạn token hiện tại. Hãy chọn nội dung ngắn hơn hoặc thử lại sau."
    return f"Không thể {operation} lúc này. Vui lòng thử lại sau."

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip response compression for responses >= 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

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
import urllib.parse
from fastapi.responses import StreamingResponse, JSONResponse, Response, RedirectResponse, FileResponse
from services.cloudflare_ai import generate_image_cf, get_cached_or_generate_image, get_deterministic_comic_seed
from db.models import Story, User, Comic, ComicPanel, engine
from sqlalchemy.orm import sessionmaker, Session
from auth import verify_password, get_password_hash, create_access_token, decode_access_token, validate_bank_password, login_rate_limiter

try:
    from services.ontology import (
        NarrativeMode,
        HistoricalGroundingGatekeeper,
        auto_detect_narrative_mode,
        HistoricalDistortionError
    )
except ImportError:
    try:
        from backend.services.ontology import (
            NarrativeMode,
            HistoricalGroundingGatekeeper,
            auto_detect_narrative_mode,
            HistoricalDistortionError
        )
    except ImportError:
        NarrativeMode = None
        HistoricalGroundingGatekeeper = None
        auto_detect_narrative_mode = None
        class HistoricalDistortionError(ValueError): pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def persist_partial_story(session_id, story_id, partial_text):
    """Preserve streamed prose when the model or connection stops unexpectedly."""
    if not partial_text or not partial_text.strip():
        return

    db = SessionLocal()
    try:
        query = db.query(Story)
        if story_id:
            query = query.filter(Story.id == story_id)
        elif session_id:
            query = query.filter(Story.session_id == session_id)
        else:
            return

        story = query.first()
        if not story:
            return

        existing_text = (story.story_content or "").rstrip()
        partial = partial_text.strip()
        if not existing_text.endswith(partial):
            story.story_content = f"{existing_text}\n\n{partial}".strip() if existing_text else partial
        story.word_count = len((story.story_content or "").split())
        db.commit()
    except Exception as save_error:
        db.rollback()
        print(f"Failed to preserve interrupted story stream: {save_error}")
    finally:
        db.close()


def refund_generation_charge(
    db: Session,
    user_id: int,
    reference_id: Optional[str],
    amount: int,
    operation: str,
) -> None:
    if not reference_id:
        return
    try:
        db.rollback()
        refund_coins(
            db=db,
            user_id=user_id,
            amount=amount,
            reason=ACTION_REFUND_FAILED,
            reference_id=reference_id,
            description=f"Hoàn {amount} xu do lỗi trước khi bắt đầu {operation}.",
        )
    except Exception:
        import logging
        logging.getLogger("narrai.main").exception(
            "Could not refund generation charge for user %s, reference %s",
            user_id,
            reference_id,
        )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Sub-Routers Mount
from routers.coins_router import router as coins_router
from routers.social_router import router as social_router, recommender_router
from routers.messenger_router import router as messenger_router

app.include_router(coins_router, prefix="/api/coins", tags=["Coins"])
app.include_router(social_router, prefix="/api/social", tags=["Social"])
app.include_router(recommender_router)
app.include_router(messenger_router, prefix="/api/messenger", tags=["Messenger"])


# Banking Services
from services.banking_service import (
    deduct_coins,
    refund_coins,
    register_device_and_get_initial_coins,
    get_story_cost,
    get_action_cost,
    COST_SHORT_STORY,
    COST_MEDIUM_STORY,
    COST_LONG_STORY,
    COST_EDIT,
    COST_MANGA,
    ACTION_STORY_SHORT,
    ACTION_STORY_MEDIUM,
    ACTION_STORY_LONG,
    ACTION_STORY_EDIT,
    ACTION_COMIC_GENERATE,
    ACTION_REFUND_FAILED,
)

# Cache for users backed by CacheManager
from services.cache_service import get_cache_manager

class _UserCacheProxy(dict):
    def __getitem__(self, key):
        mgr = get_cache_manager()
        u = mgr.get_user_token(key)
        if u is None:
            raise KeyError(key)
        return User(id=u.get("id"), username=u.get("username"), full_name=u.get("full_name", ""))
    def __contains__(self, key):
        mgr = get_cache_manager()
        return mgr.get_user_token(key) is not None
    def __setitem__(self, key, value):
        mgr = get_cache_manager()
        if hasattr(value, "id"):
            mgr.set_user_token(key, {"id": value.id, "username": value.username, "full_name": getattr(value, "full_name", "") or ""}, ttl=1800)
        elif isinstance(value, dict):
            mgr.set_user_token(key, value, ttl=1800)
    def get(self, key, default=None):
        mgr = get_cache_manager()
        u = mgr.get_user_token(key)
        if u is None:
            return default
        return User(id=u.get("id"), username=u.get("username"), full_name=u.get("full_name", ""))

USER_CACHE = _UserCacheProxy()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        return None
        
    cache_mgr = get_cache_manager()
    cached_user = cache_mgr.get_user_token(token)
    if cached_user and isinstance(cached_user, dict):
        return User(
            id=cached_user.get("id"),
            username=cached_user.get("username"),
            full_name=cached_user.get("full_name", "")
        )
        
    payload = decode_access_token(token)
    if not payload:
        return None
    username: str = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    
    if user:
        cache_mgr.set_user_token(token, {
            "id": user.id,
            "username": user.username,
            "full_name": getattr(user, "full_name", "") or ""
        }, ttl=1800)
        
    return user

# ============ PYDANTIC MODELS ============
class ChatInterviewRequest(BaseModel):
    chat_history: list = []
    user_input: Optional[str] = None
    genre: Optional[str] = None
    fallback_to_heuristic: bool = False

class ChatRequest(BaseModel):
    story_text: str
    user_message: str
    story_id: int | None = None

class GenerateStoryRequest(BaseModel):
    refined_prompt: str
    story_length: str = "medium"

class StoryAllocateRequest(BaseModel):
    refined_prompt: Optional[str] = ""
    story_length: Optional[str] = "medium"
    genre: Optional[str] = None
    tone: Optional[str] = None
    session_id: Optional[str] = None

class EditTextRequest(BaseModel):
    original_text: str
    instruction: str
    story_id: int | None = None

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str | None = ""
    fingerprint: dict | str | None = None

from fastapi import Request

@app.post("/api/register")
async def register_user(request: Request, db: Session = Depends(get_db)):
    username = None
    password = None
    full_name = ""
    fingerprint_data = None

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("username")
            password = body.get("password")
            full_name = body.get("full_name", "")
            fingerprint_data = body.get("fingerprint") or body.get("fingerprint_data") or body.get("device_fingerprint")
        except Exception:
            pass
    else:
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
            full_name = form.get("full_name", "")
            fingerprint_data = form.get("fingerprint") or form.get("fingerprint_data") or form.get("device_fingerprint")
        except Exception:
            pass

    if not username or not password:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp đầy đủ tên đăng nhập và mật khẩu (Please provide username and password)")

    username = str(username).strip()
    password = str(password)
    full_name = str(full_name).strip() if full_name else ""

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Tên đăng nhập phải có ít nhất 3 ký tự (Username must be at least 3 characters)")

    # Bank-grade password validation
    is_valid, err_vi, err_en = validate_bank_password(password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"{err_vi} ({err_en})")

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại (Username already exists)")

    # Extract client IP for anti-clone guard
    client_ip = (
        request.headers.get("x-forwarded-for")
        or request.headers.get("x-real-ip")
        or (request.client.host if request.client else "127.0.0.1")
    )
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    hashed_password = get_password_hash(password)
    new_user = User(username=username, full_name=full_name, password_hash=hashed_password, coins=0)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Register device fingerprint & grant initial trial coins (8 coins if fresh, 0 if clone/throttled)
    initial_coins = 0
    try:
        initial_coins = register_device_and_get_initial_coins(
            db=db,
            client_ip=client_ip,
            fingerprint_data=fingerprint_data or {},
            user_id=new_user.id
        )
        db.refresh(new_user)
    except Exception as e:
        print(f"Anti-clone trial grant warning: {e}")

    # Generate token immediately so user is automatically logged in upon registration
    access_token = create_access_token(data={"sub": new_user.username})
    return {
        "status": "success",
        "message": "Đăng ký thành công",
        "access_token": access_token,
        "token": access_token,
        "token_type": "bearer",
        "username": new_user.username,
        "full_name": new_user.full_name or new_user.username,
        "coins": new_user.coins if new_user.coins is not None else 0,
        "coins_granted": initial_coins
    }

@app.post("/api/login")
async def login_user(request: Request, db: Session = Depends(get_db)):
    username = None
    password = None

    # Determine client IP for brute-force rate limiting
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    elif request.client and request.client.host:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("username")
            password = body.get("password")
        except Exception:
            pass
    else:
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
        except Exception:
            pass

    if not username or not password:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp đầy đủ tên đăng nhập và mật khẩu (Please provide username and password)")

    username = str(username).strip()
    password = str(password)

    # Check brute-force rate limit (HTTP 429 lockout)
    login_rate_limiter.check_rate_limit(client_ip, username)

    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        is_locked, remaining = login_rate_limiter.record_failure(client_ip, username)
        if is_locked:
            raise HTTPException(
                status_code=429,
                detail=f"Đăng nhập thất bại quá nhiều lần. Vui lòng thử lại sau {remaining} giây. (Too many failed login attempts. Please try again in {remaining} seconds.)"
            )
        raise HTTPException(status_code=400, detail="Sai tên đăng nhập hoặc mật khẩu (Invalid username or password)")
    
    # Successful login: reset failure counter
    login_rate_limiter.record_success(client_ip, username)

    access_token = create_access_token(data={"sub": user.username})
    return {
        "status": "success",
        "access_token": access_token,
        "token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "full_name": user.full_name or user.username
    }

@app.get("/api/me")
@app.get("/api/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập (Not logged in)")
    return {
        "status": "success",
        "username": current_user.username,
        "full_name": current_user.full_name or current_user.username
    }

# ============ CORE ENDPOINTS ============

@app.post("/api/chat-interview")
def chat_interview(request: ChatInterviewRequest):
    try:
        qa = get_qa_refiner()
        history = list(request.chat_history or [])
        if request.user_input and (not history or history[-1].get("content") != request.user_input):
            history.append({"role": "user", "content": request.user_input})

        response = qa.chat_interview(
            history,
            fallback_to_heuristic=request.fallback_to_heuristic,
        )
        is_ready = "[READY]" in response
        cleaned_response = response.replace("[READY]", "").strip()
        return {
            "status": "success",
            "message": cleaned_response,
            "reply": cleaned_response,
            "is_ready": is_ready,
            "detected_mode": getattr(qa, "last_model_used", None),
        }
    except Exception as e:
        import logging
        logging.getLogger("narrai.main").error(f"Chat interview failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": f"Dịch vụ AI tạm thời gián đoạn: {str(e)}",
                "detail": str(e),
                "retry_after": 5,
                "is_ready": False,
            },
        )

@app.post("/api/refine-prompt")
def refine_prompt(request: ChatInterviewRequest):
    try:
        qa = get_qa_refiner()
        refined = qa.refine_prompt(request.chat_history)
        return {"status": "success", "refined_prompt": refined}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/edit-text")
async def edit_text(
    request: EditTextRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deduct_ref = None
    if current_user:
        deduct_ok, deduct_ref, bal_after = deduct_coins(
            db=db,
            user_id=current_user.id,
            amount=COST_EDIT,
            action_type=ACTION_STORY_EDIT,
            description=f"Chỉnh sửa bản thảo - {COST_EDIT} xu",
            raise_on_insufficient=True
        )

    try:
        from agents.editor_agent import EditorAgent
        editor = EditorAgent()
        revised = editor.edit_text(request.original_text, request.instruction)
        if request.story_id:
            cache_mgr = get_cache_manager()
            cache_mgr.delete_draft(request.story_id)
        return {"status": "success", "revised_text": revised}
    except Exception as e:
        if current_user and deduct_ref:
            try:
                refund_coins(
                    db=db,
                    user_id=current_user.id,
                    amount=COST_EDIT,
                    reason=ACTION_REFUND_FAILED,
                    reference_id=deduct_ref,
                    description=f"Hoàn {COST_EDIT} xu do sự cố sửa bản thảo: {str(e)[:100]}"
                )
            except Exception as refund_err:
                print(f"Compensating rollback error: {refund_err}")
        return {"status": "error", "message": str(e)}

@app.post("/api/stories/allocate")
def allocate_story_id(
    request: StoryAllocateRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Instantly allocates a story_id and creates a draft Story record in DB.
    Allows frontend to bind story_id immediately upon transitioning from Intake Chat.
    """
    session_id = request.session_id or str(uuid.uuid4())
    new_story = Story(
        session_id=session_id,
        user_id=current_user.id if current_user else None,
        refined_prompt=request.refined_prompt or "",
        genre=request.genre or "",
        tone=request.tone or "",
        story_content="",
        word_count=0
    )
    db.add(new_story)
    db.commit()
    db.refresh(new_story)
    return {
        "status": "success",
        "story_id": new_story.id,
        "session_id": session_id
    }

@app.post("/api/generate-story")
def generate_story(
    request: GenerateStoryRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deduct_ref = None
    cost = 0
    try:
        # Auto-detect narrative mode and pre-validate historical invariants
        detected_mode = NarrativeMode.HU_CAU_TU_DO
        if auto_detect_narrative_mode is not None:
            detected_mode, _ = auto_detect_narrative_mode(request.refined_prompt)

        if HistoricalGroundingGatekeeper is not None:
            is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                request.refined_prompt, mode=detected_mode, user_prompt=request.refined_prompt
            )
            if not is_valid:
                raise HTTPException(
                    status_code=422,
                    detail=f"Vi phạm tính chân thực lịch sử Việt Nam: {'; '.join(violations)}"
                )

        cost = get_story_cost(request.story_length)
        action_type = (
            ACTION_STORY_SHORT if cost == COST_SHORT_STORY
            else ACTION_STORY_LONG if cost == COST_LONG_STORY
            else ACTION_STORY_MEDIUM
        )
        if current_user:
            deduct_ok, deduct_ref, bal_after = deduct_coins(
                db=db,
                user_id=current_user.id,
                amount=cost,
                action_type=action_type,
                description=f"Tạo truyện ({request.story_length}) - {cost} xu",
                raise_on_insufficient=True
            )

        gen = get_story_generator()
        
        # Pre-allocate Story record in DB at stream inception for both guests and authenticated users
        session_id = str(uuid.uuid4())
        pre_story_id = None
        db_pre = SessionLocal()
        try:
            pre_story = Story(
                session_id=session_id,
                user_id=current_user.id if current_user else None,
                refined_prompt=request.refined_prompt,
                story_content="",
                word_count=0
            )
            db_pre.add(pre_story)
            db_pre.commit()
            db_pre.refresh(pre_story)
            pre_story_id = pre_story.id
        except Exception as db_pre_err:
            print(f"[Pre-allocate Story DB Error in generate-story] {db_pre_err}")
        finally:
            db_pre.close()

        async def stream_and_save():
            full_story = ""
            saved_story_id = pre_story_id
            # Yield pre-allocated story_id immediately at stream inception
            if pre_story_id:
                yield f"[STORY_ID:{pre_story_id}]\n\n"

            try:
                for chunk in gen.generate_story_stream(request.refined_prompt, request.story_length):
                    full_story += chunk
                    yield chunk
            except Exception as e:
                persist_partial_story(session_id, saved_story_id, full_story)
                # Compensating transaction rollback: 100% refund on AI generation failure
                if current_user and deduct_ref:
                    rollback_db = SessionLocal()
                    try:
                        refund_coins(
                            db=rollback_db,
                            user_id=current_user.id,
                            amount=cost,
                            reason=ACTION_REFUND_FAILED,
                            reference_id=deduct_ref,
                            description=f"Hoàn {cost} xu do sự cố sinh truyện: {str(e)[:100]}"
                        )
                    except Exception as refund_err:
                        print(f"Compensating rollback error: {refund_err}")
                    finally:
                        rollback_db.close()
                yield f"\n\n[GENERATION_ERROR:{safe_generation_error(e)}]"
                return

            # Post-generation invariant validation
            if HistoricalGroundingGatekeeper is not None and full_story:
                is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                    full_story, mode=detected_mode, user_prompt=request.refined_prompt
                )
                if not is_valid:
                    # Halt generation and trigger compensating transaction coin refund
                    if current_user and deduct_ref:
                        rollback_db = SessionLocal()
                        try:
                            refund_coins(
                                db=rollback_db,
                                user_id=current_user.id,
                                amount=cost,
                                reason=ACTION_REFUND_FAILED,
                                reference_id=deduct_ref,
                                description=f"Hoàn {cost} xu do vi phạm lịch sử: {'; '.join(violations)[:100]}"
                            )
                        except Exception as refund_err:
                            print(f"Compensating rollback error on historical violation: {refund_err}")
                        finally:
                            rollback_db.close()

                    # Clean up pre-allocated story record
                    if pre_story_id:
                        db_clean = SessionLocal()
                        try:
                            pre_rec = db_clean.query(Story).filter(Story.id == pre_story_id).first()
                            if pre_rec:
                                db_clean.delete(pre_rec)
                                db_clean.commit()
                        except Exception as clean_err:
                            print(f"Error cleaning up pre-allocated story: {clean_err}")
                        finally:
                            db_clean.close()

                    yield f"\n\n[HISTORICAL_VIOLATION: Nội dung đã bị chặn do vi phạm lịch sử dân tộc: {'; '.join(violations)}]"
                    return
                
            word_count = len(full_story.split())
            db_save = SessionLocal()
            try:
                if pre_story_id:
                    existing_story = db_save.query(Story).filter(Story.id == pre_story_id).first()
                    if existing_story:
                        existing_story.story_content = full_story
                        existing_story.word_count = word_count
                        db_save.commit()
                elif word_count > 10:
                    new_story = Story(
                        session_id=session_id,
                        user_id=current_user.id if current_user else None,
                        refined_prompt=request.refined_prompt,
                        story_content=full_story,
                        word_count=word_count
                    )
                    db_save.add(new_story)
                    db_save.commit()
                    db_save.refresh(new_story)
                    saved_story_id = new_story.id
            except Exception as e:
                print(f"DB Error: {e}")
            finally:
                db_save.close()

            if saved_story_id:
                yield f"\n\n[STORY_ID:{saved_story_id}]"

        return StreamingResponse(stream_and_save(), media_type="text/plain")
    except HTTPException:
        if current_user and deduct_ref:
            refund_generation_charge(db, current_user.id, deduct_ref, cost, "sinh truyện")
        raise
    except Exception as e:
        if current_user and deduct_ref:
            refund_generation_charge(db, current_user.id, deduct_ref, cost, "sinh truyện")
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
        cache_mgr = get_cache_manager()
        cached_draft = cache_mgr.get_draft(story_id)
        if cached_draft and cached_draft.get("user_id") == current_user.id:
            story_res = {k: v for k, v in cached_draft.items() if k != "user_id"}
            return {
                "status": "success",
                "story": story_res
            }

        story = db.query(Story).filter(Story.id == story_id, Story.user_id == current_user.id).first()
        if not story:
            return {"status": "error", "message": "Không tìm thấy truyện hoặc không có quyền xem"}
            
        story_dict = {
            "id": story.id,
            "user_id": story.user_id,
            "session_id": story.session_id,
            "refined_prompt": story.refined_prompt,
            "story_content": story.story_content,
            "word_count": story.word_count,
            "bible_data": story.bible_data,
            "memory_data": story.memory_data,
            "created_at": story.created_at.strftime("%H:%M %d/%m/%Y") if story.created_at else ""
        }
        cache_mgr.set_draft(story_id, story_dict, ttl=3600)
        story_res = {k: v for k, v in story_dict.items() if k != "user_id"}
        return {
            "status": "success",
            "story": story_res
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/health")
async def health():
    missing = [name for name in REQUIRED_API_KEYS if not os.environ.get(name)]
    cache_mgr = get_cache_manager()
    cache_stats = cache_mgr.get_stats()
    return {
        "status": "ok" if not missing else "degraded",
        "message": "Backend is running!",
        "missing_keys": missing,
        "cache": cache_stats,
    }

# ================= COMIC ENDPOINTS =================
import urllib.parse
from fastapi import Response
from fastapi.responses import RedirectResponse
from db.models import Comic, ComicPanel
from services.cloudflare_ai import generate_image_cf

class ComicRequest(BaseModel):
    story_id: Optional[int] = None
    story_text: str

class ComicContinueRequest(BaseModel):
    comic_id: int
    story_text: str

def _save_panels(db, comic, script_data, start_index=0):
    """Helper to save panel data to DB and return response list with Cloudflare proxy URLs."""
    panels_response = []
    for i, item in enumerate(script_data):
        p_img_prompt = item.get('image_prompt', 'comic manga scene')
        p_dialogue = item.get('dialogue_text', '')
        p_layout = item.get('layout_type', 'square')
        p_index = start_index + item.get('panel_index', i + 1)
        
        panel = ComicPanel(
            comic_id=comic.id,
            panel_index=p_index,
            image_prompt=p_img_prompt,
            dialogue_text=p_dialogue,
            layout_type=p_layout,
            image_url=""
        )
        db.add(panel)
        db.commit()
        db.refresh(panel)
        
        # Route through Cloudflare proxy endpoint
        panel.image_url = f"/api/comic/image/{panel.id}"
        db.commit()
        
        panels_response.append({
            'panel_id': panel.id,
            'panel_index': panel.panel_index,
            'image_url': panel.image_url,
            'image_prompt': panel.image_prompt,
            'dialogue_text': panel.dialogue_text,
            'layout_type': panel.layout_type
        })
    return panels_response

def _get_story_memory(story, db):
    """Load StoryMemory from DB for visual ontology context."""
    try:
        if story and story.memory_data:
            from agents.story_memory import StoryMemory
            return StoryMemory.from_dict(json.loads(story.memory_data))
    except Exception as e:
        print(f"[Comic] Could not load story memory: {e}")
    return None

def extract_sentence_bounded_chunk(text: str, target_size: int = 5000, max_limit: int = 6500) -> tuple[str, int]:
    """
    Extracts a chunk of story text breaking strictly at the nearest sentence boundary,
    preventing mid-sentence cuts or amputated words when adapting long stories into comic panels.
    
    Parameters:
        text (str): The full story or remaining story text.
        target_size (int): Target character length for the chunk (default: 5000).
        max_limit (int): Maximum allowable character length (default: 6500).
        
    Returns:
        tuple[str, int]: (chunk_text, consumed_offset)
            - chunk_text: Cleaned prose containing only complete sentences.
            - consumed_offset: Exact character index consumed from original text,
              ensuring request.story_text[consumed_offset:] aligns cleanly with the next sentence.
    """
    if not text:
        return "", 0
        
    text_len = len(text)
    if text_len <= target_size:
        return text.strip(), text_len

    effective_limit = min(max_limit, text_len)
    search_sub = text[:effective_limit]

    # Pattern identifying complete sentence boundaries:
    # 1. Terminal punctuation [.!?] optionally followed by closing quotes ["'”’]
    #    followed by whitespace, newline, or end-of-string
    # 2. Double newlines (paragraph boundaries)
    # 3. Single newlines followed by a dialogue dash, quote, or capital letter
    boundary_regex = re.compile(
        r'(?:[\.!\?]["\'”’]?|\n\n|\n(?=[—\-\"\'A-ZÀ-Ỹ]))(?:\s+|$)'
    )

    candidates = []
    for m in boundary_regex.finditer(search_sub):
        end_pos = m.end()
        # Candidate cut should leave a substantial chunk (at least 200 chars or 20% of target)
        if end_pos >= min(300, target_size // 3):
            candidates.append(end_pos)

    chosen_cut = None
    if candidates:
        after_target = [c for c in candidates if c >= target_size]
        before_target = [c for c in candidates if c < target_size]

        if after_target:
            after_cand = after_target[0]
            if before_target:
                before_cand = before_target[-1]
                dist_after = after_cand - target_size
                dist_before = target_size - before_cand
                if dist_after <= dist_before or dist_after <= 400:
                    chosen_cut = after_cand
                else:
                    chosen_cut = before_cand
            else:
                chosen_cut = after_cand
        elif before_target:
            chosen_cut = before_target[-1]

    if not chosen_cut:
        # Fallback 1: word boundary near target_size
        space_idx = search_sub.rfind(' ', 0, target_size)
        if space_idx > target_size * 0.5:
            chosen_cut = space_idx + 1
        else:
            chosen_cut = min(target_size, text_len)

    chunk_text = text[:chosen_cut].strip()
    return chunk_text, chosen_cut

@app.post("/api/comic/generate")
def create_comic(request: ComicRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    deduct_ref = None
    try:
        if not current_user:
            return JSONResponse(
                status_code=401,
                content={"status": "error", "message": "Bạn chưa đăng nhập. Vui lòng đăng nhập để chuyển thể truyện tranh.", "code": 401}
            )

        story = None
        if request.story_id and request.story_id > 0:
            story = db.query(Story).filter(
                Story.id == request.story_id,
                Story.user_id == current_user.id,
            ).first()

        # If story doesn't exist yet for this user or was written on client, auto-save the manuscript
        if not story:
            word_count = len(request.story_text.split())
            story = Story(
                user_id=current_user.id,
                refined_prompt="Chuyển thể truyện tranh",
                story_content=request.story_text,
                word_count=word_count
            )
            db.add(story)
            db.commit()
            db.refresh(story)

        # Server-authoritative coin deduction (16 xu)
        deduct_ok, deduct_ref, bal_after = deduct_coins(
            db=db,
            user_id=current_user.id,
            amount=COST_MANGA,
            action_type=ACTION_COMIC_GENERATE,
            description=f"Chuyển thể Manga - {COST_MANGA} xu",
            raise_on_insufficient=True
        )
        
        memory = _get_story_memory(story, db)
        
        # Adapt first chunk of story using sentence boundaries (up to ~5000-6500 chars)
        text_to_adapt, adapted_len = extract_sentence_bounded_chunk(request.story_text, target_size=5000, max_limit=6500)
            
        from agents.comic_agent import ComicDirectorAgent
        director = ComicDirectorAgent()
        script_data = director.generate_comic_script(text_to_adapt, memory=memory)
        
        comic = Comic(user_id=current_user.id, story_id=story.id, title="Comic Adaptation", adapted_offset=adapted_len)
        db.add(comic)
        db.commit()
        db.refresh(comic)
        
        panels_response = _save_panels(db, comic, script_data)
        has_more = len(request.story_text) > adapted_len
            
        return {
            "status": "success",
            "comic_id": comic.id,
            "panels": panels_response,
            "adapted_offset": adapted_len,
            "has_more": has_more
        }
    except HTTPException as he:
        return JSONResponse(
            status_code=he.status_code,
            content={
                "status": "error",
                "message": he.detail,
                "detail": he.detail,
                "code": he.status_code
            }
        )
    except Exception as e:
        if current_user and deduct_ref:
            try:
                refund_coins(
                    db=db,
                    user_id=current_user.id,
                    amount=COST_MANGA,
                    reason=ACTION_REFUND_FAILED,
                    reference_id=deduct_ref,
                    description=f"Hoàn {COST_MANGA} xu do sự cố tạo truyện tranh: {str(e)[:100]}"
                )
            except Exception as refund_err:
                print(f"Compensating rollback error: {refund_err}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Lỗi tạo truyện tranh: {str(e)}"}

@app.post("/api/comic/continue")
def continue_comic(request: ComicContinueRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if not current_user:
            return {"status": "error", "message": "Bạn chưa đăng nhập."}

        comic = db.query(Comic).filter(
            Comic.id == request.comic_id,
            Comic.user_id == current_user.id,
        ).first()
        if not comic:
            return {"status": "error", "message": "Không tìm thấy truyện tranh."}
        
        current_offset = comic.adapted_offset or 0
        remaining_text = request.story_text[current_offset:]
        
        if len(remaining_text.strip()) < 50:
            return {"status": "error", "message": "Nội dung truyện chữ chưa được viết thêm. Hãy quay lại viết tiếp truyện chữ trước khi tạo thêm truyện tranh.", "no_more_text": True}
        
        existing_panels = db.query(ComicPanel).filter(
            ComicPanel.comic_id == comic.id
        ).order_by(ComicPanel.panel_index).all()
        
        previous_summary = " -> ".join([
            f"Panel {p.panel_index}: {p.dialogue_text}" 
            for p in existing_panels[-6:] if p.dialogue_text
        ])
        max_index = max([p.panel_index for p in existing_panels]) if existing_panels else 0
        
        story = db.query(Story).filter(Story.id == comic.story_id).first()
        memory = _get_story_memory(story, db)
        
        # Adapt continuation chunk using sentence boundaries (up to ~5000-6500 chars)
        new_text, chunk_len = extract_sentence_bounded_chunk(remaining_text, target_size=5000, max_limit=6500)
        
        from agents.comic_agent import ComicDirectorAgent
        director = ComicDirectorAgent()
        script_data = director.generate_continuation(previous_summary, new_text, memory=memory)
        
        panels_response = _save_panels(db, comic, script_data, start_index=max_index)
        
        comic.adapted_offset = current_offset + chunk_len
        db.commit()
        
        has_more = len(request.story_text) > comic.adapted_offset
        
        return {
            "status": "success",
            "comic_id": comic.id,
            "panels": panels_response,
            "adapted_offset": comic.adapted_offset,
            "has_more": has_more
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Lỗi tiếp tục truyện tranh: {str(e)}"}

@app.get("/api/comic/image/{panel_id}")
@app.get("/api/comics/panels/{panel_id}/image")
def get_comic_image(panel_id: int, retry: int = 0, db: Session = Depends(get_db)):
    """Proxies comic panel image generation with local disk cache and image-provider fallback."""
    panel = db.query(ComicPanel).filter(ComicPanel.id == panel_id).first()
    if not panel:
        return Response(status_code=404)
        
    try:
        story_id = int((panel.comic.story_id if panel.comic else None) or panel.comic_id or 1)
        comic_seed = get_deterministic_comic_seed(story_id)
        story = db.query(Story).filter(Story.id == story_id).first()
        memory = _get_story_memory(story, db)
        bible = getattr(memory, "story_bible", None)
        panel_id = int(panel.id)
        img_bytes, media_type = get_cached_or_generate_image(
            panel_id,
            str(panel.image_prompt or "monochrome manga illustration of a character in the story setting"),
            seed=comic_seed,
            story_id=story_id,
            cultural_tier=getattr(bible, "cultural_tier", None),
            narrative_mode=getattr(bible, "narrative_mode", None),
            genre=str(getattr(bible, "genre", "") or (story.genre if story else "") or ""),
            force_refresh=retry > 0,
        )
        headers = {"Cache-Control": "no-store"} if retry > 0 else None
        return Response(content=img_bytes, media_type=media_type, headers=headers)
    except Exception as e:
        print(f"[Comic Image] Generation failed for panel {panel_id}: {e}")
        return JSONResponse(
            status_code=503,
            content={"detail": "Image generation failed. Retry to request a fresh render."},
            headers={"Cache-Control": "no-store"},
        )


@app.post("/api/chat")
async def chat_with_assistant(request: ChatRequest, current_user: User = Depends(get_current_user)):
    if not current_user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    try:
        gen = get_story_generator()
        response = gen.handle_chat_instruction(request.story_text, request.user_message)
        if request.story_id:
            db = SessionLocal()
            try:
                story = db.query(Story).filter(
                    Story.id == request.story_id,
                    Story.user_id == current_user.id,
                ).first()
                if story and response.get("new_story_content"):
                    addition = response["new_story_content"]
                    story.story_content = f"{story.story_content}\n\n{addition}" if story.story_content else addition
                    story.word_count = len(story.story_content.split())
                    db.commit()
            finally:
                db.close()
        return {"status": "success", "chat_reply": response.get("chat_reply", ""), "new_story_content": response.get("new_story_content", "")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ===== STORY MEMORY SYSTEM =====
from agents.story_memory import StoryBible, StoryMemory
from agents.memory_extractor import MemoryExtractor
from agents.copilot_agent import CopilotAgent

# Dual-tier session store backed by CacheManager
STORY_SESSIONS = {}

def get_story_session(session_id: str, current_user: User):
    if not session_id:
        return None

    cache_mgr = get_cache_manager()
    cached_data = cache_mgr.get_session(session_id)
    if cached_data and isinstance(cached_data, dict):
        try:
            mem = StoryMemory.from_dict(cached_data)
            STORY_SESSIONS[session_id] = mem
            return mem
        except Exception as e:
            print(f"[Cache] Deserialization error for session {session_id}: {e}")

    memory = STORY_SESSIONS.get(session_id)
    if memory or not current_user:
        return memory

    db = SessionLocal()
    try:
        story = db.query(Story).filter(
            Story.session_id == session_id,
            Story.user_id == current_user.id,
        ).first()
        if not story or not story.memory_data:
            return None

        memory = StoryMemory.from_dict(json.loads(story.memory_data))
        STORY_SESSIONS[session_id] = memory
        cache_mgr.set_session(session_id, memory.to_dict(), ttl=86400)
        return memory
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Session restore error: {e}")
        return None
    finally:
        db.close()

def memory_json(memory: StoryMemory) -> str:
    return json.dumps(memory.to_dict(), ensure_ascii=False)

copilot = None
def get_copilot():
    global copilot
    if copilot is None:
        copilot = CopilotAgent()
    return copilot


memory_extractor = None
def get_memory_extractor():
    global memory_extractor
    if memory_extractor is None:
        memory_extractor = MemoryExtractor()
    return memory_extractor

class InitStoryRequest(BaseModel):
    refined_prompt: str
    story_length: str = "long"

class ChapterRequest(BaseModel):
    session_id: str
    user_instruction: str = ""

class EndStoryRequest(BaseModel):
    session_id: str

class CopilotEventRequest(BaseModel):
    session_id: str
    event_type: str
    event_data: str
    story_id: int | None = None
    selected_text: str | None = None
    cursor_position: int | None = None

@app.post("/api/copilot-event")
def copilot_event(request: CopilotEventRequest, current_user: User = Depends(get_current_user)):
    try:
        # Auth check FIRST — before any session or DB query
        if not current_user:
            return JSONResponse(status_code=401, content={"status": "error", "message": "Chưa đăng nhập"})

        memory = get_story_session(request.session_id, current_user)
        db = SessionLocal()
        try:
            story_query = db.query(Story).filter(Story.user_id == current_user.id)
            if request.story_id:
                story_query = story_query.filter(Story.id == request.story_id)
            else:
                story_query = story_query.filter(Story.session_id == request.session_id)
            story = story_query.first()
            if not story:
                return JSONResponse(status_code=404, content={"status": "error", "message": "Không tìm thấy phiên truyện hoặc không có quyền truy cập."})
            if memory is None and story.memory_data:
                memory = StoryMemory.from_dict(json.loads(story.memory_data))
        finally:
            db.close()
        
        agent = get_copilot()
        event_data_to_pass = request.event_data
        if request.selected_text or request.cursor_position is not None:
            try:
                parsed = json.loads(request.event_data)
                if isinstance(parsed, dict):
                    if request.selected_text and "selected_text" not in parsed:
                        parsed["selected_text"] = request.selected_text
                    if request.cursor_position is not None and "cursor_position" not in parsed:
                        parsed["cursor_position"] = request.cursor_position
                    event_data_to_pass = json.dumps(parsed, ensure_ascii=False)
            except Exception:
                pass
        # Copilot process the event and decides the action
        result = agent.process_event(request.event_type, event_data_to_pass, memory)
        
        # Safe print for Windows
        try:
            print(f"--- MASTER CONTROLLER THOUGHT ---")
            print(str(result.get('thought', 'No thought')).encode('utf-8', 'replace').decode('utf-8'))
            print(f"ACTION: {result.get('action')}")
            print(f"---------------------------------")
        except:
            pass
            
        
        # If story was directly modified, persist to database
        if result.get("action") == "edit_story_direct":
            if "action_params" not in result or not isinstance(result.get("action_params"), dict):
                result["action_params"] = {}
            params = result["action_params"]
            if "updated_story_content" not in params and "updated_story_content" in result:
                params["updated_story_content"] = result["updated_story_content"]
            updated_content = params.get("updated_story_content")
            if updated_content:
                from agents.copilot_agent import unwrap_story_prose
                clean_prose = unwrap_story_prose(updated_content)
                params["updated_story_content"] = clean_prose
                updated_content = clean_prose

                # Database Quarantine Guard: strictly verify clean prose before persisting
                is_raw_json = (
                    updated_content.strip().startswith("{")
                    or '"updated_story_content"' in updated_content
                    or '"action":' in updated_content
                )
                if is_raw_json:
                    clean_prose = unwrap_story_prose(updated_content)
                    if not clean_prose.strip().startswith("{") and '"updated_story_content"' not in clean_prose:
                        updated_content = clean_prose
                        params["updated_story_content"] = clean_prose
                    else:
                        print("[Copilot DB Guard] Raw JSON detected in edit_story_direct; skipping DB overwrite to prevent corruption.")
                        updated_content = None
                        params["updated_story_content"] = None
                # Historical Grounding Quarantine Guard: strictly verify historical truth before persisting
                if updated_content and HistoricalGroundingGatekeeper is not None:
                    c_mode = NarrativeMode.CHINH_SU
                    if auto_detect_narrative_mode is not None:
                        c_mode, _ = auto_detect_narrative_mode(updated_content)
                    c_valid, c_violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                        updated_content, mode=c_mode
                    )
                    if not c_valid:
                        print(f"[Copilot DB Guard] Historical distortion detected: {c_violations}")
                        return JSONResponse(
                            status_code=422,
                            content={
                                "status": "error",
                                "error": "HISTORICAL_VIOLATION",
                                "message": f"Hệ thống không thể cập nhật bản thảo vì vi phạm lịch sử Việt Nam: {'; '.join(c_violations)}",
                                "violations": c_violations
                            }
                        )

                if updated_content:
                    db = SessionLocal()
                    try:
                        story_query = db.query(Story).filter(Story.user_id == current_user.id)
                        if request.story_id:
                            story_query = story_query.filter(Story.id == request.story_id)
                        else:
                            story_query = story_query.filter(Story.session_id == request.session_id)
                        story = story_query.first()
                        if story:
                            story.story_content = updated_content
                            story.word_count = len(updated_content.split())
                            db.commit()
                            cache_mgr = get_cache_manager()
                            cache_mgr.delete_draft(story.id)
                            if memory:
                                cache_mgr.set_session(request.session_id, memory.to_dict(), ttl=86400)
                    except Exception as e:
                        print(f"[Copilot DB Update Error] {e}")
                    finally:
                        db.close()

        # Save memory changes to DB
        if memory and current_user:
            db = SessionLocal()
            try:
                story_query = db.query(Story).filter(Story.user_id == current_user.id)
                if request.story_id:
                    story_query = story_query.filter(Story.id == request.story_id)
                else:
                    story_query = story_query.filter(Story.session_id == request.session_id)
                story = story_query.first()
                if story:
                    story.memory_data = memory_json(memory)
                    db.commit()
                    cache_mgr = get_cache_manager()
                    cache_mgr.set_session(request.session_id, memory.to_dict(), ttl=86400)
            except Exception as e:
                pass
            finally:
                db.close()
                
        return {"status": "success", "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
    
@app.post("/api/init-story")
def init_story(
    request: InitStoryRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deduct_ref = None
    try:
        # Server-authoritative coin deduction (8 xu for Chapter 1)
        if current_user:
            deduct_ok, deduct_ref, bal_after = deduct_coins(
                db=db,
                user_id=current_user.id,
                amount=COST_SHORT_STORY,
                action_type=ACTION_STORY_SHORT,
                description=f"Khởi tạo truyện chương 1 - {COST_SHORT_STORY} xu",
                raise_on_insufficient=True
            )

        extractor = get_memory_extractor()
        gen = get_story_generator()

        # Step 1: Extract Story Bible from refined_prompt
        bible = extractor.extract_bible(request.refined_prompt)

        # Step 2: Create Memory with Bible
        memory = StoryMemory(story_bible=bible)
        session_id = memory.session_id

        # Pre-allocate Story record in DB at stream inception for both guests and authenticated users
        pre_story_id = None
        db_pre = SessionLocal()
        try:
            new_story = Story(
                session_id=session_id,
                user_id=current_user.id if current_user else None,
                refined_prompt=request.refined_prompt,
                story_content="",
                word_count=0,
                bible_data=json.dumps(memory.story_bible.to_dict(), ensure_ascii=False) if memory.story_bible else None,
                memory_data=memory_json(memory)
            )
            db_pre.add(new_story)
            db_pre.commit()
            db_pre.refresh(new_story)
            pre_story_id = new_story.id
        except Exception as pre_err:
            print(f"[Pre-allocate Story DB Error in init-story] {pre_err}")
        finally:
            db_pre.close()

        # Step 3: Generate Chapter 1 (streaming)
        def stream_chapter_1():
            chapter_text = ""
            saved_story_id = pre_story_id
            # Yield pre-allocated story_id immediately at stream inception
            if pre_story_id:
                yield f"[STORY_ID:{pre_story_id}]\n\n"

            try:
                for chunk in gen.generate_chapter_stream(memory):
                    chapter_text += chunk
                    yield chunk
            except Exception as e:
                persist_partial_story(session_id, pre_story_id, chapter_text)
                # Compensating transaction rollback: 100% refund on AI generation failure
                if current_user and deduct_ref:
                    rollback_db = SessionLocal()
                    try:
                        refund_coins(
                            db=rollback_db,
                            user_id=current_user.id,
                            amount=COST_SHORT_STORY,
                            reason=ACTION_REFUND_FAILED,
                            reference_id=deduct_ref,
                            description=f"Hoàn {COST_SHORT_STORY} xu do sự cố sinh chương 1: {str(e)[:100]}"
                        )
                    except Exception as refund_err:
                        print(f"Compensating rollback error: {refund_err}")
                    finally:
                        rollback_db.close()
                yield f"\n\n[GENERATION_ERROR:{safe_generation_error(e, 'sinh chương')}]"
                return

            # Step 4: Update memory with chapter 1
            memory.append_chapter(chapter_text)
            try:
                extractor.extract_memory(chapter_text, memory)
            except Exception as e:
                print(f"Memory extraction error: {e}")

            # Store session
            STORY_SESSIONS[session_id] = memory
            cache_mgr = get_cache_manager()
            cache_mgr.set_session(session_id, memory.to_dict(), ttl=86400)

            # Save/update in DB
            word_count = len(chapter_text.split())
            db = SessionLocal()
            try:
                if pre_story_id:
                    st = db.query(Story).filter(Story.id == pre_story_id).first()
                    if st:
                        st.story_content = chapter_text
                        st.word_count = word_count
                        if memory.story_bible:
                            st.bible_data = json.dumps(memory.story_bible.to_dict(), ensure_ascii=False)
                        st.memory_data = memory_json(memory)
                        db.commit()
                elif word_count > 10:
                    new_story = Story(
                        session_id=session_id,
                        user_id=current_user.id if current_user else None,
                        refined_prompt=request.refined_prompt,
                        story_content=chapter_text,
                        word_count=word_count,
                        bible_data=json.dumps(memory.story_bible.to_dict(), ensure_ascii=False) if memory.story_bible else None,
                        memory_data=memory_json(memory)
                    )
                    db.add(new_story)
                    db.commit()
                    db.refresh(new_story)
                    saved_story_id = new_story.id
            except Exception as e:
                print(f"DB Error: {e}")
            finally:
                db.close()

            # Yield session_id at the end as a special marker
            yield f"\n\n[SESSION_ID:{session_id}]"
            if saved_story_id:
                yield f"\n\n[STORY_ID:{saved_story_id}]"

        return StreamingResponse(stream_chapter_1(), media_type="text/plain")
    except HTTPException:
        if current_user and deduct_ref:
            refund_generation_charge(
                db, current_user.id, deduct_ref, COST_SHORT_STORY, "khởi tạo truyện"
            )
        raise
    except Exception as e:
        if current_user and deduct_ref:
            refund_generation_charge(
                db, current_user.id, deduct_ref, COST_SHORT_STORY, "khởi tạo truyện"
            )
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/generate-chapter")
def generate_chapter(request: ChapterRequest, current_user: User = Depends(get_current_user)):
    deduct_ref = None
    try:
        # Auth check FIRST — before any session query or coin deduction
        if not current_user:
            return JSONResponse(status_code=401, content={"status": "error", "message": "Chưa đăng nhập"})

        memory = get_story_session(request.session_id, current_user)
        if not memory:
            return JSONResponse(status_code=404, content={"status": "error", "message": "Session khong ton tai hoac da het han."})
        db = SessionLocal()
        try:
            story = db.query(Story).filter(
                Story.session_id == request.session_id,
                Story.user_id == current_user.id,
            ).first()
            if not story:
                return JSONResponse(status_code=404, content={"status": "error", "message": "Không tìm thấy phiên truyện hoặc không có quyền truy cập."})
        finally:
            db.close()

        # Server-authoritative coin deduction (8 xu per chapter)
        db_deduct = SessionLocal()
        try:
            deduct_ok, deduct_ref, bal_after = deduct_coins(
                db=db_deduct,
                user_id=current_user.id,
                amount=COST_SHORT_STORY,
                action_type=ACTION_STORY_SHORT,
                description=f"Sinh chương mới - {COST_SHORT_STORY} xu",
                raise_on_insufficient=True
            )
        finally:
            db_deduct.close()

        gen = get_story_generator()
        extractor = get_memory_extractor()

        def stream_next_chapter():
            chapter_text = ""
            try:
                for chunk in gen.generate_chapter_stream(memory, request.user_instruction):
                    chapter_text += chunk
                    yield chunk
            except Exception as e:
                persist_partial_story(request.session_id, None, chapter_text)
                # Compensating transaction rollback: 100% refund on AI generation failure
                if current_user and deduct_ref:
                    rollback_db = SessionLocal()
                    try:
                        refund_coins(
                            db=rollback_db,
                            user_id=current_user.id,
                            amount=COST_SHORT_STORY,
                            reason=ACTION_REFUND_FAILED,
                            reference_id=deduct_ref,
                            description=f"Hoàn {COST_SHORT_STORY} xu do sự cố sinh chương: {str(e)[:100]}"
                        )
                    except Exception as refund_err:
                        print(f"Compensating rollback error: {refund_err}")
                    finally:
                        rollback_db.close()
                yield f"\n\n[GENERATION_ERROR:{safe_generation_error(e, 'sinh chương')}]"
                return

            # Update memory
            memory.append_chapter(chapter_text)
            try:
                extractor.extract_memory(chapter_text, memory)
            except Exception as e:
                print(f"Memory extraction error: {e}")

            # Update session
            STORY_SESSIONS[request.session_id] = memory
            cache_mgr = get_cache_manager()
            cache_mgr.set_session(request.session_id, memory.to_dict(), ttl=86400)

            # Update story in DB
            if current_user:
                db_up = SessionLocal()
                try:
                    story = db_up.query(Story).filter(Story.session_id == request.session_id).first()
                    if story:
                        story.story_content = memory.get_full_story()
                        story.word_count = len(story.story_content.split())
                        story.memory_data = memory_json(memory)
                        db_up.commit()
                        cache_mgr.delete_draft(story.id)
                except Exception as e:
                    print(f"DB Error: {e}")
                finally:
                    db_up.close()

        return StreamingResponse(stream_next_chapter(), media_type="text/plain")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/end-story")
def end_story(request: EndStoryRequest, current_user: User = Depends(get_current_user)):
    try:
        # Auth check FIRST — before any session or DB query
        if not current_user:
            return JSONResponse(status_code=401, content={"status": "error", "message": "Chưa đăng nhập"})

        memory = get_story_session(request.session_id, current_user)
        if not memory:
            return JSONResponse(status_code=404, content={"status": "error", "message": "Session khong ton tai."})
        db = SessionLocal()
        try:
            story = db.query(Story).filter(
                Story.session_id == request.session_id,
                Story.user_id == current_user.id,
            ).first()
            if not story:
                return JSONResponse(status_code=404, content={"status": "error", "message": "Không tìm thấy phiên truyện hoặc không có quyền truy cập."})
        finally:
            db.close()

        gen = get_story_generator()

        def stream_ending():
            ending_text = ""
            try:
                for chunk in gen.generate_ending_stream(memory):
                    ending_text += chunk
                    yield chunk
            except Exception as e:
                persist_partial_story(request.session_id, None, ending_text)
                yield f"\n\n[GENERATION_ERROR:{safe_generation_error(e, 'viết đoạn kết')}]"
                return

            memory.append_chapter(ending_text)

            # Final DB save
            if current_user:
                db = SessionLocal()
                try:
                    story = db.query(Story).filter(Story.session_id == request.session_id).first()
                    if story:
                        story.story_content = memory.get_full_story()
                        story.word_count = len(story.story_content.split())
                        story.memory_data = memory_json(memory)
                        db.commit()
                        cache_mgr = get_cache_manager()
                        cache_mgr.delete_draft(story.id)
                except Exception as e:
                    print(f"DB Error: {e}")
                finally:
                    db.close()

            # Clean up session
            if request.session_id in STORY_SESSIONS:
                del STORY_SESSIONS[request.session_id]
            cache_mgr = get_cache_manager()
            cache_mgr.delete_session(request.session_id)

        return StreamingResponse(stream_ending(), media_type="text/plain")
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============ FRONTEND STATIC SERVING (NEXT.JS EXPORT) ============
from fastapi.staticfiles import StaticFiles

frontend_out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "out"))
if os.path.isdir(frontend_out_dir):
    print(f"[NarrAI] Mounting Next.js Frontend from: {frontend_out_dir}")
    app.mount("/", StaticFiles(directory=frontend_out_dir, html=True), name="frontend")
else:
    print(f"[NarrAI] Frontend out directory not found at: {frontend_out_dir}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
