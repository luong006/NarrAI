## 2026-09-28T01:04:17Z

You are the Project Orchestrator for the comprehensive upgrade of NarrAI.

Your working directory is: e:\NarrAI\.agents\teamwork\orchestrator_r4_1\
The project root directory is: e:\NarrAI
The authoritative user request is recorded in: e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md (under ## 2026-09-28T01:01:31Z).

You must manage the team to deliver the full scope of requirements and achieve 100% of the acceptance criteria:

1. R1: Sáng Tác Linh Động — Adaptive Open-Ontology, Phân Ranh Lịch Sử Chuẩn & Hư Cấu Cá Nhân:
   - 3 Chế độ sáng tác: Chính Sử (Historical Grounding Gatekeeper, strictly authentic), Dã Sử (Historical Fiction / Alternative Lens, historical era/spirit anchored with personal protagonist/fictional events), Hư Cấu Tự Do (Free Personal Fiction, 100% semantic relaxation).
   - Tri-Tier Ontology Resolver: Tier 1 Canonical Vietnamese (similarity >= 0.7, full Vietnamese honorifics, cultural entities, Comic Visual DNA, master negative filter against Hanfu/Kimono/Samurai/etc.), Tier 2 Cultural Fusion/Hybrid (0.3 <= similarity < 0.7, preserve core Vietnamese essence with relaxed era constraints for sci-fi/steampunk/cyberpunk), Tier 3 Open-Domain Adaptive Graph (similarity < 0.3, disable feudal Vietnamese filters, no forced traditional attire, dynamic ephemeral node extraction).
   - Smart Selective Language Filter (suppress awkward translation clichés like "tiêu sái", "tà mị" for pure Vietnamese/serious prose, allow if user selects xianxia/wuxia).

2. R2: Next-Gen Recommendation Engine & Open Messenger:
   - Data models in db/models.py: `social_posts`, `post_interactions` (explicit & implicit signals: dwell > 60s w=2.5, scroll_100 w=2.0, like w=1.5, comment w=3.0), `user_interest_profiles` (dynamic vector with exponential time decay lambda=0.05/day, sentiment & entity extraction from comments).
   - 3-Stage Hybrid Recommender: Candidate Generation (Content Cosine + Graph DSGO traversal), Scoring & Multi-Task Ranking (Cosine, Implicit affinity, Freshness, QualityScore), Re-ranking (MMR diversity lambda=0.7, Multi-Armed Bandit Thompson Sampling / epsilon-greedy epsilon=0.15 for cold-start).
   - Open Messenger: User directory search, 1-1 chat between ANY users, conversation management, unread status and notifications.

3. R3: Tiền Tệ Chuẩn Ngân Hàng & Chống Tấn Công Trục Lợi:
   - 100 Coin economic model (8 / 12 / 16 / 2 coins).
   - Atomic Transaction & Thread Mutex / SQLite IMMEDIATE TRANSACTION to eliminate Race Condition & Double-Spending (reject concurrent request with HTTP 402 if balance insufficient).
   - Absolute Server Authority over pricing and coin deduction (never trust client coins).
   - Compensating Transaction Rollback (REFUND_FAILED_GENERATION) if AI generation encounters 5xx or timeout.
   - Cryptographic Ledger: `coin_transactions` with chained SHA-256 hash (tx_hash = SHA256(prev_hash + user_id + amount + balance_after + timestamp)).
   - Multi-Signal Anti-Clone Guard (Canvas 2D + WebGL + AudioContext + Screen Specs + IP /24 Subnet throttling; initial 8 free coins only for fresh device/subnet, 0 coins for clones).

4. R4: Kiến Trúc Frontend Phân Lớp Không Xung Đột (ThreeUI 3D + Morphicons):
   - Layer 0 Ambient 3D Canvas (ThreeUI): Single shared WebGL context, IntersectionObserver + tab hidden auto-pause to 0% GPU/CPU, Dong Son drum motif & particle field.
   - Layer 1 Core Semantic DOM & 3D Interactive Cards: CSS 3D Transforms parallax tilt on cards & manga frames.
   - Layer 2 SVG Morphing Micro-Interactions (Morphicons): SVG path interpolation & spring physics on Like button, Coin badge/counter, Model selector (Flash/Versatile/Master).
   - Layer 3 Glassmorphism Overlay & Portals: Coin top-up modal, Messenger dialog, Copilot mounted via React Portals with `isolation: isolate` and z-index 50+ to eliminate z-fighting and blur clipping.
   - Graceful degradation for low-end hardware & prefers-reduced-motion.

5. System Integrity & Automated Testing:
   - Full Python backend py_compile clean (0 errors).
   - Frontend Next.js build clean (npm run build 0 errors).
   - Comprehensive test suite for OOD ontology, banking security & atomic locks, recommendation engine, open messenger, passing 100%.

## 2026-09-28T06:20:07Z

Sentinel Liveness Check: Please update your progress.md with the latest milestone progress (worker_m3_banking and worker_m4_frontend have delivered handoffs, worker_m1 and worker_m2 are progressing). Keep up the great work!
