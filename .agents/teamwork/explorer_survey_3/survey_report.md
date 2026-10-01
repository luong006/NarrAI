# Technical Survey Report: R3 (TensorFlow.js Hybrid), R4 (Social Expansion), R5 (Visual Fixes)

**Author**: `explorer_survey_3` (teamwork_preview_explorer)  
**Date**: 2026-09-30  
**Target Milestone**: Survey R6 / Milestone 6  
**Reference Document**: `ORIGINAL_REQUEST.md` (Section ## 2026-09-30T16:30:48Z)  

---

## Executive Summary

This report delivers the comprehensive architectural and technical survey of the NarrAI platform for three core upgrades:
1. **R3: TensorFlow.js Hybrid Architecture**: Bridging backend vector/model weight export (~2-5MB) with client-side TensorFlow.js on-device inference, IndexedDB caching (10-20MB budget), local MMR recommendation re-ranking, and non-conflicting landing page WebGL/canvas neural visual effects.
2. **R4: Social Network Expansion**: Comprehensive database schemas, REST APIs, and UI designs for 7 social components: (1) Follow/Unfollow & Feed filtering, (2) Threaded comments with `parent_comment_id`, (3) Bookmarks/Personal Library with categories and tags, (4) Notifications, (5) Content Reports, (6) Author Profiles, and (7) Trending Leaderboards (Weekly/Monthly).
3. **R5: Visual Fixes & Narrative Mode Auto-Detection**: Three sequential UI improvements: (1) Loading Skeleton for the 1-3s Intake Chat-to-Editor transition, (2) Fullscreen swipe/carousel comic reader in the post reader modal, (3) Search box on the Posts tab (title & author name search), and Auto-detected narrative mode badge in UI.

---

## Section A: R3 — TensorFlow.js Hybrid Architecture

### 1. Backend: Story Concept Vectors & Model Weights Export

#### A. Current State in Codebase
- In `backend/services/recommender_service.py` (lines 123-178), concept vectors are generated as 128-dimensional L2-normalized float vectors using multi-hash semantic feature projection (`generate_concept_vector`).
- `SocialPost.concept_vector` in `backend/db/models.py` (line 148) stores this 128-dim float vector as a serialized JSON string.
- Currently, there is no batch vector export endpoint for client-side consumption.

#### B. Vector Export API Specification
- **Endpoint**: `GET /api/recommender/export-vectors` (or `GET /api/social/vectors`)
- **Query Parameters**:
  - `since`: ISO timestamp string (optional, for delta sync)
  - `limit`: integer, default 100, max 500
  - `format`: `"json"` or `"binary"` (default: `"json"`)
- **JSON Payload Format**:
  ```json
  {
    "status": "success",
    "version": "1.0",
    "vector_dim": 128,
    "count": 48,
    "vectors": [
      {
        "post_id": 101,
        "title": "Huyết Chiến Bạch Đằng 1288",
        "genre": "Lịch sử",
        "author_id": 12,
        "author_name": "Trần Quốc Tuấn",
        "concept_vector": [0.082, -0.041, 0.125, ...],
        "created_at": "2026-09-28T14:20:00Z",
        "views_count": 340,
        "likes_count": 45,
        "completion_count": 28
      }
    ]
  }
  ```
- **Binary ArrayBuffer Optimization (Optional Fast Path)**:
  - 128 dimensions * 4 bytes (Float32) = 512 bytes per post.
  - 100 posts = 51.2 KB; 1,000 posts = ~512 KB.
  - Can be served via `Content-Type: application/octet-stream` with a 16-byte header: `[uint32 post_id, float32[128]]`.

#### C. Quantized Model Weights Export (~2-5MB)
To enable client-side neural re-ranking or feature scoring without calling the backend LLM repeatedly:
- **Format**: TensorFlow.js standard LayersModel bundle:
  - `model.json` (topology, input/output tensor specifications, weight manifests)
  - `group1-shard1of1.bin` (quantized 8-bit or 16-bit weight buffer, ~1.2 - 2.8 MB)
- **Model Topology**: A lightweight 2-Tower Scorer MLP:
  - Input: Concatenation of `[user_interest_vector (128), post_concept_vector (128), interaction_signals (4)]` = 260 inputs.
  - Layer 1: Dense(64, activation='relu', kernel_regularizer='l2')
  - Layer 2: Dense(32, activation='relu')
  - Layer 3: Dense(1, activation='sigmoid') -> Engagement Affinity Probability `P(engage | u, p)`.
- **API Endpoints**:
  - `GET /api/models/reranker/model.json`
  - `GET /api/models/reranker/weights.bin`
  - (Served with `Cache-Control: public, max-age=604800, immutable` and `GZipMiddleware` enabled).

---

### 2. Frontend: TensorFlow.js, USE Lite / MobileNet Tiny & Caching

#### A. Dependency Analysis (`package.json`)
- In `frontend/package.json`: Currently `@tensorflow/tfjs` is not installed.
- Required additions:
  ```json
  "dependencies": {
    "@tensorflow/tfjs": "^4.22.0",
    "@tensorflow-models/universal-sentence-encoder": "^1.3.3"
  }
  ```
- **Next.js Static Export Guard (`next.config.mjs`)**:
  - `next.config.mjs` has `output: 'export'`.
  - `@tensorflow/tfjs` must **never** be evaluated during Node.js prerender / static export.
  - Safe pattern: Lazy import via dynamic `import('@tensorflow/tfjs')` inside `useEffect` or client-side singleton functions guarded by `typeof window !== 'undefined'`.

#### B. IndexedDB Caching Budget (10-20MB Quota)
- Browsers allocate several megabytes for IndexedDB without prompting.
- TF.js has native scheme support for IndexedDB:
  ```ts
  // Save model:
  await model.save('indexeddb://narrai-reranker-v1');
  // Load model:
  const model = await tf.loadLayersModel('indexeddb://narrai-reranker-v1');
  ```
- **Custom Cache Budget Manager (`src/lib/tfjs/modelCache.ts`)**:
  - Database Name: `NarrAI_TFJS_Cache`
  - Object Stores: `models`, `vectors`, `metadata`
  - Budget Enforcement:
    1. Before storing new model weights, calculate total stored payload byte length.
    2. Check `navigator.storage && navigator.storage.estimate()`.
    3. If cache exceeds 18MB (budget: 10-20MB), purge oldest entries (LRU policy) or delete outdated model versions.

#### C. Client-Side Local Recommendation Re-Ranking
- Instead of making an HTTP call on every filter change, user scroll, or tab switch:
  1. Frontend maintains the user's dynamic interest vector in memory / localStorage.
  2. Candidate posts (50-200 posts) with their 128-dim vectors are cached in IndexedDB.
  3. Client computes cosine similarity + MMR diversity locally using TF.js:
     ```ts
     export function localMMRReRank(
       userVector: number[],
       candidatePosts: Array<{ id: number; vector: number[]; score?: number }>,
       lambdaMMR: number = 0.70,
       topK: number = 20
     ) {
       return tf.tidy(() => {
         const uTensor = tf.tensor1d(userVector);
         const candVectors = tf.tensor2d(candidatePosts.map(p => p.vector));
         
         // Cosine similarities
         const similarities = tf.matMul(candVectors, uTensor.expandDims(1)).squeeze();
         const simArray = Array.from(similarities.dataSync());
         
         // Greedily pick items using MMR:
         // argmax [ lambda * Sim(u, p) - (1 - lambda) * max_{s in Selected} Sim(p, s) ]
         const selected: typeof candidatePosts = [];
         const remaining = candidatePosts.map((p, i) => ({ ...p, baseSim: simArray[i] }));
         
         while (selected.length < topK && remaining.length > 0) {
           let bestIdx = 0;
           let bestScore = -Infinity;
           
           for (let i = 0; i < remaining.length; i++) {
             const cand = remaining[i];
             let maxSimSelected = 0;
             for (const s of selected) {
               // Dot product between cand and s
               const dot = cand.vector.reduce((acc, v, d) => acc + v * s.vector[d], 0);
               if (dot > maxSimSelected) maxSimSelected = dot;
             }
             const mmrScore = lambdaMMR * cand.baseSim - (1 - lambdaMMR) * maxSimSelected;
             if (mmrScore > bestScore) {
               bestScore = mmrScore;
               bestIdx = i;
             }
           }
           selected.push(remaining.splice(bestIdx, 1)[0]);
         }
         return selected;
       });
     }
     ```
  - Execution time: ~0.8ms for 100 items on CPU/WebGL. No server round-trip!

#### D. Landing Page Visual Effects Without ThreeUI / WebGL Conflict
- `src/components/canvas/ThreeAmbientCanvas.tsx` runs native WebGL GLSL shaders on Layer 0 (ambient background).
- WebGL contexts are limited per browser (typically 8 to 16).
- **Zero-Conflict Strategy**:
  1. **Backend CPU fallback for TF.js re-ranking**: Keep recommendation tensor calculations on `cpu` or `wasm` backend so TF.js does not acquire a WebGL context for math ops (`tf.setBackend('cpu')`).
  2. **Separate 2D Canvas for AI Art Effect**:
     On the landing page, create a dedicated interactive card: `"AI Stylized Preview / Generative Texture Canvas"`.
     Use an HTML5 `<canvas id="tfjs-art-canvas">` with 2D rendering context.
     Run style transfer / procedural screentone texture synthesis in TF.js, then use `tf.browser.toPixels(outputTensor, canvasElement)`.
  3. **Strict Memory Scoping**:
     Wrap all visual manipulations in `tf.tidy()` or `try { ... } finally { tensor.dispose(); }`.
     Listen to `webglcontextlost` to release references gracefully without crashing `ThreeAmbientCanvas`.

---

## Section B: R4 — Social Network Expansion

### 1. Database Schema Additions (`backend/db/models.py`)

The existing database already includes `SocialPost`, `PostInteraction`, `UserInterestProfile`, `Conversation`, `ConversationParticipant`, and `ChatMessage`.
The following models must be added:

```python
# ==================== 1. FOLLOWS ====================
class Follow(Base):
    __tablename__ = "follows"
    id = Column(Integer, primary_key=True, autoincrement=True)
    follower_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    following_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    follower = relationship("User", foreign_keys=[follower_id], backref="following_users")
    following = relationship("User", foreign_keys=[following_id], backref="follower_users")
    
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_user_follower_following"),
    )

# ==================== 2. THREADED COMMENTS ====================
# Note: PostInteraction can be enhanced, OR a dedicated Comment model can be added.
# Best practice for compatibility: Add parent_comment_id to PostInteraction:
# PostInteraction.parent_comment_id = Column(Integer, ForeignKey("post_interactions.id"), nullable=True, index=True)
# PostInteraction.reply_count = Column(Integer, default=0, nullable=False)

# ==================== 3. BOOKMARKS / PERSONAL LIBRARY ====================
class Bookmark(Base):
    __tablename__ = "bookmarks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    post_id = Column(Integer, ForeignKey("social_posts.id"), index=True, nullable=False)
    category = Column(String(100), default="Yêu thích", index=True) # e.g. "Đang đọc", "Yêu thích", "Để dành"
    tags = Column(Text, default="[]") # JSON list of strings
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", backref="bookmarks")
    post = relationship("SocialPost", backref="bookmarks")
    
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_user_post_bookmark"),
    )

# ==================== 4. NOTIFICATIONS ====================
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    notification_type = Column(String(50), index=True, nullable=False) # LIKE, COMMENT, FOLLOW, MESSAGE
    post_id = Column(Integer, ForeignKey("social_posts.id"), nullable=True)
    comment_id = Column(Integer, nullable=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    content = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    recipient = relationship("User", foreign_keys=[recipient_id], backref="received_notifications")
    sender = relationship("User", foreign_keys=[sender_id])
    post = relationship("SocialPost")

# ==================== 5. CONTENT REPORTS ====================
class ContentReport(Base):
    __tablename__ = "content_reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    post_id = Column(Integer, ForeignKey("social_posts.id"), nullable=True, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    report_reason = Column(String(50), nullable=False) # distortion (xuyên tạc), spam, harassment (quấy rối), copyright
    details = Column(Text, nullable=True)
    status = Column(String(30), default="PENDING", index=True) # PENDING, REVIEWED, RESOLVED, DISMISSED
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    reporter = relationship("User", foreign_keys=[reporter_id])
    post = relationship("SocialPost")
    target_user = relationship("User", foreign_keys=[target_user_id])

# ==================== 6. AUTHOR PROFILES ====================
class AuthorProfile(Base):
    __tablename__ = "author_profiles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    bio = Column(Text, default="")
    avatar_url = Column(String(500), nullable=True)
    cover_url = Column(String(500), nullable=True)
    genres = Column(Text, default="[]") # JSON list of primary genres
    followers_count = Column(Integer, default=0, nullable=False)
    following_count = Column(Integer, default=0, nullable=False)
    works_count = Column(Integer, default=0, nullable=False)
    total_likes = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", backref=backref("author_profile", uselist=False))
```

### 2. Social Endpoints Specification (`backend/routers/social_router.py`)

| Component | Method & Path | Description | Authentication |
|---|---|---|---|
| **Follow** | `POST /api/social/follow/{author_id}` | Follow an author; creates notification | Required |
| **Unfollow** | `DELETE /api/social/follow/{author_id}` | Unfollow an author | Required |
| **Follow Status** | `GET /api/social/follow/status/{author_id}` | Returns `{ is_following: bool }` | Optional |
| **Filtered Feed** | `GET /api/social/feed?filter=following` | Feed showing only posts from followed authors | Required |
| **Threaded Comments** | `POST /api/social/posts/{post_id}/comments` | Submit comment/reply with `parent_comment_id` | Required |
| **List Comments** | `GET /api/social/posts/{post_id}/comments` | Returns hierarchical nested comment tree | Public |
| **Bookmarks** | `POST /api/social/bookmarks` | Save post to personal library (`category`, `tags`) | Required |
| **Remove Bookmark** | `DELETE /api/social/bookmarks/{post_id}` | Remove post from personal library | Required |
| **List Bookmarks** | `GET /api/social/bookmarks?category=...` | Retrieve bookmarked posts | Required |
| **Notifications** | `GET /api/social/notifications` | Get notifications + `unread_count` | Required |
| **Read Notification** | `PUT /api/social/notifications/{id}/read` | Mark a notification as read | Required |
| **Read All** | `PUT /api/social/notifications/mark-all-read` | Mark all notifications as read | Required |
| **Reports** | `POST /api/social/reports` | Submit violation report (distortion, spam, etc.) | Required |
| **Author Profile** | `GET /api/social/author/{identifier}` | Get profile, statistics, and published works | Public |
| **Update Profile** | `PUT /api/social/author/profile` | Update bio, avatar, and genres | Required |
| **Trending Leaderboard** | `GET /api/social/leaderboard?period=weekly` | Weekly/Monthly leaderboard ranking | Public |

### 3. Trending Leaderboard Algorithm
- Time decay formula for velocity:
  $$\text{TrendingScore}(p) = \frac{3 \cdot \text{likes} + 5 \cdot \text{comments} + 0.5 \cdot \text{views} + 4 \cdot \text{completions}}{(\text{age\_in\_hours} + 2)^{1.4}}$$
- Weekly filter: `created_at >= NOW() - INTERVAL 7 DAYS`
- Monthly filter: `created_at >= NOW() - INTERVAL 30 DAYS`

---

## Section C: R5 — Visual Fixes & Narrative Mode Auto-Detection

### 1. Item 1: Loading Skeleton (Intake Chat to Editor Transition)
- **Problem**: When user completes Intake Chat and clicks *"Bắt đầu viết truyện ngay"*, there is a 1-3 second delay while `api.streamStory` calls Groq and starts streaming. The StoryEditor currently renders a blank white canvas with no visual feedback.
- **Solution**:
  - In `frontend/src/components/editor/StoryEditor.tsx`, introduce an `isLoading` prop:
    ```tsx
    interface StoryEditorProps {
      content: string;
      isLoading?: boolean;
      ...
    }
    ```
  - When `(isLoading || isStreaming) && !content`:
    Render an elegant manuscript loading skeleton inside the paper canvas:
    ```tsx
    <div className="space-y-6 animate-pulse">
      {/* Title skeleton */}
      <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded-lg w-2/3 mb-4" />
      {/* Sub-heading skeleton */}
      <div className="h-5 bg-slate-200 dark:bg-slate-800 rounded w-1/3 mb-8" />
      {/* Paragraph 1 */}
      <div className="space-y-3">
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-full" />
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-11/12" />
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-full" />
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-4/5" />
      </div>
      {/* Paragraph 2 */}
      <div className="space-y-3 pt-4">
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-full" />
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-5/6" />
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-3/4" />
      </div>
      {/* Shimmer badge */}
      <div className="flex items-center gap-2 pt-6 text-xs text-indigo-500 font-medium">
        <Sparkles className="w-4 h-4 animate-spin text-amber-500" />
        <span>NarrAI Co-pilot đang phân rã kịch bản và khởi tạo chương đầu tiên...</span>
      </div>
    </div>
    ```

### 2. Item 2: Fullscreen Comic Reader (Swipe / Carousel in Post Modal)
- **Problem**: In `CommunityFeedView.tsx` (lines 450-481), comic panels are rendered in a static 3-column grid inside the post reader modal. Readers cannot flip or swipe through panels in sequence.
- **Solution**:
  - Add a dedicated Fullscreen Carousel Reader mode:
    - State: `fullscreenComic: boolean`, `activePanelIndex: number` (0 to `comic_panels.length - 1`).
    - Trigger: Clicking any comic panel or a new button *"Đọc toàn màn hình (Swipe Carousel)"*.
    - Features:
      1. Fixed backdrop: `fixed inset-0 z-50 bg-black/95 flex flex-col justify-between`.
      2. Large centered panel image with `object-contain max-h-[75vh]`.
      3. Dialogue / speech box positioned under the panel with crisp typography.
      4. Left/Right navigation buttons + Keyboard `ArrowLeft`/`ArrowRight` event listeners.
      5. Touch swipe gestures (`onTouchStart`, `onTouchMove`, `onTouchEnd` checking `deltaX > 50px`).
      6. Bottom thumbnail strip with panel counter (`Khung 3 / 8`).
      7. Close button (`X` or `Escape` key).

### 3. Item 3: Search Box on Posts Tab
- **Problem**: `CommunityFeedView.tsx` only has genre filter pills. There is no search box to find stories by title or author name.
- **Solution**:
  - Add a search input in the header bar of `CommunityFeedView.tsx`:
    ```tsx
    <div className="relative flex-1 max-w-md">
      <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder={lang === "vi" ? "Tìm theo tên truyện hoặc tác giả..." : "Search story or author..."}
        className="w-full pl-9 pr-8 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 focus:outline-none focus:border-indigo-500"
      />
      {searchQuery && (
        <button onClick={() => setSearchQuery("")} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
    ```
  - Real-time client-side filter + API search integration:
    Filters `posts` by `post.title.toLowerCase().includes(q) || post.author.full_name.toLowerCase().includes(q) || post.author.username.toLowerCase().includes(q)`.

### 4. Auto-Detected Narrative Mode Badge in UI
- **Requirement**: No manual dropdown! The narrative mode (`CHINH_SU`, `DA_SU`, `HU_CAU_TU_DO`) must be classified automatically by the backend/model and indicated with a small label in the UI.
- **Backend Detection**:
  - Implement `auto_detect_narrative_mode(prompt, genre)` in `backend/services/ontology.py`.
  - Scan for canonical historical heroes/events (20-30 heroes: Hai Bà Trưng, Ngô Quyền, Đinh Bộ Lĩnh, Lê Hoàn, Lý Thường Kiệt, Trần Hưng Đạo, Trần Nhân Tông, Lê Lợi, Nguyễn Trãi, Quang Trung, Phan Bội Châu, Hồ Chí Minh, Võ Nguyên Giáp, etc.).
  - If prompt contains canonical historical heroes + strict historical context $\rightarrow$ `CHINH_SU`.
  - If prompt contains canonical historical era/heroes + fictional protagonist/romance $\rightarrow$ `DA_SU`.
  - Otherwise (sci-fi, cyberpunk, western fantasy, isekai, modern) $\rightarrow$ `HU_CAU_TU_DO`.
- **UI Badge Implementation**:
  - In `StoryEditor.tsx`, `CommunityFeedView.tsx`, and `UnifiedIntakeChat.tsx`:
    - `CHINH_SU`: Amber badge: `📜 Chính sử Việt Nam` (Strict Historical Authenticity)
    - `DA_SU`: Indigo badge: `📖 Dã sử phóng tác` (Historical Fiction)
    - `HU_CAU_TU_DO`: Emerald badge: `✨ Hư cấu tự do` (Personal Fiction)

---

## Verification Plan & Concrete Checklist

1. **R3 Verification**:
   - Verify `package.json` contains `@tensorflow/tfjs`.
   - Test vector export API: `GET /api/recommender/export-vectors` returns 128-dim vectors.
   - Test model weights API: `GET /api/models/reranker/model.json` returns valid TF.js topology.
   - Run `npm run build` in `frontend/` to ensure no SSR errors with TF.js.
2. **R4 Verification**:
   - Run Python syntax checks on `backend/db/models.py` and `backend/routers/social_router.py`.
   - Execute test cases covering: Follow/Unfollow, Threaded comment replies, Bookmark CRUD, Notification generation, Content Report submission, Author profile retrieval, and Weekly/Monthly leaderboard.
3. **R5 Verification**:
   - Visually check StoryEditor loading skeleton on intake transition.
   - Verify Fullscreen comic reader swipe navigation in post modal.
   - Verify Search box filters posts by title and author.
   - Verify auto-detected narrative mode badge renders correct color and text.
