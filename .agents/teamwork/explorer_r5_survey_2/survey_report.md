# Detailed Frontend Survey & Mapping Report: Requirements #2 & #3
**Platform**: NarrAI Workspace v2.0  
**Target Areas**: Unified Intake Chat (ChatGPT/Gemini Style) & Seamless Transition to Story Editor  
**Date**: 2026-09-29  
**Investigator**: Teamwork Explorer Subagent (`explorer_r5_survey_2`)

---

## 1. Executive Summary

NarrAI's current frontend incorporates a 3-phase story setup wizard:
1. **Phase 1 (`Phase1Idea.tsx`)**: Displays 28 static genres grouped across 5 categories, a search filter, 7 trending theme cards, and a premise textarea.
2. **Phase 2 (`Phase2Interview.tsx`)**: A separate multi-step conversational interview screen with a "Bỏ qua hỏi đáp" (Skip) button.
3. **Phase 3 (`Phase3Controls.tsx`)**: A configuration screen with sliders for Story Length, Creativity, Pacing, and an SVG morphing Model Tier selector.

This multi-step wizard creates friction, breaks user flow, and contradicts modern conversational creation paradigms pioneered by ChatGPT and Gemini.

**Requirements #2 & #3 mandate**:
- **Requirement #2 (Unified Intake Chat)**: Completely abolish the 3-phase setup wizard (`Phase1Idea`, `Phase2Interview`, `Phase3Controls`). Replace with an elegant, full-screen conversational intake interface styled after Gemini/ChatGPT: spacious bubbles, a floating bottom input dock, starter suggestion pills for blank canvases, and a proactive AI co-creator assistant naturally adept in all literary genres, personal fiction liberty, Vietnamese history boundaries (Chính sử vs. Dã sử), and copyright/IP protection.
- **Requirement #3 (Seamless Transition)**: Empower the user with an instant *"Bắt đầu viết truyện ngay"* / *"Chốt cốt truyện"* action button (as well as AI-signaled readiness). When triggered, the system compresses the conversation into a 5-beat Refined Narrative Bible in 1-2 seconds, transitions directly to the `StoryEditor`, and immediately streams Chapter 1 in real time with instant `story_id` and `session_id` allocation.

---

## 2. Existing Frontend Codebase Architecture

### 2.1 Technology Stack & Directory Structure
- **Framework**: Next.js 14.2.23 (App Router, static export configured with `output: 'export'`)
- **React**: React 18.3.1
- **Styling**: Tailwind CSS 3.4.17 with custom WCAG AA compliant colors (`brand`, `paper`, `accent`) and dual typography (`Be Vietnam Pro` for UI sans-serif, `Merriweather` for manuscript serif).
- **Icons**: `lucide-react`
- **Component Hierarchy in `frontend/src/`**:
  - `app/layout.tsx`: Root layout mounting `ThemeProvider`, `ToastProvider`, `ThreeAmbientCanvas` (Layer 0), and children.
  - `app/page.tsx`: Central workspace view controller managing `view` (`landing` | `workspace`), `activeTab` (`setup` | `editor` | `comic`), and `setupPhase` (1 | 2 | 3).
  - `components/setup/`:
    * `Phase1Idea.tsx` (468 lines): Static genre grids & trending themes.
    * `Phase2Interview.tsx` (116 lines): Step 2 interview chatbox.
    * `Phase3Controls.tsx` (140 lines): Step 3 sliders & model tier selector.
  - `components/editor/`:
    * `StoryEditor.tsx` (268 lines): Manuscript paper canvas (`contentEditable`) with floating quick-action toolbar.
    * `AICopilotPanel.tsx` (310 lines): Right-side Copilot drawer with quick commands and chat.
  - `components/layout/`:
    * `Sidebar.tsx`: Left workspace navigation sidebar.
    * `LanguageSwitcher.tsx`, `ThemeToggle.tsx`.
  - `components/canvas/ThreeAmbientCanvas.tsx`: Layer 0 WebGL background.
  - `components/morphicons/`: Layer 2 SVG micro-interactions (`ModelSelectorMorphicon`, `CoinBadgeMorphicon`, `LikeButtonMorphicon`).
  - `components/portals/ClientPortal.tsx`: Layer 3 React portal wrapper.
  - `lib/api.ts`: Central API client (`streamStory`, `chatInterview`, `refinePrompt`, `generateComic`, auth, etc.).
  - `lib/types.ts`: TypeScript data models and response contracts.
  - `lib/i18n.ts`: Bilingual dictionary (`vi` & `en`).

---

## 3. Deep Analysis of Current Creation Flow vs. Target Requirements

### 3.1 Current Creation Flow (Friction & Bottlenecks)

```
[Landing / New Story]
         │
         ▼
[Phase 1: Phase1Idea.tsx]
   - 28 static genre buttons (categories: Romance, Fantasy/Sci-Fi, Action, Mystery, Slice of Life)
   - Search input for genres
   - 7 trending topic cards (Healing, Rebirth, Contract Marriage, etc.)
   - Premise textarea
   - User clicks "Tiếp tục ➔"
         │
         ▼ (calls api.chatInterview)
[Phase 2: Phase2Interview.tsx]
   - Interview chat screen with Bot & User bubbles
   - User answers questions or clicks "Bỏ qua hỏi đáp, chốt dàn ý luôn"
         │
         ▼ (calls api.refinePrompt)
[Phase 3: Phase3Controls.tsx]
   - Sliders: Story Length (short/medium/long), Creativity (1-3), Pacing (1-3)
   - Model Tier selector (Flash/Versatile/Master)
   - User clicks "Bắt đầu Chấp bút ✍️"
         │
         ▼ (calls api.streamStory)
[StoryEditor.tsx & AICopilotPanel.tsx]
   - Sets activeTab to "editor"
   - Streams story chunks into manuscript canvas
```

**Identified Issues**:
1. **Excessive click barriers**: User must go through 3 completely different screens before a single sentence of story is penned.
2. **Cognitive overload**: Forcing users to choose from 28 genre tags upfront stifles creative freedom and feels like a bureaucratic form rather than an intuitive AI studio.
3. **Disjointed mental model**: The interview chat in Phase 2 is isolated from the initial idea input in Phase 1 and the controls in Phase 3.
4. **Delays and unnecessary steps**: Even when the user has a crystal-clear idea ready to write, they must navigate Phase 1 -> Phase 2 (wait for AI question or skip) -> Phase 3 (adjust sliders) -> Phase 3 submit.

### 3.2 Target Unified Flow (Requirements #2 & #3)

```
[Landing / New Story]
         │
         ▼
[Unified Intake Chat (Gemini / ChatGPT Style)]
   - Clean, full-screen canvas with ambient Layer 0 Dong Son drum / particle backdrop
   - Blank state: Warm greeting + 4-5 inspiring starter pills (Vietnamese History, Cyberpunk, Xianxia, Thriller)
   - Conversational intake: User talks directly with AI Q&A assistant
   - Assistant naturally understands genres, encourages personal fiction freedom, enforces Vietnamese historical integrity (chính sử vs dã sử), and warns against commercial copyright infringement
   - Seamless Controls Dock: Compact Model Tier pill (Flash/Versatile/Master) & Length toggle built into the floating dock or header
         │
         ├── User clicks "Bắt đầu viết truyện ngay" (or AI detects readiness & user confirms)
         │
         ▼ (Takes 1-2s: calls api.refinePrompt to compress Refined Narrative Bible)
[Story Editor: StoryEditor.tsx]
   - Instant router/tab transition: activeTab = "editor"
   - Real-time streaming generation commences immediately: api.streamStory("init-story", ...)
   - Words stream onto the manuscript paper canvas live
   - story_id and session_id captured and locked in state
   - AI Copilot panel stands by for targeted manuscript surgery
```

---

## 4. Component Inventory & Action Plan

### 4.1 Components to Deprecate and Eliminate

| Component File | Lines | Current Role | Rationale for Elimination |
| :--- | :--- | :--- | :--- |
| `src/components/setup/Phase1Idea.tsx` | 468 | 28 static genre chips, category search, 7 trending theme cards, premise textarea | Direct violation of Requirement #2: "Completely eliminate old static genre chips (Phase 1 Idea chips)". Stifles natural conversational intake. |
| `src/components/setup/Phase2Interview.tsx` | 116 | Isolated chat container for interview questions with skip button | Replaced by full-screen Unified Intake Chat. Multi-phase wizard is abolished. |
| `src/components/setup/Phase3Controls.tsx` | 140 | Standalone sliders page for length, creativity, pacing, model tier | Sliders and tier selection are embedded compactly within the Unified Intake Chat floating controls / header, eliminating the intermediate step. |

### 4.2 New Component to Create: `UnifiedIntakeChat.tsx`
- **Location**: `frontend/src/components/setup/UnifiedIntakeChat.tsx`
- **Role**: Full-screen ChatGPT / Gemini style intake interface.
- **Design Specifications**:
  1. **Layout**:
     - Height: `100vh` (or `calc(100vh - header)`), flex-col, overflow-hidden.
     - Centered message scroll area (`max-w-4xl mx-auto w-full px-4 sm:px-6 py-6 flex-1 overflow-y-auto`).
     - Ambient background: Layer 1 DOM with high transparency (`bg-slate-50/60 dark:bg-slate-950/60 backdrop-blur-sm`), allowing the Layer 0 Three Ambient Canvas to shine through.
  2. **Blank State (Zero Messages)**:
     - Prominent NarrAI logo mark / subtle sparkling badge.
     - Warm hero greeting: *"Bạn đang ấp ủ câu chuyện gì hôm nay?"* / *"What story would you like to create today?"*
     - Subtitle emphasizing AI capabilities: *"Trò chuyện tự do bằng bất kỳ ý tưởng nào. NarrAI am hiểu mọi thể loại văn học, tôn trọng sự thật lịch sử và đồng hành cùng bạn từ ý niệm đầu tiên đến tác phẩm hoàn chỉnh."*
     - **Inspiration Starter Pills** (Clean, clickable cards):
       * 📜 **Lịch Sử Việt Nam**: *"Một nghĩa sĩ áo vải thời Hậu Lê mang gươm báu bảo vệ bến sông lịch sử..."* (Guidance on Chính sử vs Dã sử).
       * 🚀 **Khoa Học Viễn Tưởng**: *"Hà Nội năm 2099 nơi trí tuệ nhân tạo và những ký ức truyền thống giao thoa..."* (Free Personal Fiction).
       * ⚔️ **Tiên Hiệp & Kỳ Ảo**: *"Thiếu niên vô danh sở hữu linh căn dị biến, từng bước phá giải cổ trận nghìn năm..."* (Original IP creation).
       * 🌿 **Đời Sống & Chữa Lành**: *"Rời bỏ nhịp sống hối hả đô thị, trở về thung lũng sương mù mở tiệm sách nhỏ..."* (Slice of Life).
     - Clicking any starter pill immediately injects the prompt into the input bar or sends it to the AI.
  3. **Spacious Chat Message Bubbles**:
     - User bubble: Aligned right, rounded-2xl rounded-tr-sm, elegant background (`bg-brand-700 text-white shadow-sm`), clean typography.
     - Assistant bubble: Aligned left, rounded-2xl rounded-tl-sm, crisp card background (`bg-white/95 dark:bg-slate-900/95 border border-slate-200/80 dark:border-slate-800 shadow-sm text-slate-800 dark:text-slate-100`), with NarrAI avatar.
     - Markdown & formatting support for bullet points, bold text, and dialogue cues.
     - Subtle "Thinking" pulse when waiting for AI response.
  4. **Floating Action Trigger: "Bắt đầu viết truyện ngay"**:
     - Positioned at the top right of the chat header AND/OR as a floating action bar above the bottom dock.
     - State-aware styling:
       * When chat has >= 1 turn or when AI outputs `[READY]`: Button pulses with an attractive highlight (`bg-emerald-600 hover:bg-emerald-700 text-white font-bold shadow-lg shadow-emerald-600/20`), signaling readiness.
       * Includes sparkler icon (`Sparkles`), tooltip, and estimated compression time indicator: *"Chốt cốt truyện & Chấp bút ngay (1-2s)"*.
  5. **Floating Bottom Input Dock**:
     - Fixed or floating at bottom: `max-w-3xl mx-auto w-full px-4 pb-6 pt-2`.
     - Styling: Glassmorphic pill (`bg-white/85 dark:bg-slate-900/85 backdrop-blur-xl border border-slate-200/80 dark:border-slate-800 rounded-2xl shadow-xl p-2 sm:p-3`).
     - Auto-expanding textarea (`rows={1}` up to `max-h-36`), responsive height, seamless keyboard handling (`Enter` to send, `Shift+Enter` for line break).
     - Inline quick-controls:
       * Compact Model Selector: Integrated `ModelSelectorMorphicon` or compact tier pill (Flash / Versatile / Master).
       * Story Length selector pill (Ngắn / Vừa / Dài).
       * Action button: Glowing Send icon (`Send` / `ArrowUp`).

### 4.3 Files to Refactor

#### 1. `frontend/src/app/page.tsx`
- **Current State**:
  - Manages `setupPhase: 1 | 2 | 3`.
  - Imports `Phase1Idea`, `Phase2Interview`, `Phase3Controls`.
  - Handles `handlePhase1Continue`, `handleSendMessage`, `handleSkipInterview`, `handleStartWriting`.
- **Refactoring Required**:
  - Remove `setupPhase` state entirely.
  - Remove imports of `Phase1Idea`, `Phase2Interview`, `Phase3Controls`.
  - Import `UnifiedIntakeChat`.
  - Add unified transition handler: `handleStartWritingFromChat(chatHistory, options)`.
  - Wire `api.refinePrompt(chatHistory)` into a 1-2 second compression step with visual loading indicator, followed immediately by `setActiveTab("editor")` and `api.streamStory`.
  - Support instant `storyId` and `sessionId` allocation.

#### 2. `frontend/src/components/layout/Sidebar.tsx`
- **Current State**:
  - `onNewStory` resets `setActiveTab("setup")` and `setSetupPhase(1)`.
- **Refactoring Required**:
  - Update `onNewStory` to reset the Unified Intake Chat (clears chat history, resets input, sets `activeTab = "setup"`).
  - Prepare for Requirement #4 "Bài đăng" navigation tab.

#### 3. `frontend/src/components/editor/StoryEditor.tsx`
- **Current State**:
  - Top bar has title, word count, "Chuyển thể Comic", "Tải bản thảo (TXT)".
- **Refactoring Required**:
  - Add "Lưu & Đăng bài" (Save & Publish) button on top bar (Requirement #4 linkage).
  - Ensure manuscript canvas cleanly receives initial streaming chunks without layout jitter or flash.

#### 4. `frontend/src/lib/types.ts`
- **Current State**:
  - Has `InterviewResponse`, `RefineResponse`, `ChatMessage`, `StoryLength`, `TrendingTopic`, `GenreCategory`.
- **Refactoring Required**:
  - Ensure `ChatMessage` supports optional metadata (e.g. `is_ready`, `timestamp`).
  - Add `IntakeChatProps` and `StoryGenerationOptions` interfaces.

#### 5. `frontend/src/lib/i18n.ts`
- **Current State**:
  - Contains step 1, 2, 3 labels (`step1_title`, `genres_label`, `step2_title`, `skip_chat_btn`, `step3_title`).
- **Refactoring Required**:
  - Add new bilingual keys for Unified Intake Chat:
    * `intake_welcome_title`, `intake_welcome_sub`.
    * `intake_input_placeholder`.
    * `start_writing_now_btn` ("Bắt đầu viết truyện ngay"), `finalize_plot_btn` ("Chốt cốt truyện").
    * `refining_narrative_bible` ("Đang cô đọng cốt truyện & khởi tạo bản thảo...").
    * Starter prompt pill titles and snippets.

---

## 5. Streaming Generation Hooks & Backend Interface Mapping

### 5.1 Communication Flow for Q&A Assistant
- **Endpoint**: `POST /api/chat-interview`
- **Payload**:
  ```json
  {
    "chat_history": [
      { "role": "user", "content": "Tôi muốn viết về thời nhà Trần đánh giặc Nguyên Mông..." }
    ]
  }
  ```
- **Backend Handler (`backend/main.py:362` & `backend/agents/qa_refiner.py:9`)**:
  - Backend `QARefiner.chat_interview` uses `GroqClient("qwen/qwen3.8-27b")`.
  - System prompt already mandates:
    1. **Literary Genres Knowledge**: Fantasy, Urban, Mystery, Folklore horror, Sci-fi, Romance, History.
    2. **Personal Fiction Freedom**: 100% imaginative liberty when creating fictional/modern worlds.
    3. **Vietnamese History Guidelines**: Strict authenticity for real events (Chính sử) vs. fictional perspectives in real eras (Dã sử).
    4. **Copyright & Original IP Protection**: Advises creating original characters and worldbuilding rather than copying protected commercial IPs (Marvel, Harry Potter, Naruto).
    5. **Readiness Evaluation**: Appends `[READY]` tag when the narrative premise is sufficiently formed.
- **Frontend Behavior**:
  - Strips `[READY]` from visible assistant prose.
  - If `is_ready === true`, unlocks/highlights the *"Bắt đầu viết truyện ngay"* action button.

### 5.2 Compression into Refined Narrative Bible
- **Endpoint**: `POST /api/refine-prompt`
- **Payload**:
  ```json
  {
    "chat_history": [
      { "role": "user", "content": "..." },
      { "role": "assistant", "content": "..." }
    ]
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "refined_prompt": "TIÊU ĐỀ: ... \nTHỂ LOẠI: ... \nCẤU TRÚC 5 NHỊP KỊCH TÍNH: \nBeat 1: Hook ... \nBeat 2: Complication ... \nBeat 3: Turning Point ... \nBeat 4: Climax ... \nBeat 5: Cliffhanger ..."
  }
  ```
- **Performance**: High-speed LLM summarization (~1-2 seconds).

### 5.3 Streaming Generation into Story Editor
- **Endpoint**: `POST /api/init-story` (for Chapter 1 / Long Novel) or `POST /api/generate-story` (for Standard/Short Draft).
- **Client Method**: `api.streamStory(endpoint, payload, onChunk, onComplete, onError)` in `frontend/src/lib/api.ts`.
- **Streaming Protocol**:
  - Native `ReadableStream` over HTTP `POST`.
  - Client reads chunks via `reader.read()` and decodes with `TextDecoder("utf-8")`.
  - Real-time clean text unwrapping using `cleanText(fullAccumulated)` which dynamically strips:
    * `[SESSION_ID:<uuid>]`
    * `[STORY_ID:<id>]`
    * `[GENERATION_ERROR:<msg>]`
- **Instant Allocation & State Synchronization**:
  - When user transitions to Editor:
    ```typescript
    setActiveTab("editor");
    setStoryContent("");
    setStreaming(true);
    ```
  - As chunks arrive, `onChunk(chunk, cleanAccumulated)` triggers `setStoryContent(cleanAccumulated)`.
  - On stream completion, `onComplete({ fullText, cleanText, sessionId, storyId })`:
    * `setStoryId(result.storyId)`: Enables instant comic adaptation and save/publish actions.
    * `setSessionId(result.sessionId)`: Sets up multi-turn chapter continuation memory (`/api/generate-chapter`).
    * Updates Copilot welcome message: *"Chương 1 đã sẵn sàng! Bạn có thể trực tiếp bôi đen để chỉnh sửa hoặc ra lệnh cho tôi bên dưới."*

---

## 6. TypeScript Interfaces & Data Contracts

### 6.1 Unified Intake Chat Props Contract
```typescript
// frontend/src/components/setup/UnifiedIntakeChat.tsx

import { Language } from "@/lib/i18n";
import { ChatMessage, StoryLength } from "@/lib/types";
import { ModelTier } from "@/components/morphicons/ModelSelectorMorphicon";

export interface StarterPromptSuggestion {
  id: string;
  categoryVi: string;
  categoryEn: string;
  titleVi: string;
  titleEn: string;
  promptVi: string;
  promptEn: string;
  icon: string;
  badgeVi: string;
  badgeEn: string;
}

export interface UnifiedIntakeChatProps {
  lang: Language;
  history: ChatMessage[];
  onSendMessage: (content: string) => Promise<void> | void;
  onStartWriting: (options: {
    modelTier: ModelTier;
    length: StoryLength;
    promptOverride?: string;
  }) => Promise<void> | void;
  loading: boolean;
  isRefining: boolean;
  onClearChat?: () => void;
}
```

### 6.2 Stream Story Contract in `frontend/src/lib/api.ts`
```typescript
export interface StreamStoryResult {
  fullText: string;
  cleanText: string;
  sessionId?: string;
  storyId?: number;
  error?: string;
}

export interface StreamStoryPayload {
  refined_prompt: string;
  story_length: StoryLength;
  session_id?: string;
}
```

---

## 7. Precise Step-by-Step Implementation Plan for Implementer

1. **Phase 1: Build `UnifiedIntakeChat.tsx`**
   - Create `frontend/src/components/setup/UnifiedIntakeChat.tsx`.
   - Implement empty state with inspiring starter cards covering Vietnamese History (Chính sử vs. Dã sử), Sci-Fi, Xianxia, and Slice of Life.
   - Implement spacious chat bubbles (distinct styling for Assistant vs. User).
   - Implement floating bottom dock with auto-expanding textarea, Model Tier selector (`ModelSelectorMorphicon`), length picker, and send button.
   - Implement floating/header "Bắt đầu viết truyện ngay" button with pulsing highlight when ready.

2. **Phase 2: Refactor `frontend/src/app/page.tsx`**
   - Eliminate `setupPhase` (1, 2, 3) state and remove imports of `Phase1Idea`, `Phase2Interview`, `Phase3Controls`.
   - Mount `<UnifiedIntakeChat />` in `activeTab === "setup"`.
   - Implement `handleStartWritingDirectly`:
     * Calls `api.refinePrompt(chatHistory)` (takes 1-2s).
     * Instantly navigates to `activeTab = "editor"`.
     * Initiates `api.streamStory` with Chapter 1 generation.
     * Captures `sessionId` and `storyId` on stream completion.

3. **Phase 3: Update `Sidebar.tsx` & `i18n.ts`**
   - In `Sidebar.tsx`: Ensure "Viết truyện mới" (`onNewStory`) cleanly clears chat history and returns to the pristine Unified Intake Chat.
   - In `i18n.ts`: Add all new Vietnamese and English translation strings for Gemini/ChatGPT-style intake and starter pills.

4. **Phase 4: Remove / Deprecate Legacy Setup Files**
   - Safely remove or replace `Phase1Idea.tsx`, `Phase2Interview.tsx`, `Phase3Controls.tsx` to ensure zero dead code or dangling references.

5. **Phase 5: Verification & Quality Assurance**
   - Verify zero TypeScript or Next.js build errors (`next build`).
   - Verify smooth transitions between chat intake and manuscript editor.
   - Verify bilingual rendering (VI/EN) across all new chat elements.
   - Verify zero z-index or rendering conflicts with Three Ambient Canvas (Layer 0) and Client Portals (Layer 3).

---
*Report authored by Teamwork Explorer Subagent (`explorer_r5_survey_2`). End of document.*
