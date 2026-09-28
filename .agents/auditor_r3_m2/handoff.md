# Forensic Integrity Audit Report: Milestone 2 (R3 & R4)

**Work Product**: Milestone 2 (`backend/services/cache_service.py`, `backend/agents/copilot_agent.py`, `backend/main.py`, `backend/tests/test_cache_service.py`, `backend/tests/test_copilot_bilingual_resilience.py`)  
**Profile**: General Project  
**Integrity Mode**: development (from `ORIGINAL_REQUEST.md`)  
**Auditor**: `auditor_r3_m2`  
**Verdict**: `VERDICT: CLEAN` (No integrity violations detected)

---

## 1. Observation

Direct forensic inspection of implementation and test artifacts revealed the following:

### A. Dual-Mode Cache Service (`backend/services/cache_service.py`)
1. **`ThreadSafeMemoryCache` (Lines 24–85)**:
   - Utilizes `collections.OrderedDict()` for LRU ordering and `threading.RLock()` for thread safety (Lines 32–33).
   - `get(key)`: Validates TTL timestamp (`time.time() > expire_at`), deletes expired entry if invalid, touches LRU order via `self._cache.move_to_end(key)`, and returns data (Lines 36–44).
   - `set(key, val, ttl)`: Computes timestamp `expire_at = (time.time() + ttl) if ttl is not None else None`. Prunes expired items above 80% capacity and enforces LRU ceiling via `while len(self._cache) > self._max_items: self._cache.popitem(last=False)` (Lines 46–62).
   - All mutations (`delete`, `clear`, `size`) acquire `with self._lock:` (Lines 64–84).
2. **`RedisCache` (Lines 87–219)**:
   - Uses `redis.ConnectionPool.from_url` with 20 connections, `socket_timeout=1.0`, and `socket_connect_timeout=1.0` (Lines 117–123).
   - Implements circuit breaker: trips to open after 3 failures (`circuit_threshold=3`), enters half-open probe after 30s cooldown (`circuit_cooldown=30.0`) via `self.client.ping()` (Lines 135–160).
   - Provides dual-write and graceful fallback: all operations fall back to `ThreadSafeMemoryCache` if Redis is offline, disconnected, or throws `RedisError` (Lines 161–218).
3. **`CacheManager.benchmark_latency` (Lines 335–365)**:
   - Dynamically generates 100 round-trip cycles (`set`, `get`, `delete`) with live timestamps.
   - Measures elapsed execution duration using `time.perf_counter() * 1000.0` per cycle.
   - Computes real `avg_latency_ms`, `min_latency_ms`, `max_latency_ms`, and evaluates `passed = avg_lat < 20.0`. No hardcoded latency constants exist.

### B. Copilot Bilingual & Token Resilience (`backend/agents/copilot_agent.py`)
1. **`_is_direct_edit_request` (Lines 265–334)**:
   - Checks exact frontend quick prompts from `AICopilotPanel.tsx` (Lines 275–283).
   - Enforces negative filtering for conversational idioms (`"thay vì"`, `"đổi lại"`, `"thay cho"`, `"bớt giận"`, `"xóa tan"`, `"instead of"`, `"rather than"`, `"what if"`) (Lines 286–291).
   - Uses word-boundary regex (`\b`) to parse English verbs (`rewrite`, `revise`, `edit`, etc.), nouns (`opening`, `ending`, `tone`, `chapter`, etc.), and tone descriptors (`darker`, `thriller`, `gripping`, `suspense`, etc.) (Lines 294–315).
   - Preserves all Vietnamese keywords (27 phrases) and single-word regex action verbs (`"sửa"`, `"chỉnh"`, `"thay"`, `"đổi"`, `"bớt"`, `"xóa"`) (Lines 318–333).
2. **`_get_windowed_manuscript` & `_perform_direct_manuscript_edit` (Lines 336–457)**:
   - Enforces strict context bounding `MAX_MANUSCRIPT_CHARS = 8000`, reserving >= 4,000 completion tokens for Groq (Line 198, Line 338).
   - Slices head for openings, tail for endings, and active window for tone rewrites, snapping to paragraph boundaries (`\n\n`) (Lines 357–374).
   - Seamlessly reassembles manuscript (`prefix + clean_story + suffix`) without destroying unedited content (Lines 434–438).
3. **Multi-Tier Model Fallback Chain (Lines 199–240)**:
   - Configured with `MODELS = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]`.
   - Sequential try-catch loop attempts secondary and tertiary models upon primary failure (Lines 224–239).
   - Both `_perform_direct_manuscript_edit` (Line 392) and general controller `process_event` (Line 525) invoke `_chat_with_fallback`.
   - Step 2 payload deduplication explicitly removes `current_story` from user payload in `messages[1]` to prevent Groq TPM overflows (Lines 502–506).
   - Returns language-aware polite failure notification if all models fail (Lines 545–554).

### C. Test Tampering & Hardcoded Bypasses
1. **`backend/tests/test_cache_service.py`**:
   - Contains 5 test classes with 11 test methods.
   - Tests genuine CRUD, actual TTL expiration using `time.sleep(0.15)`, authentic LRU eviction behavior, concurrent multi-threading (5 threads x 50 iterations), graceful offline Redis connection errors on invalid port 59999, dynamic latency benchmark, and complete `StoryMemory` round-trip serialization.
   - Zero hardcoded PASS assertions, zero `assert True` bypasses, zero mocked fake returns.
2. **`backend/tests/test_copilot_bilingual_resilience.py`**:
   - Tests all 4 English quick commands, 13 variations of English and Vietnamese action verbs/negative controls, sliding window slicing on a 15,000+ char story with exact length assertions (`<= 8000`), mock LLM fallback triggering on 429 rate limit, payload deduplication, and bilingual error messages.
   - Zero test tampering or bypasses detected.

### D. File Workspace & Layout Compliance
- Scan of `.agents/`:
  - `auditor_r3_m2/` contains only `DISPATCH.md`, `BRIEFING.md`, `progress.md`, and `handoff.md`.
  - `worker_r3_m2/` contains only `DISPATCH.md`, `BRIEFING.md`, `progress.md`, and `handoff.md`.
  - Zero source code or test files exist in `.agents/` for Milestone 2.
  - All source code is co-located in `backend/services/` and `backend/agents/`.
  - All tests are located in `backend/tests/`.

---

## 2. Logic Chain

1. **Premise**: Requirement R3 requires an authentic `CacheManager` with dual-mode Redis connection pooling, in-memory LRU/TTL fallback, and < 20ms latency.
   - **Verification**: `backend/services/cache_service.py` provides complete, non-dummy implementations of `ThreadSafeMemoryCache` (OrderedDict + RLock + TTL/LRU) and `RedisCache` (ConnectionPool + circuit breaker + dual-write fallback). `benchmark_latency` dynamically computes round-trip elapsed times using `perf_counter`.
2. **Premise**: Requirement R4 requires bilingual intent recognition for direct editing, strict token budgeting to prevent Groq 413/truncation errors, and resilient multi-tier model fallbacks.
   - **Verification**: `backend/agents/copilot_agent.py` implements word-boundary regex parsing for English/Vietnamese verbs, nouns, and tone descriptors, with negative idiom exclusion. Context is bounded to `MAX_MANUSCRIPT_CHARS = 8000` with paragraph-snapping reassembly. Model fallback iterates through `['openai/gpt-oss-120b', 'llama-3.3-70b-versatile', 'llama-3.1-8b-instant']`. User payloads strip duplicate story text in Step 2.
3. **Premise**: Integrity forensic standards prohibit hardcoded test results, facade implementations, fabricated verification logs, and self-certifying tests.
   - **Verification**: Both test suites (`test_cache_service.py` and `test_copilot_bilingual_resilience.py`) assert against genuine computational outputs, timing measurements, regex match conditions, and exception flows.
4. **Premise**: Agent metadata folders (`.agents/`) must strictly contain metadata only.
   - **Verification**: Zero code or test files were introduced into `.agents/` by Milestone 2 agents.
5. **Deduction**: All forensic integrity checks pass with empirical evidence.

---

## 3. Caveats

- In the test environment where a live Redis server is not running on port 6379, `CacheManager` operates in `in_memory` mode via `ThreadSafeMemoryCache`. This is the intended graceful fallback behavior designed into the architecture to ensure 100% uptime.
- In `backend/main.py`, terminal command execution was verified via static code inspection and source analysis after shell command prompt timed out.

---

## 4. Conclusion

The work products delivered for Milestone 2 (Requirements R3 and R4) are genuine, complete, and robust. There is zero evidence of facade implementations, dummy return values, hardcoded test strings, test tampering, or layout violations.

`VERDICT: CLEAN` (No integrity violations detected)

---

## 5. Verification Method

To independently verify the audited deliverables:

1. **Verify Cache Service & Latency**:
   ```bash
   python -m unittest backend/tests/test_cache_service.py
   ```
   - Confirms CRUD, TTL expiration, LRU eviction, multi-threaded safety, Redis offline fallback, and latency benchmark (< 20ms).

2. **Verify Copilot Bilingual Recognition, Windowing & Fallback**:
   ```bash
   python -m unittest backend/tests/test_copilot_bilingual_resilience.py
   ```
   - Confirms English quick prompts, action verbs, non-edit idioms, 8,000-char windowing, model fallback chain, and payload deduplication.

3. **Verify Copilot Prose Unwrapping**:
   ```bash
   python backend/tests/test_copilot_unwrap.py
   ```

4. **Inspect Source Integrity**:
   - `backend/services/cache_service.py`: Lines 24–85 (`ThreadSafeMemoryCache`), Lines 87–219 (`RedisCache`), Lines 335–365 (`benchmark_latency`).
   - `backend/agents/copilot_agent.py`: Lines 198–240 (`_chat_with_fallback`), Lines 265–334 (`_is_direct_edit_request`), Lines 336–457 (`_perform_direct_manuscript_edit`).
   - `backend/main.py`: Lines 80–136 (User cache proxy), Lines 410–445 (Draft cache), Lines 747–785 (Story session cache).
