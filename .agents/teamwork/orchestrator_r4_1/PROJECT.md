# Project: NarrAI Comprehensive Upgrade

## Architecture
- **Backend**:
  - `backend/services/ontology.py`: 3 Narrative Modes (`Chính Sử`, `Dã Sử`, `Hư Cấu Tự Do`), `HistoricalGroundingGatekeeper`, `TriTierOntologyResolver` (Tier 1 >=0.7, Tier 2 0.3-0.7, Tier 3 <0.3), `SmartSelectiveLanguageFilter`, and `extract_dynamic_ephemeral_node`.
  - `backend/services/banking_service.py`: 100 Coin economy, Absolute Server Authority, Dual-Locking Concurrency Isolation (in-memory per-user `threading.Lock` + SQLite `BEGIN IMMEDIATE TRANSACTION`), Compensating Transaction Rollback (`REFUND_FAILED_GENERATION`), SHA-256 chained cryptographic ledger, and Multi-Signal Anti-Clone Guard.
  - `backend/services/recommender_service.py`: 3-stage hybrid recommender (Stage 1 Two-Tower Cosine + DSGO graph traversal, Stage 2 Multi-Task Ranking score = 0.35*Cosine + 0.25*Implicit + 0.20*Freshness + 0.20*QualityScore, Stage 3 MMR diversity lambda=0.7 + Multi-Armed Bandit epsilon=0.15 cold-start exploration, exponential decay lambda=0.05/day, comment sentiment/entity extraction).
  - `backend/services/messenger_service.py`: Open Messenger directory search across all users, 1-1 conversation management, message persistence, unread status aggregation.
  - `backend/db/models.py`: User coins column with auto-migration, `coin_transactions`, `device_fingerprints`, `subnet_records`, `social_posts`, `post_interactions`, `user_interest_profiles`, `conversations`, `conversation_participants`, `chat_messages`.
  - `backend/routers/`: `coins_router.py`, `social_router.py`, `messenger_router.py`.
- **Frontend**:
  - `frontend/src/components/canvas/ThreeAmbientCanvas.tsx`: Layer 0 single shared WebGL context, Dong Son drum motif & particle field, `IntersectionObserver` + `visibilitychange` auto-pause to 0.0% CPU/GPU.
  - `frontend/src/components/cards/InteractiveTiltCard.tsx`: Layer 1 CSS 3D Transforms (`perspective: 1000px`, `transform-style: preserve-3d`) parallax tilt on cards & manga frames.
  - `frontend/src/components/morphicons/`: Layer 2 SVG morphing micro-interactions with spring physics on Like button, Coin badge/counter, and Model selector.
  - `frontend/src/components/portals/ClientPortal.tsx`: Layer 3 React Portals with `isolation: isolate` and z-index 50+ to eliminate z-fighting and blur clipping.
  - Graceful degradation detector for low-end hardware & `prefers-reduced-motion`.

## Code Layout & Write Ownership
- **Milestone 1 Worker**: Owns `backend/services/ontology.py`, `backend/agents/story_generator.py`, `backend/agents/comic_agent.py`, `backend/services/cloudflare_ai.py`, `backend/models/scene_graph.py`, `backend/agents/story_memory.py`.
- **Milestone 2 Worker**: Owns `backend/services/recommender_service.py`, `backend/services/messenger_service.py`, `backend/routers/social_router.py`, `backend/routers/messenger_router.py`.
- **Milestone 3 Worker**: Owns `backend/db/models.py`, `backend/services/banking_service.py`, `backend/routers/coins_router.py`, `backend/auth.py`, `backend/main.py` (coin middleware & registration integration).
- **Milestone 4 Worker**: Owns `frontend/src/components/canvas/`, `frontend/src/components/cards/`, `frontend/src/components/morphicons/`, `frontend/src/components/portals/`, `frontend/src/components/modals/`, `frontend/src/components/comic/ComicViewer.tsx`, `frontend/src/app/`.
- **E2E Testing Track / Test Writer**: Owns `backend/tests/` and test runner scripts.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | 3 Narrative Modes | Chính Sử, Dã Sử, Hư Cấu Tự Do with HistoricalGroundingGatekeeper | M1 | Survey 1 |
| 2 | Tri-Tier Ontology Resolver | Tier 1 Canonical VN (>=0.7), Tier 2 Hybrid (0.3-0.7), Tier 3 Open Domain (<0.3) | M1 | Survey 1 |
| 3 | Master Negative Cultural Filter | Negative prompt against Hanfu, Kimono, Hanbok, Samurai, Ninja in Tier 1 | M1 | Survey 1 |
| 4 | Dynamic Ephemeral Node Extraction | Contextual entity/space/era extraction for Tier 3 without feudal constraints | M1 | Survey 1 |
| 5 | Smart Selective Language Filter | Suppress Chinese translation clichés in pure VN; allow in Xianxia/Wuxia | M1 | Survey 1 |
| 6 | Social Data Models | `social_posts`, `post_interactions`, `user_interest_profiles` in `db/models.py` | M2 | Survey 2 |
| 7 | 3-Stage Hybrid Recommender | Two-Tower Cosine + DSGO traversal, Multi-Task Ranking, MMR lambda=0.7, MAB epsilon=0.15 | M2 | Survey 2 |
| 8 | Interaction Signals & Vector Decay | Weighted explicit/implicit signals (Dwell>60s, Scroll_100, Like, Comment) & lambda=0.05/day decay | M2 | Survey 2 |
| 9 | Open Messenger | Full directory search across all users, 1-1 chat, conversation management, unread status | M2 | Survey 2 |
| 10 | 100 Coin Economic Model & Server Authority | 8/12/16/2 coins pricing, server-authoritative calculations, client costs ignored | M3 | Survey 2 |
| 11 | Concurrency Isolation & Atomic Locks | In-memory thread mutex + SQLite BEGIN IMMEDIATE to eliminate double-spending (HTTP 402) | M3 | Survey 2 |
| 12 | Compensating Transaction Rollback | 100% refund (`REFUND_FAILED_GENERATION`) on AI generation timeout or 5xx | M3 | Survey 2 |
| 13 | Cryptographic Ledger | `coin_transactions` with chained SHA-256 hash (`tx_hash = SHA256(...)`) | M3 | Survey 2 |
| 14 | Multi-Signal Anti-Clone Guard | Canvas 2D + WebGL + Audio + Screen + IP /24 subnet throttling (8 coins fresh / 0 clone) | M3 | Survey 2 |
| 15 | Layer 0 Ambient 3D Canvas | Single shared WebGL context, Dong Son drum motif & particle field, auto-pause 0% CPU/GPU | M4 | Survey 3 |
| 16 | Layer 1 3D Interactive Cards | CSS 3D Transforms parallax tilt on cards and manga panels with isolated GPU compositor | M4 | Survey 3 |
| 17 | Layer 2 SVG Morphicons | SVG path interpolation & spring physics on Like, Coin, Model selector | M4 | Survey 3 |
| 18 | Layer 3 Glassmorphism Portals | React Portals to body with `isolation: isolate` and z-index 50+ to eliminate z-fighting | M4 | Survey 3 |
| 19 | Graceful Degradation | Auto-detect low-end hardware & prefers-reduced-motion to fallback cleanly | M4 | Survey 3 |
| 20 | E2E Testing Suite (Tiers 1-4) | Comprehensive test suite covering all features with Category-Partition, BVA, Pairwise | M5 & E2E Track | Survey 1, 2, 3 |
| 21 | System Integrity & Builds | Backend py_compile 0 errors, Frontend npm run build 0 errors, 100% tests pass | M5 | Survey 1, 2, 3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Adaptive Open-Ontology & 3 Narrative Modes | Features 1, 2, 3, 4, 5 | None | IN_PROGRESS (Conv: a8e1cd21) |
| M2 | Next-Gen Recommender Engine & Open Messenger | Features 6, 7, 8, 9 | M3 (for DB models) | PLANNED |
| M3 | Bank-Grade Currency, Atomic Locks & Anti-Clone | Features 10, 11, 12, 13, 14 | None | IN_PROGRESS (Conv: b0cbbf64) |
| M4 | Conflict-Free Layered Frontend | Features 15, 16, 17, 18, 19 | None | IN_PROGRESS (Conv: 0ebaf68e) |
| M5 | 100% E2E Verification & Adversarial Hardening | Features 20, 21 | M1, M2, M3, M4, E2E Track | PLANNED |
