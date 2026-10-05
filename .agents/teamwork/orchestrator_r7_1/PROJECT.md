# Project: NarrAI Quality & Resilience Upgrade (R1 - R5)

## Architecture
- **Frontend (Next.js 14 / TypeScript / Tailwind CSS / Lucide React)**:
  - `frontend/src/components/LandingView.tsx`: Clean Hero, CTA buttons ("Bắt đầu sáng tác ngay", "Khám phá Cộng đồng"), 3D feature cards.
  - `frontend/src/components/UnifiedIntakeChat.tsx`: AI Co-creation intake chat with symmetrical layout, flex/sticky centered bottom dock, keyword-based client fallback, and connection status with retry.
  - `frontend/src/components/Sidebar.tsx`: Navigation sidebar with updated "Mạng xã hội" tab (`Users` icon).
  - `frontend/src/components/CommunityFeedView.tsx`: Community social feed with posts, likes, author follow/unfollow, threaded comments, and search.
  - `frontend/src/services/api.ts`: API client with structured error handling.
- **Backend (FastAPI / Groq / LangChain / SQLite WAL)**:
  - `backend/agents/qa_refiner.py`: Dual-matrix fallback (Multi-Model & Multi-Key) with Concept Mirroring system prompt and `self.llm` mock compatibility.
  - `backend/main.py`: `/api/chat-interview` robust error response handling.
  - `backend/tests/run_all_tests.py`: Comprehensive test runner covering 182+ tests across Core, Round 5, and Round 7 resilience tests.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | R1. Remove Neural Style Lab | Unmount `<NeuralVisualPreview />` from `LandingView.tsx`, keep Hero and feature cards clean | M1 | ORIGINAL_REQUEST |
| 2 | R2. Chat Layout Symmetry | Replace `fixed sm:left-64` with flex/sticky centered bottom dock, balance avatar/bubble padding, widen starter prompts | M1 | ORIGINAL_REQUEST |
| 3 | R3. Backend AI Resilience | Multi-Model (`qwen` -> `llama-70b` -> `llama-8b`), Multi-Key (`BIBLE` -> `DEFAULT` -> `COPILOT`), Concept Mirroring system prompt | M2 | ORIGINAL_REQUEST |
| 4 | R3. Frontend Chat Resilience | Dynamic keyword-based client fallback, inline connection error state with "Thử lại" button | M1 | ORIGINAL_REQUEST |
| 5 | R4. Social & Community | Rename Sidebar tab to "Mạng xã hội" (`Users` icon), add "Khám phá Cộng đồng" CTA in LandingView, verify community features | M1 | ORIGINAL_REQUEST |
| 6 | R5. System Testing & Gates | Expand `run_all_tests.py` to run 182+ tests, create `test_round7_qa_resilience.py`, verify `npm run build` | M3 | ORIGINAL_REQUEST |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Frontend UI/UX Refactoring | R1, R2, R3 (frontend fallback & retry), R4 | Survey complete | DONE |
| M2 | Backend AI Resilience & Fallback | R3 (backend qa_refiner.py fallback matrix & prompt), R5 backend test suite | Survey complete | DONE |
| M3 | Quality Gates & Verification | R5: Run 182+ tests, frontend build, review, challenge, forensic audit | M1, M2 | DONE |

## Code Layout & Write Boundaries
- **Worker Frontend (`worker_r7_frontend`) Exclusive Ownership**:
  - `frontend/src/components/LandingView.tsx`
  - `frontend/src/components/UnifiedIntakeChat.tsx`
  - `frontend/src/components/Sidebar.tsx`
  - `frontend/src/components/CommunityFeedView.tsx`
  - `frontend/src/services/api.ts`
- **Worker Backend (`worker_r7_backend`) Exclusive Ownership**:
  - `backend/agents/qa_refiner.py`
  - `backend/main.py`
  - `backend/tests/test_round7_qa_resilience.py`
  - `backend/tests/run_all_tests.py`
- Concurrent Workers MUST NOT write to each other's files.

## Interface Contracts
### `/api/chat-interview` Request & Response
- **Request**: `{ "user_input": string, "chat_history": list, "genre": optional string }`
- **Response**: `{ "reply": string, "detected_mode": optional string, "suggested_actions": optional list }`
- **Error handling**: On 5xx / rate limit, returns HTTP 503 or structured JSON `{ "detail": "...", "retry_after": ... }` to trigger frontend connection status.
