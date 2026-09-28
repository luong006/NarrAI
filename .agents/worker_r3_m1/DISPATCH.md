## 2026-09-22T04:49:10Z

You are worker_r3_m1, an implementation worker.
Working directory: e:\NarrAI\.agents\worker_r3_m1
Workspace directory: e:\NarrAI

Mandatory reading: Read e:\NarrAI\.agents\ORIGINAL_REQUEST.md (specifically the latest request under ## 2026-09-22T04:35:39Z).
Technical specification: Read e:\NarrAI\.agents\explorer_survey_r3_1\handoff.md and e:\NarrAI\.agents\PROJECT.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write Ownership (You exclusively own and will modify these files):
- backend/db/models.py
- backend/auth.py
- backend/main.py (auth routes & register/login)
- backend/tests/test_bank_auth.py
- frontend/src/lib/i18n.ts
- frontend/src/lib/toast.ts
- frontend/src/lib/api.ts
- frontend/src/lib/types.ts
- frontend/src/components/ui/Toast.tsx
- frontend/src/components/modals/AuthModal.tsx
- frontend/src/components/layout/ThemeToggle.tsx
- frontend/src/components/layout/Sidebar.tsx
- frontend/src/components/landing/LandingView.tsx
- frontend/src/components/setup/Phase1Idea.tsx
- frontend/src/components/setup/Phase2Interview.tsx
- frontend/src/components/setup/Phase3Controls.tsx
- frontend/src/components/editor/AICopilotPanel.tsx
- frontend/src/app/error.tsx
- frontend/src/app/page.tsx
- frontend/src/app/layout.tsx

Your Objectives (Milestone 1: R1 i18n 100% & R2 Bank-Grade Auth):
1. Backend Database Model & Auto-Migration:
   - In `backend/db/models.py`, add `full_name = Column(String(100), nullable=True, default="")` to `User`.
   - Add inspection-based auto-migration checking column existence and executing `ALTER TABLE users ADD COLUMN full_name VARCHAR(100) DEFAULT ''` seamlessly for SQLite and PostgreSQL.
2. Backend Bank-Grade Password Validation & Rate Limiting:
   - In `backend/auth.py`, implement `validate_bank_password(password: str) -> Tuple[bool, str, str]`:
     * Length >= 8 (strictly 8-12+ chars)
     * At least 1 uppercase letter (A-Z)
     * At least 1 lowercase letter (a-z)
     * At least 1 digit (0-9)
     * At least 1 special character (!@#$%^&*...)
     * No whitespace allowed
     * Returns clear bilingual error messages (vi & en)
   - In `backend/auth.py`, implement `LoginRateLimiter`:
     * Tracks failed attempts by (ip, username)
     * Locks out for 60s after 5 failed attempts with HTTP 429 Too Many Requests
     * Resets failure counter upon successful login
   - In `backend/main.py`:
     * Update `/api/register` to accept `full_name`, validate bank password, store `full_name`.
     * Update `/api/login` to integrate `LoginRateLimiter`, return `full_name` in auth response.
     * Update `/api/users/me` to return `full_name`.
3. Frontend i18n Dictionary Expansion:
   - In `frontend/src/lib/i18n.ts`, expand `translations.vi` and `translations.en` with all 45+ missing keys identified in `explorer_survey_r3_1/handoff.md`.
4. Unified Toast Notification System:
   - Create `frontend/src/components/ui/Toast.tsx` and `frontend/src/lib/toast.ts` with `ToastProvider` and `useToast()` hook supporting success, error, warning, info toasts.
   - Wrap application in `ToastProvider` (in `layout.tsx` or `page.tsx`).
   - Replace 100% of browser `alert(...)` calls in `page.tsx`, `HistoryModal.tsx`, `Phase1Idea.tsx`, etc. with proper bilingual toasts.
5. AuthModal Security & Full Name Overhaul:
   - In `frontend/src/components/modals/AuthModal.tsx`:
     * Add `full_name` input field with translation label.
     * Add `confirm_password` input field with real-time match validation.
     * Add real-time animated Password Strength Meter (0-100% color-coded progress bar).
     * Add 5-rule reactive visual checklist with green checkmark / red circle icons.
     * Add show/hide password toggle icons.
     * Handle HTTP 429 brute-force lockout with bilingual countdown message.
6. Eliminate All Hardcoded Strings:
   - Update `ThemeToggle.tsx` (pass lang prop, localize title and aria-label).
   - Update `LandingView.tsx` (localize hero badge, feature section header, footer).
   - Update `Phase1Idea.tsx` (localize tags, selected count, and trending topics).
   - Update `Phase2Interview.tsx` and `Phase3Controls.tsx` (localize subtitles).
   - Update `AICopilotPanel.tsx` (localize undo button, quick prompt chips, character count).
   - Update `Sidebar.tsx` to display `user.full_name || user.username`.
   - Update `app/error.tsx` with bilingual error boundary.
   - Update `lib/api.ts` error messages.

Testing & Verification Requirements:
1. Write and run unit test `backend/tests/test_bank_auth.py` verifying:
   - Valid bank passwords accepted.
   - Weak passwords rejected (length < 8, no uppercase, no lowercase, no digit, no special char, whitespace).
   - Registration saves `full_name`.
   - Rate limiting triggers HTTP 429 after 5 failures.
2. Run `python -m py_compile backend/main.py backend/auth.py backend/db/models.py`.
3. Run `npm run build` in `frontend/` and confirm 0 errors.

Report your progress in `e:\NarrAI\.agents\worker_r3_m1\progress.md` and write a complete handoff report to `e:\NarrAI\.agents\worker_r3_m1\handoff.md`. Send a completion message when done.
