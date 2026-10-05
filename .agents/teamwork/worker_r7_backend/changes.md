# Changes Report - worker_r7_backend

**Author**: `worker_r7_backend`  
**Milestone**: Milestone 2 — Backend AI Resilience & Q&A Interview Refiner  
**Timestamp**: 2026-10-05T06:12:00Z  

---

## 1. Summary of Changes

This update implements full multi-model and multi-key fallback resilience for NarrAI's narrative intake assistant (`QARefiner`), upgrades the system prompt with strict Concept Mirroring and anti-boilerplate rules, enhances the `/api/chat-interview` FastAPI endpoint to handle failure gracefully with structured HTTP 503 responses, creates the `test_round7_qa_resilience.py` test suite, and unifies all 198 tests into `run_all_tests.py`.

---

## 2. File-by-File Changes & Technical Rationale

### 2.1 `backend/agents/qa_refiner.py`
- **Multi-Model Fallback Matrix**:
  - Primary: `qwen/qwen3.8-27b`
  - Secondary: `llama-3.3-70b-versatile`
  - Tertiary: `llama-3.1-8b-instant`
- **Multi-Key Fallback Hierarchy**:
  - Primary: `GROQ_API_KEY_BIBLE`
  - Secondary: `GROQ_API_KEY`
  - Tertiary: `GROQ_API_KEY_COPILOT`
- **100% Backward Mock Compatibility**:
  - `self.llm` remains an active, initialized `GroqClient` instance.
  - `_chat_with_resilience` invokes `self.llm.chat` first before entering any fallback loop.
  - Tests that mock `refiner.llm.chat` (e.g., `test_light_novel_engine.py`) or replace `refiner.llm` continue to pass immediately without triggering fallback.
- **Concept Mirroring & Anti-Boilerplate System Prompt**:
  - Explicitly mandates extracting the author's concrete concepts (character names, settings, conflict tropes, genre).
  - Strictly forbids generic canned AI greetings ("Ý tưởng của bạn rất hay/thú vị/cuốn hút!", "Chào bạn, đây là một tiền đề tuyệt vời", "Tôi rất hào hứng...").
  - Enforces formulating 1-2 deep open-ended follow-up questions with in-parenthesis contrasting choices (e.g., `(Lựa chọn A, hay Lựa chọn B?)`).
  - Preserves Vietnamese historical integrity guardrails (Hai Bà Trưng, Ngô Quyền, Lý Thường Kiệt, Trần Hưng Đạo, Lê Lợi, Quang Trung) and commercial IP copyright protection.
  - Emits `[READY]` token when the premise is mature or upon explicit author command.
- **Dynamic Heuristic Generator (`generate_fallback_question`)**:
  - Provides offline/exhaustion heuristic question generation extracting historical figures, sci-fi/cyberpunk settings, cultivation tropes, detective clues, or capitalized proper nouns.
- **Story Outline Synthesis (`refine_prompt`)**:
  - Preserves the exact 5 Dramatic Narrative Beats (`Hook (0-15%)`, `Rising Friction (15-40%)`, `Turning Point (40-70%)`, `Visceral Climax (70-90%)`, `Lingering Cliffhanger (90-100%)`) required by `test_light_novel_engine.py`.
  - Added fallback resilience to `refine_prompt` if primary client fails.

### 2.2 `backend/main.py`
- **Pydantic Model `ChatInterviewRequest`**:
  - Added default value `chat_history: list = []`.
  - Added optional fields `user_input: Optional[str] = None`, `genre: Optional[str] = None`, and `fallback_to_heuristic: bool = False`.
- **Endpoint `/api/chat-interview`**:
  - Merges `request.user_input` into `chat_history` if provided.
  - Passes `fallback_to_heuristic` to `qa.chat_interview()`.
  - Returns structured success response with `message`, `reply` (meeting `PROJECT.md` contract), `is_ready`, and `detected_mode`.
  - On exception/exhaustion, catches error and returns `JSONResponse(status_code=503, content={"status": "error", "message": "Dịch vụ AI tạm thời gián đoạn: ...", "detail": "...", "retry_after": 5, "is_ready": False})`. This allows the frontend to show connection status and offer a retry action.

### 2.3 `backend/tests/test_round7_qa_resilience.py` (New File)
- **16 Comprehensive Test Cases**:
  1. `test_qa_refiner_initialization_defaults`: Validates model hierarchy, key list, and primary client.
  2. `test_qa_refiner_mock_compatibility`: Validates that `refiner.llm.chat` mock works directly.
  3. `test_multi_model_fallback_rate_limit_to_llama_70b`: Simulates 429 rate limit on Qwen; verifies automatic progression to Llama 3.3 70B.
  4. `test_multi_model_fallback_tertiary_to_llama_8b`: Simulates failures on Qwen and Llama 70B; verifies fallback to Llama 3.1 8B.
  5. `test_multi_key_fallback_on_auth_quota_error`: Simulates 401/quota failure on `GROQ_API_KEY_BIBLE`; verifies fallback to `GROQ_API_KEY`.
  6. `test_multi_key_fallback_tertiary_copilot_key`: Simulates failures on BIBLE and DEFAULT keys; verifies fallback to `GROQ_API_KEY_COPILOT`.
  7. `test_exhaustion_raises_runtime_error`: Verifies `RuntimeError` on complete fallback exhaustion when heuristic is disabled.
  8. `test_heuristic_fallback_when_exhausted_and_enabled`: Verifies heuristic question when `fallback_to_heuristic=True`.
  9. `test_system_prompt_concept_mirroring_mandate`: Verifies Concept Mirroring rules, ban on boilerplate, and absence of 19th-century realism persona.
  10. `test_concept_mirroring_historical_figures`: Verifies mirroring of Trần Hưng Đạo and Chính sử vs Dã sử contrasting choices.
  11. `test_concept_mirroring_scifi_cyberpunk`: Verifies mirroring of Sài Gòn 2099 setting with contrasting options.
  12. `test_concept_mirroring_xianxia_fantasy`: Verifies mirroring of cultivation tropes.
  13. `test_concept_mirroring_proper_noun_extraction`: Verifies extraction of custom proper nouns.
  14. `test_api_chat_interview_success`: Tests `/api/chat-interview` endpoint with TestClient for success payload.
  15. `test_api_chat_interview_with_user_input`: Tests endpoint handling of `user_input`.
  16. `test_api_chat_interview_503_error_on_exhaustion`: Tests that endpoint returns HTTP 503 structured response on AI failure.

### 2.4 `backend/tests/run_all_tests.py`
- Upgraded `build_e2e_suite()` to discover and load:
  - **Core Track (111 tests)**: `test_e2e_ontology_modes`, `test_e2e_banking_security`, `test_e2e_recommender_messenger`, `test_banking_adversarial_empirical`, `test_adversarial_narrative_recommender`, `test_backend_integration_gen2`.
  - **Round 5 Track (71 tests)**: `test_e2e_round5_surgery_feed`, `test_adversarial_round5_resilience`.
  - **Round 7 Track (16 tests)**: `test_round7_qa_resilience`.
  - **Total**: 198 automated unit and integration tests executed in unified suite.
