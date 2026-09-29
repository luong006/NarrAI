## 2026-09-29T03:30:42Z
Read e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md.
Read e:\NarrAI\PROJECT.md.
Read e:\NarrAI\.agents\teamwork\explorer_r5_survey_2\survey_report.md.

You are the Frontend Intake & Transition Implementer for Milestone 2.
Your working directory is e:\NarrAI\.agents\teamwork\worker_r5_m2.
You own exclusively:
- frontend/src/components/setup/UnifiedIntakeChat.tsx (create new)
- frontend/src/components/setup/Phase1Idea.tsx, Phase2Interview.tsx, Phase3Controls.tsx (safely remove/retire)
- frontend/src/app/page.tsx (mount UnifiedIntakeChat, remove setupPhase, implement seamless transition handler)
- frontend/src/components/layout/Sidebar.tsx (update onNewStory to reset intake chat)
- frontend/src/lib/types.ts
- frontend/src/lib/i18n.ts

Tasks to implement:
1. Build UnifiedIntakeChat.tsx:
   - Minimalist, elegant full-screen chat interface (ChatGPT/Gemini style), translucent background letting Layer 0 Three Ambient Canvas shine through.
   - Starter prompt suggestion pills for empty state: Vietnamese History (Chính sử vs. Dã sử guidance), Sci-Fi/Cyberpunk, Xianxia, Slice of Life.
   - Spacious chat bubbles (User vs Assistant) with Markdown formatting support.
   - Floating bottom dock with auto-expanding textarea, integrated ModelSelectorMorphicon (Flash/Versatile/Master), story length selector pill, and send button.
   - Prominent "Bắt đầu viết truyện ngay" / "Chốt cốt truyện" button (pulses when AI outputs [READY] or turns >= 1).
2. Implement seamless transition:
   - When user clicks "Bắt đầu viết truyện ngay":
     * Call api.refinePrompt(chatHistory) (1-2s compression into Refined Narrative Bible).
     * Instantly set activeTab = "editor", clear manuscript canvas, set streaming = true.
     * Trigger api.streamStory with Chapter 1 generation and lock story_id & session_id.
3. Remove legacy setup wizard files (Phase1Idea.tsx, Phase2Interview.tsx, Phase3Controls.tsx) and eliminate all dangling imports.
4. Update frontend/src/app/page.tsx, Sidebar.tsx, types.ts, and i18n.ts with bilingual VI/EN support.
5. Verification: Run npm run build inside frontend/ to ensure 0 TypeScript or Next.js build errors.
6. Write detailed handoff.md in your working directory. Update progress.md with timestamp.
