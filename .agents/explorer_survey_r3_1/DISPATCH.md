## 2026-09-22T04:38:00Z
Objective: Conduct a thorough, code-level investigation of the existing codebase for Requirements R1 and R2:
- R1: Hoàn Thiện Song Ngữ (i18n) Toàn Diện 100% (Anh ⟷ Việt)
  Examine frontend architecture in `frontend/`. Check how i18n is currently structured (`frontend/lib/i18n.ts`, language contexts, locale files, dictionaries). Scan all components: navbar, copilot buttons/drawer, toasts, auth modal, story interview/wizard, editor toolbar & action buttons, comic viewer. Identify every single hardcoded English or Vietnamese string, missing dictionary key, and how language toggling works across components.
- R2: Hệ Thống Đăng Nhập / Đăng Ký Chuẩn Bảo Mật Ngân Hàng & Họ Tên Đầy Đủ
  Examine backend auth and user database schemas: `backend/routers/auth.py`, `backend/db/database.py`, models, password hashing, and migration history.
  Examine frontend auth components (`frontend/components/AuthModal.tsx` or similar).
  Determine how to add `full_name` (backward-compatible auto DB upgrade for SQLite/Postgres), the 5 password rules (min length 8-12, upper, lower, digit, special character, no whitespace) on both frontend and backend, real-time Password Strength Meter and visual checklist, confirm password field, rate-limiting / brute force protection, and multilingual error messages.
