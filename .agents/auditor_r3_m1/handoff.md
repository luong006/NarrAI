# Forensic Integrity Audit Report: Milestone 1 (R1 & R2)

**Work Product**: Milestone 1 (R1 100% i18n & R2 Bank-Grade Auth)  
**Profile**: General Project (Integrity mode: Development)  
**Verdict**: `VERDICT: CLEAN` (No integrity violations detected)

---

## 1. Observation

### 1.1 Bank-Grade Password Validation (`backend/auth.py` lines 47-70)
```python
def validate_bank_password(password: str) -> Tuple[bool, str, str]:
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
```
- Direct Observation: The function does NOT return `True` unconditionally. It sequentially tests length (>=8), absence of whitespace (`any(c.isspace())`), uppercase (`[A-Z]`), lowercase (`[a-z]`), digit (`[0-9]`), and special characters (`[^A-Za-z0-9]`). If any condition fails, it immediately returns `False` along with bilingual error strings.

### 1.2 Brute-Force Rate Limiting (`backend/auth.py` lines 72-151 & `backend/main.py` lines 224-239)
```python
class LoginRateLimiter:
    def __init__(self, max_failures: int = 5, lockout_seconds: int = 60, window_seconds: int = 300):
        self.max_failures = max_failures
        self.lockout_seconds = lockout_seconds
        self.window_seconds = window_seconds
        self._lock = threading.RLock()
        self._attempts: Dict[str, dict] = {}
```
- Direct Observation: Not a dummy stub or mock. It synchronizes via `threading.RLock()`, prunes timestamps older than 300s window, counts failures, and computes `locked_until = now + lockout_seconds` when reaching 5 failures.
- In `backend/main.py` line 225, `login_rate_limiter.check_rate_limit(client_ip, username)` executes before authentication. On failure, `record_failure` is called (line 229) and raises `HTTPException(429)` if locked. On successful login, `record_success` deletes the tracking key (line 238).

### 1.3 `User.full_name` Database Persistence (`backend/db/models.py` & `backend/main.py`)
- Direct Observation in `backend/db/models.py`:
  * Model column defined at line 13: `full_name = Column(String(100), nullable=True, default="")`.
  * Auto-migration at lines 79-83:
    ```python
    if "users" in tables:
        user_cols = [c["name"] for c in inspector.get_columns("users")]
        if "full_name" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(100) DEFAULT ''"))
            conn.commit()
    ```
- Direct Observation in `backend/main.py`:
  * `register_user` extracts `full_name` from request (line 139), instantiates `new_user = User(username=username, full_name=full_name, password_hash=hashed_password)` (line 171), commits to database (`db.commit()`), and returns `"full_name": new_user.full_name or new_user.username` (line 185).
  * `login_user` and `read_users_me` return `user.full_name or user.username` (lines 247, 258).
- Direct Observation in `frontend/src/lib/api.ts`:
  * Lines 84-88 transmit `full_name: fullName ? fullName.trim() : ""` in the JSON registration payload.

### 1.4 Toast Notification Rendering (`frontend/src/lib/toast.ts`, `Toast.tsx`, `layout.tsx`)
- Direct Observation:
  * `ToastProvider` (`frontend/src/lib/toast.ts`) manages active toast list via `useState<ToastItem[]>([])`.
  * `ToastContainer` (`frontend/src/components/ui/Toast.tsx`) renders actual DOM markup (`<div role="alert" ...>`) with Lucid icons and slide-in animations.
  * Root layout (`frontend/src/app/layout.tsx` line 21-24) mounts `<ToastContainer />` inside `<ToastProvider>`.
  * In `frontend/src/app/page.tsx` and `frontend/src/components/setup/Phase1Idea.tsx`, 100% of browser `alert()` invocations have been replaced by `toast.error()`, `toast.success()`, `toast.warning()`, and `toast.info()`.

### 1.5 Reactive Password Checklist & Strength Meter (`frontend/src/components/modals/AuthModal.tsx`)
- Direct Observation:
  * Lines 52-61: `rules` is a reactive `useMemo` depending on `password`, testing length >= 8, `/[A-Z]/`, `/[a-z]/`, `/[0-9]/`, `/[^A-Za-z0-9]/`, and `!/\s/`.
  * Lines 75-100: `strength` is a reactive `useMemo` calculating score (1 to 5), percentage (20% to 100%), color (`rose-500` -> `orange-500` -> `amber-500` -> `emerald-500` -> `indigo-600`), and localized labels.
  * Lines 314-323: Renders 5 reactive check items with `CheckCircle2` / `XCircle`.
  * Line 380: Submit button explicitly disabled if `!allRulesPassed || !passwordsMatch`.
  * Lines 42-49 & 166-172: When backend returns HTTP 429, parses remaining seconds from detail string and runs an active 1-second interval countdown timer.

### 1.6 Absence of Test Bypasses and Test Tampering (`backend/tests/test_bank_auth.py`)
- Direct Observation: `test_bank_auth.py` contains 224 lines of real test cases using `unittest`.
  * `TestBankPasswordValidation`: Tests 6 valid passwords, 5 short/empty samples, missing uppercase, missing lowercase, missing digits, missing special chars, and 5 whitespace variants.
  * `TestLoginRateLimiter`: Tests 4 failed attempts pass, 5th attempt locks out, `check_rate_limit` raises `HTTPException(429)`, successful login resets state, and user/IP isolation.
  * `TestUserModelAndDatabase`: Actually creates an in-memory SQLite database, commits a `User` record with `full_name`, and queries it back.
  * Zero hardcoded test bypasses or fabricated test results.

### 1.7 Workspace Layout Compliance
- Direct Observation: Search of `.agents/worker_r3_m1/` confirmed only metadata files (`BRIEFING.md`, `DISPATCH.md`, `handoff.md`, `progress.md`).
- Zero source code or test files were written into `.agents/`.

---

## 2. Logic Chain

1. **Premise 1 (Anti-Facade Check)**: A work product is clean only if implemented functions execute real, verifiable logic rather than returning static dummy values.
   - *Evidence*: `validate_bank_password` in `auth.py` tests 6 explicit regex and string conditions and returns `False` if any fails; `LoginRateLimiter` enforces atomic locking, timestamp pruning, and lockout calculation; `ToastProvider` + `ToastContainer` manages dynamic state and mounts DOM elements; `AuthModal.tsx` reactively derives checklist state from password input.
   - *Inference*: No dummy facades exist.

2. **Premise 2 (Database Persistence Check)**: Full name must be stored in the persistent data store and exposed through API endpoints.
   - *Evidence*: `models.py` declares `full_name` column and auto-migration script; `main.py` ingests `full_name` and saves via SQLAlchemy session; tests verify insert and retrieval from SQLite.
   - *Inference*: `User.full_name` genuinely persists in SQLite/PostgreSQL.

3. **Premise 3 (Test Tampering & Layout Check)**: Tests must not be mocked to bypass failures, and no code files may reside in `.agents/`.
   - *Evidence*: `test_bank_auth.py` executes real logic against real validator, rate limiter, and SQLite DB. `.agents/worker_r3_m1/` contains only 4 markdown metadata files.
   - *Inference*: Tests are authentic and layout compliance is 100%.

---

## 3. Caveats
- `run_command` in this non-interactive subagent environment requires user approval and times out if prompt is unattended. Forensic verification was performed via comprehensive static code analysis, AST inspection, regex scanning, and schema verification.
- The `LoginRateLimiter` operates in-memory per process. In a horizontally scaled multi-worker deployment, rate limiting would eventually synchronize via Redis (which is the objective of Milestone 2 / R3). For Milestone 1 development mode, this in-memory implementation is fully compliant and genuinely functional.

---

## 4. Conclusion
All five forensic integrity criteria have been verified with concrete evidence:
1. `validate_bank_password` really enforces all 5 criteria + whitespace restriction.
2. `LoginRateLimiter` genuinely records failed attempts, tracks sliding windows, and locks out with HTTP 429.
3. `User.full_name` is genuinely declared, migrated, stored in DB, and returned to client.
4. `ToastProvider` and `ToastContainer` actively manage toast state and render DOM elements.
5. `AuthModal.tsx` reactively computes password strength and checklist state on every keystroke.
6. Zero test tampering or hardcoded bypasses detected.
7. Zero code/test files written to `.agents/`.

**VERDICT: CLEAN** (No integrity violations detected)

---

## 5. Verification Method
To reproduce this verification:
1. View `backend/auth.py` lines 47-70 to verify `validate_bank_password` logic.
2. View `backend/auth.py` lines 72-151 to verify `LoginRateLimiter` logic.
3. View `backend/db/models.py` lines 13 and 69-85 to verify `User.full_name` column and auto-migration.
4. View `frontend/src/lib/toast.ts`, `frontend/src/components/ui/Toast.tsx`, and `frontend/src/app/layout.tsx` to verify `ToastProvider` DOM mounting.
5. View `frontend/src/components/modals/AuthModal.tsx` lines 51-100 to verify reactive checklist and strength meter.
6. View `backend/tests/test_bank_auth.py` to inspect the comprehensive unit tests.
7. Inspect `.agents/worker_r3_m1/` to verify absence of source code.
