## 2026-10-05T05:32:19Z
You are explorer_r7_backend, an exploration specialist for NarrAI.
Your working directory: e:\NarrAI\.agents\teamwork\explorer_r7_backend

MANDATORY FIRST STEP: Read the user request at:
e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md (specifically the section timestamped 2026-10-05T05:28:19Z).

YOUR MISSION (Survey Backend & AI Resilience for R3):
1. Backend Survey (`backend/agents/qa_refiner.py` and `backend/main.py`):
   - Analyze the current intake chat / interview endpoint (e.g. `/api/chat-interview` or `/api/interview`) and `qa_refiner.py`.
   - Multi-Model Fallback: How are models currently invoked (Groq / OpenAI / etc.)? How can we implement a robust fallback chain: `qwen/qwen3.8-27b` -> `llama-3.3-70b-versatile` -> `llama-3.1-8b-instant` on rate limits or API errors?
   - Multi-Key Fallback: How are Groq API keys loaded from env? How to implement automatic rotation/fallback: `GROQ_API_KEY_BIBLE` -> `GROQ_API_KEY` -> `GROQ_API_KEY_COPILOT`?
   - System Prompt: Inspect current prompt in `qa_refiner.py`. How to upgrade it so the AI always extracts key concepts/keywords from the user's input and asks 1-2 thoughtful, open-ended follow-up questions without boilerplate or repetitive canned replies?
2. Frontend Chat Integration Survey (`UnifiedIntakeChat.tsx` & `frontend/src/services/api.ts`):
   - How does the frontend call the chat interview endpoint?
   - Where is the static canned message (if any) currently coming from?
   - How to replace static fallback messages with clear connection status and a "Thử lại" (Retry) button?
   - How to implement a Dynamic Client Fallback that, in case of total network offline/server failure, dynamically generates an intelligent follow-up question based on user keywords rather than a static error text?

OUTPUT REQUIREMENTS:
- Write your detailed findings to `e:\NarrAI\.agents\teamwork\explorer_r7_backend\analysis.md`.
- Write your handoff summary to `e:\NarrAI\.agents\teamwork\explorer_r7_backend\handoff.md`.
- Keep `progress.md` updated with liveness timestamps.
- Send a completion message back to the orchestrator when finished.
