## 2026-09-28T01:12:18Z
You are Worker M4 (teamwork_preview_worker).
Your working directory is: e:\NarrAI\.agents\teamwork\worker_m4_frontend\
The project root directory is: e:\NarrAI
You MUST first read the authoritative user request at:
e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md (especially section ## 2026-09-28T01:01:31Z).
Also read:
- `e:\NarrAI\.agents\teamwork\orchestrator_r4_1\PROJECT.md`
- `e:\NarrAI\.agents\teamwork\explorer_survey_3\report.md`
- `e:\NarrAI\.agents\teamwork\explorer_survey_3\handoff.md`

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write Ownership (Exclusive):
You own:
- `frontend/src/components/canvas/ThreeAmbientCanvas.tsx`
- `frontend/src/components/cards/InteractiveTiltCard.tsx`
- `frontend/src/components/morphicons/` (LikeButtonMorphicon.tsx, CoinBadgeMorphicon.tsx, ModelSelectorMorphicon.tsx, index.ts)
- `frontend/src/components/portals/ClientPortal.tsx`
- `frontend/src/components/modals/` (CoinTopupModal.tsx, MessengerModal.tsx, updating AuthModal.tsx / HistoryModal.tsx with ClientPortal)
- `frontend/src/components/comic/ComicViewer.tsx` (integrating InteractiveTiltCard)

Your Task (Milestone 4 — Conflict-Free Layered Frontend Pipeline):
1. Implement Layer 0: `frontend/src/components/canvas/ThreeAmbientCanvas.tsx`
   - Single shared WebGL canvas (`position: fixed; inset: 0; z-index: 0; pointer-events: none;`).
   - Native WebGL GLSL Shader engine (~12KB, zero external dependencies): procedural Dong Son drum motif & interactive floating particle field responsive to cursor.
   - Resource optimization: `IntersectionObserver` + `document.addEventListener('visibilitychange')` auto-pausing CPU/GPU to 0.0% when tab is hidden or canvas is out of viewport.
   - SSR safe (`typeof window !== 'undefined'`).
2. Implement Layer 1: `frontend/src/components/cards/InteractiveTiltCard.tsx`
   - CSS 3D Transforms (`perspective: 1000px`, `transform-style: preserve-3d`) with smooth parallax tilt on cursor hover.
   - Elevate content planes (`translateZ(30px)` on titles/buttons, `translateZ(48px)` on speech bubbles) on GPU compositor at stable 60 FPS.
   - Integrate into `frontend/src/components/comic/ComicViewer.tsx`.
3. Implement Layer 2: `frontend/src/components/morphicons/`
   - Zero-dependency spring physics using closed-form Euler damped harmonic oscillator ($F = -k\Delta x - cv$).
   - `LikeButtonMorphicon.tsx`: subtle heart stroke morphing into radiant filled heart with 8-ray micro-burst particle animation.
   - `CoinBadgeMorphicon.tsx`: spinning 3D coin morphing into balance counter badge.
   - `ModelSelectorMorphicon.tsx`: morphing between Flash (⚡), Versatile (🌟), and Master (👑).
4. Implement Layer 3: `frontend/src/components/portals/ClientPortal.tsx`
   - Mount modals via `createPortal(children, document.body)` with `isolation: isolate` and `z-index: 50+`.
   - Implement `CoinTopupModal.tsx` and `MessengerModal.tsx`.
   - Update `AuthModal.tsx` and `HistoryModal.tsx` to wrap inside `ClientPortal` to eliminate CSS 3D stacking context traps and blur clipping.
5. Graceful Degradation:
   - Auto-detect `prefers-reduced-motion` and low-end devices (`navigator.hardwareConcurrency <= 2`), falling back cleanly to pure CSS static styling.
6. Verify Next.js build compatibility:
   - Ensure all components are client components (`'use client';`) and build without errors.
7. Write your handoff report to `e:\NarrAI\.agents\teamwork\worker_m4_frontend\handoff.md` and send a completion message.
