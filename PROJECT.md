# Project: NarrAI Round 5 (Flexible Manuscript Surgery, Unified Intake Chat, Community Feed & 4-Layer Architecture)

## Architecture
NarrAI v2.0 is an AI-powered storytelling, manuscript surgery, and manga studio with a FastAPI backend and Next.js App Router frontend.
- **Backend Architecture**: FastAPI (`backend/main.py`) driving specialized AI services:
  - `CopilotAgent` (`backend/agents/copilot_agent.py`): 5-Target Flexible Manuscript Surgery, Dynamic Semantic Chunk Slicer, Structural Heading Preservation.
  - `StoryGenerator` (`backend/agents/story_generator.py`): Light Novel engine rules, streaming generation, instant `story_id` allocation.
  - `QARefiner` (`backend/agents/qa_refiner.py`): Intelligent conversational intake, Vietnamese historical authenticity (Chính sử vs. Dã sử), genre mastery, IP protection, and 1-2s Refined Narrative Bible compression.
  - `SocialRouter` & `RecommenderService` (`backend/routers/social_router.py`, `backend/services/recommender_service.py`): Community feed, 3-stage recommendation (Two-Tower Cosine + Multi-Armed Bandit 15% + MMR $\lambda=0.7$), "Lưu & Đăng bài" persistence.
- **Frontend 4-Layer Collision-Free Architecture**:
  - **Layer 0 (ThreeUI 3D)**: `ThreeAmbientCanvas.tsx` running Dong Son Drum shader quad + 350 particles, auto-pausing on tab hidden / out of screen (GPU 0%).
  - **Layer 1 (Semantic DOM & 3D Interactive Cards)**: `InteractiveTiltCard.tsx` with CSS 3D Transforms (`perspective: 1000px`, `transform-style: preserve-3d`), `UnifiedIntakeChat.tsx`, `StoryEditor.tsx`, `CommunityFeed.tsx`.
  - **Layer 2 (Morphicons SVG)**: Spring physics vector interactions (`LikeButtonMorphicon`, `ModelSelectorMorphicon`, `CoinBadgeMorphicon`).
  - **Layer 3 (Modals & Chat Portals)**: `ClientPortal.tsx` with React Portals, `isolation: isolate`, and `z-index: 60` (`PostReaderModal`, `AuthModal`, `MessengerModal`, `CoinTopupModal`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | R5.1.1 Target 1: Opening / Hook Rewrite | Viết lại mở đầu giật gân (In Medias Res), giữ nguyên tiêu đề và mạch truyện chính | M1 | Survey 1 |
| 2 | R5.1.2 Target 2: Character & Dialogue Surgery | Thay tên, đổi đại từ, cập nhật khẩu ngữ hiện đại, subtext, phản ứng sinh lý trên phân đoạn hoặc toàn bộ truyện | M1 | Survey 1 |
| 3 | R5.1.3 Target 3: Middle Beats & Scene Insertion | Thêm biến cố, đẩy nhanh nhịp độ (Pacing), chèn tình huống nguy nan hoặc đào sâu nội tâm không làm xáo trộn mở đầu và kết | M1 | Survey 1 |
| 4 | R5.1.4 Target 4: Climax & Ending Rewrite | Xây dựng Lingering Cliffhanger nghẹt thở hoặc kết thúc dâng trào cảm xúc, giữ vững logic | M1 | Survey 1 |
| 5 | R5.1.5 Target 5: Tone Shift & Style Restyling | Viết lại truyện theo phong cách chỉ định (u tối, giật gân, hài hước, trinh thám, cổ trang) bảo toàn cốt truyện và nhân vật | M1 | Survey 1 |
| 6 | R5.1.6 Dynamic Semantic Chunk Slicing | Phân rã lát cắt `prefix` -> `window_to_edit` -> `suffix` chuẩn xác theo mốc chương `## Chương X` và cấu trúc ngữ nghĩa | M1 | Survey 1 |
| 7 | R5.1.7 Heading & Structure Preservation Engine | Bảo toàn tuyệt đối nhãn tiêu đề `**[TÊN TIÊU ĐỀ]**` và các chương `## Chương X` qua mọi lượt can thiệp | M1 | Survey 1 |
| 8 | R5.1.8 Story ID Immediate Pre-allocation & Streaming | Cấp phát `story_id` tức thì khi bắt đầu chuyển giao hoặc stream (hỗ trợ cả guest và registered users), endpoint `/api/stories/allocate` | M1 | Survey 1 |
| 9 | R5.1.9 Social Publish Data Enrichment | Bổ sung lưu văn bản bản thảo và tự động đồng bộ ảnh bìa manga trong `POST /api/social/publish`, trả đủ truyện chữ và comic trong `GET /post/{id}` | M1 | Survey 3 |
| 10 | R5.2.1 Legacy Setup Wizard Elimination | Loại bỏ hoàn toàn lưới 28 chip thể loại cũ (`Phase1Idea`), phỏng vấn chia bước cũ (`Phase2Interview`), và bảng điều khiển rời (`Phase3Controls`) | M2 | Survey 2 |
| 11 | R5.2.2 Unified Intake Chat Interface | Giao diện AI Intake Chat tối giản, tinh tế chuẩn ChatGPT / Gemini, canvas toàn màn hình, dock input nổi, ModelSelectorMorphicon, starter pills | M2 | Survey 2 |
| 12 | R5.2.3 Literary, Historical & IP Domain Intelligence | Trợ lý Q&A đối thoại am hiểu sâu sắc thể loại văn học, tự do sáng tạo hư cấu, tôn trọng chính sử Việt Nam (phân định chính sử / dã sử), cảnh báo bản quyền IP | M2 | Survey 2 |
| 13 | R5.2.4 Seamless Transition to Story Editor | Nút "Bắt đầu viết truyện ngay" / "Chốt cốt truyện" cô đọng Refined Narrative Bible trong 1-2s, chuyển thẳng sang StoryEditor và kích hoạt streaming | M2 | Survey 2 |
| 14 | R5.3.1 Community Feed ("Bài đăng" Tab) | Bổ sung tab điều hướng "Bài đăng" trên Sidebar và page.tsx, hiển thị danh sách tác phẩm xuất bản của cộng đồng và cá nhân | M3 | Survey 3 |
| 15 | R5.3.2 3D Parallax Tilt Cards & Reader Modal | Thẻ 3D Parallax Tilt (`InteractiveTiltCard`) hiển thị bìa, trích đoạn, thể loại, metrics; Modal đọc truyện chữ & xem comic (`PostReaderModal`) | M3 | Survey 3 |
| 16 | R5.3.3 Community Interactions & 3-Stage Recommender | Tương tác Like Morphicon, bình luận, chia sẻ; kết nối với bộ gợi ý 3 giai đoạn (Two-Tower + Bandit 15% Cold-Start + MMR lambda=0.7) | M3 | Survey 3 |
| 17 | R5.3.4 Save & Publish Button ("Lưu & Đăng bài") | Nút "Lưu & Đăng bài" trên thanh công cụ StoryEditor: tự động lưu bản thảo, sync bìa manga, gọi `/api/social/publish`, toast kèm link xem bài đăng | M3 | Survey 3 |
| 18 | R5.3.5 4-Layer Collision-Free Architecture Enforcement | Đảm bảo tuyệt đối 4 tầng không xung đột: Layer 0 ThreeUI pause, Layer 1 CSS 3D Cards, Layer 2 Morphicons spring, Layer 3 React Portals isolation/z-index 60 | M3 | Survey 3 |
| 19 | R5.4.1 E2E Test Suite Creation (Tiers 1-4) | Xây dựng bộ kiểm thử E2E độc lập: Tier 1 Feature Coverage, Tier 2 Boundaries, Tier 3 Cross-feature combinations, Tier 4 Real-world scenarios | M4 | Test Track |
| 20 | R5.4.2 Adversarial Coverage Hardening (Tier 5) & Full Build Pass | Kiểm thử đối kháng hộp trắng bởi Challengers, đảm bảo py_compile 0 lỗi và npm run build 0 lỗi | M4 | System Gate |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Backend Copilot Surgery Engine & Story ID Allocation | `backend/agents/copilot_agent.py`, `backend/main.py`, `backend/services/recommender_service.py`, `backend/routers/social_router.py` | none | DONE |
| M2 | Frontend Unified Intake Chat & Seamless Transition | `frontend/src/components/setup/UnifiedIntakeChat.tsx`, `frontend/src/app/page.tsx`, `frontend/src/components/layout/Sidebar.tsx`, `frontend/src/lib/types.ts`, `frontend/src/lib/i18n.ts` | none | DONE |
| M3 | Community Feed, Save & Publish Button & 4-Layer Integration | `frontend/src/components/feed/CommunityFeed.tsx`, `frontend/src/components/modals/PostReaderModal.tsx`, `frontend/src/components/editor/StoryEditor.tsx`, `frontend/src/lib/api.ts`, `frontend/src/app/page.tsx` | M1, M2 | IN_PROGRESS |
| M4 | E2E Testing Track, Adversarial Hardening & Final Gate | `backend/tests/test_e2e_round5_surgery_feed.py`, `backend/tests/test_adversarial_round5_resilience.py`, py_compile, Next.js build | M1, M2, M3 | PLANNED |

## Code Layout & Ownership
- `backend/agents/copilot_agent.py`: 5-target classifier, semantic chunk slicing, heading preservation, targeted prompts. Owned exclusively by M1 Worker.
- `backend/main.py`: Story pre-allocation, `/api/stories/allocate`, streaming yield of `[STORY_ID:{id}]`. Owned exclusively by M1 Worker.
- `backend/services/recommender_service.py` & `backend/routers/social_router.py`: `publish_post` manuscript saving and cover sync, `get_post_details` content enrichment. Owned exclusively by M1 Worker.
- `frontend/src/components/setup/UnifiedIntakeChat.tsx`: New ChatGPT/Gemini intake component. Owned exclusively by M2 Worker.
- `frontend/src/components/setup/`: Removal of `Phase1Idea.tsx`, `Phase2Interview.tsx`, `Phase3Controls.tsx`. Owned exclusively by M2 Worker.
- `frontend/src/components/feed/`: Community feed component (`CommunityFeed.tsx`). Owned exclusively by M3 Worker.
- `frontend/src/components/modals/PostReaderModal.tsx`: Text & comic reader modal. Owned exclusively by M3 Worker.
- `frontend/src/components/editor/StoryEditor.tsx`: "Lưu & Đăng bài" button and publishing toast. Owned exclusively by M3 Worker.
- `frontend/src/lib/api.ts`: Social feed and publishing API client methods. Owned exclusively by M3 Worker.
- `frontend/src/components/layout/Sidebar.tsx` & `frontend/src/app/page.tsx`: Navigation wiring for Setup, Editor, Comic, Feed. Coordinated between M2 and M3.
- `backend/tests/`: E2E tests, boundary tests, adversarial tests. Owned exclusively by E2E Test Writer / Challenger.

## Interface Contracts
### Copilot Flexible Surgery Contract
- Input: `instruction: str`, `story_content: str`, `context: dict`.
- Intent: One of `TARGET_1_OPENING`, `TARGET_2_CHARACTER_DIALOGUE`, `TARGET_3_MIDDLE_BEATS`, `TARGET_4_CLIMAX_ENDING`, `TARGET_5_TONE_STYLE`.
- Slicing: `(prefix, window_to_edit, suffix) = slice_manuscript(story_content, target)`.
- Output: `updated_story_content = prefix + sanitized_edited_window + suffix`.
- Invariant: `**[TITLE]**` must remain identical at top; all `## Chương X` occurrences across `prefix`, `window_to_edit`, and `suffix` must be preserved 100%.

### Unified Intake Chat ↔ Story Editor Transition
- User click "Bắt đầu viết truyện ngay" / "Chốt cốt truyện" (or AI ready confirmation):
  1. Frontend calls `api.refinePrompt(chatHistory)` -> returns `refined_prompt` (1-2s).
  2. Frontend sets `activeTab = "editor"`, clears editor canvas, sets `streaming = true`.
  3. Frontend triggers `api.streamStory("init-story", { refined_prompt, story_length, session_id })`.
  4. Stream yields `[STORY_ID:<id>]` at inception, locking `storyId` in frontend state for immediate Manga adaptation or Social Publishing.

### Social Publishing & Feed Contract
- `POST /api/social/publish`:
  - Request body: `{ title: str, content_snippet: str, story_text?: str, story_id?: int, genre: str, tags: list[str], cover_image_url?: str }`.
  - Response: `{ status: "success", post: SocialPostResponse }`.
  - Side effect: If `story_text` provided, saves/updates `Story`. If `cover_image_url` not provided, extracts first panel image from associated `Comic`.
- `GET /api/social/feed?page=1&limit=20&genre=...`:
  - Response: `{ posts: list[SocialPostResponse], total: int, page: int }`.
- `GET /api/social/post/{post_id}`:
  - Response: Includes `id`, `title`, `content_snippet`, `story_content` (full text), `comic_panels` (panel images/dialogues), `author`, `likes_count`, `comments_count`.
- `StoryEditor.tsx`:
  - "Lưu & Đăng bài" triggers save of current manuscript -> `POST /api/social/publish` -> displays success toast with direct link to view post in Community Feed.
