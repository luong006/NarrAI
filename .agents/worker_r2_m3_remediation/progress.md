# Progress - Milestone 3 Remediation

- Last visited: 2026-09-20T18:35:00Z
- Status: Completed code remediation across `backend/agents/comic_agent.py`, `backend/services/cloudflare_ai.py`, and `backend/tests/test_challenger_r2_m3_1_adversarial.py`.

## Completed Tasks:
1. Added Vietnamese negation and prohibition guard (`VIETNAMESE_NEGATION_WORDS`, `CLAUSE_DELIMITERS_PATTERN`, `is_action_negated()`) to `backend/agents/comic_agent.py`.
2. Tightened action gesture patterns (1, 4, 6) in `ACTION_GESTURE_MAPPINGS` and updated `extract_action_from_prose()` to iterate matches and filter out negated actions.
3. Updated `SPATIAL_ENCLOSURES` to include `sword`, `blade`, `weapon` in forbidden spatial tokens.
4. Hardened `sanitize_spatial_prompt()` to include extended modifiers, prepositions, plurals `(?:es|s)?`, clean trailing dangling prepositions, and collapse multiple commas.
5. Reordered prompt assembly in `_validate_panels()` for CLIP 77-token budget prioritization: setting anchor (~tokens 22-45) -> core action gesture (~tokens 45-65) -> character visual DNA -> remaining scene nuances.
6. Implemented `format_pollinations_prompt(prompt, max_len=500)` in `backend/services/cloudflare_ai.py` with delimiter-aware boundary slicing and guaranteed setting anchor preservation.
7. Updated `get_cached_or_generate_image()` fallback in `backend/services/cloudflare_ai.py` to use `format_pollinations_prompt()`.
8. Upgraded `backend/tests/test_challenger_r2_m3_1_adversarial.py` to assert robust fixed behaviors across all 4 vulnerability categories.
