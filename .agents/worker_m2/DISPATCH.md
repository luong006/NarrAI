## 2026-09-19T14:02:00Z
You are Worker subagent for Milestone 2 of the NarrAI project.
Working directory: e:\NarrAI\.agents\worker_m2
Identity: worker_m2
Parent conversation ID: 6bf39d70-f735-4c2a-8a7a-0d9642a300c3

Read e:\NarrAI\.agents\ORIGINAL_REQUEST.md carefully before doing anything else.
Read e:\NarrAI\PROJECT.md and survey report e:\NarrAI\.agents\explorer_survey_2\handoff.md and analysis.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Exclusive File Ownership for Milestone 2 (R2: Khóa Cứng Tính Nhất Quán Nhân Vật Manga & Deterministic Seed):
Files you own:
- backend/agents/comic_agent.py (DNA_EXTRACTOR_PROMPT, extract_character_dna, and Smart Character DNA injection in _validate_panels)
- backend/services/cloudflare_ai.py (get_deterministic_comic_seed and seed handling in get_cached_or_generate_image)
- backend/main.py (comic image generation endpoint around lines 530-550 linking panel to story_id seed)
- backend/tests/test_comic_dna_seed.py (unit tests for R2)

Tasks to implement:
1. `backend/agents/comic_agent.py`:
   - Upgrade `DNA_EXTRACTOR_PROMPT`:
     - Professional manga studio lead designer prompt.
     - Mandatory visual traits: exact garment type, fabric texture, separate distinct colors, collar/neck/chest accessories (ribbon tie, bow tie, pendant, brooch, collar pin), exact immutable hairstyle/texture/parting/bangs, immutable facial features (eye shape, jawline, marks).
     - Metadata fields: `gender` ("male", "female"), `role` ("lead", "antagonist", "supporting"), and rich `aliases`.
   - Update `extract_character_dna`:
     - When loading from `memory.story_bible.characters`, populate aliases with lowercase name, first/last names, and gender-appropriate pronoun aliases.
   - Overhaul Smart DNA Injection in `_validate_panels`:
     - Inspect BOTH `item.get("image_prompt", "")` AND `item.get("dialogue_text", "")`.
     - Implement Vietnamese Semantic Pronoun Dictionary:
       - Female pronouns/nouns: "cô bé", "nữ sinh", "cô ấy", "nàng", "cô gái", "chị", "em gái", "bé gái".
       - Male pronouns/nouns: "anh bạn", "bạn cùng bàn", "học sinh nam", "cậu ấy", "chàng trai", "anh ấy", "thiếu niên", "cậu bạn".
       - Relational/neutral: "học sinh", "bạn cùng lớp", "bạn học", "người bạn".
     - Use word boundary regex matching (`\b` or boundary checks) to prevent false positives (e.g., character "An" must NOT match "an establishing shot" or "clean").
     - Remove the premature `break` at line 210: accumulate and inject ALL matching characters present in the scene into `image_prompt`.
     - If no explicit match, use gender/role-aware fallback instead of blindly picking character 0.
2. `backend/services/cloudflare_ai.py`:
   - Add `get_deterministic_comic_seed(story_id: int) -> int`:
     `return (int(story_id) * 7919 + 4289000) % 900000 + 100000`
   - In `get_cached_or_generate_image`, accept `story_id: Optional[int] = None`. If `seed is None` and `story_id is not None`, compute seed via `get_deterministic_comic_seed(story_id)`.
3. `backend/main.py`:
   - In `/api/comics/panels/{panel_id}/image`, resolve `story_id` from `panel.comic.story_id` (fallback to `panel.comic_id` or 1), compute `comic_seed = get_deterministic_comic_seed(story_id)`, and pass to `get_cached_or_generate_image`.
4. `backend/tests/test_comic_dna_seed.py`:
   - Create unit tests verifying DNA prompt structure, Smart DNA injection with pronouns, regex boundary protection against substring false positives ("An" vs "an establishing shot"), multi-character injection, and deterministic seed generation.

Verification:
- Compile touched files: `python -m py_compile backend/agents/comic_agent.py backend/services/cloudflare_ai.py backend/main.py backend/tests/test_comic_dna_seed.py`
- Run test suite: `python backend/tests/test_comic_dna_seed.py`

Document changes in:
- `e:\NarrAI\.agents\worker_m2\changes.md`
- `e:\NarrAI\.agents\worker_m2\handoff.md`
Send message to parent when done.
