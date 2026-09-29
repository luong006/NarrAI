## 2026-09-29T04:14:00Z
<USER_REQUEST>
Read e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md.
Read e:\NarrAI\PROJECT.md.
Read e:\NarrAI\.agents\teamwork\explorer_r5_survey_3\survey_report.md and handoff.md.

You are the Community Feed & 4-Layer Implementer for Milestone 3.
Your working directory is e:\NarrAI\.agents\teamwork\worker_r5_m3.
You own exclusively:
- frontend/src/lib/api.ts
- frontend/src/components/editor/StoryEditor.tsx
- frontend/src/components/feed/CommunityFeed.tsx (create new)
- frontend/src/components/modals/PostReaderModal.tsx (create new)
- frontend/src/components/layout/Sidebar.tsx
- frontend/src/app/page.tsx
- frontend/src/lib/types.ts & frontend/src/lib/i18n.ts (add social feed types and bilingual keys)

Tasks to implement:
1. In frontend/src/lib/api.ts:
   - Add getSocialFeed(params) -> GET /api/social/feed
   - Add publishSocialPost(payload) -> POST /api/social/publish
   - Add interactSocialPost(payload) -> POST /api/social/interact
   - Add getSocialPostDetails(postId) -> GET /api/social/post/{post_id}
2. In frontend/src/components/editor/StoryEditor.tsx:
   - Add prominent "Lưu & Đăng bài" (Save & Publish) button on the top toolbar (with glowing badge, tooltip, loading state).
   - Trigger onSaveAndPublish prop when clicked.
3. In frontend/src/app/page.tsx:
   - Support activeTab: "setup" | "editor" | "comic" | "feed".
   - Implement handleSaveAndPublishStory: saves latest story text, syncs comic cover if available, calls api.publishSocialPost, shows success toast with direct link to view the post.
   - Wire "feed" tab to render <CommunityFeed />.
4. In frontend/src/components/feed/CommunityFeed.tsx:
   - Clean, elegant community feed view.
   - Use InteractiveTiltCard (Layer 1, CSS 3D Transforms perspective: 1000px, preserve-3d) for post cards.
   - Display title, manga cover image if available, excerpt, genre tag, author badge, completion/like/view metrics.
   - Connect Like interaction using LikeButtonMorphicon (Layer 2).
   - Genre filter tabs (Tất cả, Lịch sử, Viễn tưởng, Tiên hiệp, Đời sống, etc.).
   - Clicking a card opens PostReaderModal.
5. In frontend/src/components/modals/PostReaderModal.tsx:
   - Use ClientPortal (Layer 3) with isolation: isolate and z-index: 60 to prevent any z-fighting.
   - Render full novel text (story_content) with elegant typography and reader controls.
   - Render manga comic panels (if available) with zoom / full view.
   - Telemetry tracking for dwell time and scroll signals sent to api.interactSocialPost.
6. In frontend/src/components/layout/Sidebar.tsx:
   - Add navigation tab "Bài đăng" (with Newspaper/BookOpen icon) alongside "Sáng tác" and "Truyện tranh".
7. Verify 4-Layer Architecture compliance:
   - Layer 0: ThreeAmbientCanvas (auto-pause on hidden tab, GPU 0%).
   - Layer 1: Semantic DOM & InteractiveTiltCard.
   - Layer 2: Morphicons SVG spring physics.
   - Layer 3: ClientPortal with isolation: isolate and z-index: 60.
8. Verification: Ensure frontend compiles cleanly without errors (npm run build).
9. Write detailed handoff.md in your working directory. Update progress.md with timestamp.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
</USER_REQUEST>
