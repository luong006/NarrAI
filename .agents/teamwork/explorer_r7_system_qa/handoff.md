# Handoff Report: Testing & Verification Baseline Survey (R1-R5)

**Agent**: `explorer_r7_system_qa`  
**Working Directory**: `e:\NarrAI\.agents\teamwork\explorer_r7_system_qa`  
**Recipient**: `parent` (`6e1fbb7b-e64c-45b5-8d0a-ea6939f474c6`)  
**Timestamp**: 2026-10-05T05:41:30Z  
**Handoff Type**: Hard (Task Complete)  

---

## 1. Observation

1. **Test Runner Composition & Discovery**:
   - `backend/tests/run_all_tests.py` lines 23-42 only loads 6 modules:
     - `test_e2e_ontology_modes.py` (22 tests)
     - `test_e2e_banking_security.py` (17 tests)
     - `test_e2e_recommender_messenger.py` (14 tests)
     - `test_banking_adversarial_empirical.py` (21 tests)
     - `test_adversarial_narrative_recommender.py` (27 tests)
     - `test_backend_integration_gen2.py` (10 tests)
     - Subtotal in `run_all_tests.py`: **111 tests**.
   - Round 5 tests are located in:
     - `test_e2e_round5_surgery_feed.py` (50 tests)
     - `test_adversarial_round5_resilience.py` (21 tests)
     - Subtotal Round 5: **71 tests**.
     - Combined Core + Round 5 = **182 tests** (the exact number referenced in `ORIGINAL_REQUEST.md:399`).
   - Round 6 tests are located in:
     - `test_round6_copilot_stress.py` (8 tests)
     - `test_round6_copilot_surgery.py` (12 tests)
     - `test_round6_historical_copyright.py` (20 tests)
     - `test_round6_social_features.py` (25 tests)
     - `test_round6_tfjs_export.py` (8 tests)
     - `test_round6_wal_performance.py` (12 tests)
     - Subtotal Round 6: **85 tests**.
   - Discovered grand total across all suites in `backend/tests/`: **267+ tests**.

2. **Test Coverage Gaps for `qa_refiner`, `interview`, `social`, and `landing`**:
   - `qa_refiner` and `interview`:
     - `grep_search` across `backend/tests/` for `qa_refiner` found only `test_light_novel_engine.py:278` (testing Phase 2 `refine_prompt`) and `test_adversarial_m1.py:397` (checking cliché absence in source text).
     - `grep_search` for `interview` yielded **0 matches**.
     - `QARefiner.chat_interview()` and endpoint `POST /api/chat-interview` currently have **zero direct automated tests**.
   - `social`:
     - Rich existing test coverage: `test_round6_social_features.py` (25 tests), `test_e2e_recommender_messenger.py` (14 tests), and `test_e2e_round5_surgery_feed.py` (8 tests).
     - Missing coverage: Verification of Sidebar tab rename to "Cộng đồng tác giả" / "Mạng xã hội" and Landing Page direct entry point.
   - `landing`:
     - **0 tests** exist for landing page behavior in backend, and frontend currently has no automated test runner configured in `frontend/package.json`.

3. **Backend `qa_refiner.py` Implementation Vulnerability**:
   - `backend/agents/qa_refiner.py` lines 6-8:
     ```python
     class QARefiner:
         def __init__(self):
             self.llm = GroqClient(model_name="qwen/qwen3.8-27b", api_key=os.environ.get("GROQ_API_KEY_BIBLE"))
     ```
   - Only a single model (`qwen/qwen3.8-27b`) and a single key (`GROQ_API_KEY_BIBLE`) are utilized.
   - There is NO fallback to `llama-3.3-70b-versatile` or `llama-3.1-8b-instant`.
   - There is NO fallback to `GROQ_API_KEY` or `GROQ_API_KEY_COPILOT`.
   - If Groq encounters rate limiting (429) or token congestion, `chat_interview()` raises an unhandled exception, causing `main.py:406` to return `{"status": "error", "message": ...}`.

4. **Frontend Layout and Canned Response Observations**:
   - `frontend/src/components/setup/UnifiedIntakeChat.tsx` line 597:
     `<div className="fixed bottom-0 left-0 right-0 sm:left-64 p-3 sm:p-5 ...">`
     This hardcoded `sm:left-64` causes the bottom dock to sit asymmetrical to the chat viewport.
   - `frontend/src/components/setup/UnifiedIntakeChat.tsx` lines 289-310:
     Falls back to hardcoded static Vietnamese strings:
     `"Ý tưởng của bạn rất cuốn hút! Hãy chia sẻ thêm về nhân vật chính, xung đột cốt lõi hoặc bối cảnh không gian nhé."`
     and
     `"Đang kết nối lại với trợ lý NarrAI..."`
     causing user complaints of repetitive robotic loops whenever the backend falters.
   - `frontend/src/components/landing/LandingView.tsx`:
     - Line 10: `import { NeuralVisualPreview } from "@/components/canvas/NeuralVisualPreview";`
     - Lines 85-87: `<NeuralVisualPreview lang={lang} />`
     - Lines 73-81: CTA section only contains "Bắt đầu sáng tác ngay", lacking any "Khám phá Cộng đồng" link.
   - `frontend/src/components/layout/Sidebar.tsx` lines 152-162:
     - Uses `Compass` icon and displays label `{t.tab_posts || "Bài đăng"}`.

5. **Frontend Build Toolchain**:
   - `frontend/package.json`: Next.js `14.2.23`, React `18.3.1`, `@tensorflow/tfjs` `^4.20.0`, TypeScript `5.7.2`.
   - `next.config.mjs`: `output: 'export'`, `typescript: { ignoreBuildErrors: false }`.
   - Removing `<NeuralVisualPreview />` from `LandingView.tsx` will not break TensorFlow.js modules as long as `@tensorflow/tfjs` stays in `package.json` and `NeuralVisualPreview.tsx` remains present for modal use.

---

## 2. Logic Chain

1. **Step 1 (Test Runner Discrepancy)**: Observation 1 confirms that `run_all_tests.py` explicitly loads only the 6 core modules totaling 111 tests. The remaining 71 tests to reach 182 are found in `test_e2e_round5_surgery_feed.py` and `test_adversarial_round5_resilience.py`. Furthermore, Round 6 contains an additional 85 tests. Therefore, executing only `run_all_tests.py` in its current state leaves Round 5, Round 6, and new suites unrun. The runner must be expanded to discover or register all suites.
2. **Step 2 (Root Cause of AI Repetitive Response)**: Observation 3 shows that `QARefiner` in `qa_refiner.py` has no model or key fallback. When `qwen/qwen3.8-27b` hits rate limits or `GROQ_API_KEY_BIBLE` is throttled, the backend returns an error. Observation 4 shows that `UnifiedIntakeChat.tsx` handles errors by rendering a static boilerplate string. Because rate limits persist across consecutive calls, the user repeatedly receives identical canned text, perceiving it as a broken loop.
3. **Step 3 (Resilience Architecture)**: By adding Multi-Model Fallback (`qwen/qwen3.8-27b` -> `llama-3.3-70b-versatile` -> `llama-3.1-8b-instant`), Multi-Key Fallback (`GROQ_API_KEY_BIBLE` -> `GROQ_API_KEY` -> `GROQ_API_KEY_COPILOT`), keyword-reflective system prompting, and client-side dynamic fallback questions, the AI interview flow becomes completely resilient against outages.
4. **Step 4 (Frontend Visual Cleanliness & Symmetry)**: Removing `<NeuralVisualPreview />` from `LandingView.tsx` (Observation 4) removes visual noise on the landing page. Replacing `fixed sm:left-64` in `UnifiedIntakeChat.tsx` with a centered container resolves dock asymmetry. Renaming the Sidebar tab from "Bài đăng" to "Cộng đồng tác giả" with `Users`/`Globe` icon and adding an "Explore Community" button to `LandingView.tsx` satisfies R4 without architectural collision.
5. **Step 5 (Quality Gate Feasibility)**: Observation 5 confirms strict TypeScript checking (`ignoreBuildErrors: false`). Testing strategy must verify zero TypeScript errors on `npm run build` alongside 100% backend unit test passing.

---

## 3. Caveats

1. **Execution of `run_command`**: An interactive permission prompt timed out during initial execution. Consequently, all metrics and line numbers were derived via thorough static analysis, regex grep, AST inspection, and line-by-line reading of test suites. When running commands in production, permissions must be granted to execute `python backend/tests/run_all_tests.py` and `npm run build`.
2. **Active LLM API Keys**: Multi-key fallback requires at least one of `GROQ_API_KEY_BIBLE`, `GROQ_API_KEY`, or `GROQ_API_KEY_COPILOT` to be provisioned in the live environment. If none are provisioned, our proposed design includes a deterministic Socratic keyword fallback to ensure the system never crashes.
3. **No Frontend Automated Test Runner**: There is no Jest or Playwright runner in `frontend/package.json`. Structural frontend verification for R1, R2, and R4 is achieved via automated AST/regex assertions in Python test scripts alongside `npm run build`.

---

## 4. Conclusion

1. **Test Suite Baseline**: The current backend test battery contains **267+ tests** across Core (111), Round 5 (71), Round 6 (85), and specialized tracks. The "182 tests" referenced in the user request corresponds exactly to Core (111) + Round 5 (71).
2. **Identified Test Gap**: Zero tests currently cover `QARefiner.chat_interview()`, multi-model fallback, multi-key fallback, or `/api/chat-interview`. A dedicated test suite (`backend/tests/test_round7_chat_resilience.py`) with 15 test cases must be introduced.
3. **Actionable Implementation Guidance**:
   - In `backend/agents/qa_refiner.py`: Introduce multi-model fallback, multi-key fallback, keyword-reflective prompt directives, and deterministic fallback.
   - In `backend/tests/run_all_tests.py`: Expand `build_e2e_suite()` to discover all test modules so that running `python backend/tests/run_all_tests.py` executes all 182+ tests.
   - In `frontend/src/components/landing/LandingView.tsx`: Remove `<NeuralVisualPreview />` and its import; add "Khám phá Cộng đồng" CTA button.
   - In `frontend/src/components/setup/UnifiedIntakeChat.tsx`: Remove `fixed sm:left-64` in favor of centered sticky/flex layout; balance avatars; eliminate static repetitive error text in favor of dynamic keyword fallback.
   - In `frontend/src/components/layout/Sidebar.tsx` & `i18n.ts`: Rename "Bài đăng" to "Cộng đồng tác giả" / "Mạng xã hội" with `Users`/`Globe` icon.

---

## 5. Verification Method

To independently verify the baseline and validate upcoming implementations, execute the following commands:

1. **Verify Complete Backend Test Suite (All 182+ Tests)**:
   ```powershell
   python -m unittest discover -s backend/tests -p "test_*.py"
   ```
   *Expected outcome*: All discovered tests pass with 0 errors and 0 failures.

2. **Verify Expanded Unified Test Runner**:
   ```powershell
   python backend/tests/run_all_tests.py
   ```
   *Expected outcome*: Discovers and executes all registered test tracks with 100% success.

3. **Verify Python Syntax**:
   ```powershell
   python -m py_compile backend/main.py backend/agents/qa_refiner.py backend/llm/groq_client.py backend/routers/social_router.py
   ```
   *Expected outcome*: Exit code 0, no syntax errors.

4. **Verify Frontend Clean Production Build**:
   ```powershell
   cd frontend
   npm run build
   ```
   *Expected outcome*: Next.js static export finishes cleanly with 0 TypeScript errors.

5. **Verify Elimination of `NeuralVisualPreview` on Landing Page**:
   ```powershell
   python -c "content = open('frontend/src/components/landing/LandingView.tsx', encoding='utf-8').read(); assert 'NeuralVisualPreview' not in content, 'NeuralVisualPreview still present in LandingView!'"
   ```

6. **Verify Chat Dock Symmetry**:
   ```powershell
   python -c "content = open('frontend/src/components/setup/UnifiedIntakeChat.tsx', encoding='utf-8').read(); assert 'fixed sm:left-64' not in content, 'Asymmetric fixed sm:left-64 still present in UnifiedIntakeChat!'"
   ```

**Invalidation Conditions**:
- If `python -m unittest discover -s backend/tests -p "test_*.py"` reports any regression failures.
- If `npm run build` fails with TypeScript compile errors.
- If `NeuralVisualPreview` remains rendered on the Landing Page.
- If AI chat interview falls back to hardcoded static repetitive text.
