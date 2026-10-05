# Changes Report - worker_r7_frontend

## Overview
This report documents all frontend modifications made to fulfill the requirements of Milestone 7 (visual polish, layout symmetry, dynamic client fallback & retry mechanism, and community social feed enhancements).

---

## 1. `frontend/src/components/landing/LandingView.tsx`

### Description of Changes:
- **Cleaned Hero Visuals**: Completely unmounted and removed `<NeuralVisualPreview />` and its corresponding import, keeping the landing page clean, elegant, and focused on the Hero typography and interactive 3D feature cards.
- **Added Community CTA**: Added a secondary CTA button `"Khám phá Cộng đồng"` (or `"Explore Community"` in English) adjacent to `"Bắt đầu sáng tác ngay"` in the hero section.
- **Icon & Props**: Added `Users` icon from `lucide-react` to the CTA button. Added optional prop `onExploreCommunity?: () => void` to `Props` interface, defaulting safely to `onOpenAuth` if not provided.
- **Aesthetic**: Styled with translucent glassmorphic backdrop-blur (`bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border border-slate-200/80 dark:border-slate-800`), hover lift, and subtle shadows.

---

## 2. `frontend/src/components/layout/Sidebar.tsx`

### Description of Changes:
- **Renamed Tab**: Renamed the community navigation tab from `"Khám phá"` / `"Explore"` to `"Mạng xã hội"` (Vietnamese) or `"Community & Social"` (English) to directly reflect community networking features.
- **Icon Standardization**: Replaced `Compass` icon with `Users` icon from `lucide-react`, matching the design language across the landing page and social feed.

---

## 3. `frontend/src/lib/types.ts`

### Description of Changes:
- **ChatMessage Interface**: Extended `ChatMessage` with:
  - `is_offline_fallback?: boolean`: flags messages generated via client fallback.
  - `error_message?: string`: records error reason if needed.
  - `failed_prompt?: string`: preserves the original user prompt for one-click retry.
- **SocialComment Interface**: Extended `SocialComment` with:
  - `parent_comment_id?: number | null`: tracks parent comment ID for hierarchical replies.
  - `replies?: SocialComment[]`: recursive nested replies array.
- **InteractSocialPostPayload Interface**: Extended payload with:
  - `parent_comment_id?: number | null`: supports sending nested comment interactions to the backend.

---

## 4. `frontend/src/lib/api.ts`

### Description of Changes:
- **Resilient chatInterview**: Wrapped `chatInterview` in a structured try-catch block returning `{ status: 'error', message }` instead of throwing unhandled exceptions, allowing the frontend to capture network failures or server 500s gracefully.
- **Author Follow Endpoints**: Added `followAuthor(userId: number)` and `unfollowAuthor(userId: number)` invoking `POST /api/social/follow/{userId}` and `POST /api/social/unfollow/{userId}` with appropriate authentication headers.

---

## 5. `frontend/src/components/setup/UnifiedIntakeChat.tsx`

### Description of Changes:
- **Layout & Symmetry Normalization (R2)**:
  - **In-flow Centered Dock**: Eliminated fixed positioning (`fixed sm:left-64`) that caused persistent horizontal drifting between sidebar and main window. Switched both the message scroll container and bottom input dock to `max-w-4xl mx-auto w-full px-4` within an in-flow flex layout.
  - **Reduced Dead Bottom Padding**: Reduced excessive bottom padding from `pb-48` to `pb-6`, making the chat window feel compact and responsive.
  - **Symmetrical Avatars**: Symmetrical `w-9 h-9 rounded-xl` dimensions for both user and assistant avatars.
  - **Balanced Bubbles**: Symmetrical padding `px-4.5 py-3.5 rounded-2xl` for message bubbles.
  - **Balanced Starter Prompts**: Refactored the 4 starter prompt cards into a balanced 2x2 grid (`grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5`) with normalized card heights (`min-h-[140px]`).
- **Dynamic Client Fallback (R3)**:
  - Eliminated static canned fallback strings.
  - Implemented `extractNarrativeConcepts(userText)` to parse Vietnamese proper nouns, genres (historical, sci-fi, xianxia, detective, fantasy), and themes.
  - Implemented `generateDynamicClientFallback(prompt, history, lang)` which creates tailored narrative probing questions based on user input keywords when the backend AI is offline or unreachable.
- **Offline Connection Badge & Retry Mechanism (R3)**:
  - Integrated `is_offline_fallback` indicator in assistant messages with `WifiOff` badge.
  - Added a prominent `"Thử lại"` / `"Retry"` button on fallback messages that rewinds chat history to the failed turn and re-triggers `api.chatInterview`.

---

## 6. `frontend/src/components/social/CommunityFeedView.tsx`

### Description of Changes:
- **Author Follow/Unfollow Toggle**:
  - Added follow/unfollow toggle buttons on post cards and inside the reader modal.
  - Managed with optimistic state sets `followingAuthorIds` and `followLoadingIds`.
  - Uses `UserPlus` and `UserCheck` icons with smooth micro-interactions.
- **Threaded Hierarchical Comments**:
  - Implemented `organizedComments` memo that separates root comments (`parent_comment_id == null`) and builds `replyMap[parentId]`.
  - Added "Trả lời" (Reply) action button on each comment.
  - Added active replying banner ("Đang trả lời @...") with a cancel button above the comment input textarea.
  - Styled nested replies with left margin indentation (`ml-6 sm:ml-8`), subtle left border guides, and `CornerDownRight` connector icons.
- **Verification of Existing Community Features**:
  - Verified genre filters ("Tất cả", "Lịch sử", "Huyền huyễn", "Trinh thám", "Khoa viễn tưởng", "Đời thường", "Kỳ ảo").
  - Verified live search input filtering post titles, authors, and snippets.
  - Verified reading modal with like button, view count, and full-prose display.

---

## File Verification Summary
| File | Status | Key Features |
|---|---|---|
| `frontend/src/components/landing/LandingView.tsx` | Modified | NeuralVisualPreview removed, Community CTA added |
| `frontend/src/components/layout/Sidebar.tsx` | Modified | Tab renamed to "Mạng xã hội", Users icon |
| `frontend/src/lib/types.ts` | Modified | ChatMessage fallback fields, SocialComment parent_comment_id |
| `frontend/src/lib/api.ts` | Modified | chatInterview resilience, followAuthor/unfollowAuthor |
| `frontend/src/components/setup/UnifiedIntakeChat.tsx` | Modified | In-flow dock, dynamic fallback, retry button, 2x2 cards |
| `frontend/src/components/social/CommunityFeedView.tsx` | Modified | Author follow toggle, threaded comment replies |
