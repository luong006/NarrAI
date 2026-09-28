## 2026-09-20T13:54:55Z
You are worker_r2_m2_remediation, a specialized implementation Worker subagent.
Your Working Directory: e:\NarrAI\.agents\worker_r2_m2_remediation
Workspace Directory: e:\NarrAI
Original Request File: e:\NarrAI\.agents\ORIGINAL_REQUEST.md (MANDATORY: Read this first!)
Project Document: e:\NarrAI\.agents\PROJECT.md
Explorer Remediation Blueprint: e:\NarrAI\.agents\explorer_r2_m2_fix\report.md (MANDATORY: Read Section 3 carefully! It contains exact line-by-line drop-in replacement code for all 6 vulnerabilities).
Adversarial Test Suite: e:\NarrAI\backend\tests\test_adversarial_dsgo.py

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Exclusive File Write Ownership:
- backend/models/scene_graph.py
- backend/tests/test_dynamic_scene_graph.py
- backend/tests/test_adversarial_dsgo.py

Objectives:
1. Apply the drop-in remediation code from Section 3 of e:\NarrAI\.agents\explorer_r2_m2_fix\report.md to backend/models/scene_graph.py:
   - Fix 1: Negation detection in is_transition_verb_negated() and negative lookahead for deceptive objects (?!\s*(?:sổ|tủ|hòm|xe)).
   - Fix 2: Candidate enclosure matching in gate_scene_transition: remove premature break, sort candidates by connectivity and prose position.
   - Fix 3: Compound word preservation in sanitize_spatial_prompt: use (?<![\w\-]) and (?![\w\-])(?:\s*[,.])? to preserve hyphenated compounds (street-style, off-road, car-free) and handle street (outdoor).
   - Fix 4: Disconnected entity teleportation & active_entities cleanup in transition_scene: reject moving disconnected entities, and clean up active_entities from old_loc.
   - Fix 5: Safe deserialization in DynamicSceneGraph.from_dict: wrap model_validate in try/except, sanitize malformed dicts, provide safe fallback.
   - Fix 6: Vitality enforcement: exclude DECEASED entities from moving in transition_scene, and validate UNCONSCIOUS actors in validate_vitality.
2. Verification:
   - Run python -m py_compile backend/models/scene_graph.py
   - Run python -m unittest backend/tests/test_adversarial_dsgo.py -v (all 18 tests MUST pass)
   - Run python -m unittest backend/tests/test_dynamic_scene_graph.py -v (all 15+ tests MUST pass)
   - Run python -m unittest backend/tests/test_light_novel_engine.py -v (all tests pass, 0 regressions on M1)
3. Report your actions and test outputs in e:\NarrAI\.agents\worker_r2_m2_remediation\handoff.md and send a completion message to parent.
