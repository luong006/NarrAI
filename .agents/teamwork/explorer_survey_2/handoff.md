# Handoff Report — Explorer Survey 2: R2 (Recommender & Messenger) & R3 (Banking & Anti-Clone)
**Agent**: Explorer Survey 2 (`teamwork_preview_explorer`)  
**Target Recipient**: Orchestrator / Implementer Agents  
**Timestamp**: 2026-09-28T01:12:00Z  
**Handoff Type**: Hard (Task Complete)

---

## 1. Observation
1. **Database Schema & Models (`backend/db/models.py`)**:
   - `User` table (lines 8-19) contains only `id`, `username`, `full_name`, `password_hash`, `created_at`, and `stories` relationship. It lacks a `coins` balance column, credit transaction ledger, and social relationships.
   - `Story` table (lines 20-37) stores `bible_data` and `memory_data` as JSON text.
   - Database engine configuration (line 65): `engine = create_engine('sqlite:///narrai.db', connect_args={'check_same_thread': False})`.
   - Existing auto-migration block (lines 69-85) safely checks table columns using `inspect(engine)` and executes `ALTER TABLE` without corrupting existing records.
2. **Authentication & Security (`backend/auth.py` & `backend/main.py`)**:
   - `backend/auth.py` contains `validate_bank_password` (lines 47-70) and thread-safe `LoginRateLimiter` (lines 72-195).
   - `POST /api/register` in `backend/main.py` (lines 163-223) creates users with hashed passwords but does not collect device fingerprints or inspect IP `/24` subnets.
3. **Ontology Knowledge Base (`backend/models/scene_graph.py`)**:
   - `DynamicSceneGraph` (lines 447-805) contains `entities: Dict[str, CharacterEntity]`, `enclosures: Dict[str, SpaceEnclosure]`, `items: Dict[str, ItemEntity]`, and `relations: List[Dict[str, Any]]`.
   - `backend/agents/story_memory.py` (lines 280-300) serializes and deserializes `dynamic_scene_graph` to/from `Story.memory_data`.
4. **AI Generation Endpoints (`backend/main.py`)**:
   - `POST /api/generate-story` (lines 334-375): streams story content and saves `Story` if user is logged in. Currently 0 coin checks or deductions.
   - `POST /api/story/init` (lines 940-985): extracts Bible and streams Chapter 1. Currently 0 coin checks or deductions.
   - `POST /api/edit-text` (lines 321-333): edits text via `EditorAgent`. Currently 0 coin checks or deductions.
   - `POST /api/comics` (lines 595-635): creates comic adaptation and saves panels. Currently 0 coin checks or deductions.
   - In all these endpoints, if the underlying LLM/diffusion call fails, no compensating transaction or coin refund occurs.

---

## 2. Logic Chain
1. **From Observation 1**: Because `User` currently lacks `coins`, and SQLite is used via SQLAlchemy with `check_same_thread=False`, adding `coins = Column(Integer, default=0)` accompanied by the existing inspection-based auto-migration pattern (`ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0`) guarantees backward compatibility without breaking existing user data in `narrai.db`.
2. **From Observation 1 & 4**: Multiple simultaneous requests can read the same balance before deducting, causing race conditions and double-spending. Introducing a dual-locking architecture—(a) In-memory per-user `threading.Lock` to serialize threads within the Python process, and (b) SQLite `BEGIN IMMEDIATE` transaction to immediately acquire a write lock at the database engine level—strictly serializes concurrent deductions. If a user with 8 coins submits 2 requests at the exact same millisecond, request 1 reduces coins from 8 to 0, and request 2 reads balance = 0, immediately triggering `HTTPException(status_code=402, detail="Số dư xu không đủ...")`.
3. **From Observation 4**: In generative AI systems, network interruptions, 5xx errors, and timeouts frequently occur after coin deduction. Implementing a Compensating Transaction pattern (`REFUND_FAILED_GENERATION`) wrapped around the external AI calls ensures that whenever an exception occurs during streaming or script generation, the exact deducted amount is atomically credited back and appended to the cryptographic ledger.
4. **From Observation 1**: To implement tamper-evident banking integrity, `coin_transactions` must store a blockchain-style hash chain:
   $$tx\_hash = \text{SHA256}(prev\_hash + str(user\_id) + str(amount) + str(balance\_after) + timestamp)$$
   Any manual row tampering or balance edits directly inside `narrai.db` will break the hash link, detected by the ledger integrity auditor.
5. **From Observation 2**: Sybil and bot clone attacks exploit initial trial bonuses. Combining Canvas 2D + WebGL + AudioContext + Screen Specs into a composite SHA-256 fingerprint together with `/24` subnet throttling ensures genuine new users receive 8 free coins, while duplicate devices or subnet-throttled bots receive 0 coins (`initial_coins = 0`).
6. **From Observation 3**: Because `Story.memory_data` already preserves `DynamicSceneGraph` with characters (`CharacterEntity`) and environments (`SpaceEnclosure`), published `SocialPost` records can store indexed lists of `dsgo_entities` and `dsgo_spaces`. This enables Stage 1 candidate generation to traverse the DSGO ontology graph and discover thematically and lore-linked stories across different authors.
7. **From Observation 1 & R2 Requirements**: A 3-Stage Recommender combining Content Cosine similarity (128-dim concept vectors with exponential decay $\lambda = 0.05/\text{day}$), Multi-Task Ranking ($0.35 \times \text{Cosine} + 0.25 \times \text{Affinity} + 0.20 \times \text{Freshness} + 0.20 \times \text{Quality}$), and Stage 3 Re-ranking (MMR $\lambda = 0.7$ for genre diversity + Multi-Armed Bandit $\epsilon = 0.15$ Thompson Sampling for cold-start exploration) prevents echo-chambers and ensures exposure for new creators.
8. **From Observation 1 & R2 Requirements**: An Open Messenger architecture requiring user directory search across ALL users, idempotent 1-1 conversation creation, message persistence, and unread count aggregations completes the literary social ecosystem.

---

## 3. Caveats
1. **Network Sandbox & Test Execution**: In this explorer subagent session, interactive terminal execution (`run_command`) timed out waiting for user approval. Static codebase inspection and model analysis were performed instead.
2. **Single SQLite Database File**: While `BEGIN IMMEDIATE` ensures serialization on a single SQLite database, multi-node clustered deployments would require PostgreSQL `SELECT ... FOR UPDATE` or Redis distributed locks (`Redlock`). For the current architecture, SQLite `BEGIN IMMEDIATE` with WAL mode and `busy_timeout=5000` is completely robust and standard.
3. **Client Fingerprint Availability**: Browsers with strict privacy extensions or non-standard webview environments might block Canvas or AudioContext extraction. The anti-clone service must gracefully handle missing/fallback parameters by generating a fallback hash without crashing.

---

## 4. Conclusion
1. **Readiness**: The codebase has solid foundations (DSGO models, cache service, clean auth, auto-migration mechanisms) that make implementing R2 and R3 straightforward and elegant.
2. **Modular Architecture**: R2 and R3 should be isolated into dedicated services (`banking_service.py`, `recommender_service.py`, `messenger_service.py`) and routers (`coins_router.py`, `social_router.py`, `messenger_router.py`) to keep `main.py` clean.
3. **Execution Plan**:
   - Update `backend/db/models.py` with `coins` column, auto-migration, and tables `coin_transactions`, `device_fingerprints`, `subnet_records`, `social_posts`, `post_interactions`, `user_interest_profiles`, `conversations`, `conversation_participants`, `chat_messages`.
   - Implement `backend/services/banking_service.py` with dual-locking, pricing authority, SHA-256 chained ledger, compensating transaction rollback, and anti-clone guard.
   - Implement `backend/services/recommender_service.py` with 3-stage pipeline (Cosine + DSGO traversal, Multi-task ranking, MMR $\lambda=0.7$, MAB $\epsilon=0.15$, vector decay $\lambda=0.05/\text{day}$, sentiment/entity comment extraction).
   - Implement `backend/services/messenger_service.py` with user directory search, 1-1 conversation management, messaging, unread counts.
   - Expose routers and hook coin deduction into existing AI routes in `backend/main.py`.
   - Create test suites: `test_banking_concurrency.py`, `test_recommender_engine.py`, `test_open_messenger.py`.

---

## 5. Verification Method
1. **Inspect Survey Report**:
   - Read `e:\NarrAI\.agents\teamwork\explorer_survey_2\report.md` for complete mathematical formulas, schema definitions, and implementation guides.
2. **Static Code Verification**:
   - Check `backend/db/models.py` line 69-85 for the auto-migration pattern.
   - Check `backend/models/scene_graph.py` line 447 for `DynamicSceneGraph` structure.
   - Check `backend/auth.py` line 47-195 for bank-grade password and rate limiter patterns.
3. **Target Test Commands (for Implementer/Verifier)**:
   - Banking & Concurrency: `python -m unittest backend/tests/test_banking_concurrency.py`
   - Recommender: `python -m unittest backend/tests/test_recommender_engine.py`
   - Messenger: `python -m unittest backend/tests/test_open_messenger.py`
   - Existing suite regression: `python -m unittest discover -s backend/tests -p "test_*.py"`
   - Backend syntax check: `python -m py_compile backend/main.py backend/services/banking_service.py backend/services/recommender_service.py backend/services/messenger_service.py`
