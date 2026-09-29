# Handoff Report: Frontend Survey for Requirements #2 & #3
**Agent**: `explorer_r5_survey_2` (Teamwork Explorer)  
**Task**: Survey & Map Frontend Codebase for Unified Intake Chat & Seamless Transition to Story Editor  
**Target Milestone**: Requirements #2 & #3 Architecture & Implementation Blueprint  
**Date**: 2026-09-29  

---

## 1. Observation

1. **Legacy Multi-Phase Setup Components in `frontend/src/components/setup/`**:
   - `frontend/src/components/setup/Phase1Idea.tsx` (lines 10–69, 147–232, 310–467): Defines 28 static genres grouped across 5 categories (`GENRE_CATEGORIES`), 7 trending themes (`FALLBACK_THEMES`), category search bar, and premise textarea.
   - `frontend/src/components/setup/Phase2Interview.tsx` (lines 31–115): Implements a separate interview chat interface with Bot/User message bubbles, textarea input, and a "Bỏ qua hỏi đáp, chốt dàn ý luôn" (`onSkip`) button.
   - `frontend/src/components/setup/Phase3Controls.tsx` (lines 47–139): Renders sliders for Story Length (short/medium/long), Creativity (1-3), Pacing (1-3), and `ModelSelectorMorphicon` tier selection before a "Bắt đầu Chấp bút" submit button.

2. **Workspace View Controller State in `frontend/src/app/page.tsx`**:
   - Lines 157–159:
     ```typescript
     const [activeTab, setActiveTab] = useState<"setup" | "editor" | "comic">("setup");
     const [setupPhase, setSetupPhase] = useState<1 | 2 | 3>(1);
     ```
   - Lines 242–385:
     * `handlePhase1Continue`: Combines prompt with genre tags `[Thể loại: ...]`, transitions `setupPhase(2)`, calls `api.chatInterview`.
     * `handleSendMessage`: Appends user message, calls `api.chatInterview(updatedHistory)`, checks `res.is_ready`.
     * `handleSkipInterview`: Calls `api.refinePrompt(chatHistory)`, stores `refinedPrompt`, transitions `setupPhase(3)`.
     * `handleStartWriting`: Takes `(length, creativity, pacing)`, sets `activeTab("editor")`, calls `api.streamStory(endpoint, ...)`.
   - Lines 838–864: Conditionally renders `Phase1Idea` (phase 1), `Phase2Interview` (phase 2), or `Phase3Controls` (phase 3).

3. **Backend QARefiner & Prompt Intelligence in `backend/agents/qa_refiner.py`**:
   - Lines 14–44: System prompt for `chat_interview` is already configured with Gemini/ChatGPT style guidelines, encompassing:
     * Comprehensive genre knowledge (Fantasy, Urban, Mystery, Folklore horror, Sci-fi, Romance, History).
     * Rule 1: Free Personal Fiction (100% creative liberty for modern/fictional settings).
     * Rule 2: Vietnamese Historical Integrity (Strict factual adherence for real figures/battles vs. fictional lens for Dã sử).
     * Rule 3: Copyright & Original IP Protection (Advising original characters/lore rather than copying commercial IPs).
     * Appends `[READY]` tag when the narrative concept is sufficiently developed.
   - Lines 60–97: `refine_prompt` compresses the entire interview history into a 5-beat Dramatic Narrative Bible (`TIÊU ĐỀ`, `THỂ LOẠI`, `NHÂN VẬT & POV`, `BỐI CẢNH`, `CẤU TRÚC 5 NHỊP KỊCH TÍNH`) within 1-2 seconds.

4. **Streaming Protocol in `frontend/src/lib/api.ts`**:
   - Lines 171–224: `api.streamStory(endpoint, payload, onChunk, onComplete, onError)`: Reads HTTP response via `res.body.getReader()`, strips `[SESSION_ID:...]`, `[STORY_ID:...]`, `[GENERATION_ERROR:...]` in real time, and passes cleaned text to `onChunk`.
   - On completion, parses `sessionId` and `storyId` from markers.

5. **Layer 0 & Layer 2 Visual Pipeline**:
   - `frontend/src/components/canvas/ThreeAmbientCanvas.tsx`: Native WebGL background runs on `z-index: 0` behind DOM elements.
   - `frontend/src/components/morphicons/ModelSelectorMorphicon.tsx`: High-performance SVG spring physics selector for `flash` | `versatile` | `master` tiers.
   - `frontend/src/components/portals/ClientPortal.tsx`: Renders modals on `z-index: 50+` with `isolation: isolate`.

---

## 2. Logic Chain

1. **Direct Constraint Violation of Current Architecture**:
   - Observation 1 & 2 show that creating a story currently requires stepping through Phase 1 (`Phase1Idea.tsx`), Phase 2 (`Phase2Interview.tsx`), and Phase 3 (`Phase3Controls.tsx`).
   - Requirement #2 explicitly demands: *"Completely eliminate old static genre chips (Phase 1 Idea chips) and multi-phase interview (Phase 2 Interview). Minimalist, elegant full-screen chat interface with floating bottom input bar and spacious chat bubbles."*
   - Therefore, `Phase1Idea.tsx`, `Phase2Interview.tsx`, and `Phase3Controls.tsx` must be deprecated and replaced by a unified component `UnifiedIntakeChat.tsx`.

2. **Integration of AI Assistant Intelligence**:
   - Observation 3 shows that the backend `QARefiner` is already prompted with full knowledge of genres, personal fiction freedom, Vietnamese history integrity, and IP copyright rules, and signals readiness with `[READY]`.
   - By creating a full-screen chat interface in `UnifiedIntakeChat.tsx`, the frontend directly exposes this intelligence in a ChatGPT / Gemini conversational environment.
   - For empty chat states, starter suggestion pills (Vietnamese History, Cyberpunk, Xianxia, Slice of Life) provide immediate creative sparks without rigid static chips.

3. **Mechanism for Seamless 1-2s Transition to Story Editor**:
   - Observation 2 & 4 demonstrate that `api.refinePrompt` and `api.streamStory` already exist and operate synchronously.
   - Currently, the transition is bottlenecked by the intermediate Phase 3 sliders screen.
   - By embedding compact tier/length controls directly into `UnifiedIntakeChat` (or using intelligent defaults) and adding a prominent *"Bắt đầu viết truyện ngay"* action button, the user can trigger transition instantly.
   - When clicked:
     1. Frontend calls `api.refinePrompt(chatHistory)` (takes 1-2s).
     2. Switches `activeTab` to `"editor"`.
     3. Calls `api.streamStory("init-story", { refined_prompt })`.
     4. Words stream live into `StoryEditor.tsx`, with `story_id` and `session_id` allocated immediately.

---

## 3. Caveats

- **Active Terminal Command Timeout**: During initial environment inspection, interactive terminal commands (`npm run build`) encountered user permission prompt timeout. All code analysis was conducted directly on source files via read-only inspection tools (`view_file`, `grep_search`, `find_by_name`).
- **R4 (Community Feed & Save & Publish)**: Requirement #4 introduces a "Bài đăng" tab and "Lưu và đăng bài" button on `StoryEditor.tsx`. While the scope of this survey focuses on R2 and R3, the design of `UnifiedIntakeChat` and `StoryEditor` explicitly preserves space and props for R4 compatibility.
- **Backend Model Availability**: Backend `qa_refiner.py` utilizes `GroqClient("qwen/qwen3.8-27b")` with `GROQ_API_KEY_BIBLE`. The frontend handles graceful fallbacks if network or API keys are missing.

---

## 4. Conclusion

The path to implement Requirements #2 & #3 is clear, clean, and isolated:
1. **Create `frontend/src/components/setup/UnifiedIntakeChat.tsx`**: A full-screen Gemini/ChatGPT-style chat interface with starter inspiration pills, spacious bubbles, floating bottom input dock, and an instant *"Bắt đầu viết truyện ngay"* action button.
2. **Refactor `frontend/src/app/page.tsx`**: Remove `setupPhase` (1, 2, 3), replace legacy phase components with `UnifiedIntakeChat`, and wire the 1-2 second `api.refinePrompt` compression step directly into `StoryEditor` streaming.
3. **Deprecate / Remove Legacy Setup Files**: Remove `Phase1Idea.tsx`, `Phase2Interview.tsx`, `Phase3Controls.tsx` to maintain clean, zero-cruft codebase hygiene.
4. **Update `Sidebar.tsx` and `i18n.ts`**: Connect "Viết truyện mới" to reset intake chat, and provide 100% bilingual VI/EN translations.

---

## 5. Verification Method

To independently verify the survey findings and subsequent implementation:
1. **Files Inspection**:
   - Inspect `frontend/src/app/page.tsx` lines 158, 242–385, 838–864 to verify legacy 3-phase structure.
   - Inspect `backend/agents/qa_refiner.py` lines 14–44 to verify Q&A assistant rules.
   - Inspect `frontend/src/components/setup/Phase1Idea.tsx` to verify 28 static genre chips.
2. **Build Verification**:
   - Run Next.js build:
     ```powershell
     cd e:\NarrAI\frontend
     npm run build
     ```
     Ensure clean compilation with 0 TypeScript and 0 ESLint errors.
3. **Behavioral Invalidation Conditions**:
   - The implementation fails if any static genre chips or Phase 1/Phase 2 multi-step wizard screens appear when starting a story.
   - The implementation fails if clicking "Bắt đầu viết truyện ngay" does not compress the narrative bible and navigate to `StoryEditor` with active streaming within 1-3 seconds.
