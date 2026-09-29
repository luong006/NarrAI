## 2026-09-29T03:30:42Z
Read e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md.
Read e:\NarrAI\PROJECT.md.
Read e:\NarrAI\.agents\teamwork\explorer_r5_survey_1\survey_report.md.

You are the Backend Surgery & Story ID Implementer for Milestone 1.
Your working directory is e:\NarrAI\.agents\teamwork\worker_r5_m1.
You own exclusively:
- backend/agents/copilot_agent.py
- backend/main.py
- backend/services/recommender_service.py
- backend/routers/social_router.py

Tasks to implement:
1. 5-Target Intent Classifier in copilot_agent.py:
   - TARGET_1_OPENING (Opening/Hook rewrite)
   - TARGET_2_CHARACTER_DIALOGUE (Character names, pronouns, modern phrasing, subtext, micro-actions)
   - TARGET_3_MIDDLE_BEATS (Middle beats, pacing, scene insertion)
   - TARGET_4_CLIMAX_ENDING (Climax & ending cliffhanger / emotional surge)
   - TARGET_5_TONE_STYLE (Tone shift & style restyling across manuscript)
2. Dynamic Semantic Chunk Slicing (prefix -> window_to_edit -> suffix) respecting chapter markers (## Chương X) and semantic paragraph boundaries.
3. Structural Heading Preservation Engine: Zero-loss guarantee for **[TITLE]** and ## Chương X across all surgery targets.
4. 5 targeted Light Novel prompt templates in copilot_agent.py.
5. In backend/main.py: Pre-allocate story_id at stream inception in /api/init-story and /api/generate-story (for both guests and registered users), yielding [STORY_ID:{id}] immediately. Implement endpoint POST /api/stories/allocate.
6. In backend/services/recommender_service.py and backend/routers/social_router.py:
   - In publish_post: accept story_text and auto-save/update Story; auto-extract first panel from Comic as cover_image_url if missing.
   - In get_post_details: return full story_content and comic_panels for reader modal.
7. Verification: Run python -m py_compile on modified files and run existing tests (e.g. test_copilot_bilingual_resilience.py).
8. Write detailed handoff.md in your working directory. Update progress.md with timestamp.
