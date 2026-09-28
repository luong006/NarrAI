# Handoff Report: Independent Review of Milestone 1 (R1 & R2)

**Reviewer Agent**: `reviewer_r3_m1_2`  
**Verdict**: **REQUEST_CHANGES**  
**Timestamp**: 2026-09-22T05:37:30Z  
**Working Directory**: `e:\NarrAI\.agents\reviewer_r3_m1_2`  

---

## 1. Observation

### Observation 1.1: Stray `alert(...)` Calls in `frontend/src/components/modals/HistoryModal.tsx`
An exhaustive static pattern search for `\balert\(` across `frontend/src/` revealed two lingering browser alert invocations in `HistoryModal.tsx`:
- **File**: `frontend/src/components/modals/HistoryModal.tsx`, Lines 46–61:
  ```tsx
  46:   const handleStoryClick = async (id: number) => {
  47:     setLoading(true);
  48:     try {
  49:       const res = await api.getStoryDetail(id);
  50:       if (res.status === 'success' && res.story) {
  51:         onSelectStory(res.story);
  52:         onClose();
  53:       } else {
  54:         alert("Không thể tải chi tiết truyện.");
  55:       }
  56:     } catch (e: any) {
  57:       alert("Lỗi tải truyện: " + e.message);
  58:     } finally {
  59:       setLoading(false);
  60:     }
  61:   };
  ```
- **Context**: The worker implemented `ToastProvider` and `useToast()` in `frontend/src/lib/toast.ts` and `frontend/src/components/ui/Toast.tsx`, but omitted importing or utilizing `useToast()` in `HistoryModal.tsx`.
- **Impact**: Violates ORIGINAL_REQUEST.md R1 ("loại bỏ hoàn toàn window.alert") and PROJECT.md Feature 2 ("replacing 100% of browser alert() calls").

---

### Observation 1.2: Hardcoded Vietnamese Strings in `ComicViewer.tsx` and `HistoryModal.tsx`
- **File**: `frontend/src/components/comic/ComicViewer.tsx`, Lines 42–53:
  ```tsx
  42:       {error && (
  43:         <div className="comic-panel-skeleton text-center p-4 flex flex-col items-center justify-center">
  44:           <span className="text-red-500 text-xs font-semibold mb-2">Chưa tải được khung tranh #{panel.panel_index}</span>
  45:           <button
  46:             onClick={handleManualRetry}
  47:             className="px-3 py-1 bg-brand-700 hover:bg-brand-800 text-white rounded text-xs font-medium transition-colors shadow flex items-center gap-1"
  48:           >
  49:             <RefreshCw className="w-3 h-3" />
  50:             <span>Thử lại</span>
  51:           </button>
  52:         </div>
  53:       )}
  ```
  *Note*: Translation keys `t.panel_load_error` (`"Chưa tải được khung tranh"` / `"Failed to load manga panel"`) and `t.retry_btn` (`"Thử lại"` / `"Retry"`) were already added to `frontend/src/lib/i18n.ts` (lines 149–150 and 323–324), but were bypassed in favor of raw Vietnamese literals. When switching to English (`ENG`), these elements remain in Vietnamese.
- **File**: `frontend/src/components/modals/HistoryModal.tsx`, Line 40:
  ```tsx
  40:       setError(e.message || "Lỗi tải lịch sử truyện.");
  ```
  Literal Vietnamese string used without i18n fallback.

---

### Observation 1.3: Interface Contracts & Backward Compatibility for `full_name`
- **Database Schema (`backend/db/models.py`)**:
  - Line 13: `full_name = Column(String(100), nullable=True, default="")`
  - Auto-migration runtime block (lines 69–85):
    ```python
    with engine.connect() as conn:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if "users" in tables:
            user_cols = [c["name"] for c in inspector.get_columns("users")]
            if "full_name" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(100) DEFAULT ''"))
                conn.commit()
    ```
    Compatible with both SQLite (3.1.6+) and PostgreSQL.
- **Clean Fallback Execution (`user.full_name or user.username`)**:
  - `backend/main.py`:
    - Line 185 (`/api/register`): `"full_name": new_user.full_name or new_user.username`
    - Line 247 (`/api/login`): `"full_name": user.full_name or user.username`
    - Line 258 (`/api/me`, `/api/users/me`): `"full_name": current_user.full_name or current_user.username`
  - `frontend/src/lib/api.ts`: Lines 67, 108, 130 fallback cleanly (`data.full_name || data.username`).
  - `frontend/src/components/layout/Sidebar.tsx`: Line 28 defines `const displayName = fullName || username;` and renders `@username` only when both exist.
  - `frontend/src/app/page.tsx`: Lines 202, 760, 884 assign `fullName: res.full_name || res.username`.

---

### Observation 1.4: Password Validation Boundary & Rate Limiter Analysis
- **Password Length Boundaries (`backend/auth.py` & `frontend/src/components/modals/AuthModal.tsx`)**:
  - **7 characters**: Evaluates `len < 8` -> rejected on backend (`validate_bank_password`), frontend disabled (`rules.length = false`).
  - **8 characters**: Minimum length met on both backend and frontend. Frontend gives 4/5 score (80% "Strong").
  - **12 characters**: Meets backend and frontend criteria; triggers 12+ character bonus in `AuthModal.tsx` (`rules.noSpace && password.length >= 12`) -> achieves 5/5 score (100% "Very Strong - Bank-Grade").
  - **Whitespace**: Prohibited across entire string on both ends via `any(c.isspace() for c in password)` and `!/\s/.test(password)`.
- **Confirm Password Live Match Edge Cases (`AuthModal.tsx`)**:
  - Line 71: `const passwordsMatch = confirmPassword.length > 0 && password === confirmPassword;`
  - When empty: no false green/red alerts displayed; submit button disabled.
  - Live editing either field updates `passwordsMatch` immediately.
- **Rate Limiter Concurrency (`backend/auth.py`)**:
  - Line 81: `self._lock = threading.RLock()` protects `is_locked`, `record_failure`, `record_success`, `reset_all`.
  - Concurrency is thread-safe within a single process.
  - **Vulnerability**: In `record_failure`, `record["failures"]` prunes old timestamps, but keys in `self._attempts` are never pruned or size-bounded. Under a distributed credential stuffing attack generating millions of random usernames, `_attempts` will grow monotonically without bound in memory.

---

## 2. Logic Chain

1. **Requirement R1 & Project Contract**:
   - The user dispatch states: *"Alert replacement completeness in frontend (ensure no stray window.alert remains)"* and ORIGINAL_REQUEST.md demands *"100% i18n Anh ⟷ Việt không để sót bất kỳ chuỗi ký tự cố định nào"*.
   - Observation 1.1 reveals verbatim `alert("Không thể tải chi tiết truyện.")` and `alert("Lỗi tải truyện: " + e.message)` in `frontend/src/components/modals/HistoryModal.tsx`.
   - Observation 1.2 reveals hardcoded Vietnamese text in `ComicViewer.tsx` (`"Chưa tải được khung tranh #"`, `"Thử lại"`) despite existing translation keys in `i18n.ts`.
   - **Conclusion**: The frontend does not fulfill 100% alert elimination nor 100% i18n string extraction.

2. **Interface Contracts & Backward Compatibility**:
   - Observation 1.3 shows database schema definition, SQLAlchemy inspection, and standard ANSI SQL `ALTER TABLE` statement.
   - All backend endpoints (`/api/register`, `/api/login`, `/api/me`) and frontend presentation points (`Sidebar.tsx`, `api.ts`, `page.tsx`) explicitly enforce `user.full_name or user.username`.
   - **Conclusion**: Interface contracts and backward compatibility are fully satisfied.

3. **Robustness & Edge Cases**:
   - Observation 1.4 confirms boundary testing on password lengths (7, 8, 12 chars), character complexity classes, and confirm password live reactive matching are well-architected.
   - Concurrency is protected by `RLock`, but unbounded dictionary storage presents an operational memory risk under high-volume malicious scanning.
   - **Conclusion**: Core auth logic is robust; minor hardening recommended for rate limiter dictionary eviction.

4. **Integrity Audit**:
   - No evidence of hardcoded test bypasses, dummy implementations, falsified logs, or mock returns in production routes. All logic is authentic.
   - **Conclusion**: No integrity violation, but clear quality deficiencies require revision.

---

## 3. Caveats

1. **In-Memory Rate Limiting Scope**:
   `LoginRateLimiter` operates in-memory within the active Python process. In a multi-worker production configuration (e.g. Uvicorn with `--workers 4`), rate limits are tracked per-worker rather than globally. Since Milestone 2 introduces a shared `CacheManager` with Redis, backing the rate limiter with Redis/CacheManager in M2/M4 is recommended.
2. **Terminal Interactive Commands**:
   Subagent executions requiring interactive user prompt confirmation timed out after 60s. All findings in this report were verified by rigorous static code examination, AST inspection, cross-referencing, and regex validation across the entire workspace.

---

## 4. Conclusion & Verdict

**Verdict**: **REQUEST_CHANGES**

Milestone 1 satisfies the backend database schema auto-migration, password complexity validation, and auth endpoints. However, it cannot be approved due to:
1. Stray `alert(...)` calls remaining in `frontend/src/components/modals/HistoryModal.tsx` (violating prompt mandate and R1).
2. Hardcoded untranslated strings in `ComicViewer.tsx` (lines 44, 50) and `HistoryModal.tsx` (line 40) (violating 100% bilingual R1).

---

## 5. Review Report

### Findings

#### [Major] Finding 1: Stray `alert(...)` Calls in `HistoryModal.tsx`
- **What**: Browser `alert()` popups used instead of unified toast system.
- **Where**: `frontend/src/components/modals/HistoryModal.tsx`, Lines 54 and 57.
- **Why**: Violates Milestone 1 R1 ("Unified Toast Notification System replacing 100% of browser alert() calls") and the prompt checklist.
- **Suggestion**:
  1. Import `useToast` from `@/lib/toast`.
  2. Inside `HistoryModal`, instantiate `const { toast } = useToast();`.
  3. Replace line 54 `alert("Không thể tải chi tiết truyện.");` with `toast.error(t.unknown_error || "Không thể tải chi tiết truyện.");`.
  4. Replace line 57 `alert("Lỗi tải truyện: " + e.message);` with `toast.error(e.message || t.network_error);`.

#### [Minor] Finding 2: Hardcoded Untranslated Strings in `ComicViewer.tsx` and `HistoryModal.tsx`
- **What**: Vietnamese string literals hardcoded in UI components where i18n translation keys already exist.
- **Where**:
  - `frontend/src/components/comic/ComicViewer.tsx`, Line 44: `<span className="text-red-500 text-xs font-semibold mb-2">Chưa tải được khung tranh #{panel.panel_index}</span>`
  - `frontend/src/components/comic/ComicViewer.tsx`, Line 50: `<span>Thử lại</span>`
  - `frontend/src/components/modals/HistoryModal.tsx`, Line 40: `setError(e.message || "Lỗi tải lịch sử truyện.");`
- **Why**: Breaks 100% bilingual guarantee when user selects English (`ENG`).
- **Suggestion**:
  1. In `ComicViewer.tsx`, change line 44 to:
     `<span className="text-red-500 text-xs font-semibold mb-2">{t.panel_load_error} #{panel.panel_index}</span>`
  2. In `ComicViewer.tsx`, change line 50 to:
     `<span>{t.retry_btn}</span>`
  3. In `HistoryModal.tsx`, update line 40 to fallback to a localized error key (e.g. `t.network_error`).

#### [Minor] Finding 3: Unbounded Memory Growth in `LoginRateLimiter`
- **What**: `self._attempts` dictionary in `backend/auth.py` retains keys indefinitely if an IP/username pair is attacked once and never seen again.
- **Where**: `backend/auth.py`, Lines 82 & 113.
- **Why**: Potential memory leak under distributed credential stuffing attacks generating high cardinality random keys.
- **Suggestion**: Add a periodic key-cleanup routine or maximum dictionary size (e.g., evict entries where `now - last_seen > window_seconds` when `len(self._attempts) > 10000`).

---

### Verified Claims

| Claim | Verification Method | Status |
|---|---|---|
| User schema has `full_name` | Checked `backend/db/models.py:13` | PASS |
| Auto-migration works on SQLite & Postgres | Checked `backend/db/models.py:69-85` with ANSI SQL `ALTER TABLE` | PASS |
| Legacy users without `full_name` fallback cleanly | Checked `models.py`, `main.py`, `api.ts`, `Sidebar.tsx`, `page.tsx` | PASS |
| Password validation rules (8+ chars, uppercase, lowercase, digit, special, no space) | Traced `backend/auth.py:47-70` & `AuthModal.tsx:52-70` | PASS |
| Boundary tests on password length (7, 8, 12 chars) | Boundary analysis: 7 fails, 8 passes (80%), 12 passes (100%) | PASS |
| Rate limiter thread-safety | Checked `threading.RLock()` usage in `backend/auth.py` | PASS |
| Confirm password live match edge cases | Traced reactive matching logic in `AuthModal.tsx:71-74` | PASS |
| 100% replacement of browser `alert()` in UI | Checked via regex search `\balert\(` across `frontend/src/` | **FAIL** (`HistoryModal.tsx`) |
| 100% i18n without hardcoded strings | Checked component UI strings | **FAIL** (`ComicViewer.tsx`, `HistoryModal.tsx`) |

---

## 6. Adversarial Challenge Report

**Overall Risk Assessment**: **MEDIUM**

### Challenges

#### Challenge 1: Stray Modal Alerts Disrupting Mobile and Embedded UX
- **Assumption Challenged**: Frontend notification system has completely unified around custom toasts.
- **Attack Scenario**: Network disconnection occurs while fetching an archived story in `HistoryModal.tsx`. The browser halts execution with a native blocking `window.alert()` dialog, blocking the main thread and breaking the embedded/PWA user experience.
- **Blast Radius**: Poor UX, inconsistent design language, UI freezes on modal interaction.
- **Mitigation**: Swap `alert()` with `useToast()` in `HistoryModal.tsx`.

#### Challenge 2: Memory Exhaustion via Distributed Brute-Force Key Flooding
- **Assumption Challenged**: `LoginRateLimiter` memory usage is bounded.
- **Attack Scenario**: Attacker launches a botnet generating 500,000 requests with pseudo-random spoofed `X-Forwarded-For` IPs and random usernames. `LoginRateLimiter` creates 500,000 dictionary entries. Because only timestamps within an entry are pruned upon subsequent access, unrepeated keys are never garbage-collected.
- **Blast Radius**: Increased RSS memory usage of Python backend, potential Out-Of-Memory (OOM) crash on containerized hosts (Render/Fly.io).
- **Mitigation**: Add LRU key eviction or integrate with M2 `CacheManager` with automatic TTL key expiration.

---

## 7. Independent Verification Method

To independently verify these findings:
1. Search for lingering `alert(` calls:
   ```bash
   grep -rn "alert(" frontend/src/
   ```
   *Expected Output*: Displays lines 54 and 57 of `frontend/src/components/modals/HistoryModal.tsx`.
2. Inspect `ComicViewer.tsx` lines 44 and 50:
   Notice hardcoded Vietnamese strings `"Chưa tải được khung tranh #"` and `"Thử lại"`.
3. Invalidation Condition: If `HistoryModal.tsx` replaces `alert()` with `toast.error()` and `ComicViewer.tsx` uses `{t.panel_load_error}` and `{t.retry_btn}`, this review's rejection conditions will be fully resolved.
