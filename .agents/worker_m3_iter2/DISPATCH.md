## 2026-09-20T05:30:05Z

You are worker_m3_iter2, assigned to remediate Milestone 3 of Project NarrAI based on adversarial feedback.
Your working directory is: e:\NarrAI\.agents\worker_m3_iter2

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY CONTEXT:
Read e:\NarrAI\.agents\ORIGINAL_REQUEST.md carefully before doing any work.
Read e:\NarrAI\PROJECT.md.
Read e:\NarrAI\.agents\challenger_m3_2\handoff.md (CRITICAL: contains exact root causes and remediation requirements).
Also read e:\NarrAI\.agents\challenger_m3_1\handoff.md and e:\NarrAI\.agents\worker_m3\handoff.md.

ASSIGNMENT — Remediate Milestone 3 Deficiencies:
1. Fix Spaced Dots Ellipsis Leak in `backend/agents/comic_agent.py`:
   - In `sanitize_complete_dialogue`:
     Currently Step 4 (`s = re.sub(r'\.{2,}', '.', s)`) runs before Step 5 (`s = re.sub(r'\s+([,\.!\?])', r'\1', s)`). When input has spaced dots (e.g. `"Tôi . . . không biết."`), Step 5 deletes spaces between dots AFTER Step 4 has already run, leaving `"Tôi... không biết."`.
     Remedy: Pre-normalize spaced dots in Step 3 with `s = re.sub(r'(?:\s*\.\s*){2,}', ' - ', s)`, AND also ensure Step 4 runs after Step 5 so no consecutive dots can ever emerge.
     Assert that `sanitize_complete_dialogue("Tôi . . . không biết.")` contains NO `...`.
2. Fix None/Null Dialogue Coercion in `backend/agents/comic_agent.py`:
   - In `_validate_panels` (lines 533 and 636), `item.get("dialogue_text", "")` returns `None` if the dictionary has `{"dialogue_text": None}`. Calling `str(None)` turns it into `"None"`, which `sanitize_complete_dialogue` turns into `"None."`.
     Remedy: Use `str(item.get("dialogue_text") or "").strip()` and `str(item.get("narrator_text") or "").strip()`. If empty or None, it falls back to rich default sentences, NEVER literal `"None."`.
3. Fix Test Suite Assertion in `backend/tests/test_comic_zero_truncation.py`:
   - In `test_fallback_no_twelve_panel_cutoff` (lines 238-245):
     The test provided 15 narrative sentences, but `decompose_story_beats` groups narrative sentences up to 3 sentences per beat (by design for manga pacing), producing 5 panels. The assertion `self.assertGreaterEqual(len(panels), 15)` failed with `AssertionError: 5 not greater than or equal to 15`.
     Remedy: Change `test_fallback_no_twelve_panel_cutoff` to use 15 dialogue lines:
     `dialogues = [f'Nhân vật {i + 1}: "Câu thoại số {i + 1} diễn ra đầy kịch tính!"' for i in range(15)]`
     Because dialogue lines break beats individually, this produces >= 15 panels and properly verifies the removal of the 12-panel cap.
     Also add a test with 45 narrative sentences verifying >= 15 panels.
   - Add test case verifying spaced dots: `sanitize_complete_dialogue("Tôi . . . không biết.")` has 0% `...`.
   - Add test case verifying `None` dialogue: `_validate_panels([{"dialogue_text": None}])` does not contain `"None."`.
4. Fix `backend/tests/test_challenger_m3_adversarial.py`:
   - In `test_fallback_removes_twelve_panel_limit_and_dots` (line 345), change the 20 paragraphs to 20 dialogue lines (or 60 narrative sentences) so `self.assertGreaterEqual(len(panels), 20)` succeeds cleanly.
5. Verification:
   - Ensure all backend files compile: `python -m py_compile backend/agents/comic_agent.py backend/main.py backend/tests/test_comic_zero_truncation.py backend/tests/test_challenger_m3_adversarial.py backend/tests/test_challenger_m3_2_stress.py`.
   - Verify that `test_comic_zero_truncation.py`, `test_challenger_m3_adversarial.py`, and `test_challenger_m3_2_stress.py` all pass completely with 0 failures.
   - Verify regression suites pass (`test_copilot_unwrap.py`, `test_comic_dna_seed.py`, `test_adversarial_unwrap.py`, `test_challenger_m2_adversarial.py`).
   - Write comprehensive report to `e:\NarrAI\.agents\worker_m3_iter2\handoff.md`.
