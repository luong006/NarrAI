"""
NarrAI Coins & Banking API Router
Endpoints:
- GET  /balance: Retrieve current user's authenticated coin balance
- GET  /transactions: Audit history of user transactions
- POST /verify-ledger: Cryptographic SHA-256 chain verification
- POST /claim-trial: Multi-Signal Anti-Clone Guard trial coin claim
- POST /topup: Add coins to account
- POST /deduct: Server-authoritative coin deduction
- POST /refund: Compensating transaction rollback
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional, Any, List
from sqlalchemy.orm import Session

from db.models import get_db, User, CoinTransaction
from auth import decode_access_token
from services.cache_service import get_cache_manager
from services.banking_service import (
    deduct_coins,
    refund_coins,
    topup_coins,
    verify_ledger_integrity,
    register_device_and_get_initial_coins,
    get_action_cost,
    get_story_cost,
    COST_SHORT_STORY,
    COST_MEDIUM_STORY,
    COST_LONG_STORY,
    COST_EDIT,
    COST_MANGA,
    STANDARD_TOPUP_COINS,
    INITIAL_TRIAL_COINS,
    ACTION_REFUND_FAILED
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)

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

# ==================== PYDANTIC SCHEMAS ====================

class VerifyLedgerRequest(BaseModel):
    user_id: Optional[int] = None

class ClaimTrialRequest(BaseModel):
    fingerprint: Optional[Any] = None
    canvas_hash: Optional[str] = None
    webgl_hash: Optional[str] = None
    audio_hash: Optional[str] = None
    screen_specs: Optional[str] = None

class TopupRequest(BaseModel):
    amount: int = STANDARD_TOPUP_COINS
    description: Optional[str] = "Nạp xu tài khoản"
    reference_id: Optional[str] = None

class DeductRequest(BaseModel):
    action_type: str
    story_length: Optional[str] = None
    description: Optional[str] = None
    reference_id: Optional[str] = None

class RefundRequest(BaseModel):
    amount: int
    reason: Optional[str] = ACTION_REFUND_FAILED
    description: Optional[str] = None
    reference_id: Optional[str] = None

# ==================== API ENDPOINTS ====================

@router.get("/balance")
async def get_balance(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the authenticated user's current coin balance directly from database.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập (Authentication required)"
        )
    
    user = db.query(User).filter(User.id == current_user.id).first()
    coins = user.coins if user and user.coins is not None else 0
    
    return {
        "status": "success",
        "user_id": current_user.id,
        "username": current_user.username,
        "coins": coins,
        "balance": coins
    }

@router.get("/transactions")
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns transaction history with cryptographic hashes for auditing.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập (Authentication required)"
        )

    query = (
        db.query(CoinTransaction)
        .filter(CoinTransaction.user_id == current_user.id)
        .order_by(CoinTransaction.id.desc())
    )
    total = query.count()
    txs = query.offset(offset).limit(min(limit, 100)).all()

    items = []
    for tx in txs:
        items.append({
            "id": tx.id,
            "user_id": tx.user_id,
            "amount": tx.amount,
            "balance_after": tx.balance_after,
            "action_type": tx.action_type,
            "tx_type": tx.action_type,
            "description": tx.description,
            "reference_id": tx.reference_id,
            "prev_hash": tx.prev_hash,
            "tx_hash": tx.tx_hash,
            "timestamp": tx.timestamp,
            "created_at": tx.created_at.isoformat() if tx.created_at else None
        })

    return {
        "status": "success",
        "total": total,
        "limit": limit,
        "offset": offset,
        "transactions": items
    }

@router.post("/verify-ledger")
async def verify_ledger(
    request: VerifyLedgerRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Audits the cryptographic SHA-256 chain integrity of the ledger.
    Detects any manual database tampering, broken links, or mathematical discrepancies.
    """
    target_user_id = request.user_id
    if target_user_id is None:
        if current_user:
            target_user_id = current_user.id
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Vui lòng cung cấp user_id hoặc đăng nhập để kiểm toán sổ cái."
            )

    is_valid, msg = verify_ledger_integrity(db, user_id=target_user_id)
    return {
        "status": "success" if is_valid else "tampered",
        "is_valid": is_valid,
        "message": msg,
        "user_id": target_user_id
    }

@router.post("/claim-trial")
async def claim_trial(
    request: Request,
    body: ClaimTrialRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates client hardware fingerprint and IP /24 subnet:
    - Fresh device & subnet = 8 free trial coins.
    - Duplicate device or throttled subnet = 0 coins.
    """
    # Extract client IP
    client_ip = (
        request.headers.get("x-forwarded-for")
        or request.headers.get("x-real-ip")
        or (request.client.host if request.client else "127.0.0.1")
    )
    
    # Formulate fingerprint data
    fp_data = body.fingerprint
    if fp_data is None:
        fp_data = {
            "canvas_hash": body.canvas_hash or "",
            "webgl_hash": body.webgl_hash or "",
            "audio_hash": body.audio_hash or "",
            "screen_specs": body.screen_specs or ""
        }

    user_id = current_user.id if current_user else None
    coins_granted = register_device_and_get_initial_coins(
        db=db,
        client_ip=client_ip,
        fingerprint_data=fp_data,
        user_id=user_id
    )

    new_balance = 0
    if current_user:
        user = db.query(User).filter(User.id == current_user.id).first()
        new_balance = user.coins if user and user.coins is not None else 0
    else:
        new_balance = coins_granted

    if coins_granted > 0:
        return {
            "status": "success",
            "coins_granted": coins_granted,
            "new_balance": new_balance,
            "message": f"Chúc mừng! Bạn đã nhận thành công {coins_granted} xu tân thủ trải nghiệm."
        }
    else:
        return {
            "status": "duplicate_or_throttled",
            "coins_granted": 0,
            "new_balance": new_balance,
            "message": "Thiết bị hoặc dải mạng IP này đã từng nhận thưởng tân thủ. Số dư được cấp: 0 xu."
        }

@router.post("/topup")
async def topup(
    body: TopupRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Standard top-up endpoint (default: 100 coins = 100k VND).
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập (Authentication required)"
        )

    if body.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Số xu nạp phải lớn hơn 0."
        )

    ok, tx_hash, new_balance = topup_coins(
        db=db,
        user_id=current_user.id,
        amount=body.amount,
        description=body.description or f"Nạp {body.amount} xu vào tài khoản",
        reference_id=body.reference_id
    )

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Nạp xu thất bại: {tx_hash}"
        )

    return {
        "status": "success",
        "amount": body.amount,
        "new_balance": new_balance,
        "tx_hash": tx_hash,
        "message": f"Nạp thành công {body.amount} xu vào tài khoản."
    }

@router.post("/deduct")
async def deduct(
    body: DeductRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Server-Authoritative Coin Deduction endpoint.
    Client cannot dictate costs; server computes cost strictly from action and length.
    Rejects with HTTP 402 if balance is insufficient.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập (Authentication required)"
        )

    # Server calculates authoritative cost
    cost = get_action_cost(body.action_type, body.story_length)

    ok, tx_hash, new_balance = deduct_coins(
        db=db,
        user_id=current_user.id,
        amount=cost,
        action_type=body.action_type,
        description=body.description or f"Thanh toán {body.action_type}",
        reference_id=body.reference_id,
        raise_on_insufficient=True
    )

    return {
        "status": "success",
        "action_type": body.action_type,
        "cost": cost,
        "new_balance": new_balance,
        "tx_hash": tx_hash,
        "message": f"Thanh toán thành công {cost} xu cho {body.action_type}."
    }

@router.post("/refund")
async def refund(
    body: RefundRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compensating transaction refund endpoint.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập (Authentication required)"
        )

    if body.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Số xu hoàn lại phải lớn hơn 0."
        )

    ok, tx_hash, new_balance = refund_coins(
        db=db,
        user_id=current_user.id,
        amount=body.amount,
        reason=body.reason or ACTION_REFUND_FAILED,
        description=body.description or f"Hoàn lại {body.amount} xu",
        reference_id=body.reference_id
    )

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hoàn xu thất bại: {tx_hash}"
        )

    return {
        "status": "success",
        "refunded_amount": body.amount,
        "new_balance": new_balance,
        "tx_hash": tx_hash,
        "message": f"Đã hoàn lại {body.amount} xu vào tài khoản của bạn."
    }
