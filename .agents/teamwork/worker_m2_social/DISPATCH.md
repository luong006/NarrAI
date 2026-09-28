## 2026-09-28T06:02:40Z
You are Worker M2 (teamwork_preview_worker).
Your working directory is: e:\NarrAI\.agents\teamwork\worker_m2_social\
The project root directory is: e:\NarrAI
You MUST first read the authoritative user request at:
e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md (especially section ## 2026-09-28T01:01:31Z).
Also read:
- `e:\NarrAI\.agents\teamwork\orchestrator_r4_1\PROJECT.md`
- `e:\NarrAI\.agents\teamwork\explorer_survey_2\report.md`
- `e:\NarrAI\.agents\teamwork\worker_m3_banking\handoff.md` (which documents the newly implemented database models in `backend/db/models.py`)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write Ownership (Exclusive):
You own:
- `backend/services/recommender_service.py`
- `backend/services/messenger_service.py`
- `backend/routers/social_router.py`
- `backend/routers/messenger_router.py`

Your Task (Milestone 2 — Next-Gen Recommendation Engine & Open Messenger):
1. In `backend/services/recommender_service.py`:
   - Implement the 3-Stage Hybrid Recommender System:
     - Stage 1: Candidate Generation: Two-Tower Content Cosine Similarity (User Interest Vector vs Post Concept Vector) + Graph-Based DSGO Traversal (querying stories sharing common characters or space enclosures from `dsgo_entities` and `dsgo_spaces` in `SocialPost`).
     - Stage 2: Scoring & Multi-Task Ranking:
       $Score(p, u) = 0.35 \times CosineSim(U_u, V_p) + 0.25 \times ImplicitAffinity(u, p) + 0.20 \times Freshness(p) + 0.20 \times QualityScore(p)$
       with signal weights: w(Dwell > 60s) = 2.5, w(Scroll_100) = 2.0, w(Like) = 1.5, w(Comment) = 3.0.
       QualityScore based on completion count and interactions.
     - Stage 3: Re-ranking, Serendipity & Exploration:
       - Maximal Marginal Relevance (MMR) with $\lambda = 0.7$ for genre/topic diversity, preventing echo-chambers.
       - Multi-Armed Bandit (Thompson Sampling / $\epsilon$-greedy $\epsilon=0.15$) reserving 15% of feed slots for cold-start exploration of newly published works.
   - Dynamic User Interest Vector update with exponential decay $\lambda = 0.05/\text{day}$.
   - Sentiment & Entity extraction from comments to update `user_interest_profiles`.
2. In `backend/services/messenger_service.py`:
   - Open Messenger:
     - User directory search across ALL users (by username or full_name).
     - 1-1 conversation management (idempotent get or create between any two users).
     - Send and receive messages with real-time persistence in SQLite.
     - Read status tracking (`is_read`, `last_read_message_id`) and unread count aggregation.
3. In `backend/routers/social_router.py`:
   - Endpoints: `GET /feed`, `POST /publish`, `POST /interact`, `GET /post/{post_id}`.
4. In `backend/routers/messenger_router.py`:
   - Endpoints: `GET /users`, `GET /conversations`, `POST /conversations`, `GET /conversations/{id}/messages`, `POST /conversations/{id}/messages`, `GET /unread-count`.
5. Verify changes with `python -m py_compile` across all created files and document results.
6. Write handoff report to `e:\NarrAI\.agents\teamwork\worker_m2_social\handoff.md` and send a completion message.
