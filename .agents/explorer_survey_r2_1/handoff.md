# HANDOFF REPORT — R1. MODERN LIGHT NOVEL & WEB NOVEL ENGINE

**Agent ID**: `explorer_survey_r2_1`  
**Working Directory**: `e:\NarrAI\.agents\explorer_survey_r2_1`  
**Handoff Type**: Hard Handoff (Investigation & Proposal Complete)  
**Parent Agent**: `parent` (`3095f755-04d9-4da7-bb70-b02b1e63c909`)  
**Timestamp**: 2026-09-20T13:26:00Z  

---

## 1. OBSERVATION

Direct code observations from the NarrAI codebase:

1. **Story Generation Core File Location & Persona**:
   - In `backend/agents/story_generator.py` (line 41, `class StoryGenerator`), the prompt builder `_build_prompt` (lines 86-127) uses:
     ```python
     system_prompt = f"""Bạn là một đại tiểu thuyết gia xuất chúng tầm cỡ quốc tế, chuyên sáng tác truyện bằng tiếng Việt hiện đại."""
     ```
   - In `backend/agents/story_generator.py` (lines 146-150), `generate_chapter_stream` uses:
     ```python
     system_prompt = f"""Ban la tac gia dang truc tiep viet mot chuong tieu thuyet bang tieng Viet."""
     ```
   - In `backend/agents/copilot_agent.py` (line 170), `DIRECT_EDIT_PROMPT` uses:
     ```python
     DIRECT_EDIT_PROMPT = """Bạn là Đại văn hào kiêm Biên tập viên hàng đầu."""
     ```

2. **Current Ruleset Bias**:
   - In `backend/agents/story_generator.py` (lines 5-36), `MODERN_NOVEL_WRITING_RULES` defines basic rules (In Medias Res, Show don't tell, Pacing, Dialogue with subtext, Narrative ontology, Cliffhanger, Anti-cliché banlist).
   - Crucially, it **lacks any definition of Point-of-View (POV)** (First-Person / Tight Third-Person), **lacks guidelines or formatting for Interior Monologues (độc thoại nội tâm)**, and lacks youth conversational dialogue conventions.

3. **Narrative Beat Absence**:
   - In `backend/agents/story_generator.py` (lines 45-77), `_extract_narrative_ontology` extracts 4 blocks: `[THỰC THỂ & NHÂN VẬT]`, `[QUAN HỆ & ĐỘNG CƠ]`, `[QUY TẮC THẾ GIỚI & BỐI CẢNH]`, and `[CHUỖI NHÂN QUẢ CHÍNH]`. There is no Narrative Beat breakdown.
   - In `backend/agents/story_memory.py` (lines 8-36, `StoryBible` and lines 39-95, `StoryMemory`), neither class stores or tracks Narrative Beats or progression milestones.
   - In `backend/agents/qa_refiner.py` (lines 43-62), `refine_prompt` establishes a traditional 4-stage outline ("Mở đầu", "Diễn biến", "Cao trào", "Kết thúc") rather than a dynamic 5-beat rhythm.

4. **Copilot & Editor Editorial Guidance**:
   - In `backend/agents/copilot_agent.py` (lines 226-298), `_perform_direct_manuscript_edit` uses `DIRECT_EDIT_PROMPT` which instructs editing without enforcing Light Novel / Web Novel standards.
   - In `backend/agents/editor_agent.py` (lines 11-18), `edit_text` provides general instructions without explicit inner monologue or sharp dialogue guidelines.

---

## 2. LOGIC CHAIN

1. **From Observation 1 (Persona priming)**: Calling the LLM "đại tiểu thuyết gia xuất chúng tầm cỡ quốc tế" and "Đại văn hào" primes the language model to mimic traditional 19th/20th-century classical literary authors. This directly produces long descriptive paragraphs, distant third-person omniscient narration, and slow-moving exposition instead of the snappy, immersive, youth-oriented feel of modern Light Novels and Web Novels.
2. **From Observation 2 (Missing POV & Interior Monologue rules)**: Without explicit instructions for Tight POV and Interior Monologues, LLMs treat characters from an external observation camera angle. The reader cannot experience the protagonist's uncensored thoughts, anxiety, tactical calculations, or witty self-reflections, which are the core emotional drivers of Light Novel / Web Novel readership.
3. **From Observation 3 (Lack of Narrative Beat architecture)**: Because `_extract_narrative_ontology` and `StoryBible` only capture static entities and broad causal chains, story chapters lack structural checkpoints. The AI tends to wander in the middle of chapters and abruptly invent an ending or cliffhanger, rather than executing a satisfying dramatic arc.
4. **From Observations 3 & 4 (Copilot/Editor alignment)**: When a user prompts the AI to "viết lại mở đầu kịch tính hơn" or "thêm xung đột", the Copilot currently falls back on generic editing instructions, often perpetuating or returning to static descriptive writing.
5. **Synthesis Conclusion**: Upgrading NarrAI to a modern Light Novel / Web Novel engine requires a coordinated 4-part transformation:
   - (A) Reforming System Prompts across `story_generator.py`, `copilot_agent.py`, `editor_agent.py`, and `qa_refiner.py` with the "Bút vàng Light Novel & Web Novel" persona and 4 stylistic pillars (Tight POV, Interior Monologue, Natural Youth Dialogue, Fast Pacing).
   - (B) Introducing a formal **5-Beat Dramatic Narrative Architecture** (Incisive Hook -> Rising Friction -> Turning Point -> Visceral Climax -> Lingering Cliffhanger).
   - (C) Updating `StoryBible` and `StoryMemory` to store and track narrative beats.
   - (D) Upgrading `_extract_narrative_ontology` and `refine_prompt` to generate this beat sheet upfront.

---

## 3. CAVEATS

- **File Name Clarification**: The user request referenced `backend/agents/story_agent.py` as an example path; the actual file in the repository is `backend/agents/story_generator.py`.
- **Read-Only Scope**: In strict accordance with the explorer role constraints, no source code files were modified during this investigation. All proposed code modifications are documented in `report.md`.
- **Runtime Model Dependency**: The story generation model in production is `openai/gpt-oss-120b` via Groq. Groq's high throughput is well-suited for fast-paced streaming prose, but prompt clarity must be concise and avoid conflicting guidelines.

---

## 4. CONCLUSION

The investigation and architectural proposal for **R1. Tái Cấu Trúc Động Cơ Văn Phong Truyện Chữ (Modern Light Novel & Web Novel Engine)** is complete. 
A comprehensive technical report has been compiled at:
`e:\NarrAI\.agents\explorer_survey_r2_1\report.md`

Key deliverables produced:
1. Complete mapping of all relevant backend agents, prompts, data models, and frontend integration points.
2. Full replacement text for `LIGHT_NOVEL_ENGINE_RULES` and updated system prompts.
3. Detailed specifications for the **5 Dramatic Narrative Beats** framework.
4. Concrete prompt and code upgrades for `story_generator.py`, `copilot_agent.py`, `editor_agent.py`, `qa_refiner.py`, and `story_memory.py`.
5. Clear integration alignment showing how R1's visceral scene anchoring directly enables R2 (Dynamic Scene-Graph Ontology) and R3 (Text-to-Image Manga consistency).

---

## 5. VERIFICATION METHOD

To independently verify the findings and test the future implementation:

1. **Verify Source Code Locations**:
   - Inspect `backend/agents/story_generator.py` (lines 5-38, 45-77, 86-127, 139-179).
   - Inspect `backend/agents/copilot_agent.py` (lines 170-191).
   - Inspect `backend/agents/editor_agent.py` (lines 11-18).
   - Inspect `backend/agents/qa_refiner.py` (lines 43-62).
   - Inspect `backend/agents/story_memory.py` (lines 8-95).

2. **Syntax Compilation Check**:
   - Run Python compilation across backend files once implemented:
     ```bash
     python -m py_compile backend/agents/story_generator.py backend/agents/copilot_agent.py backend/agents/editor_agent.py backend/agents/qa_refiner.py backend/agents/story_memory.py backend/agents/memory_extractor.py backend/main.py
     ```

3. **Narrative Quality Validation**:
   - Generate story with test prompt (e.g. from `backend/data/trending_themes.json`).
   - Verify opening 3 sentences contain an immediate hook (In Medias Res), 0% weather/scenery cliché.
   - Verify presence of interior monologues and natural modern Vietnamese dialogue.
   - Verify chapter progression fulfills the 5-beat rhythm ending on a cliffhanger.
