# Handoff Report — Frontend Survey for R1, R2, R4

**Agent**: `explorer_r7_frontend`  
**Working Directory**: `e:\NarrAI\.agents\teamwork\explorer_r7_frontend`  
**Recipient**: Orchestrator (`6e1fbb7b-e64c-45b5-8d0a-ea6939f474c6`)  
**Timestamp**: 2026-10-05T05:40:00Z  

---

## 1. Observation

1. **R1 (Landing Page & `<NeuralVisualPreview />`)**:
   - In `frontend/src/components/landing/LandingView.tsx`:
     - Line 10: `import { NeuralVisualPreview } from "@/components/canvas/NeuralVisualPreview";`
     - Lines 84-88:
       ```tsx
       {/* AI Art & Neural Style Preview Showcase (Feature 30) */}
       <section className="max-w-4xl mx-auto px-6 pb-12">
         <NeuralVisualPreview lang={lang} />
       </section>
       ```
   - In `frontend/src/app/page.tsx`:
     - Line 23: `import { NeuralVisualPreview } from "@/components/canvas/NeuralVisualPreview";`
     - Line 168: `const [isNeuralModalOpen, setIsNeuralModalOpen] = useState(false);`
     - Lines 984-998: Modal rendering `<NeuralVisualPreview lang={lang} />` conditioned on `isNeuralModalOpen` (which is never toggled `true`).
   - In `frontend/src/components/canvas/NeuralVisualPreview.tsx`:
     - Uses 2D HTML5 Canvas (`ctx.createImageData(w, h)`), deterministic PRNG, and harmonic math.
     - Does **not** import `@tensorflow/tfjs` or `@tensorflow/tfjs-core`.
   - In `frontend/src/services/tfjsRecommender.ts`:
     - Line 66: `const tf = await import(/* webpackIgnore: true */ "@tensorflow/tfjs");`
     - Uses `@tensorflow/tfjs` independently for story concept vector inference and local candidate re-ranking.

2. **R2 (Unified Intake Chat Symmetry & Bottom Dock)**:
   - In `frontend/src/components/setup/UnifiedIntakeChat.tsx`:
     - Line 471: Scroll container with `<div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8 pb-48">`.
     - Line 597: Hardcoded fixed dock:
       ```tsx
       <div className="fixed bottom-0 left-0 right-0 sm:left-64 p-3 sm:p-5 bg-gradient-to-t from-slate-50/95 via-slate-50/80 to-transparent dark:from-slate-950/95 dark:via-slate-950/80 dark:to-transparent z-20 pointer-events-none">
       ```
     - Line 490: Starter prompts grid:
       ```tsx
       <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full text-left">
       ```
     - Lines 290-310: Hardcoded fallback responses on error or non-success:
       ```tsx
       content: "Ý tưởng của bạn rất cuốn hút! Hãy chia sẻ thêm về nhân vật chính, xung đột cốt lõi hoặc bối cảnh không gian nhé."
       ```
       and
       ```tsx
       content: "Đang kết nối lại với trợ lý NarrAI. Bạn có thể tiếp tục chia sẻ hoặc bấm 'Bắt đầu viết truyện ngay'..."
       ```

3. **R4 (Sidebar Navigation & Social Features)**:
   - In `frontend/src/components/layout/Sidebar.tsx`:
     - Line 6: `import { PlusCircle, BookOpen, LogOut, User, MessageSquare, Compass, FileText, Palette } from "lucide-react";`
     - Lines 152-163:
       ```tsx
       <button onClick={() => onTabChange?.("posts")} ...>
         <Compass className="w-4 h-4 text-violet-600 dark:text-violet-400" />
         <span>{t.tab_posts || (lang === "vi" ? "Bài đăng" : "Community Feed")}</span>
       </button>
       ```
   - In `frontend/src/components/landing/LandingView.tsx`:
     - Lines 73-81: Hero only contains a single primary CTA button for `onOpenAuth` ("Bắt đầu sáng tác ngay").
   - In `frontend/src/components/social/CommunityFeedView.tsx`:
     - Contains feed loading, genre filtering (6 pills), search box (`searchQuery`), fullscreen comic reader, and `LikeButtonMorphicon`.
     - Lacks a Follow/Unfollow Author button on cards and modal.
     - Renders comments in a flat list (lines 758-778) without reply action or indentation for `parent_comment_id`.
   - In `backend/routers/social_router.py`:
     - Lines 471-540: `POST /api/social/follow/{user_id}` and `POST /api/social/unfollow/{user_id}` exist and are fully tested.
     - Line 141 & 362: `POST /api/social/interact` supports `parent_comment_id` and dispatches reply notifications.

---

## 2. Logic Chain

1. **R1 Logic**:
   - *Observation*: `<NeuralVisualPreview />` is mounted at `LandingView.tsx:86` and does not import `@tensorflow/tfjs`. `@tensorflow/tfjs` is used exclusively in `services/tfjsRecommender.ts`.
   - *Inference*: Removing `<NeuralVisualPreview />` from `LandingView.tsx` will not disrupt TensorFlow.js or any other component.
   - *Conclusion*: Simply remove lines 10 and 84-88 from `LandingView.tsx` to restore a clean Hero + Feature Card layout.

2. **R2 Logic**:
   - *Observation*: `UnifiedIntakeChat.tsx:597` uses `fixed sm:left-64` viewport positioning, decoupling it from its flex parent and requiring `pb-48` in the scroll container.
   - *Inference*: Because `UnifiedIntakeChat` is a `flex flex-col h-full w-full relative` container, moving the dock into normal document flow (`shrink-0` or `sticky bottom-0`) naturally centers it with the message thread and removes viewport dependencies.
   - *Conclusion*: Replace `fixed sm:left-64` with a `shrink-0 w-full` footer containing `max-w-3xl mx-auto`, and decrease `pb-48` to `pb-6`. Widen the starter prompts grid gap from `gap-3.5` to `gap-4 sm:gap-5` with uniform card padding and min-height.

3. **R4 Logic**:
   - *Observation*: `Sidebar.tsx:160` uses `<Compass />` and label "Bài đăng". `LandingView.tsx:73` lacks a community button. `CommunityFeedView.tsx` lacks follow author and nested comment replies, despite backend support in `social_router.py`.
   - *Inference*: The community feature is under-promoted and missing client interactions.
   - *Conclusion*:
     1. In `Sidebar.tsx`, switch icon to `Users` and text to `t.tab_community` ("Mạng xã hội" / "Community & Social").
     2. In `LandingView.tsx`, add a secondary CTA "Khám phá Cộng đồng" calling `onExploreCommunity()`.
     3. In `CommunityFeedView.tsx`, add Follow button wired to `api.followAuthor` and a Reply button under comments wired to `interactPost({ parent_comment_id })`.

---

## 3. Caveats

- **No Backend Changes Needed for UI/UX**: The backend social endpoints (`follow`, `unfollow`, `interact` with `parent_comment_id`, `following` feed) are already fully operational and covered by tests.
- **R3 Backend Multi-Model Fallback**: Detailed exploration of `qa_refiner.py` and `main.py` is being handled by the backend explorer (`explorer_r7_backend`), but this frontend survey provides the complementary client-side recommendations for dynamic offline fallback.

---

## 4. Conclusion

The frontend codebase is well-structured and modular. The recommended modifications are surgical and clean:
1. **R1**: Strip `<NeuralVisualPreview />` from `LandingView.tsx`.
2. **R2**: Replace `fixed sm:left-64` in `UnifiedIntakeChat.tsx` with flex `shrink-0` bottom bar, polish avatar/bubble symmetry, widen starter prompts grid, and eliminate static error strings.
3. **R4**: Rename tab to "Mạng xã hội" with `Users` icon, add "Khám phá Cộng đồng" CTA to Landing page, and wire Follow Author + Threaded Comments in `CommunityFeedView.tsx`.

---

## 5. Verification Method

1. **Codebase Inspection**:
   - Verify `LandingView.tsx` contains 0 instances of `NeuralVisualPreview`.
   - Verify `UnifiedIntakeChat.tsx` contains 0 instances of `fixed sm:left-64`.
   - Verify `Sidebar.tsx` imports `Users` and displays "Mạng xã hội".
2. **TypeScript & Build Check**:
   - Run `npm run build` in `e:\NarrAI\frontend` to ensure 0 TypeScript or JSX compilation errors.
3. **Invalidation Conditions**:
   - If removing `<NeuralVisualPreview />` causes compilation errors (prevented by removing both import and usage).
   - If changing input dock layout causes the input bar to be hidden behind the screen (prevented by `shrink-0` within `flex flex-col h-full`).
