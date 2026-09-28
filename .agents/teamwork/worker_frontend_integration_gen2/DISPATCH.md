## 2026-09-28T13:50:17Z
You are worker_frontend_integration_gen2, a teamwork_preview_worker.
Your working directory is: e:\NarrAI\.agents\teamwork\worker_frontend_integration_gen2\
Project root: e:\NarrAI

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY: You MUST read e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md before starting work.
Also inspect reference reports:
- e:\NarrAI\.agents\teamwork\orchestrator_r4_1\PROJECT.md
- e:\NarrAI\.agents\teamwork\reviewer_frontend\handoff.md
- e:\NarrAI\.agents\teamwork\worker_m4_frontend\handoff.md
- e:\NarrAI\.agents\teamwork\orchestrator_r4_1\GATE_STATUS.md

SCOPE & RESPONSIBILITY (Exclusive write ownership of frontend/):
1. In `frontend/src/app/layout.tsx` (and/or `frontend/src/app/page.tsx`):
   - Mount Layer 0 `<ThreeAmbientCanvas />` inside `<ThemeProvider>` so the 3D ambient WebGL background (Dong Son drum motifs and particles) renders seamlessly.
2. In `frontend/src/components/layout/Sidebar.tsx`:
   - Mount `<CoinBadgeMorphicon />` to display user coin balance and trigger the coin top-up modal.
   - Add Open Messenger trigger button (with chat icon / unread indicator) to trigger opening the messenger modal.
3. In `frontend/src/app/page.tsx`:
   - Add state management for `isCoinModalOpen` and `isMessengerOpen`.
   - Mount `<CoinTopupModal isOpen={isCoinModalOpen} onClose={() => setIsCoinModalOpen(false)} />` and `<MessengerModal isOpen={isMessengerOpen} onClose={() => setIsMessengerOpen(false)} />` (wrapped in `ClientPortal` with `zIndex={60}` and `isolation: isolate`).
   - Ensure Layer 1 (`InteractiveTiltCard`) and Layer 2 Morphicons (`LikeButtonMorphicon`, `ModelSelectorMorphicon`) are properly accessible and wired.
4. In `frontend/src/components/setup/Phase3Controls.tsx` (or `AICopilotPanel.tsx`):
   - Mount `<ModelSelectorMorphicon />` in the model selection UI.
5. In `frontend/src/components/morphicons/LikeButtonMorphicon.tsx`:
   - Cancel ongoing `burstRafRef` on rapid clicks before starting a new burst.
6. In `frontend/src/components/portals/ClientPortal.tsx`:
   - In the `useEffect` cleanup function, ensure `portalRootRef.current = null;`.
7. Production Build Verification:
   - In `frontend`, run `npm run build`.
   - Ensure Next.js production build / static export succeeds cleanly with 0 errors and 0 type errors.
   - If any errors or type mismatches occur, fix them cleanly.
8. Document all file changes, commands executed, and full build output in `e:\NarrAI\.agents\teamwork\worker_frontend_integration_gen2\handoff.md`.
9. Send a completion message via send_message to your caller when done.
