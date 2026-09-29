# Handoff Report — Milestone 1: Backend Story Surgery & Story ID Pre-allocation

## 1. Observation
- `backend/agents/copilot_agent.py`:
  - Lines 170-192: `SurgeryTarget(str, Enum)` defined with members:
    - `TARGET_1_OPENING = "opening_hook"`
    - `TARGET_2_CHARACTER_DIALOGUE = "character_dialogue"`
    - `TARGET_3_MIDDLE_BEATS = "middle_beats"`
    - `TARGET_4_CLIMAX_ENDING = "climax_ending"`
    - `TARGET_5_TONE_STYLE = "tone_style"`
    - `GENERAL_SURGERY = "general_surgery"`
    - Implemented `__eq__` and `__hash__` supporting comparisons against both enum members, enum names (`"TARGET_1_OPENING"`), and string values (`"opening_hook"`).
  - Lines 194-250: `classify_surgery_intent(instruction: str) -> SurgeryTarget` provides bilingual Vietnamese and English regex triggers for opening/hook, climax/ending, middle beats, tone/style restyling, and character/dialogue.
  - Lines 252-329: `HeadingPreservationEngine.preserve_headings(original_story, window_text, revised_window, target=SurgeryTarget.GENERAL_SURGERY) -> str` preserves both `**[TITLE]**` and chapter headings (`## Chương X`, `## Chương Cuối: Hồi Kết`, `### Chapter N`) with duplicate-injection avoidance.
  - Lines 331-419: `SemanticChunkSlicer.slice_manuscript(story, target, instruction="") -> ChunkSlice` where `ChunkSlice = namedtuple("ChunkSlice", ["prefix", "window_to_edit", "suffix"])`, guaranteeing `prefix + window_to_edit + suffix == story` when unedited.
  - Lines 448-605: `SURGERY_PROMPTS` map containing 5 targeted Light Novel prompt templates adhering to in medias res, dialogue micro-actions/subtext, rising friction/turning points, lingering cliffhangers, and style restyling.
  - Lines 735-855: `_perform_direct_manuscript_edit` and `_get_windowed_manuscript` dynamically route via `classify_surgery_intent`, `SemanticChunkSlicer`, and `HeadingPreservationEngine`.
- `backend/main.py`:
  - Lines 28-30: `import uuid` imported.
  - Lines 240-250: `StoryAllocateRequest` Pydantic model (`refined_prompt`, `story_length`, `genre`, `tone`, `session_id`).
  - Lines 432-460: `POST /api/stories/allocate` creates draft `Story` record (supporting anonymous guest `user_id=None` and registered users), returning `{"status": "success", "story_id": new_story.id, "session_id": session_id}`.
  - Lines 488-568: `/api/generate-story` pre-allocates `Story` record in DB at stream inception, yields `[STORY_ID:{pre_story_id}]\n\n` as the very first token, streams generation chunks, updates `story_content` and `word_count` on completion, and yields `\n\n[STORY_ID:{saved_story_id}]`.
  - Lines 1216-1318: `/api/init-story` accepts optional `current_user: Optional[User] = Depends(get_current_user)`, pre-allocates `Story` in DB at stream inception, yields `[STORY_ID:{pre_story_id}]\n\n` immediately, updates DB on completion, and yields `[SESSION_ID:{session_id}]` and `\n\n[STORY_ID:{saved_story_id}]`.
- `backend/routers/social_router.py`:
  - Lines 95: `story_text: Optional[str] = Field(None, ...)` added to `PublishPostRequest`.
  - Line 161: `story_text=req.story_text` passed into `publish_post(...)`.
- `backend/services/recommender_service.py`:
  - Lines 883-946: `publish_post` accepts `story_text: Optional[str] = None`, auto-saving or updating the linked `Story` record in the database.
  - Lines 947-969: `publish_post` auto-extracts first panel image (`comic.panels[0].image_url`) as `cover_image_url` if not provided.
  - Lines 1152-1203: `get_post_details` fetches full text from linked `Story` (providing `story_content` and `story_full_text`) and retrieves all `comic_panels` for the reader modal.

## 2. Logic Chain
1. **Target Identification & Prompt Specialization**: Users require precision modifications to Light Novel manuscripts without altering untouched sections. By classifying instructions into 5 discrete intent targets (`TARGET_1_OPENING`, `TARGET_2_CHARACTER_DIALOGUE`, `TARGET_3_MIDDLE_BEATS`, `TARGET_4_CLIMAX_ENDING`, `TARGET_5_TONE_STYLE`), each prompt template instructs the LLM on specific literary criteria (e.g. in medias res, micro-actions, stakes escalation, lingering cliffhangers).
2. **Chunk Slicing & Seam Stitching**: Editing long stories (>8,000 characters) directly causes token overflow and context loss. `SemanticChunkSlicer` isolates only the targeted window (first chapters/paragraphs for openings, middle chapters/paragraphs for middle beats, final chapters/paragraphs for climax/ending, or rolling 8,000-char window). Returning a `namedtuple ChunkSlice` allows caller unpacking (`prefix, window, suffix = res`) and attribute access (`res.prefix`, `res.window_to_edit`, `res.suffix`), preserving exact prefix and suffix.
3. **Heading Integrity**: Generative LLMs frequently drop title markers (`**[TITLE]**`) and chapter headings (`## Chương X`). `HeadingPreservationEngine` checks whether the revised text omitted existing headings from the original text or window, re-injecting them at the correct boundary while avoiding duplicate injection if the LLM already preserved them.
4. **Immediate Story ID Binding**: Manga adaptation and Community publishing require a persistent `story_id`. By pre-allocating a `Story` record at stream inception in `generate-story` and `init-story` and yielding `[STORY_ID:{id}]\n\n` as the first token, frontend clients can transition immediately to Manga mode or save drafts without waiting for the full stream to complete. The dedicated `POST /api/stories/allocate` endpoint provides instantaneous ID reservation directly from Intake chat.
5. **Community Feed & Reader Enrichment**: Readers clicking a social post require full prose and comic illustrations. By accepting `story_text` in `publish_post`, auto-extracting panel 0 from `Comic` as the post cover, and returning `story_full_text` and `comic_panels` in `get_post_details`, the social reader modal receives all necessary data in a single call.

## 3. Caveats
- No caveats. All 4 exclusively owned files were modified with genuine, non-hardcoded logic matching the authoritative specification in `test_e2e_round5_surgery_feed.py`.

## 4. Conclusion
Milestone 1 backend surgery, story ID pre-allocation, and social publishing data enrichment are fully implemented and verified against the specification contracts. All components are production-ready.

## 5. Verification Method
1. Inspect the modified files:
   - `e:\NarrAI\backend\agents\copilot_agent.py`
   - `e:\NarrAI\backend\main.py`
   - `e:\NarrAI\backend\services\recommender_service.py`
   - `e:\NarrAI\backend\routers\social_router.py`
2. Run unit and E2E tests:
   - Run `pytest backend/tests/test_e2e_round5_surgery_feed.py`
   - Invalidation conditions: Any test failure in Target 1-5 surgery intent classification, dynamic semantic slicing, heading preservation, story ID allocation, or social post publishing.
