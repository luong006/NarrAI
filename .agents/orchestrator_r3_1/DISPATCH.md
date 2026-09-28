# Dispatch Instructions

## 2026-09-22T04:36:48Z

You are the Project Orchestrator for the NarrAI Comprehensive Upgrade.

Working Directory: e:\NarrAI\.agents\orchestrator_r3_1
Workspace Directory: e:\NarrAI
Authoritative Request: Read e:\NarrAI\.agents\ORIGINAL_REQUEST.md (specifically the latest request under ## 2026-09-22T04:35:39Z).

Your objective is to lead the team to fulfill all requirements R1 to R7 and satisfy all Acceptance Criteria:
1. R1. Hoàn Thiện Song Ngữ (i18n) Toàn Diện 100% (Anh ⟷ Việt) không sót bất kỳ hardcoded string nào trên toàn bộ UI (navbar, copilot buttons, toasts, auth modal, story interview, editor toolbar, comic viewer).
2. R2. Hệ Thống Đăng Nhập / Đăng Ký Chuẩn Bảo Mật Ngân Hàng & Họ Tên Đầy Đủ (full_name, mật khẩu 5 tiêu chí: độ dài >= 8, chữ hoa, thường, số, ký tự đặc biệt, no whitespace; Password Strength Meter & checklist thời gian thực; confirm password; chống brute force/spam; thông báo lỗi đa ngôn ngữ; DB auto upgrade backward compatible).
3. R3. Tích Hợp & Kiểm Tra Bộ Nhớ Đệm Redis (Redis Cache Layer with Fallback sang in-memory LRU/TTL cache, query latency < 20ms).
4. R4. Khắc Phục Triệt Để Lỗi Tương Tác AI Co-pilot (đa ngôn ngữ lệnh tiếng Anh & tiếng Việt như "Rewrite in a darker, more gripping thriller tone", token budget quản lý an toàn, tự động thử lại/fallback).
5. R5. Đột Phá Chất Văn Tiểu Thuyết — Loại Bỏ Văn Phong AI, Nâng Chuẩn Tác Giả Chuyên Nghiệp (anti-cliché banlist 0 vi phạm, Show Don't Tell, In Medias Res, thoại sắc sảo có subtext).
6. R6. Khóa Cứng Tính Nhất Quán Ngoại Hình Nhân Vật Truyện Tranh (Face, Hair, Outfits đưa lên đầu ngân sách 77 token CLIP, đồng bộ Visual DNA qua các khung tranh).
7. R7. Triệt Tiêu 100% Tranh Màu & Khắc Phục Lỗi Khung Tranh Không Hiển Thị (100% monochrome manga với server post-processing grayscale/thresholding, nội bộ xử lý URL/retry/disk cache/fallback, 0% broken image).

Ensure:
- py_compile compiles cleanly across all backend modules.
- npm run build succeeds 0 errors on frontend.
- Rigorous unit and adversarial tests covering all requirements.
- Maintain your progress in e:\NarrAI\.agents\orchestrator_r3_1\progress.md and BRIEFING.md.
- When all criteria are verified, report completion to the Sentinel.
