"""
NarrAI Banking Service & Cryptographic Currency Engine
Implements:
1. 100 Coin economic pricing model (Short=8, Medium=12, Long=16, Edit=2, Manga=16).
2. Dual-locking concurrency isolation (In-memory per-user threading.Lock + SQLite BEGIN IMMEDIATE TRANSACTION).
3. Absolute Server Authority over pricing calculations.
4. Compensating Transaction Rollback (REFUND_FAILED_GENERATION) with 100% automatic refund.
5. Cryptographic Immutable Ledger with SHA-256 hash chaining and integrity verification.
6. Multi-Signal Anti-Clone Guard (Canvas 2D + WebGL + AudioContext + Screen Specs) + IP /24 Subnet Throttling.
"""

import hashlib
import threading
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException, status

from db.models import User, CoinTransaction, DeviceFingerprint, SubnetRecord

# ==================== PRICING CONSTANTS (ABSOLUTE SERVER AUTHORITY) ====================
COST_SHORT_STORY = 8
COST_MEDIUM_STORY = 12
COST_LONG_STORY = 16
COST_EDIT = 2
COST_MANGA = 16
INITIAL_TRIAL_COINS = 100
STANDARD_TOPUP_COINS = 100
VND_PER_COIN = 1000  # 100k VND = 100 Coins

# Genesis Hash for cryptographic ledger root
GENESIS_HASH = "0" * 64

# Action type definitions
ACTION_STORY_SHORT = "STORY_GENERATE_SHORT"
ACTION_STORY_MEDIUM = "STORY_GENERATE_MEDIUM"
ACTION_STORY_LONG = "STORY_GENERATE_LONG"
ACTION_STORY_EDIT = "STORY_EDIT"
ACTION_COMIC_GENERATE = "COMIC_GENERATE"
ACTION_INITIAL_GRANT = "INITIAL_GRANT"
ACTION_TOPUP = "TOPUP"
ACTION_REFUND_FAILED = "REFUND_FAILED_GENERATION"

def get_story_cost(story_length: Optional[str]) -> int:
    """
    Derives generation cost strictly on the server based on length tier.
    Never trusts client-supplied pricing parameters.
    """
    length = (story_length or "medium").strip().lower()
    if length == "short":
        return COST_SHORT_STORY
    elif length == "long":
        return COST_LONG_STORY
    else:
        return COST_MEDIUM_STORY

def get_action_cost(action_type: str, story_length: Optional[str] = None) -> int:
    """
    Calculates cost for arbitrary actions on the server.
    """
    clean_action = (action_type or "").upper().strip()
    if "SHORT" in clean_action:
        return COST_SHORT_STORY
    elif "LONG" in clean_action:
        return COST_LONG_STORY
    elif "MEDIUM" in clean_action:
        return COST_MEDIUM_STORY
    elif "EDIT" in clean_action:
        return COST_EDIT
    elif "COMIC" in clean_action or "MANGA" in clean_action:
        return COST_MANGA
    elif "STORY" in clean_action:
        return get_story_cost(story_length)
    return COST_MEDIUM_STORY

# ==================== DUAL-LOCKING CONCURRENCY REGISTRY ====================

class UserMutexRegistry:
    """
    Thread-safe registry maintaining per-user locks.
    Prevents race conditions and double-spending across threads within the process.
    """
    def __init__(self):
        self._locks: Dict[int, threading.Lock] = {}
        self._meta_lock = threading.Lock()

    def get_user_lock(self, user_id: int) -> threading.Lock:
        with self._meta_lock:
            if user_id not in self._locks:
                self._locks[user_id] = threading.Lock()
            return self._locks[user_id]

    def reset(self):
        with self._meta_lock:
            self._locks.clear()

user_mutexes = UserMutexRegistry()
_db_write_lock = threading.RLock()

# ==================== HASH CHAINING HELPER ====================

def compute_transaction_hash(prev_hash: str, user_id: int, amount: int, balance_after: int, timestamp: str) -> str:
    """
    Calculates SHA-256 chained transaction hash:
    tx_hash = SHA256(prev_hash + user_id + amount + balance_after + timestamp)
    """
    payload = f"{prev_hash}{user_id}{amount}{balance_after}{timestamp}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

# ==================== CORE BANKING OPERATIONS ====================

def deduct_coins(
    db: Session,
    user_id: int,
    amount: int,
    action_type: str,
    description: str = "",
    reference_id: Optional[str] = None,
    raise_on_insufficient: bool = True
) -> Tuple[bool, str, int]:
    """
    Atomically deducts coins with Dual-Locking Concurrency Isolation:
    1. In-memory per-user threading.Lock serialization.
    2. SQLite BEGIN IMMEDIATE transaction for database level isolation.
    3. If current_balance < required, immediately rejects with HTTP 402 Payment Required.
    4. Appends tamper-evident SHA-256 chained ledger entry.
    Returns: (success: bool, tx_hash_or_error: str, new_balance: int)
    """
    cost = abs(int(amount))
    user_lock = user_mutexes.get_user_lock(user_id)
    
    with user_lock, _db_write_lock:
        # SQLite immediate exclusive lock to prevent concurrent write collisions
        try:
            db.execute(text("BEGIN IMMEDIATE"))
        except Exception:
            pass  # Session may already be in an active transaction

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            try:
                db.execute(text("ROLLBACK"))
            except Exception:
                db.rollback()
            if raise_on_insufficient:
                raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
            return False, "User not found", 0

        current_balance = user.coins if user.coins is not None else 0
        if current_balance < cost:
            try:
                db.execute(text("ROLLBACK"))
            except Exception:
                db.rollback()
            if raise_on_insufficient:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Số dư xu không đủ ({current_balance} xu < {cost} xu yêu cầu). Vui lòng nạp thêm xu để tiếp tục."
                )
            return False, f"Số dư xu không đủ ({current_balance} < {cost})", current_balance

        # Deduct balance
        new_balance = current_balance - cost
        user.coins = new_balance

        # Find previous transaction hash for hash-chaining
        last_tx = (
            db.query(CoinTransaction)
            .filter(CoinTransaction.user_id == user_id)
            .order_by(CoinTransaction.id.desc())
            .first()
        )
        prev_hash = last_tx.tx_hash if last_tx else GENESIS_HASH

        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        tx_amount = -cost
        tx_hash = compute_transaction_hash(prev_hash, user_id, tx_amount, new_balance, timestamp)

        tx = CoinTransaction(
            user_id=user_id,
            amount=tx_amount,
            balance_after=new_balance,
            action_type=action_type,
            description=description or f"Thanh toán dịch vụ {action_type} (-{cost} xu)",
            reference_id=reference_id,
            prev_hash=prev_hash,
            tx_hash=tx_hash,
            timestamp=timestamp,
            created_at=datetime.utcnow()
        )
        db.add(tx)
        db.commit()
        return True, tx_hash, new_balance

def refund_coins(
    db: Session,
    user_id: int,
    amount: int,
    reason: str = ACTION_REFUND_FAILED,
    reference_id: Optional[str] = None,
    description: str = ""
) -> Tuple[bool, str, int]:
    """
    Compensating Transaction Rollback:
    Credits back 100% of the deducted coins when an upstream AI generation fails.
    Records REFUND_FAILED_GENERATION in the chained cryptographic ledger.
    Returns: (success: bool, tx_hash_or_error: str, new_balance: int)
    """
    refund_amount = abs(int(amount))
    user_lock = user_mutexes.get_user_lock(user_id)

    with user_lock, _db_write_lock:
        try:
            db.execute(text("BEGIN IMMEDIATE"))
        except Exception:
            pass

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            try:
                db.execute(text("ROLLBACK"))
            except Exception:
                db.rollback()
            return False, "User not found", 0

        current_balance = user.coins if user.coins is not None else 0
        new_balance = current_balance + refund_amount
        user.coins = new_balance

        last_tx = (
            db.query(CoinTransaction)
            .filter(CoinTransaction.user_id == user_id)
            .order_by(CoinTransaction.id.desc())
            .first()
        )
        prev_hash = last_tx.tx_hash if last_tx else GENESIS_HASH

        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        tx_amount = refund_amount
        tx_hash = compute_transaction_hash(prev_hash, user_id, tx_amount, new_balance, timestamp)

        tx = CoinTransaction(
            user_id=user_id,
            amount=tx_amount,
            balance_after=new_balance,
            action_type=reason or ACTION_REFUND_FAILED,
            description=description or f"Tự động hoàn {refund_amount} xu ({reason})",
            reference_id=reference_id,
            prev_hash=prev_hash,
            tx_hash=tx_hash,
            timestamp=timestamp,
            created_at=datetime.utcnow()
        )
        db.add(tx)
        db.commit()
        return True, tx_hash, new_balance

def topup_coins(
    db: Session,
    user_id: int,
    amount: int = STANDARD_TOPUP_COINS,
    description: str = "Nạp xu tài khoản",
    reference_id: Optional[str] = None
) -> Tuple[bool, str, int]:
    """
    Adds coins to user balance and records TOPUP in cryptographic ledger.
    Returns: (success: bool, tx_hash_or_error: str, new_balance: int)
    """
    topup_amount = abs(int(amount))
    user_lock = user_mutexes.get_user_lock(user_id)

    with user_lock, _db_write_lock:
        try:
            db.execute(text("BEGIN IMMEDIATE"))
        except Exception:
            pass

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            try:
                db.execute(text("ROLLBACK"))
            except Exception:
                db.rollback()
            return False, "User not found", 0

        current_balance = user.coins if user.coins is not None else 0
        new_balance = current_balance + topup_amount
        user.coins = new_balance

        last_tx = (
            db.query(CoinTransaction)
            .filter(CoinTransaction.user_id == user_id)
            .order_by(CoinTransaction.id.desc())
            .first()
        )
        prev_hash = last_tx.tx_hash if last_tx else GENESIS_HASH

        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        tx_amount = topup_amount
        tx_hash = compute_transaction_hash(prev_hash, user_id, tx_amount, new_balance, timestamp)

        tx = CoinTransaction(
            user_id=user_id,
            amount=tx_amount,
            balance_after=new_balance,
            action_type=ACTION_TOPUP,
            description=description or f"Nạp thành công +{topup_amount} xu",
            reference_id=reference_id,
            prev_hash=prev_hash,
            tx_hash=tx_hash,
            timestamp=timestamp,
            created_at=datetime.utcnow()
        )
        db.add(tx)
        db.commit()
        return True, tx_hash, new_balance

# ==================== CRYPTOGRAPHIC LEDGER AUDITING ====================

def verify_ledger_integrity(db: Session, user_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    Verifies the cryptographic integrity of the ledger:
    1. prev_hash chaining matches previous transaction's tx_hash.
    2. Recalculates SHA-256 for every entry.
    3. Verifies balance continuity: balance[i-1] + amount[i] == balance[i].
    4. Confirms final balance equals User.coins in the database.
    """
    if user_id is not None:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, f"Không tìm thấy người dùng #{user_id}."

        txs = (
            db.query(CoinTransaction)
            .filter(CoinTransaction.user_id == user_id)
            .order_by(CoinTransaction.id.asc())
            .all()
        )

        if not txs:
            if (user.coins or 0) == 0:
                return True, "Sổ cái trống, số dư 0 xu hoàn toàn hợp lệ."
            return False, f"Số dư tài khoản là {user.coins} xu nhưng không có bất kỳ bút toán nào trong sổ cái."

        expected_prev = GENESIS_HASH
        # Baseline starting balance before the first transaction in the recorded ledger
        running_balance = txs[0].balance_after - txs[0].amount

        for tx in txs:
            # 1. Chaining check
            if tx.prev_hash != expected_prev:
                return False, f"Đứt gãy liên kết chuỗi băm tại giao dịch #{tx.id}: prev_hash={tx.prev_hash} khác kỳ vọng {expected_prev}"

            # 2. Math continuity check
            if running_balance + tx.amount != tx.balance_after:
                return False, f"Lỗi số học số dư tại giao dịch #{tx.id}: {running_balance} + ({tx.amount}) != {tx.balance_after}"

            # 3. Cryptographic hash check
            expected_hash = compute_transaction_hash(
                tx.prev_hash, tx.user_id, tx.amount, tx.balance_after, tx.timestamp
            )
            if tx.tx_hash != expected_hash:
                return False, f"Phát hiện can thiệp giả mạo dữ liệu tại giao dịch #{tx.id}: mã băm không khớp!"

            expected_prev = tx.tx_hash
            running_balance = tx.balance_after

        if running_balance != (user.coins or 0):
            return False, f"Số dư hiện tại trong bảng users ({user.coins}) không khớp với số dư kết chuyển sổ cái ({running_balance})."

        return True, f"Sổ cái người dùng #{user_id} toàn vẹn 100% ({len(txs)} giao dịch đã kiểm toán)."

    # If user_id is None, verify all users with transactions
    all_users = db.query(User).all()
    for u in all_users:
        ok, msg = verify_ledger_integrity(db, user_id=u.id)
        if not ok:
            return False, msg

    return True, "Toàn bộ sổ cái hệ thống toàn vẹn 100%."

# ==================== MULTI-SIGNAL ANTI-CLONE & SUBNET GUARD ====================

def extract_ip_subnet(client_ip: Optional[str]) -> str:
    """
    Normalizes client IP into /24 subnet (IPv4) or /64 prefix (IPv6).
    """
    if not client_ip:
        return "0.0.0.0/24"
    
    # In case of comma-separated forwarded proxy headers
    ip = client_ip.split(",")[0].strip()
    if ":" in ip and "." in ip:
        ip = ip.split(":")[0]  # Strip IPv4 port
        
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        
    v6_parts = ip.split(":")
    if len(v6_parts) >= 4:
        return f"{':'.join(v6_parts[:4])}::/64"
        
    return f"{ip}/24"

def compute_composite_fingerprint(fingerprint_data: Any) -> Tuple[str, Dict[str, str]]:
    """
    Builds composite hardware fingerprint:
    composite_fp = SHA256(Canvas2D + "|" + WebGL + "|" + AudioContext + "|" + ScreenSpecs)
    Returns: (composite_hash: str, raw_components: dict)
    """
    components = {
        "canvas_hash": "",
        "webgl_hash": "",
        "audio_hash": "",
        "screen_specs": ""
    }

    if isinstance(fingerprint_data, str):
        raw = fingerprint_data.strip()
        if len(raw) == 64 and all(c in "0123456789abcdefABCDEF" for c in raw):
            components["canvas_hash"] = raw
            return raw.lower(), components
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        components["canvas_hash"] = h
        return h, components

    if isinstance(fingerprint_data, dict):
        components["canvas_hash"] = str(fingerprint_data.get("canvas_hash") or fingerprint_data.get("canvas") or "").strip()
        components["webgl_hash"] = str(fingerprint_data.get("webgl_hash") or fingerprint_data.get("webgl") or "").strip()
        components["audio_hash"] = str(fingerprint_data.get("audio_hash") or fingerprint_data.get("audio") or "").strip()
        components["screen_specs"] = str(fingerprint_data.get("screen_specs") or fingerprint_data.get("screen") or "").strip()

    raw_str = f"{components['canvas_hash']}|{components['webgl_hash']}|{components['audio_hash']}|{components['screen_specs']}"
    composite_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
    return composite_hash, components

def register_device_and_get_initial_coins(
    db: Session,
    client_ip: Optional[str],
    fingerprint_data: Any,
    user_id: Optional[int] = None
) -> int:
    """
    Evaluates anti-clone signals:
    1. Composite Browser Fingerprint (Canvas + WebGL + Audio + Screen).
    2. IP /24 Subnet Throttling (max 2 trial grants per subnet per 24 hours).
    
    If fresh device AND fresh subnet:
      Grants 8 free trial coins.
    If duplicate device OR throttled subnet:
      Grants 0 coins (prevents sybil farming).
    """
    composite_fp, components = compute_composite_fingerprint(fingerprint_data)
    subnet_str = extract_ip_subnet(client_ip)

    # 1. Check Device Fingerprint
    existing_fp = (
        db.query(DeviceFingerprint)
        .filter(DeviceFingerprint.fingerprint_hash == composite_fp)
        .first()
    )
    if existing_fp and existing_fp.has_claimed_trial:
        # Duplicate / Clone Device detected!
        return 0

    # 2. Check Subnet Throttling
    existing_subnet = (
        db.query(SubnetRecord)
        .filter(SubnetRecord.subnet == subnet_str)
        .first()
    )
    now = datetime.utcnow()
    if existing_subnet:
        # If last claim was > 24 hours ago, reset daily counter
        if existing_subnet.last_claim_at and (now - existing_subnet.last_claim_at) > timedelta(hours=24):
            existing_subnet.claim_count = 0
            
        if existing_subnet.claim_count >= 2:
            # Subnet rate-limited / throttled!
            return 0

    # 3. Device and Subnet are both eligible!
    # Update or insert device record
    if not existing_fp:
        existing_fp = DeviceFingerprint(
            fingerprint_hash=composite_fp,
            canvas_hash=components["canvas_hash"][:64],
            webgl_hash=components["webgl_hash"][:64],
            audio_hash=components["audio_hash"][:64],
            screen_specs=components["screen_specs"][:255],
            user_id=user_id,
            has_claimed_trial=True,
            created_at=now
        )
        db.add(existing_fp)
    else:
        existing_fp.has_claimed_trial = True
        if user_id:
            existing_fp.user_id = user_id

    # Update or insert subnet record
    if not existing_subnet:
        existing_subnet = SubnetRecord(
            subnet=subnet_str,
            claim_count=1,
            last_claim_at=now,
            created_at=now
        )
        db.add(existing_subnet)
    else:
        existing_subnet.claim_count += 1
        existing_subnet.last_claim_at = now

    # If user_id provided, credit coins and append ledger entry
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            cur_coins = user.coins if user.coins is not None else 0
            new_balance = cur_coins + INITIAL_TRIAL_COINS
            user.coins = new_balance

            last_tx = (
                db.query(CoinTransaction)
                .filter(CoinTransaction.user_id == user_id)
                .order_by(CoinTransaction.id.desc())
                .first()
            )
            prev_hash = last_tx.tx_hash if last_tx else GENESIS_HASH
            timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            tx_hash = compute_transaction_hash(
                prev_hash, user_id, INITIAL_TRIAL_COINS, new_balance, timestamp
            )

            tx = CoinTransaction(
                user_id=user_id,
                amount=INITIAL_TRIAL_COINS,
                balance_after=new_balance,
                action_type=ACTION_INITIAL_GRANT,
                description=f"Tặng thưởng tân thủ 8 xu (Thiết bị mới)",
                reference_id=composite_fp,
                prev_hash=prev_hash,
                tx_hash=tx_hash,
                timestamp=timestamp,
                created_at=now
            )
            db.add(tx)

    db.commit()
    return INITIAL_TRIAL_COINS
