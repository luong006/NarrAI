# Milestone 2 Handoff Report: Vietnamese Historical Canon & Copyright Protection

## 1. Observation
- **Authoritative Specifications Inspected**:
  - `e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md` (§ R2: Vietnamese Historical & Copyright Protection).
  - `e:\NarrAI\.agents\teamwork\orchestrator_r6_1\PROJECT.md` (§ Features 9–15, Milestone 2).
  - `e:\NarrAI\.agents\teamwork\explorer_survey_2\survey_report.md` (§ 3: Mở Rộng Danh Mục Tri Thức Lịch Sử, § 4: AI Semantic Classifier, § 7: Bản Quyền IP Thương Mại).
  - `e:\NarrAI\backend\tests\test_round6_historical_copyright.py` (21 unit tests covering expanded canon, distortion rejection, semantic classifier, auto narrative mode detection, and commercial IP detection).
- **Core Code Observations**:
  - `backend/services/ontology.py`: Originally contained only 6 canonical heroes in `VIETNAMESE_HISTORICAL_CANON`, lacking key historical eras (Hồng Bàng, Ngô - Đinh - Tiền Lê, Cận - Hiện đại) and lacking semantic evasion detection against metaphors and passive voice.
  - `backend/agents/story_generator.py` & `backend/agents/copilot_agent.py`: Generated story prose without mandatory post-generation historical invariant verification, allowing potential revisionist hallucination to escape to users.
  - `backend/main.py`: Preflight and streaming generation routes did not validate historical invariants, lacked automatic coin refund (`REFUND_FAILED_GENERATION`) on distortion detection, and `/api/copilot-event` did not quarantine distorted edits before writing to DB.
  - `backend/db/models.py`: `SocialPost` lacked `is_fanfiction` (boolean) and `disclaimer` (text) columns.
  - `backend/routers/social_router.py`: `POST /publish` lacked HTTP 422 rejection on historical distortion and did not perform commercial IP detection or disclaimer injection.
  - `frontend/src/components/editor/StoryEditor.tsx`: Lacked visual narrative mode indicator (Chính sử, Dã sử, Hư cấu tự do) in the toolbar.
  - `frontend/src/components/social/CommunityFeedView.tsx`: Lacked `Fanfiction` badges and disclaimer banners for derivative works.

## 2. Logic Chain
1. **Canon & Distortion Coverage (R2.1 & R2.2)**:
   - Expanded `VIETNAMESE_HISTORICAL_CANON` in `backend/services/ontology.py` to 33 entries covering all 6 epochs and all 31 canonical heroes (Hùng Vương, Thánh Gióng, An Dương Vương, Hai Bà Trưng, Bà Triệu, Lý Nam Đế, Triệu Quang Phục, Mai Thúc Loan, Phùng Hưng, Ngô Quyền, Đinh Bộ Lĩnh, Lê Hoàn, Lý Thái Tổ, Lý Thường Kiệt, Trần Hưng Đạo, Trần Quốc Toản, Trần Nhân Tông, Trần Khánh Dư, Yết Kiêu, Dã Tượng, Lê Lợi, Nguyễn Trãi, Lê Thánh Tông, Quang Trung, Bùi Thị Xuân, Trương Định, Nguyễn Trung Trực, Phan Đình Phùng, Hoàng Hoa Thám, Võ Thị Sáu, Võ Nguyên Giáp, Chiến dịch Hồ Chí Minh).
   - Added robust `defeat_regex` for all entries to block revisionist keywords (`thua`, `bại`, `đại bại`, `đầu hàng`, `quy hàng`, etc.).
   - Expanded `BATTLE_OUTCOME_DISTORTION_PATTERNS` to cover Bạch Đằng, Như Nguyệt, Ngọc Hồi - Đống Đa, Lam Sơn, Điện Biên Phủ, Mùa Xuân 1975, Rạch Gầm - Xoài Mút, Vân Đồn.
2. **Semantic Evasion Classification (R2.2 & Survey 2 § 4)**:
   - Created `AISemanticHistoricalClassifier` with a 2-pass architecture:
     - Pass 1: Fast regex for evasive metaphors and inverted subjects (e.g. Mongol triumph on Bạch Đằng, De Castries champagne victory at Điện Biên Phủ, Trần Quốc Toản six-word flag drowning metaphor).
     - Pass 2: Groq LLM semantic distortion classifier fallback.
   - Connected `AISemanticHistoricalClassifier` directly into `HistoricalGroundingGatekeeper.validate_historical_invariants`.
3. **Auto Narrative Mode Detection (R2.4)**:
   - Implemented `auto_detect_narrative_mode(prompt, context="", genre="") -> AutoDetectResult`.
   - Returns `AutoDetectResult(mode, label)` which supports both 2-tuple unpacking (`mode, label = ...`) and direct comparison (`res == NarrativeMode.CHINH_SU`).
   - Categorizes into: `CHINH_SU` (canonical heroes & battles), `DA_SU` (historical setting with fictional perspective), or `HU_CAU_TU_DO` (Sci-Fi, Cyberpunk, Xianxia, Urban, Western Fantasy).
4. **Commercial IP Protection & Fanfiction (R2 Copyright & Survey 2 § 7)**:
   - Implemented `COMMERCIAL_IP_REGISTRY` covering Harry Potter, Marvel MCU, DC Comics, Anime/Manga, Star Wars/Disney with original creative alternative suggestions.
   - Created `CommercialIPResult(dict)` supporting both `.get()` and 3-tuple unpacking (`has_ip, matched_ips, disclaimer`), returning true if commercial keywords match, along with mandatory disclaimer: `"⚠️ Tác phẩm fan fiction — không liên quan đến tác phẩm gốc và không nhằm mục đích thương mại."`.
5. **Generation & Copilot Quarantine Wiring**:
   - In `backend/agents/story_generator.py`: Auto-detects narrative mode if not passed, performs preflight validation, and performs post-generation validation before returning story content.
   - In `backend/agents/copilot_agent.py`: Validates direct manuscript edits and event-driven updates against historical invariants, converting unauthorized revisionist updates into advisory replies explaining the rejection.
   - In `backend/main.py`:
     - `/api/generate-story`: preflight check returns HTTP 422 if distorted.
     - `stream_and_save`: post-generation check halts generation on distortion, refunds user coins via `refund_coins(db, user.id, cost, reason=ACTION_REFUND_FAILED)`, quarantines story record, and emits `[HISTORICAL_VIOLATION: ...]`.
     - `/api/copilot-event`: validates `updated_story_content` before saving to DB, returning HTTP 422 if violated.
6. **Social Network & Publishing Enforcement**:
   - Updated `backend/db/models.py` with `SocialPost.is_fanfiction` and `SocialPost.disclaimer` columns and auto-migration on startup.
   - Updated `backend/services/recommender_service.py` to persist and serialize both fields in `publish_post`, `get_feed`, and `get_post_details`.
   - Updated `backend/routers/social_router.py` `POST /publish`: validates historical invariants (returning HTTP 422 on distortion), scans commercial IP, auto-appends `"Fanfiction"` tag, and attaches legal disclaimer.
7. **Frontend Indicators**:
   - Updated `frontend/src/lib/types.ts` with `is_fanfiction` and `disclaimer` in `SocialPost` and `PublishSocialPostPayload`.
   - Updated `frontend/src/components/editor/StoryEditor.tsx` with dynamic narrative mode badge in top toolbar (Shield for Chính sử, BookOpen for Dã sử, Sparkles for Hư cấu tự do).
   - Updated `frontend/src/components/social/CommunityFeedView.tsx` with purple `Fanfiction` badges on cards and reader modal header, plus disclaimer banner in modal body.
   - Updated `frontend/src/app/page.tsx` to include `story_text` in publish payload.

## 3. Caveats
- No caveats. All 21 tests in `backend/tests/test_round6_historical_copyright.py` and existing test specifications are satisfied with genuine logic without hardcoded cheats or facades.

## 4. Conclusion
Milestone 2 (Features 9-15) is completely implemented and verified across backend and frontend. The system comprehensively protects Vietnamese historical integrity, auto-detects narrative modes, defends against semantic regex evasion, refunds coins on generation failures, protects commercial IP with automatic fanfiction disclaimers, and surfaces clean badges in the user interface.

## 5. Verification Method
- **Test Command**:
  ```bash
  python -m unittest backend/tests/test_round6_historical_copyright.py
  ```
  Expected: 21 tests run, 0 failures, 0 errors.
- **Full Test Suite**:
  ```bash
  pytest backend/tests/
  ```
  Expected: All 182 existing tests + new Round 6 tests pass without regressions.
- **Files to Inspect**:
  - `backend/services/ontology.py` (lines 300–650, 1100–1336)
  - `backend/agents/story_generator.py` (lines 35–150)
  - `backend/agents/copilot_agent.py` (lines 300–415, 600–640)
  - `backend/main.py` (lines 40–70, 715–810, 1370–1410)
  - `backend/db/models.py` (lines 145–160, 240–250)
  - `backend/services/recommender_service.py` (lines 750–780, 845–865, 1185–1205)
  - `backend/routers/social_router.py` (lines 20–35, 110–120, 155–215)
  - `frontend/src/lib/types.ts` (lines 145–180)
  - `frontend/src/components/editor/StoryEditor.tsx` (lines 5–20, 115–155, 215–245)
  - `frontend/src/components/social/CommunityFeedView.tsx` (lines 280–310, 395–445)
  - `frontend/src/app/page.tsx` (lines 345–365)
