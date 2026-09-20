## 2026-09-20T05:12:28Z

You are worker_m3, assigned to Milestone 3 of Project NarrAI.
Your working directory is: e:\NarrAI\.agents\worker_m3

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY CONTEXT:
Read e:\NarrAI\.agents\ORIGINAL_REQUEST.md carefully before doing any work.
Also read e:\NarrAI\PROJECT.md and e:\NarrAI\.agents\explorer_survey_3\handoff.md.

YOUR ASSIGNMENT — Milestone 3 (Requirement R3):
Chấm dứt hoàn toàn tình trạng cắt xén dấu '.....' trong truyện tranh & Sentence Boundaries Decomposition.

Exclusively Owned Files for this milestone:
1. `backend/agents/comic_agent.py`
2. `backend/main.py` (specifically chunking logic)
3. `backend/tests/test_comic_zero_truncation.py` (create comprehensive test suite)

Detailed Requirements to Implement:
1. Eliminate Schema Few-Shot Truncation Leak in `backend/agents/comic_agent.py`:
   - In `BEAT_DIRECTOR_PROMPT`, remove all `"dialogue_text": "..."` and `"image_prompt": "wide establishing shot of..."`. Replace with complete, vivid Vietnamese sentences (e.g. `"dialogue_text": "Hôm nay là một ngày thật đặc biệt đối với tôi."`).
   - Add explicit instructions in `BEAT_DIRECTOR_PROMPT` prohibiting `...`, `…`, `.....`, and incomplete trailing fragments. Every dialogue and narrator caption must be a complete, grammatically sound sentence ending with `.`, `!`, or `?`.
2. Implement Zero-Ellipsis Dialogue Sanitizer:
   - In `backend/agents/comic_agent.py`, implement `sanitize_complete_dialogue(text: str) -> str`:
     * Clean all occurrences of `...`, `…`, `.....`, and multiple consecutive periods.
     * Mid-sentence pauses or speech hesitations should be converted smoothly to hyphens/dashes (` - `) or commas (`, `) so character emotion is preserved without ellipsis.
     * Clean all trailing dots/ellipses.
     * Ensure the string ends with a valid terminal punctuation mark (`.`, `!`, `?`, `"`, `”`).
     * If the dialogue was entirely dots, whitespace, or empty, return an empty string or complete sentence as appropriate.
   - Use `sanitize_complete_dialogue` inside `_validate_panels` for both `dialogue_text` and any narrator text.
3. Sentence Boundaries Decomposition:
   - In `backend/agents/comic_agent.py`, implement `decompose_story_beats(story_text: str) -> List[str]`:
     * Split Vietnamese narrative prose cleanly at sentence boundaries (`.`, `!`, `?`, `\n`, Vietnamese dialogue quotes `"..."`, `“...”`, and dashes `—`).
     * Ensure short dialogues (< 15 chars like "Chào bạn!", "Đi thôi!") are NOT discarded.
     * Group sentences into cohesive story beats (e.g., 1-3 sentences per beat).
4. Overhaul Beat Fallback Generation:
   - In `backend/agents/comic_agent.py`, update `_create_structured_beat_fallback`:
     * Remove the hardcoded `"dialogue_text": "Câu chuyện bắt đầu..."`. Replace with a complete sentence derived from the decomposed beats or a complete opening sentence.
     * Use `decompose_story_beats` to generate sequential panels matching the full story progression without arbitrary line truncations or 12-panel cutoffs.
     * Ensure every fallback panel has complete, non-truncated dialogue.
5. Sentence-Bounded Chunking in `backend/main.py`:
   - Implement `extract_sentence_bounded_chunk(text: str, target_size: int = 5000, max_limit: int = 6500) -> tuple[str, int]`:
     * In `create_comic` and `continue_comic`, replace arbitrary `request.story_text[:chunk_size]` cuts with `extract_sentence_bounded_chunk`.
     * The chunk must break strictly at the nearest sentence boundary (`. `, `! `, `? `, `.\n`, `!\n`, `?\n`, `."`, etc.) before or around `target_size`, never amputating words or sentences midway.
6. Test Suite Creation:
   - Create `backend/tests/test_comic_zero_truncation.py` with comprehensive unit tests covering:
     * `sanitize_complete_dialogue` with various ellipsis patterns (trailing, mid-sentence, multiple dots `.....`, unicode `…`, quotes).
     * `decompose_story_beats` with multi-sentence paragraphs, dialogue lines, exclamation/question marks.
     * Fallback generation verifying 0% ellipsis in any panel.
     * `extract_sentence_bounded_chunk` verifying clean sentence boundaries on long texts (> 6000 chars).
     * Panel validation ensuring complete sentences and zero `...`.
7. Verification Requirements:
   - Compile all modified backend files with `python -m py_compile backend/agents/comic_agent.py backend/main.py backend/tests/test_comic_zero_truncation.py`.
   - Run unittest for `test_comic_zero_truncation.py`.
   - Run existing regression tests to ensure no breakage:
     * `python -m unittest backend/tests/test_copilot_unwrap.py`
     * `python -m unittest backend/tests/test_comic_dna_seed.py`
     * `python -m unittest backend/tests/test_adversarial_unwrap.py`
     * `python -m unittest backend/tests/test_challenger_m2_adversarial.py`
   - Document all changes and verification outputs in `e:\NarrAI\.agents\worker_m3\handoff.md`.
   - Send completion message to parent orchestrator with reference to your handoff.md.
