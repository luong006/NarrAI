## 2026-09-20T18:30:00Z
You are Worker (worker_r2_m3_remediation) for Milestone 3 Remediation.
Working Directory: e:\NarrAI\.agents\worker_r2_m3_remediation
Workspace: e:\NarrAI
Original Request: e:\NarrAI\.agents\ORIGINAL_REQUEST.md (MANDATORY: read this first!)
Remediation Blueprint: e:\NarrAI\.agents\explorer_r2_m3_fix\report.md (MANDATORY: Follow this exact specification!)
Project Master Plan: e:\NarrAI\.agents\PROJECT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A forensic auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

File Write Ownership (Exclusive):
- backend/agents/comic_agent.py
- backend/services/cloudflare_ai.py
- backend/tests/test_challenger_r2_m3_1_adversarial.py

Your Mission:
Implement the exact drop-in remediation code from e:\NarrAI\.agents\explorer_r2_m3_fix\report.md:
1. In `backend/agents/comic_agent.py`:
   - Add `VIETNAMESE_NEGATION_WORDS`, `CLAUSE_DELIMITERS_PATTERN`, and `is_action_negated()`.
   - Update `ACTION_GESTURE_MAPPINGS` and `extract_action_from_prose()` to enforce negation checking on all matches, and tighten patterns 1, 4, 6.
   - Update `SPATIAL_ENCLOSURES` to include `sword`, `blade`, `weapon` in forbidden tokens for school/classroom.
   - Update `sanitize_spatial_prompt()` to include modifiers (`ancient`, `stone`, `old`, `abandoned`, `wooden`), prepositions (`at`, `to`, `through`, `into`, `outside`, `towards`), plurals `(?:es|s)?`, and collapse double commas cleanly.
   - Update `_validate_panels()` prompt layout to prioritize `setting: {setting_anchor}` and `action_desc` early (right after `STYLE_PREFIX`), ensuring both are within CLIP's 77-token attention window.
2. In `backend/services/cloudflare_ai.py`:
   - Implement `format_pollinations_prompt(prompt, max_len=500)` with delimiter-aware slicing and setting anchor preservation.
   - Update `get_cached_or_generate_image()` fallback to use `format_pollinations_prompt()`.
3. In `backend/tests/test_challenger_r2_m3_1_adversarial.py`:
   - Update test suite with the complete drop-in implementation from Section 6.2 of `report.md`, asserting the robust, fixed behavior.
4. Run verification commands:
   - `python -m py_compile backend/agents/comic_agent.py backend/services/cloudflare_ai.py backend/tests/test_challenger_r2_m3_1_adversarial.py backend/tests/test_comic_modern_school_sync.py`
   - `python -m unittest backend/tests/test_challenger_r2_m3_1_adversarial.py -v`
   - `python -m unittest backend/tests/test_comic_modern_school_sync.py -v`
   - `python -m unittest backend/tests/test_challenger_r2_m3_2_stress.py -v`
   - `python -m unittest backend/tests/test_comic_dna_seed.py -v`
   - `python -m unittest backend/tests/test_comic_zero_truncation.py -v`

Write your handoff report to `e:\NarrAI\.agents\worker_r2_m3_remediation\handoff.md` and send a message when complete.
