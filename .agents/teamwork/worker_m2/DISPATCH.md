## 2026-09-30T17:03:36Z

You are worker_m2, a teamwork_preview_worker agent.
Your working directory is e:\NarrAI\.agents\teamwork\worker_m2.
Your parent orchestrator is orchestrator_r6_1 (conv ID: 92e67f82-c02c-4fa1-9967-5963454f8d77).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY INSTRUCTIONS:
1. Read the authoritative user request at e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md, especially section ## 2026-09-30T16:30:48Z (R2: Vietnamese Historical & Copyright Protection).
2. Read the project specification at e:\NarrAI\.agents\teamwork\orchestrator_r6_1\PROJECT.md (Milestone 2).
3. Read the technical survey report at e:\NarrAI\.agents\teamwork\explorer_survey_2\survey_report.md.
4. Inspect the test suite contracts in `backend/tests/test_round6_historical_copyright.py`.

ASSIGNED SCOPE: Milestone 2 (Features 9-15):
A. Vietnamese Historical Canon & Semantic Classifier (`backend/services/ontology.py`):
   1. Expand `VIETNAMESE_HISTORICAL_CANON` from 6 to 31 heroes across all 6 epochs (Hùng Vương, Thánh Gióng, An Dương Vương, Bà Triệu, Lý Nam Đế, Triệu Quang Phục, Mai Thúc Loan, Phùng Hưng, Ngô Quyền, Đinh Bộ Lĩnh, Lê Hoàn, Lý Thái Tổ, Lý Thường Kiệt, Trần Hưng Đạo, Trần Quốc Toản, Trần Nhân Tông, Trần Khánh Dư, Yết Kiêu, Dã Tượng, Lê Lợi, Nguyễn Trãi, Lê Thánh Tông, Quang Trung, Bùi Thị Xuân, Trương Định, Nguyễn Trung Trực, Phan Đình Phùng, Hoàng Hoa Thám, Võ Thị Sáu, Võ Nguyên Giáp, Đại thắng Mùa Xuân 1975) with associated battles/events and core invariants.
   2. Expand `BATTLE_OUTCOME_DISTORTION_PATTERNS`.
   3. Implement `AISemanticHistoricalClassifier` (2-pass: fast regex + LLM semantic analysis fallback) to catch regex bypass like "quân Mông Cổ ca khúc khải hoàn trên sông Bạch Đằng" or unlisted heroes.
   4. Implement `auto_detect_narrative_mode(prompt: str, context: str = "") -> NarrativeMode` that automatically classifies into `CHINH_SU`, `DA_SU`, or `HU_CAU_TU_DO` based on context, without manual UI selection.
   5. Implement `COMMERCIAL_IP_REGISTRY` and `detect_commercial_ip(text: str) -> Tuple[bool, List[str], str]`.

B. Post-Generation Validation Wiring & Hard-Blocking:
   6. In `backend/agents/story_generator.py`: Call `HistoricalGroundingGatekeeper.validate_historical_invariants(story_content, mode, prompt)` post-generation. If invalid, halt and raise distortion error.
   7. In `backend/agents/copilot_agent.py`: Import `HistoricalGroundingGatekeeper`. Call `validate_historical_invariants` on `updated_story_content` before applying edits. Reject revisionist surgery.
   8. In `backend/main.py`: In `/api/generate-story` and `stream_and_save`, validate invariants. If invalid, halt generation, yield error event, and trigger coin refund `REFUND_FAILED_GENERATION`.

C. Publish Protection & Copyright Disclaimer:
   9. In `backend/db/models.py`: Add `is_fanfiction = Column(Boolean, default=False)` and `disclaimer = Column(Text, nullable=True)` to `SocialPost`, with startup auto-migration.
   10. In `backend/routers/social_router.py`: In `POST /publish`, validate historical invariants (reject 422 if distorted); call `detect_commercial_ip`; if detected, auto-set `is_fanfiction = True` and attach disclaimer `⚠️ Tác phẩm fan fiction — không liên quan đến tác phẩm gốc và không nhằm mục đích thương mại`.

D. Frontend UI Components:
   11. In `frontend/src/components/editor/StoryEditor.tsx`: Render auto-detected narrative mode badge in top toolbar.
   12. In `frontend/src/components/social/CommunityFeedView.tsx`: Render fanfiction badge and reader disclaimer banner on posts with `is_fanfiction`.

E. Verification:
   - Run `python -m unittest backend/tests/test_round6_historical_copyright.py`.
   - Run `python backend/tests/run_all_tests.py` (confirm 182 existing tests continue to pass 100%).
   - Write your handoff report to `e:\NarrAI\.agents\teamwork\worker_m2\handoff.md` and send a message back to orchestrator_r6_1.
