# System & Testing Exploration Survey for NarrAI R1-R5 Baseline

**Author**: `explorer_r7_system_qa`  
**Date**: 2026-10-05  
**Scope**: Verification baseline, test suite inspection, frontend build evaluation, and comprehensive test coverage strategy for R1 - R5  
**Target Repository**: `e:\NarrAI`  

---

## 1. Executive Summary

A comprehensive survey of the NarrAI codebase was conducted to establish the testing and verification baseline for the current milestone (prompt timestamped `2026-10-05T05:28:19Z`). The milestone focuses on resolving 5 visual and operational issues:
1. **R1**: Completely removing `<NeuralVisualPreview />` ("Neural Style Laboratory") from `LandingView.tsx` while preserving TensorFlow.js dependencies and modules.
2. **R2**: Restoring layout symmetry to `UnifiedIntakeChat.tsx` (eliminating the rigid `fixed sm:left-64` bottom input dock, balancing avatars/padding, and aligning starter prompts).
3. **R3**: Eliminating AI chat repetitive boilerplate responses by introducing Backend Multi-Model Fallback (`qwen/qwen3.8-27b` -> `llama-3.3-70b-versatile` -> `llama-3.1-8b-instant`), Multi-Key Fallback (`GROQ_API_KEY_BIBLE` -> `GROQ_API_KEY` -> `GROQ_API_KEY_COPILOT`), system prompt keyword reflection, and Frontend dynamic client-side fallback.
4. **R4**: Renaming and emphasizing the Community/Social section in the Sidebar and adding an "Explore Community" link directly on the Landing Page.
5. **R5**: Auditing end-to-end functionality across all core tracks to ensure 100% test pass rate across all 182+ backend tests and clean `npm run build` compilation.

---

## 2. Test Suite Architecture & Current Baseline

### 2.1 Test Suite Inventory & Composition

Inspection of `backend/tests/` revealed **39 Python files** containing **267+ automated test cases**:

| Test Group | Modules | Test Count | Description |
|---|---|---|---|
| **Core E2E Track** | `test_e2e_ontology_modes.py`<br>`test_e2e_banking_security.py`<br>`test_e2e_recommender_messenger.py`<br>`test_banking_adversarial_empirical.py`<br>`test_adversarial_narrative_recommender.py`<br>`test_backend_integration_gen2.py` | **111 tests** | Covers R1 Open-Ontology (22), R3 Banking & Anti-Clone (17), R2 Recommender & Messenger (14), Banking Concurrency & Ledger Integrity (21), Adversarial Invariants & Evasion (27), and FastAPI Router Integration (10). |
| **Round 5 Track** | `test_e2e_round5_surgery_feed.py`<br>`test_adversarial_round5_resilience.py` | **71 tests** | Covers 5-Target Copilot Manuscript Surgery (50) and Adversarial Surgery Stress & Invariant Preservation (21). |
| **Round 6 Track** | `test_round6_copilot_stress.py`<br>`test_round6_copilot_surgery.py`<br>`test_round6_historical_copyright.py`<br>`test_round6_social_features.py`<br>`test_round6_tfjs_export.py`<br>`test_round6_wal_performance.py` | **85 tests** | Covers selectedText & cursor positioning (20), expanded 20+ historical hero canon & semantic evasion (20), social follow/threads/bookmarks/reports/leaderboard (25), TF.js vector export (8), and SQLite WAL & GZip (12). |
| **Specialized Suites** | `test_light_novel_engine.py`, `test_comic_*.py`, `test_bank_auth.py`, `test_cache_service.py` | **30+ tests** | Unit tests for prompt styling, comic DNA, caching, and auth. |
| **TOTAL IN REPOSITORY** | All discovered test modules | **267+ tests** | Comprehensive multi-tier regression coverage. |

### 2.2 Analysis of `backend/tests/run_all_tests.py`

Inspection of `backend/tests/run_all_tests.py` (lines 23-42) revealed a critical discrepancy:
```python
def build_e2e_suite() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    from tests import test_e2e_ontology_modes
    from tests import test_e2e_banking_security
    from tests import test_e2e_recommender_messenger
    from tests import test_banking_adversarial_empirical
    from tests import test_adversarial_narrative_recommender
    from tests import test_backend_integration_gen2

    suite.addTests(loader.loadTestsFromModule(test_e2e_ontology_modes))
    ...
```
- **Finding**: `run_all_tests.py` currently only imports and registers the **6 Core modules (111 tests)**.
- **Root Cause of "182 tests" Reference**: The milestone document notes "182 tests (111 core + 71 round 5)". Round 5 tests (`test_e2e_round5_surgery_feed.py` and `test_adversarial_round5_resilience.py`) contain the remaining 71 tests, but were executed via `python -m unittest discover -s backend/tests -p "test_*round5*.py"`.
- **Recommendation**: `run_all_tests.py` should be updated to include `test_e2e_round5_surgery_feed`, `test_adversarial_round5_resilience`, and the Round 6 suites so that executing `python backend/tests/run_all_tests.py` validates the complete 182+ test battery in a single pass.

---

## 3. Test Coverage Gaps for R1 - R5

A systematic search across `backend/tests/` was performed to evaluate existing coverage for the four target functional areas:

### 3.1 `qa_refiner` and `interview` Coverage Gap
- **Current State**:
  - `grep_search` for `qa_refiner` yielded only 2 references:
    1. `test_adversarial_m1.py`: Merely asserts that the file `qa_refiner.py` does not contain banned AI cliché words.
    2. `test_light_novel_engine.py:278`: Tests `QARefiner.refine_prompt` (Phase 2 compression into 5 narrative beats).
  - `grep_search` for `interview` yielded **0 occurrences** across all test files.
- **Missing Coverage**:
  - `QARefiner.chat_interview()` has **ZERO direct unit or integration tests**.
  - `POST /api/chat-interview` has **ZERO endpoint tests**.
  - There are NO tests verifying multi-model fallback behavior when `qwen/qwen3.8-27b` fails.
  - There are NO tests verifying multi-key fallback behavior across `GROQ_API_KEY_BIBLE`, `GROQ_API_KEY`, and `GROQ_API_KEY_COPILOT`.
  - There are NO tests asserting that the Socratic follow-up mechanism parses author keywords and formulates dynamic questions rather than hardcoded canned responses.

### 3.2 `social` Coverage
- **Current State**:
  - Extensive coverage already exists:
    - `test_round6_social_features.py` (25 tests): Follow/unfollow, threaded comments (`parent_comment_id`), bookmarks, notifications, content reports, author profiles, and trending leaderboard.
    - `test_e2e_recommender_messenger.py` (14 tests): Social models, Two-Tower cosine similarity, decay, MMR diversity, multi-armed bandit, and 1-to-1 messenger.
    - `test_e2e_round5_surgery_feed.py` (8 tests): Publishing posts, cover sync from comic panels, manuscript saving, and post details retrieval.
- **Missing Coverage for R4**:
  - Sidebar navigation rename verification (checking that the UI exposes "Mạng xã hội" / "Cộng đồng").
  - Verification that Landing Page has a functional entry point redirecting new visitors directly to the Community Feed.

### 3.3 `landing` Coverage
- **Current State**:
  - `grep_search` for `landing` in `backend/tests/` returned **0 results**.
  - The frontend has no Jest/Vitest test runner configured in `frontend/package.json`.
- **Missing Coverage for R1**:
  - Verification that `LandingView.tsx` no longer imports or renders `<NeuralVisualPreview />`.
  - Verification that removing `<NeuralVisualPreview />` preserves `@tensorflow/tfjs` in `package.json` and keeps `NeuralVisualPreview.tsx` available for other contexts (e.g., modal view in `page.tsx`).

---

## 4. Frontend Build Baseline & Dependency Analysis

### 4.1 Configuration and Toolchain
- **Next.js Version**: `14.2.23` (App Router)
- **React Version**: `18.3.1`
- **TypeScript**: `5.7.2`
- **Tailwind CSS**: `3.4.17`
- **Build Mode**: Static export (`output: 'export'` in `next.config.mjs` unless `VERCEL` env is defined).
- **TypeScript Strictness**: `typescript.ignoreBuildErrors: false`. This means ANY typing defect or bad import will fail the production build immediately.
- **ESLint**: `eslint.ignoreDuringBuilds: true`.

### 4.2 TensorFlow.js Integration
- **Package**: `@tensorflow/tfjs` version `^4.20.0` in `dependencies`.
- **Usages**:
  1. `frontend/src/services/tfjsRecommender.ts`: On-device concept vector inference and local re-ranking.
  2. `frontend/src/components/canvas/NeuralVisualPreview.tsx`: Client-side visual neural texture generation.
  3. `frontend/src/app/page.tsx`: Embedded in modal dialog `isNeuralModalOpen`.
  4. `frontend/src/components/landing/LandingView.tsx`: Embedded in landing page section (lines 85-87).
- **Safety Verification for R1**:
  - In `LandingView.tsx`:
    - Line 10: `import { NeuralVisualPreview } from "@/components/canvas/NeuralVisualPreview";`
    - Lines 85-87: `<section className="max-w-4xl mx-auto px-6 pb-12"><NeuralVisualPreview lang={lang} /></section>`
  - Both line 10 and lines 85-87 must be removed.
  - `NeuralVisualPreview.tsx` must remain in `src/components/canvas/` so `page.tsx` line 23 does not break.
  - `@tensorflow/tfjs` must remain in `package.json` so `tfjsRecommender.ts` and backend `test_round6_tfjs_export.py` remain valid.

### 4.3 Chat Layout & Symmetry Analysis (R2)
In `frontend/src/components/setup/UnifiedIntakeChat.tsx`:
- **Bottom Input Dock Asymmetry**:
  - Line 597: `<div className="fixed bottom-0 left-0 right-0 sm:left-64 p-3 sm:p-5 ...">`
  - Problem: `fixed sm:left-64` assumes a fixed sidebar width of 256px on screens >= 640px, causing the input capsule to be off-center on different viewport sizes and conflicting with the main chat container.
  - Solution: Replace `fixed sm:left-64` with a centered flex/sticky container that aligns 1:1 with the main conversation container (`max-w-3xl mx-auto w-full`).
- **Avatar & Padding Symmetry**:
  - User and AI message bubbles in lines 526-570 need balanced margins, matching avatar sizing (`w-8 h-8 rounded-full`), and symmetrical horizontal padding.
- **Starter Cards Layout**:
  - Lines 490-516: The 4 prompt cards (`starterIdeas`) should maintain balanced grid heights (`grid-cols-1 sm:grid-cols-2 gap-3.5`) with consistent flex alignments.

### 4.4 Repetitive Canned Chat & Dynamic Fallback Analysis (R3)
In `frontend/src/components/setup/UnifiedIntakeChat.tsx`:
- **Current Bug**:
  - Lines 289-299:
    ```tsx
    } else {
      setMessages([
        ...newHistory,
        {
          role: "assistant",
          content: lang === "vi"
            ? "Ý tưởng của bạn rất cuốn hút! Hãy chia sẻ thêm về nhân vật chính, xung đột cốt lõi hoặc bối cảnh không gian nhé."
            : "Fascinating premise! Could you elaborate more on the protagonist, core conflict, or narrative setting?"
        }
      ]);
    }
    ```
  - Lines 302-310:
    ```tsx
    } catch (err: any) {
      setMessages([
        ...newHistory,
        {
          role: "assistant",
          content: lang === "vi"
            ? "Đang kết nối lại với trợ lý NarrAI. Bạn có thể tiếp tục chia sẻ hoặc bấm 'Bắt đầu viết truyện ngay' ở góc trên để khởi tạo bản thảo ngay lập tức!"
            : "Reconnecting to NarrAI Assistant..."
        }
      ]);
    }
    ```
  - Whenever the backend returns an error or encounters a rate limit, the user is repeatedly shown the same rigid phrase.
- **Solution Required**:
  1. Backend must provide resilient multi-model and multi-key fallback so calls succeed with high reliability.
  2. Frontend must remove the repetitive static boilerplate. On backend failure, display a clear connection error indicator with a "Thử lại" (Retry) action.
  3. For offline/network failure, integrate Dynamic Client Fallback that extracts keywords from `textToSend` and generates a customized Socratic question.

---

## 5. Test Coverage Strategy for R1 - R5

To guarantee zero regression and establish a reliable quality gate, we specify the test cases that must be implemented in a dedicated test suite: `backend/tests/test_round7_chat_resilience.py`.

### 5.1 Test Cases Specification

#### Track A: Backend Multi-Model & Multi-Key Fallback (`qa_refiner.py`)
1. `test_qa_refiner_primary_model_success`:
   - Mock primary model `qwen/qwen3.8-27b` to return valid Socratic questions.
   - Assert `chat_interview()` succeeds without attempting fallback.
2. `test_qa_refiner_fallback_to_llama_70b_on_primary_failure`:
   - Mock `qwen/qwen3.8-27b` to raise 429 RateLimitError.
   - Mock `llama-3.3-70b-versatile` to return valid response.
   - Assert `chat_interview()` transparently catches error and falls back to `llama-3.3-70b-versatile`.
3. `test_qa_refiner_fallback_to_llama_8b_on_secondary_failure`:
   - Mock both `qwen/qwen3.8-27b` and `llama-3.3-70b-versatile` to fail.
   - Mock `llama-3.1-8b-instant` to succeed.
   - Assert response is delivered seamlessly from the tertiary model.
4. `test_qa_refiner_multi_key_fallback_chain`:
   - Test fallback key resolution order: `GROQ_API_KEY_BIBLE` -> `GROQ_API_KEY` -> `GROQ_API_KEY_COPILOT`.
   - Assert that if the primary key is missing or encounters a 401 Unauthorized, the next key is tried immediately.
5. `test_qa_refiner_exhaustion_dynamic_recovery`:
   - When all Groq models and keys are exhausted, assert that `chat_interview()` executes a deterministic keyword-based question generator instead of raising an unhandled 500 error.

#### Track B: System Prompt Keyword Reflection & Socratic Invariants
6. `test_system_prompt_keyword_analysis_mandate`:
   - Inspect `system_prompt` inside `chat_interview()`.
   - Assert the prompt explicitly instructs the LLM to extract the author's concrete keywords (genre, characters, conflicts, settings) and forbids canned generic answers.
7. `test_system_prompt_single_or_double_question_constraint`:
   - Assert system prompt enforces asking at most 1 to 2 concise open-ended questions per turn.
8. `test_ready_token_lifecycle`:
   - Assert that `[READY]` token is emitted only when premise is mature or user explicitly commands creation.
   - Verify that `/api/chat-interview` strips `[READY]` from `message` and sets `is_ready: True`.

#### Track C: API Endpoint Integration (`main.py`)
9. `test_api_chat_interview_success`:
   - Send `POST /api/chat-interview` with sample `chat_history`.
   - Assert response status code is 200 and schema contains `status: "success"`, `message: str`, `is_ready: bool`.
10. `test_api_chat_interview_error_handling`:
   - Send malformed payload or trigger simulated failure.
   - Assert response handles error gracefully without server crash.

#### Track D: Social Navigation & Discovery
11. `test_social_feed_and_community_endpoints`:
   - Verify `/api/social/feed` returns posts with author profile, cover image, and engagement counts.
   - Verify `/api/social/publish` persists draft and syncs to community feed.

#### Track E: Frontend Structural Compliance Checks (Static AST / Code Inspection)
12. `test_frontend_landing_view_no_neural_preview`:
   - Read `frontend/src/components/landing/LandingView.tsx`.
   - Assert string `NeuralVisualPreview` does NOT exist in the file.
13. `test_frontend_landing_view_has_community_link`:
   - Read `frontend/src/components/landing/LandingView.tsx`.
   - Assert a CTA button linking to "Khám phá Cộng đồng" / "Explore Community" is present.
14. `test_frontend_intake_chat_no_fixed_left_64`:
   - Read `frontend/src/components/setup/UnifiedIntakeChat.tsx`.
   - Assert string `fixed sm:left-64` does NOT exist in the file.
15. `test_frontend_sidebar_community_naming`:
   - Read `frontend/src/components/layout/Sidebar.tsx`.
   - Assert the navigation tab uses `Users` or `Globe` icon and displays the Community label.

---

## 6. Verification Commands & Quality Gate Matrix

| Verification Gate | Command | Passing Criteria |
|---|---|---|
| **Python Syntax Check** | `python -m py_compile backend/main.py backend/agents/qa_refiner.py backend/llm/groq_client.py backend/routers/social_router.py` | Exit code 0, 0 syntax errors across all touched backend files. |
| **Core E2E Suite** | `python backend/tests/run_all_tests.py` | 100% pass (all 111 core tests + any updated test suites). |
| **Round 5 Surgery Suite** | `python -m unittest discover -s backend/tests -p "test_*round5*.py"` | 100% pass (71 tests). |
| **Round 6 Social/WAL/TFJS** | `python -m unittest discover -s backend/tests -p "test_round6_*.py"` | 100% pass (85 tests). |
| **Round 7 Resilience Suite** | `python -m unittest backend/tests/test_round7_chat_resilience.py` | 100% pass (all fallback, prompt, and structural tests). |
| **Comprehensive Unified Run** | `python -m unittest discover -s backend/tests -p "test_*.py"` | 100% pass across all 267+ tests in the repository. |
| **Frontend Production Build** | `cd frontend && npm run build` | Next.js 14 production build succeeds with exit code 0, zero TypeScript errors (`ignoreBuildErrors: false`), clean static export. |
| **Frontend Design Lint** | `cd frontend && npm run lint` | Next.js lint passes without blocking errors. |

---

## 7. Recommended Implementation Plan for Upstream Teams

1. **Backend Team**:
   - Update `backend/agents/qa_refiner.py` with `MultiModelFallback` (`qwen/qwen3.8-27b` -> `llama-3.3-70b-versatile` -> `llama-3.1-8b-instant`).
   - Implement `MultiKeyFallback` supporting `GROQ_API_KEY_BIBLE`, `GROQ_API_KEY`, and `GROQ_API_KEY_COPILOT`.
   - Refactor `chat_interview` system prompt: mandate keyword reflection and forbid generic canned answers.
   - Implement deterministic keyword-based question fallback if all external API calls are unavailable.
   - Update `backend/tests/run_all_tests.py` to discover/register Round 5, Round 6, and new Round 7 suites.

2. **Frontend Team**:
   - Remove `<NeuralVisualPreview />` and its import from `frontend/src/components/landing/LandingView.tsx`.
   - Add "Khám phá Cộng đồng" CTA button in `LandingView.tsx` and wire `onExploreCommunity` in `page.tsx` (`setView("workspace")`, `setActiveTab("posts")`).
   - In `UnifiedIntakeChat.tsx`: replace `fixed sm:left-64` with centered layout; balance avatars and padding; align starter prompt cards.
   - In `UnifiedIntakeChat.tsx`: remove static repetitive error messages; add dynamic client fallback and retry button on failure.
   - In `Sidebar.tsx` and `i18n.ts`: rename "Bài đăng" tab to "Cộng đồng tác giả" / "Mạng xã hội" with `Users` or `Globe` icon.

3. **QA / Verification Team**:
   - Create `backend/tests/test_round7_chat_resilience.py` with the 15 specified test cases.
   - Execute the 7 quality gate checks listed in Section 6.
