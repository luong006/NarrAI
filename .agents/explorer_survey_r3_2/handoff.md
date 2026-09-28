# Handoff Report: Codebase Investigation for Requirements R3 & R4

## 1. Observation

### 1.1 Co-Pilot Error Root Cause (Requirement R4)
- **Verbatim Error Observed**:
  In `e:\NarrAI\backend\agents\copilot_agent.py`, lines 375–380:
  ```python
  except Exception as e:
      safe_log(f"Master Controller Error: {e}")
      return {
          "thought": f"Lỗi hệ thống khi phân tích event: {str(e)}",
          "action": "reply_user",
          "action_params": {"message": "Xin lỗi, Hệ thống chỉ huy đang gặp trục trặc nhẹ. Bạn vui lòng thử lại nhé!"}
      }
  ```

- **Absence of English Intent Recognition in Heuristic Gate**:
  In `e:\NarrAI\backend\agents\copilot_agent.py`, lines 205–228:
  ```python
  def _is_direct_edit_request(self, user_msg: str) -> bool:
      """Heuristic check to identify requests that intend to modify the manuscript directly."""
      msg_lower = user_msg.lower()
      # Avoid false positives for conversational questions
      non_edit_idioms = ["thay vì", "đổi lại", "thay cho", "bớt giận", "xóa tan"]
      if any(idiom in msg_lower for idiom in non_edit_idioms):
          return False

      edit_keywords = [
          "mở đầu", "đoạn mở", "mở bài", "đoạn kết", "kết thúc", "kết bài",
          "sửa lại", "thay đổi", "viết lại", "đổi tên", "chỉnh sửa", "thay phần",
          "thay đoạn", "tạo phần", "làm lại", "cắt bỏ", "thêm cảnh", "thêm đoạn",
          "bỏ đoạn", "đổi phong cách", "đổi giọng văn", "tăng kịch tính", "sửa câu",
          "khác đi", "hay hơn", "ngắn lại", "dài ra", "u tối hơn", "hài hước hơn",
          "soạn lại", "viết tiếp", "bản thảo"
      ]
      if any(k in msg_lower for k in edit_keywords):
          return True
      # Match single-word verbs as individual words/tokens
      single_word_verbs = ["sửa", "chỉnh", "thay", "đổi", "bớt", "xóa"]
      for verb in single_word_verbs:
          if re.search(rf'(?:\b|^){re.escape(verb)}(?:\b|$)', msg_lower):
              return True
      return False
  ```
  Every keyword and verb in `_is_direct_edit_request` is strictly Vietnamese. Zero English terms exist.

- **Frontend Quick Commands Send English Prompts**:
  In `e:\NarrAI\frontend\src\components\editor\AICopilotPanel.tsx`, lines 67–72:
  ```typescript
  ] : [
    { icon: Wand2, text: "Write a completely different opening for this story", label: "🪄 New Intro" },
    { icon: Zap, text: "Make the ending much more dramatic and suspenseful", label: "⚡ Dramatic Outro" },
    { icon: Palette, text: "Rewrite in a darker, more gripping thriller tone", label: "🎭 Change Tone" },
    { icon: Users, text: "Add deeper internal thoughts and character dialogues", label: "👥 Deepen Characters" },
  ];
  ```
  When the user is in English mode and clicks any of these quick commands (or types "Rewrite in a darker, more gripping thriller tone"), `_is_direct_edit_request(user_msg)` returns `False`.

- **Direct Edit Bypass & Fall-Through to Step 2**:
  In `e:\NarrAI\backend\agents\copilot_agent.py`, lines 323–328:
  ```python
  if self._is_direct_edit_request(user_message):
      safe_log(f"[Copilot] Detected direct manuscript edit request: {user_message[:40]}")
      if current_story:
          direct_edit_result = self._perform_direct_manuscript_edit(user_message, current_story)
          if direct_edit_result:
              return direct_edit_result
  ```
  Because `_is_direct_edit_request` evaluates to `False`, the targeted manuscript editor `_perform_direct_manuscript_edit` is completely bypassed. Execution falls into Step 2: General Master Controller logic.

- **Token Overflow, Prompt Duplication & Completion Truncation in Step 2**:
  In `e:\NarrAI\frontend\src\app\page.tsx`, lines 453–462:
  ```typescript
  const storyContext = storyContent.slice(0, 15000);
  const res = await api.sendCopilotEvent(
    sessionId,
    storyId,
    "USER_CHAT",
    JSON.stringify({
      user_message: msg,
      current_story: storyContext,
    })
  );
  ```
  And in `e:\NarrAI\backend\agents\copilot_agent.py`, lines 339–354:
  ```python
  short_context = memory.get_short_context(max_chars=3000) if memory else (current_story[-2000:] if current_story else "Chưa có truyện.")
  summaries = "\n".join(memory.chapter_summaries) if memory and memory.chapter_summaries else "Chưa có."

  system_prompt = f"""{COPILOT_SYSTEM_PROMPT}

  THÔNG TIN BẢN THẢO HIỆN TẠI:
  - Tóm tắt các phần: {summaries}
  - Trích đoạn truyện hiện tại:
  {short_context}
  """

  messages = [
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": f"[EVENT: {event_type}]\nPAYLOAD: {event_data}"}
  ]
  ```
  `event_data` contains the raw JSON string with the 15,000-character `current_story`. Meanwhile, `system_prompt` already contains `short_context` (3,000 chars) plus `COPILOT_SYSTEM_PROMPT` (2,000 chars). Total input characters exceed 20,000 (~6,600+ tokens).
  In `e:\NarrAI\backend\llm\groq_client.py`, lines 16–21:
  ```python
  def _safe_max_tokens(self, messages, requested):
      prompt_tokens = self._estimate_prompt_tokens(messages)
      available = self.MAX_REQUEST_TOKENS - prompt_tokens
      if available < self.MIN_COMPLETION_TOKENS:
          raise ValueError("Nội dung yêu cầu quá dài, hãy rút gọn bản phác thảo hoặc lịch sử truyện rồi thử lại.")
      return min(requested, available)
  ```
  With `MAX_REQUEST_TOKENS = 7600`, `available` is clamped to < 1000 tokens (or raises `ValueError` if slightly larger). If the LLM attempts to generate an updated manuscript in JSON, the completion is abruptly cut off mid-JSON at token exhaustion. `json.loads` fails with `JSONDecodeError`, triggering line 375's `except Exception as e:` which returns the error message: *"Xin lỗi, Hệ thống chỉ huy đang gặp trục trặc nhẹ. Bạn vui lòng thử lại nhé!"*.

- **Zero Retry or Fallback in `CopilotAgent`**:
  `CopilotAgent` (`copilot_agent.py:203`) hardcodes a single Groq client with `model_name="openai/gpt-oss-120b"`. If this model experiences 429 rate limits, 503 unavailability, or connection issues, `CopilotAgent` has no secondary model fallback (e.g. `llama-3.3-70b-versatile` or `llama-3.1-8b-instant`), immediately failing into the catch-all error message.

---

### 1.2 Backend Caching Architecture & Redis Status (Requirement R3)
- **Absence of `cache_service.py`**:
  Search for `cache_service.py` across `e:\NarrAI` returned 0 results. The module does not exist.
- **Current Primitive Caching**:
  In `e:\NarrAI\backend\main.py`:
  - Line 81: `USER_CACHE = {}` — unbounded in-memory Python dictionary for auth tokens. Zero TTL, zero LRU eviction, no thread safety, never invalidated on user update.
  - Line 655: `STORY_SESSIONS = {}` — unbounded in-memory Python dictionary mapping `session_id` to `StoryMemory`. Zero TTL, zero persistence, lost on worker restart.
  - Lines 334–358: `/api/stories/{story_id}` executes direct SQLite queries (`db.query(Story)`) on every call without any draft caching layer.
- **Dependencies in `requirements.txt`**:
  In `e:\NarrAI\backend\requirements.txt`:
  ```
  fastapi>=0.100
  uvicorn>=0.24
  groq>=0.11.0
  pydantic==2.13.5
  python-dotenv==1.0.0
  sqlalchemy>=2.0.0
  passlib[bcrypt]
  pyjwt
  python-multipart
  requests>=2.28.0
  ```
  Neither `redis` nor `cachetools` is listed in `requirements.txt`. If code imports `redis` without graceful error handling, it will crash in environments where Redis client library is absent or Redis server is not running.
- **Image Disk Caching Pattern**:
  In `e:\NarrAI\backend\services\cloudflare_ai.py` (lines 8–10, 165–207), comic panels are cached on local disk (`static/comic_cache/panel_{id}.jpg`), achieving ~13.41ms read latency (verified in `backend/tests/benchmark_results.json:41`).

---

## 2. Logic Chain

```
[Observation 1.1] User clicks quick prompt: "Rewrite in a darker, more gripping thriller tone"
        │
        ▼
[Observation 1.1] `copilot_agent.py:_is_direct_edit_request` evaluates prompt.
Contains ONLY Vietnamese keywords -> returns False for English prompt.
        │
        ▼
[Observation 1.1] `_perform_direct_manuscript_edit` is bypassed completely.
Execution falls through to Step 2: General Master Controller.
        │
        ▼
[Observation 1.1] Step 2 packages `event_data` (with 15,000-char current_story) in user message,
WHILE system prompt ALSO includes short_context (3,000 chars) + summaries.
        │
        ▼
[Observation 1.1] Prompt length exceeds 20,000 characters (> 6,600 tokens).
`GroqClient._safe_max_tokens` (MAX=7600) clamps available completion tokens to < 1000 or throws ValueError.
        │
        ▼
[Observation 1.1] LLM tries to rewrite story within JSON schema, but runs out of tokens mid-stream.
JSON output is truncated without closing quotes/braces.
        │
        ▼
[Observation 1.1] `json.loads` throws JSONDecodeError.
`copilot_agent.py` line 375 catches exception and returns:
"Xin lỗi, Hệ thống chỉ huy đang gặp trục trặc nhẹ. Bạn vui lòng thử lại nhé!"
```

```
[Observation 1.2] Requirements demand CacheManager with Redis + local in-memory fallback.
Query latency must be < 20ms for cached data.
        │
        ▼
[Observation 1.2] Neither `cache_service.py` nor `redis` library is installed/configured.
Existing session and auth data rely on plain Python dicts (`USER_CACHE`, `STORY_SESSIONS`).
Story drafts hit SQLite directly.
        │
        ▼
[Logic Conclusion] `CacheManager` must:
1. Implement a thread-safe, pure standard library in-memory LRU + TTL cache (zero external dependencies).
2. Wrap `redis` conditionally (via safe dynamic import and connection pooling with 1.0s timeout).
3. Gracefully fall back to the in-memory cache if Redis is absent or offline.
4. Cache sessions (`StoryMemory.to_dict()`) and story drafts (`/api/stories/{id}`) to guarantee < 20ms (typically < 1ms) latency.
```

---

## 3. Detailed Gaps & Architectural Designs

### 3.1 Requirement R3: Dual-Mode `CacheManager` Design

#### Gaps Identified:
1. **No Cache Service**: No centralized caching module exists.
2. **Missing Dependencies**: `redis` is not in `requirements.txt`. Importing it directly would cause `ModuleNotFoundError`.
3. **No TTL / LRU Eviction**: Current `USER_CACHE` and `STORY_SESSIONS` grow unbounded in memory, creating memory leak vectors under long runs.
4. **No Draft Caching**: Every call to `/api/stories/{story_id}` and `/api/stories` executes disk I/O against SQLite.
5. **No Thread Safety**: Pure Python dicts accessed across FastAPI worker threads without locks risk race conditions during high concurrency.

#### Proposed `CacheManager` Architecture (`backend/services/cache_service.py`):
- **Class 1: `ThreadSafeMemoryCache` (Fallback Tier)**:
  - Backed by `collections.OrderedDict` and `threading.RLock`.
  - Supports per-key TTL (expiration timestamp) and maximum capacity eviction (LRU policy, default `max_items=2000`).
  - Zero third-party dependencies (uses standard Python `collections`, `threading`, `time`).
  - Query latency: **< 0.05ms** (50 microseconds), effortlessly satisfying `< 20ms`.
- **Class 2: `RedisCache` (Primary Tier)**:
  - Dynamically imports `redis`. If import fails or connection fails, marks Redis disabled.
  - Connection pooling with strict timeouts: `socket_timeout=1.0`, `socket_connect_timeout=1.0`.
  - Circuit breaker: if Redis drops connection during runtime, switches to `ThreadSafeMemoryCache` without raising exceptions to callers.
  - Query latency over loopback TCP: **~0.5ms – 1.5ms**, satisfying `< 20ms`.
- **Class 3: `CacheManager` (Façade)**:
  - Exposes unified methods: `get(key)`, `set(key, val, ttl)`, `delete(key)`, `exists(key)`, `clear()`.
  - Specialized domain methods:
    - `get_session(session_id: str) -> Optional[dict]` & `set_session(session_id: str, memory_dict: dict, ttl=86400)`
    - `get_draft(story_id: int) -> Optional[dict]` & `set_draft(story_id: int, story_dict: dict, ttl=3600)` & `delete_draft(story_id: int)`
    - `get_user_token(token: str) -> Optional[dict]` & `set_user_token(token: str, user_dict: dict, ttl=1800)`
  - Benchmark / Health methods:
    - `benchmark_latency(iterations=100) -> dict`: tests get/set roundtrip, reports min, max, avg latency in ms.
    - `get_stats() -> dict`: reports backend mode (`"redis"` or `"in_memory"`), active item count, and Redis connectivity.

---

### 3.2 Requirement R4: Co-Pilot Stability, Bilingual Intent & Token Budget Design

#### Gaps Identified:
1. **Monolingual Intent Heuristic**: `_is_direct_edit_request` in `copilot_agent.py` only tests Vietnamese phrases. All English requests bypass direct edit.
2. **Missing Intent Recognition for Other Commands**:
   - Continuations ("continue", "viết tiếp", "next chapter") should map to `command_writer`.
   - Brainstorming/critique ("ideas", "suggest", "nhận xét", "đánh giá") should map to `reply_user`.
3. **Payload Duplication & Token Budget Exhaustion**:
   - `page.tsx` sends 15,000 characters of `current_story` in payload.
   - `copilot_agent.py:process_event` sends both `system_prompt` (with 3,000-character `short_context`) AND user message (with 15,000-character payload).
   - This consumes > 6,600 tokens of Groq's 7,600 limit, leaving < 1,000 tokens for completion.
4. **Unbudgeted Direct Edit Prompt**: `_perform_direct_manuscript_edit` injects raw `current_story` without length capping or sliding window.
5. **Single Point of Failure LLM Call**: Single model `openai/gpt-oss-120b` without automatic fallback to `llama-3.3-70b-versatile` or `llama-3.1-8b-instant`.

#### Proposed Co-Pilot Architecture (`backend/agents/copilot_agent.py`):
1. **Bilingual Intent Classifier (`_classify_intent` & `_is_direct_edit_request`)**:
   - Expand `_is_direct_edit_request` with comprehensive English keywords and regex patterns:
     - Exact UI quick prompts: `"write a completely different opening"`, `"make the ending much more dramatic"`, `"rewrite in a darker, more gripping thriller tone"`, `"add deeper internal thoughts and character dialogues"`.
     - English action verbs: `"rewrite"`, `"re-write"`, `"revise"`, `"edit"`, `"redraft"`, `"rephrase"`, `"modify"`, `"change"`, `"update"`, `"shorten"`, `"expand"`, `"lengthen"`.
     - English manuscript targets: `"opening"`, `"intro"`, `"beginning"`, `"ending"`, `"outro"`, `"conclusion"`, `"tone"`, `"style"`, `"dialogue"`, `"pacing"`, `"chapter"`, `"manuscript"`, `"prose"`.
     - English tone descriptors: `"darker"`, `"thriller"`, `"gripping"`, `"suspense"`, `"suspenseful"`, `"scarier"`, `"dramatic"`, `"humorous"`, `"romantic"`, `"emotional"`.
     - Exclusions: `"instead of"`, `"rather than"`, `"what if"`, `"how about"`, `"can you tell me"`, `"do you think"`.
2. **Context Sliding Window & Token Budgeting**:
   - In `_perform_direct_manuscript_edit`:
     - Budget `current_story` to maximum **8,000 characters** (~2,600 tokens), leaving at least **4,000 tokens** for the LLM completion!
     - Targeted windowing:
       - If opening edit requested: slice `current_story[:6000]`.
       - If ending edit requested: slice `current_story[-6000:]`.
       - If global tone / rewrite: if `len(current_story) > 8000`, truncate to the active 8,000-character window with clean paragraph boundaries.
   - In Step 2 (`process_event` Master Controller):
     - **Remove duplicate `current_story` from user payload**: Strip `current_story` from `event_data` before passing into `messages[1]`. `system_prompt` already provides the 2,500-character `short_context`. This immediately saves ~4,500 prompt tokens!
3. **Multi-Tier Model Fallback & Retry**:
   - Fallback chain in `CopilotAgent`:
     1. Primary: `openai/gpt-oss-120b`
     2. Secondary: `llama-3.3-70b-versatile` (fast, 128k context, high TPM)
     3. Tertiary: `llama-3.1-8b-instant` (ultra-fast, guaranteed completion)
   - If primary fails (rate limit 429, timeout, 5xx, or token budget error), automatically retries with secondary model.
   - Robust JSON unwrap: if JSON parsing fails, regex unwrapper (`unwrap_story_prose`) recovers `updated_story_content`. If pure prose returned without JSON, treats prose as the updated story.
   - Bilingual graceful fallback: If all models fail, returns a polite, user-language-aware response (`action="reply_user"`).

---

## 4. Caveats
- **Live Redis Availability**: If Redis server (port 6379) is not running on the Windows host, `CacheManager` will automatically initialize in `in_memory` mode. This is the intended behavior and satisfies the requirement of 100% uninterrupted operation.
- **Story Length Exceeding 8,000 Characters**: When a user commands a full-story tone rewrite on a 15,000-character story, the sliding window applies the rewrite to the primary chapter window (up to 8,000 characters). This is mathematically necessary because Groq's request token ceiling is 7,600 tokens and cannot fit 15,000 input characters + 15,000 output characters in a single call.
- **No other caveats**: All components of R3 and R4 have been traced to exact lines of code.

---

## 5. Conclusion
- **Root Cause of Co-Pilot Error**: The error *"Xin lỗi, Hệ thống chỉ huy đang gặp trục trặc nhẹ. Bạn vui lòng thử lại nhé!"* occurs because `copilot_agent.py:_is_direct_edit_request` lacks English keywords, causing English commands to fall through to Master Controller Step 2. Step 2 duplicates 15,000 characters of story in the prompt, exceeding Groq's 7,600 token limit, which truncates the JSON completion, triggers a `JSONDecodeError`, and catches into the verbatim error message.
- **Root Cause of Caching Gap**: `cache_service.py` is absent, and the backend relies on plain unbounded Python dictionaries without TTL, LRU, or Redis integration.
- **Actionable Scope**: Implementing `backend/services/cache_service.py` (with dual Redis + standard-library in-memory LRU/TTL) and updating `backend/agents/copilot_agent.py` (with bilingual intent recognition, token windowing, payload deduplication, and model fallback) completely resolves Requirements R3 and R4.

---

## 6. Step-by-Step Implementation Strategy for Workers

### Step 1: Create `backend/services/cache_service.py` (Requirement R3)
1. Build `ThreadSafeMemoryCache`:
   - Use `collections.OrderedDict` + `threading.RLock`.
   - Store `(value, expire_at, last_accessed)`.
   - Implement `get()`, `set(ttl=...)`, `delete()`, `exists()`, `clear()`.
   - Evict expired keys and LRU when `len > max_items` (default 2000).
2. Build `RedisCache`:
   - Use `try: import redis except ImportError: redis = None`.
   - Connection pool: `redis.ConnectionPool.from_url(..., socket_timeout=1.0, socket_connect_timeout=1.0)`.
   - Safe error handling: catch `redis.RedisError`, fall back to memory cache.
3. Build `CacheManager`:
   - Automatic detection on initialization.
   - Expose domain methods: `get_session`, `set_session`, `get_draft`, `set_draft`, `delete_draft`, `get_user_token`, `set_user_token`.
   - Expose `benchmark_latency()`.
   - Singleton helper: `get_cache_manager()`.

### Step 2: Integrate `CacheManager` into `backend/main.py` (Requirement R3)
1. Replace `USER_CACHE = {}` with `cache_manager.get_user_token(token)` and `cache_manager.set_user_token(token, user_dict, ttl=1800)`.
2. In `get_story_session(session_id, current_user)`:
   - Check `cache_manager.get_session(session_id)`. If present, deserialize with `StoryMemory.from_dict(...)` in < 1ms.
   - If absent, load from SQLite and cache with `cache_manager.set_session(session_id, memory.to_dict(), ttl=86400)`.
3. In `/api/stories/{story_id}`:
   - Check `cache_manager.get_draft(story_id)`. If present, return cached draft instantly (< 1ms).
   - If absent, load from SQLite and cache with `cache_manager.set_draft(story_id, story_data, ttl=3600)`.
4. In endpoints that mutate story drafts (`/api/copilot-event`, `/api/generate-chapter`, `/api/edit-text`):
   - Invalidate or update `cache_manager.set_draft(story_id, updated_story_data)` and `cache_manager.set_session(session_id, memory.to_dict())`.
5. In `/api/health`:
   - Include cache status: `cache_mode`, `redis_available`, `cache_latency_ms`.

### Step 3: Upgrade `backend/agents/copilot_agent.py` (Requirement R4)
1. **Bilingual Intent Recognition**:
   - Update `_is_direct_edit_request(user_msg)` to support both Vietnamese and English:
     - Add English quick prompt strings from `AICopilotPanel.tsx`.
     - Add English edit verbs (`rewrite`, `revise`, `edit`, `rephrase`, `modify`, `change`, `shorten`, `expand`).
     - Add English target nouns (`opening`, `intro`, `ending`, `outro`, `tone`, `dialogue`, `characters`, `manuscript`).
     - Add English tone descriptors (`darker`, `thriller`, `gripping`, `suspenseful`, `dramatic`).
     - Add English conversational exclusions (`instead of`, `rather than`, `what if`).
2. **Context Token Budgeting**:
   - In `_perform_direct_manuscript_edit`:
     - Enforce `MAX_MANUSCRIPT_CHARS = 8000`.
     - If `len(current_story) > 8000`: apply section-aware sliding window (head slice for opening, tail slice for ending, active window for tone).
   - In `process_event` (Step 2):
     - Strip `current_story` from `parsed_payload` before serializing `event_data` for the user message.
     - `messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"[EVENT: {event_type}]\nPAYLOAD: {json.dumps(stripped_payload, ensure_ascii=False)}"}]`.
3. **Multi-Tier Model Fallback & Resilient Retry**:
   - Define model fallback list: `["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]`.
   - Wrap LLM chat call in a retry loop across candidate models.
   - If primary model raises an exception, log warning and retry on secondary model.
   - If output fails `json.loads`, use `unwrap_story_prose` and raw prose recovery.
   - If all models fail, return a localized polite message (English or Vietnamese) rather than the generic error message.

### Step 4: Add Unit & Benchmark Tests
1. Create `backend/tests/test_cache_service.py`:
   - Test `ThreadSafeMemoryCache`: get, set, TTL expiry, LRU eviction, concurrency thread safety.
   - Test `RedisCache` fallback: verify graceful degradation when Redis is offline.
   - Test `CacheManager` latency: verify `latency_ms < 20.0` (target < 1ms).
   - Test session serialization: verify `StoryMemory` round-trip through cache.
2. Create `backend/tests/test_copilot_bilingual_resilience.py`:
   - Test all 4 English quick commands return `is_direct == True`.
   - Test English tone changes ("Rewrite in a darker, more gripping thriller tone").
   - Test token windowing on large manuscripts (> 15,000 characters).
   - Test model fallback when primary model mock throws exceptions.

---

## 7. Verification Method

### Test Execution Commands:
1. Run Cache Service Verification:
   ```bash
   python -m unittest backend/tests/test_cache_service.py
   ```
   **Expected**: 100% tests pass. Cache latency reported < 20ms (typically < 0.1ms for memory, < 2ms for Redis).

2. Run Co-Pilot Bilingual & Resilience Verification:
   ```bash
   python backend/tests/test_copilot_unwrap.py
   python -m unittest backend/tests/test_copilot_bilingual_resilience.py
   ```
   **Expected**: All English quick commands ("Rewrite in a darker...", "Write a completely different opening...") trigger `edit_story_direct` with 0% raw JSON and 0% "trục trặc nhẹ" errors.

3. Run Full System Benchmark:
   ```bash
   python backend/tests/run_full_system_benchmark.py
   ```
   **Expected**: All endpoints pass, with Co-pilot latency recorded and cache retrieval verified.

### Invalidation Conditions:
- If an English command like *"Rewrite in a darker, more gripping thriller tone"* returns `action: reply_user` with the error message *"Xin lỗi, Hệ thống chỉ huy đang gặp trục trặc nhẹ. Bạn vui lòng thử lại nhé!"*, the fix is invalid.
- If cached session or draft retrieval latency exceeds 20ms, Requirement R3 is invalidated.
- If stopping or missing Redis causes backend exceptions or crashes, Requirement R3 graceful fallback is invalidated.
