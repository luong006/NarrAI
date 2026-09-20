# Detailed Code Changes — Milestone 2 (R2: Manga Character Visual Consistency & Deterministic Seed)

## Summary of Modifications

Milestone 2 establishes strict visual continuity across sequential manga frames and locks diffusion latent space using canonical story-level deterministic seeds.

### 1. `backend/agents/comic_agent.py`
- **Upgraded `DNA_EXTRACTOR_PROMPT`**:
  - Configured prompt for a lead character designer and visual continuity director in a professional manga studio.
  - Mandated visual physical traits: exact garment type & cut, fabric texture & specific colors, collar/neck/chest accessories (ribbon tie, bow tie, pendant, brooch, collar pin, chest badge, jade pendant on red cord).
  - Mandated immutable hairstyle (length, cut, texture, bangs, center/side parting, hair accessories).
  - Mandated immutable facial features (age, eye shape and color, sharp jawline, permanent marks).
  - Added structured metadata schema: `gender` ("female" / "male"), `role` ("lead", "antagonist", "supporting", etc.), and comprehensive `aliases` registry (Vietnamese pronouns, generic nouns, and English equivalents).
- **Updated `extract_character_dna`**:
  - When loading characters from `memory.story_bible.characters`:
    - Populates `aliases` with lowercase character full name as well as first/last name sub-tokens.
    - Inspects gender and role cues to auto-enrich with Vietnamese pronouns:
      - Female: `"cô bé"`, `"nữ sinh"`, `"cô ấy"`, `"nàng"`, `"cô gái"`, `"chị"`, `"em gái"`, `"bé gái"`, `"she"`, `"her"`, `"girl"`, `"schoolgirl"`, `"female student"`.
      - Male: `"anh bạn"`, `"bạn cùng bàn"`, `"học sinh nam"`, `"cậu ấy"`, `"chàng trai"`, `"anh ấy"`, `"thiếu niên"`, `"cậu bạn"`, `"cậu bé"`, `"nam sinh"`, `"he"`, `"him"`, `"boy"`, `"schoolboy"`, `"male student"`.
      - Desk mate / classmate: `"anh bạn cùng bàn"`, `"cô bạn cùng bàn"`, `"bạn cùng bàn"`, `"bạn cùng lớp"`, `"bạn học"`, `"người bạn"`, `"desk mate"`, `"classmate"`.
      - Student / lead: `"học sinh"`, `"student"`.
    - Injects `prior_context` into the LLM extraction prompt so the model maintains visual continuity with previously known characters.
    - Added guaranteed fallback with rich aliases covering both male and female pronouns.
- **Overhauled Smart DNA Injection in `_validate_panels`**:
  - Scans both `image_prompt` and `dialogue_text` combined (`search_text = f"{prompt} {dialogue}"`).
  - Implements the Vietnamese Semantic Pronoun Dictionary with gender-appropriate mapping for all registered characters.
  - Implemented safe regex boundary matching `rf"(?<!\w){re.escape(alias)}(?!\w)"` preventing substring false positives (e.g., character "An" does not match `"clean"`, `"another"`, or `"panoramic"`).
  - Added specialized protection for short alias `"an"` so that English article usages (e.g. `"An establishing shot"`, `"an extreme close-up"`, `"an empty room"`) are distinguished from the character name `"An"`.
  - Removed the premature `break` at line 210: loop now accumulates all matching characters in the scene and joins their visual DNAs with commas, ensuring secondary characters are never dropped in dialogue/action panels.
  - Replaced blind fallback (`char_entry_list[0]`) with gender- and role-aware resolution: scans for female cues (`girl`, `cô gái`, etc.) or male cues (`boy`, `chàng trai`, etc.), falling back to the designated `lead`/`protagonist` character.
  - In `generate_comic_script`, ensured dictionary `dna` objects are safely unpacked via `dna.get('dna', dna)`.

### 2. `backend/services/cloudflare_ai.py`
- Added `get_deterministic_comic_seed(story_id: int | None = 1) -> int`:
  - Formula: `(int(anchor_id) * 7919 + 4289000) % 900000 + 100000`
  - Guarantees fixed, deterministic 6-digit seeds strictly in the range `[100000, 999999]`.
- Updated `get_cached_or_generate_image`:
  - Added parameter `story_id: Optional[int] = None`.
  - If `seed is None` and `story_id is not None`, computes `panel_seed = get_deterministic_comic_seed(story_id)`.
  - Ensures both Cloudflare Workers AI call and Pollinations fallback redirect share the identical synchronized seed.

### 3. `backend/main.py`
- Imported `get_deterministic_comic_seed` from `services.cloudflare_ai`.
- In `/api/comic/image/{panel_id}` (and added alias route `/api/comics/panels/{panel_id}/image`):
  - Resolves canonical `story_id` from `(panel.comic.story_id if panel.comic else None) or panel.comic_id or 1`.
  - Computes `comic_seed = get_deterministic_comic_seed(story_id)`.
  - Passes `seed=comic_seed, story_id=story_id` into `get_cached_or_generate_image`.
  - Uses `comic_seed` in Pollinations fallback redirect URL.

### 4. `backend/tests/test_comic_dna_seed.py`
- Created comprehensive unit test suite covering:
  - `test_dna_extractor_prompt_structure`: verifies studio designer constraints, garment cut, fabric, collar, accessories, hairstyle, facial permanence, and metadata schema.
  - `test_extract_character_dna_story_bible_aliases`: verifies StoryMemory alias population, sub-token splitting, and gender-appropriate pronoun enrichment.
  - `test_smart_dna_injection_female_pronoun`: verifies dialogue containing `"cô bé"` injects female lead DNA.
  - `test_smart_dna_injection_male_deskmate_pronoun`: verifies dialogue containing `"anh bạn cùng bàn"` injects desk mate DNA.
  - `test_regex_boundary_protection_an_false_positives`: verifies boundary regex prevents `"An"` from matching `"An establishing shot"`, `"clean"`, or `"another"`, while matching genuine character occurrences in prompt and dialogue.
  - `test_multi_character_injection_no_early_break`: verifies duel scene with Lý Tiêu and Hắc Ma Quân injects BOTH character DNAs without dropping either.
  - `test_multi_character_pronoun_dialogue`: verifies dialogue with `"Cô bé nhìn anh bạn cùng bàn mỉm cười"` injects both characters.
  - `test_gender_aware_fallback`: verifies human indicators without explicit names resolve by female/male cues.
  - `test_deterministic_comic_seed_formula_and_range`: verifies mathematical formula, invariance across 100 iterations, and bounded range `[100000, 999999]`.
  - `test_get_cached_or_generate_image_uses_story_id`: verifies diffusion generation call receives synchronized story seed when `seed is None`.
