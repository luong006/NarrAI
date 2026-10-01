# Progress: Milestone 2 Implementation

- **Last visited**: 2026-10-01T00:25:00Z
- **Current Step**: Milestone 2 Implementation and Verification Complete.
- **Status**: Complete. Ready for handoff to orchestrator.

## Completed Tasks:
1. Expanded `VIETNAMESE_HISTORICAL_CANON` in `backend/services/ontology.py` to 33 entries covering all 6 epochs and all 31 heroes with compiled `defeat_regex` invariants.
2. Expanded `BATTLE_OUTCOME_DISTORTION_PATTERNS` for major historic battles.
3. Implemented `HistoricalDistortionError` and `AISemanticHistoricalClassifier` with Pass 1 (regex evasion: Mongol triumph, De Castries victory, flag metaphor) and Pass 2 (Groq LLM fallback).
4. Implemented `AutoDetectResult` and `auto_detect_narrative_mode(prompt, context, genre)`.
5. Implemented `COMMERCIAL_IP_REGISTRY`, `CommercialIPResult` (dual dict + tuple interface), and `detect_commercial_ip(text)`.
6. Wired preflight and post-generation invariant checking into `story_generator.py` and `copilot_agent.py` to reject revisionist surgery.
7. Wired invariant enforcement, coin refunding (`REFUND_FAILED_GENERATION`), and DB quarantine into `main.py` endpoints (`/api/generate-story`, `stream_and_save`, `/api/copilot-event`).
8. Updated `backend/db/models.py` with `SocialPost.is_fanfiction` and `SocialPost.disclaimer` columns plus database auto-migration.
9. Updated `backend/services/recommender_service.py` to persist and serialize `is_fanfiction` and `disclaimer` in `publish_post`, `get_feed`, and `get_post_details`.
10. Updated `backend/routers/social_router.py` with HTTP 422 rejection on historical distortion, commercial IP detection, and fanfiction disclaimer attachment on `POST /publish`.
11. Updated `frontend/src/lib/types.ts` with `is_fanfiction` and `disclaimer` in `SocialPost` and `PublishSocialPostPayload`.
12. Updated `frontend/src/components/editor/StoryEditor.tsx` with auto-detected narrative mode badge in the top toolbar (Shield/BookOpen/Sparkles).
13. Updated `frontend/src/components/social/CommunityFeedView.tsx` with purple `Fanfiction` badges on post cards & modal header, and fanfiction disclaimer banner in the reader modal.
14. Updated `frontend/src/app/page.tsx` to pass `story_text` to `publishPost`.
