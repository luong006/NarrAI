## 2026-09-20T13:26:16Z
You are worker_r2_m1, a specialized implementation Worker subagent.
Your Working Directory: e:\NarrAI\.agents\worker_r2_m1
Workspace Directory: e:\NarrAI
Original Request File: e:\NarrAI\.agents\ORIGINAL_REQUEST.md (MANDATORY: You MUST read e:\NarrAI\.agents\ORIGINAL_REQUEST.md before starting work! Focus on ## 2026-09-20T13:19:05Z - Requirement R1).
Project Scope Document: e:\NarrAI\.agents\PROJECT.md
Explorer Survey Report: e:\NarrAI\.agents\explorer_survey_r2_1\report.md (MANDATORY: Read this report carefully, it contains precise line numbers, current gaps, and exact proposed prompt and code structures).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Exclusive File Write Ownership:
- backend/agents/story_generator.py
- backend/agents/copilot_agent.py
- backend/agents/editor_agent.py
- backend/agents/qa_refiner.py
- backend/agents/story_memory.py
- backend/tests/test_light_novel_engine.py (create or update tests)

Objectives for Milestone 1 (R1. Modern Light Novel & Web Novel Engine):
1. Reform Story System Prompts:
   - In backend/agents/story_generator.py:
     * Replace MODERN_NOVEL_WRITING_RULES with LIGHT_NOVEL_ENGINE_RULES embodying:
       a. Tight POV (Ngôi thứ nhất hoặc Ngôi thứ ba bám sát).
       b. Rich Interior Monologue (Độc thoại nội tâm sắc bén: tâm lý, lo âu, tính toán, tự giễu cợt).
       c. Sharp Youth Dialogue (Đối thoại tự nhiên, gãy gọn, có subtext, mang ngôn ngữ giới trẻ hiện đại, không ngữ điệu dịch thuật).
       d. In Medias Res Hook (Mở đầu cuốn hút ngay từ câu đầu, quăng người đọc vào tình huống kịch tính, 0% tả thời tiết mây gió dông dài).
       e. Anti-Cliché Banlist (Cấm sáo ngữ mở đầu, cấm liệt kê tính từ trừu tượng).
     * Update author persona in _build_prompt and generate_chapter_stream from 19th century "đại tiểu thuyết gia" to modern trending Light/Web Novel writer ("Bút vàng chuyên gia sáng tác Light Novel & Web Novel thịnh hành").
   - In backend/agents/copilot_agent.py:
     * Update DIRECT_EDIT_PROMPT to align strictly with Light Novel / Web Novel standards, ensuring manual or copilot edits never regress into static descriptive prose.
   - In backend/agents/editor_agent.py:
     * Align edit_text prompt with Light Novel pacing, tight POV, and punchy dialogue.
   - In backend/agents/qa_refiner.py:
     * Update refine_prompt outline generator to produce the 5-Beat Dramatic Narrative Architecture.

2. Implement 5-Beat Dramatic Narrative Architecture:
   - Beat 1: Hook (0-15%): Xung đột bùng nổ ngay lập tức, cuốn độc giả vào tình thế nan giải.
   - Beat 2: Rising Friction / Complication (15-40%): Trở ngại leo thang, phản ứng tâm lý và đối thoại va chạm.
   - Beat 3: Turning Point (40-70%): Biến cố đảo chiều nhận thức hoặc kế hoạch phá sản.
   - Beat 4: Visceral Climax (70-90%): Đỉnh điểm cảm xúc hoặc hành động quyết định.
   - Beat 5: Lingering Cliffhanger (90-100%): Nút thắt chưa gỡ, kích thích tột độ muốn đọc chương tiếp.
   - Update _extract_narrative_ontology in story_generator.py to include [CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC BEATS)].
   - Update StoryBible in backend/agents/story_memory.py to store narrative_beats: List[str] = field(default_factory=list) and include them in to_prompt_block() and serialization (to_dict, from_dict).
   - Update generate_chapter_stream to enforce the 5 beats during streaming narrative generation.

3. Verification:
   - Create comprehensive unit tests in backend/tests/test_light_novel_engine.py verifying:
     * LIGHT_NOVEL_ENGINE_RULES presence and contents (POV, interior monologue, youth dialogue, hook, anti-cliché).
     * StoryBible narrative_beats serialization/deserialization and prompt block formatting.
     * _extract_narrative_ontology prompt includes 5 dramatic beats.
     * copilot DIRECT_EDIT_PROMPT and editor edit_text alignment.
   - Run python -m py_compile across all modified backend files.
   - Run python -m unittest backend/tests/test_light_novel_engine.py and ensure 100% pass.
   - Run existing tests to ensure no regressions: python -m unittest backend/tests/test_comic_zero_truncation.py (and others).

4. Reporting:
   - Record all actions, test results, commands executed, and layout verification in e:\NarrAI\.agents\worker_r2_m1\handoff.md.
   - Send completion message to parent when done.
