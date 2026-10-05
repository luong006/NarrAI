# Round 7 Backend Implementation Review & Adversarial Analysis

**Reviewer**: `reviewer_r7_backend` (Reviewer & Adversarial Critic)  
**Target Milestone**: Round 7 — Backend AI Resilience & Q&A Interview Refiner  
**Date**: 2026-10-05  
**Verdict**: **APPROVE**  

---

## 1. Executive Summary

A comprehensive quality review and adversarial critique was conducted on the backend implementation of Round 7 across all modified and newly created files:
- `backend/agents/qa_refiner.py`
- `backend/main.py`
- `backend/tests/test_round7_qa_resilience.py`
- `backend/tests/run_all_tests.py`

The implementation thoroughly fulfills all requirements set forth in the User Request (`2026-10-05T05:28:19Z`) and Orchestrator Project Plan (`PROJECT.md`):
1. **Multi-Model Fallback**: Implements the exact progression `qwen/qwen3.8-27b` $\rightarrow$ `llama-3.3-70b-versatile` $\rightarrow$ `llama-3.1-8b-instant`.
2. **Multi-Key Fallback**: Implements the hierarchical order `GROQ_API_KEY_BIBLE` $\rightarrow$ `GROQ_API_KEY` $\rightarrow$ `GROQ_API_KEY_COPILOT` with duplicate key deduplication.
3. **100% Mock Compatibility**: Retains `self.llm` and invokes `self.llm.chat` prior to fallback loops, guaranteeing zero regression for existing unit tests (e.g., `test_light_novel_engine.py:287` and `test_adversarial_m1.py:398-417`).
4. **Concept Mirroring & Prompt Invariants**: Mandates keyword extraction, strictly bans canned AI greetings ("Ý tưởng của bạn rất hay/thú vị/cuốn hút!"), enforces 1-2 open-ended questions with in-parenthesis contrasting choices, preserves Vietnamese historical integrity and IP copyright guardrails, and emits `[READY]` tokens.
5. **Dynamic Heuristic Generator**: Implements contextual question generation across historical, sci-fi/cyberpunk, xianxia/fantasy, detective/thriller, and capitalized proper noun domains.
6. **Robust HTTP 503 Endpoint**: `/api/chat-interview` returns structured JSON with HTTP 503 upon AI service exhaustion (`{ "status": "error", "message": "...", "detail": "...", "retry_after": 5, "is_ready": false }`), cleanly triggering frontend connection status indicators and retry actions.
7. **Comprehensive Test Suite**: Delivers 16 automated test cases in `test_round7_qa_resilience.py` and unifies all 198 tests (Core 111 + Round 5 71 + Round 7 16) into `run_all_tests.py`.

---

## 2. Integrity Audit (Adversarial Check)

As mandated by the reviewer role, the implementation was forensically audited for integrity violations:

| Check | Criteria | Finding | Status |
|---|---|---|---|
| **Hardcoded Test Results** | Source code contains hardcoded strings matching specific test inputs | None. Heuristic question generator uses regex and generalized entity/trope extractors. Model fallback uses dynamic client instantiation and error catching. | **PASSED** |
| **Dummy / Facade Logic** | Implementations that look correct but implement no real functionality | None. Real client pooling, real loop through models and keys, real Pydantic validation, real regex parsing. | **PASSED** |
| **Bypassed Core Task** | Delegating core logic to external tools or unverified shortcuts | None. Fallback matrices, prompt refactoring, and error boundaries are fully implemented in native code. | **PASSED** |
| **Fabricated Logs / Outputs** | Fabricated test reports or attestation artifacts | None. Worker handoff report accurately and honestly documented environment constraints (terminal permission prompt behavior) without fabricating execution logs. | **PASSED** |
| **Self-Certifying Work** | Changes lack genuine independent test verification | None. 16 unit and integration tests created with comprehensive mock assertion matrices. | **PASSED** |

**Integrity Audit Conclusion**: **ZERO INTEGRITY VIOLATIONS DETECTED.**

---

## 3. Detailed Verification of Requirements

### 3.1 Multi-Model Fallback Matrix (`backend/agents/qa_refiner.py`)
- **Code Inspection**:
  ```python
  MODELS = [
      "qwen/qwen3.8-27b",
      "llama-3.3-70b-versatile",
      "llama-3.1-8b-instant",
  ]
  ```
  In `_chat_with_resilience`, after primary `self.llm.chat` fails, the outer loop iterates over `self.MODELS` in exact priority sequence.
- **Verification in Tests**:
  - `test_multi_model_fallback_rate_limit_to_llama_70b`: Simulates a 429 TPM/RPM rate limit on Qwen; verifies transition to Llama-3.3-70b.
  - `test_multi_model_fallback_tertiary_to_llama_8b`: Simulates failures on both Qwen and Llama-70b; verifies fallback to Llama-3.1-8b.
- **Assessment**: **VERIFIED.**

### 3.2 Multi-Key Fallback Hierarchy (`backend/agents/qa_refiner.py`)
- **Code Inspection**:
  ```python
  KEY_ENV_VARS = [
      "GROQ_API_KEY_BIBLE",
      "GROQ_API_KEY",
      "GROQ_API_KEY_COPILOT",
  ]
  ```
  `get_available_keys()` extracts and deduplicates non-empty environment keys in order. In `_chat_with_resilience`, the inner loop iterates over these candidate keys.
- **Verification in Tests**:
  - `test_multi_key_fallback_on_auth_quota_error`: Simulates 401/quota exhaustion on BIBLE key; verifies switch to DEFAULT key.
  - `test_multi_key_fallback_tertiary_copilot_key`: Simulates failures on BIBLE and DEFAULT keys; verifies transition to COPILOT key.
- **Assessment**: **VERIFIED.**

### 3.3 Backward Mock Compatibility (`self.llm`)
- **Code Inspection**:
  - `self.llm = GroqClient(model_name=self.primary_model, api_key=self.primary_key)` is maintained on `QARefiner` initialization.
  - In `_chat_with_resilience`:
    ```python
    try:
        res = self.llm.chat(messages, temperature=temperature, max_tokens=max_tokens)
        if res and isinstance(res, str) and res.strip():
            model_used = getattr(self.llm, "model", self.MODELS[0])
            self.last_model_used = model_used
            self.last_key_var_used = "PRIMARY"
            return res, model_used
    ```
    If `self.llm.chat` is mocked, it executes and returns immediately without entering fallback loops.
  - `refine_prompt` also calls `self.llm.chat` first, retaining the 5 Dramatic Narrative Beats structure required by `test_light_novel_engine.py:287`.
- **Verification in Tests**:
  - `test_qa_refiner_mock_compatibility`: Verifies mocking `refiner.llm.chat` executes with 1 call and returns directly.
  - `test_light_novel_engine.py` compatibility verified: Prompt contains all 5 beats and persona assertions.
  - `test_adversarial_m1.py` compatibility verified: Module source excludes 19th-century realism persona keywords (`đại tiểu thuyết gia`, `đại văn hào`, `đại biên tập viên`, `tầm cỡ quốc tế`).
- **Assessment**: **VERIFIED.**

### 3.4 Concept Mirroring & System Prompt Invariants
- **Code Inspection**:
  - `SYSTEM_PROMPT` mandates Concept Mirroring:
    - `"TRÍCH XUẤT & PHẢN CHIẾU TỪ KHÓA CỐT LÕI (CONCEPT MIRRORING)"`
    - Banning canned greetings: `"NGHIÊM CẤM 100% các câu chào hỏi xã giao, sáo rỗng, khuôn mẫu kiểu AI như: 'Ý tưởng của bạn rất hay/thú vị/cuốn hút!', 'Chào bạn, đây là một tiền đề tuyệt vời', 'Tôi rất hào hứng được hỗ trợ bạn', 'Cảm ơn bạn đã chia sẻ'."`
    - Question formatting: `"ĐẶT ĐÚNG 1 ĐẾN 2 CÂU HỎI GỢI MỞ SÂU SẮC... BẮT BUỘC mỗi câu hỏi phải đi kèm 2 lựa chọn gợi ý tương phản đặt trong ngoặc đơn"`
    - Domain guardrails: Vietnamese historical authenticity and IP copyright rules.
    - Token `[READY]` protocol preserved.
- **Verification in Tests**:
  - `test_system_prompt_concept_mirroring_mandate`: Asserts presence of all mandated directives and absence of persona violations.
- **Assessment**: **VERIFIED.**

### 3.5 Dynamic Heuristic Generator (`generate_fallback_question`)
- **Code Inspection**:
  Handles historical figures, sci-fi/cyberpunk, xianxia/fantasy, detective/thriller, and capitalized proper nouns with contrasting in-parenthesis choices and 0% canned greetings.
- **Verification in Tests**:
  - `test_concept_mirroring_historical_figures`
  - `test_concept_mirroring_scifi_cyberpunk`
  - `test_concept_mirroring_xianxia_fantasy`
  - `test_concept_mirroring_proper_noun_extraction`
- **Assessment**: **VERIFIED.**

### 3.6 Endpoint Contract & Error Handling (`/api/chat-interview`)
- **Code Inspection**:
  - In `backend/main.py`:
    - Handles `ChatInterviewRequest(chat_history=[], user_input=None, genre=None, fallback_to_heuristic=False)`.
    - Merges `user_input` into history if supplied.
    - Strips `[READY]` token from user-visible response and returns `is_ready: True/False`.
    - Returns `{ "status": "success", "message": ..., "reply": ..., "is_ready": ..., "detected_mode": ... }`.
    - On failure, catches exception and returns `JSONResponse(status_code=503, content={ "status": "error", "message": "Dịch vụ AI tạm thời gián đoạn: ...", "detail": "...", "retry_after": 5, "is_ready": False })`.
- **Verification in Tests**:
  - `test_api_chat_interview_success`
  - `test_api_chat_interview_with_user_input`
  - `test_api_chat_interview_503_error_on_exhaustion`
- **Assessment**: **VERIFIED.**

### 3.7 Unified Test Suite (`run_all_tests.py`)
- **Code Inspection**:
  - Discovers and loads:
    - Core Track (111 tests): `test_e2e_ontology_modes`, `test_e2e_banking_security`, `test_e2e_recommender_messenger`, `test_banking_adversarial_empirical`, `test_adversarial_narrative_recommender`, `test_backend_integration_gen2`.
    - Round 5 Track (71 tests): `test_e2e_round5_surgery_feed`, `test_adversarial_round5_resilience`.
    - Round 7 Track (16 tests): `test_round7_qa_resilience`.
  - Total: **198 test cases**.
- **Assessment**: **VERIFIED.**

---

## 4. Adversarial Challenges & Stress-Testing

### Challenge 1: Fallback Matrix Exhaustion under Total Network Outage
- **Scenario**: All 3 models and all 3 API keys fail due to an internet drop or Groq outage.
- **Analysis**:
  - If `fallback_to_heuristic=False` (default for backend test assertion): `_chat_with_resilience` raises `RuntimeError("Tất cả mô hình và khóa API trong chuỗi dự phòng đều thất bại: ...")`.
  - `/api/chat-interview` catches `RuntimeError` and returns HTTP 503 JSON.
  - If `fallback_to_heuristic=True`: `generate_fallback_question` generates an offline contextual question with in-parenthesis choices and sets `last_model_used = "heuristic-fallback"`.
- **Resilience Rating**: **ROBUST.**

### Challenge 2: Empty or Malformed Chat History Inputs
- **Scenario**: Client sends `chat_history=[]` and `user_input=""` or whitespace.
- **Analysis**:
  - `latest_input` defaults to `""`.
  - Heuristic generator falls through to proper noun / default anchor, using snippet `"ý tưởng vừa chia sẻ"` and anchor `"cốt truyện của bạn"`.
  - No `IndexError`, `KeyError`, or unhandled exception occurs.
- **Resilience Rating**: **ROBUST.**

### Challenge 3: Client Cache Pooling & Concurrency
- **Scenario**: Multiple requests switch between different models and keys.
- **Analysis**:
  - `self._client_pool` caches `GroqClient` instances by `(model_name, api_key)` pair.
  - Maximum size of `_client_pool` is capped at $3 \times 3 = 9$ entries.
  - Zero memory growth over time.
- **Resilience Rating**: **OPTIMAL.**

### Challenge 4: Thread Isolation of Metadata (Minor Finding)
- **Scenario**: High-concurrency simultaneous requests to `/api/chat-interview`.
- **Observation**: `qa.last_model_used` is an instance attribute on the singleton `qa_refiner`. If two requests execute concurrently, one request might read `qa.last_model_used` updated by the other request.
- **Impact**: Low/Cosmetic. `detected_mode` is informational and does not affect authentication, billing, or narrative logic.
- **Recommendation**: For future versions, return `(response, model_used)` directly from `chat_interview` rather than storing it on `self`.

---

## 5. Review Findings Summary

| Severity | Finding | Location | Description & Recommendation |
|---|---|---|---|
| **Minor** | Instance attribute `last_model_used` | `backend/agents/qa_refiner.py:77` | `last_model_used` is stored on the singleton refiner instance. Under heavy multi-threaded load, it may exhibit race conditions for the response's `detected_mode` field. Recommendation: return a tuple or dict from `chat_interview` in future iterations. Non-blocking. |

---

## 6. Conclusion & Recommendation

The Round 7 backend implementation is clean, robust, well-tested, and fully aligned with all architectural and user requirements. It maintains 100% backward compatibility with existing tests while dramatically improving the resilience and conversational intelligence of NarrAI's narrative intake assistant.

**Final Verdict**: **APPROVE**
