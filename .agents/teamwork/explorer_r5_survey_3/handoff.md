# Handoff Report: Survey Requirements #4 & #5

## 1. Observation

Direct code observations from the NarrAI repository:

1. **Database Models & Tables (`backend/db/models.py`)**:
   - `SocialPost` defined at lines 133–161 with fields `id`, `user_id`, `story_id`, `title`, `content_snippet`, `cover_image_url`, `genre`, `tags`, `concept_vector`, `dsgo_entities`, `dsgo_spaces`, `completion_count`, `likes_count`, `comments_count`, `views_count`, `dwell_time_avg`, `created_at`.
   - `PostInteraction` defined at lines 163–190 with fields `interaction_type`, `dwell_seconds`, `scroll_depth`, `comment_text`, `sentiment_score`, `extracted_entities`.
   - `UserInterestProfile` defined at lines 192–207 with `interest_vector` (128-dim JSON), `last_decay_time`, `genre_affinity`, `entity_affinity`.
   - `Story`, `Comic`, `ComicPanel` defined at lines 28–70.

2. **Backend Social Router & Mounting (`backend/routers/social_router.py` & `backend/main.py`)**:
   - `routers/social_router.py` provides:
     - `GET /feed` (lines 116–141)
     - `POST /publish` (lines 144–183)
     - `POST /interact` (lines 185–221)
     - `GET /post/{post_id}` (lines 223–244)
   - Mounted in `backend/main.py` at line 88 & 92:
     ```python
     88: from routers.social_router import router as social_router
     92: app.include_router(social_router, prefix="/api/social", tags=["Social"])
     ```

3. **Recommendation Algorithm Implementation (`backend/services/recommender_service.py`)**:
   - Stage 1 Candidate Generation (lines 431–528): Content Cosine Top 40 + Graph DSGO Traversal Top 20.
   - Stage 2 Scoring (lines 530–625): $0.35 \times \text{Cosine} + 0.25 \times \text{Affinity} + 0.20 \times \text{Freshness} + 0.20 \times \text{Quality}$.
   - Stage 3 Exploration & Diversity (lines 627–767): MMR with $\lambda = 0.70$ and Multi-Armed Bandit with $15\%$ exploration using Thompson Sampling $\text{Beta}(\alpha, \beta)$.
   - Dynamic decay (lines 263–306): Exponential decay with $\lambda = 0.05/\text{day}$.
   - Sentiment analysis (lines 183–240): Vietnamese/English sentiment lexicon mapping to $[-1.0, 1.0]$.
   - Limitation observed in `publish_post` (lines 884–950): does not take or save updated `story_text` into `Story`, nor does it automatically extract comic cover from `ComicPanel` if `cover_image_url` is omitted.
   - Limitation observed in `get_post_details` (lines 1086–1107): only returns `content_snippet`; does not return `story_content` or `comic_panels`.

4. **Frontend Architecture & Components**:
   - `src/app/page.tsx` line 157:
     ```typescript
     157: const [activeTab, setActiveTab] = useState<"setup" | "editor" | "comic">("setup");
     ```
     No `"feed"` or `"community"` tab exists in `page.tsx`.
   - `src/components/layout/Sidebar.tsx` lines 97–134:
     Only has "Tạo truyện mới" (`onNewStory`), "Lịch sử tác phẩm" (`onOpenHistory`), and "Open Messenger" (`onOpenMessenger`). No "Bài đăng" tab.
   - `src/components/editor/StoryEditor.tsx` lines 172–188:
     Top bar only contains "Chuyển thể Truyện tranh" (`onAdaptToComic`) and "Tải bản thảo (TXT)" (`onDownload`). No "Lưu & Đăng bài" (Save & Publish) button.
   - `src/lib/api.ts` lines 37–338:
     No methods exist for `getSocialFeed`, `publishSocialPost`, `interactSocialPost`, or `getSocialPostDetails`.
   - `src/components/feed/`: No community feed component directory or file exists.
   - `src/components/canvas/ThreeAmbientCanvas.tsx` (Layer 0): WebGL Dong Son Drum shader quad + 350 interactive 3D particles. Fixed `z-index: 0; pointer-events: none`. Auto-pause via `visibilitychange`, `IntersectionObserver`, and 8s idle watchdog. Fallback CSS gradient for `prefers-reduced-motion`.
   - `src/components/cards/InteractiveTiltCard.tsx` (Layer 1): CSS 3D Transforms `perspective: 1000px`, `transform-style: preserve-3d`, specular glare overlay, 60 FPS compositor.
   - `src/components/morphicons/` (Layer 2): `LikeButtonMorphicon.tsx`, `CoinBadgeMorphicon.tsx`, `springPhysics.ts` Euler damped harmonic oscillator.
   - `src/components/portals/ClientPortal.tsx` (Layer 3): `createPortal` with `isolation: isolate` and `z-index: 60`. Used in `AuthModal`, `HistoryModal`, `CoinTopupModal`, `MessengerModal`.

---

## 2. Logic Chain

1. **Backend Readiness**:
   - *Premise*: `SocialPost`, `PostInteraction`, `UserInterestProfile` are migrated in SQLite (`db/models.py`), and the 3-Stage Recommender service (`services/recommender_service.py`) satisfies all mathematical constraints.
   - *Observation*: `routers/social_router.py` is already mounted at `/api/social`.
   - *Deduction*: Backend algorithmic core is 100% complete. However, to support one-click publish from `StoryEditor` and full-story reading from the Community Feed:
     a) `publish_post` must accept `story_text` to auto-save the manuscript and auto-sync comic cover image from the first panel of `Comic`.
     b) `get_post_details` must include `story_content` and `comic_panels` so the reader modal can display the novel text and comic panels.

2. **Frontend Gap**:
   - *Premise*: Requirement #4 mandates a "Bài đăng" tab next to "Sáng tác" and "Truyện tranh", a 3D parallax tilt card feed, a text story & comic reader modal, morphicon interactions, and a "Lưu & Đăng bài" button.
   - *Observation*: `page.tsx` lacks `"feed"` in `activeTab`. `StoryEditor.tsx` lacks the publish button. `api.ts` lacks social endpoints. No `CommunityFeed.tsx` or `PostReaderModal.tsx` exists.
   - *Deduction*: Implementing Requirement #4 requires:
     a) Adding API methods in `src/lib/api.ts`.
     b) Adding "Lưu & Đăng bài" button to `StoryEditor.tsx` toolbar and connecting it to a handler in `page.tsx` that calls `api.publishSocialPost` and shows a success toast with a direct link to view the post.
     c) Creating `CommunityFeed.tsx` with genre filtering, 3D tilt cards using `InteractiveTiltCard` (Layer 1), and `LikeButtonMorphicon` (Layer 2).
     d) Creating `PostReaderModal.tsx` using `ClientPortal` (Layer 3) to render full text story reading with dwell/scroll signal tracking and comic adaptation viewing.
     e) Updating `Sidebar.tsx` and `page.tsx` to provide clear navigation between "Sáng tác", "Truyện tranh", and "Bài đăng".

3. **Frontend 4-Layer Architecture Alignment**:
   - *Premise*: Requirement #5 requires WebGL Layer 0, CSS 3D Layer 1, Morphicons Layer 2, and Portals Layer 3 with zero collision and 60 FPS.
   - *Observation*: Layer 0 (`ThreeAmbientCanvas`), Layer 1 (`InteractiveTiltCard`), Layer 2 (`LikeButtonMorphicon`), and Layer 3 (`ClientPortal`) are already cleanly implemented and decoupled.
   - *Deduction*: All new UI components must strictly adhere to this 4-layer contract:
     - Community Feed cards MUST use `InteractiveTiltCard` (Layer 1) with `transform-style: preserve-3d`.
     - Like buttons MUST use `LikeButtonMorphicon` (Layer 2).
     - Reader Modal MUST use `ClientPortal` (Layer 3) with `isolation: isolate` and `z-index: 60`.

---

## 3. Caveats

- **Network Mode**: Investigation was performed in read-only analysis mode without modifying production source code.
- **Story IDs for Unsaved Drafts**: If a user writes text manually in the editor without calling `streamStory`, `storyId` is null. The "Lưu & Đăng bài" handler and backend `publish_post` must gracefully create a new `Story` record when `story_id` is null.
- **Comic Panel Image URLs**: Comic panel URLs are formatted as `/api/comic/image/{panel.id}`. The reader modal must use `api.getComicImageUrl(...)` to correctly prefix the backend host in dev/production environments.

---

## 4. Conclusion

The system is in an optimal state to complete Requirements #4 & #5:
1. The backend foundation (database models, routers, 3-stage recommendation engine) is 90% ready; it only needs small data enrichments in `publish_post` (auto-saving draft text and syncing comic cover) and `get_post_details` (returning full text and comic panels).
2. The frontend 4-layer visual pipeline is 100% established (`ThreeAmbientCanvas`, `InteractiveTiltCard`, `LikeButtonMorphicon`, `ClientPortal`).
3. The remaining work is strictly scoped:
   - Implement social API client functions in `frontend/src/lib/api.ts`.
   - Add the "Lưu & Đăng bài" button to `StoryEditor.tsx` with success toast post redirection.
   - Build `CommunityFeed.tsx` and `PostReaderModal.tsx`.
   - Integrate 3-tab navigation ("Sáng tác", "Truyện tranh", "Bài đăng") into `Sidebar.tsx` and `page.tsx`.

---

## 5. Verification Method

1. **Backend Verification**:
   - Run python compiler check on all backend modules:
     ```powershell
     python -m py_compile backend/main.py backend/routers/social_router.py backend/services/recommender_service.py backend/db/models.py
     ```
   - Run recommender test suites:
     ```powershell
     python backend/tests/test_e2e_recommender_messenger.py
     python backend/tests/test_adversarial_narrative_recommender.py
     ```

2. **Frontend Verification**:
   - Inspect files created and updated:
     - `frontend/src/lib/api.ts`
     - `frontend/src/components/editor/StoryEditor.tsx`
     - `frontend/src/components/feed/CommunityFeed.tsx`
     - `frontend/src/components/modals/PostReaderModal.tsx`
     - `frontend/src/components/layout/Sidebar.tsx`
     - `frontend/src/app/page.tsx`
   - Run Next.js production build:
     ```powershell
     cd frontend
     npm run build
     ```
   - Invalidation conditions: Any TypeScript compilation error in `npm run build` or any regression in existing test suites indicates a verification failure.
