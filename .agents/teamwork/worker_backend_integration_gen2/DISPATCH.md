## 2026-09-28T13:50:17Z
You are worker_backend_integration_gen2, a teamwork_preview_worker.
Your working directory is: e:\NarrAI\.agents\teamwork\worker_backend_integration_gen2\
Project root: e:\NarrAI

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY: You MUST read e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md before starting work.
Also inspect reference reports:
- e:\NarrAI\.agents\teamwork\orchestrator_r4_1\PROJECT.md
- e:\NarrAI\.agents\teamwork\challenger_banking\handoff.md
- e:\NarrAI\.agents\teamwork\challenger_narrative\handoff.md
- e:\NarrAI\.agents\teamwork\orchestrator_r4_1\GATE_STATUS.md

SCOPE & RESPONSIBILITY (Exclusive write ownership of backend/):
1. In `backend/main.py`:
   - Import and mount `coins_router`: `from routers.coins_router import router as coins_router` -> `app.include_router(coins_router, prefix="/api/coins", tags=["Coins"])`.
   - Import and mount `social_router`: `from routers.social_router import router as social_router` -> `app.include_router(social_router, prefix="/api/social", tags=["Social"])` (check existing prefix in router).
   - Import and mount `messenger_router`: `from routers.messenger_router import router as messenger_router` -> `app.include_router(messenger_router, prefix="/api/messenger", tags=["Messenger"])` (check existing prefix in router).
   - Wire coin deductions and compensating rollback (`refund_coins` with `REFUND_FAILED_GENERATION`) into story generation / edit endpoints in `backend/main.py`.
   - In `/api/register` endpoint in `backend/main.py`, ensure device fingerprint registration / initial trial coins grant logic is integrated.
2. In `backend/services/ontology.py`:
   - Apply regex hardening recommended by challenger_narrative:
     - In `HistoricalGroundingGatekeeper`, ensure `defeat_regex` and `BATTLE_OUTCOME_DISTORTION_PATTERNS` regexes handle multiline breaks cleanly (`(?s)` or `re.DOTALL`).
     - In `TRANSLATION_CLICHE_BANLIST`, replace literal spaces with `\s+` (e.g., `r"tiêu\s+sái"`, etc.) so whitespace variations cannot evade detection.
3. System & Test Verification:
   - Run python compilation syntax check: `python -m py_compile backend/main.py backend/services/*.py backend/routers/*.py backend/db/*.py`
   - Run unified test runner: `python backend/tests/run_all_tests.py`
   - Run all test suites:
     - `python -m unittest backend/tests/test_e2e_ontology_modes.py`
     - `python -m unittest backend/tests/test_e2e_banking_security.py`
     - `python -m unittest backend/tests/test_e2e_recommender_messenger.py`
     - `python -m unittest backend/tests/test_banking_adversarial_empirical.py`
     - `python -m unittest backend/tests/test_adversarial_narrative_recommender.py`
   - Ensure 100% of tests pass without any errors or regressions.
4. Document all file changes, commands executed, and full test outputs in `e:\NarrAI\.agents\teamwork\worker_backend_integration_gen2\handoff.md`.
5. Send a completion message via send_message to your caller when done.
