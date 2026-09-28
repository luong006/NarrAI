# Handoff Report: Survey of Requirements R1 (100% i18n) & R2 (Bank-Grade Auth & Full Name)

## 1. Observation

### 1.1 Scope & Codebase Structure
- Frontend: Next.js 14 App Router in `frontend/src/` with React 18, Tailwind CSS, Lucide icons, `next-themes`.
- Backend: FastAPI in `backend/main.py`, SQLAlchemy models in `backend/db/models.py`, JWT & bcrypt auth in `backend/auth.py`.
- No third-party toast library or i18n library (e.g. `next-intl` or `react-i18next`) is installed in `frontend/package.json`. i18n is currently handled via custom dictionary `translations` in `frontend/src/lib/i18n.ts`.

---

### 1.2 Detailed Observations for Requirement R1: i18n (Anh ⟷ Việt)

#### A. Dictionary State in `frontend/src/lib/i18n.ts`
- Total dictionary keys: 98 keys per locale (`vi` and `en`).
- Missing keys for:
  - Top navigation & Theme toggle (`theme_light`, `theme_dark`, `theme_toggle_aria`, `pro_badge`).
  - Landing hero badge & feature section title.
  - Auth modal additions: `full_name`, `confirm_password`, `pass_match_err`, password rules checklist (5 items), strength meter levels (5 levels), brute-force lockout notice.
  - Setup phases: Subtitles, genre count badge suffix (`"đã chọn"` vs `"selected"`), trending themes titles & descriptions in English, prompt prefixes (`[Thể loại: ]` vs `[Genre: ]`).
  - Copilot panel: Undo button label & tooltip (`"Hoàn tác"` vs `"Undo"`), character count label, live drafting indicator, quick prompt labels.
  - Comic viewer: Panel loading error, retry button (`"Thử lại"` vs `"Retry"`), adaptation validation alerts.
  - Error boundary: Interface crash title, error details, retry button, home button.
  - System toasts: Error, success, warning, info notifications replacing raw browser `alert()`.

#### B. Component-by-Component Hardcoded String Inventory

1. **`frontend/src/components/layout/ThemeToggle.tsx`**:
   - Lines 23-24:
     ```tsx
     title={theme === "dark" ? "Chuyển sang giao diện Sáng" : "Chuyển sang giao diện Tối"}
     aria-label="Toggle theme"
     ```
     *Issue*: Component accepts no `lang` prop; tooltip is hardcoded Vietnamese, `aria-label` is hardcoded English.

2. **`frontend/src/components/landing/LandingView.tsx`**:
   - Line 44:
     ```tsx
     <span>Hệ Thống Sáng Tác Tiểu Thuyết & Manga AI Chuyên Nghiệp</span>
     ```
     *Issue*: Hero badge string is 100% hardcoded Vietnamese.
   - Line 69:
     ```tsx
     <h2 className="...">Tính Năng Trọng Tâm Của NarrAI</h2>
     ```
     *Issue*: Section header is 100% hardcoded Vietnamese.
   - Line 100:
     ```tsx
     <p>NarrAI Co-creation System © 2026. Designed for deep narrative craftsmanship.</p>
     ```
     *Issue*: Footer copyright is hardcoded English.

3. **`frontend/src/components/setup/Phase1Idea.tsx`**:
   - Lines 70-111: `FALLBACK_THEMES` contains 5 trending topics only in Vietnamese:
     - `title`: `"Chữa lành & Bỏ phố về quê"`, `"Trùng sinh báo thù & Nữ cường"`, `"Cưới trước yêu sau / Hợp đồng"`, `"Linh dị dân gian Việt Nam"`, `"Xuyên thư & Hệ thống 'Vô tri'"`
     - `description` and `prompt_snippet` are purely Vietnamese.
   - Line 158:
     ```tsx
     combined = `[Thể loại: ${selectedGenres.join(", ")}] ${combined}`;
     ```
   - Line 161:
     ```tsx
     combined = `[Chủ đề: ${selectedThemes.join(", ")}] ${combined}`;
     ```
     *Issue*: Vietnamese tags injected into prompt even if in English mode.
   - Lines 165-171: Browser `alert()` using inline ternary:
     ```tsx
     alert(lang === "vi" ? "Vui lòng nhập ý tưởng khởi đầu hoặc chọn ít nhất 1 thể loại/chủ đề!" : "Please enter your story concept or select at least one genre/theme!");
     ```
   - Lines 188-191: Inline ternary for step subtitle instead of dictionary key.
   - Line 202:
     ```tsx
     ({selectedGenres.length} đã chọn)
     ```
     *Issue*: `"đã chọn"` hardcoded Vietnamese suffix.
   - Line 268:
     ```tsx
     ({selectedThemes.length} đã chọn)
     ```
     *Issue*: `"đã chọn"` hardcoded Vietnamese suffix.
   - Line 303:
     ```tsx
     {lang === "vi" ? "Ý tưởng cốt truyện của bạn:" : "Your story premise:"}
     ```

4. **`frontend/src/components/setup/Phase2Interview.tsx`**:
   - Line 38: Inline ternary:
     ```tsx
     {lang === 'vi' ? "Trả lời các câu hỏi để AI định hình cốt truyện hoặc bấm bỏ qua để chốt dàn ý ngay." : "Answer AI questions to flesh out your narrative, or skip to finalize immediately."}
     ```

5. **`frontend/src/components/setup/Phase3Controls.tsx`**:
   - Line 55: Inline ternary:
     ```tsx
     {lang === 'vi' ? "Thiết lập cấu hình văn phong trước khi AI bắt đầu chấp bút chương đầu tiên." : "Configure story parameters before AI begins drafting chapter 1."}
     ```

6. **`frontend/src/components/editor/AICopilotPanel.tsx`**:
   - Lines 88-89: Inline ternary:
     ```tsx
     {lang === "vi" ? "Trực tiếp sửa bản thảo" : "Live Manuscript Editor"}
     ```
   - Lines 97-100:
     ```tsx
     title="Hoàn tác chỉnh sửa gần nhất"
     >
       <RotateCcw className="w-3 h-3" />
       <span>Hoàn tác</span>
     ```
     *Issue*: Undo button label and title are 100% hardcoded Vietnamese.
   - Line 115:
     ```tsx
     {selectedText.length} chars
     ```
     *Issue*: `"chars"` hardcoded English.
   - Lines 186-189: Inline ternary:
     ```tsx
     {streaming ? lang === "vi" ? "AI đang chấp bút thời gian thực..." : "AI is drafting live..." : t.ai_thinking}
     ```
   - Line 217: Inline ternary:
     ```tsx
     {lang === "vi" ? "Lệnh can thiệp nhanh bản thảo:" : "Direct manuscript commands:"}
     ```
   - Lines 62-72: `quickPrompts` defines English commands:
     - `"Write a completely different opening for this story"`
     - `"Make the ending much more dramatic and suspenseful"`
     - `"Rewrite in a darker, more gripping thriller tone"`
     - `"Add deeper internal thoughts and character dialogues"`
     *Direct Link to Backend*: In `backend/agents/copilot_agent.py` line 213, `_is_direct_edit_request()` ONLY inspects Vietnamese keywords (`"mở đầu"`, `"sửa lại"`, etc.). Clicking these English quick action chips causes `_is_direct_edit_request()` to evaluate to `False`, throwing error or missing direct edit!

7. **`frontend/src/components/comic/ComicViewer.tsx`**:
   - Line 44:
     ```tsx
     <span className="text-red-500 text-xs font-semibold mb-2">Chưa tải được khung tranh #{panel.panel_index}</span>
     ```
     *Issue*: Hardcoded Vietnamese error message.
   - Line 50:
     ```tsx
     <span>Thử lại</span>
     ```
     *Issue*: Hardcoded Vietnamese retry button.

8. **`frontend/src/app/page.tsx`**:
   - Line 284: `alert("Lỗi từ AI: " + (res.message || "Vui lòng thử lại"));` -> Hardcoded Vietnamese.
   - Line 287: `alert("Lỗi kết nối: " + e.message);` -> Hardcoded Vietnamese.
   - Lines 323-328: Hardcoded Vietnamese prompt instructions injected into AI generation prompt regardless of language:
     - `" Hãy giữ cốt truyện cực kỳ logic, thực tế."`
     - `" Hãy bùng nổ sáng tạo, thêm những tình tiết bất ngờ (plot twist) điên rồ."`
     - `" Nhịp độ truyện chậm rãi, miêu tả nội tâm và bối cảnh thật chi tiết."`
     - `" Nhịp độ truyện nhanh, dồn dập, tập trung vào hành động và hội thoại kịch tính."`
   - Line 348: `alert("Thông báo hệ thống: " + result.error);` -> Hardcoded Vietnamese.
   - Lines 353-356: Hardcoded Vietnamese Copilot assistant message:
     ```tsx
     content: length === "long"
       ? "Chương 1 đã hoàn tất! Bạn có thể ra lệnh cho Copilot bên dưới, ấn 'Viết tiếp chương mới' hoặc 'Chuyển thể Truyện tranh'."
       : "Bản thảo đã hoàn tất! Bạn có thể bôi đen văn bản để sửa nhanh, ra lệnh cho Copilot hoặc chuyển thể sang truyện tranh."
     ```
   - Line 363: `alert("Lỗi chấp bút: " + err.message);` -> Hardcoded Vietnamese.
   - Lines 389-396: Action labels notice banner.
   - Line 399: `alert("Không thể sửa: " + (res.message || "Lỗi xử lý"));` -> Hardcoded Vietnamese.
   - Line 402: `alert("Lỗi sửa văn bản: " + e.message);` -> Hardcoded Vietnamese.
   - Line 416: `alert("Không thể sửa: " + (res.message || "Lỗi xử lý"));` -> Hardcoded Vietnamese.
   - Line 419: `alert("Lỗi: " + e.message);` -> Hardcoded Vietnamese.
   - Line 480: `(params.summary_of_changes ? "\n\n📝 Chi tiết thay đổi: " + params.summary_of_changes : "")` -> Hardcoded Vietnamese prefix.
   - Line 489: `params.message || "Đã xử lý."` -> Hardcoded Vietnamese fallback.
   - Line 503: `"Đang yêu cầu viết lại: " + (params.critique || "")` -> Hardcoded Vietnamese.
   - Line 509: `"Đã xử lý tác vụ: " + action` -> Hardcoded Vietnamese.
   - Line 527: `"Lỗi kết nối Copilot: " + (err.message || "Không xác định")` -> Hardcoded Vietnamese.
   - Line 555: `alert("Lỗi viết chương: " + result.error);` -> Hardcoded Vietnamese.
   - Line 560: `content: "Đã viết xong chương mới! Bạn có thể tiếp tục ra lệnh hoặc kết thúc truyện."` -> Hardcoded Vietnamese.
   - Line 567: `alert("Lỗi viết tiếp: " + err.message);` -> Hardcoded Vietnamese.
   - Line 574: Fallback prompt: `"Hãy viết tiếp chương tiếp theo. Tối thiểu 2000 từ. Kết thúc bằng tình tiết kịch tính."` -> Hardcoded Vietnamese.
   - Line 589: `alert("Lỗi: " + err.message);` -> Hardcoded Vietnamese.
   - Line 601: `confirm(lang === "vi" ? "Bạn có chắc muốn kết thúc câu chuyện? AI sẽ chấp bút đoạn kết trọn vẹn." : "Are you sure you want to conclude the story?")`
   - Line 615: `alert("Lỗi kết thúc: " + result.error);` -> Hardcoded Vietnamese.
   - Line 620: `content: "Câu chuyện đã kết thúc trọn vẹn! Bạn có thể tải xuống bản thảo hoặc chuyển thể sang truyện tranh."` -> Hardcoded Vietnamese.
   - Line 627: `alert("Lỗi kết thúc: " + err.message);` -> Hardcoded Vietnamese.
   - Line 634: Fallback prompt: `"Hãy viết ĐOẠN KẾT THÚC. Gói gọn tất cả tuyến truyện..."` -> Hardcoded Vietnamese.
   - Line 649: `alert("Lỗi: " + err.message);` -> Hardcoded Vietnamese.
   - Line 677: `content: "Đã tải bản thảo \"${story.title || 'Đang viết'}\". Bạn có thể tiếp tục chỉnh sửa, ra lệnh cho Copilot hoặc chuyển thể sang truyện tranh."` -> Hardcoded Vietnamese.
   - Line 685: `alert(lang === "vi" ? "Bản thảo cần có nội dung chữ để chuyển thể truyện tranh." : "Manuscript needs content to adapt.");`
   - Line 690: `alert(lang === "vi" ? "Chưa có mã bản thảo trên máy chủ. Hãy chờ AI tạo xong bản thảo hoặc lưu truyện trước khi chuyển thể." : "Story ID not ready.");`
   - Line 704: `alert("Lỗi chuyển thể truyện tranh: " + (res.message || "Lỗi hệ thống"));` -> Hardcoded Vietnamese.
   - Line 708: `alert("Lỗi: " + e.message);` -> Hardcoded Vietnamese.
   - Line 722: `alert(lang === "vi" ? "Chưa có thêm nội dung chữ mới để vẽ tiếp tranh!" : "No new text written yet to continue comic serialization!");`
   - Line 729: `alert("Lỗi: " + e.message);` -> Hardcoded Vietnamese.
   - Line 818: `{lang === "vi" ? "Hoàn tác (Undo)" : "Undo"}`

9. **`frontend/src/app/error.tsx`**:
   - Lines 24-42: Entire error boundary is hardcoded Vietnamese:
     - `"Đã xảy ra sự cố giao diện"`
     - `"Ngoại lệ phía client. Vui lòng tải lại trang hoặc bấm Thử lại."`
     - `"Thử lại"`
     - `"Về trang chủ"`

10. **`frontend/src/lib/api.ts`**:
    - Lines 27, 34, 69, 105: Hardcoded Vietnamese error parsing fallbacks:
      - `"Lỗi không xác định từ máy chủ"`
      - `"Đã xảy ra lỗi không xác định"`
      - `"Không thể kết nối tới máy chủ (Network Error)"`

---

### 1.3 Detailed Observations for Requirement R2: Bank-Grade Auth & Full Name

#### A. Database Model & Schema (`backend/db/models.py`)
- `User` class (lines 8-15):
  ```python
  class User(Base):
      __tablename__ = "users"
      id = Column(Integer, primary_key=True)
      username = Column(String(50), unique=True, index=True)
      password_hash = Column(String(128))
      created_at = Column(DateTime, default=datetime.utcnow)
      stories = relationship("Story", back_populates="author")
  ```
  *Gap*: `full_name` column is missing from `User`.
- Auto-migration history (lines 68-74):
  ```python
  try:
      with engine.connect() as conn:
          from sqlalchemy import text
          conn.execute(text("ALTER TABLE comics ADD COLUMN adapted_offset INTEGER DEFAULT 0"))
          conn.commit()
  except Exception:
      pass
  ```
  *Pattern observed*: Narrai applies runtime schema upgrade on app start using raw ALTER TABLE. Adding `full_name` via `inspector.get_columns("users")` followed by `ALTER TABLE users ADD COLUMN full_name VARCHAR(100) DEFAULT ''` will maintain complete backward compatibility for both SQLite and PostgreSQL.

#### B. Password Security & Rules (`backend/main.py`)
- Line 155-156:
  ```python
  if len(password) < 4:
      raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 4 ký tự")
  ```
  *Gap*: Only requires 4 characters! Completely lacks bank-grade security:
  - No uppercase requirement (`[A-Z]`).
  - No lowercase requirement (`[a-z]`).
  - No digit requirement (`[0-9]`).
  - No special character requirement (`[!@#$%^&*...]`).
  - No prohibition against whitespace.
  - Length minimum is 4 instead of 8-12.

#### C. Brute-Force & Rate Limiting (`backend/main.py`)
- Lines 178-216 (`login_user`):
  No attempt tracking, no IP or username throttling, no lockout period. Vulnerable to dictionary attacks and credential stuffing.

#### D. Frontend Auth Component (`frontend/src/components/modals/AuthModal.tsx`)
- Lines 18-22:
  ```tsx
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  ```
  *Gaps*:
  - No `full_name` input field.
  - No `confirm_password` input field.
  - No Password Strength Meter (progress bar / color-coded score).
  - No real-time visual checklist with checkmarks for the 5 banking rules.
  - No client-side validation preventing weak password submissions.
  - No show/hide password toggle.
  - No brute-force countdown feedback on HTTP 429.

---

## 2. Logic Chain

1. **Premise 1**: Requirement R1 dictates 100% Vietnamese ⟷ English toggling with zero hardcoded strings across the entire user experience.
   - *Observation*: 10 distinct files (`page.tsx`, `AICopilotPanel.tsx`, `LandingView.tsx`, `Phase1Idea.tsx`, `ComicViewer.tsx`, `ThemeToggle.tsx`, `error.tsx`, `api.ts`, `AuthModal.tsx`, `HistoryModal.tsx`) contain over 35 hardcoded Vietnamese or English strings, inline ternaries, and missing dictionary keys.
   - *Direct Impact*: When switching to English (`ENG`), the user still sees Vietnamese error alerts, Vietnamese undo button, Vietnamese comic retry buttons, Vietnamese Copilot messages, and Vietnamese landing page badges.
   - *Resolution*: Expand `translations.vi` and `translations.en` in `frontend/src/lib/i18n.ts` by ~45 new standardized keys. Replace every hardcoded string and inline ternary with `t[key]`. Replace browser `alert()` with a unified bilingual Toast notification system.

2. **Premise 2**: Copilot quick command chips in English ("New Intro", "Dramatic Outro", "Change Tone", "Deepen Characters") fail to trigger direct editing.
   - *Observation*: In `backend/agents/copilot_agent.py` line 205, `_is_direct_edit_request()` only matches Vietnamese keywords (`"mở đầu"`, `"sửa lại"`).
   - *Direct Impact*: Clicking English chips routes the prompt as general chat or overloads tokens, triggering the exact error in R4: *"Xin lỗi, Hệ thống chỉ huy đang gặp trục trặc nhẹ. Bạn vui lòng thử lại nhé!"*.
   - *Resolution*: Add comprehensive English intent keywords to `_is_direct_edit_request()` (`"opening"`, `"intro"`, `"ending"`, `"outro"`, `"rewrite"`, `"tone"`, `"characters"`, `"dialogue"`, `"cliffhanger"`).

3. **Premise 3**: Requirement R2 mandates bank-grade authentication with `full_name`, 5 password criteria, strength meter, visual checklist, confirm password, brute-force protection, and backward-compatible DB upgrade.
   - *Observation*: `backend/db/models.py` lacks `full_name` in `User`. `backend/main.py` only validates `len(password) < 4` and has no rate limiting. `frontend/src/components/modals/AuthModal.tsx` has no `full_name`, no confirm password, no strength meter, and no checklist.
   - *Resolution*:
     1. Add `full_name = Column(String(100), nullable=True, default="")` to `User`.
     2. Implement inspection-based auto-migration checking column existence before executing `ALTER TABLE users ADD COLUMN full_name VARCHAR(100) DEFAULT ''`.
     3. Implement strict 5-rule password validator function `validate_bank_password()` on backend and frontend.
     4. Build thread-safe `AuthRateLimiter` (5 failed attempts per IP/username -> 60s cooldown with HTTP 429).
     5. Overhaul `AuthModal.tsx` with Full Name field, Confirm Password field, live Password Strength Meter (0-100% animated bar), 5-point reactive visual checklist with green checkmarks, and localized error messages.

---

## 3. Caveats

1. **Redis Cache (R3 dependency)**:
   - While investigating R2 brute-force protection, Redis was checked. The local machine currently does not run a standing Redis service by default. Therefore, the brute-force rate limiter must be built with a standalone in-memory tracker (with TTL expiration) that gracefully integrates with the `CacheManager` being surveyed for R3.
2. **Existing Users in Database (`narrai.db`)**:
   - Existing user rows in `narrai.db` do not have `full_name`. The auto-migration sets default `""`, and `read_users_me` and `login` must fallback to `user.full_name or user.username` to prevent `null` display issues.
3. **Password Hashing Speed**:
   - `backend/auth.py` intentionally sets bcrypt rounds to 6 (`bcrypt.gensalt(rounds=6)`) to avoid CPU starvation on free-tier hosting (Render). Bank-grade complexity checks on plain text strings before hashing provide superior security without increasing bcrypt hashing latency.

---

## 4. Conclusion & Precise Architecture Blueprint

### 4.1 Requirement R1: 100% i18n Architecture Blueprint
1. **Dictionary Expansion (`frontend/src/lib/i18n.ts`)**:
   - Group translations logically: `common`, `auth`, `nav`, `landing`, `setup`, `editor`, `copilot`, `comic`, `toasts`.
   - Add all 45+ identified missing keys to both `vi` and `en` with strict TypeScript typing (`Record<Language, Record<string, string>>`).
2. **Unified Toast Notification System (`frontend/src/components/ui/Toast.tsx` & `lib/toast.ts`)**:
   - Create lightweight `ToastProvider` and `useToast()` hook.
   - Toast types: `success`, `error`, `warning`, `info`.
   - Replace 100% of browser `alert(...)` calls in `page.tsx`, `HistoryModal.tsx`, `Phase1Idea.tsx` with `toast.error(t.error_msg)` or `toast.success(t.success_msg)`.
3. **Hardcoded String Elimination**:
   - Pass `lang` to `ThemeToggle.tsx`.
   - Localize `LandingView.tsx` badge, section title, and footer.
   - Localize `Phase1Idea.tsx` tags, selected count, and category names.
   - Localize `AICopilotPanel.tsx` undo button and quick chips.
   - Localize `ComicViewer.tsx` panel error and retry buttons.
   - Localize `app/error.tsx` error boundaries.
4. **Copilot Multilingual Keyword Alignment**:
   - Update `_is_direct_edit_request` in `backend/agents/copilot_agent.py` to match all English quick command phrases.

### 4.2 Requirement R2: Bank-Grade Security Architecture Blueprint
1. **Database Schema & Auto-Migration (`backend/db/models.py`)**:
   ```python
   class User(Base):
       __tablename__ = "users"
       id = Column(Integer, primary_key=True)
       username = Column(String(50), unique=True, index=True)
       full_name = Column(String(100), nullable=True, default="")
       password_hash = Column(String(128))
       created_at = Column(DateTime, default=datetime.utcnow)
       stories = relationship("Story", back_populates="author")

   # Auto-migration
   try:
       with engine.connect() as conn:
           from sqlalchemy import text, inspect
           inspector = inspect(engine)
           if "users" in inspector.get_table_names():
               cols = [c["name"] for c in inspector.get_columns("users")]
               if "full_name" not in cols:
                   conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(100) DEFAULT ''"))
                   conn.commit()
   except Exception as e:
       print(f"Auto-migration full_name: {e}")
   ```
2. **Backend Bank-Grade Password Validator (`backend/auth.py`)**:
   ```python
   def validate_bank_password(password: str) -> Tuple[bool, str, str]:
       """Returns (is_valid, error_vi, error_en)"""
       if not password or len(password) < 8:
           return False, "Mật khẩu phải có tối thiểu 8 ký tự.", "Password must be at least 8 characters."
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
3. **Brute-Force Rate Limiter (`backend/auth.py`)**:
   - `LoginRateLimiter`: Tracks `(ip, username)` attempt timestamps.
   - Rule: Max 5 consecutive failures within 5 minutes -> 60s cooldown lock.
   - Resets failure counter upon successful login.
   - Raises `HTTPException(status_code=429, detail="Too many failed login attempts...")`.
4. **Frontend Auth Modal Overhaul (`frontend/src/components/modals/AuthModal.tsx`)**:
   - New input: `full_name` (labeled "Họ và tên" / "Full Name").
   - New input: `confirm_password` (labeled "Xác nhận mật khẩu" / "Confirm Password").
   - Show/Hide password toggle on both password inputs.
   - Real-time Strength Meter:
     - Calculates score (0 to 5) based on length >= 8, length >= 12, uppercase, lowercase, digit, special char.
     - Progress bar segments: Red (Weak) ➔ Amber (Fair) ➔ Emerald (Strong) ➔ Cyan/Indigo (Excellent).
   - Visual Checklist component:
     - 5 items with dynamic checkmark / cross icon:
       1. Độ dài 8-12+ ký tự
       2. Chữ hoa (A-Z)
       3. Chữ thường (a-z)
       4. Chữ số (0-9)
       5. Ký tự đặc biệt (!@#$%)
       6. Không khoảng trắng
   - Live confirm password match feedback.
   - Submission button disabled until all criteria pass.
5. **API & Types Update**:
   - Update `frontend/src/lib/api.ts` `register(username, password, fullName)`.
   - Update `frontend/src/lib/types.ts` `User` and `AuthResponse` with `full_name`.
   - Update `Sidebar.tsx` to render `user.full_name || user.username`.

---

## 5. Verification Method

To independently verify the survey and implementation:

1. **Database Schema Verification**:
   Run python check to ensure column `full_name` exists:
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('backend/narrai.db'); c = conn.cursor(); c.execute('PRAGMA table_info(users)'); print(c.fetchall())"
   ```
   *Expected*: Column `full_name` with type `VARCHAR(100)` is present.

2. **Backend Password & Rate Limiting Unit Tests**:
   Create a test script `backend/tests/test_bank_auth.py` asserting:
   - Rejection of weak passwords: length < 8, no uppercase, no lowercase, no digit, no special character, containing space.
   - Acceptance of valid bank password: e.g. `StrongPass123!`.
   - Registration saves `full_name`.
   - 5 consecutive failed login attempts trigger HTTP 429 Too Many Requests.

3. **Frontend Bilingual Toggling & Build Verification**:
   - Build frontend: `cd frontend && npm run build`. Ensure 0 TypeScript or lint errors.
   - Switch language between `VIE` and `ENG`:
     - Verify Navbar, ThemeToggle tooltip, Landing badge, Auth modal, Interview, Controls, Editor toolbar, Copilot quick command chips, Undo button, and Comic viewer toggle 100% accurately without a single leftover Vietnamese string in ENG or English string in VIE.
