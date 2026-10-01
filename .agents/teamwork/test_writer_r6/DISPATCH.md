## 2026-09-30T16:43:32Z
You are test_writer_r6, a teamwork_preview_test_writer agent.
Your working directory is e:\NarrAI\.agents\teamwork\test_writer_r6.
Your parent orchestrator is orchestrator_r6_1 (conv ID: 92e67f82-c02c-4fa1-9967-5963454f8d77).

MANDATORY INSTRUCTIONS:
1. Read the authoritative user request at e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md, especially section ## 2026-09-30T16:30:48Z.
2. Read the project specification at e:\NarrAI\.agents\teamwork\orchestrator_r6_1\PROJECT.md.
3. Read the technical survey reports:
   - e:\NarrAI\.agents\teamwork\explorer_survey_1\survey_report.md
   - e:\NarrAI\.agents\teamwork\explorer_survey_2\survey_report.md
   - e:\NarrAI\.agents\teamwork\explorer_survey_3\survey_report.md

ASSIGNED SCOPE: E2E Testing Track (Milestone 5 Test Suites):
Design and author comprehensive, opaque-box, requirement-driven test suites in `backend/tests/`:
1. `test_round6_copilot_surgery.py`:
   - Test chapter targeting: "sửa Chương 2" or "sửa Chương 3" correctly slices and edits only that chapter in a multi-chapter story.
   - Test `instruction` utilization in `SemanticChunkSlicer`.
   - Test selectedText targeting.
   - Test Path B non-truncation: long story (>5000 chars) edited via Path B does NOT lose preceding text.
   - Test intermediate heading preservation: multi-chapter edit preserves `## Chương 1`, `## Chương 2`, `## Chương 3` in correct relative order.
2. `test_round6_historical_copyright.py`:
   - Test 31 heroes canon and invariant validation.
   - Test rejection of historical distortion: "Trần Hưng Đạo thua trận Bạch Đằng" blocked.
   - Test AI semantic classifier: regex evasion ("quân Mông Cổ ca khúc khải hoàn trên sông Bạch Đằng") blocked.
   - Test 3 narrative modes auto-detection (`CHINH_SU`, `DA_SU`, `HU_CAU_TU_DO`).
   - Test commercial IP copyright detection and fanfiction disclaimer attachment on publish.
3. `test_round6_social_features.py`:
   - Test Follow / Unfollow CRUD & following feed.
   - Test Threaded comments with `parent_comment_id`.
   - Test Bookmarks / personal library CRUD.
   - Test Notifications CRUD.
   - Test Content Reports CRUD.
   - Test Author Profiles.
   - Test Trending leaderboards (weekly / monthly).
4. `test_round6_wal_performance.py`:
   - Test SQLite WAL mode (`PRAGMA journal_mode;` returns `wal` on disk-backed DB).
   - Test indexes on Comic, ComicPanel, SocialPost, and composite indexes.
   - Test GZipMiddleware compression on responses >= 500 bytes.
5. `test_round6_tfjs_export.py`:
   - Test `GET /api/recommender/export-vectors` returns 128-dim vectors.

Create `TEST_INFRA.md` in `e:\NarrAI\.agents\teamwork\test_writer_r6\TEST_INFRA.md`.
Execute test discovery or python unittest to verify your test suites syntax and execution.
Write your handoff report to `e:\NarrAI\.agents\teamwork\test_writer_r6\handoff.md` and send a message back to orchestrator_r6_1.
