# NarrAI Round 5 Test Infrastructure & Architecture (TEST_INFRA.md)

**Project**: NarrAI v2.0 — Flexible Manuscript Surgery, Unified Intake Chat, Community Feed & 4-Layer Architecture  
**Specification Reference**: `ORIGINAL_REQUEST.md` (Version `2026-09-29T03:08:30Z`) & `PROJECT.md`  
**Test Suite Architect**: E2E Test Writer (`test_writer_r5`)  
**Scope**: Requirements 1, 2, 3, 4, 5 (R1: Flexible Manuscript Surgery, R2: Unified Intake Chat, R3: Seamless Transition & Story ID Allocation, R4: Community Feed & Social Publish, R5: 4-Layer Architecture)  

---

## 1. Executive Summary & Testing Philosophy

The NarrAI Round 5 E2E Test Infrastructure is an opaque-box, behavior-driven testing harness engineered to guarantee absolute correctness, structural integrity, and architectural isolation across all core subsystems:
1. **Copilot Flexible Manuscript Surgery (R1)**: Verifies the 5 surgical editing targets (Target 1 Opening/Hook, Target 2 Character & Dialogue, Target 3 Middle Beats & Scene Insertion, Target 4 Climax & Ending, Target 5 Tone Shift & Restyling) with context-aware semantic sliding windows.
2. **Dynamic Semantic Chunk Slicing & Heading Preservation (R1)**: Enforces exact partitioning into `prefix` -> `window_to_edit` -> `suffix` along chapter boundaries (`## Chương X`) and guarantees 100% preservation of `**[TITLE]**` and sequential chapter headers.
3. **Story ID Immediate Pre-allocation & Streaming Endpoints (R3)**: Guarantees immediate `story_id` generation for both guest and authenticated users before/at stream inception via `[STORY_ID:<id>]` and `/api/stories/allocate`.
4. **Social Publish Data Enrichment & 3-Stage Community Feed (R4)**: Validates automatic manuscript persistence, comic cover synchronization, full-content retrieval in `GET /post/{id}`, and 3-stage recommendation ranking (Two-Tower Cosine + Bandit 15% Cold-Start + MMR $\lambda=0.7$).

### Key Architectural Tenets
- **100% In-Memory Isolation**: Every test case runs against an ephemeral, isolated SQLite database (`sqlite:///:memory:`). No state leaks across tests; no persistent test artifacts contaminate the workspace.
- **Zero Mock Facades**: Tests exercise genuine programmatic logic, database ORM relations, regex parsers, and exact mathematical formulas. External LLM network calls are mocked deterministically at the transport boundary while testing all parsing, unwrapping, heading preservation, slicing, and database operations end-to-end.
- **Authoritative Mathematical & Structural Oracles**: Expected outputs are derived directly from the explicit formulas and invariant specifications in `PROJECT.md` and `ORIGINAL_REQUEST.md`.

---

## 2. 4-Tier Test Methodology

Every functional requirement is verified across four distinct tiers of rigor:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   TIER 4: REAL-WORLD APPLICATION SCENARIOS             │
│   Complete author journeys: Light novel hook/polish, historical epic   │
│   middle beat insertion, and guest-to-registered publishing lifecycles │
├────────────────────────────────────────────────────────────────────────┤
│                   TIER 3: CROSS-FEATURE INTEGRATION                    │
│   Surgery + Publish, Intake Refine + Stream + Surgery, Comic Cover     │
│   Sync + Draft Save, and Recommender Feed + Dwell Profile Decay        │
├────────────────────────────────────────────────────────────────────────┤
│                   TIER 2: BOUNDARY & CORNER CASES                      │
│   Empty strings, massive texts (>15k chars), multi-chapter novels,     │
│   missing fields, guest vs auth users, unicode/smart quote edge cases  │
├────────────────────────────────────────────────────────────────────────┤
│                   TIER 1: FEATURE COVERAGE (HAPPY PATH)                │
│   >=5 tests per feature across Target 1-5 surgery, dynamic slicing,    │
│   heading preservation, story_id allocation, publish, 3-stage feed     │
└────────────────────────────────────────────────────────────────────────┘
```

### Tier 1: Feature Coverage (Isolated Happy Path)
- Validates core contractual behaviors of each component in isolation with standard, well-formed inputs.
- Requires $\ge 5$ discrete tests per feature area:
  - Target 1: Opening / Hook Rewrite ($\ge 5$ tests)
  - Target 2: Character & Dialogue Surgery ($\ge 5$ tests)
  - Target 3: Middle Beats & Scene Insertion ($\ge 5$ tests)
  - Target 4: Climax & Ending Rewrite ($\ge 5$ tests)
  - Target 5: Tone Shift & Style Restyling ($\ge 5$ tests)
  - Dynamic Semantic Chunk Slicing ($\ge 5$ tests)
  - Structural Heading Preservation Engine ($\ge 5$ tests)
  - Story ID Immediate Pre-allocation & Streaming ($\ge 5$ tests)
  - Social Publish Data Enrichment ($\ge 5$ tests)
  - 3-Stage Community Feed & Reader Modal ($\ge 5$ tests)

### Tier 2: Boundary, Limit & Corner Cases
- Tests behavior at exact technical and mathematical boundaries:
  - Empty strings, whitespace-only inputs, and `None` parameters.
  - Massive manuscripts exceeding $15,000$ characters enforcing window truncation limits without memory exhaustion.
  - Multi-chapter novels with 5+ sequential chapters (`## Chương 1` to `## Chương 5`).
  - Missing payload fields in publishing requests (missing `story_id`, missing `tags`, missing `cover_image_url`).
  - Guest vs authenticated user permissions.
  - Special characters, unicode diacritics, smart quotes, emojis, and codeblocks.

### Tier 3: Cross-Feature Combinations
- Tests interconnected pipelines across architectural boundaries:
  - **Surgery + Social Publish**: Author creates draft $\rightarrow$ copilot performs surgical edits $\rightarrow$ manuscript updates in DB $\rightarrow$ publishes to community feed $\rightarrow$ full text retrievable via `GET /post/{id}`.
  - **Intake Refine + Stream + Surgery**: QARefiner condenses prompt $\rightarrow$ pre-allocates `story_id` $\rightarrow$ streams Light Novel text $\rightarrow$ copilot edits opening without loss of session metadata.
  - **Draft Save + Comic Cover Sync**: Story written $\rightarrow$ Comic panels generated $\rightarrow$ author publishes without cover URL $\rightarrow$ server automatically extracts panel 0 image URL as `cover_image_url`.
  - **Recommender Feed + Dwell Profile Decay**: Post served via Thompson Sampling Bandit $\rightarrow$ reader spends $>60$s reading $\rightarrow$ interaction logs `DWELL_TIME` $\rightarrow$ exponential decay updates user interest profile.

### Tier 4: Real-World Application Scenarios
- End-to-end journey simulations mirroring real production users:
  - **Modern Light Novel Author Journey**: High school fantasy author creates story from prompt, performs Target 1 opening surgery to hook readers with in medias res, performs Target 2 dialogue polish with micro-actions, publishes to community feed with tags, and verifies post appears in 3-stage feed.
  - **Vietnamese Historical Multi-Chapter Journey**: Author composes 3-chapter historical fiction, uses Target 3 to insert high-stakes battlefield confrontation in Chapter 2, verifies Chapter 1 and Chapter 3 are 100% unperturbed and all `## Chương X` preserved, adapts to manga, and publishes with auto-synced comic cover.
  - **Guest-to-Registered Lifecycle**: Anonymous user starts story, receives pre-allocated guest `story_id`, performs Target 5 tone shift to thriller, registers account, and accesses published post in community feed.

---

## 3. Authoritative Mathematical & Structural Oracles

### 3.1 Dynamic Semantic Chunk Slicing Oracle
Given manuscript $S$, target $T \in \{\text{OPENING}, \text{CHAR\_DIALOGUE}, \text{MIDDLE\_BEATS}, \text{CLIMAX\_ENDING}, \text{TONE\_STYLE}\}$:
- **Target 1 (Opening)**:
  $$S = \text{window} + \text{suffix}, \quad \text{prefix} = \emptyset$$
  Where split point is the boundary of Chapter 2 (`\n## Chương 2`) or first 2-3 paragraphs.
- **Target 4 (Ending)**:
  $$S = \text{prefix} + \text{window}, \quad \text{suffix} = \emptyset$$
  Where split point is the boundary of the final chapter marker or last 2-3 paragraphs.
- **Target 3 (Middle Beats)**:
  $$S = \text{prefix} + \text{window} + \text{suffix}$$
  Where `prefix` isolates preceding chapters/paragraphs, `window` isolates targeted middle scenes, and `suffix` isolates subsequent climax.
- **Target 2 & 5 (Character & Tone)**:
  If $|S| \le 8000$, $\text{window} = S$. If $|S| > 8000$, chapter-aware rolling window.

### 3.2 Heading Preservation Invariant
For any transformation $f_{\text{edit}}(S, T) \to S'$:
1. **Title Invariant**:
   $$\text{match}(S, \text{r'^\*\*\[?[^\*\n]+\]?\*\*'}) \implies \text{match}(S', \text{r'^\*\*\[?[^\*\n]+\]?\*\*'}) = \text{title}_{\text{original}}$$
2. **Chapter Heading Invariant**:
   $$\forall c \in \text{headings}(S, \text{r'##\s+Chương\s+\d+'}), \quad c \in \text{headings}(S')$$

### 3.3 3-Stage Recommender Scoring Oracle
1. **Stage 1 (Candidate Retrieval)**: Top 40 Content Cosine $\text{sim}(U_u, V_p) = \frac{U_u \cdot V_p}{\|U_u\|_2 \|V_p\|_2}$ + Top 20 DSGO Graph Overlap.
2. **Stage 2 (Multi-Task Scoring)**:
   $$\text{Score}(p, u) = 0.35 \cdot \text{CosineSim}(U_u, V_p) + 0.25 \cdot \text{ImplicitAffinity}(u, p) + 0.20 \cdot \text{Freshness}(p) + 0.20 \cdot \text{QualityScore}(p)$$
   Where $\text{Freshness}(p) = \frac{1}{1 + 0.02 \cdot \text{hours}}$, $\text{QualityScore}(p) = 0.40 \cdot \text{CompRate} + 0.30 \cdot \text{LikeRatio} + 0.30 \cdot \text{DwellNorm}$.
3. **Stage 3 (MMR & Bandit)**:
   - **MMR Diversity** ($\lambda = 0.70$):
     $$\text{MMR} = \operatorname{argmax}_{p \in R \setminus S} \left[ 0.70 \cdot \text{Score}(p) - 0.30 \max_{s \in S} \text{Sim}(p, s) \right]$$
   - **Multi-Armed Bandit** ($\epsilon = 0.15$): $15\%$ of slots reserved for cold-start posts ($\text{views} < 30$) via Thompson Sampling.

---

## 4. Test Suite Inventory

### 4.1 `backend/tests/test_e2e_round5_surgery_feed.py`
The primary comprehensive E2E test harness covering all functional requirements in Round 5 across Tiers 1–4.

| Tier | Test Function | Feature Subsystem | Authoritative Source |
|---|---|---|---|
| 1 | `test_target1_intent_classification_vietnamese` | Target 1 Surgery Intent | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target1_intent_classification_english` | Target 1 Surgery Intent | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target1_slicing_isolates_opening_and_preserves_suffix` | Target 1 Dynamic Slicing | `PROJECT.md` § M1 |
| 1 | `test_target1_execution_in_medias_res_hook` | Target 1 Hook Rewrite | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target1_preserves_title_across_opening_rewrite` | Target 1 Heading Preservation | `PROJECT.md` § M1 |
| 1 | `test_target2_intent_classification_rename` | Target 2 Character Surgery | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target2_intent_classification_dialogue_subtext` | Target 2 Dialogue Surgery | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target2_dialogue_action_interleaving` | Target 2 Micro-Action Polish | `PROJECT.md` § M1 |
| 1 | `test_target2_pronoun_and_naming_consistency` | Target 2 Naming Invariance | `PROJECT.md` § M1 |
| 1 | `test_target2_preserves_chapter_markers` | Target 2 Structural Invariance | `PROJECT.md` § M1 |
| 1 | `test_target3_intent_classification_vietnamese` | Target 3 Middle Beats Intent | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target3_intent_classification_english` | Target 3 Middle Beats Intent | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target3_slicing_isolates_middle_paragraphs` | Target 3 Dynamic Slicing | `PROJECT.md` § M1 |
| 1 | `test_target3_execution_middle_insertion_integrity` | Target 3 Scene Insertion | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target3_multi_chapter_middle_isolation` | Target 3 Chapter-Aware Slicing | `PROJECT.md` § M1 |
| 1 | `test_target4_intent_classification_vietnamese` | Target 4 Climax Intent | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target4_intent_classification_english` | Target 4 Climax Intent | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target4_slicing_isolates_ending_paragraphs` | Target 4 Dynamic Slicing | `PROJECT.md` § M1 |
| 1 | `test_target4_lingering_cliffhanger_execution` | Target 4 Cliffhanger Polish | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target4_preserves_ending_chapter_heading` | Target 4 Heading Preservation | `PROJECT.md` § M1 |
| 1 | `test_target5_intent_classification_vietnamese` | Target 5 Tone Shift Intent | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target5_intent_classification_english` | Target 5 Tone Shift Intent | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target5_humor_and_mystery_tone_detection` | Target 5 Style Detection | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target5_restyle_preserves_core_events` | Target 5 Plot Preservation | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_target5_large_manuscript_sliding_window` | Target 5 Window Management | `PROJECT.md` § M1 |
| 1 | `test_semantic_slicing_chapter_marker_split` | Dynamic Slicing (Chapters) | `PROJECT.md` § M1 |
| 1 | `test_semantic_slicing_paragraph_fallback` | Dynamic Slicing (Paragraphs) | `PROJECT.md` § M1 |
| 1 | `test_semantic_slicing_ending_chapter_boundary` | Dynamic Slicing (Outro) | `PROJECT.md` § M1 |
| 1 | `test_semantic_slicing_middle_three_chapters` | Dynamic Slicing (Tri-Chapter) | `PROJECT.md` § M1 |
| 1 | `test_semantic_slicing_seam_stitch_reconstitution` | Slicing Reconstitution | `PROJECT.md` § M1 |
| 1 | `test_heading_preservation_bracketed_title` | Title Preservation `**[...]**` | `PROJECT.md` § M1 |
| 1 | `test_heading_preservation_unbracketed_bold_title` | Title Preservation `**...**` | `PROJECT.md` § M1 |
| 1 | `test_heading_preservation_chapter_header_reinjection` | Chapter Header Re-injection | `PROJECT.md` § M1 |
| 1 | `test_heading_preservation_multiple_chapter_headers` | Multi-Chapter Preservation | `PROJECT.md` § M1 |
| 1 | `test_heading_preservation_no_duplicate_injection` | Anti-Duplication Safeguard | `PROJECT.md` § M1 |
| 1 | `test_story_id_allocation_endpoint_guest` | Story ID Allocation (Guest) | `PROJECT.md` § M1 |
| 1 | `test_story_id_allocation_endpoint_authenticated` | Story ID Allocation (Auth) | `PROJECT.md` § M1 |
| 1 | `test_story_id_stream_marker_format` | Stream Yield `[STORY_ID:{id}]` | `PROJECT.md` § M1 |
| 1 | `test_story_id_database_persistence` | Story Database Integrity | `backend/db/models.py` |
| 1 | `test_story_id_locks_session_for_manga_transition` | Manga Transition Bridge | `ORIGINAL_REQUEST.md` § R3 |
| 1 | `test_publish_post_persists_social_post_record` | Social Publish Persistence | `ORIGINAL_REQUEST.md` § R4 |
| 1 | `test_publish_post_auto_saves_story_text` | Auto-save Manuscript in Publish | `PROJECT.md` § M1 |
| 1 | `test_publish_post_auto_syncs_comic_first_panel_cover` | Comic Panel 0 Cover Sync | `PROJECT.md` § M1 |
| 1 | `test_publish_post_preserves_explicit_cover_image` | Explicit Cover Override | `PROJECT.md` § M1 |
| 1 | `test_get_post_details_returns_story_content_and_comic_panels` | Post Details Enrichment | `PROJECT.md` § M1 |
| 1 | `test_recommender_stage1_candidate_generation` | Stage 1 Candidate Generation | `ORIGINAL_REQUEST.md` § R4 |
| 1 | `test_recommender_stage2_multitask_scoring` | Stage 2 Multi-Task Ranking | `ORIGINAL_REQUEST.md` § R4 |
| 1 | `test_recommender_stage3_mmr_genre_diversity` | Stage 3 MMR ($\lambda=0.7$) | `ORIGINAL_REQUEST.md` § R4 |
| 1 | `test_recommender_stage3_bandit_cold_start_exploration` | Stage 3 Bandit ($\epsilon=0.15$) | `ORIGINAL_REQUEST.md` § R4 |
| 1 | `test_reader_interaction_logging_and_view_increment` | Reader Modal Interaction | `ORIGINAL_REQUEST.md` § R4 |
| 2 | `test_boundary_empty_strings_and_none_values` | Empty / None Input Robustness | Boundary Spec |
| 2 | `test_boundary_massive_text_exceeding_15000_chars` | Massive Manuscript (>15k chars) | BVA Robustness |
| 2 | `test_boundary_multi_chapter_novel_5_chapters` | 5-Chapter Sequential Novel | Structural Stress |
| 2 | `test_boundary_missing_fields_in_publish_request` | Missing Publishing Fields | Schema Robustness |
| 2 | `test_boundary_guest_vs_authenticated_publishing` | Guest vs Authenticated Logic | Authorization Edge |
| 2 | `test_boundary_special_characters_quotes_emoji_diacritics` | Vietnamese Unicode & Diacritics | Character Encoding |
| 3 | `test_integration_surgery_to_social_publish` | Surgery $\rightarrow$ Social Publish | Integration Spec |
| 3 | `test_integration_intake_refine_to_stream_to_surgery` | Refine $\rightarrow$ Stream $\rightarrow$ Surgery | Integration Spec |
| 3 | `test_integration_comic_creation_to_cover_sync_publishing` | Comic Creation $\rightarrow$ Cover Sync | Integration Spec |
| 3 | `test_integration_feed_discovery_to_dwell_time_profile_decay` | Discovery $\rightarrow$ Dwell $\rightarrow$ Profile Decay | Integration Spec |
| 4 | `test_scenario_modern_light_novel_author_journey` | Modern Light Novel Journey | User Workflow |
| 4 | `test_scenario_vietnamese_historical_multi_chapter_journey` | Historical Epic Multi-Chapter Journey | User Workflow |
| 4 | `test_scenario_guest_to_registered_lifecycle` | Anonymous $\rightarrow$ Registered Journey | User Workflow |

### 4.2 `backend/tests/test_adversarial_round5_resilience.py`
Dedicated adversarial challenge suite designed to stress-test error recovery, sanitization, and attack surface defense.

| Test Function | Adversarial Attack Vector / Stress Condition |
|---|---|
| `test_adversarial_deeply_nested_json_prose_envelope` | Triple-nested stringified JSON with escaped markdown code fences |
| `test_adversarial_malformed_chapter_headers` | Corrupted headers (`# Chương`, `## Ch 1`, `Chương 1:` without markdown) |
| `test_adversarial_single_paragraph_giant_wall_of_text` | 10,000-character wall of text with 0 double-newlines |
| `test_adversarial_recommender_extreme_and_negative_dwell` | Dwell time of $10^6$ seconds and negative dwell times (-50s) |
| `test_adversarial_recommender_zero_division_guard` | All-zero vectors and 0-view posts computing quality metrics |
| `test_adversarial_deliberate_heading_stripping_attack` | LLM intentionally strips `**[TITLE]**` and chapter markers |
| `test_adversarial_xss_and_html_injection_in_publish` | `<script>alert(1)</script>` and raw HTML in titles and snippets |

---

## 5. Execution Commands

### Run Round 5 E2E Test Suite
```powershell
python backend/tests/test_e2e_round5_surgery_feed.py
```

### Run Round 5 Adversarial Resilience Test Suite
```powershell
python backend/tests/test_adversarial_round5_resilience.py
```

### Run via Pytest
```powershell
pytest backend/tests/test_e2e_round5_surgery_feed.py backend/tests/test_adversarial_round5_resilience.py -v
```

---

## 6. Quality Status & Compliance

- [x] **Strict 4-Tier Structure**: Tier 1 (50 tests covering all 6 feature domains), Tier 2 (6 boundary tests), Tier 3 (4 cross-feature integration tests), Tier 4 (3 complete user workflows).
- [x] **Zero Mock Facades**: All tests exercise genuine programmatic logic, database ORM relations, regex parsers, or exact mathematical formulas.
- [x] **In-Memory Concurrency & Isolation**: Every test initializes and tears down an independent SQLite in-memory database.
- [x] **Python Compilation Clean**: Fully compliant with `python -m py_compile`.
