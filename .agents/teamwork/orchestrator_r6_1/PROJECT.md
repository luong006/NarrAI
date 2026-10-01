# Project: NarrAI Round 6 Comprehensive Upgrade

## Architecture
NarrAI is an AI-powered literary creation and social platform featuring:
- **Backend**: FastAPI with SQLite (WAL mode), SQLAlchemy ORM, Multi-agent LLM pipelines (StoryGenerator, CopilotAgent, ComicAgent, QARefiner), Adaptive Open-Ontology with 31-Hero Vietnamese Historical Canon & AI Semantic Classifier, Recommendation & Social Services, and TensorFlow.js Model/Vector Export APIs.
- **Frontend**: Next.js 14 (App Router, static export `output: 'export'`), React 18, Tailwind CSS, Layered Visual Pipeline (Layer 0: WebGL ThreeAmbientCanvas, Layer 1: Semantic DOM 3D Cards, Layer 2: Morphicons SVG Spring Physics, Layer 3: Glassmorphism Modals & Portals), on-device TensorFlow.js Lite recommendation re-ranking & IndexedDB cache.
- **Data & Concurrency**: SQLite with `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`, Thread-safe Mutex + Database Transaction locking for banking/coins, Comprehensive single & composite indexes.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Copilot Frontend Selection | Pass `selectedText` & DOM caret `cursorPosition` from `StoryEditor.tsx` & `page.tsx` to Copilot | M1 | Survey 1 |
| 2 | Copilot Chapter Targeting | Parse "sửa Chương X" via regex in `SemanticChunkSlicer` & slice targeted chapter | M1 | Survey 1 |
| 3 | Slicer Instruction Utilization | Extract targeting/position info from `instruction` parameter in `slice_manuscript` | M1 | Survey 1 |
| 4 | Copilot Path B Fallback Fix | Eliminate 2000-char whole-manuscript overwrite; safely merge or re-route to Path A | M1 | Survey 1 |
| 5 | Heading Intermediate Preservation | Place intermediate `## Chương X` titles at proportional paragraph offsets, not top | M1 | Survey 1 |
| 6 | SQLite WAL Mode Activation | Set `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;` on engine connect | M1 | Survey 1 |
| 7 | Performance DB Indexing | Add indexes on `Comic.user_id`, `Comic.story_id`, `ComicPanel.comic_id`, `SocialPost.story_id` + composite indexes | M1 | Survey 1 |
| 8 | FastAPI GZip Middleware | Add `GZipMiddleware(minimum_size=500)` to `backend/main.py` | M1 | Survey 1 |
| 9 | Expanded Vietnamese Canon | Expand `VIETNAMESE_HISTORICAL_CANON` from 6 to 31 heroes across 6 historical epochs | M2 | Survey 2 |
| 10 | AI Semantic Classifier | 2-pass classifier (regex + LLM semantic analysis) to block regex bypass | M2 | Survey 2 |
| 11 | Activate Historical Invariants | Wire `validate_historical_invariants` post-generation into `story_generator.py` & `copilot_agent.py` | M2 | Survey 2 |
| 12 | Auto-Detect Narrative Modes | Server auto-detection of 3 modes (`CHINH_SU`, `DA_SU`, `HU_CAU_TU_DO`) without manual UI selection | M2 | Survey 2 |
| 13 | Auto-Detect Mode Badge | Expose and render auto-detected mode badge in `StoryEditor.tsx` toolbar | M2 | Survey 2 |
| 14 | Hard-Blocking at Generation & Publish | Halt generation & refund coins on distortion; reject publish with 422 HTTP error | M2 | Survey 2 |
| 15 | Commercial IP Detection & Disclaimer | Detect commercial IP (Marvel, Harry Potter, etc.) and auto-attach fanfiction disclaimer on publish | M2 | Survey 2 |
| 16 | Follow/Unfollow Author System | Schema & API for author following and following-prioritized feed | M3 | Survey 3 |
| 17 | Threaded Comments | Comment replies with `parent_comment_id` in DB and REST endpoints | M3 | Survey 3 |
| 18 | Bookmarks / Personal Library | User bookmarks with custom categories/tags and retrieval endpoints | M3 | Survey 3 |
| 19 | Notification System | Real-time / polled notifications for like, comment, follow, message events | M3 | Survey 3 |
| 20 | Content Reporting System | User reports for distortion, spam, harassment with resolution status | M3 | Survey 3 |
| 21 | Author Profile Page & APIs | Author profile with bio, stats, works list, and follower counts | M3 | Survey 3 |
| 22 | Trending Leaderboard | Weekly and monthly trending ranking with time-decayed velocity formula | M3 | Survey 3 |
| 23 | Loading Skeleton Animation | 1-3s shimmer/pulse skeleton transition in `StoryEditor.tsx` during intake-to-editor | M3 | Survey 3 |
| 24 | Fullscreen Comic Reader | Modal swipe/carousel reader for sequential comic viewing in `CommunityFeedView.tsx` | M3 | Survey 3 |
| 25 | Posts Search Box | Search input on Posts tab filtering by story title and author name | M3 | Survey 3 |
| 26 | Backend TF.js Vector & Model Export | `GET /api/recommender/export-vectors` (128-dim) & quantized weights export endpoints | M4 | Survey 3 |
| 27 | Client TensorFlow.js Integration | `@tensorflow/tfjs` installed & SSR-safe dynamic import for static Next.js export | M4 | Survey 3 |
| 28 | IndexedDB Cache Manager | 10-20MB client cache with LRU eviction for neural weights and embeddings | M4 | Survey 3 |
| 29 | Client Local Re-Ranking | On-device MMR & score re-ranking on CPU/WASM backend avoiding WebGL contention | M4 | Survey 3 |
| 30 | Landing Page Neural Visual Effects | Generative AI art texture / style preview on landing page without Layer 0 WebGL clash | M4 | Survey 3 |
| 31 | Zero-Regression Existing Test Suite | Verify all 182 existing tests pass 100% | M5 | Testing Track |
| 32 | Round 6 Comprehensive Unit Tests | New tests for Copilot surgery, Historical validation, Social features, TF.js, WAL & indexes | M5 | Testing Track |
| 33 | Frontend Production Build Clean | `npm run build` succeeds with 0 TypeScript errors | M5 | Testing Track |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Copilot Manuscript Surgery & Performance | Features 1-8: `copilot_agent.py`, `StoryEditor.tsx`, `page.tsx`, SQLite WAL, Indexes, GZip | none | DONE |
| M2 | Vietnamese Historical & Copyright Protection | Features 9-15: `ontology.py`, `story_generator.py`, `copilot_agent.py`, `main.py`, `social_router.py`, `models.py`, `StoryEditor.tsx` | none | BLOCKED: CHALLENGE_FAILED (iteration 2 remediation mapped) |
| M3 | Social Network Expansion & Visual Fixes | Features 16-25: `models.py`, `social_router.py`, `CommunityFeedView.tsx`, `StoryEditor.tsx` | M1 | PLANNED |
| M4 | TensorFlow.js Hybrid Architecture | Features 26-30: `recommender_service.py`, `social_router.py`, client `@tensorflow/tfjs`, IndexedDB, Landing page effects | M3 | PLANNED |
| M5 | Test Suite, Regression Verification & Build | Features 31-33: Complete regression test run (182 existing + new R6 suites) & `npm run build` | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### Copilot Frontend ↔ Backend
- Payload `USER_CHAT` copilot event:
  ```json
  {
    "user_message": "string",
    "current_story": "string",
    "selected_text": "string (optional)",
    "cursor_position": "number (optional)"
  }
  ```
- Returned `edit_story_direct` action:
  ```json
  {
    "action": "edit_story_direct",
    "params": {
      "updated_story_content": "string (clean markdown prose with no raw JSON or truncation)"
    }
  }
  ```

### Historical Grounding & Auto-Detect Mode
- `auto_detect_narrative_mode(prompt: str, context: str = "") -> NarrativeMode`
- `validate_historical_invariants(story_text: str, mode: NarrativeMode, user_prompt: str = "") -> Tuple[bool, str]`
- Returns `(True, "OK")` or `(False, "Vi phạm tính chân thực lịch sử: [reason]")`.
- On `False` in generation: raises exception / halts stream and executes `ACTION_REFUND_FAILED`.
- On `False` in publish: returns HTTP 422 Unprocessable Entity.

### Social Models & REST Endpoints
- `Follow`: `id`, `follower_id`, `following_id`, `created_at`
- `PostComment`: `id`, `post_id`, `user_id`, `parent_comment_id` (nullable), `content`, `created_at`
- `Bookmark`: `id`, `user_id`, `post_id`, `category`, `created_at`
- `Notification`: `id`, `user_id`, `actor_id`, `notification_type`, `target_id`, `is_read`, `created_at`
- `ContentReport`: `id`, `reporter_id`, `target_id`, `target_type`, `reason`, `status`, `created_at`
- `SocialPost`: augmented with `is_fanfiction: bool`, `disclaimer: str`

### TensorFlow.js Export & Client
- `GET /api/recommender/export-vectors`: returns array of `{ "post_id": int, "concept_vector": [float, ...] }`
- Client: dynamic import of `@tensorflow/tfjs`, CPU backend for vector math, isolated 2D canvas for neural visual effects.

## Code Layout
- `backend/agents/copilot_agent.py` — SemanticChunkSlicer, HeadingPreservationEngine, CopilotAgent
- `backend/agents/story_generator.py` — StoryGenerator with pre-flight & post-generation historical invariant validation
- `backend/services/ontology.py` — VIETNAMESE_HISTORICAL_CANON (31 heroes), AISemanticHistoricalClassifier, auto_detect_narrative_mode, COMMERCIAL_IP_REGISTRY, detect_commercial_ip
- `backend/services/recommender_service.py` — Hybrid recommender, concept vector exports, time-decayed trending leaderboards
- `backend/db/models.py` — SQLite WAL configuration, single & composite indexes, models: User, Story, Comic, ComicPanel, SocialPost, Follow, PostComment, Bookmark, Notification, ContentReport
- `backend/main.py` — GZipMiddleware, generation & copilot streaming guards, coin refunds on invariant violation
- `backend/routers/social_router.py` — Social endpoints (publish, feed, follow, comments, bookmarks, notifications, reports, leaderboard, vector export)
- `frontend/src/components/editor/StoryEditor.tsx` — Text selection / caret offset extraction, loading skeleton, auto-detect mode badge
- `frontend/src/components/social/CommunityFeedView.tsx` — Fullscreen comic carousel, posts search box, fanfiction badge & disclaimer
- `frontend/src/lib/tfjs/` — Client TensorFlow.js recommendation re-ranker, IndexedDB cache manager
- `backend/tests/` — Test suites (run_all_tests.py, test_round6_*.py)
