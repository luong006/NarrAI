# Project: NarrAI Core Hardening & Consistency

## Architecture
NarrAI is an AI-powered storytelling and manga creation studio with a FastAPI backend and Next.js / React frontend.
- **Backend**: FastAPI (`backend/main.py`) driving specialized AI agents:
  - `StoryAgent`: Plot & chapter generation.
  - `ComicDirectorAgent` (`backend/agents/comic_agent.py`): Story beat breakdown, character visual DNA extraction, panel script generation, layout direction.
  - `CopilotAgent` (`backend/agents/copilot_agent.py`): Interactive editor assistant, direct manuscript revisions (`edit_story_direct`).
  - `CloudflareAIService` (`backend/services/cloudflare_ai.py`): Text-to-image diffusion generation with caching.
- **Frontend**: Next.js 14 App Router (`frontend/src/app/page.tsx`):
  - `StoryEditor` (`frontend/src/components/editor/StoryEditor.tsx`): ContentEditable Markdown prose editor.
  - `AICopilotPanel` (`frontend/src/components/editor/AICopilotPanel.tsx`): Interactive chat with Copilot.
  - `ComicViewer` (`frontend/src/components/comic/ComicViewer.tsx`): Sequential manga viewer with speech bubbles.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | R1.1 Backend Multi-pass Unwrap & Prose Sanitizer | `unwrap_story_prose` in `copilot_agent.py` decodes nested JSON (`action_params`, `updated_story_content`, `story_content`), unescapes `\n` and `\"` unconditionally, handles codeblocks and dialogue quotes. | M1 | Survey 1 |
| 2 | R1.2 Direct Edit Robustness & Keyword Extension | `_perform_direct_manuscript_edit` uses `strict=False`, robust fallback, keyword extensions for single-word Vietnamese editing commands. | M1 | Survey 1 |
| 3 | R1.3 Backend Database Quarantine | `backend/main.py` validates and prevents raw JSON strings from being persisted into SQLite `story.story_content`. | M1 | Survey 1 |
| 4 | R1.4 Frontend Multi-layer JSON Decoupler & Unescape | `frontend/src/app/page.tsx` implements multi-pass `unwrapStoryProseFrontend` to eliminate nested JSON and escaped newlines. | M1 | Survey 1 |
| 5 | R1.5 Editor DOM Safety Net | `frontend/src/components/editor/StoryEditor.tsx` filters any accidental raw JSON before rendering to DOM `innerText`. | M1 | Survey 1 |
| 6 | R2.1 Ultra-detailed DNA Extractor Prompt | `DNA_EXTRACTOR_PROMPT` in `comic_agent.py` extracts exact garment types, distinct colors, collar/neck/chest accessories, exact hairstyle, and immutable facial features. | M2 | Survey 2 |
| 7 | R2.2 Smart DNA Injection with Semantic Pronoun Dict | `_validate_panels` scans both prompt and Vietnamese dialogue, uses regex word boundaries, resolves Vietnamese pronouns/relational nouns, and injects all present characters without early break. | M2 | Survey 2 |
| 8 | R2.3 Deterministic Comic Seed by Story ID | `cloudflare_ai.py` implements `get_deterministic_comic_seed(story_id)` and `backend/main.py` supplies canonical `story_id` to lock latent diffusion noise across all panels. | M2 | Survey 2 |
| 9 | R3.1 Eliminate Schema Few-Shot Truncation Leak | `BEAT_DIRECTOR_PROMPT` in `comic_agent.py` removes all `"dialogue_text": "..."` and `"..."` examples, replacing them with complete Vietnamese sentences. | M3 | Survey 3 |
| 10 | R3.2 Zero-Ellipsis Dialogue Sanitizer | `sanitize_complete_dialogue` in `comic_agent.py` strips all `...`, `…`, and `.....` mid-sentence and trailing ellipses, converting pauses to dashes/commas and ensuring proper terminal punctuation. | M3 | Survey 3 |
| 11 | R3.3 Sentence Boundaries Decomposition & Beat Fallback | `decompose_story_beats` in `comic_agent.py` and `_create_structured_beat_fallback` break paragraphs into atomic dialogue/narrative beats, generating sequential panels with zero ellipsis. | M3 | Survey 3 |
| 12 | R3.4 Sentence-Bounded Chunking | `extract_sentence_bounded_chunk` in `backend/main.py` replaces arbitrary 6000-char string slicing with complete sentence boundary breaks. | M3 | Survey 3 |
| 13 | M4 Full System Verification & Quality Gate | Backend `py_compile`, frontend `npm run build`, regression test suite verifying R1, R2, R3 invariants. | M4 | System Gate |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | R1 Copilot Editor Raw JSON Elimination | `backend/agents/copilot_agent.py`, `backend/main.py`, `frontend/src/app/page.tsx`, `frontend/src/components/editor/StoryEditor.tsx` | none | DONE |
| M2 | R2 Manga Character Visual Consistency & Seed | `backend/agents/comic_agent.py` (DNA & Smart Injection), `backend/services/cloudflare_ai.py`, `backend/main.py` (seed derivation) | M1 | DONE |
| M3 | R3 Zero Truncation Comic Panels & Sentence Boundaries | `backend/agents/comic_agent.py` (Prompts, Sanitizer, Beat decomposition), `backend/main.py` (chunking) | M2 | DONE |
| M4 | Final Quality Gate & Verification | Full system py_compile, frontend npm run build, comprehensive unit/E2E test suite | M1, M2, M3 | DONE |

## Code Layout
- `backend/agents/copilot_agent.py`: Copilot manuscript direct edit logic, prose unwrapping. Owned exclusively by M1.
- `frontend/src/app/page.tsx`: Copilot event handling, story content state update. Owned exclusively by M1.
- `frontend/src/components/editor/StoryEditor.tsx`: Editor DOM rendering. Owned exclusively by M1.
- `backend/services/cloudflare_ai.py`: Deterministic seed calculation and image generation. Owned exclusively by M2.
- `backend/agents/comic_agent.py`:
  - Visual DNA Extraction & Smart DNA Injection: Owned by M2.
  - Beat prompts, zero ellipsis sanitization, sentence beat decomposition, fallback: Owned by M3.
- `backend/main.py`:
  - Copilot DB persistence unwrap: Owned by M1.
  - Comic image seed passing: Owned by M2.
  - Sentence-bounded chunking: Owned by M3.
- `backend/tests/`: Quality gate verification tests. Owned by M4.

## Interface Contracts
### Copilot ↔ Editor
- `copilot_agent.process_event` returns `{"action": "edit_story_direct", "action_params": {"updated_story_content": "<clean markdown prose>"}}`.
- `updated_story_content` MUST be raw markdown text only, never JSON-wrapped, with real newlines (`\n`).

### Comic Agent ↔ Diffusion Service
- `cloudflare_ai.get_deterministic_comic_seed(story_id: int) -> int`: Returns fixed seed in range `[100000, 999999]`.
- `ComicDirectorAgent.generate_script`: Each panel's `dialogue_text` must be a complete Vietnamese sentence ending in `.` / `!` / `?` / `"` with 0% `...` or `.....`.
