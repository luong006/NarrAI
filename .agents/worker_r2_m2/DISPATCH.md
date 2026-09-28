## 2026-09-20T13:36:59Z
You are worker_r2_m2, a specialized implementation Worker subagent.
Your Working Directory: e:\NarrAI\.agents\worker_r2_m2
Workspace Directory: e:\NarrAI
Original Request File: e:\NarrAI\.agents\ORIGINAL_REQUEST.md (MANDATORY: You MUST read e:\NarrAI\.agents\ORIGINAL_REQUEST.md before starting work! Focus on ## 2026-09-20T13:19:05Z - Requirement R2).
Project Document: e:\NarrAI\.agents\PROJECT.md
Explorer Survey Report: e:\NarrAI\.agents\explorer_survey_r2_2\report.md (MANDATORY: Read this report carefully! It contains full Pydantic schemas, invariant rules, and architectural design for DSGO).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Exclusive File Write Ownership:
- backend/models/scene_graph.py (NEW module)
- backend/agents/story_memory.py
- backend/agents/story_generator.py
- backend/agents/memory_extractor.py
- backend/tests/test_dynamic_scene_graph.py (NEW comprehensive test suite)

Objectives for Milestone 2 (R2. Dynamic Scene-Graph Ontology & Spatial Scene Enclosure):
1. Build Dynamic Scene-Graph Ontology Models in `backend/models/scene_graph.py`:
   - Define 3-dimensional constraint models using Pydantic:
     * Dimension 1 - Entity: `CharacterEntity` (id, name, aliases, visual_dna, vitality_state, current_location_id, inventory, psychological_state). `VitalityState` enum (ALIVE, INJURED, UNCONSCIOUS, DECEASED).
     * Dimension 2 - Space: `SpaceEnclosure` (id, name, boundary_type, architectural_anchor, persistent_fixtures, lighting_atmosphere, negative_drift_tokens, connected_enclosures). `BoundaryType` enum (INDOOR_ENCLOSED, VEHICLE_INTERIOR, OUTDOOR_CONFINED, OUTDOOR_OPEN).
     * Dimension 3 - Era & Genre: `EraGenreConstraint` (era_name, genre_name, world_axioms, era_banlist, tech_level).
     * Unified Graph: `DynamicSceneGraph` (entities: Dict[str, CharacterEntity], enclosures: Dict[str, SpaceEnclosure], era_genre: EraGenreConstraint, active_enclosure_id: Optional[str]).
   - Implement Automated Invariant Gatekeepers in `backend/models/scene_graph.py`:
     * Vitality Invariant (deceased entities cannot act).
     * Spatial Exclusivity (entities in an enclosure cannot interact directly with entities in other disconnected enclosures).
     * Spatial Drift Sanitizer (`sanitize_spatial_prompt(prompt, enclosure)`: strips prohibited outdoor/street keywords when inside an enclosed room).
     * Era Drift Sanitizer (`sanitize_era_prompt(prompt, era_genre)`: strips prohibited historical/wuxia keywords like hanfu, robes, swords when in modern setting).
     * Scene Transition Gating: method to safely transition active enclosure when transition verbs appear, or lock to current enclosure if no transition occurs.
     * Helper methods for serializing to dict and deserializing from dict.

2. Integrate DSGO into `StoryMemory` and `StoryBible` in `backend/agents/story_memory.py`:
   - Add `dynamic_scene_graph: Optional[DynamicSceneGraph] = None` to `StoryMemory`.
   - Update `StoryMemory.to_dict()` and `StoryMemory.from_dict()` to serialize/deserialize `dynamic_scene_graph` safely (handling legacy data gracefully where dynamic_scene_graph is None).
   - Update `StoryMemory.to_prompt_block()` to format the active enclosure, architectural anchor, and character locations into prompt blocks for LLM injection.

3. Update `story_generator.py` and `memory_extractor.py`:
   - In `story_generator.py`: Update `_extract_narrative_ontology` and `generate_chapter_stream` to leverage the 3D constraint ontology and spatial enclosure context.
   - In `memory_extractor.py`: Update `extract_memory` to support spatial state transitions and entity location updates.

4. Comprehensive Unit Tests in `backend/tests/test_dynamic_scene_graph.py`:
   - Test Pydantic model creation and validation for CharacterEntity, SpaceEnclosure, EraGenreConstraint, DynamicSceneGraph.
   - Test Invariant Rules: Vitality check, Spatial exclusivity check, Era consistency check.
   - Test Spatial Scene Enclosure: Enclosed room drifting keywords quarantine/sanitization (`sanitize_spatial_prompt`), outdoor keyword removal.
   - Test Scene Transition Gating (locking enclosure vs valid transition).
   - Test serialization/deserialization roundtrip into `StoryMemory.to_dict()` and `from_dict()`.
   - Test backward compatibility with legacy None or empty inputs.

5. Verification:
   - Run `python -m py_compile` across all modified backend files.
   - Run `python -m unittest backend/tests/test_dynamic_scene_graph.py -v` (100% pass).
   - Run existing regression tests: `python -m unittest backend/tests/test_light_novel_engine.py` and others.

6. Reporting:
   - Document all changes, test commands, and layout verification in `e:\NarrAI\.agents\worker_r2_m2\handoff.md`.
   - Send completion message to parent when done.
