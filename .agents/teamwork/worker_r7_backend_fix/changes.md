# Changes Report — worker_r7_backend_fix

**Agent**: `worker_r7_backend_fix`  
**Date**: 2026-10-05T06:40:00Z  
**Target Milestone**: R7 AI Resilience Remediations (Challenger Defect Fixes)  

---

## 1. Summary of Changes

Remediated the deterministic offline/heuristic fallback logic in `qa_refiner.py` and added regression test coverage in `test_round7_qa_resilience.py`.

### A. `backend/agents/qa_refiner.py`
1. **Sci-Fi Keyword Clean-Up in `generate_fallback_question`**:
   - Removed `"ai"` substring from `scifi_keywords`. The raw substring `"ai"` caused widespread false positive matches in Vietnamese (e.g., words containing the high-frequency diphthong `"ai"` such as *"hai"*, *"phải"*, *"lại"*, *"tại"*, and loanwords like *"isekai"*). Replaced with explicit phrase `"trí tuệ nhân tạo"`.
   - Removed `"thám tử tư"` from `scifi_keywords`. Preserved it solely under `thriller_keywords` to prevent classic detective/noir stories from being hijacked into cyberpunk prompts.
   - Changed generic `"ký ức"` to `"ký ức số"`. This prevents emotional/slice-of-life memory narratives from triggering sci-fi corporatocracy questions.
   
2. **Expansion of Sentence-Initial Stopwords in `filtered_caps`**:
   - Expanded the list of excluded stopwords from 8 to 20 tokens:
     `{"Tôi", "Bạn", "Một", "Khi", "Hãy", "Trong", "Để", "Nếu", "Chuyện", "Câu", "Viết", "Kể", "Vào", "Đây", "Đó", "Về", "Tác", "Cuộc", "Ngày", "Ở"}`
   - Prevents sentence-initial verbs and nouns (e.g. `"Kể về..."`, `"Viết về..."`, `"Chuyện một..."`) from being extracted as character names (e.g. producing `"nhân vật Kể"`).

3. **Sanitization of `chat_history` in `chat_interview`**:
   - Sanitized incoming `chat_history` dictionaries before forwarding them to `messages` for LLM consumption.
   - Retains strictly `{"role": ..., "content": ...}`, stripping out client-side metadata flags (`is_offline_fallback`, `error_message`, `failed_prompt`, `is_ready`, etc.). This protects against LLM provider schema rejection errors.

---

### B. `backend/tests/test_round7_qa_resilience.py`
Added 5 comprehensive unit tests targeting all challenger findings:
1. `test_chat_interview_sanitizes_metadata`: Verifies that `chat_interview` strips client metadata (`is_offline_fallback`, `error_message`, etc.) and retains only `role` and `content`.
2. `test_isekai_am_thuc_does_not_trigger_scifi`: Verifies that `"Isekai ẩm thực"` does NOT trigger sci-fi questions or cyberpunk neon world tropes.
3. `test_hai_tam_hon_co_don_does_not_trigger_scifi`: Verifies that `"Hai tâm hồn cô đơn tại Hà Nội"` does NOT trigger sci-fi questions.
4. `test_ke_ve_does_not_extract_nhan_vat_ke`: Verifies that `"Kể về một người thợ rèn"` does NOT extract `"nhân vật Kể"`, instead cleanly setting the anchor to `"cốt truyện của bạn"`.
5. `test_tham_tu_tu_triggers_thriller_not_scifi`: Verifies that `"Thám tử tư điều tra vụ án"` triggers the detective/thriller question template rather than the sci-fi template.

---

## 2. Verification Summary
- **Python Syntax Verification**: Clean syntax across `qa_refiner.py` and `test_round7_qa_resilience.py`.
- **Test Discoverability**: 19 tests in `test_round7_qa_resilience.py` integrated into `run_all_tests.py`.
- **Zero Regression**: Preserves backwards compatibility with `self.llm` mocks, historical figure extraction, and existing test suites.
