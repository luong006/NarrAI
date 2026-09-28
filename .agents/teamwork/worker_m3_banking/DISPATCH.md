## 2026-09-28T01:12:18Z
You are Worker M3 (teamwork_preview_worker).
Your working directory is: e:\NarrAI\.agents\teamwork\worker_m3_banking\
The project root directory is: e:\NarrAI
You MUST first read the authoritative user request at:
e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md (especially section ## 2026-09-28T01:01:31Z).
Also read:
- `e:\NarrAI\.agents\teamwork\orchestrator_r4_1\PROJECT.md`
- `e:\NarrAI\.agents\teamwork\explorer_survey_2\report.md`
- `e:\NarrAI\.agents\teamwork\explorer_survey_2\handoff.md`

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write Ownership (Exclusive):
You own:
- `backend/db/models.py`
- `backend/services/banking_service.py`
- `backend/routers/coins_router.py`

Your Task (Milestone 3 + Foundation Database Models):
1. In `backend/db/models.py`:
   - Add `coins = Column(Integer, default=0)` to `User` model, with safe auto-migration (`ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0`).
   - Implement `CoinTransaction` with fields: `id`, `user_id`, `amount`, `balance_after`, `action_type`, `description`, `tx_hash`, `prev_hash`, `timestamp`.
   - Implement `DeviceFingerprint` and `SubnetRecord` for anti-clone tracking.
   - Implement social models needed for M2: `SocialPost` (including `concept_vector`, `dsgo_entities`, `dsgo_spaces`, `completion_count`, `likes_count`, `views_count`), `PostInteraction` (`interaction_type`, `dwell_seconds`, `scroll_depth`), `UserInterestProfile` (`interest_vector`, `last_decay_time`), `Conversation`, `ConversationParticipant`, `ChatMessage`.
2. In `backend/services/banking_service.py`:
   - 100 Coin economic model pricing constants: Short story = 8, Medium = 12, Long = 16, Edit = 2, Manga = 16.
   - Dual-locking concurrency isolation: in-memory per-user `threading.Lock` + SQLite `BEGIN IMMEDIATE TRANSACTION` ensuring zero double-spending. If balance < required, reject with HTTP 402 Payment Required.
   - Absolute Server Authority: derive cost on server, never trust client-supplied amounts.
   - Compensating Transaction Rollback (`REFUND_FAILED_GENERATION`): 100% refund on failure.
   - Cryptographic Ledger: SHA-256 chained hash `tx_hash = SHA256(prev_hash + str(user_id) + str(amount) + str(balance_after) + timestamp)`. Include `verify_ledger_integrity(db, user_id)`.
   - Multi-Signal Anti-Clone Guard: composite fingerprint (Canvas 2D + WebGL + AudioContext + Screen Specs) + IP /24 subnet throttling. Fresh device & subnet = 8 free coins; duplicate device or throttled subnet = 0 coins.
3. In `backend/routers/coins_router.py`:
   - Endpoints: `GET /balance`, `GET /transactions`, `POST /verify-ledger`, `POST /claim-trial`, `POST /topup`.
4. Verify by running `python -m py_compile backend/db/models.py backend/services/banking_service.py backend/routers/coins_router.py` and document results.
5. Write your handoff report to `e:\NarrAI\.agents\teamwork\worker_m3_banking\handoff.md` and send a completion message.
