# BRIEFING — 2026-09-29T03:24:00Z

## Mission
Investigate and map NarrAI backend codebase for Requirement #1: Copilot Flexible Manuscript Surgery with 5 targets, Dynamic Semantic Chunk Slicing, heading preservation, and Story ID / streaming generation endpoints.

## 🔒 My Identity
- Archetype: explorer
- Roles: Backend Copilot & Manuscript Surgery Survey
- Working directory: e:\NarrAI\.agents\teamwork\explorer_r5_survey_1
- Original parent: 9fb5ac33-e7c4-4e1d-855b-61d34153fe76
- Milestone: Survey & Architecture Mapping for R5 Follow-up

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Analyze FastAPI routes, story services, copilot router/service, manuscript editing logic, chunking/slicing, LLM prompts
- Survey Requirement #1: 5 surgery targets, dynamic semantic chunk slicing, heading preservation, story ID allocation, streaming generation endpoints
- Output detailed survey report to survey_report.md and handoff.md
- Update progress.md with heartbeat
- Send message to caller when done

## Current Parent
- Conversation ID: 9fb5ac33-e7c4-4e1d-855b-61d34153fe76
- Updated: 2026-09-29T03:24:00Z

## Investigation State
- **Explored paths**: `backend/main.py`, `backend/agents/copilot_agent.py`, `backend/agents/story_generator.py`, `backend/agents/editor_agent.py`, `backend/agents/qa_refiner.py`, `backend/db/models.py`, `backend/services/`, `backend/tests/`, `frontend/src/components/editor/AICopilotPanel.tsx`, `frontend/src/lib/api.ts`
- **Key findings**:
  1. `copilot_agent.py` only uses crude boolean flags (`is_opening`, `is_ending`, `is_middle`) and falls back to 8,000-char truncation for Target 2 (Character/Dialogue) & Target 5 (Tone Shift).
  2. Heading preservation currently only operates when `is_opening_edit == True`, leaving Targets 2, 3, 4, 5 vulnerable to title and chapter header loss (`## Chương X`).
  3. A single monolithic edit prompt is used instead of 5 dedicated surgical prompts.
  4. Story ID is only allocated at stream termination and only for authenticated users; guest users receive no Story ID.
- **Unexplored areas**: None for Requirement #1 backend scope; ready for implementation.

## Key Decisions Made
- Designed `SurgeryTarget` enum and multi-dimensional intent classifier for the 5 targets.
- Designed `SemanticChunkSlicer` utilizing chapter headings and paragraphs for clean `prefix` -> `window_to_edit` -> `suffix` slicing.
- Designed `HeadingPreservationEngine` safeguarding `**[TITLE]**` and `## Chương X` headings.
- Formulated 5 distinct surgical prompt templates tailored to Light Novel rules.
- Designed early Story ID allocation flow and `POST /api/stories/allocate` endpoint.

## Artifact Index
- `e:\NarrAI\.agents\teamwork\explorer_r5_survey_1\survey_report.md` — detailed survey report with code templates and prompts
- `e:\NarrAI\.agents\teamwork\explorer_r5_survey_1\handoff.md` — 5-component handoff report
- `e:\NarrAI\.agents\teamwork\explorer_r5_survey_1\progress.md` — liveness heartbeat
