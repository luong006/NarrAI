# Execution Plan — orchestrator_r7_1

## Objective
Lead the team to resolve all 5 requirements (R1 - R5) per ORIGINAL_REQUEST.md (2026-10-05T05:28:19Z):
- R1: Remove "Neural Style Laboratory" (<NeuralVisualPreview />) from Landing Page.
- R2: Symmetrical layout & centered input dock for UnifiedIntakeChat.
- R3: AI Chat resilience (Multi-Model & Multi-Key fallback in backend, keyword-based follow-up questions, client error UI & dynamic fallback).
- R4: Social / Community visibility (Sidebar rename, Landing Page CTA, verify full community features).
- R5: Full flow verification, 100% 182+ backend tests pass, frontend npm run build pass.

## Phase 0: Survey & Codebase Mapping (Parallel Explorers)
- **explorer_r7_frontend**: Inspect LandingView.tsx, NeuralVisualPreview, UnifiedIntakeChat.tsx, Sidebar, Community tabs.
- **explorer_r7_backend**: Inspect qa_refiner.py, main.py, model fallback chains, API key fallback, system prompt, api.ts error handling.
- **explorer_r7_system_qa**: Inspect test suites (run_all_tests.py, test_round5, etc.), frontend build script, and end-to-end integration points.

## Phase 1: Milestone Decomposition & Work Orders
- **Milestone 1 (M1 - Frontend UI/UX)**:
  - Worker: worker_r7_frontend (R1, R2, R4)
  - Tasks: Remove NeuralVisualPreview in LandingView; re-align UnifiedIntakeChat (flex/sticky centered dock, symmetric bubbles); update Sidebar navigation tab & Landing Page CTA.
- **Milestone 2 (M2 - AI Resilience & Prompting)**:
  - Worker: worker_r7_backend (R3 Backend & Frontend Dynamic Fallback)
  - Tasks: Implement Multi-Model & Multi-Key fallback in qa_refiner.py and main.py; update system prompt for deep follow-up questions; update UnifiedIntakeChat and api.ts with connection retry UI and keyword-based client fallback.
- **Milestone 3 (M3 - System Integration & Quality Gates)**:
  - Workers / Reviewers / Challengers / Forensic Auditor
  - Tasks: Verify all 182+ backend tests pass; verify frontend build passes cleanly; empirical challenge on AI chat fallback & layout; forensic audit for authentic implementation (no hardcoded cheats).

## Phase 2: Review, Challenge & Forensic Verification Gates
- 2 Reviewers: reviewer_r7_frontend, reviewer_r7_backend
- 2 Challengers: challenger_r7_ai, challenger_r7_e2e
- 1 Forensic Auditor: auditor_r7_integrity

## Phase 3: Final Acceptance & Victory Reporting
- Confirm all 5 requirements pass acceptance criteria.
- Report victory to Sentinel.
