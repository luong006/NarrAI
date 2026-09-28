## 2026-09-28T13:45:36Z
You are the Backend Integration Worker (teamwork_preview_worker).
Your working directory is: e:\NarrAI\.agents\teamwork\worker_backend_integration\
The project root directory is: e:\NarrAI
You MUST first read the authoritative user request at:
e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md (especially section ## 2026-09-28T01:01:31Z).
Also read:
- `e:\NarrAI\.agents\teamwork\challenger_banking\handoff.md`
- `e:\NarrAI\.agents\teamwork\challenger_narrative\handoff.md`
- `e:\NarrAI\.agents\teamwork\worker_m3_banking\handoff.md`
- `e:\NarrAI\.agents\teamwork\worker_m2_social\handoff.md`

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write Ownership (Exclusive):
You own:
- `backend/main.py`
- `backend/services/ontology.py`

Your Task:
Complete the backend integration across all milestones:
1. In `backend/main.py`:
   - Import `coins_router`, `social_router`, `messenger_router` and mount them:
     - `app.include_router(coins_router.router, prefix="/api/coins", tags=["Coins"])`
     - `app.include_router(social_router.router, prefix="/api/social", tags=["Social"])`
     - `app.include_router(messenger_router.router, prefix="/api/messenger", tags=["Messenger"])`
   - Wire coin deductions into story generation endpoints:
     - In `/api/generate-story`, `/api/story/init`, `/api/edit-text`: derive cost using `banking_service.get_story_cost()` or `get_action_cost()`. Deduct coins atomically with `banking_service.deduct_coins()`. Reject with 402 if balance insufficient. If external AI call fails with 5xx or timeout, call `banking_service.refund_coins(db, user_id, cost, reason="REFUND_FAILED_GENERATION")`.
   - In `/api/register`:
     - Inspect request headers for device fingerprint and client IP; call `banking_service.register_device_and_get_initial_coins()`, granting 8 trial coins for new device/subnet and 0 for duplicates/clones.
2. In `backend/services/ontology.py`:
   - Apply regex hardening `(?s)` and `\s+` to `HistoricalGroundingGatekeeper` patterns and `TRANSLATION_CLICHE_BANLIST` as recommended by Challenger Narrative.
3. Verify:
   - Run compilation: `python -m py_compile backend/main.py backend/services/ontology.py`
   - Run unified tests: `python backend/tests/run_all_tests.py` and document results.
4. Write handoff report to `e:\NarrAI\.agents\teamwork\worker_backend_integration\handoff.md` and send a completion message.
