## 2026-10-05T05:42:57Z
You are worker_r7_backend, an implementation specialist for NarrAI.
Your working directory: e:\NarrAI\.agents\teamwork\worker_r7_backend

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY FIRST STEP: Read the user request at:
e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md (specifically the section timestamped 2026-10-05T05:28:19Z).

Also read:
- e:\NarrAI\.agents\teamwork\orchestrator_r7_1\PROJECT.md
- e:\NarrAI\.agents\teamwork\explorer_r7_backend\analysis.md
- e:\NarrAI\.agents\teamwork\explorer_r7_system_qa\analysis.md

YOUR EXCLUSIVE WRITE OWNERSHIP:
- `backend/agents/qa_refiner.py`
- `backend/main.py`
- `backend/tests/test_round7_qa_resilience.py` (new test suite)
- `backend/tests/run_all_tests.py`
Do NOT modify frontend files.

TASKS TO IMPLEMENT:
1. R3 Backend (`backend/agents/qa_refiner.py`):
   - Multi-Model Fallback:
     - Primary: `qwen/qwen3.8-27b`
     - Secondary: `llama-3.3-70b-versatile`
     - Tertiary: `llama-3.1-8b-instant`
   - Multi-Key Fallback:
     - Primary: `GROQ_API_KEY_BIBLE`
     - Secondary: `GROQ_API_KEY`
     - Tertiary: `GROQ_API_KEY_COPILOT`
   - CRITICAL COMPATIBILITY REQUIREMENT:
     - Maintain `self.llm` mock compatibility so existing tests (which mock `self.llm` or `ChatGroq`) continue to pass 100%!
   - Upgraded System Prompt:
     - Enforce Concept Mirroring: AI must extract specific keywords/concepts from user input (e.g. character, theme, conflict) and respond with 1-2 deep, open-ended narrative follow-up questions with in-parenthesis contrasting choices.
     - Strictly ban canned greetings, boilerplate responses, and static templates.
2. `backend/main.py`:
   - Enhance the `/api/chat-interview` endpoint error handling so that if all backend keys/models fail, it returns a structured error response with status code 503 or detail JSON, allowing the frontend to show connection status and retry.
3. Tests (`backend/tests/test_round7_qa_resilience.py`):
   - Create comprehensive unit tests for:
     - Multi-model fallback progression on rate limit / 429 errors.
     - Multi-key fallback progression on authentication / quota errors.
     - Concept Mirroring and question generation formatting in system prompt.
     - Mock resilience and error handling.
4. Test Runner (`backend/tests/run_all_tests.py`):
   - Update `run_all_tests.py` so that it discovers and runs all 182+ tests (Core 111 + Round 5 71 + new Round 7 resilience tests).
   - Run `python backend/tests/run_all_tests.py` and confirm 100% tests PASS.
   - Run `python -m py_compile backend/main.py backend/agents/qa_refiner.py` to confirm syntax is clean.

OUTPUT REQUIREMENTS:
- Write `changes.md` in `e:\NarrAI\.agents\teamwork\worker_r7_backend\` detailing every modified file and rationale.
- Write `handoff.md` with full Verification Method and Results (test execution logs).
- Send a completion message to the orchestrator when finished.


## 2026-10-05T06:05:43Z
**Context**: Milestone 2 Implementation (Backend AI Resilience & Tests)
**Content**: Orchestrator heartbeat check. Please report your current progress on tasks (qa_refiner.py fallback matrix & Concept Mirroring prompt, main.py interview endpoint error handling, test_round7_qa_resilience.py).
**Action**: Update your progress.md with current task status and timestamp, and notify orchestrator of any blockers.
