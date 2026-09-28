## 2026-09-20T14:04:11Z

You are worker_r2_m3, a specialized implementation Worker subagent.
Your Working Directory: e:\NarrAI\.agents\worker_r2_m3
Workspace Directory: e:\NarrAI
Original Request File: e:\NarrAI\.agents\ORIGINAL_REQUEST.md (MANDATORY: Read this first! Focus on ## 2026-09-20T13:19:05Z - Requirement R3).
Project Document: e:\NarrAI\.agents\PROJECT.md
Explorer Survey Report: e:\NarrAI\.agents\explorer_survey_r2_3\report.md (MANDATORY: Read this report carefully! It contains exact line numbers, architectural design, and proposed code for R3).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Exclusive File Write Ownership:
- backend/agents/comic_agent.py
- backend/services/cloudflare_ai.py
- backend/tests/test_comic_modern_school_sync.py (new comprehensive test suite)

Objectives for Milestone 3 (R3. Text-to-Image Sync & Manga Hallucination Elimination):
1. Lock in Modern Monochrome School Manga Art Style:
   - In backend/agents/comic_agent.py:
     * Update STYLE_PREFIX to:
       "masterpiece modern monochrome manga, Japanese high school manga comic art style, crisp clean black and white ink lineart, professional manga panel layout, "
     * Update STYLE_SUFFIX to:
       ", clean G-pen lineart, delicate screentone shading, fine dot pattern tones, high contrast black ink on bright white paper, no color, pure monochrome, studio quality 2D manga illustration, expressive anime aesthetic, sharp contours"

2. Purge Historical/Wuxia Priming from DNA Extractor:
   - In DNA_EXTRACTOR_PROMPT:
     * Remove all ancient/wuxia tokens: "huyền bào", "dragon hem", "jade pendant on red cord", "crimson red mantle".
     * Replace with modern school uniform exemplars: crisp button-up shirt, navy blazer, pleated skirt, tailored trousers, school tie/ribbon, chest badge.
     * Enforce compact visual DNA representation (<30 words per character) to preserve CLIP 77 token budget.

3. Enforce 100% Panel Spatial Enclosure Anchoring & Quarantine Filter:
   - Implement SPATIAL_ENCLOSURES, resolve_spatial_enclosure, and sanitize_spatial_prompt in backend/agents/comic_agent.py.
   - Enforce that setting_anchor is attached to 100% of panels (remove layout == "wide" bypass and 'background' presence bypass).
   - In sanitize_spatial_prompt: Strip out conflicting/outdoor/traffic/ancient keywords (street, road, highway, car, traffic, palace, temple, castle) before rendering indoor classroom scenes, while preserving subwords like 'classroom'.

4. Implement Action/Gesture Semantic Mapping from Prose:
   - In backend/agents/comic_agent.py:
     * Implement ACTION_GESTURE_MAPPINGS and extract_action_from_prose(dialogue_or_prose).
     * Map Vietnamese prose actions ("cúi đầu cặm cụi viết bài", "nhìn ra cửa sổ", "quay sang nói chuyện", "đứng bật dậy", "gục đầu xuống bàn", "nhìn lên bảng đen") into exact physical character actions at the desk/room.
     * In _validate_panels and _create_structured_beat_fallback: use the extracted action instead of hardcoded generic strings.

5. Master Negative Prompt & School Exclusions:
   - In backend/services/cloudflare_ai.py:
     * Define BASE_NEGATIVE_PROMPT (banning colors, photoreal, Western comics, speech bubbles, text/watermark).
     * Define MODERN_SCHOOL_EXCLUSIONS (banning historical robes, hanfu, kimono, armor, swords, palaces, busy streets/cars).
     * Define get_master_negative_prompt(genre: str = "school").
     * Update generate_image_cf and get_cached_or_generate_image to use get_master_negative_prompt() and support custom_negative_prompt suffixes.

6. Comprehensive Unit Testing:
   - Create backend/tests/test_comic_modern_school_sync.py:
     * Test ACTION_GESTURE_MAPPINGS: "An cặm cụi ghi chép bài" -> sitting at wooden student desk, writing attentively.
     * Test Spatial Quarantine Filter: "sitting at desk near busy street and moving cars" -> strips street and cars.
     * Test 100% panel anchor attachment across square, tall, and wide layouts.
     * Test DNA extractor prompt lacks wuxia priming.
     * Test cloudflare_ai negative prompt contains MODERN_SCHOOL_EXCLUSIONS.
   - Run python -m py_compile backend/agents/comic_agent.py backend/services/cloudflare_ai.py backend/tests/test_comic_modern_school_sync.py.
   - Run python -m unittest backend/tests/test_comic_modern_school_sync.py -v.
   - Run existing regression tests: test_comic_zero_truncation.py, test_comic_dna_seed.py, test_comic_ontology_visuals.py, test_adversarial_dsgo.py, test_dynamic_scene_graph.py, test_light_novel_engine.py.

7. Report all findings, changes, and verification in e:\NarrAI\.agents\worker_r2_m3\handoff.md and notify parent.
