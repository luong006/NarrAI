# Frontend UI/UX Comprehensive Survey & Technical Architecture Report (R1, R2, R4)

**Surveyor**: `explorer_r7_frontend`  
**Date**: 2026-10-05  
**Target Scope**: NarrAI Frontend Next.js 14 Web Application (`e:\NarrAI\frontend`)

---

## Executive Summary

This report delivers a full architectural and component-level investigation for requirements **R1**, **R2**, and **R4** of the NarrAI platform:
1. **R1 (Landing Page De-cluttering)**: Detailed analysis of `<NeuralVisualPreview />` in `LandingView.tsx` and `app/page.tsx`. Verification of zero-impact removal on `@tensorflow/tfjs` dependencies and styling plan for a clean, minimal Hero + Core Features layout.
2. **R2 (Unified Intake Chat Symmetry & Alignment)**: Diagnosis of hardcoded viewport positioning (`fixed sm:left-64` at line 597) in `UnifiedIntakeChat.tsx`, avatar/bubble alignment discrepancies, starter prompt grid breathing room, and dynamic fallback error handling.
3. **R4 (Social Network & Community Discoverability)**: Plan for upgrading the Sidebar navigation tab from "Bài đăng" to "Mạng xã hội" / "Cộng đồng tác giả" with Lucide `Users` icon, embedding a prominent "Khám phá Cộng đồng" CTA in the Landing Page Hero, and auditing `CommunityFeedView.tsx` for follow author and threaded comments.

---

## 1. R1: Landing Page & `<NeuralVisualPreview />` Deconstruction

### 1.1 Mounting, Imports, and State Analysis
- **Target File**: `frontend/src/components/landing/LandingView.tsx`
  - **Import**: Line 10:
    ```tsx
    import { NeuralVisualPreview } from "@/components/canvas/NeuralVisualPreview";
    ```
  - **Mount Location**: Lines 84-88:
    ```tsx
    {/* AI Art & Neural Style Preview Showcase (Feature 30) */}
    <section className="max-w-4xl mx-auto px-6 pb-12">
      <NeuralVisualPreview lang={lang} />
    </section>
    ```
  - **Props passed**: Only `lang={lang}`.
- **Secondary Usage**: `frontend/src/app/page.tsx`
  - Line 23: `import { NeuralVisualPreview } from "@/components/canvas/NeuralVisualPreview";`
  - Line 168: `const [isNeuralModalOpen, setIsNeuralModalOpen] = useState(false);`
  - Lines 984-998: Modal rendering `isNeuralModalOpen && (<div ...><NeuralVisualPreview lang={lang} /></div>)`.
  - *Note*: `setIsNeuralModalOpen(true)` is never invoked anywhere in the application.

### 1.2 Impact on TensorFlow.js & System Modules
- **File Checked**: `frontend/src/components/canvas/NeuralVisualPreview.tsx` (375 lines).
  - Despite its name, `NeuralVisualPreview.tsx` uses standard HTML5 Canvas 2D (`canvas.getContext("2d")`) to render CPU-based harmonic wave math (`Math.sin`, `Math.cos`). It does **not** import `@tensorflow/tfjs` or `@tensorflow/tfjs-core`.
- **Actual TensorFlow.js Usage**:
  - Found in `frontend/src/services/tfjsRecommender.ts` (Universal Sentence Encoder Lite client embeddings and local cosine re-ranking) and `frontend/src/services/indexedDBCache.ts`.
  - `@tensorflow/tfjs` in `package.json` (`^4.20.0`) is entirely untouched and unimpacted by the removal of `<NeuralVisualPreview />`.
- **Conclusion**:
  - Removing `<NeuralVisualPreview />` from `LandingView.tsx` has **zero negative impact** on TensorFlow.js, WebGL canvas (`ThreeAmbientCanvas.tsx`), or any data pipelines.

### 1.3 Recommended Layout for Clean & Minimal Landing Page
By removing lines 10 and 84-88 from `LandingView.tsx`:
1. **Top Navbar**: Logo NarrAI Pro, Layer 2 Coin Badge Morphicon, Language Switcher, Theme Toggle, Login button.
2. **Hero Section**:
   - Translucent badge: `Sparkles` + `t.hero_badge` + `LikeButtonMorphicon`.
   - Title: `t.hero_title` (4xl/6xl font-extrabold).
   - Subtitle: `t.hero_sub`.
   - **Dual Action Button Group**:
     - Primary CTA: "Bắt đầu sáng tác ngay" (`t.hero_cta`) -> triggers `onOpenAuth` (or direct drafting).
     - Secondary CTA (R4): "Khám phá Cộng đồng" -> triggers `onExploreCommunity()` directly to the community feed.
3. **Core Features Section** (3D Interactive Tilt Cards):
   - Card 1: `Bot` — Trợ lý AI Q&A Đồng sáng tác (am hiểu Lịch sử Việt Nam & Hư cấu tự do).
   - Card 2: `Edit3` — Phẫu thuật Bản thảo Đa mục tiêu (bôi đen sửa đoạn, giữ nguyên mạch văn).
   - Card 3: `ImageIcon` — Chuyển thể Manga Đen trắng 100% (Visual DNA nhất quán).
4. **Footer**: Clean copyright footer.

The resulting page is ultra-fast, visually calm, and immediately directs creators to either writing or reading community works.

---

## 2. R2: Unified Intake Chat Layout & Symmetry Analysis

### 2.1 The Root Cause of Bottom Dock Asymmetry
- **File**: `frontend/src/components/setup/UnifiedIntakeChat.tsx`
- **Location**: Line 597:
  ```tsx
  {/* Floating Bottom Dock (Layer 1 Semantic DOM with Layer 2 Morphicon) */}
  <div className="fixed bottom-0 left-0 right-0 sm:left-64 p-3 sm:p-5 bg-gradient-to-t from-slate-50/95 via-slate-50/80 to-transparent dark:from-slate-950/95 dark:via-slate-950/80 dark:to-transparent z-20 pointer-events-none">
    <div className="max-w-3xl mx-auto w-full pointer-events-auto">
  ```
- **Architectural Flaw**:
  1. `fixed` positions relative to the entire browser window (viewport), rather than the parent workspace `<main className="flex-1 flex overflow-hidden">`.
  2. `sm:left-64` assumes the sidebar is always on-screen and exactly 256px wide. Any responsive shift, mobile toggle, or screen scaling causes the input bar to drift horizontally away from the conversation container.
  3. Because the dock was `fixed`, the scroll area had to use an aggressive padding `pb-48` (line 471) to prevent message occlusion.

### 2.2 Solution: Fluid Flex/Sticky Dock Architecture
In `UnifiedIntakeChat.tsx`, the outer container is already `flex flex-col h-full w-full relative`:
```tsx
<div className="flex flex-col h-full w-full bg-slate-50/40 dark:bg-slate-950/40 ... relative">
  {/* Header (shrink-0) */}
  <header className="h-14 shrink-0 ...">...</header>

  {/* Scroll Area (flex-1) */}
  <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8 pb-4">
    <div className="max-w-3xl mx-auto w-full flex flex-col min-h-full justify-between">
      ... messages ...
    </div>
  </div>

  {/* Integrated Dock (shrink-0) */}
  <div className="shrink-0 w-full p-3 sm:p-4 bg-gradient-to-t from-slate-50/95 via-slate-50/90 to-transparent dark:from-slate-950/95 dark:via-slate-950/90 dark:to-transparent border-t border-slate-200/50 dark:border-slate-800/50 z-20">
    <div className="max-w-3xl mx-auto w-full">
      ... glassmorphic capsule & controls ...
    </div>
  </div>
</div>
```
**Benefits**:
- 100% matched to the width and horizontal center of the chat thread.
- Zero hardcoded pixel/rem offsets (`sm:left-64` completely removed).
- `pb-48` is reduced to `pb-4` or `pb-6`, and `messagesEndRef.current?.scrollIntoView()` lands perfectly at the true bottom.

### 2.3 User & AI Message Bubble Balance
- **Current Bubble Code** (lines 523-570):
  - User avatar: `w-8 h-8 rounded-full bg-slate-800 text-white dark:bg-slate-200 dark:text-slate-900` ("U").
  - AI avatar: `w-8 h-8 rounded-full bg-gradient-to-tr from-brand-600 to-indigo-600 text-white` (`Sparkles`).
  - User bubble: `max-w-[88%] sm:max-w-[80%] px-4 py-3.5 rounded-2xl bg-brand-600 text-white rounded-tr-sm shadow-md`.
  - AI bubble: `max-w-[88%] sm:max-w-[80%] px-4 py-3.5 rounded-2xl bg-white/80 dark:bg-slate-900/80 border border-slate-200/80 dark:border-slate-800/80 text-slate-800 dark:text-slate-100 rounded-tl-sm shadow-sm`.
- **Refinement Recommendation**:
  - Increase avatar size slightly to `w-9 h-9` with consistent subtle borders (`border border-slate-200 dark:border-slate-700/60`).
  - Replace the plain "U" text avatar with a Lucide `User` icon or gradient background for parity with the AI `Sparkles` icon.
  - Standardize bubble padding: `px-4.5 py-3.5` with symmetrical rounded corners (`rounded-2xl`).
  - Align typing state (lines 574-586) padding (`px-4.5 py-3.5`) to eliminate micro-jumps when typing transitions to a message.

### 2.4 Starter Prompt Cards (4 Pills) Airy & Symmetrical Grid
- **Current Code** (lines 489-516):
  ```tsx
  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full text-left">
    {starterIdeas.map((item) => (
      <button key={item.id} className="p-4 rounded-2xl ...">
  ```
- **Issues**:
  - `gap-3.5` (14px) feels tight on desktop monitors.
  - Card heights can fluctuate if text wrapping differs, making the 2-column grid look uneven.
  - `line-clamp-2` truncates without providing breathing room for the badge and explore arrow.
- **Recommended Adjustments**:
  - Grid: `grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-5 w-full text-left`.
  - Card wrapper: `p-5 sm:p-5.5 rounded-2xl min-h-[155px] flex flex-col justify-between border border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-slate-900/70 hover:border-indigo-400 dark:hover:border-indigo-500 hover:shadow-lg dark:hover:shadow-indigo-950/20 hover:-translate-y-0.5 transition-all`.
  - Header: Stacked category badge with `text-[10px] font-semibold tracking-wide uppercase px-2 py-0.5 rounded-md` and bold title `text-xs sm:text-sm font-bold`.
  - Description: `text-xs text-slate-500 dark:text-slate-400 leading-relaxed font-normal line-clamp-3`.

### 2.5 Error Handling & Dynamic Client Fallback (R3 Frontend Connection)
- **Problem**: Lines 289-310 show hardcoded static replies on any backend error:
  - `"Ý tưởng của bạn rất cuốn hút! Hãy chia sẻ thêm về nhân vật chính..."`
  - `"Đang kết nối lại với trợ lý NarrAI..."`
- **Solution**:
  1. Remove static boilerplate responses.
  2. Implement an intelligent keyword-based client fallback parser (`generateDynamicClientFallback(userInput)`):
     - If the user mentions historical keywords ("Trần Hưng Đạo", "Lý Thường Kiệt", "Bạch Đằng"), suggest focusing on historical grounding vs. personal drama.
     - If sci-fi/cyberpunk keywords appear, suggest exploring technology consequences or identity conflict.
     - If cultivation/fantasy appears, suggest magic hierarchy or forbidden artifacts.
  3. If network is unreachable, render an unobtrusive inline notification bar with a "Thử lại" (Retry) action.

---

## 3. R4: Social Network Navigation & Community Discoverability

### 3.1 Sidebar Navigation Update
- **File**: `frontend/src/components/layout/Sidebar.tsx`
- **Current Tab Button** (lines 151-163):
  ```tsx
  {/* Bảng tin Bài đăng (Community Feed) */}
  <button
    onClick={() => onTabChange?.("posts")}
    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
      activeTab === "posts"
        ? "bg-violet-50 dark:bg-violet-950/70 text-violet-700 dark:text-violet-300 font-bold"
        : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
    }`}
  >
    <Compass className="w-4 h-4 text-violet-600 dark:text-violet-400" />
    <span>{t.tab_posts || (lang === "vi" ? "Bài đăng" : "Community Feed")}</span>
  </button>
  ```
- **Changes**:
  1. Replace icon `Compass` with `Users` from `lucide-react`:
     ```tsx
     import { ..., Users } from "lucide-react";
     ```
  2. Update text label:
     - In `frontend/src/lib/i18n.ts`:
       - `vi`: `tab_community: "Mạng xã hội"`, `tab_community_desc: "Cộng đồng tác giả"`
       - `en`: `tab_community: "Community & Social"`, `tab_community_desc: "Creator Network"`
     - In `Sidebar.tsx`:
       ```tsx
       <Users className="w-4 h-4 text-violet-600 dark:text-violet-400" />
       <span>{t.tab_community || (lang === "vi" ? "Mạng xã hội" : "Community")}</span>
       ```

### 3.2 Landing Page "Khám phá Cộng đồng" CTA
- **File**: `frontend/src/components/landing/LandingView.tsx`
- **Add prop**:
  ```tsx
  interface Props {
    lang: Language;
    onLanguageChange: (lang: Language) => void;
    onOpenAuth: () => void;
    onExploreCommunity?: () => void;
  }
  ```
- **In Hero button section**:
  ```tsx
  <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
    <button
      onClick={onOpenAuth}
      className="w-full sm:w-auto px-8 py-4 rounded-xl text-base font-bold text-white bg-brand-700 hover:bg-brand-800 shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2 transition-all hover:scale-[1.02]"
    >
      <span>{t.hero_cta}</span>
      <ArrowRight className="w-4 h-4" />
    </button>
    <button
      onClick={onExploreCommunity}
      className="w-full sm:w-auto px-7 py-4 rounded-xl text-base font-bold text-slate-800 dark:text-slate-200 bg-white/80 dark:bg-slate-900/80 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center justify-center gap-2 transition-all hover:scale-[1.02] backdrop-blur-sm"
    >
      <Users className="w-4 h-4 text-violet-600 dark:text-violet-400" />
      <span>{lang === "vi" ? "Khám phá Cộng đồng" : "Explore Community"}</span>
    </button>
  </div>
  ```
- **In `frontend/src/app/page.tsx`**:
  Wire `onExploreCommunity`:
  ```tsx
  <LandingView
    lang={lang}
    onLanguageChange={handleLanguageChange}
    onOpenAuth={() => setIsAuthOpen(true)}
    onExploreCommunity={() => {
      setView("workspace");
      setActiveTab("posts");
    }}
  />
  ```

### 3.3 Community View Component Audit (`CommunityFeedView.tsx`)
- **File**: `frontend/src/components/social/CommunityFeedView.tsx` (943 lines)
- **Features Already Present & Working**:
  - **Feed Grid**: Interactive 3D tilt cards, cover art preview, genre tags, fanfiction disclaimers, reading time, view counter.
  - **Morphicon Like Button**: Full integration with optimistic updates (`LikeButtonMorphicon`).
  - **Genre Filter**: 6 genre pills ("Tất cả", "Lịch sử", "Tiên hiệp", "Khoa học viễn tưởng", "Trinh thám", "Đô thị").
  - **Search Input**: Live client-side search by title, author name, username, or author ID with clear (X) button.
  - **Fullscreen Comic Reader**: Sequential carousel with swipe gestures, keyboard arrow keys, page counter, esc key, and thumbnail strip.
- **Identified Gaps & Required Enhancements**:
  1. **Follow / Unfollow Author Action**:
     - Backend API exists at `POST /api/social/follow/{user_id}` and `POST /api/social/unfollow/{user_id}`.
     - Add `followAuthor` and `unfollowAuthor` wrappers in `frontend/src/lib/api.ts`.
     - In `CommunityFeedView.tsx`, add a "Theo dõi" (Follow) button in the Author row of both Post Card and Reader Modal.
  2. **Threaded Comments (Hierarchical Replies)**:
     - Backend supports `parent_comment_id` in `POST /api/social/interact` and returns it in `GET /api/social/post/{post_id}`.
     - Add `parent_comment_id?: number | null` and `replies?: SocialComment[]` to `SocialComment` in `types.ts`.
     - In `CommunityFeedView.tsx`, add a "Trả lời" (Reply) button per comment. When clicked, set `replyingToComment` and submit `parent_comment_id`. Render nested replies indented with a left border (`border-l-2 border-indigo-400/40 pl-3 ml-6`).

---

## 4. Verification & Testing Matrix

| Feature | Verification Method | Expected Result |
|---|---|---|
| R1: Landing Page | Inspect `LandingView.tsx` | No `<NeuralVisualPreview />`, clean Hero + Cards, builds cleanly |
| R1: TFJS Integrity | Inspect `services/tfjsRecommender.ts` | Recommender logic and embeddings intact |
| R2: Chat Dock Center | Inspect `UnifiedIntakeChat.tsx` | Dock is container-relative flex/sticky, 0 `fixed sm:left-64` |
| R2: Card Grid Spacing | Inspect `starterIdeas` layout | 4 cards evenly spaced with `gap-4 sm:gap-5`, balanced min-height |
| R4: Sidebar Tab | Inspect `Sidebar.tsx` | Icon is `Users`, label is "Mạng xã hội" / "Community & Social" |
| R4: Landing CTA | Inspect `LandingView.tsx` & `page.tsx` | "Khám phá Cộng đồng" navigates straight to `posts` tab |
| R4: Social Features | Inspect `CommunityFeedView.tsx` | Feed, like, follow author, threaded comments, search box all functional |
| System Build | Static verification | 0 syntax errors, valid TypeScript definitions |
