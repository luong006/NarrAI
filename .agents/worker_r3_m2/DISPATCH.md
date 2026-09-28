## 2026-09-22T06:02:35Z

You are worker_r3_m2, an implementation worker.
Working directory: e:\NarrAI\.agents\worker_r3_m2
Workspace directory: e:\NarrAI

Mandatory reading: Read e:\NarrAI\.agents\ORIGINAL_REQUEST.md (specifically the latest request under ## 2026-09-22T04:35:39Z).
Technical specification: Read e:\NarrAI\.agents\explorer_survey_r3_2\handoff.md and e:\NarrAI\.agents\PROJECT.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write Ownership (You exclusively own and will modify these files):
- backend/services/cache_service.py
- backend/agents/copilot_agent.py
- backend/main.py (cache integration, session/draft caching, copilot event handling, /api/health)
- backend/tests/test_cache_service.py
- backend/tests/test_copilot_bilingual_resilience.py

Your Objectives (Milestone 2: R3 Redis Cache with Fallback & R4 Resilient AI Co-pilot):
1. Build `backend/services/cache_service.py` (Requirement R3):
   - `ThreadSafeMemoryCache`:
     * Backed by `collections.OrderedDict` + `threading.RLock()`.
     * Per-key TTL (timestamp) + LRU capacity eviction (default max_items=2000).
     * Methods: `get(key)`, `set(key, val, ttl)`, `delete(key)`, `exists(key)`, `clear()`.
     * Sub-millisecond latency (< 0.1ms).
   - `RedisCache`:
     * Conditional import `try: import redis except ImportError: redis = None`.
     * Connection pooling with short timeouts (`socket_timeout=1.0`, `socket_connect_timeout=1.0`).
     * Circuit-breaker: catches `redis.RedisError` and gracefully falls back to `ThreadSafeMemoryCache`.
   - `CacheManager` (Façade):
     * Detects Redis on initialization; if offline/absent, seamlessly activates `ThreadSafeMemoryCache`.
     * Domain methods:
       - `get_session(session_id: str) -> Optional[dict]` & `set_session(session_id: str, memory_dict: dict, ttl: int = 86400)`
       - `get_draft(story_id: int) -> Optional[dict]` & `set_draft(story_id: int, story_dict: dict, ttl: int = 3600)` & `delete_draft(story_id: int)`
       - `get_user_token(token: str) -> Optional[dict]` & `set_user_token(token: str, user_dict: dict, ttl: int = 1800)`
     * Expose `benchmark_latency(iterations: int = 100) -> dict` returning `avg_latency_ms < 20.0`.
     * Expose `get_stats() -> dict` with `mode` ("redis" or "in_memory"), item count, latency.
     * Singleton factory `get_cache_manager()`.

2. Integrate `CacheManager` in `backend/main.py` (Requirement R3):
   - Replace unbounded `USER_CACHE = {}` with `cache_manager.get_user_token` and `cache_manager.set_user_token`.
   - In `get_story_session(session_id, current_user)`: check `cache_manager.get_session(session_id)`. If present, deserialize via `StoryMemory.from_dict()`. If absent, load from DB and cache.
   - In `/api/stories/{story_id}`: check `cache_manager.get_draft(story_id)`. If present, return cached draft in < 1ms. If absent, load and cache.
   - On draft update endpoints (`/api/copilot-event`, `/api/generate-chapter`, `/api/edit-text`): update/invalidate draft and session cache.
   - In `/api/health`: report cache status and latency.

3. Upgrade `backend/agents/copilot_agent.py` (Requirement R4):
   - Bilingual Intent Recognition in `_is_direct_edit_request(user_msg)`:
     * Add English quick prompt strings from frontend: `"Write a completely different opening for this story"`, `"Make the ending much more dramatic and suspenseful"`, `"Rewrite in a darker, more gripping thriller tone"`, `"Add deeper internal thoughts and character dialogues"`.
     * Add English action verbs: `rewrite`, `re-write`, `revise`, `edit`, `redraft`, `rephrase`, `modify`, `change`, `update`, `shorten`, `expand`.
     * Add English target nouns: `opening`, `intro`, `ending`, `outro`, `conclusion`, `tone`, `style`, `dialogue`, `pacing`, `chapter`, `manuscript`, `prose`, `cliffhanger`.
     * Add English tone descriptors: `darker`, `thriller`, `gripping`, `suspense`, `dramatic`, `humorous`.
     * Exclude conversational phrases: `instead of`, `rather than`, `what if`.
   - Token Budgeting & Sliding Window in `_perform_direct_manuscript_edit`:
     * Enforce maximum 8,000 characters context window (`MAX_MANUSCRIPT_CHARS = 8000`), leaving at least 4,000 tokens for Groq completion.
     * Apply section-targeted windowing (head for opening, tail for ending, active window for tone).
   - Payload Deduplication in Step 2 (`process_event`):
     * Strip duplicated `current_story` from `event_data` before serializing into `messages[1]`. `system_prompt` already has `short_context` (3,000 chars).
   - Multi-Tier Model Fallback:
     * Model chain: `["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]`.
     * Retries secondary model if primary fails with rate limit, timeout, or context error.
     * Robust unwrapping: use regex `unwrap_story_prose` and prose extraction if JSON parsing encounters truncation.
     * User-aware polite fallback if all models fail.

4. Testing & Verification:
   - Create `backend/tests/test_cache_service.py`:
     * Test `ThreadSafeMemoryCache`: get, set, TTL expiry, LRU eviction, concurrency.
     * Test `RedisCache` graceful degradation when Redis is offline.
     * Test `benchmark_latency()` confirms latency < 20ms (typically < 0.1ms).
     * Test `StoryMemory` serialization roundtrip through cache.
   - Create `backend/tests/test_copilot_bilingual_resilience.py`:
     * Test all 4 English quick commands trigger `_is_direct_edit_request == True`.
     * Test "Rewrite in a darker, more gripping thriller tone" triggers direct edit.
     * Test manuscript windowing on > 15,000 char story.
     * Test model fallback behavior.
   - Run `python -m unittest backend/tests/test_cache_service.py`.
   - Run `python -m unittest backend/tests/test_copilot_bilingual_resilience.py`.
   - Run `python -m py_compile backend/services/cache_service.py backend/agents/copilot_agent.py backend/main.py`.

Write handoff report to `e:\NarrAI\.agents\worker_r3_m2\handoff.md` and send completion message.
