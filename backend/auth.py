import bcrypt
import jwt
from datetime import datetime, timedelta
import os
import re
import threading
import time
from typing import Tuple, Dict, Optional
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

SECRET_KEY = os.environ.get("SECRET_KEY", "narrai-jwt-default-secret-key-dev-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        print("Verify password error:", e)
        return False

def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    # Use rounds=6 (very fast) instead of default 12 to bypass Render CPU bottleneck
    salt = bcrypt.gensalt(rounds=6)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def validate_bank_password(password: str) -> Tuple[bool, str, str]:
    """
    Validates password against bank-grade security standards:
    - Length >= 8 characters
    - At least 1 uppercase letter (A-Z)
    - At least 1 lowercase letter (a-z)
    - At least 1 digit (0-9)
    - At least 1 special character (!@#$%^&*()_+-=[]{};':"\\|,.<>/?~`)
    - No whitespace allowed
    Returns: (is_valid, error_vi, error_en)
    """
    if not password or len(password) < 8:
        return False, "Mật khẩu phải có tối thiểu 8 ký tự.", "Password must be at least 8 characters long."
    if any(c.isspace() for c in password):
        return False, "Mật khẩu không được chứa khoảng trắng.", "Password must not contain whitespace."
    if not re.search(r'[A-Z]', password):
        return False, "Mật khẩu phải có ít nhất 1 chữ in hoa (A-Z).", "Password must contain at least 1 uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Mật khẩu phải có ít nhất 1 chữ thường (a-z).", "Password must contain at least 1 lowercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Mật khẩu phải có ít nhất 1 chữ số (0-9).", "Password must contain at least 1 digit."
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, "Mật khẩu phải có ít nhất 1 ký tự đặc biệt (!@#$%...).", "Password must contain at least 1 special character."
    return True, "", ""

class LoginRateLimiter:
    """
    Thread-safe rate limiter tracking failed login attempts by (ip, username).
    Locks out for 60 seconds after 5 failed attempts within 5 minutes.
    Hardened with bounded max_capacity and automatic eviction of expired entries.
    """
    def __init__(
        self,
        max_failures: int = 5,
        lockout_seconds: int = 60,
        window_seconds: int = 300,
        max_capacity: int = 5000,
    ):
        self.max_failures = max_failures
        self.lockout_seconds = lockout_seconds
        self.window_seconds = window_seconds
        self.max_capacity = max_capacity
        self._lock = threading.RLock()
        self._attempts: Dict[str, dict] = {}

    def _get_key(self, ip: str, username: str) -> str:
        clean_ip = (ip or "unknown").strip()
        clean_user = (username or "anonymous").strip().lower()
        return f"{clean_ip}:{clean_user}"

    def _cleanup_expired(self, now: float) -> None:
        """
        Prunes expired attempt records. If size still exceeds max_capacity,
        evicts the oldest entries by least recent activity to prevent unbounded memory growth.
        """
        expired_keys = []
        for key, record in list(self._attempts.items()):
            locked_until = record.get("locked_until", 0)
            valid_failures = [t for t in record.get("failures", []) if now - t < self.window_seconds]
            if not valid_failures and locked_until <= now:
                expired_keys.append(key)
            else:
                record["failures"] = valid_failures

        for key in expired_keys:
            self._attempts.pop(key, None)

        if len(self._attempts) >= self.max_capacity:
            def get_last_activity(item):
                rec = item[1]
                latest_failure = max(rec.get("failures", [0])) if rec.get("failures") else 0
                return max(latest_failure, rec.get("locked_until", 0))

            sorted_entries = sorted(self._attempts.items(), key=get_last_activity)
            excess = len(self._attempts) - self.max_capacity + 1
            for k, _ in sorted_entries[:excess]:
                self._attempts.pop(k, None)

    def is_locked(self, ip: str, username: str) -> Tuple[bool, int]:
        """
        Check if the (ip, username) is currently locked out.
        Returns (is_locked, remaining_seconds).
        """
        key = self._get_key(ip, username)
        now = time.time()
        with self._lock:
            record = self._attempts.get(key)
            if not record:
                return False, 0
            locked_until = record.get("locked_until", 0)
            if locked_until > now:
                remaining = int(locked_until - now) + 1
                return True, remaining
            # Prune failures; if expired, remove entry
            record["failures"] = [t for t in record.get("failures", []) if now - t < self.window_seconds]
            if not record["failures"]:
                self._attempts.pop(key, None)
            return False, 0

    def record_failure(self, ip: str, username: str) -> Tuple[bool, int]:
        """
        Record a failed attempt.
        Returns (is_locked_now, remaining_seconds).
        """
        key = self._get_key(ip, username)
        now = time.time()
        with self._lock:
            if key not in self._attempts and len(self._attempts) >= self.max_capacity:
                self._cleanup_expired(now)

            record = self._attempts.setdefault(key, {"failures": [], "locked_until": 0})
            
            # Prune failures older than window_seconds
            record["failures"] = [t for t in record["failures"] if now - t < self.window_seconds]
            record["failures"].append(now)

            if len(record["failures"]) >= self.max_failures:
                record["locked_until"] = now + self.lockout_seconds
                return True, self.lockout_seconds
            return False, 0

    def record_success(self, ip: str, username: str) -> None:
        """
        Clear failure counter upon successful login.
        """
        key = self._get_key(ip, username)
        with self._lock:
            if key in self._attempts:
                del self._attempts[key]

    def reset_all(self) -> None:
        """Clear all rate limit tracking (useful for tests)."""
        with self._lock:
            self._attempts.clear()

    def check_rate_limit(self, ip: str, username: str) -> None:
        """
        Raises HTTPException(429) if locked out.
        """
        locked, remaining = self.is_locked(ip, username)
        if locked:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail=f"Đăng nhập thất bại quá nhiều lần. Vui lòng thử lại sau {remaining} giây. (Too many failed login attempts. Please try again in {remaining} seconds.)"
            )

login_rate_limiter = LoginRateLimiter()
