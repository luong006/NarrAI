# Comprehensive Codebase Survey Report: Requirement 1 (R1)
## Adaptive Open-Ontology, 3 Narrative Modes, Tri-Tier Ontology Resolver & Smart Selective Language Filter

- **Author**: Explorer Survey 1 (`teamwork_preview_explorer`)
- **Date**: 2026-09-28
- **Project**: NarrAI (e:\NarrAI)
- **Target Specification**: `ORIGINAL_REQUEST.md` (Section ## 2026-09-28T01:01:31Z)

---

## 1. Executive Summary & Problem Diagnosis

### 1.1 The Architectural Bottleneck
In the current milestone iterations (Milestone 2 & 3), NarrAI introduced a powerful **Dynamic Scene-Graph Ontology (DSGO)** and **Comic Director Agent**. However, these systems suffered from severe **domain over-specialization and rigid overfitting to Modern Japanese School Manga**:

1. **Hardcoded Japanese School Biases in Comic Generation (`backend/agents/comic_agent.py`)**:
   - `STYLE_PREFIX` (lines 9–12) hardcodes `"masterpiece modern monochrome manga, Japanese high school manga comic art style..."`.
   - `SPATIAL_ENCLOSURES` (lines 121–158) only defines `"classroom"`, `"school_hallway"`, and `"school_rooftop"`. Any unmapped indoor scene defaults unconditionally to a school classroom with wooden student desks, green chalkboard, and school windows.
   - `DNA_EXTRACTOR_PROMPT` (lines 26–60) strictly prompts for `"17yo Vietnamese student"`, short-sleeve school uniforms, sailor collars, and necktie ribbons.
   - `ACTION_GESTURE_MAPPINGS` (lines 250–300) hardcodes classroom gestures (`"sitting at wooden student desk"`, `"looking forward toward classroom blackboard"`, `"holding school backpack strap"`).

2. **Rigid Era Bans in Ontology & Scene Graph (`backend/models/scene_graph.py`)**:
   - `DEFAULT_MODERN_ERA_BANLIST` (lines 286–291) unconditionally bans `hanfu, robes, flowing robes, sword, swords, magic staff, cultivation, flying sword, ancient, medieval, kimono, samurai armor, plate armor, armor, taichi, wuxia, xianxia, chariot, ancient scroll, jade pendant, taoist robes`.
   - `sanitize_era_prompt` (lines 399–440) strips these tokens whenever the setting is deemed "modern" or unspecified.
   - `StoryMemory.init_scene_graph_from_bible` (`backend/agents/story_memory.py` lines 144–163) unconditionally builds an `EraGenreConstraint` with `era_name="modern_2020s"`, `era_banlist=["hanfu", "robes", "sword", "magic", "cultivation"]`, and enclosure `"Lớp học"`.
   - Result: If a user attempts to write a Vietnamese historical epic (e.g., King Quang Trung at the Battle of Ngọc Hồi - Đống Đa or General Trần Hưng Đạo at Bạch Đằng River), swords, armor, and battlefields are stripped or quarantined!

3. **Absence of Historical Grounding & Respect for Vietnamese History**:
   - There is no validator to ensure that Vietnamese historical figures, timelines, and battle outcomes remain authentic. A generative hallucination like "Trần Hưng Đạo bại trận Bạch Đằng" could slip through undetected.
   - There is no distinction between strict authentic history (Chính sử), historical fiction with fictional personal protagonists (Dã sử), and free fantasy/modern fiction (Hư cấu tự do).

4. **Inflexible Cliché Filtering (`backend/agents/story_generator.py`)**:
   - `AI_CLICHE_BANLIST` (lines 60–98) bans general AI tropes, but does not handle or selectively filter awkward translation tropes (`"tiêu sái"`, `"tà mị"`, `"lãnh khốc"`, `"bản tọa"`, `"đế tôn"`).
   - If a user writes pure Vietnamese literature or historical prose, these sáo ngữ Hán-Việt dịch sượng severely degrade literary quality. However, if the user deliberately selects **Tiên hiệp** (Xianxia) or **Kiếm hiệp** (Wuxia), these terms are genre-native idioms that must be permitted.

---

## 2. Exhaustive Codebase Survey & Inspection Findings

### 2.1 `backend/models/scene_graph.py` (34,616 bytes, 882 lines)
- **Current Responsibilities**:
  - Defines Pydantic models: `VitalityState`, `EntityRole`, `BoundaryType`, `EraType` (lines 16–44).
  - Dimension 1: `CharacterEntity` (lines 50–128) and `ItemEntity` (lines 130–155).
  - Dimension 2: `SpaceEnclosure` (lines 161–204) with `build_enclosure_fragment()`, `boundary_type`, `architectural_anchor`, `negative_drift_tokens`.
  - Dimension 3: `EraGenreConstraint` (lines 210–273) with `era_name`, `genre_name`, `world_axioms`, `era_banlist`, `mandatory_style_anchor`, `forbidden_visual_tokens`, `forbidden_prose_cliches`.
  - Sanitizers: `sanitize_spatial_prompt` (lines 354–397) and `sanitize_era_prompt` (lines 399–441).
  - Graph Master: `DynamicSceneGraph` (lines 447–881) with invariant gatekeepers:
    - `validate_vitality` (line 514)
    - `validate_spatial_exclusivity` (line 528)
    - `validate_era_consistency` (line 553)
    - `validate_action` (line 570)
    - `transition_scene` (line 619)
    - `gate_scene_transition` (line 688)
    - `build_enclosure_prompt_fragment` (line 753)
    - `get_combined_negative_tokens` (line 760)
    - `sanitize_prompt` (line 786)
- **Gaps for Requirement 1**:
  - `EraType` only has `MODERN_2020S`, `HISTORICAL_MEDIEVAL`, `ANCIENT_EAST_ASIA`, `CYBERPUNK_2099`, `VICTORIAN_1890S`, `CUSTOM`. It lacks Vietnamese dynasties and canonical periods (`VIETNAMESE_CANONICAL`, `VIETNAMESE_FUSION`, `OPEN_DOMAIN`).
  - No concept of `NarrativeMode` (Chính sử, Dã sử, Hư cấu tự do).
  - No concept of `CulturalTier` (Tier 1 Canonical, Tier 2 Hybrid Fusion, Tier 3 Open Domain).
  - Negative token generation (`get_combined_negative_tokens`) assumes modern school defaults. It lacks master negative filtering against cultural distortion (`Hanfu, Kimono, Hanbok, Samurai, Ninja`) for Vietnamese domains, and lacks relaxation for Open Domain.

### 2.2 `backend/agents/story_generator.py` (26,100 bytes, 379 lines)
- **Current Responsibilities**:
  - `LIGHT_NOVEL_ENGINE_RULES` (lines 8–47): 7 writing rules (Tight POV & In Medias Res, Rich Interior Monologue, Youth Dialogue, Fast-paced Staccato Pacing, 5 Dramatic Beats, Anti-Cliché Banlist, 4-Pillar Show Don't Tell).
  - `AI_CLICHE_BANLIST` (lines 60–98): 36 regex patterns for AI cliché detection.
  - `validate_anti_cliche_compliance(text: str)` (lines 100–120): Programmatic validator returning `(is_clean, violations)`.
  - `_extract_narrative_ontology(refined_prompt: str)` (lines 126–189): LLM call with system prompt `"Bạn là Kiến trúc sư Dynamic Scene-Graph Ontology kiêm Chuyên gia Light Novel..."`. Hardcodes modern assumptions in fallback (lines 166, 180).
  - `_build_prompt(refined_prompt, story_length)` (lines 199–241): Combines Light Novel prompt with `ontology_block`.
  - `generate_chapter_stream(memory, user_instruction)` (lines 253–310): Injects `bible_block`, `memory_block`, and `spatial_enclosure_note`.
  - `generate_ending_stream(memory)` (lines 311–341): Generates story resolution.
- **Gaps for Requirement 1**:
  - Prompt rules assume contemporary Vietnamese Light Novel; they do not adapt to historical Vietnamese honorifics (`Bệ hạ/khanh, chàng/nàng, u/con, tía/má, đồng chí`) in Historical Mode or high fantasy in Open Domain.
  - Cliché banlist does not differentiate between standard AI tropes and translated Wuxia/Xianxia clichés (`"tiêu sái"`, `"tà mị"`, `"lãnh khốc"`, `"bản tọa"`, `"đế tôn"`).
  - Does not receive or respect `narrative_mode` or `cultural_tier`.

### 2.3 `backend/agents/comic_agent.py` (61,609 bytes, 1,148 lines)
- **Current Responsibilities**:
  - `STYLE_PREFIX` and `STYLE_SUFFIX` (lines 9–17): Modern monochrome school manga style.
  - `DNA_EXTRACTOR_PROMPT` (lines 26–60): Prompts LLM to extract character visual DNA.
  - `SETTING_EXTRACTOR_PROMPT` (lines 63–78): Extracts spatial anchor and atmosphere.
  - `BEAT_DIRECTOR_PROMPT` (lines 81–117): Master comic director prompt enforcing sequential beat-by-beat panels with 0% ellipsis.
  - `SPATIAL_ENCLOSURES` (lines 121–158): Registry for classroom, school hallway, school rooftop.
  - `resolve_spatial_enclosure` (lines 160–179): Matches keywords against `SPATIAL_ENCLOSURES`, defaults to `classroom`.
  - `sanitize_spatial_prompt` (lines 181–226): Strips forbidden spatial tokens.
  - `extract_action_from_prose` (lines 301–314) and `ACTION_GESTURE_MAPPINGS` (lines 250–300): Hardcoded classroom actions.
  - `extract_character_dna` (lines 486–660): Pulls from DSGO `memory.dynamic_scene_graph.entities`, or falls back to LLM extraction.
  - `extract_setting_dna` (lines 661–722): Pulls active enclosure from DSGO or falls back to LLM.
  - `_validate_panels` (lines 731–1002): Injects character DNA into CLIP position 1 (~15–42 tokens), cleans duplicate tags, applies `STYLE_PREFIX` + `STYLE_SUFFIX`.
  - `generate_comic_script` (lines 1004–1045): Full storyboard pipeline.
  - `_create_structured_beat_fallback` (lines 1087–1148): Sentence-boundary fallback with zero ellipsis.
- **Gaps for Requirement 1**:
  - Complete absence of Vietnamese traditional attire DNA (`Áo Ngũ Thân`, `Áo Nhật Bình`, `Áo Tấc`, `Khăn Đóng`, `Áo Bà Ba`, `Nón Lá`).
  - No master negative filter against `Hanfu, Kimono, Hanbok, Samurai, Ninja` when generating Vietnamese cultural visuals.
  - No adaptation for Open Domain (Tier 3) or Cultural Fusion (Tier 2).

### 2.4 `backend/services/cloudflare_ai.py` (11,015 bytes, 270 lines)
- **Current Responsibilities**:
  - `BASE_NEGATIVE_PROMPT` (lines 22–29): Pure monochrome manga negative prompt.
  - `MODERN_SCHOOL_EXCLUSIONS` (lines 32–37): Excludes ancient robes, hanfu, kimono, armor, swords, palaces, etc.
  - `get_master_negative_prompt(genre: str = "school")` (lines 39–45): If `genre == "school"`, appends `MODERN_SCHOOL_EXCLUSIONS`.
  - `get_deterministic_comic_seed(story_id: int | None = 1)` (lines 53–60): Seed formula `(story_id * 7919 + 4289000) % 900000 + 100000`.
  - `generate_image_cf(...)` (lines 62–115): Cloudflare Workers AI runner with fallback chain across 3 diffusion models.
  - `get_cached_or_generate_image(...)` (lines 153–229): Local disk cache + Cloudflare AI call + grayscale post-processing (`ImageOps.grayscale`).
- **Gaps for Requirement 1**:
  - Negative prompt logic only knows about `MODERN_SCHOOL_EXCLUSIONS`.
  - Needs a dedicated `VIETNAMESE_CANONICAL_NEGATIVE_PROMPT` (`Hanfu, Kimono, Hanbok, Samurai, Ninja, Katana, Geisha, Qing queue, traditional Chinese attire, Japanese kimono...`).
  - Needs an adaptive resolver that builds negative prompts based on `cultural_tier` and `narrative_mode`.

### 2.5 `backend/agents/story_memory.py` (11,809 bytes, 300 lines)
- **Current Responsibilities**:
  - `StoryBible` (lines 42–110): `title`, `genre`, `characters`, `world_setting`, `main_plot`, `writing_style`, `refined_prompt`, `narrative_beats`.
  - `StoryMemory` (lines 111–300): Long-term memory store tracking chapter summaries, character states, unresolved threads, relationship map, and `dynamic_scene_graph`.
  - `init_scene_graph_from_bible()` (lines 131–197): Auto-bootstraps `DynamicSceneGraph`. Hardcodes `era_name="modern_2020s"` and `SpaceEnclosure(name="Lớp học", boundary_type=INDOOR_ENCLOSED)`.
- **Gaps for Requirement 1**:
  - `StoryBible` lacks `narrative_mode: str` and `cultural_tier: int`.
  - `init_scene_graph_from_bible` must query the `TriTierOntologyResolver` to construct an appropriate `EraGenreConstraint` and initial `SpaceEnclosure` (e.g., Hoàng thành Thăng Long, Cổng làng, Trạm không gian, etc., instead of always Classroom!).

### 2.6 `backend/agents/copilot_agent.py` (27,165 bytes, 555 lines)
- **Current Responsibilities**:
  - `COPILOT_SYSTEM_PROMPT` (lines 133–168): Defines Master Controller capabilities: `edit_story_direct`, `command_writer`, `reply_user`, `reject_and_rewrite`, `heal_image`.
  - `DIRECT_EDIT_PROMPT` (lines 170–195): Direct manuscript editing engine with In Medias Res, Tight POV, and 0% JSON leakage.
  - `_is_direct_edit_request(user_msg)` (lines 265–334): Bilingual heuristic detector.
  - `unwrap_story_prose(text)` (lines 22–129): 10-pass unwrapper preventing raw JSON display.
- **Gaps for Requirement 1**:
  - Copilot prompts must be conditioned on `narrative_mode`. In Mode 1 (Chính sử), Copilot must refuse to make historical distortions (e.g. changing historical battle outcomes or turning historic heroes into traitors). In Mode 3, Copilot has complete semantic freedom.

### 2.7 `backend/agents/memory_extractor.py` (10,045 bytes, 227 lines)
- **Current Responsibilities**:
  - `extract_bible(refined_prompt: str)` (lines 41–88): Uses `qwen/qwen3.8-27b` to extract `StoryBible` JSON.
  - `extract_memory(new_chapter_text, current_memory)` (lines 89–227): Extracts chapter summary, character states, threads, spatial transitions, and runs `gate_scene_transition`.
  - Creates new `SpaceEnclosure` nodes dynamically when spatial transitions occur (lines 191–207).
- **Gaps for Requirement 1**:
  - `extract_bible` must extract `narrative_mode` and identify whether the context has historical or cultural entities.
  - Ephemeral node extraction for Tier 3 (Open Domain) should extract arbitrary world anchors, technology levels, and races (e.g., alien planets, Victorian streets, magic academies).

### 2.8 `backend/main.py` (46,771 bytes, 1,153 lines)
- **Current Endpoints**:
  - `/api/chat-interview` (line 299)
  - `/api/refine-prompt` (line 310)
  - `/api/generate-story` (line 334)
  - `/api/init-story` (line 939)
  - `/api/generate-chapter` (line 1012)
  - `/api/end-story` (line 1079)
  - `/api/copilot-event` (line 824)
  - `/api/comic/generate` (line 594)
  - `/api/comic/continue` (line 636)
  - `/api/comic/image/{panel_id}` (line 694)
- **Gaps for Requirement 1**:
  - Request models (`GenerateStoryRequest`, `InitStoryRequest`, `ChapterRequest`) do not explicitly accept `narrative_mode` or `genre` or expose ontology tier resolution.
  - Need dedicated ontology inspection / resolver endpoints (e.g., `/api/ontology/resolve`, `/api/ontology/validate`).

### 2.9 `frontend/` (Next.js 14 App Router)
- **Current Structure**:
  - `frontend/src/lib/types.ts`: Models for `User`, `StoryDetail`, `ComicPanel`, `GenreCategory`.
  - `frontend/src/components/setup/Phase1Idea.tsx`: 28 genres grouped into 5 categories, trending themes, custom idea input.
  - `frontend/src/components/setup/Phase2Interview.tsx`: Interactive chat interview.
  - `frontend/src/components/setup/Phase3Controls.tsx`: Sliders for Story Length, Creativity, Pacing.
  - `frontend/src/components/editor/StoryEditor.tsx`: Main drafting surface.
  - `frontend/src/components/editor/AICopilotPanel.tsx`: AI Co-pilot chat and quick actions.
  - `frontend/src/app/page.tsx`: Workspace orchestration.
- **Gaps for Requirement 1**:
  - No UI selector for the **3 Narrative Modes** (Chính Sử, Dã Sử, Hư Cấu Tự Do).
  - No indicator showing the resolved **Cultural Tier** (Tier 1 Canonical VN, Tier 2 Hybrid Fusion, Tier 3 Open Domain).
  - Needs clean i18n support in `frontend/src/lib/i18n.ts` for the 3 modes and feedback toasts.

---

## 3. Detailed Architecture & Design for Requirement 1 (R1)

### 3.1 Architecture Diagram: Adaptive Open-Ontology & Narrative Pipeline

```
                                  [ User Input / Story Brief ]
                                                │
                                                ▼
                        ┌───────────────────────────────────────────────┐
                        │   TRI-TIER ONTOLOGY RESOLVER (services/ontology)
                        │   - Cultural Similarity Score (0.0 to 1.0)     │
                        │   - Mode Dispatcher (Mode 1 / Mode 2 / Mode 3) │
                        └───────┬───────────────┬───────────────┬───────┘
                                │               │               │
       ┌────────────────────────┘               │               └────────────────────────┐
       ▼                                        ▼                                        ▼
[ TIER 1: CANONICAL VN ]             [ TIER 2: CULTURAL FUSION ]              [ TIER 3: OPEN DOMAIN ]
Similarity >= 0.7                    0.3 <= Similarity < 0.7                  Similarity < 0.3
Mode 1 (Chính sử) or Mode 2 (Dã sử)  Hybrid / Sci-fi / Steampunk VN           Fantasy / Sci-fi / Western / OOD
────────────────────────────────     ────────────────────────────────         ────────────────────────────────
• Full VN Honorifics System          • Preserves Core VN Essence              • 100% Semantic Relaxation
• Cultural Entities (Trống đồng,     • Relaxes Era Constraints                • Disables Feudal VN Filters
  Nỏ thần, Cổng làng, Bến sông...)     (Cyberpunk, Steampunk, Post-apoc)      • No Forced Traditional Attire
• Comic Visual DNA: Cổ phục          • Hybrid Attire (Neon Áo Dài,            • Dynamic Ephemeral Node
  (Áo Ngũ Thân, Nhật Bình, Tấc...)     Mecha Áo Ngũ Thân, Visor Nón Lá)         Extraction (Free entities/spaces)
• Master Negative: Hanfu, Kimono,    • Master Negative: Hanfu, Kimono,        • Standard Negative: Quality,
  Hanbok, Samurai, Ninja               Hanbok, Samurai (Preserves VN)           Distortion, Artifacts only
• Historical Grounding Gatekeeper    • Historical Anchor + Sci-fi tech        • Historical Gatekeeper bypassed
  (Strict in Mode 1, Spirit in Mode 2)
       │                                        │                                        │
       └────────────────────────┬───────────────┴────────────────────────────────────────┘
                                │
                                ▼
         ┌─────────────────────────────────────────────────────────────┐
         │     SMART SELECTIVE LANGUAGE FILTER                         │
         │     - Is genre Tiên hiệp / Kiếm hiệp (Wuxia / Xianxia)?     │
         │       • YES ──> Allow clichés ("tiêu sái", "tà mị", etc.)   │
         │       • NO  ──> STRICTLY SUPPRESS / BAN translation clichés │
         └──────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
         ┌─────────────────────────────────────────────────────────────┐
         │     NARRATIVE GENERATION & COMIC MULTI-MODAL PIPELINE        │
         │     - StoryGenerator (In Medias Res, 5 Beats, Guided Tone)   │
         │     - ComicDirectorAgent (Tier-Aware DNA + Enclosures)      │
         │     - Cloudflare Workers AI (Master Negative Injection)     │
         └─────────────────────────────────────────────────────────────┘
```

---

## 4. Component Deep Dive & Specification

### 4.1 Component A: 3 Chế Độ Sáng Tác (3 Narrative Modes)

#### Model Definition (`backend/models/narrative_mode.py` or within `backend/models/scene_graph.py`)
```python
from enum import Enum

class NarrativeMode(str, Enum):
    STRICT_HISTORICAL = "strict_historical"      # Chế độ 1 — Chính Sử & Tôn Trọng Sự Thật Lịch Sử
    HISTORICAL_FICTION = "historical_fiction"    # Chế độ 2 — Dã Sử & Phóng Tác Góc Nhìn Cá Nhân
    FREE_FICTION = "free_fiction"                # Chế độ 3 — Hư Cấu Cá Nhân Hoàn Toàn Tự Do
```

#### Mode 1: Chính Sử & Tôn Trọng Sự Thật Lịch Sử (Strict Historical Authenticity)
- **Target Scope**: Real historical figures and battles (Hai Bà Trưng, Ngô Quyền, Đinh Bộ Lĩnh, Lê Hoàn, Lý Thường Kiệt, Trần Hưng Đạo, Lê Lợi, Nguyễn Huệ / Quang Trung, Trận Bạch Đằng, Phòng tuyến Như Nguyệt, Khởi nghĩa Lam Sơn, Trận Ngọc Hồi - Đống Đa).
- **Core Invariant**: Absolute historical fidelity. Zero historical distortion or revisionism.
- **Historical Grounding Gatekeeper Engine**:
  - Maintains an immutable **Vietnamese Historical Truth Knowledge Base**:
    - **Figures & Alignments**:
      - `Trần Hưng Đạo (Trần Quốc Tuấn)`: Tiết chế quốc công, tác giả *Hịch tướng sĩ*, chỉ huy 3 lần kháng Nguyên, chiến thắng Bạch Đằng 1288. Invariant: Không thể đầu hàng hoặc bại trận.
      - `Ngô Quyền`: Tiền Ngô Vương, cọc ngầm sông Bạch Đằng 938, chém Lưu Hoằng Tháo, chấm dứt 1000 năm Bắc thuộc. Invariant: Đại thắng Nam Hán.
      - `Lý Thường Kiệt`: Thái úy thời Lý, phòng tuyến sông Như Nguyệt 1077, tuyên ngôn *Nam quốc sơn hà*. Invariant: Đánh tan quân Tống.
      - `Lê Lợi`: Bình Định Vương, khởi nghĩa Lam Sơn 10 năm gian khổ, gươm thần Thuận Thiên, giải phóng Thăng Long. Invariant: Đánh đuổi quân Minh vương thông.
      - `Quang Trung (Nguyễn Huệ)`: Hoàng đế Tây Sơn, hành quân thần tốc Tết Kỷ Dậu 1789, chiến thắng Ngọc Hồi - Đống Đa, quét sạch 29 vạn quân Thanh (Tôn Sĩ Nghị). Invariant: Đại phá quân Thanh.
      - `Hai Bà Trưng (Trưng Trắc, Trưng Nhị)`: Khởi nghĩa năm 40 chống Tô Định, "Đền nợ nước, trả thù nhà". Invariant: Khởi nghĩa quật khởi.
    - **Inviolable Battle Outcomes**:
      - `Bạch Đằng 938`: Ngô Quyền thắng Nam Hán (Lưu Hoằng Tháo tử trận).
      - `Như Nguyệt 1077`: Lý Thường Kiệt thắng Tống (Quách Quỳ, Triệu Tiết giảng hòa rút lui).
      - `Bạch Đằng 1288`: Trần Hưng Đạo thắng Nguyên Mông (Ô Mã Nhi bị bắt sống, Thoát Hoan chui ống đồng trốn chạy).
      - `Ngọc Hồi - Đống Đa 1789`: Quang Trung thắng Mãn Thanh (Sầm Nghi Đống thắt cổ, Tôn Sĩ Nghị vượt sông tháo chạy).
  - **Validation & Gatekeeping**:
    - `validate_historical_authenticity(text: str) -> Tuple[bool, List[str]]`: Checks for forbidden falsifications (e.g., regex matching `"Trần Hưng Đạo.*(?:bại trận|thua cuộc|đầu hàng|bị bắt)"`, `"Ngô Quyền.*(?:thua|thất bại)"`, `"Quang Trung.*(?:thua|đầu hàng)"`).
    - Injects strict historical constraints into LLM System Prompt.

#### Mode 2: Dã Sử & Phóng Tác Góc Nhìn Cá Nhân (Historical Fiction / Alternative Lens)
- **Target Scope**: Stories anchored in authentic historical eras and cultural atmosphere (thời Lý, thời Trần, kháng chiến...), where national figures maintain their core stature, but the **protagonist and micro-events are fictional** (e.g., romance between a village girl and a royal guardsman, an anonymous scout during the Battle of Bạch Đằng, an unsung warrior in Lam Sơn).
- **Core Invariant**: Macro historical era, technology, and cultural spirit are strictly preserved; micro events and personal relationships are completely free to invent.
- **Gatekeeping**:
  - Allows user-created fictional characters as leads.
  - Ensures fictional events do not contradict macro historical outcomes.

#### Mode 3: Hư Cấu Cá Nhân Hoàn Toàn Tự Do (Free Personal Fiction / Non-Historical)
- **Target Scope**: Contemporary romance, urban fantasy, high fantasy, cyberpunk, isekai, modern thriller, Western detective.
- **Core Invariant**: **Complete Semantic Relaxation (100% tự do sáng tạo)**.
- **Gatekeeping**:
  - Historical Grounding Gatekeeper is completely bypassed.
  - No feudal Vietnamese honorifics or traditional attire are imposed.

---

### 4.2 Component B: Tri-Tier Ontology Resolver

#### Tier Architecture & Classification
The resolver classifies any input prompt / story brief into one of three tiers based on **Vietnamese Cultural Similarity Score** ($S_{cult} \in [0.0, 1.0]$):

$$\text{Tier} = \begin{cases} 
\text{Tier 1: Canonical Vietnamese Cultural Domain}, & S_{cult} \ge 0.7 \\ 
\text{Tier 2: Cultural Fusion / Hybrid Domain}, & 0.3 \le S_{cult} < 0.7 \\ 
\text{Tier 3: Open-Domain Adaptive Graph}, & S_{cult} < 0.3 
\end{cases}$$

#### Similarity Scoring Engine (`services/ontology.py`)
Calculates $S_{cult}$ combining:
1. **Vietnamese Cultural Lexical Density**:
   - Historical figures, dynasties (Hồng Bàng, Đinh, Tiền Lê, Lý, Trần, Hậu Lê, Tây Sơn, Nguyễn...).
   - Traditional cultural entities: `trống đồng`, `nỏ thần`, `gươm báu`, `cổng làng`, `bến sông`, `mái đình`, `cây đa`, `giếng nước`, `thuyền rồng`, `chiếu dời đô`, `hịch tướng sĩ`.
   - Traditional attire tokens: `áo ngũ thân`, `áo nhật bình`, `áo tấc`, `khăn đóng`, `áo bà ba`, `nón lá`, `nón quai thao`, `áo yếm`.
   - Cultural honorifics: `bệ hạ`, `khanh`, `trẫm`, `hoàng thượng`, `chàng`, `nàng`, `u`, `con`, `tía`, `má`, `đồng chí`, `thưa thầy`.
2. **Hybrid & Fusion Markers**:
   - Combinations of Vietnamese entities with futuristic or fantasy tokens: `cyberpunk thăng long`, `steampunk nguyễn triều`, `việt nam hậu tận thế`, `hà nội 2099`, `sài gòn neon`.
3. **Out-of-Domain Negative Indicators**:
   - Western locations: `new york`, `london`, `paris`, `hogwarts`, `chicago`, `tokyo`.
   - Foreign fantasy entities: `elf`, `dwarf`, `orc`, `vampire`, `werewolf`, `spaceship`, `cyberware`, `matrix`, `galactic empire`.
   - Western character names: `john`, `alice`, `arthur`, `elena`, `sherlock`.

#### Tier 1: Canonical Vietnamese Cultural Domain ($S_{cult} \ge 0.7$)
- **Honorifics Rules**:
  - Imperial/Court: `Bệ hạ / Trẫm / Khanh`, `Hoàng thượng`, `Thần`.
  - Intimate/Traditional: `Chàng / Nàng`, `Huynh / Muội`, `Đại huynh / Tiểu muội`.
  - Family/Rural: `U / Con`, `Tía / Má`, `Thầy / Con`, `Bác / Cháu`.
  - Modern Revolution/Historical: `Đồng chí`.
- **Cultural Entities & Props**:
  - `Trống đồng Đông Sơn`, `Nỏ thần Kim Quy`, `Gươm thần Thuận Thiên`, `Voi chiến Bùi Thị Xuân`, `Chiến thuyền Bạch Đằng`.
  - Rural landmarks: `Cổng làng rêu phong`, `Bến sông quê`, `Cây đa cổ thụ`, `Giếng làng`, `Mái đình cong`.
- **Comic Visual DNA (Vietnamese Traditional Attire)**:
  - `Áo Ngũ Thân`: Traditional 5-panel Vietnamese tunic (tay chẽn for daily/action, tay thụng for ceremonies), standing collar, five fabric buttons.
  - `Áo Nhật Bình`: Traditional rectangular collar robe worn by royalty and noble women of the Nguyễn dynasty.
  - `Áo Tấc`: Formal wide-sleeved ngũ thân robe.
  - `Khăn Đóng`: Traditional Vietnamese fabric-wrapped turban (distinct from turbans of other cultures).
  - `Áo Bà Ba`: Traditional Southern Vietnamese silk shirt with scoop neck and two lower pockets.
  - `Nón Lá`: Conical palm leaf hat.
  - `Nón Quai Thao`: Flat large palm hat with silk hanging chin-straps.
  - `Áo Yếm`: Traditional diamond-shaped halter undergarment.
- **Master Negative Filter (Anti-Cultural Distortion)**:
  - Strictly bans: `"hanfu, kimono, yukata, hanbok, samurai, samurai armor, ninja, katana, geisha, qing queue, pigtail hairstyle, chinese traditional clothing, japanese traditional clothing, tangzhuang, cheongsam, qipao"`
  - Reason: AI diffusion models frequently hallucinate Chinese Hanfu or Japanese Kimono when prompted for East Asian historical attire. The Master Negative filter ensures 100% pure Vietnamese visual identity.

#### Tier 2: Cultural Fusion / Hybrid Domain ($0.3 \le S_{cult} < 0.7$)
- **Scope**: Sci-fi Vietnam, Cyberpunk Thăng Long 2099, Steampunk Triều Nguyễn, Post-apocalyptic Mekong, Urban Fantasy Hanoi.
- **Core Invariant**:
  - Preserves core Vietnamese cultural identity (silhouettes, motifs, street names, food, cultural references).
  - **Relaxes Era Constraints**: Allows high-tech cybernetics, holographic interfaces, flying airships, steam engines, laser weaponry, or mythical magic.
- **Visual DNA Fusion**:
  - `Cyberpunk Áo Dài`: Glowing neon-circuit fiberoptic Áo Dài with carbon-fiber slit trousers.
  - `Mecha Áo Ngũ Thân`: Armored reinforced Ngũ Thân coat with robotic exoskeletons.
  - `HUD Nón Lá`: Translucent composite conical hat with built-in heads-up display visor.
- **Master Negative**:
  - Still bans Hanfu, Kimono, Samurai, Ninja (preserves Vietnamese essence).
  - Does NOT ban sci-fi, guns, cybernetics, or futuristic machinery.

#### Tier 3: Open-Domain Adaptive Graph ($S_{cult} < 0.3$)
- **Scope**: Western detective, Victorian London noir, Modern NYC high school, High Fantasy (Middle Earth style), Space Opera, Cultivation Xianxia.
- **Core Invariant**:
  - **Disables Feudal Vietnamese Filters completely**: No Vietnamese honorifics (`u/con`, `bệ hạ/khanh`) are forced into Western or modern contexts.
  - **No Forced Traditional Attire**: Characters will NOT be drawn wearing Áo Dài or Nón Lá.
  - **Dynamic Ephemeral Node Extraction**: The system dynamically extracts characters, enclosures, and era constraints directly from the story text on the fly without any hardcoded defaults.

---

### 4.3 Component C: Smart Selective Language Filter

#### The Cliché Taxonomy
The system splits clichés into two distinct categories:

1. **Universal AI Clichés (`AI_CLICHE_BANLIST`)** — **Always Banned in All Modes/Genres**:
   - Sáo ngữ AI lười biếng: `"nhanh như nhịp tim chậm rãi"`, `"khoảng trống trong lòng"`, `"nỗi lo đè nặng lên vai"`, `"thở dài giọng nhẹ"`, `"trái tim đập thình thịch"`, `"nụ cười bí ẩn nở trên môi"`, `"đôi mắt sáng rực lên"`, `"cảm xúc trào dâng trong lồng ngực"`, `"lòng tôi chợt nặng trĩu"`, `"một cảm giác kỳ lạ lan tỏa"`, `"thế giới dường như dừng lại"`, `"thời gian như ngừng trôi"`.

2. **Chinese-Translation Clichés (`TRANSLATION_CLICHE_BANLIST`)** — **Selectively Controlled**:
   - Sáo ngữ tiên hiệp/kiếm hiệp dịch sượng:
     - `"tiêu sái"`
     - `"tà mị"` / `"nụ cười tà mị"`
     - `"lãnh khốc"` / `"lãnh khốc vô tình"`
     - `"bản tọa"` / `"bổn tọa"`
     - `"đế tôn"`
     - `"không khỏi hít vào một ngụm khí lạnh"`
     - `"sát khí cuộn trào"` / `"sát khí ngút trời"`
     - `"lão phu"`
     - `"tiểu súc sinh"`
     - `"muốn chết"` (khi dùng kiểu đe dọa dịch thô)
     - `"ngươi dám"`

#### Selective Logic Matrix
| Setting / Genre Selected | Mode | Action on Universal AI Clichés | Action on Translation Clichés |
|---|---|---|---|
| **Chính Sử (Strict History)** | Mode 1 | **BANNED** | **STRICTLY BANNED** (Purges foreign translation clichés from Vietnamese history) |
| **Dã Sử (Historical Fiction)** | Mode 2 | **BANNED** | **STRICTLY BANNED** |
| **Pure Vietnamese / Literary** | Mode 3 | **BANNED** | **STRICTLY BANNED** |
| **Tiên Hiệp (Xianxia)** | Mode 3 | **BANNED** | **ALLOWED** (Genre-native conventions preserved) |
| **Kiếm Hiệp (Wuxia)** | Mode 3 | **BANNED** | **ALLOWED** (Genre-native conventions preserved) |
| **Huyền Huyễn (Xuanhuan)**| Mode 3 | **BANNED** | **ALLOWED** |
| **Modern Campus / Sci-Fi** | Mode 3 | **BANNED** | **STRICTLY BANNED** |

#### Implementation Signature (`backend/services/ontology.py`)
```python
def validate_smart_language_compliance(
    text: str,
    genre: str = "",
    narrative_mode: NarrativeMode = NarrativeMode.FREE_FICTION,
    cultural_tier: int = 3
) -> Tuple[bool, List[str]]:
    """
    Validates text with selective cliché enforcement:
    - Base AI clichés are always checked.
    - Translation clichés are only checked if the genre is NOT Wuxia/Xianxia.
    """
```

---

## 5. File-by-File Blueprint: Modifications & Additions

### 5.1 New Core Service: `backend/services/ontology.py` (To be created)
This new file serves as the centralized engine for Requirement 1. It will contain:
1. `NarrativeMode` Enum (`STRICT_HISTORICAL`, `HISTORICAL_FICTION`, `FREE_FICTION`).
2. `CulturalTier` Enum (`TIER_1_CANONICAL_VN`, `TIER_2_CULTURAL_FUSION`, `TIER_3_OPEN_DOMAIN`).
3. `VIETNAMESE_HISTORICAL_KB`: Structured knowledge base of dynasties, rulers, battle outcomes, and inviolable facts.
4. `HistoricalGroundingGatekeeper`:
   - `validate_historical_invariants(text: str) -> Tuple[bool, List[str]]`
   - `get_historical_grounding_prompt(mode: NarrativeMode, era_or_figure: str) -> str`
5. `TriTierOntologyResolver`:
   - `calculate_cultural_similarity(text_or_prompt: str, genre: str = "") -> float`
   - `resolve_tier(similarity: float) -> CulturalTier`
   - `get_tier_visual_dna_rules(tier: CulturalTier) -> dict`
   - `get_master_negative_filter(tier: CulturalTier, genre: str = "") -> str`
   - `get_honorifics_guidelines(tier: CulturalTier, mode: NarrativeMode) -> str`
6. `SmartSelectiveLanguageFilter`:
   - `AI_CLICHE_BANLIST`: Universal AI clichés.
   - `TRANSLATION_CLICHE_BANLIST`: Chinese translation clichés.
   - `is_wuxia_genre(genre: str) -> bool`
   - `validate_smart_language_compliance(...) -> Tuple[bool, List[str]]`
   - `get_prompt_cliche_instructions(genre: str, mode: NarrativeMode) -> str`
7. `extract_dynamic_ephemeral_node(story_text: str, llm_client) -> Tuple[CharacterEntity, SpaceEnclosure, EraGenreConstraint]`: For Tier 3 Open Domain.

### 5.2 Modifications to `backend/models/scene_graph.py`
- **Import & Re-export**: Import `NarrativeMode` and `CulturalTier` from `services.ontology` for seamless interoperability.
- **`EraGenreConstraint`**:
  - Add fields: `cultural_tier: int = 1`, `narrative_mode: str = "free_fiction"`.
  - Add method: `is_vietnamese_canonical() -> bool`.
- **`DynamicSceneGraph`**:
  - Add `narrative_mode: NarrativeMode = NarrativeMode.FREE_FICTION`.
  - Add `cultural_tier: int = 1`.
  - Update `validate_era_consistency`: Do not ban swords/robes if `cultural_tier == 1` (historical Vietnam) or `cultural_tier == 3` (fantasy/medieval)!
  - Update `get_combined_negative_tokens`: Pull from `TriTierOntologyResolver.get_master_negative_filter`.

### 5.3 Modifications to `backend/agents/story_generator.py`
- **Imports**: Import `NarrativeMode`, `CulturalTier`, `HistoricalGroundingGatekeeper`, `TriTierOntologyResolver`, `SmartSelectiveLanguageFilter`.
- **`validate_anti_cliche_compliance`**: Delegate to `SmartSelectiveLanguageFilter.validate_smart_language_compliance`.
- **`_extract_narrative_ontology`**:
  - Accept `narrative_mode: NarrativeMode` and `genre: str`.
  - Query `TriTierOntologyResolver` to inject appropriate cultural dimension constraints into prompt rather than hardcoding modern light novel.
- **`_build_prompt` and `generate_chapter_stream`**:
  - Inject `HistoricalGroundingGatekeeper` guidelines when `narrative_mode == NarrativeMode.STRICT_HISTORICAL`.
  - Inject appropriate Vietnamese honorific rules for Tier 1.
  - Inject selective cliché rules based on genre.

### 5.4 Modifications to `backend/agents/comic_agent.py`
- **`STYLE_PREFIX` and `STYLE_SUFFIX`**:
  - Generalize beyond `"Japanese high school manga"`:
    - Tier 1: `"masterpiece monochrome historical manga, Vietnamese traditional aesthetics, crisp clean ink lineart, delicate screentone shading..."`
    - Tier 2: `"masterpiece monochrome cyberpunk manga, futuristic Vietnamese aesthetic, neon screentone shading, high contrast ink lineart..."`
    - Tier 3: `"masterpiece modern monochrome manga, dynamic manga panel layout, crisp clean black and white ink lineart..."`
- **`DNA_EXTRACTOR_PROMPT`**:
  - Expand costume catalog to explicitly recognize Vietnamese traditional attire: `Áo Ngũ Thân`, `Áo Nhật Bình`, `Áo Tấc`, `Khăn Đóng`, `Áo Bà Ba`, `Nón Lá`, `Nón Quai Thao`.
  - Adapt aliases to include traditional honorifics (`chàng`, `nàng`, `tiểu thư`, `công tử`, `bệ hạ`, `tướng quân`, `nghĩa sĩ`).
- **`SPATIAL_ENCLOSURES` & `resolve_spatial_enclosure`**:
  - Add traditional Vietnamese enclosures:
    - `"vietnamese_village"`: `cổng làng, bến sông, cây đa, giếng nước, mái đình`.
    - `"imperial_palace_vn"`: `hoàng thành Thăng Long, điện Kính Thiên, cột cờ, cung đình Huế, ngai vàng sơn son thếp vàng`.
    - `"battlefield_vn"`: `bãi cọc sông Bạch Đằng, chiến thuyền, gươm giáo, cờ lau, cờ lệnh`.
  - In Tier 3: If no predefined enclosure matches, use `SETTING_EXTRACTOR_PROMPT` output directly instead of falling back to `"classroom"`!
- **`_validate_panels`**:
  - Inject Master Negative Filter (`Hanfu, Kimono, Hanbok, Samurai, Ninja`) into image prompt or negative prompt when in Tier 1.

### 5.5 Modifications to `backend/services/cloudflare_ai.py`
- **`get_master_negative_prompt`**:
  - Accept `cultural_tier: int = 1`, `genre: str = ""`.
  - When `cultural_tier == 1` or `cultural_tier == 2`: Inject `VIETNAMESE_CANONICAL_NEGATIVE_PROMPT` (`hanfu, kimono, hanbok, samurai, ninja, katana, geisha, qing queue...`).
  - When `cultural_tier == 3` and genre is fantasy/sci-fi: Do NOT ban swords or armor!

### 5.6 Modifications to `backend/agents/story_memory.py`
- **`StoryBible`**:
  - Add fields: `narrative_mode: str = "free_fiction"`, `cultural_tier: int = 1`.
- **`init_scene_graph_from_bible`**:
  - Resolve tier and mode.
  - Dynamically construct `EraGenreConstraint` and initial `SpaceEnclosure` corresponding to the resolved tier and setting.

### 5.7 Modifications to `backend/agents/copilot_agent.py`
- **`COPILOT_SYSTEM_PROMPT` & `DIRECT_EDIT_PROMPT`**:
  - Inject awareness of `narrative_mode`.
  - If `narrative_mode == STRICT_HISTORICAL`: Enforce that the editor must preserve historical accuracy and not falsify documented history.

### 5.8 Modifications to `backend/main.py`
- **Request Models**:
  - `GenerateStoryRequest`: Add `narrative_mode: str = "free_fiction"`, `genre: str = ""`.
  - `InitStoryRequest`: Add `narrative_mode: str = "free_fiction"`, `genre: str = ""`.
- **New API Endpoints**:
  - `POST /api/ontology/resolve`: Accepts `{ prompt: str, genre: str }` and returns `{ cultural_similarity: float, cultural_tier: int, tier_name: str, suggested_mode: str }`.
  - `POST /api/ontology/validate-history`: Accepts `{ text: str }` and returns `{ is_valid: bool, violations: List[str] }`.

### 5.9 Modifications to Frontend (`frontend/src/`)
- **`frontend/src/lib/types.ts`**:
  - Add `NarrativeMode = 'strict_historical' | 'historical_fiction' | 'free_fiction'`.
  - Add `CulturalTier = 1 | 2 | 3`.
- **`frontend/src/lib/i18n.ts`**:
  - Add translations for the 3 modes:
    - Mode 1: "Chính Sử & Tôn Trọng Sự Thật Lịch Sử" / "Strict Historical Authenticity"
    - Mode 2: "Dã Sử & Phóng Tác Góc Nhìn Cá Nhân" / "Historical Fiction (Personal Lens)"
    - Mode 3: "Hư Cấu Cá Nhân Hoàn Toàn Tự Do" / "Free Fiction (Complete Freedom)"
  - Add descriptions and badges for the 3 tiers.
- **`frontend/src/components/setup/Phase1Idea.tsx` & `Phase3Controls.tsx`**:
  - Add an intuitive 3-button Mode Selector with icons (Quill & Shield for Mode 1, Scroll & Mask for Mode 2, Flying Feather/Sparkles for Mode 3).
  - Pass `narrative_mode` down to `handlePhase1Continue` and `handleStartWriting`.
- **`frontend/src/app/page.tsx`**:
  - Track `narrativeMode` state.
  - Pass `narrative_mode` to `api.streamStory` payload.

---

## 6. Edge Cases & Risk Analysis

| # | Edge Case / Hazard | Potential Failure Mode | Architectural Mitigation |
|---|---|---|---|
| 1 | **Ambiguous Vietnamese Names in Open Domain** | A character named "An" in a Western Sci-Fi story might trigger Vietnamese historical honorifics or school uniform DNA. | Safe regex word boundaries + semantic context window check (already partially present in `comic_agent.py` line 885, but now strictly decoupled by `CulturalTier == 3`). |
| 2 | **Historical Revisionism Hallucination** | An LLM might generate "Trần Hưng Đạo bại trận Bạch Đằng" in Mode 1. | `HistoricalGroundingGatekeeper.validate_historical_invariants` intercepts generation, detects negation/defeat of historical champions, and triggers automatic re-prompting or error. |
| 3 | **Cultural Fusion Identity Drift** | A Cyberpunk Hanoi story (Tier 2) drifting completely into Western Cyberpunk without Vietnamese essence, or devolving into Japanese Cyberpunk with Samurai. | Tier 2 retains the Master Negative Filter against Samurai/Kimono, while anchoring Vietnamese cultural symbols (Áo Dài, Nón Lá, Cầu Long Biên, Hồ Gươm). |
| 4 | **CLIP 77-Token Budget Saturation** | Adding extensive Vietnamese cổ phục descriptions (Áo Ngũ Thân tay thụng, Khăn Đóng, Áo Nhật Bình) could exceed the 77-token limit, pushing character facial DNA or action out of attention. | Compact DNA tokenization: Limit attire anchor to concise keywords (e.g., `"wearing navy silk Áo Ngũ Thân with Khăn Đóng"`) restricted to $\le 25$ words, placed at Position 1. |
| 5 | **Wuxia/Xianxia Genre Detection False Positives** | A story set in ancient Vietnam misclassified as Xianxia, thereby allowing inappropriate Chinese slang like `"đế tôn"`. | `is_wuxia_genre` checks explicit genre choice (`"tiên hiệp"`, `"kiếm hiệp"`) AND requires `narrative_mode == FREE_FICTION`. If `narrative_mode` is Mode 1 or 2, translation clichés are STRICTLY FORBIDDEN regardless of keywords! |
| 6 | **Ellipsis (`...`) Regeneration in Dialogue** | Historical or dramatic dialogue might re-introduce `...` truncations. | The existing `sanitize_complete_dialogue` multi-pass filter in `comic_agent.py` is preserved and applied to all panel generation. |

---

## 7. Verification & Testing Strategy

### 7.1 Unit & Invariant Test Suite (`backend/tests/test_adaptive_open_ontology.py`)
1. **Mode 1 Invariant Validation**:
   - Test that `validate_historical_invariants("Trần Hưng Đạo đại thắng quân Nguyên Mông trên sông Bạch Đằng")` returns `True, []`.
   - Test that `validate_historical_invariants("Trần Hưng Đạo bại trận trên sông Bạch Đằng")` returns `False` with violation report.
   - Test that Quang Trung, Ngô Quyền, Lê Lợi historical invariants are strictly upheld.
2. **Tri-Tier Cultural Similarity Resolution**:
   - Input: `"Trần Quốc Toản bóp nát quả cam tại bến Bình Than, khởi nghĩa thời Trần"` $\to$ Similarity $\ge 0.7$ (Tier 1).
   - Input: `"Thám tử Sài Gòn 2099 lái xe bay điều tra án mạng tại chợ Bến Thành ngập đèn neon"` $\to$ $0.3 \le$ Similarity $< 0.7$ (Tier 2).
   - Input: `"Sherlock Holmes walks through foggy London streets in 1895 with Dr. Watson"` $\to$ Similarity $< 0.3$ (Tier 3).
3. **Smart Language Filter**:
   - Input: `"Hắn nở một nụ cười tà mị, khí phách tiêu sái"` with `genre="Văn học hiện đại"` $\to$ Violations detected.
   - Input: `"Hắn nở một nụ cười tà mị, khí phách tiêu sái"` with `genre="Tiên hiệp"` and `mode=FREE_FICTION` $\to$ Clean (0 violations).
   - Input: `"nhanh như nhịp tim chậm rãi"` with `genre="Tiên hiệp"` $\to$ Violation detected (Universal AI cliché is never allowed).
4. **Comic Visual DNA & Master Negative Filter**:
   - Verify that Tier 1 generates prompts with Vietnamese traditional attire and includes `Hanfu, Kimono, Hanbok, Samurai, Ninja` in the negative prompt.
   - Verify that Tier 3 does not inject Áo Ngũ Thân or classroom anchors.

---

## 8. Summary of Deliverables & Next Steps

This investigation provides the complete specification, code locations, architecture, and risk analysis for implementing Requirement 1 (R1).

- **Implementation target files**:
  - `backend/services/ontology.py` (New centralized service)
  - `backend/models/scene_graph.py` (Model updates & re-exports)
  - `backend/agents/story_generator.py` (Prompt & cliché validator updates)
  - `backend/agents/comic_agent.py` (Visual DNA, style prefix, and negative prompt updates)
  - `backend/services/cloudflare_ai.py` (Master negative prompt updates)
  - `backend/agents/story_memory.py` (Bible & Scene-Graph bootstrapping updates)
  - `backend/agents/copilot_agent.py` (Historical guard awareness)
  - `backend/main.py` (Endpoints & request schemas)
  - `frontend/src/` (Mode selector, i18n, and workspace state)
- **Handoff Report**: Documented in `handoff.md` with complete 5-component protocol.
