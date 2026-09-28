## 2026-09-28T13:45:36Z

You are the Frontend Integration Worker (teamwork_preview_worker).
Your working directory is: e:\NarrAI\.agents\teamwork\worker_frontend_integration\
The project root directory is: e:\NarrAI
You MUST first read the authoritative user request at:
e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md (especially section ## 2026-09-28T01:01:31Z).
Also read:
- `e:\NarrAI\.agents\teamwork\reviewer_frontend\handoff.md` (which details the exact mounting locations and code snippets)
- `e:\NarrAI\.agents\teamwork\worker_m4_frontend\handoff.md`

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write Ownership (Exclusive):
You own:
- `frontend/src/app/layout.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/app/page.tsx`

Your Task:
Complete the UI integration of Milestone 4 components based on the Reviewer's findings:
1. In `frontend/src/app/layout.tsx`:
   - Import `ThreeAmbientCanvas` from `@/components/canvas/ThreeAmbientCanvas` and mount it as a background canvas (e.g. right inside `<body>`, before `{children}`).
2. In `frontend/src/components/layout/Sidebar.tsx`:
   - Import `CoinBadgeMorphicon` from `@/components/morphicons` and display the live coin counter/badge. Clicking it opens the `CoinTopupModal`.
   - Add a Messenger icon/button to open `MessengerModal`.
3. In `frontend/src/app/page.tsx`:
   - Add state for `isTopupOpen` and `isMessengerOpen`.
   - Render `<CoinTopupModal isOpen={isTopupOpen} onClose={() => setIsTopupOpen(false)} />` and `<MessengerModal isOpen={isMessengerOpen} onClose={() => setIsMessengerOpen(false)} />`.
   - Wire `<ModelSelectorMorphicon />` into the story setup/mode selector area.
4. Verify TypeScript and Next.js compatibility:
   - Ensure all imports and JSX are clean and valid.
5. Write your handoff report to `e:\NarrAI\.agents\teamwork\worker_frontend_integration\handoff.md` and send a completion message.
