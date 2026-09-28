## 2026-09-28T01:05:15Z

You are Explorer Survey 2 (teamwork_preview_explorer).
Your working directory is: e:\NarrAI\.agents\teamwork\explorer_survey_2\
The project root directory is: e:\NarrAI
You MUST first read the authoritative user request at:
e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md (especially section ## 2026-09-28T01:01:31Z).

Your objective:
Conduct an in-depth codebase survey for Requirement 2 (R2) and Requirement 3 (R3):
1. R2: Next-Gen Recommendation Engine & Open Messenger:
   - Data models in db/models.py: `social_posts`, `post_interactions` (explicit & implicit signals: dwell > 60s w=2.5, scroll_100 w=2.0, like w=1.5, comment w=3.0), `user_interest_profiles` (dynamic vector with exponential time decay lambda=0.05/day, sentiment & entity extraction from comments).
   - 3-Stage Hybrid Recommender: Candidate Generation (Content Cosine + Graph DSGO traversal), Scoring & Multi-Task Ranking (Cosine, Implicit affinity, Freshness, QualityScore), Re-ranking (MMR diversity lambda=0.7, Multi-Armed Bandit Thompson Sampling / epsilon-greedy epsilon=0.15 for cold-start).
   - Open Messenger: User directory search, 1-1 chat between ANY users, conversation management, unread status and notifications.
2. R3: Tiền Tệ Chuẩn Ngân Hàng & Chống Tấn Công Trục Lợi:
   - 100 Coin economic model (8 / 12 / 16 / 2 coins).
   - Atomic Transaction & Thread Mutex / SQLite IMMEDIATE TRANSACTION to eliminate Race Condition & Double-Spending (reject concurrent request with HTTP 402 if balance insufficient).
   - Absolute Server Authority over pricing and coin deduction (never trust client coins).
   - Compensating Transaction Rollback (REFUND_FAILED_GENERATION) if AI generation encounters 5xx or timeout.
   - Cryptographic Ledger: `coin_transactions` with chained SHA-256 hash (tx_hash = SHA256(prev_hash + user_id + amount + balance_after + timestamp)).
   - Multi-Signal Anti-Clone Guard (Canvas 2D + WebGL + AudioContext + Screen Specs + IP /24 Subnet throttling; initial 8 free coins only for fresh device/subnet, 0 coins for clones).

Investigate:
- Existing database schema in db/models.py, db/database.py, migrations/init scripts.
- Existing credit/coin system, auth endpoints, social or feed endpoints, and transaction logic.
- Concurrency mechanisms, database locking in SQLite/SQLAlchemy, and transaction atomicity.
- How to structure the backend routes, services, schemas, and tests for both R2 and R3.

Deliverables:
- Write your comprehensive findings to e:\NarrAI\.agents\teamwork\explorer_survey_2\report.md.
- Write your handoff report to e:\NarrAI\.agents\teamwork\explorer_survey_2\handoff.md.
- Keep e:\NarrAI\.agents\teamwork\explorer_survey_2\progress.md updated.
- When finished, send a completion message back with the key findings and file paths.
