## 2026-10-05T06:34:32Z
You are worker_r7_backend_fix, a backend remediation specialist for NarrAI.
Your working directory: e:\NarrAI\.agents\teamwork\worker_r7_backend_fix

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY FIRST STEP: Read the user request at:
e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md (specifically the section timestamped 2026-10-05T05:28:19Z).

Also read:
- e:\NarrAI\.agents\teamwork\orchestrator_r7_1\PROJECT.md
- e:\NarrAI\.agents\teamwork\challenger_r7_ai\handoff.md (CRITICAL: full challenger report detailing the defect)

YOUR EXCLUSIVE WRITE OWNERSHIP:
- `backend/agents/qa_refiner.py`
- `backend/tests/test_round7_qa_resilience.py`
- `backend/tests/run_all_tests.py`

TASKS TO REMEDIATE:
1. In `backend/agents/qa_refiner.py`:
   - In `generate_fallback_question`:
     - In `scifi_keywords`: Remove `"ai"` (keep `"trí tuệ nhân tạo"`). Remove `"thám tử tư"` (it is preserved in `thriller_keywords`). Change generic `"ký ức"` to `"ký ức số"`.
     - In `filtered_caps`: Expand excluded stop words to filter sentence-initial verbs/nouns: `"Tôi", "Bạn", "Một", "Khi", "Hãy", "Trong", "Để", "Nếu", "Chuyện", "Câu", "Viết", "Kể", "Vào", "Đây", "Đó", "Về", "Tác", "Cuộc", "Ngày", "Ở"`.
   - In `chat_interview`:
     - Sanitize `chat_history`: strip out any client-specific metadata (`is_offline_fallback`, `error_message`, `failed_prompt`, `is_ready`) and keep only `role` and `content` before passing to LLM messages.
2. In `backend/tests/test_round7_qa_resilience.py`:
   - Add unit tests verifying:
     - Input `"Isekai ẩm thực"` does NOT trigger sci-fi questions.
     - Input `"Hai tâm hồn cô đơn tại Hà Nội"` does NOT trigger sci-fi questions.
     - Input `"Kể về một người thợ rèn"` does NOT extract `"nhân vật Kể"`.
     - Input `"Thám tử tư điều tra vụ án"` triggers detective/thriller question, not sci-fi.
3. Test Verification:
   - Run `python backend/tests/run_all_tests.py` and confirm 100% tests PASS.
   - Run `python -m py_compile backend/agents/qa_refiner.py`.

OUTPUT REQUIREMENTS:
- Write `changes.md` in `e:\NarrAI\.agents\teamwork\worker_r7_backend_fix\`.
- Write `handoff.md` with Verification Method and Results.
- Send a completion message to the orchestrator when finished.
