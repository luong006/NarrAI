# Handoff Report: Requirement 1 (R1) Survey
## Adaptive Open-Ontology, 3 Narrative Modes, Tri-Tier Resolver & Smart Selective Language Filter

- **Agent**: Explorer Survey 1 (`teamwork_preview_explorer`)
- **Recipient**: Parent Orchestrator (`917dbd03-2475-4a83-acdb-bab7b7e5cc76`)
- **Handoff Type**: Hard (Task Complete)
- **Date**: 2026-09-28

---

## 1. Observation

Direct code and architectural observations across the codebase:

1. **Hardcoded Japanese School Manga Overfitting in Comic Director**:
   - `backend/agents/comic_agent.py` lines 9–17:
     ```python
     STYLE_PREFIX = (
         "masterpiece modern monochrome manga, Japanese high school manga comic art style, "
         "crisp clean black and white ink lineart, professional manga panel layout, "
     )
     ```
   - `backend/agents/comic_agent.py` lines 121–158: `SPATIAL_ENCLOSURES` only defines `"classroom"`, `"school_hallway"`, and `"school_rooftop"`. In `resolve_spatial_enclosure` (line 170):
     ```python
     if not matched_enc:
         matched_enc = dict(SPATIAL_ENCLOSURES["classroom"])
     ```
   - `backend/agents/comic_agent.py` lines 26–59: `DNA_EXTRACTOR_PROMPT` hardcodes school uniform examples: `"crisp white short-sleeve school uniform button-up shirt with stiff collar, small dark navy ribbon tie pinned at collar, pleated dark navy skirt"`.
   - `backend/agents/comic_agent.py` lines 250–300: `ACTION_GESTURE_MAPPINGS` hardcodes classroom gestures (`"sitting at wooden student desk"`, `"looking forward toward the classroom blackboard"`, `"open sliding classroom doorway"`).

2. **Rigid Era Bans in Ontology & Scene Graph**:
   - `backend/models/scene_graph.py` lines 286–291:
     ```python
     DEFAULT_MODERN_ERA_BANLIST: List[str] = [
         "hanfu", "robes", "flowing robes", "sword", "swords", "magic staff",
         "cultivation", "flying sword", "ancient", "medieval", "kimono",
         "samurai armor", "plate armor", "armor", "taichi", "wuxia", "xianxia",
         "chariot", "ancient scroll", "jade pendant", "taoist robes"
     ]
     ```
   - `backend/models/scene_graph.py` lines 399–440: `sanitize_era_prompt` unconditionally strips swords, robes, and ancient armor if the era is modern or unspecified.
   - `backend/agents/story_memory.py` lines 144–163: `StoryMemory.init_scene_graph_from_bible` unconditionally assigns `era_name="modern_2020s"`, `era_banlist=["hanfu", "robes", "sword", "magic", "cultivation"]`, and enclosure `SpaceEnclosure(name="Lớp học")`.
   - `backend/services/cloudflare_ai.py` lines 32–45: `MODERN_SCHOOL_EXCLUSIONS` bans all historical clothing, ancient robes, armor, swords, palaces, etc.

3. **Inflexible Cliché Handling in Story Generator**:
   - `backend/agents/story_generator.py` lines 60–98: `AI_CLICHE_BANLIST` only contains 36 patterns for general AI tropes (e.g. `"nhanh như nhịp tim chậm rãi"`, `"khoảng trống trong lòng"`).
   - `backend/agents/story_generator.py` lines 100–120: `validate_anti_cliche_compliance(text: str)` checks only `AI_CLICHE_BANLIST`. It does not detect or selectively filter Chinese-translation tropes (`"tiêu sái"`, `"tà mị"`, `"lãnh khốc"`, `"bản tọa"`, `"đế tôn"`).
   - `grep_search` across `backend` revealed zero existing occurrences of `"tiêu sái"` or `"tà mị"` in the codebase.

4. **Absence of Narrative Mode and Cultural Tier Abstractions**:
   - `backend/models/scene_graph.py` and `backend/agents/story_memory.py` contain no fields for `narrative_mode` or `cultural_tier`.
   - `backend/main.py` request models (`GenerateStoryRequest` line 147, `InitStoryRequest` line 807) only take `refined_prompt` and `story_length`.
   - `frontend/src/components/setup/Phase1Idea.tsx` contains 28 genres and trending topics, but no selector for the 3 narrative modes.

---

## 2. Logic Chain

1. **From Observation 1 & 2 to Core Problem**:
   - Because `SPATIAL_ENCLOSURES` defaults to `"classroom"`, `StoryMemory.init_scene_graph_from_bible` sets `SpaceEnclosure` to `"Lớp học"`, and `DEFAULT_MODERN_ERA_BANLIST` strips swords and robes, the system is incapable of properly processing historical Vietnamese epics, hybrid sci-fi, or open-domain fantasy. Historical figures would be placed in classrooms and swords would be stripped.
2. **From Requirement 1 & Observation 3 to Solution for Modes & Tiers**:
   - Introducing `NarrativeMode` (Mode 1: Strict Historical, Mode 2: Historical Fiction, Mode 3: Free Fiction) and `TriTierOntologyResolver` (Tier 1: Canonical VN $\ge 0.7$, Tier 2: Hybrid $0.3 \le S < 0.7$, Tier 3: Open Domain $< 0.3$) directly solves this by dynamically conditioning the ontology, style anchors, visual DNA, and negative prompts on the resolved tier and chosen mode.
3. **From Observation 3 to Smart Language Filter**:
   - Because translation clichés (`"tiêu sái"`, `"tà mị"`, `"lãnh khốc"`, `"bản tọa"`, `"đế tôn"`) are currently completely unhandled in `story_generator.py`, adding `TRANSLATION_CLICHE_BANLIST` and conditioning its enforcement on `genre not in ["tiên hiệp", "kiếm hiệp", "wuxia", "xianxia"]` ensures that pure Vietnamese literature remains untainted while genre fans of Xianxia/Wuxia are not arbitrarily penalized.
4. **From Observation 1 & Cloudflare AI to Master Negative Filter**:
   - In Tier 1 (Canonical VN), the biggest diffusion model error is confusing Vietnamese traditional attire (`Áo Ngũ Thân`, `Áo Nhật Bình`, `Áo Tấc`, `Khăn Đóng`) with Chinese Hanfu or Japanese Kimono. Introducing `VIETNAMESE_CANONICAL_NEGATIVE_PROMPT` containing `Hanfu, Kimono, Hanbok, Samurai, Ninja` in `services/cloudflare_ai.py` and `agents/comic_agent.py` guarantees 100% Vietnamese visual purity.

---

## 3. Caveats

- **Network / External Diffusion Models**: The investigation observed the fallback chain in `services/cloudflare_ai.py` (`@cf/bytedance/stable-diffusion-xl-lightning`, `@cf/lykon/dreamshaper-8-lcm`, `@cf/stabilityai/stable-diffusion-xl-base-1.0`). If Cloudflare AI tokens are exhausted, the local monochrome fallback generates procedural manga panels.
- **LLM Token Limits**: `_extract_narrative_ontology` runs on Groq (`openai/gpt-oss-120b`). Prompt size must stay within limits when injecting historical invariants.

---

## 4. Conclusion

The codebase survey for Requirement 1 is complete.
The architecture is fully documented with exact code locations, proposed data structures, and algorithms in `report.md`.
Implementing Requirement 1 requires:
1. Creating `backend/services/ontology.py` containing:
   - `NarrativeMode` and `CulturalTier` enums.
   - `HistoricalGroundingGatekeeper` with Vietnamese Historical Knowledge Base (Hai Bà Trưng, Ngô Quyền, Lý Thường Kiệt, Trần Hưng Đạo, Lê Lợi, Quang Trung; Bạch Đằng, Như Nguyệt, Ngọc Hồi - Đống Đa) and invariant checks.
   - `TriTierOntologyResolver` with cultural similarity scoring ($S_{cult}$ thresholds $0.7$ and $0.3$), Tier-aware visual DNA, and Master Negative filters against `Hanfu/Kimono/Samurai/Ninja`.
   - `SmartSelectiveLanguageFilter` with `TRANSLATION_CLICHE_BANLIST` allowing clichés for Xianxia/Wuxia and strictly suppressing them for pure Vietnamese/historical prose.
   - `extract_dynamic_ephemeral_node` for Tier 3 Open Domain.
2. Integrating this service into:
   - `backend/models/scene_graph.py` (decouple modern school bias, add tier/mode fields).
   - `backend/agents/story_generator.py` (mode-aware prompting and smart cliché filtering).
   - `backend/agents/comic_agent.py` (Vietnamese attire DNA, traditional enclosures, master negative filter).
   - `backend/services/cloudflare_ai.py` (tier-aware master negative prompt).
   - `backend/agents/story_memory.py` (tier-aware scene graph bootstrap).
   - `backend/agents/copilot_agent.py` (historical guard awareness).
   - `backend/main.py` (mode/genre parameters and resolution endpoints).
   - `frontend/src/` (3-mode selector, i18n, and workspace state).

---

## 5. Verification Method

1. **Python Compilation Verification**:
   ```powershell
   python -m py_compile backend/models/scene_graph.py backend/agents/story_generator.py backend/agents/comic_agent.py backend/services/cloudflare_ai.py backend/agents/story_memory.py backend/agents/copilot_agent.py backend/main.py
   ```
2. **Unit & Invariant Test Execution**:
   Run the test runner to verify existing invariant tests pass:
   ```powershell
   python -m unittest backend/tests/test_dynamic_scene_graph.py backend/tests/test_comic_modern_school_sync.py backend/tests/test_light_novel_engine.py
   ```
3. **New Test Suite for R1**:
   Inspect and execute `backend/tests/test_adaptive_open_ontology.py` (to be written during implementation) covering:
   - Historical invariant checks (e.g. Trần Hưng Đạo defeating Mongol invaders).
   - Tri-tier resolution accuracy across 3 distinct test cases (Canonical VN, Hybrid Cyberpunk, Western Detective).
   - Selective cliché suppression across genre boundaries (Wuxia vs Pure VN).
   - Visual DNA & Master Negative filter verification.
4. **Invalidation Conditions**:
   - If historical falsifications (e.g. "Trần Hưng Đạo bại trận") pass validation in Mode 1 without violation.
   - If Chinese Hanfu / Kimono / Samurai are not banned in Tier 1.
   - If translated clichés ("tiêu sái", "tà mị") are allowed in pure Vietnamese or historical prose.
   - If translated clichés are blocked when the user explicitly selects "Tiên hiệp" or "Kiếm hiệp".
