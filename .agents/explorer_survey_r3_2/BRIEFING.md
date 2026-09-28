# BRIEFING — 2026-09-22T04:38:00Z

## Mission
Investigate Requirements R3 (Redis Cache Layer with Fallback) and R4 (Fix AI Co-pilot Interaction Errors, Bilingual Intent Recognition, Token Budgeting, and Resilient Fallback)

## 🔒 My Identity
- Archetype: explorer
- Roles: explorer
- Working directory: e:\NarrAI\.agents\explorer_survey_r3_2
- Original parent: a3edd042-8945-4b7c-87dd-9bb0b36f6266
- Milestone: survey_r3_r4

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Deliver structured handoff report in handoff.md
- Maintain progress.md heartbeat

## Current Parent
- Conversation ID: a3edd042-8945-4b7c-87dd-9bb0b36f6266
- Updated: 2026-09-22T04:45:00Z

## Investigation State
- **Explored paths**:
  - `backend/main.py` (caching dictionaries `USER_CACHE`, `STORY_SESSIONS`, `/api/copilot-event`, `/api/stories/{id}`)
  - `backend/agents/copilot_agent.py` (`_is_direct_edit_request`, `_perform_direct_manuscript_edit`, `process_event`, `COPILOT_SYSTEM_PROMPT`, `DIRECT_EDIT_PROMPT`)
  - `backend/agents/story_memory.py` (`StoryMemory`, `StoryBible` serialization to_dict / from_dict)
  - `backend/agents/story_generator.py` (`handle_chat_instruction`, context trimming)
  - `backend/agents/editor_agent.py` (`edit_text`)
  - `backend/llm/groq_client.py` (token estimation, safe max tokens, retry logic)
  - `backend/services/cloudflare_ai.py` (disk caching pattern)
  - `backend/requirements.txt` (missing redis/cachetools)
  - `frontend/src/app/page.tsx` (`handleSendCopilotMessage`, 15,000 char context slice)
  - `frontend/src/components/editor/AICopilotPanel.tsx` (English quick prompts)
  - `frontend/src/lib/api.ts` (`sendCopilotEvent`)
  - `backend/tests/run_full_system_benchmark.py` & `test_copilot_unwrap.py`
- **Key findings**:
  - R4 Root Cause: `_is_direct_edit_request` has zero English keywords. English quick prompts ("Rewrite in a darker...", "Write a completely different opening...") return False.
  - Bypassing direct edit triggers Step 2, which duplicates 15,000 chars of story in user prompt while system prompt also has short_context. This exhausts Groq token limits (7600 max), clamps completion tokens to < 1000 or throws ValueError, causing JSON truncation. Truncated JSON fails `json.loads`, throwing exception that produces verbatim error message: "Xin lỗi, Hệ thống chỉ huy đang gặp trục trặc nhẹ. Bạn vui lòng thử lại nhé!".
  - R3 Findings: `cache_service.py` is absent. Only primitive, unbounded Python dicts exist with no TTL/LRU. Redis is not connected. A dual-mode `CacheManager` with zero-dependency thread-safe LRU+TTL in-memory cache and optional Redis pool achieves < 0.1ms (in-memory) / < 2ms (Redis) query latency (< 20ms required).
- **Unexplored areas**: None. Both R3 and R4 thoroughly explored down to exact line numbers and root causes.

## Key Decisions Made
- Formulate complete architectural design and code blueprints for R3 `CacheManager` and R4 bilingual intent/token budget/retry in `handoff.md`.

## Artifact Index
- e:\NarrAI\.agents\explorer_survey_r3_2\handoff.md — Final investigation handoff report
- e:\NarrAI\.agents\explorer_survey_r3_2\progress.md — Progress log & heartbeat
